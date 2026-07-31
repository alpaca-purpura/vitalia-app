---
proposal_id: 2026-05-17-offer-studio-multi-session-maintenance
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
  - vitalia/docs/product/stories/vitalia-ux-discovery/ (Batch 5 fidelización adherencia + Batch 4 agenda)
  - vitalia/docs/product/stories/vitalia-slice-1-fidelizacion/
  - vitalia/docs/product/stories/vitalia-slice-1-agenda/
origin_brands: [vitalia]
detected_by: /architect-orchestrator (2026-05-17 ready package emission)

# Target
target_package: core/luana-core-offer-studio
target_module: src/luana_core_offer_studio/domain/offer.py + offer_format_catalog.py + ai_schemas
target_ep: null  # extiende contract existente; no nueva EP

# Impact assessment
semver_bump: minor                       # nuevas columnas opcionales + nuevo enum value, no breaking
breaking_change: false
brands_affected_consumers:
  - vitalia                              # origen — needs Slice 1 fidelización + agenda
  - comunify                             # cohort courses ya tienen sessions_expected nativo (refactor consolidation)
  - fitflow                              # memberships necesitan maintenance_schedule (membership renewals)
  - nicolify                             # B2B services con horas facturables pueden adoptar sessions_expected
  - lupulo                               # experiencias gastronómicas multi-curso (degustaciones N pasos)
  - saasora                              # subscriptions tienen affinity con maintenance_schedule (renewals)
  - retailly                             # subscription products + cart recovery cadence
  - guestly                              # paquetes turísticos multi-noche + maintenance entre estadías
  - inmoflow                             # post-venta inmobiliaria seguimiento periódico (no urgente)
  - fixia                                # servicios hogar mantenimiento periódico (limpieza, fumigación, A/C tune)
brands_at_risk_regression: []            # nullable columns + default safe (NONE/false), no risk to existing brands

# Lift plan
lift_estimated_effort: "1-2 days (engine catalog bump + 1 brand consumer migration vitalia + arch tests)"
lift_owner: /architect-orchestrator (engine modify) + /dev-team builder-backend
arch_test_downstream_required: true       # R3 mandatory — corre arch fitness todos brands shipped
migration_notes_required: false           # nullable + safe defaults
---

# Promotion Proposal — offers multi-session + maintenance schedule columns

## 1. Patrón a promover

Vitalia Slice 1 fidelización adherencia (Batch 5 ratificado Chris 2026-05-17) + agenda (Batch 4) requieren saber si una offer es **multi-sesión** y/o requiere **mantenimiento periódico** para automatizar re-engagement workflows:

- `requires_multi_session` (boolean, default false) — tratamientos que necesitan ≥2 sesiones (ortodoncia, blanqueamiento, depilación curso completo)
- `sessions_expected` (int nullable) — número total de sesiones esperadas (N=4 para depilación, N=12 para ortodoncia)
- `gap_alert_days` (int nullable) — máximo gap entre sesiones antes que cron detecte abandono multi-sesión (typically 14-30 días dental, 60-90 ortodoncia)
- `maintenance_schedule` (enum: `NONE | MONTHLY | QUARTERLY | BIANNUAL | ANNUAL | CUSTOM`, default `NONE`) — cadencia mantenimiento periódico (limpieza dental c/6m = BIANNUAL, implante anual = ANNUAL, depilación maintenance c/3m = QUARTERLY)
- `maintenance_custom_days` (int nullable) — usado cuando `maintenance_schedule = CUSTOM` (e.g., 45 días)

**Origen story:**
- Vitalia [[vitalia-ux-discovery]] Batch 5 fidelización — 4 patrones automatización (multi-sesión incompleto + follow-up médico + mantenimiento periódico + ausencia prolongada) requieren estos fields en offers
- Vitalia [[vitalia-ux-discovery]] Batch 4 agenda — sheet cobro Capa 2 muestra `sessions_completed / sessions_expected` per appointment cuando `requires_multi_session=true`

## 2. Por qué cross-brand

El concepto de offer multi-sesión + maintenance schedule trasciende salud. **9/10 brands portfolio** tienen offers que encajan en este modelo:

