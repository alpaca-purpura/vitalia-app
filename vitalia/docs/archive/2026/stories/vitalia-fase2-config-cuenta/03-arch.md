---
story_id: vitalia-fase2-config-cuenta
brand: vitalia
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: partial-with-rationale
architect_run_on: 2026-06-11
---

# Contract: Cuenta del tenant (config.cuenta) — D3-revoked (especialidades editables)

> Single source of truth for parallel FE + BE implementation. RONDA 2 spec
> (`01-spec.md`) + D3-revoked (especialidades editables, ratificado 2026-06-11).
> Patrón ADR-vitalia-004 (sub-tab N3-static) + HIPAA-lite (audit log, tenant scope).

## 0. Context Summary

- **PR ID:** vitalia-fase2-config-cuenta · release F4
- **Architect run on:** 2026-06-11 (Opus 4.8 cutoff Jan 2026; no novel framework research needed — patrón ADR-vitalia-004 ya cementado en `lisa/marca`)
- **Módulos tocados:** `clinics/` (EXTEND: campos cuenta + service + endpoints) · `brand_studio/` (EXTEND: specialties editable write a `config_json`) · `_shared/` (NEW: fiscal-id validator + specialty catalog) · FE `features/config/`
- **Surface → builder → auditor mapping** (PM usa para spawnear agentes correctos):

  | Surface | Builder | Auditor |
  |---|---|---|
  | `vitalia/backend/src/modules/vitalia/clinics/{domain,infrastructure,application,api}/` (EXTEND) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
  | `vitalia/backend/src/modules/vitalia/_shared/validation/` (NEW fiscal validator) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
  | `vitalia/backend/src/modules/vitalia/_shared/catalogs/` (NEW specialty catalog) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
  | `vitalia/backend/src/modules/vitalia/brand_studio/application/` (EXTEND specialties write) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
  | `vitalia/frontend/src/app/[tenantId]/(shell-organism)/config/cuenta/**` + `features/config/**` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |

- **NO agentic surface.** Esta story NO toca `copilot/` ni `sales_agent/`. La "posible recalc agentes" (D3-revoked § scope) se resuelve por EVENT (domain event `ClinicSpecialtiesChanged`) que los agentes consumen runtime; NO requiere builder-agentic en esta story (el system prompt lee `config_json.clinic_config.primary_specialties` en runtime — zero-touch, ver § 8).
- **Skills consultados:**
  - `backend-expert`: DDD Inside-Out, repo tenant-scoped, response_model mandatory, migration idempotente raw SQL.
  - `frontend-expert` + `vitalia-design-system`: FSD-Lite, N3-static SubSubTabsBar, `@luana/ui-kit` canon (Select/Group/FloatingAutosaveIndicator/timezone-select/currency-selector), `use-autosave` 600ms.
  - `brand-expert`: specialties son `tenant.config_json.clinic_config.primary_specialties` (NO en Clinic entity); read via `marca_service.get_clinic_config`; write nuevo brand-local sin tocar engine schema.
  - `offer-expert`: N/A (no offers). `copilot-expert`/`sales-agent-expert`: N/A (sin surface agentic; recalc por event runtime).
- **CONTEXT-BRIEF source:** ausente (story-level) → self-ran greps (Path B). Cross-module NO-NEW-LAYER scan ejecutado (ver § Existing systems audit).
- **capability YAML afectada (post-merge, paradigma post 2026-05):** `vitalia/docs/product/capabilities/configuracion/cuenta.yaml` (`cap_change_type: new`) + bloques v3.2 (`scenarios[]` + `access` + `business_rules`). Zona derivada de SYSTEM-MAP: Plataforma → Configuración → cuenta. `modules/configuracion.md` narrative update si aplica.
- **Architecture gates que deben seguir verdes:** ver § 12.

## Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (Path B — fallback, no CONTEXT-BRIEF a story-level)

### Audit cross-module ejecutado
```bash
# 1. Specialty catalog existente (core + brands)
grep -rln "SPECIALTY_CATALOG|specialty_catalog|MEDICAL_SPECIALT|SpecialtyCatalog" core/ vitalia/backend/src/ comunify/backend/src/
#   → 0 matches (catálogo NO existe). Specialties hoy = list[str] libre en marca_dtos (sin catálogo ni validación).

# 2. Tenant fiscal-id validator (CUIT/RUC/RFC/NIT/RUT) existente
grep -rln "validate_fiscal|FiscalId|validate_tax_id|tax_id_validator" core/ vitalia/backend/src/ comunify/backend/src/ (excluyendo node_modules)
#   → 0 matches en código de producto. clinics/credential_validator.py = valida credenciales MÉDICAS de doctor (CMP/matrícula), NO IDs fiscales de tenant. fiscal/ = emisión SUNAT (otro concern). 

# 3. Cross-brand mirror config-cuenta
find comunify/backend/src/ comunify/frontend/src/ -path "*cuenta*" -o -path "*account*config*"
#   → 0 matches (sin mirror cross-brand).

# 4. Specialties SSoT actual (dónde persisten)
grep -n "clinic_vertical|primary_specialties" brand_studio/.../marca_service.py
#   → tenant.config_json["clinic_config"]["primary_specialties"] (engine TenantModel.config_json JSONB).
```

