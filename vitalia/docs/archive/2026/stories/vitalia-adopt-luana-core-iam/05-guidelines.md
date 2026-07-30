# 05-guidelines.md — vitalia-adopt-luana-core-iam

> Builder/auditor consumption: patterns required + forbidden + skill loads + files in scope.
> SSoT: this file is the contract para qué SE PUEDE y NO SE PUEDE tocar.

## § 1 — Patterns REQUIRED

### 1.1 Schema-mirror exception per `.claude/rules/backend-ddd.md` § Schema-mirror

Builder-backend MAY ejecutar migration DDL en `vitalia/backend/alembic/versions/022_*.py` matching engine `luana_core_iam` ORM model schemas, sin necesidad de promotion proposal. Esta exception:

- **Permitida**: CREATE TABLE users/tenants/user_tenants + indexes/FKs verbatim matching engine ORM.
- **NO permitida**: edits a `core/luana-core-iam/src/`. Engine es read-only.
- **NO permitida**: declarar duplicate SQLAlchemy model classes en `vitalia/backend/src/` para users/tenants/user_tenants (engine SSoT). Consumer imports desde `luana_core_iam.infrastructure.models`.

### 1.2 Engine boundary CRITICAL (anti-duplication.md cardinal)

- ✅ CONSUME engine via Python imports:
  ```python
  from luana_core_iam.domain.user import User
  from luana_core_iam.domain.tenant import Tenant
  from luana_core_iam.infrastructure.models.user_model import UserModel
  from luana_core_iam.infrastructure.models.tenant_model import TenantModel
  from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel
  from luana_core_iam.infrastructure.repositories.user_repository import UserRepository
  from luana_core_iam.infrastructure.repositories.tenant_repository import TenantRepository
  from luana_core_iam.infrastructure.repositories.user_tenant_repository import UserTenantRepository
  ```
- ❌ NO touch `core/luana-core-iam/src/` (any file). Story scope es brand-only.
- ❌ NO promotion proposal needed (engine no se modifica).

### 1.3 Audit log SYNC write per HIPAA-lite invariant

TODA mutación (tenant/user/clinic create/update/ban/suspend/delete) MUST escribir row en `vitalia_audit_log` ANTES de retornar response success. Usar SSoT helper `vitalia/backend/src/modules/vitalia/audit/audit_writer.py::write_audit_log_sync(...)`.

```python
from src.modules.vitalia.audit.audit_writer import write_audit_log_sync

with get_sync_session() as session:
    repo = TenantRepository(session)
    created = repo.create(tenant)
    write_audit_log_sync(
        db=session,
        tenant_id=created.id,
        clinic_id=None,
        user_id=admin_user_id,
        action="tenant.create",
        resource_type="tenant",
        resource_id=created.id,
        payload={"name": ...},  # sanitize_payload aplicado internamente
    )
# después de salir del context manager session.commit() ya fue ejecutado por write_audit_log_sync.
```

NO `BackgroundTasks.add_task(write_audit_log_sync, ...)`. NO async fire-forget. NO outbox pattern (audit es SSoT inmediato).

### 1.4 Dual filter PHI helper decorator

Decorator `@require_clinic_access(clinic_id_from="path")` vive en `vitalia/backend/src/modules/vitalia/clinics/api/decorators.py`. Aplica a futuras routes PHI. En story scope cubre SC-09/SC-10/SC-11 vía test surrogate (tenant scope check).

### 1.5 SQLAlchemy 2.0 ORM en clinics module

Brand-local code (`vitalia/backend/src/modules/vitalia/clinics/`) usa SQLA 2.0 idioms:
```python
from sqlalchemy import select
stmt = select(ClinicModel).where(ClinicModel.tenant_id == tenant_id)
result = db.execute(stmt).scalars().all()
```

NO `session.query(ClinicModel).filter(...)` legacy.

