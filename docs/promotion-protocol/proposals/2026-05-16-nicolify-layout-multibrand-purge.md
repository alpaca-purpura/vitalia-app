---
proposal_id: 2026-05-16-nicolify-layout-multibrand-purge
state: migrated
opened_date: 2026-05-16
opened_by: /pm-luana
ratified_by: Chris (autonomous delegation — "cierre completo nicolify antes de vitalia")
ratified_date: 2026-05-16
migrated_date: 2026-05-16
migrated_pr: Commits A-D (d3113fa, d296fc7, a26b97d, this commit)

# Origen
origin_learnings:
  - docs/architecture/luana-platform/03-nicolify-carve-out-audit.md  # Fase 4 lifts/drops pending

origin_brands: [nicolify]

# Target
target_package: nicolify/backend/src/modules/nicolify/   # vertical layout completion
target_module: nicolify/backend/src/modules/nicolify/{admin,edges,workers,persistence}/
target_ep: null                                          # layout-only, no EP touch

# Impact assessment
semver_bump: n/a                                         # brand-vertical layout, no core API
breaking_change: false                                   # zero functional change, solo path moves
brands_affected_consumers: [nicolify]                    # only nicolify touched
brands_at_risk_regression: []                            # no cross-brand impact

# Lift plan
lift_estimated_effort: "M (3-4 horas mecánico)"
lift_owner: /pm-luana                                    # patrón Waves 1-4 anteriores (commits 3b02db2, 627ff93, 880c7b4)
arch_test_downstream_required: true                      # arch fitness updates path-based
migration_notes_required: false                          # zero runtime change
---

## 1. Patrón a promover

**No es promotion brand→core.** Es **completion del carve-out multibrand layout interno de nicolify**. Post Waves 1-4 (Carve-out audit ADR-003), `nicolify/backend/src/` quedó con código brand-vertical genuino mal-ubicado en paths legacy single-brand (`src/{admin,edges,workers,shared,scripts,tests}/`). El cierre alinea con CLAUDE.md topología (`{brand}/backend/src/modules/{brand}/...`).

## 2. Por qué cross-brand (no aplica)

Layout-only completion. NO toca engine, NO toca otras brands. Aplica solo a nicolify.

Sin embargo, **establece pattern de referencia para brands futuras (saasora, inmoflow, retailly, fixia, guestly, fitflow) sobre dónde colocar admin/edges/workers/persistence brand-local**. Documentado en `_pm-brand-template/`.

## 3. Análisis técnico

### Paths a mover