### Sistemas existentes encontrados
| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| `Clinic` entity + repo + service + router | `vitalia/backend/src/modules/vitalia/clinics/` | active | **EXTEND** (campos cuenta + service methods + PATCH endpoint) |
| Audit writer (sync + async) | `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` | active | **CONSUME** (`AsyncAuditWriter.write`) |
| `TenantLocale` VO (currency+timezone) | `core/luana-core-platform/.../domain/locale.py` | active (engine) | **CONSUME** read-only |
| `clinic_config` en `tenant.config_json` (specialties/vertical SSoT) | engine `TenantModel.config_json` JSONB, leído por `marca_service.get_clinic_config` | active | **EXTEND** vía brand service (read-modify-write JSONB; NO column nueva en engine) |
| `@luana/ui-kit` canon (Select, Group, FloatingAutosaveIndicator, timezone-select, currency-selector, FormPageScaffold) | `core/@luana/ui-kit/src/` | active (engine TS) | **CONSUME** (canon binding HARD) |
| `use-autosave` hook 600ms | `vitalia/frontend/src/hooks/use-autosave.ts` | active | **CONSUME** |
| N3-static `SubSubTabsBar` + `AGENT_SUBSUBTABS` | `vitalia/frontend/src/lib/shell-routes.ts` | active | **EXTEND** (agregar entry `config.cuenta`) |
| Credential validator (doctor médico) | `clinics/application/credential_validator.py` | active | **REFERENCE** (patrón country-rules dict; NO reusar — distinto dominio: credencial médica ≠ ID fiscal) |
| `test_fe_be_contract_parity.py` (HB-42 embudo gate) | `vitalia/backend/tests/architecture/` | active | **EXTEND** (registrar CONTRACT_PAIRS de esta story) |

### Decisión por sistema
- **Clinic (clinics/, active): EXTEND.** Agregar campos `legal_name · fiscal_id · address · phone · email · language · currency` al `Clinic` entity + model + migration idempotente. Back-compat: campos nullable (clínicas existentes no los tienen). NO se rompe ningún consumer (lectura tolera None).
- **Specialties (tenant.config_json, active): EXTEND vía brand service.** Las specialties YA viven en `config_json.clinic_config.primary_specialties` (engine JSONB). El write nuevo (D3-revoked editable) hace **read-modify-write del JSONB brand-local** vía `ClinicAccountService` — NUNCA agrega columna al engine `TenantModel` (engine-boundary: consume read, replicate write brand-local; ver memoria `engine-boundary-consume-not-mount`). Validación contra specialty catalog del país.
- **Fiscal-id validator (NO existe): NEW justificado.** Ningún validador de ID fiscal de tenant existe. `credential_validator.py` valida credenciales médicas de doctor (CMP/matrícula numérica), semántica distinta (no CUIT/RUC/RFC). `fiscal/` es emisión SUNAT. NEW acotado: `_shared/validation/fiscal_id_validator.py` con dict country-rules (mismo PATRÓN que `credential_validator`, distinto dominio). **Lift candidate documentado** (multi-país, plausible cross-brand) — NO lift ahora (1ª impl, vive brand-local).
- **Specialty catalog (NO existe): NEW justificado.** Specialties hoy = `list[str]` libre sin catálogo. NEW: `_shared/catalogs/specialty_catalog.py` con catálogo por país (AR/PE/MX/CL/CO/UY). **Lift candidate documentado** — NO lift ahora.
- **Sin cross-brand mirror.** comunify no tiene config-cuenta. "Cuenta del tenant" (legales+fiscal+locale) es plausible lift a `core/luana-core-tenant-profile` SI comunify/nicolify lo replican → marcar promotion candidate, NO lift en 1ª impl.

## 1. Domain Entities

### `Clinic` (EXTEND — `clinics/domain/clinic.py`)
Agregar a la entidad existente (todos nullable para back-compat; clínicas existentes no los tienen):
```python
class Clinic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # --- existentes (NO tocar) ---
    id: UUID
    tenant_id: UUID
    name: str                         # nombre comercial
    slug: str
    country: str = Field(max_length=2, description="ISO 3166-1 alpha-2 · read-only post-alta")
    timezone: str = Field(default="UTC")
    plan_tier: str = Field(default="starter")
    is_active: bool = True
    onboarding_completed: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    # --- NUEVOS (D3-revoked + RONDA 2) ---
    legal_name: str | None = None      # razón social (Q7 separada de nombre comercial)
    fiscal_id: str | None = None       # CUIT/RUC/RFC/NIT/RUT — validado por país
    address: str | None = None         # dirección (freetext, sin validación estricta)
    phone: str | None = None           # teléfono de contacto (freetext)
    email: str | None = None           # email de contacto (freetext, no EmailStr — admite vacío)
    language: str = Field(default="es-419", description="derivado del país, read-only MVP")
    currency: str | None = None        # ISO 4217 — editable (Q8); fallback TenantLocale
```
> `vertical`/`clinic_type` + `primary_specialties` NO viven en `Clinic` — viven en `tenant.config_json.clinic_config` (SSoT). NO duplicar.