**Excepción documentada**: `ClinicModel` usa `Column()` style (legacy) para consistencia con engine `UserModel`/`TenantModel` que también usan `Column()` (engine ORM no migrado a `mapped_column()`). Builder NO refactoriza ni engine ni brand a `mapped_column()` — preserva engine convention.

### 1.6 Pydantic v2 DTOs

`ClinicCreate`, `ClinicUpdate`, `ClinicResponse` + `DbStateResponse` + `AuditLogEntry`:
- `model_config = ConfigDict(from_attributes=True, extra="forbid")` (donde aplique)
- Explicit field types — no `Any` / no untyped dicts.
- `response_model=` en TODA route.

### 1.7 FastAPI conventions

- `FastAPI(redirect_slashes=False)` (already cementado en `main.py` — verify keep).
- Bearer auth + `X-Tenant-ID` header en routes brand-scoped `/api/v1/vitalia/clinics/...`.
- `X-Internal-Token` header en routes test-only `/api/v1/vitalia/admin/{db-state,audit-log}`.
- Annotated dependencies:
  ```python
  from typing import Annotated
  from fastapi import Depends
  from sqlalchemy.orm import Session
  from luana_core_platform.core.database import get_db

  DBDep = Annotated[Session, Depends(get_db)]

  @router.post("/", response_model=ClinicResponse)
  def create_clinic(payload: ClinicCreate, db: DBDep) -> ClinicResponse: ...
  ```

### 1.8 Spanish neutro LatAm en UI strings

Per spec § 5 tabla canónica. Sin voseo. `tú`/`tu`/`tus`. Ej: "Ingresa la contraseña" (NO "Ingresá").

### 1.9 Idempotent migrations

- `CREATE TABLE IF NOT EXISTS ...`
- `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...`
- `CREATE INDEX IF NOT EXISTS ...`
- `DO $$ BEGIN ... EXCEPTION WHEN ... THEN ...; END $$;` para guards complejos
- NO `sa.Enum(..., create_type=True)` (broken SA 2.0)
- NO `op.create_table()` (no idempotent)

### 1.10 Bcrypt admin auth — engine helper consumption

`vitalia/backend/src/modules/vitalia/admin/_shared/auth.py::verify_admin_password(plain_password)` ALREADY uses bcrypt directly (no engine helper). Story preserves as-is. Future: lift to `core/luana-core-iam/...` if 2nd brand replicates exact admin pattern (promotion candidate).

### 1.11 PII / PHI sanitization

`from luana_core_observability.recording.sanitization import sanitize_payload` consumed inside `audit_writer.write_audit_log_sync`. Defense-in-depth: caller también should NOT include PHI in payload (story scope only identity fields — names, slugs, emails OK; NO diagnosis, treatment, dosage).

### 1.12 TDD — RED test first per layer

- Domain layer: RED test antes que `clinic.py` entity exista.
- Infrastructure: RED test antes que `clinic_repository.py` exista.
- Application: RED test antes que `clinic_service.py` exista.
- API: RED test antes que `router.py` exista.
- Architecture fitness: RED test antes del rewrite (e.g., `test_admin_no_raw_sql.py` FAIL inicialmente porque admin tiene SQL crudo; GREEN post-rewrite).

