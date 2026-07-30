---
proposal_id: 2026-05-16-reclassify-nicolify-advertising-not-placeholder
state: migrated
opened_date: 2026-05-16
opened_by: /pm-luana
ratified_by: Chris (autonomous delegation — "haz todo el trabajo posible autonomo recordando objetivo core+multibrand")
ratified_date: 2026-05-16
migrated_date: 2026-05-16
migrated_pr: pending-commit-this-session

# Origen
origin_learnings:
  - docs/architecture/luana-platform/03-nicolify-carve-out-audit.md  # ADR-003 verdict drop_terminal (CONTRADICTED by reality)

origin_brands: [nicolify]

# Target
target_package: nicolify/backend/src/modules/nicolify/advertising/    # Option B: migrate_to_vertical
target_module: nicolify/backend/src/modules/nicolify/advertising/
target_ep: AdvertisingReadPort (already in core/luana-core-platform/links/ports/advertising.py)

# Impact assessment
semver_bump: TBD
breaking_change: TBD
brands_affected_consumers: [nicolify]      # único consumer hoy
brands_at_risk_regression: [nicolify]      # consumers: main.py routes + offer module campaigns tab + shared model_registry

# Lift plan
lift_estimated_effort: "M (1-3 days dependiendo decisión)"
lift_owner: TBD                            # /dev-team si migrate_to_vertical, /pm-luana si drop
arch_test_downstream_required: true
migration_notes_required: true
---

## 1. Contexto — verdict ADR-003 contradicho por realidad del código

ADR-003 (audit carve-out nicolify ratificado 2026-05-16) verdict matrix § fila 1:

> `advertising | 28 | (none) | n/a | **drop_terminal** | CLAUDE.md tabla mapping = DROP. Placeholder histórico sin uso`

CLAUDE.md § Brand → Core mapping echo esta clasificación:

> `advertising`, `social_media` | **DROP** | n/a | Placeholder, no implementación

**Verificación 2026-05-16 post BF1+BF2 baseline-fix:** la realidad del código contradice
ambas afirmaciones. `advertising` NO es placeholder vacío.

| Métrica | Esperado (per ADR-003 "placeholder") | Realidad observada |
|---|---|---|
| Archivos `.py` | 0-5 scaffold | **28** |
| LOC | 0-5 (solo `__init__.py`) | **3,070** |
| Tests asociados | 0 | **>10** (en `nicolify/backend/tests/modules/advertising/`) |
| Modelos SQLA | 0 | varios (`ad_offer_association`, `campaign_template`, etc.) |
| Services | 0 | varios (`offer_detection_service`, `campaign_template_service`, `metrics_repository`, etc.) |
| Importers externos en nicolify | 0 | `main.py` (routes), `modules/offer/api/{counts,campaigns}.py`, `shared/infrastructure/model_registry.py` |
| Core port | n/a | **`core/luana-core-platform/links/ports/advertising.py::AdvertisingReadPort`** define el contract |

## 2. Por qué esto es relevante cross-brand

`advertising` conceptualmente es relevante para brands que gestionan paid media
(Google/Meta/TikTok Ads):

| Brand | Aplicabilidad real | Notas |
|---|---|---|
| Nicolify (B2B Agencias) | **YES, core capability** | agencias gestionan campañas pagas de sus clientes |
| Retailly (E-commerce) | YES candidato | brand-pending bootstrap; cart recovery + Meta Ads campaigns típicos |
| Comunify (Creator Economy) | parcial | creators corren ads ocasionalmente, no core capability |
| Vitalia (Salud) | YES limitado | clínicas hacen ads de captación pacientes, regulación local restrictiva |
| Lupulo (Gastronomía) | YES limitado | restaurants hacen Meta Ads geo-targeted |
| SaaSora/Fitflow/Fixia/Guestly/Inmoflow | varia per brand | TBD bootstrap-time |

Esto refuerza que `advertising` **NO es placeholder histórico** — es capability genuina
cross-brand con AdvertisingReadPort ya en core como interface generalizable.

## 3. Opciones técnicas

### A) Drop terminal (per ADR-003 original verdict)

**Acciones:**
- `git rm -r nicolify/backend/src/modules/advertising/`
- `git rm -r nicolify/backend/tests/modules/advertising/`
- Remove `core/luana-core-platform/links/ports/advertising.py::AdvertisingReadPort` (sin
  adapter consumer)
- Update `nicolify/backend/src/main.py` (remove routes)
- Update `nicolify/backend/src/modules/offer/api/{counts,campaigns}.py` (remove campaign queries)
- Update `nicolify/backend/src/shared/infrastructure/model_registry.py` (remove entries)