### `ClinicSpecialtiesChanged` (NEW domain event — `clinics/domain/events.py`)
Emitido cuando admin cambia specialties (D3-revoked § "posible recalc agentes"). Subscriber opcional; los agentes leen `config_json` runtime → este event sirve para invalidar cache/trace, NO para mutar prompt.
```python
class ClinicSpecialtiesChanged:  # subclass del DomainEvent base brand-local
    tenant_id: UUID
    clinic_id: UUID
    old_specialties: list[str]
    new_specialties: list[str]
    changed_by_user_id: UUID
```

## 2. SQLAlchemy 2.0 Models

### `ClinicModel` (EXTEND — `clinics/infrastructure/models/clinic_model.py`)
Tabla existente `vitalia_clinic_branches`. Agregar columnas (todas nullable). **Mantener estilo `Column()`** del modelo existente (coherencia con engine models — el modelo ya usa `Column`, no `mapped_column`; NO mezclar estilos en el mismo archivo).
```python
legal_name = Column(String, nullable=True)
fiscal_id  = Column(String, nullable=True, comment="CUIT/RUC/RFC/NIT/RUT validado por país")
address    = Column(String, nullable=True)
phone      = Column(String, nullable=True)
email      = Column(String, nullable=True)
language   = Column(String, nullable=False, server_default="es-419")
currency   = Column(String(3), nullable=True, comment="ISO 4217")
```
> Index existente `ix_*` sobre tenant_id + slug ya cubre las queries. NO nuevo index (fiscal_id no se busca por sí solo).
> Specialties NO tienen tabla nueva — viven en engine `tenants.config_json` JSONB. CERO migración para specialties.

## 3. Pydantic v2 DTOs

> Path: `clinics/api/dtos.py` (EXTEND). `model_config = ConfigDict(from_attributes=True)` en todos. response_model mandatory en cada route.

```python
class ClinicAccountResponse(BaseModel):
    """GET — full account view (editable + read-only fields + derived)."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    # editable
    name: str                          # nombre comercial
    legal_name: str | None             # razón social
    fiscal_id: str | None
    address: str | None
    phone: str | None
    email: str | None
    currency: str | None               # editable (Q8)
    timezone: str                      # editable
    # read-only (definido en el alta)
    country: str                       # read-only
    language: str                      # derived del país, read-only
    clinic_type: str                   # read-only (de config_json.clinic_config.clinic_vertical)
    # editable D3-revoked
    primary_specialties: list[str]     # editable (validado vs catálogo país)
    # derived label para badges
    fiscal_id_label: str               # "CUIT" | "RUC" | "RFC" | "NIT" | "RUT" — derivado de country

class ClinicAccountPatchRequest(BaseModel):
    """PATCH — partial update. Solo campos editables. read-only rechazados si presentes."""
    model_config = ConfigDict(from_attributes=True)
    name: str | None = None
    legal_name: str | None = None
    fiscal_id: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    currency: str | None = None
    timezone: str | None = None
    primary_specialties: list[str] | None = None
    # NUNCA acepta: country, language, clinic_type (read-only — ignorados o 422 si llegan)

class SpecialtyCatalogResponse(BaseModel):
    """GET — catálogo de especialidades del país de la clínica (para multi-select)."""
    model_config = ConfigDict(from_attributes=True)
    country: str
    specialties: list[str]             # opciones válidas para ese país

class DpoReferenceResponse(BaseModel):
    """GET — DPO read-only (referencia; se gestiona en Seguridad y cumplimiento)."""
    model_config = ConfigDict(from_attributes=True)
    name: str | None
    email: str | None
    role_label: str                    # "Responsable de tratamiento (DPO)"
    manage_url_subpath: str            # "config/seguridad" (link relativo)
```
> **Fiscal validation error** → 422 con `{"field": "fiscal_id", "message": "Formato CUIT (Argentina) no válido"}` (Spanish neutro). Patrón del `CredentialValidationError` existente.

## 4. API Routes

> Router NUEVO `clinics/api/account_router.py` (montado bajo `/api/v1/clinics/account`). Mantener `clinics/api/router.py` existente intacto (CRUD admin de clínicas).
> Todas: Bearer + `X-Tenant-ID`. `redirect_slashes=False` (global). `response_model=` en cada una.

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| GET | `/api/v1/clinics/account` | Bearer + X-Tenant-ID | — | `ClinicAccountResponse` | Datos de la clínica del tenant (1 clínica MVP) |
| PATCH | `/api/v1/clinics/account` | Bearer + X-Tenant-ID | `ClinicAccountPatchRequest` | `ClinicAccountResponse` | Update parcial editable + audit log + specialties validation |
| GET | `/api/v1/clinics/account/specialties-catalog` | Bearer + X-Tenant-ID | — | `SpecialtyCatalogResponse` | Catálogo especialidades del país (multi-select options) |
| GET | `/api/v1/clinics/account/dpo` | Bearer + X-Tenant-ID | — | `DpoReferenceResponse` | DPO read-only + link a Seguridad |