| Brand | Aplicabilidad | Razón |
|---|---|---|
| vitalia | ya implementa (Slice 1) | origen — fidelización adherencia 4 patrones |
| comunify | ya implementa parcial | cohort courses tienen sessions_expected nativo (Story 12 shipped) — refactor consolidation to engine canonical contract |
| fitflow | candidato | memberships gym/yoga renewal cycle = maintenance_schedule MONTHLY; programas multi-sesión (Crossfit 12 weeks) = requires_multi_session |
| nicolify | candidato | B2B services horas facturables → sessions_expected; retainer renewals → maintenance_schedule MONTHLY |
| lupulo | candidato | degustación multi-curso (5 pasos = sessions_expected=5); wine club membership = maintenance_schedule MONTHLY |
| saasora | candidato | trial → paid conversion sessions; subscription renewals = maintenance_schedule MONTHLY/ANNUAL |
| retailly | candidato | subscription products (café mensual, pet food MONTHLY); replenishment = maintenance_schedule |
| guestly | candidato | paquetes turísticos multi-noche (sessions_expected=N noches); annual loyalty trip = maintenance_schedule ANNUAL |
| inmoflow | candidato | post-venta seguimiento periódico (ANNUAL check-in); maintenance plans hipotecarios |
| fixia | candidato | mantenimiento periódico hogar (fumigación c/3m, limpieza A/C anual, jardinería QUARTERLY) — **caso de uso fortísimo** |
| **no aplica** | — | (ninguna brand del portfolio descalifica) |

10/10 brands aplican. **Justificación cross-brand fortísima.** Fixia + Vitalia + Fitflow + Saasora + Retailly tienen los casos de uso más obvios.

## 3. Análisis técnico

### Schema actual

Engine `core/luana-core-offer-studio/src/luana_core_offer_studio/domain/offer.py` define el contract base offer + catalogs (archetype, value_level, format, variant, biz_type, ladder_hints, preset — 7 catalogs DAG). Las columnas propuestas extienden el offer domain model con metadata adherencia/cadencia.

Comunify Story 12 (shipped) tiene `sessions_expected` en su offer table local — pattern already proven, pero NO está en engine canonical → otras brands lo re-implementan ad-hoc. Esto es **anti-patrón cross-brand mirror** (.claude/rules/anti-duplication.md).

### Schema propuesto contract engine

```python
# core/luana-core-offer-studio/src/luana_core_offer_studio/domain/offer.py
# (domain model + Pydantic schema extension)

from enum import StrEnum

class MaintenanceScheduleEnum(StrEnum):
    NONE = "NONE"
    MONTHLY = "MONTHLY"           # cada 30 días aprox
    QUARTERLY = "QUARTERLY"       # cada 90 días aprox
    BIANNUAL = "BIANNUAL"         # cada 180 días aprox
    ANNUAL = "ANNUAL"             # cada 365 días aprox
    CUSTOM = "CUSTOM"             # use maintenance_custom_days

class OfferAdherenceContract(Protocol):
    """Columns brand `offers` tables MUST implement (post 2026-05-17 contract bump)."""
    requires_multi_session: bool                       # default False
    sessions_expected: int | None                      # >= 1 if requires_multi_session else None
    gap_alert_days: int | None                         # cron threshold
    maintenance_schedule: MaintenanceScheduleEnum      # default NONE
    maintenance_custom_days: int | None                # required if maintenance_schedule == CUSTOM
```

### Migration approach per consumer brand

Cada brand consumer ejecuta:

