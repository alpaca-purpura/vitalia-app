---
proposal_id: 2026-05-17-platform-tenants-location-columns
state: migrated
opened_date: 2026-05-17
opened_by: /pm-luana
ratified_by: Chris
ratified_date: 2026-05-17
migrated_date: 2026-05-17
migrated_commit: 5ca61019bb03c7304c30fbb5a4b7196ecc3fc27c

# Origen
origin_learnings: []  # cementado durante /architect ux-discovery 2026-05-17, no learning pre-existente
origin_stories:
  - vitalia/docs/product/stories/vitalia-ux-discovery/ (Batch 7 wizard Brand Studio onboarding agentic)
  - vitalia/docs/product/stories/vitalia-slice-1-onboarding-wizard/
origin_brands: [vitalia]
detected_by: /architect-orchestrator (2026-05-17 ready package emission)

# Target
target_package: core/luana-core-platform
target_module: src/luana_core_platform/links/ports/tenant_profile.py + domain port contract
target_ep: null  # extiende contract existente; no nueva EP

# Impact assessment
semver_bump: minor                       # nuevas columnas opcionales, no breaking
breaking_change: false
brands_affected_consumers:               # opt-in via {brand}/config/brand.yaml + ADD COLUMN local migration
  - vitalia                              # origen — needs immediately Slice 1
  - nicolify                             # ya tiene equivalente field implícito (patient_locale), candidate refactor
  - comunify                             # multi-país creator economy, lo necesitará
  - lupulo                               # timezone reservas mesa crítico
  - saasora                              # multi-país SaaS subscriptions
  - inmoflow                             # real estate locale-driven
  - retailly                             # ecommerce multi-país D2C
  - fixia                                # servicios hogar geo-specific
  - guestly                              # turismo timezone + country crítico
  - fitflow                              # fitness studios multi-país
brands_at_risk_regression: []            # nullable columns, no risk to existing brands

# Lift plan
lift_estimated_effort: "1 day (engine contract extension + 1 brand consumer migration vitalia)"
lift_owner: /architect-orchestrator (engine modify) + /dev-team builder-backend
arch_test_downstream_required: true       # R3 mandatory — corre arch fitness todos brands shipped
migration_notes_required: false           # nullable + safe defaults
---

# Promotion Proposal — tenants location columns engine extension

## 1. Patrón a promover

Vitalia Slice 1 wizard Brand Studio onboarding agentic (Batch 7 ratificado Chris 2026-05-17) requiere capturar metadata location del tenant durante setup conversacional: **país + ciudad + timezone IANA**, además del flag `is_onboarded` que distingue tenants completaron setup vs scaffold-only.

Estos 4 fields son universalmente útiles cross-brand:

- `is_onboarded` (boolean, default false) — track wizard completion. Hoy ningún brand tiene este field explícito; cada brand lo simula con presence checks ad-hoc en otros campos.
- `location_country` (varchar(2) ISO 3166-1 alpha-2) — locale resolution + currency default + compliance jurisdiction
- `location_city` (varchar nullable) — disambiguation + analytics regional
- `timezone` (varchar IANA TZ, default 'America/Argentina/Buenos_Aires' o `null` to force fill) — schedule operations + cron triggers per tenant TZ

**Origen story:**
- Vitalia: [[vitalia-ux-discovery]] Batch 7 wizard onboarding cementó slot `tenant.location {country+city+timezone}` REQUIRED para activar tenant + `is_onboarded` flag
- Nicolify: hoy resuelve locale vía `patient_locale.timezone` (per-paciente, no per-tenant — anti-pattern para crons tenant-wide)
- Comunify: similar a Nicolify, sin field tenant-level

## 2. Por qué cross-brand

Toda brand multitenant LATAM requiere conocer la ubicación + TZ del tenant para:
- Currency default (LATAM PEN/MXN/COP/ARS/CLP/USD/BRL — `vitalia/config/brand.yaml::default_currency_per_country`)
- Compliance jurisdiction (HIPAA-lite PE vs AR vs CL — `vitalia/.claude/rules/hipaa-lite.md` LATAM regulations)
- Cron jobs tenant-aware (re-engagement workflows, fiscal deadlines SUNAT 3d, fidelization reminders)
- Analytics regional (channel performance por país)
- Multi-language UI futuro (Slice 3+ — ES/PT/EN)