### 1.13 Native commands (NO docker exec)

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/{ruff,pytest}
cd ${WS}/vitalia/frontend && npx {tsc,vitest,playwright}
```

Docker exec SOLO para alembic migrations runtime (`docker exec luana-dev-vitalia_backend_dev-1 alembic upgrade head`).

## § 2 — Patterns FORBIDDEN

### 2.1 SQL crudo en admin/modules/{tenants,users,clinics}.py

❌ `session.execute(text("SELECT ... FROM tenants ..."))`
❌ `session.execute(text("INSERT INTO users ..."))`
❌ `session.execute(text("UPDATE ... SET ..."))`
❌ `session.execute(text("DELETE FROM ..."))`

✅ Consume engine repos: `TenantRepository(session).get_all()` / `.create(tenant)` / etc.

**Exception**: `admin/api/admin_helpers_router.py` (NEW, Playwright support) MAY use raw SQL for audit log read query — file location distinto (NOT bajo `admin/modules/`). Arch test `test_admin_no_raw_sql.py` scopes to `admin/modules/{tenants,users,clinics}.py` only.

### 2.2 Tablas brand-prefixed para entities engine

❌ `vitalia_users` / `vitalia_tenants` / `vitalia_user_tenants` / `vitalia_user_profiles`

✅ `users` / `tenants` / `user_tenants` (engine canonical names). Migration 022 CREATE TABLE sin prefix `vitalia_`.

### 2.3 Clerk auth en admin Streamlit

❌ Clerk JWT verification en admin Streamlit (admin no es flow customer-facing).

✅ bcrypt password verification existing pattern (`_shared/auth.py`).

### 2.4 Hardcoded passwords en código

❌ `if password == "admin123": ...`

✅ Env var `VITALIA_ADMIN_PASSWORD_HASH` (bcrypt hash) + `verify_admin_password(password)`.

### 2.5 Async fire-forget audit log

❌ `asyncio.create_task(write_audit_log_async(...))` después de response.
❌ `BackgroundTasks.add_task(...)` para audit log.

✅ `write_audit_log_sync(db, ...)` ANTES de session.commit() final del request handler.

### 2.6 PHI en URLs (GET query params)

❌ `GET /api/v1/vitalia/patients?dni=12345678&diagnosis=cancer`

✅ POST body con DTOs sanitized. Aplica a futuros endpoints `/patients`, `/treatments`. NOT story scope (admin no toca PHI directamente — clinics es identity only).

### 2.7 Voseo en UI strings

❌ "Ingresá la contraseña" / "Hacé click en Crear"

✅ "Ingresa la contraseña" / "Haz click en Crear"

Per `.claude/rules/spanish-text.md`. Magic comment `<!-- voseo-allowed -->` solo si el archivo cita ejemplos verbatim de voseo (no aplica a story).

### 2.8 Edits a `core/luana-core-iam/src/`

❌ Modificar engine models / repositories / domain / API.

✅ CONSUME via imports. Si engine necesita extension (e.g., `UserTenantRepository.link()` method missing), workaround inline en story scope (direct ORM insert acceptable) + flag como future promotion candidate.

### 2.9 Cross-brand mirror

❌ Copiar `nicolify/backend/src/modules/nicolify/admin/` → `vitalia/backend/src/modules/vitalia/admin/` con renames.

✅ Si 2 brands replicarian pattern admin idéntico → `/pm-luana` promotion proposal `core/luana-core-admin/` con Extension SDK EP-N. NOT this story.

### 2.10 Default flag flips

❌ Story NO flipea defaults `USE_*_PATTERN_*`, `LITELLM_PROXY_ENABLED`, etc. (sin side-effect path migration audit).

### 2.11 Hard deletes

❌ `DELETE FROM vitalia_clinics WHERE id = ...`

✅ Soft delete: `UPDATE vitalia_clinics SET deleted_at = NOW(), is_active = false WHERE ...`. `ClinicRepository.soft_delete(tenant_id, clinic_id)`.

## § 3 — Skills to LOAD (builder mandatory)

| Skill | Trigger | Loading reason |
|---|---|---|
| `backend-expert` | siempre — BE story | DDD Inside-Out, SQLA 2.0, Pydantic v2, arch fitness, native commands, runtime quality checklist |
| `playwright-expert` | cuando tocás `vitalia/frontend/e2e/admin/**` | admin-smoke project, fixtures, POM patterns, native execution, Clerk-NOT-required pattern (bcrypt session cookie) |

NO load (story scope no aplica):
- `frontend-expert` — no React/Next.js feature (solo Playwright TS infra)
- `copilot-expert` / `sales-agent-expert` — story sin agentic
- `brand-expert` / `offer-expert` / `metrics-expert` — story sin brand/offer/analytics touch

## § 4 — Rules to LOAD (builder + auditor mandatory)

| Rule | Why |
|---|---|
| `.claude/rules/anti-duplication.md` | Engine boundary read-only + cross-brand mirror ban (cardinal) |
| `.claude/rules/backend-ddd.md` § Schema-mirror exception | Justifica migration 022 DDL mirror engine without promotion |
| `.claude/rules/backend-migrations.md` | Idempotent raw SQL only, IF NOT EXISTS, no `sa.Enum` |
| `.claude/rules/tenant-isolation.md` | Every clinic query filters `tenant_id` |
| `vitalia/.claude/rules/hipaa-lite.md` | Dual filter, audit log sync, sanitization, RBAC strict (overlay) |
| `.claude/rules/spanish-text.md` | UI strings Spanish neutro sin voseo |
| `.claude/rules/tdd-mandatory.md` | RED → GREEN per layer |
| `.claude/rules/auditor-downstream-regression.md` | Schema-mirror engine tables NO requires promotion proposal — solo DDL en brand DB |
| `.claude/rules/git-safety.md` | Triple-branch + git haiku delegation |
| `.claude/rules/admin-panel.md` | Streamlit registry-based `st.navigation`, no logic en pages/, _shared/ for cross-module utils |

## § 5 — Files in SCOPE (builder MAY modify or create)

### NEW files
```
vitalia/backend/alembic/versions/022_vitalia_add_engine_iam_tables.py
vitalia/backend/alembic/versions/023_vitalia_clinics.py
vitalia/backend/src/modules/vitalia/clinics/__init__.py
vitalia/backend/src/modules/vitalia/clinics/domain/__init__.py
vitalia/backend/src/modules/vitalia/clinics/domain/clinic.py
vitalia/backend/src/modules/vitalia/clinics/infrastructure/__init__.py
vitalia/backend/src/modules/vitalia/clinics/infrastructure/models/__init__.py
vitalia/backend/src/modules/vitalia/clinics/infrastructure/models/clinic_model.py
vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/__init__.py
vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/clinic_repository.py
vitalia/backend/src/modules/vitalia/clinics/application/__init__.py
vitalia/backend/src/modules/vitalia/clinics/application/clinic_service.py
vitalia/backend/src/modules/vitalia/clinics/api/__init__.py
vitalia/backend/src/modules/vitalia/clinics/api/dtos.py
vitalia/backend/src/modules/vitalia/clinics/api/decorators.py
vitalia/backend/src/modules/vitalia/clinics/api/router.py
vitalia/backend/src/modules/vitalia/audit/__init__.py
vitalia/backend/src/modules/vitalia/audit/audit_writer.py
vitalia/backend/src/modules/vitalia/admin/modules/clinics.py
vitalia/backend/src/modules/vitalia/admin/pages/clinicas.py
vitalia/backend/src/modules/vitalia/admin/api/__init__.py
vitalia/backend/src/modules/vitalia/admin/api/admin_helpers_router.py
vitalia/backend/tests/modules/vitalia/admin/__init__.py
vitalia/backend/tests/modules/vitalia/admin/test_tenants_crud.py
vitalia/backend/tests/modules/vitalia/admin/test_users_crud.py
vitalia/backend/tests/modules/vitalia/admin/test_clinics_admin.py
vitalia/backend/tests/modules/vitalia/admin/test_audit_log_sync.py
vitalia/backend/tests/modules/vitalia/clinics/__init__.py
vitalia/backend/tests/modules/vitalia/clinics/test_clinic_repository.py
vitalia/backend/tests/modules/vitalia/clinics/test_clinic_service.py
vitalia/backend/tests/modules/vitalia/clinics/test_require_clinic_access.py
vitalia/backend/tests/modules/vitalia/clinics/test_admin_helpers_db_state.py
vitalia/backend/tests/modules/vitalia/clinics/test_admin_helpers_audit_log.py
vitalia/backend/tests/integration/__init__.py
vitalia/backend/tests/integration/test_alembic_head.py
vitalia/backend/tests/architecture/test_admin_no_raw_sql.py
vitalia/backend/tests/architecture/test_admin_consumes_engine_repos.py
vitalia/backend/tests/architecture/test_clinics_domain_no_engine_imports.py
vitalia/backend/tests/architecture/test_phantom_tables_zero_refs.py
vitalia/frontend/e2e/admin/admin_auth.fixture.ts
vitalia/frontend/e2e/admin/utils/db_verify.ts
vitalia/frontend/e2e/admin/utils/types.ts
vitalia/frontend/e2e/admin/admin-login.spec.ts
vitalia/frontend/e2e/admin/admin-tenants-crud.spec.ts
vitalia/frontend/e2e/admin/admin-users-crud.spec.ts
vitalia/frontend/e2e/admin/admin-clinics-extension.spec.ts
vitalia/frontend/e2e/admin/admin-hipaa-dual-filter.spec.ts
```

### MODIFIED files
```
vitalia/backend/alembic/versions/014_vitalia_tenants_columns.py    [guard DO $$ IF table EXISTS]
vitalia/backend/src/modules/vitalia/admin/app.py                   [add Clinicas PageSpec + Salir button]
vitalia/backend/src/modules/vitalia/admin/modules/tenants.py       [REWRITE — consume TenantRepository]
vitalia/backend/src/modules/vitalia/admin/modules/users.py         [REWRITE — consume UserRepository + UserTenantRepository]
vitalia/backend/src/main.py                                        [register clinics router + admin_helpers router]
vitalia/docker-compose.dev.yml                                     [add vitalia_admin_dev service port 8502]
vitalia/.env.dev.template                                          [add single-quote comment + VITALIA_INTERNAL_API_TOKEN]
vitalia/frontend/playwright.config.ts                              [add admin-smoke project]
Makefile                                                           [add dev-vitalia-admin target]
```

### Existing files CONSUMED (read-only — NO modify)
```
core/luana-core-iam/src/luana_core_iam/**                          [engine — consume via imports, NO touch]
core/luana-core-observability/src/luana_core_observability/recording/sanitization.py  [consume sanitize_payload]
core/luana-core-platform/src/luana_core_platform/core/database.py  [consume SessionLocal + get_db]
vitalia/backend/src/modules/vitalia/admin/_shared/auth.py          [bcrypt verify_admin_password]
vitalia/backend/src/modules/vitalia/admin/_shared/db.py            [get_sync_session]
vitalia/backend/alembic/versions/013_vitalia_audit_log.py          [audit log schema — consume]
nicolify/backend/alembic/versions/001_initial_snapshot.py          [verbatim schema reference for migration 022 — read for canonical engine DDL]
```

## § 6 — Files OUT of scope (builder MUST NOT modify)

❌ `core/luana-core-iam/src/`
❌ `core/luana-core-observability/src/`
❌ `core/luana-core-platform/src/`
❌ Cualquier `core/luana-core-*/src/` engine package
❌ `nicolify/backend/`, `comunify/backend/`, `lupulo/backend/` (cross-brand)
❌ `nicolify/frontend/`, `comunify/frontend/`, `lupulo/frontend/` (cross-brand)
❌ `vitalia/frontend/src/` (story sin FE Next.js — ONLY `vitalia/frontend/e2e/admin/` permitido)
❌ `vitalia/backend/src/modules/vitalia/{appointments,patients,treatments,sales_agent,copilot,...}/` (otros módulos vitalia — story scope solo admin + clinics + audit)
❌ `.claude/rules/` raíz (story no agrega rules platform — patrón vitalia-specific en overlay si needed)

## § 7 — DAG implementation order

```
                              ┌──────────────────────────────────┐
                              │ T-doc-env-template (independiente)│
                              └──────────────────────────────────┘
                              
                              ┌──────────────────────────────────┐
                              │ T-be-add-engine-iam-tables       │
                              │ (migrations 022 + edit 014 guard)│
                              └──────────────┬───────────────────┘
                                             │
                                             ▼
                              ┌──────────────────────────────────┐
                              │ T-be-apply-pending-migrations    │
                              │ (alembic upgrade head)           │
                              └──────────────┬───────────────────┘
                                             │
                              ┌──────────────┴───────────────┐
                              │                              │
                              ▼                              ▼
              ┌──────────────────────────┐   ┌──────────────────────────┐
              │ T-be-admin-rewrite       │   │ T-be-admin-deletion      │
              │ (tenants.py + users.py)  │   │ (DELETE phantom refs)    │
              └──────────────┬───────────┘   └─────────────┬────────────┘
                             │                             │
                             └──────────────┬──────────────┘
                                            │
                                            ▼
                              ┌──────────────────────────────────┐
                              │ T-be-clinics-extension           │
                              │ (migration 023 + DDD module      │
                              │  + admin clinics page +          │
                              │  @require_clinic_access)         │
                              └──────────────┬───────────────────┘
                                             │
                                             ▼
                              ┌──────────────────────────────────┐
                              │ T-infra-admin-service            │
                              │ (docker-compose + Makefile +     │
                              │  Playwright admin-smoke setup)   │
                              └──────────────────────────────────┘