```python
# {brand}/backend/alembic/versions/YYYY_MM_DD_HHMM_{brand}_offer_adherence_columns.py
def upgrade():
    # Enum type (engine canonical name to enable cross-brand portability)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE maintenance_schedule_enum AS ENUM
                ('NONE', 'MONTHLY', 'QUARTERLY', 'BIANNUAL', 'ANNUAL', 'CUSTOM');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    # Columns idempotent
    op.execute("""
        ALTER TABLE offers
            ADD COLUMN IF NOT EXISTS requires_multi_session BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS sessions_expected INTEGER,
            ADD COLUMN IF NOT EXISTS gap_alert_days INTEGER,
            ADD COLUMN IF NOT EXISTS maintenance_schedule maintenance_schedule_enum NOT NULL DEFAULT 'NONE',
            ADD COLUMN IF NOT EXISTS maintenance_custom_days INTEGER
    """)
    # Check constraints
    op.execute("""
        ALTER TABLE offers
            ADD CONSTRAINT chk_offer_sessions_expected_positive
                CHECK (sessions_expected IS NULL OR sessions_expected >= 1),
            ADD CONSTRAINT chk_offer_maintenance_custom_days_valid
                CHECK (
                    (maintenance_schedule = 'CUSTOM' AND maintenance_custom_days >= 1)
                    OR (maintenance_schedule <> 'CUSTOM' AND maintenance_custom_days IS NULL)
                )
    """)
```

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Brand consumer no opt-in → adherence_port falla por field missing | Baja | Port define `| None` opcional. Arch fitness en brand consumer detecta. |
| Comunify Story 12 ya tiene `sessions_expected` con default distinto → conflict | Media | Migration cross-brand audit — `/pm-luana` ratifica que comunify column type/default coincide. Si no, migration adapter. |
| Cron job `multi_session_gap_sweep` falla porque brand no setea `gap_alert_days` | Baja | Cron filtra `WHERE gap_alert_days IS NOT NULL`. Default behavior = no alert. |
| Bump `_CATALOG_VERSION` offer-studio engine forzado | Media | Test arch fitness `test_catalog_version_bump.py` ambos stacks (engine + brand consumer) corre en cada brand activa |
| Migration check constraints rompen brand legacy con data inconsistente | Baja | Backfill pre-constraint: UPDATE offers SET maintenance_schedule = 'NONE' WHERE maintenance_schedule IS NULL antes ADD constraint |

## 4. Lift plan

### Pre-lift checklist

- [ ] Generalización contract en `core/luana-core-offer-studio/src/luana_core_offer_studio/domain/offer.py` (MaintenanceScheduleEnum + OfferAdherenceContract)
- [ ] Tests unitarios en `core/luana-core-offer-studio/tests/domain/test_offer_adherence_contract.py`
- [ ] Bump `_CATALOG_VERSION` en `offer.py` (offer-catalogs.md rule)
- [ ] Documentación contract en `docs/core-modules/offer-studio.md` (sección offer_adherence)
- [ ] CHANGELOG entry en `core/luana-core-offer-studio/CHANGELOG.md` (minor bump)
- [ ] Vitalia migration drafted en `vitalia/backend/alembic/versions/` (T-be-migration-015)
- [ ] Comunify reconciliation check — `sessions_expected` column existente alinea con engine canonical contract

### Lift execution (orden)

1. **Step 1 (engine modify):** `/architect-orchestrator` edita `core/luana-core-offer-studio/src/luana_core_offer_studio/domain/offer.py` agregando `MaintenanceScheduleEnum` + `OfferAdherenceContract` Protocol + bump `_CATALOG_VERSION`
2. **Step 2 (engine tests):** crear `test_offer_adherence_contract.py` + `test_catalog_version_bumped.py`
3. **Step 3 (engine semver):** bump `core/luana-core-offer-studio/pyproject.toml::version` minor
4. **Step 4 (engine docs):** actualizar `docs/core-modules/offer-studio.md` con promotion history entry
5. **Step 5 (vitalia consumer):** vitalia migration `ALTER TABLE offers ADD COLUMN IF NOT EXISTS ...` + enum type + check constraints (T-be-migration-015 en `vitalia/backend/alembic/versions/`)
6. **Step 6 (comunify reconciliation):** verificar comunify `sessions_expected` existing column compatible con engine contract; si no, brand-local alembic migration adapta type/default
7. **Step 7 (R3 arch test downstream):** `make arch-test` (engine + all 4 shipped brands)
8. **Step 8 (rollback path):** revert engine commit + revert vitalia migration

### Post-lift (brands consumer opt-in incremental)

- **Vitalia (origen):** automático via T-be-migration-015 + integración en cron jobs `multi_session_gap_sweep` + `maintenance_due_sweep`
- **Comunify (reconciliation):** si reconciliation Step 6 detect mismatch, abrir story `comunify-offer-adherence-canonical-adopt`
- **Fitflow, Saasora, Retailly, Guestly, Inmoflow, Fixia (bootstrap pendientes):** heredan canonical contract al bootstrap
- **Nicolify, Lupulo:** opt-in cuando primera story brand-specific lo necesite

