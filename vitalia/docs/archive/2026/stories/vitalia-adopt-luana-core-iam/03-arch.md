# 03-arch.md — vitalia-adopt-luana-core-iam (consolidado)

> Brand: vitalia · Story: vitalia-adopt-luana-core-iam
> Architect run on: 2026-05-19 (Opus 4.7, cutoff Jan 2026; no live web research needed — all patterns ya cementados en codebase nicolify + engine luana-core-iam)
> Parent outcome (brand): `vitalia/docs/product/outcomes/admin-iam-adopt.md`
> Parent outcome (platform): `docs/product/outcomes/admin-iam-adoption-platform.md`
> Spec: `vitalia/docs/product/stories/vitalia-adopt-luana-core-iam/01-spec.md`
> Sub-arch BE detail: `03-arch-be.md`

## § 0 — Context Summary

### Surface → builder → auditor mapping

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/backend/alembic/versions/{022,023}_*.py` (migrations) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/backend/src/modules/vitalia/admin/{modules,app.py,_shared}/` (Streamlit rewrite + DELETE phantom) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/backend/src/modules/vitalia/clinics/{domain,infrastructure,application,api}/` (NEW DDD module) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/backend/tests/{modules/vitalia/{admin,clinics},integration,architecture}/` (NEW + UPDATED) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/docker-compose.dev.yml` + Makefile + `.env.dev.template` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| `vitalia/frontend/e2e/admin/*.spec.ts` + `playwright.config.ts` (admin-smoke project) | `builder-backend` (Sonnet — TS specs son testing infra, no FE feature) | `auditor-backend` (Opus) |

NO surface FE (Next.js src/) — admin es Streamlit puro. NO surface agentic.

### Skills consulted

- **`backend-expert`** — DDD Inside-Out (Domain → Infra → App → API), arch fitness, native commands, Pydantic v2 + SQLA 2.0
- **`brand-expert` / `offer-expert`** — N/A (story sin brand/offer touchpoints)
- **`copilot-expert` / `sales-agent-expert`** — N/A (story sin agentic)
- **`vitalia/.claude/rules/hipaa-lite.md`** — dual filter `(tenant_id, clinic_id)` obligatorio + audit log sync write + sanitization payload + RBAC strict
- **`.claude/rules/anti-duplication.md`** — § Engine boundary read-only (cero edits `core/luana-core-iam/src/`) + schema-mirror exception per `backend-ddd.md`
- **`.claude/rules/backend-ddd.md`** § Schema-mirror exception — builder-backend MAY mirror engine migration DDL en migration brand-local (justifica migration 022 + 023)
- **`.claude/rules/auditor-downstream-regression.md`** — schema-mirror engine tables NO requiere promotion proposal (NO se modifica engine — solo se ejecuta DDL en brand DB)

### CONTEXT-BRIEF source

- Self-ran greps (Path B fallback — story chica, brief skipped; spec.md ya muy denso)
- Cross-module audit ejecutado abajo en §13

### Capability YAML files affected (post-merge updates required)

- `vitalia/docs/product/capabilities/admin/tenants-crud.yaml` (NEW)
- `vitalia/docs/product/capabilities/admin/users-crud.yaml` (NEW)
- `vitalia/docs/product/capabilities/admin/clinics-crud.yaml` (NEW)
- `vitalia/docs/product/capabilities/iam/luana-core-iam-adoption.yaml` (NEW)
- `vitalia/docs/product/capabilities/clinics/clinic-management.yaml` (NEW)
- `vitalia/docs/product/modules/admin.md` (UPDATE auto-list)
- `vitalia/docs/product/modules/iam.md` (NEW or UPDATE auto-list)
- `vitalia/docs/product/modules/clinics.md` (NEW)

### Architecture gates that must keep passing

- `vitalia/backend/tests/architecture/test_phi_dual_filter.py` (existing — extender allowlist con ClinicRepository)
- `vitalia/backend/tests/architecture/test_audit_log_sync_write.py` (existing — verificar admin rewrite cumple sync write)
- `vitalia/backend/tests/architecture/test_no_legacy_paths.py` (existing — bloquear references a tablas phantom)
- `vitalia/backend/tests/architecture/test_vitalia_no_query_without_tenant_filter.py` (existing — clinics queries deben filtrar tenant_id)
- `vitalia/backend/tests/architecture/test_migrations_idempotent.py` (existing — migrations 022 + 023 idempotent)
- NEW: `vitalia/backend/tests/architecture/test_admin_no_raw_sql.py` (admin/modules/{tenants,users}.py cero `session.execute(...SELECT|INSERT|UPDATE|DELETE...)`)
- NEW: `vitalia/backend/tests/architecture/test_admin_consumes_engine_repos.py` (admin/modules/{tenants,users}.py import desde `luana_core_iam.infrastructure.repositories`)
- NEW: `vitalia/backend/tests/architecture/test_clinics_domain_no_engine_imports.py` (clinics/domain/ NO importa luana_core_iam — domain layer pure)
- NEW: `vitalia/backend/tests/architecture/test_phantom_tables_zero_refs.py` (grep cero references a `vitalia_user_profiles`, `vitalia_tenants` en admin/)

## § 1 — Decisión arquitectónica (resumen)

Esta story implementa las 5 decisiones cementadas en parent platform outcome:

| # | Decisión | Aplicación vitalia |
|---|---|---|
| D1 | Brand consume engine `luana-core-iam` sin reinventar | Migration 022 ejecuta CREATE TABLE users/tenants/user_tenants matching engine ORM models (schema-mirror exception). Admin rewrite consume `UserRepository`/`TenantRepository`/`UserTenantRepository`. |
| D2 | `clinic` = brand-extension vitalia | Migration 023 CREATE TABLE `vitalia_clinics` FK → tenants(id). DDD module `vitalia/backend/src/modules/vitalia/clinics/` con ClinicRepository. NO engine touch. |
| D3 | Nicolify hardcodes purgados (DONE) | Pre-requisite migrated en main commits b869eaf + 39b73703. Story 022 NO depende. |
| D4 | Admin Streamlit per-brand port 8502 | Service `vitalia_admin_dev` en `vitalia/docker-compose.dev.yml`. Makefile target `dev-vitalia-admin`. |
| D5 | Admin = super-CRUD Chris only, bcrypt auth | Existing `_shared/auth.py::verify_admin_password` reusado. NO Clerk. |

### Engine boundary CRITICAL

- ✅ CONSUME `from luana_core_iam.infrastructure.repositories import UserRepository, TenantRepository, UserTenantRepository`
- ✅ CONSUME `from luana_core_iam.domain.{user,tenant} import User, Tenant`
- ❌ NO touch `core/luana-core-iam/src/` (engine read-only — schema-mirror exception aplica solo a migration DDL en `{brand}/backend/alembic/versions/`)
- ❌ NO promotion proposal needed (engine no se modifica)

## § 2 — Domain entities (NEW — clinics module only)

### Clinic (Pydantic v2)

```python
# vitalia/backend/src/modules/vitalia/clinics/domain/clinic.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class Clinic(BaseModel):
    """Vitalia brand-extension Clinic entity (sub-unit organizacional under Tenant).

    HIPAA-lite invariant: All PHI queries downstream MUST filter by (tenant_id, clinic_id).
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID                          # FK → tenants(id) engine
    name: str
    address: str | None = None
    timezone: str = "UTC"                    # default UTC, override per-clinic
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None       # soft delete
```

NO PHI fields in Clinic entity. Identity-only (name, address, timezone). PHI fields se introducen en futuras tablas `patients`, `treatments`, etc. con dual filter enforced via `@require_clinic_access`.

### NO domain changes en User / Tenant / UserTenant

Story consume engine domain models verbatim. Cero edits a `core/luana-core-iam/src/luana_core_iam/domain/`.

## § 3 — SQLAlchemy 2.0 Models

### Engine mirror models (NO created in brand — already exist in engine)

`core/luana-core-iam/src/luana_core_iam/infrastructure/models/{user,tenant,user_tenant}_model.py` — used directly via `from luana_core_iam.infrastructure.models import UserModel, TenantModel, UserTenantModel`.

Migration 022 ejecuta DDL matching engine ORM schema (verbatim desde nicolify 001:2210-2300). NO duplicar SQLAlchemy model declarations en `vitalia/backend/src/`.

### ClinicModel (NEW — brand-local)

```python
# vitalia/backend/src/modules/vitalia/clinics/infrastructure/models/clinic_model.py
import uuid
from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class ClinicModel(Base):
    """Vitalia brand-extension: clinic (multi-sede under tenant)."""

    __tablename__ = "vitalia_clinics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    timezone = Column(String(64), server_default="UTC", nullable=False)
    is_active = Column(Boolean, default=True, server_default="true", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # soft delete
```

Index plan:
- `ix_vitalia_clinics_tenant_id` (multi-tenant queries)
- `ix_vitalia_clinics_tenant_active` (compound `tenant_id, is_active` for active list filter)
- `uq_vitalia_clinics_tenant_name` (unique `tenant_id, name` — no duplicate clinic names per tenant)

## § 4 — Pydantic v2 DTOs (clinics module)

```python
# vitalia/backend/src/modules/vitalia/clinics/api/dtos.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ClinicCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    tenant_id: UUID
    name: str
    address: str | None = None
    timezone: str = "UTC"


class ClinicUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    name: str | None = None
    address: str | None = None
    timezone: str | None = None
    is_active: bool | None = None


class ClinicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    name: str
    address: str | None
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
```

## § 5 — API Routes (clinics module + admin helper endpoints for Playwright DB verify)

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| POST | `/api/v1/vitalia/clinics` | Bearer + X-Tenant-ID | ClinicCreate | ClinicResponse | Create clinic under tenant (dual-filter enforced) |
| GET | `/api/v1/vitalia/clinics` | Bearer + X-Tenant-ID | — | list[ClinicResponse] | List clinics for current tenant |
| GET | `/api/v1/vitalia/clinics/{clinic_id}` | Bearer + X-Tenant-ID | — | ClinicResponse | Get clinic (dual filter `tenant_id + clinic_id`) |
| PATCH | `/api/v1/vitalia/clinics/{clinic_id}` | Bearer + X-Tenant-ID | ClinicUpdate | ClinicResponse | Update clinic |
| DELETE | `/api/v1/vitalia/clinics/{clinic_id}` | Bearer + X-Tenant-ID | — | None (204) | Soft delete (`deleted_at = NOW()`) |
| GET | `/api/v1/vitalia/admin/db-state` | Internal token | — | DbStateResponse | **Test-only helper**: returns row counts (tenants, users, user_tenants, clinics) for Playwright DB verify. NO PHI exposed. |
| GET | `/api/v1/vitalia/admin/audit-log` | Internal token | — | list[AuditLogEntry] | **Test-only helper**: GET audit log entries filtered by `action` + `since` query params. Sanitized payload returned. |

`/api/v1/vitalia/admin/*` endpoints son helpers exclusivos para Playwright DB state verification. Guarded by `X-Internal-Token` header matching `VITALIA_INTERNAL_API_TOKEN` env var. NO accesible desde Streamlit UI ni internet público.

`FastAPI(redirect_slashes=False)` ya cementado en `vitalia/backend/src/main.py`.

## § 6 — TypeScript Types (Playwright specs only — NO Next.js feature)

```ts
// vitalia/frontend/e2e/admin/utils/types.ts
export interface DbStateResponse {
  tenants: number;
  users: number;
  userTenants: number;
  clinics: number;
}

export interface AuditLogEntry {
  id: string;
  tenantId: string | null;
  clinicId: string | null;
  userId: string;
  action: string;
  resourceType: string;
  resourceId: string | null;
  occurredAt: string;
}
```

## § 7 — Repository Interfaces

### Engine repositories (consumed via import, NO touch)

- `UserRepository(db: Session)` — `get_by_id` / `get_by_email` / `get_by_clerk_id` / `create` / `update` (existing engine)
- `TenantRepository(db: Session)` — `get_by_id` / `get_by_slug` / `get_all` / `create` / `update` (existing engine)
- `UserTenantRepository(db: Session)` — `get_tenants_for_user` (existing engine)

### NEW brand-local repository

```python
# vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/clinic_repository.py
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from vitalia.modules.vitalia.clinics.domain.clinic import Clinic
from vitalia.modules.vitalia.clinics.infrastructure.models.clinic_model import ClinicModel


class ClinicRepository:
    """Vitalia clinic repository — sync (Streamlit-compatible) + async paths.

    HIPAA-lite invariant: ALL queries MUST filter tenant_id (dual filter
    becomes (tenant_id, clinic_id) when downstream PHI tables hit).
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, tenant_id: UUID, clinic_id: UUID) -> Clinic | None:
        """Get clinic by id under tenant scope (tenant filter mandatory)."""
        model = self.db.execute(
            select(ClinicModel)
            .where(ClinicModel.tenant_id == tenant_id)
            .where(ClinicModel.id == clinic_id)
            .where(ClinicModel.deleted_at.is_(None))
        ).scalars().first()
        return Clinic.model_validate(model) if model else None

    def list_for_tenant(self, tenant_id: UUID, active_only: bool = True) -> list[Clinic]:
        """List clinics for tenant."""
        stmt = select(ClinicModel).where(ClinicModel.tenant_id == tenant_id)
        if active_only:
            stmt = stmt.where(ClinicModel.is_active.is_(True))
        stmt = stmt.where(ClinicModel.deleted_at.is_(None)).order_by(ClinicModel.created_at.desc())
        models = self.db.execute(stmt).scalars().all()
        return [Clinic.model_validate(m) for m in models]

    def create(self, clinic: Clinic) -> Clinic:
        db_clinic = ClinicModel(
            id=clinic.id,
            tenant_id=clinic.tenant_id,
            name=clinic.name,
            address=clinic.address,
            timezone=clinic.timezone,
            is_active=clinic.is_active,
        )
        self.db.add(db_clinic)
        self.db.commit()
        self.db.refresh(db_clinic)
        return Clinic.model_validate(db_clinic)

    def update(self, tenant_id: UUID, clinic: Clinic) -> Clinic:
        db_clinic = self.db.execute(
            select(ClinicModel)
            .where(ClinicModel.tenant_id == tenant_id)
            .where(ClinicModel.id == clinic.id)
        ).scalars().first()
        if db_clinic:
            db_clinic.name = clinic.name
            db_clinic.address = clinic.address
            db_clinic.timezone = clinic.timezone
            db_clinic.is_active = clinic.is_active
            self.db.commit()
            self.db.refresh(db_clinic)
            return Clinic.model_validate(db_clinic)
        return clinic

    def soft_delete(self, tenant_id: UUID, clinic_id: UUID) -> bool:
        from datetime import datetime, timezone as tz
        db_clinic = self.db.execute(
            select(ClinicModel)
            .where(ClinicModel.tenant_id == tenant_id)
            .where(ClinicModel.id == clinic_id)
        ).scalars().first()
        if not db_clinic:
            return False
        db_clinic.deleted_at = datetime.now(tz=tz.utc)
        db_clinic.is_active = False
        self.db.commit()
        return True
```

`get_by_id` recibe `tenant_id` + `clinic_id` (mandatory dual filter argument). Async variant (futuro) misma signature.

## § 8 — Application Services + Audit log helper

### ClinicService (brand-local)

```python
# vitalia/backend/src/modules/vitalia/clinics/application/clinic_service.py
import uuid
from uuid import UUID

from vitalia.modules.vitalia.clinics.domain.clinic import Clinic
from vitalia.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import ClinicRepository
from vitalia.modules.vitalia.audit.audit_writer import write_audit_log_sync  # NEW helper §8.2


class ClinicService:
    def __init__(self, repo: ClinicRepository) -> None:
        self.repo = repo

    def create_clinic(
        self,
        tenant_id: UUID,
        actor_user_id: UUID,
        name: str,
        address: str | None,
        timezone: str = "UTC",
    ) -> Clinic:
        """Create clinic + write audit log SYNC before return."""
        clinic = Clinic(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=name,
            address=address,
            timezone=timezone,
        )
        created = self.repo.create(clinic)

        # AUDIT LOG sync write — HIPAA-lite invariant
        write_audit_log_sync(
            db=self.repo.db,
            tenant_id=tenant_id,
            clinic_id=created.id,
            user_id=actor_user_id,
            action="clinic.create",
            resource_type="clinic",
            resource_id=created.id,
            payload={"name": name, "timezone": timezone},  # NO PHI
        )
        return created
```

### audit_writer helper (NEW shared utility)

```python
# vitalia/backend/src/modules/vitalia/audit/audit_writer.py
import json
from datetime import datetime, timezone as tz
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from luana_core_observability.recording.sanitization import sanitize_payload  # engine helper


def write_audit_log_sync(
    db: Session,
    *,
    tenant_id: UUID,
    clinic_id: UUID | None,
    user_id: UUID,
    action: str,
    resource_type: str,
    resource_id: UUID | None,
    payload: dict[str, Any] | None = None,
    from_ip: str | None = None,
    user_agent: str = "VitaliaAdmin/1.0",
) -> None:
    """Write SYNC row to vitalia_audit_log. MUST be called before action return.

    HIPAA-lite invariant: NO PHI in payload. Caller responsibility to sanitize.
    Function applies sanitize_payload as defense in depth.
    """
    safe_payload = sanitize_payload(payload or {}, compliance_level="hipaa_lite")
    payload_bytes = json.dumps(safe_payload, default=str, ensure_ascii=False).encode("utf-8")

    db.execute(
        text("""
            INSERT INTO vitalia_audit_log (
                id, tenant_id, clinic_id, user_id, action, resource_type,
                resource_id, from_ip, user_agent, payload_redacted, occurred_at
            ) VALUES (
                gen_random_uuid(), :tenant_id, :clinic_id, :user_id, :action,
                :resource_type, :resource_id, :from_ip, :user_agent, :payload, NOW()
            )
        """),
        {
            "tenant_id": str(tenant_id),
            "clinic_id": str(clinic_id) if clinic_id else None,
            "user_id": str(user_id),
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "from_ip": from_ip,
            "user_agent": user_agent,
            "payload": payload_bytes,
        },
    )
    db.commit()
```

`vitalia/backend/src/modules/vitalia/audit/audit_writer.py` reemplaza `_encode_payload` + inline INSERTs en phantom admin/modules/. SSoT único de audit log writes.

### `@require_clinic_access` decorator (NEW, FastAPI)

```python
# vitalia/backend/src/modules/vitalia/clinics/api/decorators.py
from functools import wraps
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from luana_core_iam.api.dependencies import get_current_user, get_current_tenant_id
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from vitalia.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import ClinicRepository
from vitalia.modules.vitalia.audit.audit_writer import write_audit_log_sync


def require_clinic_access(clinic_id_from: str = "path"):
    """Decorator FastAPI route — verifies user has scope to clinic_id passed.

    Args:
        clinic_id_from: 'path' (from URL param) | 'query' | 'body'

    Behavior:
        - Reads clinic_id from request (path|query|body) per arg
        - Resolves user.clinic_assignments (future table user_clinics M:N for vitalia)
          For story scope: simplest verify user_tenants row exists for (user_id, tenant_id)
          + clinic.tenant_id == tenant_id (single-clinic-per-user MVP gate)
        - Mismatch → HTTP 403 + audit_log row action='phi.access_denied'
        - Match → continue
    """
    # impl detalle en builder phase — pseudocódigo aquí.
    ...
```

Por simplicidad MVP story: decorator verifica `clinic.tenant_id == X-Tenant-ID` (tenant scope) + futuro extender a `user_clinics` M:N cuando se introduzca PHI tables. SC-10 cubre tenant mismatch como surrogate de cross-clinic block.

## § 9 — Migration Notes

### Migration 022_vitalia_add_engine_iam_tables.py (NEW)

```python
"""Vitalia migration 022 — add engine IAM tables (users, tenants, user_tenants).

Per platform outcome admin-iam-adoption-platform D1: each brand executes DDL
matching engine luana_core_iam ORM models (schema-mirror exception per
.claude/rules/backend-ddd.md). Engine OWNS the SSoT; brand executes CREATE TABLE.

Schema sourced verbatim from nicolify/backend/alembic/versions/001_initial_snapshot.py:2210-2300
(proven canonical, auditable cross-brand).

Idempotent: CREATE TABLE IF NOT EXISTS / ALTER TABLE ADD COLUMN IF NOT EXISTS.

Revision ID: 022_vitalia
Revises: 021_vitalia
Create Date: 2026-05-19
"""

from alembic import op

revision = "022_vitalia"
down_revision = "021_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── tenants (engine SSoT) ─────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.tenants (
            id uuid NOT NULL,
            name character varying NOT NULL,
            slug character varying NOT NULL,
            config_json jsonb,
            is_active boolean,
            created_at timestamp with time zone DEFAULT now(),
            updated_at timestamp with time zone,
            gemini_api_key character varying,
            can_use_platform_keys boolean DEFAULT false,
            webhook_secret character varying,
            clerk_org_id character varying,
            default_currency character varying DEFAULT 'USD'::character varying,
            timezone character varying DEFAULT 'UTC'::character varying,
            extraction_priority integer DEFAULT 0 NOT NULL,
            tracking_config jsonb DEFAULT '{}'::jsonb,
            weekly_start_day integer DEFAULT 0,
            fiscal_year_start_month integer DEFAULT 1,
            fiscal_year_start_day integer DEFAULT 1,
            CONSTRAINT pk_tenants PRIMARY KEY (id)
        );
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_tenants_slug ON public.tenants(slug);")

    # ── users (engine SSoT) ───────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.users (
            id uuid NOT NULL,
            full_name character varying,
            email character varying NOT NULL,
            phone character varying,
            role character varying,
            is_active boolean,
            created_at timestamp with time zone DEFAULT now(),
            updated_at timestamp with time zone,
            clerk_id character varying,
            CONSTRAINT pk_users PRIMARY KEY (id)
        );
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON public.users(email);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_clerk_id ON public.users(clerk_id);")

    # ── user_tenants (engine M:N) ─────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.user_tenants (
            user_id uuid NOT NULL,
            tenant_id uuid NOT NULL,
            role character varying,
            created_at timestamp with time zone DEFAULT now(),
            is_active boolean DEFAULT true NOT NULL,
            CONSTRAINT pk_user_tenants PRIMARY KEY (user_id, tenant_id),
            CONSTRAINT fk_user_tenants_user FOREIGN KEY (user_id) REFERENCES public.users(id),
            CONSTRAINT fk_user_tenants_tenant FOREIGN KEY (tenant_id) REFERENCES public.tenants(id)
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.user_tenants;")
    op.execute("DROP TABLE IF EXISTS public.users;")
    op.execute("DROP TABLE IF EXISTS public.tenants;")
```

**Crítico**: migration 014_vitalia_tenants_columns.py (ALTER TABLE tenants ADD COLUMN ...) ahora será aplicable porque tenants table existe post-022. Cuando `alembic upgrade head` corre 022 antes de 014, el ALTER funciona.

NOTA importante revision chain: 022 down_revision=021_vitalia. 014 ya existe entre 013 y 015 con down_revision=013_vitalia. Como 022 viene DESPUÉS de 014 en la chain, 014 corre con DB en estado pre-022 (NO existe tabla tenants). El fix correcto: **022 debe insertarse BEFORE 014 en chain** O **el 014 ALTER es idempotent con IF NOT EXISTS** (ya lo es per inspection).

Solución pragmática: 022 viene después de 021 (head). 014 ya usa `ALTER TABLE tenants ADD COLUMN IF NOT EXISTS ...`. Cuando se aplica 014 en orden, FAILS porque tenants no existe. SOLUCIÓN: refactorizar 014 a usar `DO $$ BEGIN ... EXCEPTION WHEN undefined_table THEN NULL; END $$;` (skip silenciosamente si tabla no existe), Y luego 022 aplica CREATE TABLE tenants (con todos los campos incluyendo los de 014: `is_onboarded, location_country, location_city, timezone`). Ver `03-arch-be.md` § Migration ordering strategy para detalles.

Alternativa más limpia: agregar campos `is_onboarded, location_country, location_city, timezone` directo a 022 CREATE TABLE (matching state final), y refactor 014 a no-op IF EXISTS / o leave 014 idempotent guarded por table_exists check.

**Decisión arquitectural**: 022 incluye los 4 campos de 014 en el CREATE TABLE inicial. 014 se modifica a guard `DO $$ BEGIN ... EXCEPTION WHEN undefined_table THEN RAISE NOTICE 'skipped 014: tenants missing — applied by 022 instead'; END $$;` (per .claude/rules/backend-migrations.md). Builder ejecuta este refactor como parte de T-be-add-engine-iam-tables.

### Migration 023_vitalia_clinics.py (NEW)

```python
"""Vitalia migration 023 — vitalia_clinics brand-extension table.

Brand-extension sub-unit organizacional. FK to engine tenants(id).
Per platform outcome admin-iam-adoption-platform D2: clinic is brand-local
(NOT engine). Future EP-19 lift triggered when 2nd brand replicates pattern.

Idempotent. HIPAA-lite: NO PHI columns here (identity only).

Revision ID: 023_vitalia
Revises: 022_vitalia
Create Date: 2026-05-19
"""

from alembic import op

revision = "023_vitalia"
down_revision = "022_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_clinics (
            id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID         NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            name            VARCHAR(255) NOT NULL,
            address         VARCHAR(500),
            timezone        VARCHAR(64)  NOT NULL DEFAULT 'UTC',
            is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ,
            deleted_at      TIMESTAMPTZ
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_clinics_tenant_id ON vitalia_clinics(tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_clinics_tenant_active ON vitalia_clinics(tenant_id, is_active) WHERE deleted_at IS NULL;")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_clinics_tenant_name ON vitalia_clinics(tenant_id, name) WHERE deleted_at IS NULL;")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_vitalia_clinics_tenant_name;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_clinics_tenant_active;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_clinics_tenant_id;")
    op.execute("DROP TABLE IF EXISTS vitalia_clinics;")
```

### Prod-clone test command (dev iteration)

```bash
WS=$(git rev-parse --show-toplevel)
docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev -c "DROP TABLE IF EXISTS vitalia_clinics CASCADE; DROP TABLE IF EXISTS user_tenants CASCADE; DROP TABLE IF EXISTS users CASCADE; DROP TABLE IF EXISTS tenants CASCADE;"
docker exec luana-dev-vitalia_backend_dev-1 alembic stamp 021_vitalia
docker exec luana-dev-vitalia_backend_dev-1 alembic upgrade head
docker exec luana-dev-vitalia_backend_dev-1 alembic current  # → 023_vitalia
```

## § 9.5 — Tests audit (default flip — N/A)

[x] **No aplica** — CONTRACT no flipea defaults side-effect (no feature flags `USE_*_PATTERN_*`, `LITELLM_PROXY_ENABLED`, etc.). Story es migration + admin rewrite + clinics module + infra setup, NO toca side-effect call paths existentes.

## § 10 — File Structure

### NEW files

```
vitalia/backend/alembic/versions/
├── 022_vitalia_add_engine_iam_tables.py     [NEW migration]
└── 023_vitalia_clinics.py                    [NEW migration]

vitalia/backend/src/modules/vitalia/clinics/                                 [NEW DDD module]
├── __init__.py
├── domain/
│   ├── __init__.py
│   └── clinic.py                              [Pydantic v2 Clinic entity]
├── infrastructure/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── clinic_model.py                    [SQLA 2.0 ClinicModel]
│   └── repositories/
│       ├── __init__.py
│       └── clinic_repository.py               [ClinicRepository sync+async]
├── application/
│   ├── __init__.py
│   └── clinic_service.py                      [ClinicService — orchestrator + audit_log writes]
└── api/
    ├── __init__.py
    ├── dtos.py                                [ClinicCreate, ClinicUpdate, ClinicResponse]
    ├── decorators.py                          [@require_clinic_access]
    └── router.py                              [FastAPI routes /api/v1/vitalia/clinics]

vitalia/backend/src/modules/vitalia/audit/                                    [NEW SHARED helper module]
├── __init__.py
└── audit_writer.py                            [write_audit_log_sync helper SSoT]

vitalia/backend/src/modules/vitalia/admin/modules/
└── clinics.py                                 [NEW admin page — clinic CRUD via ClinicService]

vitalia/backend/src/modules/vitalia/admin/pages/
└── clinicas.py                                [NEW thin wrapper Streamlit page]

vitalia/backend/src/modules/vitalia/admin/api/                                [NEW test-only helper endpoints]
├── __init__.py
└── admin_helpers_router.py                    [/api/v1/vitalia/admin/db-state + /audit-log]

vitalia/backend/tests/modules/vitalia/admin/                                   [NEW]
├── __init__.py
├── test_tenants_crud.py                       [unit SC-02, SC-03, SC-07]
├── test_users_crud.py                         [unit SC-04, SC-05, SC-06]
├── test_clinics_admin.py                      [unit SC-08]
└── test_audit_log_sync.py                     [unit audit_writer]

vitalia/backend/tests/modules/vitalia/clinics/                                 [NEW]
├── __init__.py
├── test_clinic_repository.py                  [unit dual filter]
├── test_clinic_service.py                     [unit SC-08]
└── test_require_clinic_access.py              [unit SC-09, SC-10, SC-11]

vitalia/backend/tests/integration/                                             [NEW]
├── __init__.py
└── test_alembic_head.py                       [SC-14 — upgrade 001→023 verifica tables exist]

vitalia/backend/tests/architecture/                                            [NEW arch fitness tests]
├── test_admin_no_raw_sql.py                   [no session.execute SQL crudo in admin/modules/{tenants,users}.py]
├── test_admin_consumes_engine_repos.py        [admin imports luana_core_iam.infrastructure.repositories]
├── test_clinics_domain_no_engine_imports.py   [clinics/domain/ no importa luana_core_iam]
└── test_phantom_tables_zero_refs.py           [grep vitalia_user_profiles + vitalia_tenants → 0 hits]

vitalia/frontend/e2e/admin/                                                    [NEW Playwright admin-smoke specs]
├── admin_auth.fixture.ts                      [bcrypt session cookie injection custom]
├── utils/
│   ├── db_verify.ts                           [helpers POST /db-state + /audit-log]
│   └── types.ts                               [TS mirror DTOs]
├── admin-login.spec.ts                        [SC-01 + SC-12]
├── admin-tenants-crud.spec.ts                 [SC-02 + SC-03 + SC-07]
├── admin-users-crud.spec.ts                   [SC-04 + SC-05 + SC-06]
├── admin-clinics-extension.spec.ts            [SC-08 + SC-13]
└── admin-hipaa-dual-filter.spec.ts            [SC-09 + SC-10 + SC-11]
```

### MODIFIED files

```
vitalia/backend/alembic/versions/
└── 014_vitalia_tenants_columns.py            [MODIFY: guard ALTER en DO $$ BEGIN ... EXCEPTION WHEN undefined_table THEN RAISE NOTICE; END $$]

vitalia/backend/src/modules/vitalia/admin/
├── app.py                                     [MODIFY: PAGE_SPECS add Clinicas page; sidebar Salir button]
├── modules/
│   ├── tenants.py                             [REWRITE COMPLETO — DELETE phantom SQL, USE TenantRepository]
│   └── users.py                               [REWRITE COMPLETO — DELETE phantom SQL, USE UserRepository + UserTenantRepository]

vitalia/backend/src/main.py                    [REGISTER clinics router + admin_helpers router]

vitalia/docker-compose.dev.yml                 [ADD vitalia_admin_dev service port 8502]
vitalia/.env.dev.template                       [ADD comment re single-quote requirement + VITALIA_INTERNAL_API_TOKEN]
vitalia/frontend/playwright.config.ts           [ADD admin-smoke project]
Makefile                                       [ADD dev-vitalia-admin target]
```

### DELETED files

```
NINGUNO. Rewrite es modificación de archivos existentes con cero deuda residual
(per directiva Chris). Files admin/modules/{tenants,users}.py se reescriben in-place.
```

## § 11 — Cross-Cutting Concerns

- **Tenant isolation** — Every clinic query filters `tenant_id` (incl. `get_by_id`). Engine repos (User/Tenant/UserTenant) consumed as-is per engine contracts. Admin operates over global engine tables (no tenant filter on tenants/users/user_tenants listing — admin is platform-level).
- **HIPAA dual filter** — Clinic table NOT PHI (identity only), but introduces `tenant_id + clinic_id` pattern. `@require_clinic_access` decorator es scaffold para futuros endpoints `/patients`, `/treatments`. Test arch fitness existing (`test_phi_dual_filter.py`) cubre cuando PHI tables se introduzcan.
- **Currency** — N/A (story sin monetary fields user-facing — tenants.default_currency es campo existente engine, NO touched).
- **Master data** — `DateTime(timezone=True)` en ClinicModel. Store UTC. `timezone` column per-clinic for display logic future.
- **Spanish neutro LatAm** — UI strings tabla canónica en spec § 5 (tuteo, sin voseo).
- **PII / PHI** — `response_model=` en TODA route. Audit log payload sanitized via `sanitize_payload(payload, compliance_level="hipaa_lite")`. Admin maneja identity-only (email, slug, name) — NO PHI fields. Admin helper endpoints `/admin/db-state` returns COUNTS only, NO row content.
- **Native-first dev** — lint/tests run native Linux (host): `cd vitalia/backend && ${WS}/.venv/bin/ruff check src/ tests/`, `${WS}/.venv/bin/pytest tests/`. Docker only for runtime + alembic.

## § 12 — Architecture Fitness Impact

### Gates que MUST keep passing

| Test file | Aplicación a esta story |
|---|---|
| `test_phi_dual_filter.py` | Existente — extender PHI_ORM_MODELS si futuro PHI table introducida en clinics module (no aplica MVP) |
| `test_audit_log_sync_write.py` | Existente — verificar audit_writer.write_audit_log_sync usado en admin + clinics services |
| `test_no_legacy_paths.py` | Existente — agregar guard: vitalia_user_profiles + vitalia_tenants → 0 hits |
| `test_vitalia_no_query_without_tenant_filter.py` | Existente — clinics queries deben filtrar tenant_id |
| `test_migrations_idempotent.py` | Existente — 022 + 023 deben pasar idempotency check |

### NEW gates introducidos

| Test file | Allowlist Strategy |
|---|---|
| `test_admin_no_raw_sql.py` | No allowlist — admin/modules/{tenants,users,clinics}.py CERO `session.execute(...SELECT|INSERT|UPDATE|DELETE...)`. Admin helper router (admin_helpers_router.py) EXEMPT — son thin helpers para Playwright DB verify, no business logic. |
| `test_admin_consumes_engine_repos.py` | admin/modules/{tenants,users}.py MUST `from luana_core_iam.infrastructure.repositories import ...` |
| `test_clinics_domain_no_engine_imports.py` | clinics/domain/clinic.py CERO `from luana_core_iam` (domain pure) |
| `test_phantom_tables_zero_refs.py` | Shrink-only allowlist initially empty. Future: si Streamlit usa string literal "vitalia_clinics" en non-SQL context (display label), permitido en clinics.py file only. |

## § 13 — Existing systems audit (NO NEW LAYER rule)

### Source of evidence

- [x] Self-run greps (Path B — fallback, no CONTEXT-BRIEF generated since story chica)

### Audit cross-module ejecutado

```bash
# 1. Engine IAM ya define modelos User/Tenant/UserTenant
grep -rn "class UserModel\|class TenantModel\|class UserTenantModel" core/luana-core-iam/src/
# → core/luana-core-iam/src/luana_core_iam/infrastructure/models/{user,tenant,user_tenant}_model.py

# 2. Engine IAM ya define repositories
grep -rn "class UserRepository\|class TenantRepository\|class UserTenantRepository" core/luana-core-iam/src/
# → core/luana-core-iam/src/luana_core_iam/infrastructure/repositories/{user,tenant,user_tenant}_repository.py

# 3. Cross-brand mirror check (clinic concept)
for B in nicolify comunify lupulo; do
  find ${WS}/$B/backend/src -path "*/clinics/*" 2>/dev/null
done
# → CERO hits. Clinic concept es brand-local vitalia.

# 4. Verify NO core/luana-core-clinics existe
ls ${WS}/core/luana-core-clinics 2>/dev/null
# → No such directory. Clinic NO existe en engine (correcto per D2).

# 5. Verify shared audit log helper existe en engine observability
grep -rn "sanitize_payload" core/luana-core-observability/src/
# → core/luana-core-observability/src/luana_core_observability/recording/sanitization.py::sanitize_payload (engine SSoT)

# 6. Verify admin code phantom estado actual
grep -n "vitalia_user_profiles\|vitalia_clinics\|vitalia_tenants" vitalia/backend/src/modules/vitalia/admin/modules/
# → ~30 hits a tablas phantom — SE ELIMINAN en rewrite
```

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| Engine IAM models | `core/luana-core-iam/src/luana_core_iam/infrastructure/models/` | active | **CONSUME** via import (D1 verbatim) |
| Engine IAM repos | `core/luana-core-iam/src/luana_core_iam/infrastructure/repositories/` | active | **CONSUME** via import (D1 verbatim) |
| Engine IAM domain | `core/luana-core-iam/src/luana_core_iam/domain/{user,tenant}.py` | active | **CONSUME** via import |
| Engine observability sanitization | `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py` | active | **CONSUME** `sanitize_payload(...)` |
| Vitalia audit_log table + indexes | `vitalia/backend/alembic/versions/013_vitalia_audit_log.py` | active | **CONSUME** verbatim (no schema change, ya partitioned 2026-04..08) |
| Vitalia admin auth bcrypt | `vitalia/backend/src/modules/vitalia/admin/_shared/auth.py` | active | **CONSUME** verbatim |
| Vitalia admin sync DB session | `vitalia/backend/src/modules/vitalia/admin/_shared/db.py` | active | **CONSUME** verbatim (already wraps luana_core_platform.core.database.SessionLocal) |
| Admin tenants.py phantom code | `vitalia/backend/src/modules/vitalia/admin/modules/tenants.py` | broken (phantom tables) | **REWRITE** consumiendo TenantRepository |
| Admin users.py phantom code | `vitalia/backend/src/modules/vitalia/admin/modules/users.py` | broken (phantom tables) | **REWRITE** consumiendo UserRepository + UserTenantRepository |
| Vitalia clinics module | NONEXISTENT | — | **NEW** — DDD scaffold (per D2 brand-extension) |
| Audit log helper SSoT | NONEXISTENT (admin modules tienen inline INSERT) | — | **NEW** — `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` SSoT |

### Decisión por sistema

- **Engine IAM (models/repos/domain)** (paths arriba): EXTEND/CONSUME via import. NO touch engine. Schema-mirror exception aplica solo a migration DDL en `vitalia/backend/alembic/`.
- **Engine observability sanitization** (`core/luana-core-observability/.../sanitization.py`): CONSUME `sanitize_payload`.
- **Vitalia audit_log table** (migration 013): CONSUME schema verbatim. NO new migration alterando tabla.
- **Vitalia admin bcrypt auth + sync db session** (`_shared/{auth,db}.py`): CONSUME verbatim.
- **Admin tenants.py + users.py**: REWRITE COMPLETO. Phantom code DELETED. CERO deuda técnica residual per Chris directive.
- **Vitalia clinics module**: NEW DDD scaffold. Por qué NEW (no EXTEND): no existe equivalent en core/luana-core-* (verificado grep §13). Brand-first per D2 — futuro lift EP-19 trigger cuando 2da brand replique sub-unit pattern.
- **Audit log helper**: NEW SSoT en `vitalia/backend/src/modules/vitalia/audit/audit_writer.py`. Por qué NEW: hoy cada admin module hace inline INSERT INTO vitalia_audit_log → duplicación 2 sitios + tendencia a crecer. Lift a engine `core/luana-core-observability/.../persistence/` postponed hasta 2da brand replique pattern (per anti-duplication.md threshold = 2 consumers en > 1 brand). En vitalia mismo, multiple consumers (admin/tenants, admin/users, admin/clinics, clinic_service) justifica SSoT brand-local.

Cross-brand mirror check: ❌ NO existe `nicolify/backend/src/modules/nicolify/clinics/` — clinic es brand-local vitalia. Si futuro lupulo/fitflow/guestly/fixia/retailly replica sub-unit pattern, trigger automático para `/pm-luana` proposal EP-19 `TenantSubUnit`.

## § 14 — Test Surfaces (TDD-mandatory)

### Backend tests (RED → GREEN per layer)

**Domain layer** (clinics):
- `test_clinic_entity_pydantic_v2.py` — instantiate Clinic + serialization roundtrip
- `test_clinic_invariants.py` — `tenant_id` mandatory, `deleted_at` nullable, soft delete

**Infrastructure layer** (clinics):
- `test_clinic_model_table_name.py` — `__tablename__ == "vitalia_clinics"`, indexes declared
- `test_clinic_repository.py` — `get_by_id` requires `tenant_id` arg, soft_delete sets `deleted_at`, dual filter tenant scope, queries excluded `deleted_at IS NOT NULL`

**Application layer**:
- `test_clinic_service.py::test_create_clinic_writes_audit_log` (SC-08)
- `test_audit_writer.py::test_payload_sanitized_via_engine_helper`
- `test_audit_writer.py::test_sync_commit_before_return`

**API layer**:
- `test_clinics_router_dual_filter.py` (SC-09, SC-10, SC-11)
- `test_admin_helpers_db_state_endpoint.py` (Playwright support)
- `test_admin_helpers_audit_log_endpoint.py` (Playwright support)

**Admin module tests** (after rewrite):
- `test_tenants_crud.py::test_create_tenant_calls_engine_repository` (SC-02)
- `test_tenants_crud.py::test_list_tenants_via_repository` (SC-03)
- `test_tenants_crud.py::test_suspend_tenant_writes_audit_log` (SC-07)
- `test_users_crud.py::test_create_user_and_link_to_tenant` (SC-04)
- `test_users_crud.py::test_list_users_with_tenants_join` (SC-05)
- `test_users_crud.py::test_ban_user_toggle_writes_audit_log` (SC-06)

**Integration tests**:
- `test_alembic_head.py::test_upgrade_001_to_023_succeeds` (SC-14)
- `test_alembic_head.py::test_post_upgrade_tables_exist` (verifica `users`, `tenants`, `user_tenants`, `vitalia_clinics`)

**Architecture fitness** (RED before implementation):
- `test_admin_no_raw_sql.py`
- `test_admin_consumes_engine_repos.py`
- `test_clinics_domain_no_engine_imports.py`
- `test_phantom_tables_zero_refs.py`

### Playwright admin-smoke (E2E — RED before Streamlit rewrite)

5 spec files mandatory — ver § 15 detail Phase B en `04-validators.yaml`. Cada spec ASSERT DOM + network + DB state via API helper + audit log row via API helper.

### Agentic tests

N/A — story sin agentic surface.

## § 15 — Research Notes (date-aware)

Knowledge cutoff Opus 4.7 = Jan 2026. Story implementa patterns ya cementados en codebase + skills consultados — no requires live web research. Single cite:

- **`backend/tests/architecture/test_no_legacy_paths.py`** + `.claude/rules/anti-duplication.md` (accessed 2026-05-19) — schema-mirror exception per `backend-ddd.md` precedent en PI-12 S1 T-1 (cost_recorder canonicalization) ratified by Chris. Justifica que migration 022 ejecute CREATE TABLE users/tenants/user_tenants sin promotion proposal.
- **`nicolify/backend/alembic/versions/001_initial_snapshot.py:2210-2300`** (accessed 2026-05-19) — schema canonical proven cross-brand, fuente verbatim para migration 022.
- **`core/luana-core-iam/src/luana_core_iam/infrastructure/models/`** (accessed 2026-05-19) — engine ORM SSoT que migration 022 DDL debe matchear.

## § 16 — Open Questions for PM

NINGUNA. Chris pre-autorizó cadena E2E completa. Decisiones cementadas en parent platform outcome D1-D5. Architect autonomous proceed → tickets ready.