**RBAC (RN-1):** solo rol `admin_clinic` puede PATCH. Otros roles autorizados → GET ok, PATCH → **403 Forbidden**. Resolver via JWT context (`user_resolver`) — NO header spoofeable. Ver memoria `audit-actor-must-be-authenticated-uuid`.
**Cross-tenant (RN-5):** clinic resuelta por `X-Tenant-ID`; tenant_B no puede leer/escribir tenant_A → 404 (no 403, evita leak). 1 clínica por tenant (MVP) → no clinic_id en URL; el service resuelve la única clínica activa del tenant.
**Idempotency:** PATCH es naturalmente idempotente (mismo payload = mismo estado). Sin dedup table necesaria (no es create).

## 5. TypeScript Types (Frontend)

> Path: `vitalia/frontend/src/features/config/types/cuenta.types.ts`. **camelCase exact mirror** de los Pydantic DTOs. ISO datetimes como `string`. **NO campos imaginados** (lección embudo HB-42 — registrar par en `test_fe_be_contract_parity.py`).

```typescript
export interface ClinicAccountResponse {
  id: string;
  tenantId: string;
  name: string;
  legalName: string | null;
  fiscalId: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  currency: string | null;
  timezone: string;
  country: string;
  language: string;
  clinicType: string;
  primarySpecialties: string[];
  fiscalIdLabel: string;
}

export interface ClinicAccountPatchRequest {
  name?: string;
  legalName?: string;
  fiscalId?: string;
  address?: string;
  phone?: string;
  email?: string;
  currency?: string;
  timezone?: string;
  primarySpecialties?: string[];
}

export interface SpecialtyCatalogResponse {
  country: string;
  specialties: string[];
}

export interface DpoReferenceResponse {
  name: string | null;
  email: string | null;
  roleLabel: string;
  manageUrlSubpath: string;
}
```
> **Zod schema** (`cuenta-schema.ts`) mirror exacto + validación fiscal client-side (UX preview; el backend es la autoridad). Camelizar en el fetch boundary (`api/get-account.ts` mapea snake→camel del JSON) — NUNCA declarar un campo que el BE no emite.

## 6. Repository Interfaces

> `ClinicRepository` (EXTEND — `clinics/infrastructure/repositories/clinic_repository.py`). **NO es PhiRepositoryBase** (clinic identity = non-PHI per domain docstring; ver § Architecture Decisions). Tenant-scoped en TODA query (incl. get_by_id). Async.

```python
class ClinicRepository:  # existente — NO cambia a PhiRepositoryBase
    async def get_active_for_tenant(self, tenant_id: UUID) -> Clinic | None:  # NEW
        """Única clínica activa del tenant (MVP 1-clínica). tenant-scoped."""
    async def update_account(self, tenant_id: UUID, clinic_id: UUID, **fields) -> Clinic:  # NEW
        """Update parcial campos cuenta. Dual where(tenant_id, id). soft-delete-aware."""
    # existentes: get_by_id(tenant_id, clinic_id), get_by_slug, list_by_tenant, create, soft_delete
```
> Specialties write NO va por ClinicRepository — va por `ClinicConfigRepository` (NEW, lee/escribe `tenant.config_json.clinic_config` JSONB vía engine `TenantModel`). tenant-scoped (`where(TenantModel.id == tenant_id)`).

## 7. Application Services

### `ClinicAccountService` (NEW — `clinics/application/clinic_account_service.py`)
```python
class ClinicAccountService:
    def __init__(self, db: AsyncSession): ...
    async def get_account(self, tenant_id: UUID) -> ClinicAccountResponse:
        # clinic = repo.get_active_for_tenant(tenant_id)  → 404 si None
        # config = config_repo.get_clinic_config(tenant_id)  → clinic_type + specialties
        # fiscal_id_label = FISCAL_ID_LABEL_BY_COUNTRY[clinic.country]
        # language = LANGUAGE_BY_COUNTRY[clinic.country]
    async def patch_account(self, *, tenant_id, requesting_user_id, requesting_role, patch) -> ClinicAccountResponse:
        # 1. RBAC gate: role != admin_clinic → raise ForbiddenError (403)
        # 2. reject read-only fields si presentes (country/language/clinic_type) → 422
        # 3. fiscal_id presente → validate_fiscal_id(fiscal_id, clinic.country) → 422 si inválido
        # 4. primary_specialties presente → validate_specialties(specialties, clinic.country) → 422 si fuera de catálogo
        # 5. transaction boundary: update clinic fields + update config_json specialties (atomic, mismo commit)
        # 6. AsyncAuditWriter.write(action="clinic.account.updated", payload={campos cambiados, NO PHI})  ← SYNC pre-response
        # 7. specialties cambió → emit ClinicSpecialtiesChanged event (event_bus, best-effort)
        # 8. return get_account(tenant_id)  ← refleja persistido
    async def get_specialty_catalog(self, tenant_id: UUID) -> SpecialtyCatalogResponse:
        # clinic.country → SPECIALTY_CATALOG[country]
    async def get_dpo_reference(self, tenant_id: UUID) -> DpoReferenceResponse:
        # read-only desde compliance/iam; manage_url_subpath="config/seguridad"
```
**Transaction boundary:** clinic fields + config_json specialties en el MISMO commit (atomicidad — si una falla, ambas revierten). Audit log row escrito SYNC antes del response (hipaa-lite § Audit log — no fire-and-forget).
**Event emission:** `ClinicSpecialtiesChanged` solo si specialties cambió, best-effort (`try/except` — no rompe el PATCH).
**Idempotency keys:** N/A (PATCH idempotente por naturaleza).

