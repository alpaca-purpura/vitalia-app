# 03-arch-be.md — vitalia-adopt-luana-core-iam (Backend sub-arch)

> Sub-architecture detail for backend surface. Consumer: `builder-backend` (Sonnet).
> Parent: `03-arch.md` (consolidado).

## § 0 — Owner & scope

- **Builder**: `builder-backend` (Sonnet)
- **Auditor**: `auditor-backend` (Opus)
- **NO surface FE Next.js**: ONLY Playwright E2E specs live in `vitalia/frontend/e2e/admin/` (testing infra, NO React).
- **NO surface agentic**.

## § 1 — Migration ordering strategy (CRITICAL)

### Problem

Migration `014_vitalia_tenants_columns.py` (existing) does `ALTER TABLE tenants ADD COLUMN IF NOT EXISTS ...` — but tenants table does NOT exist in vitalia DB hoy. `alembic upgrade head` falls en 014 con `psycopg2.errors.UndefinedTable: relation "tenants" does not exist`.

### Solution adoptada

1. **Migration 022 incluye los 4 campos de 014 en el CREATE TABLE inicial** (`is_onboarded`, `location_country`, `location_city`, `timezone`).

   ```sql
   CREATE TABLE IF NOT EXISTS public.tenants (
       ...
       timezone character varying DEFAULT 'UTC'::character varying,
       is_onboarded boolean NOT NULL DEFAULT false,
       location_country character varying(2),
       location_city character varying(255),
       ...
   );
   ```

2. **Migration 014 se MODIFICA** a wrapper guard que skip silenciosamente si tenants no existe:

   ```python
   def upgrade() -> None:
       """Idempotent ALTER — skips if tenants table doesn't exist yet
       (will be created by 022 with all columns inline).
       """
       op.execute("""
           DO $$ BEGIN
               IF EXISTS (
                   SELECT FROM information_schema.tables
                   WHERE table_schema = 'public' AND table_name = 'tenants'
               ) THEN
                   ALTER TABLE tenants ADD COLUMN IF NOT EXISTS is_onboarded BOOLEAN NOT NULL DEFAULT FALSE;
                   ALTER TABLE tenants ADD COLUMN IF NOT EXISTS location_country VARCHAR(2);
                   ALTER TABLE tenants ADD COLUMN IF NOT EXISTS location_city VARCHAR(255);
                   ALTER TABLE tenants ADD COLUMN IF NOT EXISTS timezone VARCHAR(64);

                   UPDATE tenants SET is_onboarded = true
                     WHERE created_at < '2026-05-17 00:00:00+00'::timestamptz
                       AND is_onboarded = false;

                   CREATE INDEX IF NOT EXISTS ix_tenants_is_onboarded ON tenants(is_onboarded);
               ELSE
                   RAISE NOTICE 'Migration 014 skipped: tenants table missing, will be created by migration 022 with all columns inline';
               END IF;
           END $$;
       """)
   ```

   Downgrade actualizada similarmente.

3. **Migration 022** crea tenants table CON los 4 columns inline. When 014 corre primero (en alembic chain order 001→014→...), 014 skips silenciosamente. Cuando 022 corre después, crea tabla completa. **Result**: cualquier orden funciona, idempotent garantizado.

### Order of application

Alembic chain (linear):
```
001 → 002 → 003 → ... → 013 (audit_log) → 014 (tenants_columns — NOW skip-if-not-exists)
    → 015 (offers_columns — exists already) → 016 → ... → 021 → 022 (NEW — engine IAM) → 023 (NEW — vitalia_clinics)
```