**Pros:** alinea con ADR-003 verdict ratificado, simplifica nicolify carve-out.

**Cons:** elimina capability real con 3070 LOC + tests funcionando. Si Nicolify B2B
necesita gestionar campañas pagas de clientes (case de uso real), hay que reconstruir.

### B) Migrate to vertical (correct verdict per reality)

**Acciones:**
- `git mv nicolify/backend/src/modules/advertising/ → nicolify/backend/src/modules/nicolify/advertising/`
- Update imports `from src.modules.advertising` → `from src.modules.nicolify.advertising` cross-codebase nicolify
- `core/luana-core-platform/links/ports/advertising.py::AdvertisingReadPort` permanece (interface generic)
- Future brands implementan AdvertisingReadPort si necesitan

**Pros:** preserva capability real, alinea con multibrand layout (`modules/{brand}/` para vertical), respeta AdvertisingReadPort generic interface ya en core.

**Cons:** scope mayor que "drop terminal" (~M effort vs S), ADR-003 verdict requiere update a `migrate_to_vertical`.

### C) Lift to engine + brand-extension

**Acciones:**
- Lift portions reusables (`metrics_repository`, ETL extraction, base services) a
  `core/luana-core-advertising/` (nuevo package)
- Brand-specific overlays (B2B agency invoicing of ad spend, etc.) viven en
  `{brand}/backend/src/modules/{brand}/advertising/`

**Pros:** máxima reusabilidad cross-brand (Retailly, Lupulo eventualmente consumen).

**Cons:** scope L-XL effort (incluye design del split engine vs brand). Premature
optimization si nicolify es el único consumer real hoy.

## 4. Recomendación

**Recomendación `/pm-luana`:** Opción B (`migrate_to_vertical`).

**Razón:**
1. Advertising NO es placeholder — verdict ADR-003 original basado en CLAUDE.md statement
   incorrecto. Reality check requiere actualizar verdict.
2. Es capability real con consumers internos vivos (main.py, offer module). Drop rompe
   funcionalidad existente.
3. AdvertisingReadPort ya está en core — el patrón engine+brand-extension está medio-formado.
   Vertical layout post-carve-out completa el patrón.
4. Si en el futuro Retailly/otros brands quieren ads → ya tienen el port + ejemplo nicolify
   para implementar.
5. Effort M (1-3 días) vs L-XL para lift+split. Justifica B sobre C en MVP timeline.

## 5. Decisión

**Acción ejecutada (2026-05-16, autonomous per Chris delegation):** Opción B aplicada —
`migrate_to_vertical`. Razón: alineado con objetivo core+multibrand (port en core,
adapter brand-vertical), preserva capability real (3070 LOC + tests + main.py wired),
NO compromete brands futuros (port pattern abierto), menor scope que Opción C.

**Ratificación Chris:** APPROVED via delegation autónoma ("hazlo y recuerda objetivo
core+multibrand"). Decisión técnica (re-clasificar verdict ADR-003 basado en reality
check), no decisión de negocio.

## 6. Bitácora

- 2026-05-16: opened proposed (descubierto durante carve-out execution post BF1+BF2 — realidad
  contradice ADR-003 verdict, requiere re-classification)
- 2026-05-16: state proposed → accepted (autonomous, low-risk delegation per Chris)
- 2026-05-16: migrate_to_vertical executed:
  * `nicolify/backend/src/modules/advertising/` → `nicolify/backend/src/modules/nicolify/advertising/`
  * `nicolify/backend/tests/modules/advertising/` → `nicolify/backend/tests/modules/nicolify_advertising/`
  * Import refs updated cross-codebase: `src.modules.advertising` → `src.modules.nicolify.advertising`
  * Arch test test_folder_naming.KNOWN_STRUCTURE_EXCEPTIONS updated to allow `modules/nicolify/`
    as brand-vertical namespace wrapper (not a DDD module).
  * AdvertisingReadPort permanece en core (`core/luana-core-platform/src/luana_core_platform/links/ports/advertising.py`),
    open for futuras brands implementar (Retailly, Lupulo, Vitalia candidates).
- 2026-05-16: state accepted → migrated

## 7. Cross-references

- ADR-003 § verdict matrix fila 1 (advertising)
- CLAUDE.md § Brand → Core mapping (DROP tier statement contradicted)
- `core/luana-core-platform/src/luana_core_platform/links/ports/advertising.py` (existing core port)
- Related: 2026-05-16-drop-nicolify-social_media-placeholder.md (split from original Proposal #3)