### Validators + catalogs (NEW)
- `_shared/validation/fiscal_id_validator.py`: `validate_fiscal_id(fiscal_id: str, country: str) -> None` (raise `FiscalIdValidationError` con field+message Spanish). Dict country-rules: AR (CUIT 11 díg + DV), PE (RUC 11 díg), MX (RFC 12-13 alfanum), CL/CO (NIT/RUT), UY (RUT 12 díg). Países no soportados → freetext (degradado, NO bloquea).
- `_shared/catalogs/specialty_catalog.py`: `SPECIALTY_CATALOG: dict[str, list[str]]` por país. `validate_specialties(specialties, country)` → raise si fuera del catálogo del país.

## 8. Agentic Surfaces

**N/A — esta story NO toca `copilot/` ni `sales_agent/`.**

La D3-revoked menciona "posible recalc agentes". Resolución arquitectónica (sin builder-agentic):
- El sales_agent + copilot leen `tenant.config_json.clinic_config.primary_specialties` en **runtime** (system prompt slot per-tenant). Cambiar specialties → el próximo turn lee el valor nuevo automáticamente. **Zero-touch agentic.**
- El event `ClinicSpecialtiesChanged` sirve para invalidar el prompt-cache per-tenant (slot 4/5 cacheable per-tenant) si el agente cachea el bloque de specialties. El subscriber (si se implementa) vive en observability/recording, NO en esta story (out of scope — el cache se invalida naturalmente al cambiar el prefix).
- **No hay eval golden ni prompt slot que esta story modifique.** Si en el futuro se quiere voice-fidelity sobre specialties, es otra story con surface agentic.

## 9. Migration Notes

> Migración NUEVA `039_vitalia_config_cuenta_fields.py` (head actual = `038_vitalia_adrian_embudo_funnel`). Raw SQL idempotente. `down_revision` obtenido vía `alembic current` (HB-37 ground-truth, NO hardcodear de memoria).

```python
def upgrade():
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS legal_name VARCHAR")
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS fiscal_id VARCHAR")
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS address VARCHAR")
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS phone VARCHAR")
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS email VARCHAR")
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS language VARCHAR NOT NULL DEFAULT 'es-419'")
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS currency VARCHAR(3)")
```
> NO `op.create_table` / `op.add_column` / `sa.Enum(create_type=True)`. Specialties = CERO migración (viven en engine `tenants.config_json` JSONB).
> **Prod-clone test:** `createdb migration_test && pg_dump --schema-only $PROD | psql migration_test && alembic stamp 038... && alembic upgrade head && dropdb migration_test`.

## 9.5 Tests audit (default flip)

- [x] **No aplica** — esta story NO flipea ningún default de feature flag side-effect (sin `USE_*`/`ENABLE_*`). Pure CRUD + nuevos campos.

## 10. File Structure

### Backend (DDD Inside-Out)
```
clinics/domain/clinic.py                                  MODIFIED (campos cuenta)
clinics/domain/events.py                                  NEW (ClinicSpecialtiesChanged)
clinics/infrastructure/models/clinic_model.py             MODIFIED (columnas)
clinics/infrastructure/repositories/clinic_repository.py  MODIFIED (get_active_for_tenant, update_account)
clinics/infrastructure/repositories/clinic_config_repository.py  NEW (config_json JSONB read/write)
clinics/application/clinic_account_service.py             NEW
clinics/api/account_router.py                             NEW (4 routes)
clinics/api/dtos.py                                       MODIFIED (4 DTOs nuevos)
_shared/validation/fiscal_id_validator.py                 NEW
_shared/catalogs/specialty_catalog.py                     NEW (+ country labels/language maps)
alembic/versions/039_vitalia_config_cuenta_fields.py      NEW
```