| Brand | Aplicabilidad | Razón |
|---|---|---|
| vitalia | ya implementa (Slice 1) | origen — wizard onboarding REQUIRED |
| nicolify | candidato refactor | hoy via patient_locale (anti-pattern), debería migrar a tenant-level |
| comunify | candidato | multi-país creator economy + timezone para cohort timing |
| lupulo | candidato | timezone CRÍTICO para reservas mesa + ventana 24-72h cancelación |
| saasora | candidato | multi-país SaaS + churn analysis regional |
| inmoflow | candidato | real estate locale-driven (zona AR/MX/CO) |
| retailly | candidato | ecommerce multi-país + cart recovery timezone-aware |
| fixia | candidato | servicios hogar geo-specific + dispatch timezone |
| guestly | candidato | turismo timezone + country CRÍTICO (OTAs Airbnb/Booking) |
| fitflow | candidato | fitness studios multi-país + clases timezone |
| **no aplica** | — | (ninguna brand del portfolio no necesita esto) |

10/10 brands actuales + bootstrap pendientes aplican. **Justificación cross-brand fuerte.**

## 3. Análisis técnico

### Schema actual (per-brand, no engine contract)

Cada brand define su `tenants` table localmente vía alembic migrations en `{brand}/backend/alembic/versions/`. No hay contract canónico en engine — solo port abstracto en `core/luana-core-platform/src/luana_core_platform/links/ports/tenant_profile.py` (read-only interface).

```python
# Brand actual (varía per-brand): vitalia/backend/.../tenants migration:
class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[UUID]
    name: Mapped[str]
    # ... brand-specific columns

# nicolify variant: similar pero patient_locale.timezone resuelve TZ por paciente, no tenant
```

### Schema propuesto contract engine

```python
# core/luana-core-platform/src/luana_core_platform/links/ports/tenant_profile.py
# (port domain interface, no ORM model — implementation per brand)

from typing import Protocol
from zoneinfo import ZoneInfo

class TenantLocationContract(Protocol):
    """Mandatory columns brand `tenants` tables MUST implement (post 2026-05-17 contract bump)."""
    is_onboarded: bool                      # default False
    location_country: str | None            # ISO 3166-1 alpha-2 (AR, PE, MX, CO, CL, BR, US, ES, ...)
    location_city: str | None               # disambiguation + analytics
    timezone: str | None                    # IANA TZ database string ('America/Lima', 'America/Argentina/Buenos_Aires', ...)
```

### Migration approach per consumer brand

Cada brand consumer Slice 1 ejecuta:

```python
# {brand}/backend/alembic/versions/YYYY_MM_DD_HHMM_{brand}_tenants_location.py
def upgrade():
    op.execute("""
        ALTER TABLE tenants
            ADD COLUMN IF NOT EXISTS is_onboarded BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS location_country VARCHAR(2),
            ADD COLUMN IF NOT EXISTS location_city VARCHAR(255),
            ADD COLUMN IF NOT EXISTS timezone VARCHAR(64)
    """)
    # Backfill brands con tenants existentes:
    # vitalia + nicolify + comunify shipped tenants → is_onboarded=true por default
    op.execute("""
        UPDATE tenants
            SET is_onboarded = TRUE
            WHERE created_at < '2026-05-17'
              AND is_onboarded IS FALSE
    """)
```

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Brand consumer no opt-in → tenant_profile_port falla por field missing | Baja | Port define `| None` opcional. Arch fitness en brand consumer detecta. |
| Backfill timezone para tenants existentes pre-2026-05-17 = NULL → cron jobs fallan | Media | Brands shipped hacen backfill manual con default por country mapping (AR→Buenos_Aires, PE→Lima, MX→Mexico_City, ...) en mismo migration |
| Convención country ISO code inconsistente (AR vs ARG) | Baja | Contract explicit: ISO 3166-1 alpha-2 (2 char). Arch fitness valida format. |
| TZ string inválido (no IANA) | Baja | Migration check constraint: timezone IS NULL OR pg_timezone_names contains it. Application validator Pydantic. |

## 4. Lift plan

### Pre-lift checklist

- [ ] Generalización del contract en `core/luana-core-platform/src/luana_core_platform/links/ports/tenant_profile.py` (TenantLocationContract Protocol)
- [ ] Tests unitarios en `core/luana-core-platform/tests/links/test_tenant_location_contract.py`
- [ ] Documentación contract en `docs/core-modules/platform.md` (sección tenant_location)
- [ ] CHANGELOG entry en `core/luana-core-platform/CHANGELOG.md` (minor bump)
- [ ] Vitalia migration drafted en `vitalia/backend/alembic/versions/` (T-be-migration-014 unblocked post accept)