```

T-doc-env-template puede ejecutarse cualquier momento paralelo (1 commit independiente).

## § 8 — Definition of Done (per ticket)

Cada ticket MUST cumplir:
- [ ] TDD: tests RED → GREEN per layer (validator_ids del ticket green)
- [ ] Ruff lint + format check passing
- [ ] Arch fitness gates passing (incl. NEW gates introducidos por este ticket)
- [ ] Migration idempotent verified (CREATE TABLE IF NOT EXISTS / DO $$ EXCEPTION)
- [ ] Spanish neutro UI strings (no voseo)
- [ ] Audit log SYNC write (HIPAA-lite invariant)
- [ ] Conventional Commits commit msg + Co-Authored-By Claude Opus
- [ ] Push a `wip/vitalia`
- [ ] T-{n}-result.md scrito con paths tocados + tests result + observations

## § 9 — Auditor checkpoints (Phase D + C1-C5)

Auditor-backend ejecuta:
- **Phase D — Gherkin verification matrix**: 14 SC-NN → tests mapping per gherkin_coverage_summary en 04-validators.yaml. ALL scenarios → at least 1 test path GREEN.
- **C1 (Code quality)**: ruff + format + type hints + structlog (no print) + Pydantic v2 idioms
- **C2 (Spec compliance)**: features match 01-spec.md acceptance criteria 1:1
- **C3 (Architecture)**: DDD layers respected, anti-duplication scan (no cross-brand mirror, no engine touch), NO NEW LAYER rule (audit log helper justified per §13 03-arch.md), schema-mirror exception properly applied
- **C4 (Cross-cutting)**: tenant_isolation (clinics queries), HIPAA dual filter scaffold, audit log sync write, Spanish neutro, currency N/A, native-first
- **C5 (Trace + observability)**: NO log of PHI in structlog statements, no PHI in `payload_redacted` (sanitize_payload guard)

Downstream regression scope per `.claude/rules/auditor-downstream-regression.md`:
- Engine edit detection: ❌ NO engine edits — verified.
- Cross-brand mirror scan: ❌ admin pattern NO mirror nicolify (different schemas, different concerns) — verified.
- NEW arch tests added: 4 (`test_admin_no_raw_sql.py`, `test_admin_consumes_engine_repos.py`, `test_clinics_domain_no_engine_imports.py`, `test_phantom_tables_zero_refs.py`) — ratchet shrink-only enforced.