### Frontend (FSD-Lite + N3-static ADR-vitalia-004)
```
app/[tenantId]/(shell-organism)/config/cuenta/page.tsx                    NEW (Server Component → redirect default leaf 'datos')
app/[tenantId]/(shell-organism)/config/cuenta/layout.tsx                  NEW (SubSubTabsBar consumer)
app/[tenantId]/(shell-organism)/config/cuenta/datos/page.tsx              NEW (SSR + AccountDataView)
app/[tenantId]/(shell-organism)/config/cuenta/preferencias/page.tsx       NEW (SSR + PreferencesView)
app/[tenantId]/(shell-organism)/config/cuenta/responsable/page.tsx        NEW (SSR + ResponsibleView)
features/config/components/cuenta/AccountDataView.tsx                     NEW ("use client" + RHF + Zod + autosave)
features/config/components/cuenta/PreferencesView.tsx                     NEW ("use client" + timezone/currency Select)
features/config/components/cuenta/ResponsibleView.tsx                     NEW (read-only + link)
features/config/components/cuenta/SpecialtiesField.tsx                    NEW (multi-select chips, ui-kit)
features/config/hooks/use-account-form.ts                                NEW (RHF + use-autosave 600ms)
features/config/api/get-account.ts                                       NEW (React Query + camelize boundary)
features/config/api/patch-account.ts                                     NEW (React Query mutation)
features/config/api/get-specialty-catalog.ts                             NEW
features/config/types/cuenta.types.ts                                    NEW (camelCase mirror)
features/config/types/cuenta-schema.ts                                   NEW (Zod + fiscal validators client)
features/config/index.ts                                                 MODIFIED (export views, remove CuentaPlaceholder)
lib/shell-routes.ts                                                      MODIFIED (AGENT_SUBSUBTABS["config.cuenta"])
```

## 11. Cross-Cutting Concerns

- **Tenant isolation:** TODA query filtra `tenant_id` (incl. `get_active_for_tenant`, `get_clinic_config`). Cross-tenant → 404. `test_vitalia_no_query_without_tenant_filter.py` enforce.
- **Currency:** `currency: str | None` en DTO (editable, Q8). FE consume vía `@luana/ui-kit` `currency-selector`. Fallback `TenantLocale.currency` si None. NUNCA hardcode `'USD'`.
- **Master data:** `DateTime(timezone=True)` ya en modelo (created_at/updated_at). timezone editable vía `@luana/ui-kit` `timezone-select`. NO `datetime.utcnow()`.
- **Spanish neutro LatAm:** UI strings + microcopy + error messages (fiscal/specialty validators) sin voseo. `test_no_voseo_in_copy.test.ts` enforce. (Sin output sales_agent — N/A excepción voz tenant.)
- **PII / PHI:** clinic identity (name, fiscal_id, address, phone, email) NO es PHI (es dato del tenant, no del paciente). `response_model=` allowlist en cada route. Audit payload NO incluye PHI (solo identity fields). `sanitize_phi_payload` aplicado dentro del audit writer.
- **HIPAA-lite:** audit log SYNC pre-response en PATCH (`AsyncAuditWriter.write`). clinic identity = non-PHI → NO dual-filter clinic_id (no es PHI repo). `test_audit_log_sync_write.py` cubre endpoints PHI; este endpoint es non-PHI pero igual escribe audit (mejor práctica HIPAA-lite — cambio de datos del tenant queda trazado).
- **Native-first:** lint/tests native host (`${WS}/.venv/bin/{ruff,pytest}` + `npx {tsc,eslint,vitest,playwright}`). NUNCA docker exec.
- **FE↔BE contract parity (HB-42, memoria embudo):** FE types = camelCase mirror EXACTO. Registrar `ContractPair(ClinicAccountResponse ↔ cuenta.types.ts)` en `test_fe_be_contract_parity.py` ANTES de merge. NO campos imaginados.

## 12. Architecture Fitness Impact

Gates que corren contra este cambio (deben seguir verdes):

**Backend (`vitalia/backend/tests/architecture/`):**
- `test_response_model_required.py` — los 4 routes nuevos tienen `response_model=`.
- `test_vitalia_no_query_without_tenant_filter.py` — toda query nueva filtra tenant_id.
- `test_audit_log_sync_write.py` — PATCH escribe audit row pre-response.
- `test_fe_be_contract_parity.py` — **EXTEND CONTRACT_PAIRS** con el par de esta story (gate HB-42, evita drift imaginado).
- `test_migrations_idempotent.py` — migración 039 usa `IF NOT EXISTS`.
- `test_clinics_domain_no_engine_imports.py` — domain `clinic.py` puro (sin sqlalchemy/fastapi).
- `test_phi_dual_filter.py` — N/A (clinic repo no es PHI; documentado en § Architecture Decisions). NO se agrega a allowlist.

