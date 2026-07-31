---
proposal_id: 2026-05-16-drop-nicolify-social_media-placeholder
state: migrated
opened_date: 2026-05-16
opened_by: /pm-luana
ratified_by: Chris
ratified_date: 2026-05-16
migrated_date: 2026-05-16
migrated_pr: pending-commit-this-session

# Origen
origin_learnings:
  - docs/architecture/luana-platform/03-nicolify-carve-out-audit.md  # ADR-003 verdict drop_terminal

origin_brands: [nicolify]

# Target
target_package: n/a                        # pure drop, no lift
target_module: n/a
target_ep: null

# Impact assessment
semver_bump: patch                         # no engine API change
breaking_change: false
brands_affected_consumers: []              # no brand uses social_media module
brands_at_risk_regression: []              # placeholder, zero downstream

# Lift plan
lift_estimated_effort: "5 min"
lift_owner: /pm-luana                      # process tooling drop, no /dev-team
arch_test_downstream_required: false       # placeholder drop, no code consumers
migration_notes_required: false
---

## 1. Patrón a promover

**Drop, no lift.** `nicolify/backend/src/modules/social_media/` es un placeholder histórico
heredado del monolito Nicolify pre-multibrand-reorg. Verificación 2026-05-16:

- 5 archivos `.py` total (`__init__.py` × 5 — uno por capa DDD: api, application, domain, infrastructure, root)
- **1 LOC por archivo** (vacíos, solo declaración del paquete)
- 0 tests
- 0 referencias externas (`grep modules.social_media` retorna 0 hits en main.py, otros módulos, core, otros brands)

CLAUDE.md tabla mapping ya lo cataloga como `DROP`:

> `advertising`, `social_media` | **DROP** | n/a | Placeholder, no implementación

ADR-003 (audit carve-out nicolify) verdict matrix § fila 15: `drop_terminal`.

## 2. Por qué cross-brand

No aplica — drop puro, no hay lift a engine cross-brand.

| Brand | Aplicabilidad | Razón |
|---|---|---|
| Nicolify | placeholder existente | drop directo |
| Vitalia/Comunify/Lupulo | no consumen | jamás referenciaron este placeholder |
| Brands pendientes | no necesitan | si en el futuro alguna brand quiere social media management → nueva story brand-vertical |

## 3. Análisis técnico

### Realidad del módulo

```bash
$ find nicolify/backend/src/modules/social_media -name "*.py" -exec wc -l {} \;
1 nicolify/backend/src/modules/social_media/__init__.py
1 nicolify/backend/src/modules/social_media/api/__init__.py
1 nicolify/backend/src/modules/social_media/application/__init__.py
1 nicolify/backend/src/modules/social_media/domain/__init__.py
1 nicolify/backend/src/modules/social_media/infrastructure/__init__.py
```

5 archivos × 1 línea = scaffold sin lógica. Ningún model SQLA, ningún service, ningún
route, ningún DTO.

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Algún workflow oculto lo importa silenciosamente | Mínima | Grep cross-codebase confirmó 0 refs |
| Brand futura quiere social media management | Baja | Nuevo módulo brand-vertical desde cero es trivial; este placeholder no aporta value |

## 4. Lift plan

### Pre-drop checklist

- [x] Grep cross-codebase: 0 referencias externas
- [x] LOC verificado: 0 lógica
- [x] Tests asociados: 0
- [x] CLAUDE.md catalog DROP statement honored
- [x] ADR-003 verdict `drop_terminal` honored

### Drop execution

1. `git rm -r nicolify/backend/src/modules/social_media/`
2. Verify arch tests pass cross-brand baseline (R3 N/A — no downstream)
3. Commit

### Post-drop

Nada. Es drop terminal puro.

## 5. Decisión

**Recomendación `/pm-luana`:** APPROVED

**Razón:** placeholder vacío. Drop alinea repo con CLAUDE.md + ADR-003 verdict ratificado.
Zero risk.

**Ratificación Chris:** APPROVED 2026-05-16 (delegación autónoma per "arranca con todo el trabajo autonomo que puedas a menos que sea decisión de negocio").

## 6. Bitácora

- 2026-05-16: opened proposed (carve-out warm-up post BF1+BF2 baseline-fix)
- 2026-05-16: state proposed → accepted (autonomous, low-risk placeholder)
- 2026-05-16: drop executed → state migrated

## 7. Cross-references

- ADR-003 § verdict matrix fila 15
- CLAUDE.md § Brand → Core mapping (DROP tier)
- Related: 2026-05-16-reclassify-nicolify-advertising-not-placeholder.md (split from original Proposal #3 because advertising contradicts placeholder verdict — 3070 LOC + tests)