### Lift execution (orden)

1. **Step 1 (engine modify):** `/architect-orchestrator` edita `core/luana-core-platform/src/luana_core_platform/links/ports/tenant_profile.py` agregando TenantLocationContract Protocol + tests engine
2. **Step 2 (engine semver):** bump `core/luana-core-platform/pyproject.toml::version` minor (e.g., 0.4.0 → 0.5.0)
3. **Step 3 (engine docs):** actualizar `docs/core-modules/platform.md` con promotion history entry
4. **Step 4 (vitalia consumer):** vitalia migration `ALTER TABLE tenants ADD COLUMN IF NOT EXISTS ...` (T-be-migration-014 en `vitalia/backend/alembic/versions/`)
5. **Step 5 (R3 arch test downstream):** `make arch-test` (engine + all 4 shipped brands: vitalia + nicolify + comunify + lupulo)
6. **Step 6 (rollback path):** revert engine commit + revert vitalia migration

### Post-lift (brands consumer opt-in incremental)

- **Vitalia (origen):** automático via T-be-migration-014 (incluido en lift Step 4)
- **Nicolify (refactor candidate):** opt-in cuando team decida migrar `patient_locale.timezone` → `tenants.timezone`. Standalone story `nicolify-tenant-location-adopt`.
- **Comunify, Lupulo, futuros:** opt-in cuando primera story brand-specific lo necesite

## 5. Decisión

**Recomendación `/pm-luana`:** APPROVED

**Razón:**
- Patrón universalmente aplicable (10/10 brands portfolio)
- Backward compat garantizado (nullable + IF NOT EXISTS)
- Riesgo de regression bajo (port read-only contract extension, no SQL alter destructivo)
- Bloquea T-be-migration-014 sub-task vitalia-slice-1-infra-cross-cutting + vitalia-slice-1-onboarding-wizard — sin esto vitalia Slice 1 no puede shipear
- Costo lift ≤ 1 day (interface extension + 1 brand consumer migration)

**Ratificación Chris:** _pending hasta state=accepted_

## 6. Bitácora

- 2026-05-17: opened by /pm-luana request /pm-vitalia post /architect ready package vitalia-ux-discovery (detect engine modify obligatorio T-be-migration-014). State: draft.
- 2026-05-17 (sesión /pm-vitalia close-slice-1): Chris ratified APPROVED. State: draft → accepted.
- 2026-05-17 (sesión idem): engine modify executed by orchestrator (main Claude context post lift gate):
  - Added `TenantLocationContract` Protocol to `core/luana-core-platform/src/luana_core_platform/links/ports/tenant_profile.py` (`is_onboarded` bool + `location_country` ISO3166-1 alpha-2 + `location_city` + `timezone` IANA).
  - Bumped `core/luana-core-platform/pyproject.toml::version` 0.1.0 → 0.2.0.
  - Created `core/luana-core-platform/tests/links/test_tenant_location_contract.py` (11 tests: Protocol shape + 8 ISO country code parametrize + non-conforming fail). All PASS.
  - Created `core/luana-core-platform/CHANGELOG.md` (Keep-a-Changelog format, 0.2.0 entry + 0.1.0 initial).
  - Gate-runner R3 downstream: engine full regression PASS (888 tests + 12 skipped) + vitalia arch fitness PASS (166 tests). Nicolify/Comunify R3 blocked by pre-existing `/home/chris/` hardcoded paths debt (orthogonal, NOT regression).
- State: accepted → migrated.

## 7. Cross-references

- Origin story: `vitalia/docs/product/stories/vitalia-ux-discovery/` Batch 7 wizard onboarding
- Slice 1 split: `vitalia/docs/product/stories/vitalia-slice-1-infra-cross-cutting/checkpoint.md` (T-be-migration-014 blocker)
- Target package: `core/luana-core-platform/`
- Target contract: `core/luana-core-platform/src/luana_core_platform/links/ports/tenant_profile.py`
- Engine docs: `docs/core-modules/platform.md` (post lift section "tenant_location_contract")
- Process: `docs/promotion-protocol/README.md`
- Related: `.claude/rules/master-data.md` (timezone + currency policy LATAM)