**Frontend (`vitalia/frontend/src/__tests__/architecture/`):**
- `test-agent-subsubtabs-ssot.test.ts` — `AGENT_SUBSUBTABS["config.cuenta"]` declarado en `shell-routes.ts`.
- `test_no_hardcoded_subtab_keys.test.ts` — sub-sub-tabs leídos del SSoT, no hardcoded.
- `test-no-native-select.test.ts` — usar `@luana/ui-kit` Select, NO `<select>` nativo (timezone/currency/specialties).
- `test-no-div-layout.test.ts` + `test_page_padding.test.ts` — page-primitives (PageContainer), NO `<div p-*>`.
- `test-ribbon-no-shadcn-tabs.test.ts` — N3-static SubSubTabsBar, NO Shadcn `<Tabs>` body.
- `test-no-clerk-organizations.test.ts` — tenant_id desde `useTenantId()`, NUNCA `useAuth().orgId`.
- `test_server_first.test.ts` — page.tsx Server Components; `"use client"` solo en views hoja.
- `test_no_voseo_in_copy.test.ts` + `test_no_hardcoded_strings.test.ts` — Spanish neutro, strings centralizados.
- `test_no_phi_real_data.test.ts` — fixtures/mockups sin PHI real.

**Allowlist updates:** ninguna allowlist crece. Si un gate FE/BE tiene `KNOWN_*` ratchet, NO se agrega entry (shrink-only).

## § Integration design (CONN — anti-orphan, ADR-vitalia-004 + paradigm)

Ninguna superficie llega a `done` como isla. Las 4 contenciones CONN:

- **C — Consumed:** la vista `config/cuenta` la consume el admin del tenant (rol `admin_clinic`) desde el Ribbon Plataforma → sub-tab "Mi cuenta". Los endpoints los consume el FE (React Query). El event `ClinicSpecialtiesChanged` lo consumen los agentes (runtime read de config_json).
- **O — On the map:** vive en `cap_target: configuracion.cuenta` (cap YAML). Zona derivada de SYSTEM-MAP: Plataforma → Configuración → área `cuenta` (hoy `status: planned target_release: F2` → esta story la lleva a `live`). Hogar declarado.
- **N — Navigable:** ruta `/{tenantId}/config/cuenta` (→ redirect edge a `/datos`). Alcanzable: Ribbon "Plataforma" tab (slug `config`, ya existe en `agent-catalog.ts`) → SubTabsBar "Mi cuenta" (ya en `RIBBON_SUBTABS.config[0]`) → N3 SubSubTabsBar (datos/preferencias/responsable). El sub-tab `config.cuenta` se quita del `PLACEHOLDER_MAP` (era placeholder) y se agrega a `SHIPPED_STATIC_SUBTABS`.
- **N — Notarized:** router `account_router` montado vía `include_router` en el app FastAPI vitalia (registration point en `main.py`/module wiring). FE: `AGENT_SUBSUBTABS["config.cuenta"]` registrado en `shell-routes.ts` (SSoT que SubSubTabsBar descubre). `config.cuenta` agregado a `SHIPPED_STATIC_SUBTABS` en `agent-catalog.ts`.

**Reachability path concreto:** Login → shell → click Ribbon "Plataforma" → SubTab "Mi cuenta" → aterriza `/{tenantId}/config/cuenta/datos` → ve datos reales (no placeholder) → edita → autosave → persiste + audit.

## § Architecture Decisions (ADR-vitalia-004 compliance: partial-with-rationale)

ADR-vitalia-004 § 3 sección 6 dice "PhiRepositoryBase mandatory para repos PHI; dual filter tenant_id+clinic_id". **Divergencia justificada:**

- **`ClinicRepository` NO hereda `PhiRepositoryBase`.** Rationale: la `Clinic` entity es **non-PHI** (su propio domain docstring lo declara: "Clinic identity fields (name, slug, country) are identity OK — not PHI"). Es dato del tenant, no del paciente. El dual-filter clinic_id es para queries de PHI **de pacientes** (proteger cross-clinic leak de datos médicos). Una clínica no se filtra por sí misma con clinic_id. El requisito ADR aplica a repos que tocan PHI de pacientes (Patient, Treatment, NPSResponse), NO a la entidad Clinic. Tradeoff aceptado: el endpoint igual escribe audit log (mejor práctica HIPAA-lite) + filtra tenant_id (isolation raíz). `test_phi_dual_filter.py` no incluye ClinicRepository (verificado — el gate escanea repos que importan PHI models).
- **Specialties write vía `config_json` JSONB read-modify-write, NO column nueva.** Rationale: las specialties son SSoT en engine `tenants.config_json.clinic_config` (consumido por marca_service + agentes runtime). Agregar columna a `vitalia_clinic_branches` duplicaría el SSoT → drift. El brand service hace read-modify-write del JSONB (engine-boundary: consume read, replicate write brand-local sin tocar engine schema — memoria `engine-boundary-consume-not-mount`). Tradeoff: JSONB no tiene constraint DB sobre specialties → validación en application layer (specialty_catalog) + event para invalidación.

Todo lo demás cumple ADR-vitalia-004 FULL: routing (1), FSD-Lite (2), client root (3), React Query+Zustand (4), RHF+Zod+autosave 600ms (5), DDD Inside-Out (6 excepto PHI base rationale arriba), migrations idempotent (7), telemetría N/A (no growth event — config change usa audit log), tests 4 capas (9).

## § cap YAML + modules/{m}.md Updates Required (post 2026-05 paradigma)