Cuando se aplica `alembic upgrade head`:
1. 001-012: snapshots vitalia medical tables (sin tocar engine IAM)
2. 013: audit_log partitioned
3. 014: SKIPPED (tenants doesn't exist) — RAISE NOTICE
4. 015-021: vitalia_* medical columns
5. 022: CREATE TABLE users + tenants + user_tenants (with 014's columns inline)
6. 023: CREATE TABLE vitalia_clinics FK → tenants(id)

## § 2 — Admin rewrite — pseudo-code skeleton

### tenants.py rewrite (concept)

```python
"""Admin module — Tenant management for Vitalia (engine luana-core-iam).

CRITICAL: NO SQL crudo. NO references to phantom tables (vitalia_tenants,
vitalia_user_profiles, vitalia_clinics).
Consume engine repositories: luana_core_iam.infrastructure.repositories.TenantRepository.
"""

from __future__ import annotations

import uuid

import structlog
from luana_core_iam.domain.tenant import Tenant
from luana_core_iam.infrastructure.repositories.tenant_repository import TenantRepository

from src.modules.vitalia.admin._shared.db import get_sync_session
from src.modules.vitalia.audit.audit_writer import write_audit_log_sync

logger = structlog.get_logger()


def render_tenants_page() -> None:
    import streamlit as st  # noqa: PLC0415

    st.header("Tenants")
    st.caption("Gestión de tenants en la plataforma Vitalia (engine luana-core-iam).")

    tab_list, tab_create = st.tabs(["Listado", "Crear nuevo"])

    with tab_list:
        _render_tenants_list()
    with tab_create:
        _render_create_tenant_form()


def _render_tenants_list() -> None:
    import streamlit as st  # noqa: PLC0415

    with get_sync_session() as session:
        repo = TenantRepository(session)
        tenants_list = repo.get_all()  # engine method (ordered desc by created_at)

    if not tenants_list:
        st.info("Aún no existen tenants. Crea el primero en la pestaña 'Crear nuevo'.")
        return

    rows = [
        {
            "ID": str(t.id)[:8],
            "Nombre": t.name,
            "Slug": t.slug,
            "Estado": "Activo" if t.is_active else "Suspendido",
            "Creado": t.created_at.strftime("%Y-%m-%d") if t.created_at else "—",
        }
        for t in tenants_list
    ]
    st.dataframe(rows, use_container_width=True)

    # Toggle suspender/activar — para cada row mostrar botón
    st.divider()
    selected_id = st.selectbox(
        "Seleccionar tenant para suspender/activar",
        options=[str(t.id) for t in tenants_list],
        format_func=lambda tid: next(t.name for t in tenants_list if str(t.id) == tid),
    )
    if st.button("Toggle Activo/Suspendido"):
        _toggle_tenant_active(uuid.UUID(selected_id))


def _render_create_tenant_form() -> None:
    import streamlit as st  # noqa: PLC0415

    with st.form("form_create_tenant", clear_on_submit=True):
        name = st.text_input("Nombre *")
        slug = st.text_input("Slug *", help="Solo letras minúsculas, números y guiones")
        country = st.selectbox("País *", options=["AR", "MX", "CO", "CL", "PE", "BR", "UY", "EC"])
        plan_tier = st.selectbox("Plan tier", options=["solo_doctor", "clinic", "multi_site"])
        submitted = st.form_submit_button("Crear tenant")

    if not submitted:
        return

    if not name.strip() or not slug.strip():
        st.error("Nombre y slug son obligatorios.")
        return

    new_tenant = Tenant(
        id=uuid.uuid4(),
        name=name.strip(),
        slug=slug.strip().lower(),
        config_json={"country": country, "plan_tier": plan_tier},
        is_active=True,
    )

    try:
        with get_sync_session() as session:
            repo = TenantRepository(session)
            created = repo.create(new_tenant)

            # Audit log SYNC write — HIPAA-lite invariant
            admin_user_id = uuid.uuid4()  # Chris super-admin, no Clerk user
            write_audit_log_sync(
                db=session,
                tenant_id=created.id,
                clinic_id=None,
                user_id=admin_user_id,
                action="tenant.create",
                resource_type="tenant",
                resource_id=created.id,
                payload={"name": name.strip(), "slug": slug.strip().lower(), "country": country, "plan_tier": plan_tier},
                user_agent="VitaliaAdmin/1.0",
            )
        st.success(f"Tenant '{name.strip()}' creado correctamente")
        logger.info("admin_tenant_created", tenant_id=str(created.id), slug=slug.strip().lower())
    except Exception as exc:  # noqa: BLE001
        logger.error("admin_create_tenant_error", error=str(exc))
        st.error(f"No se pudo crear el tenant: {exc}")


def _toggle_tenant_active(tenant_id: uuid.UUID) -> None:
    import streamlit as st  # noqa: PLC0415

    with get_sync_session() as session:
        repo = TenantRepository(session)
        tenant = repo.get_by_id(tenant_id)
        if not tenant:
            st.error("Tenant no encontrado.")
            return

        new_active = not tenant.is_active
        tenant.is_active = new_active
        updated = repo.update(tenant)

        action = "tenant.suspend" if not new_active else "tenant.activate"
        admin_user_id = uuid.uuid4()
        write_audit_log_sync(
            db=session,
            tenant_id=updated.id,
            clinic_id=None,
            user_id=admin_user_id,
            action=action,
            resource_type="tenant",
            resource_id=updated.id,
            payload={"is_active_new": new_active},
        )
    msg = "suspendido" if not new_active else "activado"
    st.success(f"Tenant '{updated.name}' {msg}")
```

### users.py rewrite (concept)

```python
"""Admin module — User management for Vitalia (engine luana-core-iam).

CONSUME UserRepository + UserTenantRepository.
NO Clerk SDK direct call (deferred — story scope is admin CRUD only).
"""
from __future__ import annotations

import uuid
from uuid import UUID

import streamlit as st
from luana_core_iam.domain.user import User
from luana_core_iam.infrastructure.repositories.user_repository import UserRepository
from luana_core_iam.infrastructure.repositories.user_tenant_repository import UserTenantRepository
from luana_core_iam.infrastructure.repositories.tenant_repository import TenantRepository
from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel

from src.modules.vitalia.admin._shared.db import get_sync_session
from src.modules.vitalia.audit.audit_writer import write_audit_log_sync


def render_users_page() -> None:
    st.header("Usuarios")
    st.caption("Gestión de usuarios — engine luana-core-iam (consumed via UserRepository + UserTenantRepository)")

    tab_list, tab_create = st.tabs(["Listado", "Crear nuevo"])
    with tab_list:
        _render_users_list()
    with tab_create:
        _render_create_user_form()


def _render_users_list() -> None:
    # Filter dropdown — tenant scope
    with get_sync_session() as session:
        tenant_repo = TenantRepository(session)
        tenants_list = tenant_repo.get_all()

    tenant_options = {"Todos": None}
    for t in tenants_list:
        tenant_options[t.name] = t.id

    selected_tenant_name = st.selectbox(
        "Filtrar por tenant",
        options=list(tenant_options.keys()),
        key="user_filter_tenant",
    )
    selected_tenant_id = tenant_options[selected_tenant_name]
    st.session_state["selected_tenant_filter"] = str(selected_tenant_id) if selected_tenant_id else None

    # Fetch users via SQLAlchemy 2.0 select() (acceptable: queries via engine model
    # directly, since admin platform-level — NOT brand-specific phantom tables).
    # NOTE: NO `session.execute(text("SELECT ..."))` raw SQL. Use ORM select().
    from sqlalchemy import select
    from luana_core_iam.infrastructure.models.user_model import UserModel

    with get_sync_session() as session:
        stmt = select(UserModel).order_by(UserModel.created_at.desc())
        users_list = session.execute(stmt).scalars().all()

        ut_repo = UserTenantRepository(session)
        rows = []
        for u in users_list:
            if selected_tenant_id and not any(
                ut.tenant_id == selected_tenant_id
                for ut in session.execute(
                    select(UserTenantModel).where(UserTenantModel.user_id == u.id)
                ).scalars().all()
            ):
                continue

            user_tenants_list = ut_repo.get_tenants_for_user(u.id)
            tenants_label = ", ".join(f"{t.name} ({role})" for t, role in user_tenants_list) or "Sin tenant"
            rows.append({
                "ID": str(u.id)[:8],
                "Email": u.email,
                "Nombre": u.full_name or "—",
                "Tenants": tenants_label,
                "Estado": "Activo" if u.is_active else "Baneado",
                "Creado": u.created_at.strftime("%Y-%m-%d") if u.created_at else "—",
            })

    if not rows:
        st.info("Aún no existen usuarios.")
        return
    st.dataframe(rows, use_container_width=True)

    # Ban toggle for selected user
    selected_user_id = st.selectbox(
        "Seleccionar usuario para banear/activar",
        options=[str(u.id) for u in users_list],
        format_func=lambda uid: next(u.email for u in users_list if str(u.id) == uid),
    )
    if st.button("Toggle Banear/Activar"):
        _toggle_user_active(uuid.UUID(selected_user_id))


def _render_create_user_form() -> None:
    with get_sync_session() as session:
        tenant_repo = TenantRepository(session)
        tenants_list = tenant_repo.get_all()

    if not tenants_list:
        st.warning("No hay tenants. Crea un tenant primero.")
        return

    with st.form("form_create_user", clear_on_submit=True):
        email = st.text_input("Email *")
        full_name = st.text_input("Nombre completo *")
        tenant_dropdown = st.selectbox(
            "Tenant *",
            options=[t.id for t in tenants_list],
            format_func=lambda tid: next(t.name for t in tenants_list if t.id == tid),
        )
        role = st.selectbox("Rol *", options=["admin", "doctor", "nurse", "recepcionist", "member", "viewer"])
        submitted = st.form_submit_button("Crear usuario y asignar")

    if not submitted:
        return

    new_user = User(
        id=uuid.uuid4(),
        full_name=full_name.strip(),
        email=email.strip().lower(),
        role=role,
        is_active=True,
    )

    try:
        with get_sync_session() as session:
            user_repo = UserRepository(session)
            created_user = user_repo.create(new_user)

            # Link to tenant via direct ORM insert (UserTenantRepository missing `link` method)
            # NOTE: should-be future engine extension; meanwhile use direct ORM insert
            session.add(UserTenantModel(
                user_id=created_user.id,
                tenant_id=tenant_dropdown,
                role=role,
                is_active=True,
            ))
            session.commit()

            admin_user_id = uuid.uuid4()
            tenant_name = next(t.name for t in tenants_list if t.id == tenant_dropdown)
            write_audit_log_sync(
                db=session,
                tenant_id=tenant_dropdown,
                clinic_id=None,
                user_id=admin_user_id,
                action="user.create_and_link",
                resource_type="user",
                resource_id=created_user.id,
                payload={"email_hash": str(uuid.uuid5(uuid.NAMESPACE_DNS, created_user.email)), "role": role},
            )
        st.success(f"Usuario '{created_user.full_name}' creado y asignado a '{tenant_name}' con rol '{role}'")
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudo crear el usuario: {exc}")


def _toggle_user_active(user_id: UUID) -> None:
    with get_sync_session() as session:
        user_repo = UserRepository(session)
        user = user_repo.get_by_id(user_id)
        if not user:
            st.error("Usuario no encontrado.")
            return
        user.is_active = not user.is_active
        updated = user_repo.update(user)
        action = "user.ban" if not updated.is_active else "user.activate"

        # tenant_id = primary tenant for audit (first user_tenant)
        ut_repo = UserTenantRepository(session)
        user_tenants_list = ut_repo.get_tenants_for_user(user_id)
        primary_tenant_id = user_tenants_list[0][0].id if user_tenants_list else uuid.uuid4()

        admin_user_id = uuid.uuid4()
        write_audit_log_sync(
            db=session,
            tenant_id=primary_tenant_id,
            clinic_id=None,
            user_id=admin_user_id,
            action=action,
            resource_type="user",
            resource_id=user_id,
            payload={"is_active_new": updated.is_active, "reason": "manual_admin_action"},
        )

    msg = "baneado" if not updated.is_active else "activado"
    st.success(f"Usuario '{updated.email}' {msg}")
```

### Note on UserTenantRepository

Current engine `UserTenantRepository` only has `get_tenants_for_user`. To link a user to a tenant on creation, story uses direct ORM insert of `UserTenantModel`. Future enhancement (NOT in this story scope): add `UserTenantRepository.link(user_id, tenant_id, role)` to engine — would require `/pm-luana` promotion proposal. Story scope: inline ORM insert acceptable since admin is platform-level (not brand-feature).

Test fitness: builder MUST verify `test_admin_no_raw_sql.py` does NOT flag this ORM `session.add(UserTenantModel(...))` — arch test scans for `session.execute(text(...))` SQL crudo only.

## § 3 — Admin helper API endpoints (Playwright support only)

`vitalia/backend/src/modules/vitalia/admin/api/admin_helpers_router.py`:

```python
"""Admin helper endpoints — TEST-ONLY for Playwright DB state verification.

Guarded by X-Internal-Token header matching VITALIA_INTERNAL_API_TOKEN env var.
NO PHI exposed. Row counts + sanitized audit log entries only.
"""

import os
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from luana_core_platform.core.database import get_db
from luana_core_iam.infrastructure.models.tenant_model import TenantModel
from luana_core_iam.infrastructure.models.user_model import UserModel
from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel
from vitalia.modules.vitalia.clinics.infrastructure.models.clinic_model import ClinicModel


router = APIRouter(prefix="/api/v1/vitalia/admin", tags=["admin-helpers"])


def _verify_internal_token(x_internal_token: str | None = Header(None)) -> None:
    expected = os.environ.get("VITALIA_INTERNAL_API_TOKEN", "")
    if not expected:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal token not configured")
    if x_internal_token != expected:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid internal token")


class DbStateResponse(BaseModel):
    tenants: int
    users: int
    user_tenants: int
    clinics: int


class AuditLogEntry(BaseModel):
    id: UUID
    tenant_id: UUID | None
    clinic_id: UUID | None
    user_id: UUID
    action: str
    resource_type: str
    resource_id: UUID | None
    occurred_at: datetime


@router.get("/db-state", response_model=DbStateResponse, dependencies=[Depends(_verify_internal_token)])
def get_db_state(db: Session = Depends(get_db)) -> DbStateResponse:
    """Return row counts for Playwright DB verify. NO PHI exposed."""
    tenants_n = db.execute(select(func.count()).select_from(TenantModel)).scalar() or 0
    users_n = db.execute(select(func.count()).select_from(UserModel)).scalar() or 0
    ut_n = db.execute(select(func.count()).select_from(UserTenantModel)).scalar() or 0
    clinics_n = db.execute(select(func.count()).select_from(ClinicModel).where(ClinicModel.deleted_at.is_(None))).scalar() or 0
    return DbStateResponse(tenants=tenants_n, users=users_n, user_tenants=ut_n, clinics=clinics_n)


@router.get("/audit-log", response_model=list[AuditLogEntry], dependencies=[Depends(_verify_internal_token)])
def get_audit_log(
    action: str | None = Query(None),
    since: datetime | None = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
) -> list[AuditLogEntry]:
    """Return audit log entries (sanitized — no payload exposed) for Playwright verification."""
    where_clauses: list[str] = []
    params: dict = {"limit": limit}
    if action:
        where_clauses.append("action = :action")
        params["action"] = action
    if since:
        where_clauses.append("occurred_at >= :since")
        params["since"] = since
    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    rows = db.execute(
        text(f"""
            SELECT id, tenant_id, clinic_id, user_id, action, resource_type, resource_id, occurred_at
            FROM vitalia_audit_log
            {where_sql}
            ORDER BY occurred_at DESC
            LIMIT :limit
        """),
        params,
    ).fetchall()

    return [
        AuditLogEntry(
            id=r.id,
            tenant_id=r.tenant_id,
            clinic_id=r.clinic_id,
            user_id=r.user_id,
            action=r.action,
            resource_type=r.resource_type,
            resource_id=r.resource_id,
            occurred_at=r.occurred_at,
        )
        for r in rows
    ]
```

**NOTE for arch test `test_admin_no_raw_sql.py`**: `admin_helpers_router.py` lives bajo `admin/api/`, NO bajo `admin/modules/`. Arch test scopes scan a `admin/modules/{tenants,users,clinics}.py` only. Helper router exempt by design (audited inline above).

## § 4 — clinics module DDD scaffold (full layers)

### domain/clinic.py

Ver § 2 03-arch.md.

### infrastructure/models/clinic_model.py

Ver § 3 03-arch.md.

### infrastructure/repositories/clinic_repository.py

Ver § 7 03-arch.md.

### application/clinic_service.py

Ver § 8 03-arch.md.

### api/dtos.py + api/router.py + api/decorators.py

Ver § 4-5-8 03-arch.md.

## § 5 — Docker compose service spec

```yaml
# vitalia/docker-compose.dev.yml — append to services:

  vitalia_admin_dev:
    build:
      context: .
      dockerfile: vitalia/backend/Dockerfile
      target: dev
    restart: unless-stopped
    env_file:
      - path: vitalia/.env.dev
        required: false
    environment:
      DATABASE_URL: "postgresql+asyncpg://postgres:password@luana_postgres_dev:5432/vitalia_dev"
      UV_PROJECT_ENVIRONMENT: "/workspace/.venv"
      STREAMLIT_SERVER_HEADLESS: "true"
      STREAMLIT_SERVER_ENABLE_CORS: "false"
      STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION: "false"  # dev only
    volumes:
      - .:/workspace:rw
      - vitalia_backend_venv:/workspace/.venv
    ports:
      - "127.0.0.1:8502:8501"
    networks:
      - luana_dev_net
    depends_on:
      luana_postgres_dev:
        condition: service_healthy
      vitalia_backend_dev:
        condition: service_started
    command: >
      sh -c "cd /workspace/vitalia/backend &&
      uv run streamlit run src/modules/vitalia/admin/app.py
      --server.port=8501
      --server.address=0.0.0.0
      --browser.gatherUsageStats=false"
    deploy:
      resources:
        limits:
          memory: 512M
```

Container reuses `vitalia_backend_venv` named volume (shared with `vitalia_backend_dev`). Hot-reload via Streamlit's built-in file watcher (NOT uvicorn --reload).

## § 6 — Makefile target

```makefile
# Append to .PHONY block:
.PHONY: dev-vitalia-admin dev-vitalia-admin-down

# Append after `dev-vitalia:` target:
dev-vitalia-admin:
	@bash scripts/dev-lock-check.sh vitalia
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml up -d vitalia_admin_dev

dev-vitalia-admin-down:
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml stop vitalia_admin_dev
	$(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml rm -f vitalia_admin_dev
```

## § 7 — .env.dev.template comment

Append to `vitalia/.env.dev.template` antes de la sección `=== Admin Streamlit ===`:

```bash
# ────────────────────────────────────────────────────────────────────
# IMPORTANTE — Single-quote requirement
# ────────────────────────────────────────────────────────────────────
# Valores con caracteres especiales ($, !, espacios, comillas) DEBEN
# ir entre comillas simples '...' (NO dobles "..."):
#   ✅ VITALIA_ADMIN_PASSWORD_HASH='$2b$12$abcdef...'
#   ❌ VITALIA_ADMIN_PASSWORD_HASH="$2b$12$abcdef..."  # bash expande $2b$12$
#   ❌ VITALIA_ADMIN_PASSWORD_HASH=$2b$12$abcdef...    # bash expande $2b$
#
# bcrypt hashes contienen $X$ que bash interpreta como variable substitution.
# Use single quotes para preservar caracteres literales.
# ────────────────────────────────────────────────────────────────────

# === Internal API token (Playwright DB verification helpers) ===
# Token usado por Playwright admin-smoke specs para autenticar contra
# /api/v1/vitalia/admin/db-state + /audit-log endpoints.
# Generar con: openssl rand -hex 32
VITALIA_INTERNAL_API_TOKEN='REPLACE_ME_openssl_rand_hex_32'
```

## § 8 — Playwright admin-smoke project setup

### playwright.config.ts modification

```typescript
// Add new project after 'smoke':
{
  name: "admin-smoke",
  testMatch: [/.*\/e2e\/admin\/.*\.spec\.ts/],
  use: {
    ...devices["Desktop Chrome"],
    baseURL: process.env.E2E_ADMIN_BASE_URL || "http://127.0.0.1:8502",
  },
},
```

### admin_auth.fixture.ts (concept)

```typescript
// vitalia/frontend/e2e/admin/admin_auth.fixture.ts
import { test as base, Page } from "@playwright/test";

type AdminFixtures = {
  authenticatedAdminPage: Page;
};

export const test = base.extend<AdminFixtures>({
  authenticatedAdminPage: async ({ page }, use) => {
    const baseUrl = process.env.E2E_ADMIN_BASE_URL || "http://127.0.0.1:8502";
    const password = process.env.VITALIA_ADMIN_PASSWORD || "";
    if (!password) {
      throw new Error("VITALIA_ADMIN_PASSWORD env var required for admin-smoke");
    }
    await page.goto(baseUrl);
    await page.getByLabel(/Contraseña/i).fill(password);
    await page.getByRole("button", { name: /Ingresar|Entrar/i }).click();
    // Wait for sidebar to appear (post-login state)
    await page.waitForSelector('[data-testid="stSidebar"]', { timeout: 15000 });
    await use(page);
  },
});
export { expect } from "@playwright/test";
```

### utils/db_verify.ts (concept)

```typescript
// vitalia/frontend/e2e/admin/utils/db_verify.ts
import { APIRequestContext } from "@playwright/test";
import { DbStateResponse, AuditLogEntry } from "./types";

const BACKEND_URL = process.env.E2E_BACKEND_URL || "http://127.0.0.1:8002";
const INTERNAL_TOKEN = process.env.VITALIA_INTERNAL_API_TOKEN || "";

export async function getDbState(request: APIRequestContext): Promise<DbStateResponse> {
  const res = await request.get(`${BACKEND_URL}/api/v1/vitalia/admin/db-state`, {
    headers: { "X-Internal-Token": INTERNAL_TOKEN },
  });
  if (!res.ok()) throw new Error(`db-state ${res.status()}: ${await res.text()}`);
  return res.json();
}

export async function getAuditLog(
  request: APIRequestContext,
  opts: { action?: string; sinceMsAgo?: number },
): Promise<AuditLogEntry[]> {
  const params: Record<string, string> = {};
  if (opts.action) params.action = opts.action;
  if (opts.sinceMsAgo) {
    params.since = new Date(Date.now() - opts.sinceMsAgo).toISOString();
  }
  const qs = new URLSearchParams(params).toString();
  const res = await request.get(`${BACKEND_URL}/api/v1/vitalia/admin/audit-log?${qs}`, {
    headers: { "X-Internal-Token": INTERNAL_TOKEN },
  });
  if (!res.ok()) throw new Error(`audit-log ${res.status()}: ${await res.text()}`);
  return res.json();
}
```

### Spec assertions pattern (admin-tenants-crud.spec.ts excerpt)

```typescript
import { test, expect } from "./admin_auth.fixture";
import { getDbState, getAuditLog } from "./utils/db_verify";

test.describe("SC-02 — Admin crea tenant nuevo", () => {
  test("creates tenant via TenantRepository + audit log row", async ({ authenticatedAdminPage: page, request }) => {
    const before = await getDbState(request);
    const sinceMs = Date.now();

    // Navigate to Tenants page via sidebar
    await page.getByRole("link", { name: /Tenants/i }).click();
    await page.getByRole("tab", { name: /Crear nuevo/i }).click();

    // Fill form
    await page.getByLabel(/Nombre/i).fill("Clínica Aurora Dental");
    await page.getByLabel(/Slug/i).fill("aurora-dental-ar");
    await page.getByLabel(/Plan/i).selectOption("clinic");
    await page.getByLabel(/País/i).selectOption("AR");
    await page.getByRole("button", { name: /Crear tenant/i }).click();

    // Assert UI success message
    await expect(page.getByText(/Tenant 'Clínica Aurora Dental' creado correctamente/i)).toBeVisible({ timeout: 10000 });

    // Assert DB row count incremented
    const after = await getDbState(request);
    expect(after.tenants).toBe(before.tenants + 1);

    // Assert audit log row created
    const entries = await getAuditLog(request, { action: "tenant.create", sinceMsAgo: Date.now() - sinceMs + 5000 });
    expect(entries.length).toBeGreaterThan(0);
    expect(entries[0].action).toBe("tenant.create");
    expect(entries[0].resourceType).toBe("tenant");
  });
});
```

## § 9 — Implementation order (T-ticket dependency)

DAG:
```
T-doc-env-template (indep, paralelo)
T-be-add-engine-iam-tables
        ↓ (depends_on: tenants table available)
T-be-apply-pending-migrations
        ↓ (DB ready for engine repos)
T-be-admin-rewrite ─── paralelo ─── T-be-admin-deletion
        ↓ (depends_on: clean admin code consuming engine)
T-be-clinics-extension
        ↓ (depends_on: clinic module operational)
T-infra-admin-service
```

## § 10 — Runtime quality checklist application

Per `references/runtime-quality-checklist.md` (loaded backend-expert):

- ✅ FastAPI `Annotated` deps: `db: Annotated[Session, Depends(get_db)]` para nuevos routes clinic
- ✅ 501 stubs: N/A (no stubs en story)
- ✅ DateTime query parsing: helper `/audit-log?since=...` parsea ISO 8601 strings — usar `datetime | None = Query(None)`
- ✅ SQLA legacy Column handling: engine models usan `Column()` legacy (NO touch). Brand ClinicModel TAMBIÉN usa `Column()` para consistency con engine style — accepted as engine convention (Vitalia hereda SQLA style del engine sin migrar a `mapped_column()` 2.0 idiom). Builder NOTA: si arch fitness gate exige `mapped_column()` cross-codebase, EXEMPT ClinicModel + engine models per existing precedent (engine models lo violan también).
- ✅ Multi-tenant test fixture: existing `vitalia/backend/tests/conftest.py` (verify presence + extend)
- ✅ JSONB shape: `Tenant.config_json` JSONB — admin form serializes `{country, plan_tier}` JSON inline