| Path actual | Files | Destino | Importers a actualizar |
|---|---|---|---|
| `src/admin/` (Streamlit) | 51 | `src/modules/nicolify/admin/` | ~10 (tests + conftest + self refs) |
| `src/edges/` | 3 | `src/modules/nicolify/edges/` | 1 (main.py:159) |
| `src/workers/` (ARQ) | 2 | `src/modules/nicolify/workers/` | 4 (3 tests + doc-gen script) |
| `src/shared/infrastructure/model_registry.py` | 1 | `src/modules/nicolify/persistence/model_registry.py` | 11+ (cross-codebase: main, admin, workers, conftest, scripts/*) |
| `src/scripts/` (one-shot migrate) | 3 | `nicolify/docs/archive/2026/migrate-scripts/` | 0 (zero refs externas) |
| `src/tests/test_telegram_flow.py` | 1 | `tests/integration/test_telegram_flow.py` | 0 (misplaced) |

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Import roto post-move | Media | Audit cross-codebase grep verbatim antes commit incremental |
| Arch fitness test path-based break | Baja | 5 arch tests identificados (test_admin_panel, test_campaigns_workers_registered, test_ddd_boundaries, test_master_data, test_payment_audit_immutable, test_folder_naming) — update path constants en mismo commit |
| `main.py:159 from src.edges import` quiebra startup | Baja | Update import en commit edges |
| ARQ workers paths break | Baja | Update test_extraction_job_names + test_campaigns_workers_registered |
| Tests collection (factory missing) | Alta pre-existente | Out of scope (handoff /pm-nicolify) — NO bloquea este lift |

## 4. Lift plan

### Pre-lift checklist

- [x] Audit completo paths + importers (this proposal § 3)
- [x] Arch tests identificados que tocan paths viejos
- [x] Cross-brand mirror scan: 0 hits (`from nicolify` en vitalia/comunify/lupulo/core = 0)
- [x] ADR-003 verdict ratificado por Chris 2026-05-16

### Lift execution

**Orden de commits incrementales (riesgo creciente):**

1. **Commit A** — edges + workers (mín riesgo, pocos importers)
   - `git mv nicolify/backend/src/edges/* nicolify/backend/src/modules/nicolify/edges/`
   - `git mv nicolify/backend/src/workers/* nicolify/backend/src/modules/nicolify/workers/`
   - Update `main.py:159` import
   - Update 4 worker importers
   - Update 2 arch tests (test_campaigns_workers_registered + test_extraction_job_names)

2. **Commit B** — admin (Streamlit 51 files)
   - `git mv nicolify/backend/src/admin nicolify/backend/src/modules/nicolify/admin`
   - Update 5+ test files (tests/admin/* + test_admin_panel + costo_agentes tests)
   - Update conftest.py reference

3. **Commit C** — model_registry → persistence
   - `git mv nicolify/backend/src/shared/infrastructure/model_registry.py nicolify/backend/src/modules/nicolify/persistence/`
   - Update 11+ importers cross-codebase
   - Cleanup empty `src/shared/`

4. **Commit D** — archive scripts + relocate test_telegram_flow + arch tests final
   - `git mv nicolify/backend/src/scripts/* nicolify/docs/archive/2026/migrate-scripts/`
   - `git mv nicolify/backend/src/tests/test_telegram_flow.py nicolify/backend/tests/integration/`
   - Update test_folder_naming KNOWN_STRUCTURE_EXCEPTIONS
   - Update ADR-003 § Tabla resumen acciones
   - Update this proposal state → migrated

### Post-lift

- `cd nicolify/backend && pytest tests/architecture/ -x` GREEN baseline
- Final `src/` tree: `main.py` + `modules/nicolify/{admin, advertising, edges, persistence, workers}/`
- Zero duplication vs core verificado por shared layer cleanup
- Brands futuras heredan layout pattern via `_pm-brand-template/`

## 5. Decisión

**Recomendación `/pm-luana`:** APPROVED

**Razón:** completion natural del carve-out audit ADR-003 § Fase 4 (lifts/drops pending). Layout-only, zero risk runtime. Desbloquea trabajo vitalia (next brand prioritaria).

**Ratificación Chris:** APPROVED upfront 2026-05-16 ("cierre completo nicolify antes de vitalia").

## 6. Bitácora

- 2026-05-16: opened by /pm-luana
- 2026-05-16: state proposed → accepted (Chris APPROVED autonomous, layout-only)
- 2026-05-16: lift executed via 4 incremental commits:
  * Commit A (`d3113fa`): edges + workers → modules/nicolify/{edges,workers}/ (5 files moved, 4 importers updated)
  * Commit B (`d296fc7`): admin → modules/nicolify/admin/ (51 files moved, 65+ refs sed-replaced cross-codebase)
  * Commit C (`a26b97d`): model_registry → modules/nicolify/persistence/ (1 file moved, 12 importers updated) + src/shared/ purged + 9 arch tests stale refs cleaned
  * Commit D (this): src/scripts/ archived to nicolify/docs/archive/2026/migrate-scripts/ + src/tests/test_telegram_flow.py relocated → tests/integration/ + ADR-003 § Tabla resumen acciones marked done
- 2026-05-16: state accepted → migrated

### Estado final verificado

```
nicolify/backend/src/
├── main.py                        # FastAPI (100% engine consumers)
└── modules/nicolify/
    ├── admin/                     # Streamlit panel
    ├── advertising/               # Brand-vertical agencias B2B
    ├── edges/                     # Edge routes
    ├── persistence/               # SQLA mapper wiring
    └── workers/                   # ARQ workers
```

- 0 paths legacy single-brand (`src/{shared,admin,edges,workers,scripts,tests}/`)
- 0 cross-brand imports (verified `grep -rn 'from nicolify' vitalia/ comunify/ lupulo/ core/` = 0 hits)
- 0 duplication con core (per ADR-003 Wave 1-4 ya cerrado)

## 7. Cross-references

- ADR-003: `docs/architecture/luana-platform/03-nicolify-carve-out-audit.md`
- Admin rule: `.claude/rules/admin-panel.md`
- Anti-duplication: `.claude/rules/anti-duplication.md`
- Related: `2026-05-16-reclassify-nicolify-advertising-not-placeholder.md` (advertising vertical mover precedente)