## 5. Decisión

**Recomendación `/pm-luana`:** APPROVED (con reconciliation check Step 6)

**Razón:**
- Patrón ultra-aplicable (10/10 brands portfolio, fortísimo caso de uso fixia + vitalia + fitflow + saasora)
- Comunify ya tiene `sessions_expected` localmente — esta proposal consolida a engine canonical → elimina cross-brand drift futuro
- Backward compat garantizado (nullable + safe defaults `NONE`/`false`)
- Riesgo de regression bajo (check constraints permisivos, migration idempotente)
- Bloquea T-be-migration-015 sub-task vitalia-slice-1-infra-cross-cutting + cron jobs vitalia-slice-1-fidelizacion + sheet cobro multi-session vitalia-slice-1-agenda
- Costo lift ≤ 1-2 days

**Ratificación Chris:** _pending hasta state=accepted_

## 6. Bitácora

- 2026-05-17: opened by /pm-luana request /pm-vitalia post /architect ready package vitalia-ux-discovery (detect engine modify obligatorio T-be-migration-015). State: draft.
- 2026-05-17 (sesión /pm-vitalia close-slice-1): Chris ratified APPROVED. State: draft → accepted.
- 2026-05-17 (sesión idem): engine modify executed by orchestrator (main Claude context post lift gate):
  - Added `MaintenanceScheduleEnum` to `core/luana-core-offer-studio/src/luana_core_offer_studio/domain/enums.py` (6 values: NONE/MONTHLY/QUARTERLY/BIANNUAL/ANNUAL/CUSTOM).
  - Added `OfferAdherenceContract` Protocol to `core/luana-core-offer-studio/src/luana_core_offer_studio/domain/offer.py` (`requires_multi_session` + `sessions_expected` + `gap_alert_days` + `maintenance_schedule` + `maintenance_custom_days`).
  - Bumped `core/luana-core-offer-studio/pyproject.toml::version` 0.1.0 → 0.2.0.
  - Created `core/luana-core-offer-studio/tests/domain/test_offer_adherence_contract.py` (13 tests: enum values stable + Protocol shape + 6 enum values parametrize + multi-session + maintenance + custom + non-conforming fail). All PASS.
  - Created `core/luana-core-offer-studio/CHANGELOG.md` (Keep-a-Changelog format, 0.2.0 entry + 0.1.0 initial).
  - **NOTA `_CATALOG_VERSION`:** NO bumpeamos los 6 catalog version constants (`api/{archetypes,formats,variant_structures,value_levels,offer_type_presets,offer_ladder_hints}.py`). El `OfferAdherenceContract` es un Protocol contract layer (typing only), NO un catalog enum nuevo. Los 7 catalog axes existentes (archetype/value_level/format/section/variant/biz_type/ladder_hints/preset) no cambian. Esto difiere de la proposal Section 4 pre-lift checklist que mencionaba bump — documentado en CHANGELOG.md.
  - Gate-runner R3 downstream: engine full regression PASS (888 tests + 12 skipped) + vitalia arch fitness PASS (166 tests). Nicolify/Comunify R3 blocked by pre-existing `/home/chris/` hardcoded paths debt (orthogonal, NOT regression).
- State: accepted → migrated.

## 7. Cross-references

- Origin stories: `vitalia/docs/product/stories/vitalia-ux-discovery/` Batch 5 fidelización + Batch 4 agenda
- Slice 1 split: `vitalia/docs/product/stories/vitalia-slice-1-infra-cross-cutting/` (T-be-migration-015 blocker) + `vitalia-slice-1-fidelizacion/` + `vitalia-slice-1-agenda/`
- Target package: `core/luana-core-offer-studio/`
- Target module: `core/luana-core-offer-studio/src/luana_core_offer_studio/domain/offer.py`
- Engine docs: `docs/core-modules/offer-studio.md` (post lift section "offer_adherence_contract")
- Process: `docs/promotion-protocol/README.md`
- Related rules: `.claude/rules/offer-catalogs.md` (catalog versioning + arch test) · `.claude/rules/anti-duplication.md` § lift shared (comunify mirror)
- Reconciliation reference: `comunify/docs/product/capabilities/offer/*.yaml` (verificar `sessions_expected` shape compatible)