Post-merge (Fase F.3, `/pm-vitalia`):
- `vitalia/docs/product/capabilities/configuracion/cuenta.yaml` — crear (`cap_change_type: new`) con bloques v3.2: `scenarios[]` (12 de la matriz cobertura), `access` (rol admin_clinic edita, otros read-only), `business_rules` (RN-1..RN-6 + AC-4b specialties). `dev_preview.main_component` → `AccountDataView.tsx`.
- `vitalia/docs/architecture/SYSTEM-MAP.yaml` — `configuracion.cuenta` status `planned` → `live` (el `/pm-vitalia` o auto-gen lo refleja).
- `modules/configuracion.md` — narrative update si cambia (área cuenta ahora live).

## § Test Surfaces (TDD-mandatory · RED-first por capa)

- **BE domain:** RED test `fiscal_id_validator` (AR/PE/MX/CL/CO/UY válidos + inválidos) · `specialty_catalog.validate_specialties` (in/out catálogo) · `Clinic` entity nuevos campos.
- **BE infrastructure:** RED test `ClinicRepository.get_active_for_tenant` + `update_account` (tenant-scoped, soft-delete-aware) · `ClinicConfigRepository` read/write config_json.
- **BE application:** RED test `ClinicAccountService.patch_account` (RBAC 403 non-admin · read-only field reject 422 · fiscal invalid 422 · specialty invalid 422 · audit log row · event emitido · transaction atomicity).
- **BE API/E2E:** RED test 4 endpoints (200 happy · 422 fiscal · 403 RBAC · 404 cross-tenant).
- **FE hook:** `use-account-form` (autosave 600ms debounce + coalesce).
- **FE component:** `AccountDataView` (read-only badges · fiscal inline error · specialties multi-select) · `PreferencesView` (timezone/currency Select · idioma read-only) · `ResponsibleView` (link).
- **E2E Playwright (live-verify real):** `e2e/specs/config/cuenta.spec.ts` — write CUIT válido + POST 200 + reload → persisted + audit row en logs (≥1 write real ejercido, AC-6). Anti-burbuja fixture (`base.ts`, NO `@playwright/test`). NO mockear el BE del surface.
- **Visual goldens:** `cuenta-datos.png`, `cuenta-prefs.png`, `cuenta-resp.png` (3 sub-sub-tabs vs mockup ratificado).
- **Arch fitness:** registrar CONTRACT_PAIR en `test_fe_be_contract_parity.py` (RED hasta que FE types existan camelCase).

## § Research Notes (DATE-AWARE)

- **Sin investigación de patrón novel necesaria.** El patrón ADR-vitalia-004 (sub-tab N3-static) ya está cementado e implementado en `lisa/marca` (3 sub-sub-tabs). El canon `@luana/ui-kit` (Select/Group/FloatingAutosaveIndicator/timezone-select/currency-selector) es SSoT existente. Fiscal-id + specialty catalogs son tablas de datos (country rules), no patrón nuevo.
- **Knowledge cutoff disclosure:** Opus 4.8 cutoff Jan 2026. Para fiscal-id formatos (CUIT AR 11 díg + dígito verificador mód-11, RUC PE 11 díg, RFC MX 12-13, etc.) — son reglas estables documentadas; el builder valida formatos contra fuentes oficiales del país si hay duda del algoritmo de dígito verificador. No requiere WebSearch live (formatos no cambiaron post-2026-01).
- Fuentes canónicas internas: `design-system-canon.md` (accessed 2026-06-11), `ADR-vitalia-004`, `shell-routes.ts` (patrón N3 vivo).

## § Open Questions for PM

1. **Fiscal-id dígito verificador:** ¿el validador exige el dígito verificador completo (CUIT mód-11) o solo formato/longitud? RONDA 2 spec dice "formato {PAÍS}". Propuesta: **formato + longitud + checksum donde el algoritmo es estándar (AR CUIT, UY RUT)**; solo longitud donde el checksum varía. Confirmar alcance MVP.
2. **Specialty catalog source:** ¿el catálogo de especialidades por país sale de una lista curada (hardcoded brand-local en `specialty_catalog.py`) o debe consumir una fuente externa? Propuesta: **curado brand-local** (lift candidate). Confirmar contenido inicial por país (qué especialidades incluir AR/PE/MX/CL/CO/UY) — o si el builder usa el set de `vision.md` Tier 1-3.
3. **DPO data source:** ¿de dónde lee el DPO (`get_dpo_reference`)? RONDA 2 dice "se gestiona en Seguridad y cumplimiento" pero esa caja puede no tener endpoint aún. Propuesta: leer de `tenant.config_json.compliance.dpo` si existe, sino mostrar empty state "Aún no configurado" + link. Confirmar.
4. **`config/cuenta` route group:** la spec lista `app/[tenantId]/(shell-organism)/config/cuenta/`. El shell usa dispatcher `[agent]/[subtab]` para placeholders. Como `config.cuenta` pasa a static, se crea la ruta estática real (mismo patrón que `lisa/marca`). Confirmado por análisis — no bloquea, pero PM ratifica que `config` static segment no colisiona con el dispatcher `[agent]`.
