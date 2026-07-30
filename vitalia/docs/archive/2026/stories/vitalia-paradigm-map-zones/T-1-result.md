# T-1 Result — F1+F4 Scripts migración + cap nuevo

**Story:** vitalia-paradigm-map-zones
**Ticket:** T-1 (F1+F4)
**Surface:** BE / scripts / caps YAML
**State:** tests-passing
**Date:** 2026-05-30

## Skills Consulted

| Skill | Invocada por | Decisión tomada |
|---|---|---|
| `backend-expert` | ALWAYS gate + naturaleza script Python | Migración YAML idempotente con `--dry-run` / `--apply`; HALT-no-silent SC-3 cardinal; script Python nativo `${WS}/.venv/bin/python`. Runtime quality checklist: sin DDD nuevo, sin Alembic, sin FastAPI (scripts puros). |
| `.claude/rules/paradigm-arquitectura.md` | T-1 must_load_skills | Árbol de decisión zona/caja aplicado: Infra→false user_visible, Agentes→map_box=agent_owner, valeria.agenda/bookings→mateo, valeria.shell→plataforma-tecnica. |
| `.claude/rules/anti-orphan-integration.md` | T-1 must_load_skills | Toda cap re-tag tiene hogar en SYSTEM-MAP zones (O — On-the-map). El validador halta si unmapped (N — Notarized). actions-index = navigable without grep (N — Navigable). |
| `.claude/rules/anti-duplication.md` | T-1 must_load_skills + NO-NEW-LAYER decision | actions-index = EXTEND sobre `_code-index.json` existente (NO grep-layer nuevo). Script thin compositor. Inventario engine: cero duplicación (scripts son brand-local). |
| `docs/process/capability-protocol.md` | T-1 must_load_skills + cap nuevo schema | Schema v4 para `product-map-zonas.yaml`: change_log[0].type:new + scenarios + access + business_rules. `map_box` 5ª dimensión ADR-vitalia-005. |
| `.claude/rules/tdd-mandatory.md` | ALWAYS gate | RED → GREEN → REFACTOR. Primera entrada del bitácora = `test_unmapped_cap_halts` RED (FileNotFoundError script no existía). 9 tests escritos ANTES del script. |

## Plan (previo a código)

**TDD orden:**
1. Escribir `scripts/tests/test_map_zones_migration.py` (9 tests) → RED (FileNotFoundError: script no existe)
2. Escribir `scripts/map_zones_migration.py` → GREEN
3. Escribir `scripts/generate_actions_index.py` (thin compositor)
4. Ejecutar migración real sobre 68 caps vitalia
5. Crear `platform/product-map-zonas.yaml` (cap nuevo)
6. Generar `_actions-index.json`

**Batería de tests por naturaleza (script de migración):**
- `test_unmapped_cap_halts` (SC-3) — HALT-no-silent cardinal
- `test_rerun_is_noop` (SC-4) — idempotencia
- `test_invalid_box_rejected` (SC-5) — box inventado rechazado
- `test_config_infra_valeria_fully_retagged` (SC-1) — retag completo correcto
- `test_valeria_agenda_to_mateo` — override especial valeria.agenda → mateo
- `test_valeria_shell_to_plataforma_tecnica` — valeria.shell → Infra
- `test_user_visible_aligned_to_zone` — Infra caps → user_visible: false
- `test_dry_run_does_not_write` — dry_run no modifica archivos
- `test_already_tagged_cap_unchanged` — idempotencia cap completamente migrada

**Integración CONN:**
- `map_box` en caps → consumido por `validate_system_map.py` (gate) + cockpit MapView (tool-scope F3)
- `_actions-index.json` → consumido por cockpit + agentes (navigable sin grep)
- `product-map-zonas.yaml` → cap nuevo con `map_box: plataforma-tecnica` (hogar en Infra)

**Prior-art confirmado:**
- `generate_code_to_cap_index.py` + `_code-index.json` — EXTEND (compositor, no nuevo layer)
- `validate_system_map.py` — MODIFY (back-compat map_box-aware)
- Cero cross-brand mirror (map_box es brand-local vitalia, ADR-vitalia-005)
- Cero engine (`core/luana-core-*`) — scripts son brand-scope

## Deliverables implementados

### 1. `scripts/map_zones_migration.py` (NUEVO)

- Idempotente (`--dry-run` default, `--apply` para escribir)
- HALT-no-silent (SC-3): cap sin mapeo → exit 1 + lista explícita, NUNCA asigna default
- Lee `SYSTEM-MAP.yaml zones[].target_boxes[].absorbs` como tabla de verdad
- Builds `absorbs_table`: `config.auth → acceso`, `infra.observability → observabilidad`, etc.
- Casos especiales:
  - `valeria.agenda/bookings` → `agent_owner: mateo + map_box: mateo`
  - `valeria.shell` → `map_box: plataforma-tecnica` (Infra, user_visible: false)
  - `config.fiscal` → `configuracion` (FUNCTIONAL_AREA_NORMALIZATIONS)
  - `ops.reconciliation` → `plataforma-tecnica.reconciliation`
  - `camila.reactivacion` → `camila.reactivar` (typo correction)
  - `playwright-smoke-suite` → `plataforma-tecnica` (SLUG_OVERRIDES)
- También actualiza `agent_owner: config/infra` → target_map_box (SC-1 grader)
- Re-mapea `functional_area: config.auth` → `acceso.auth` (solo si legacy prefix)

### 2. `scripts/generate_actions_index.py` (NUEVO thin)

- Compositor sobre `_code-index.json` (EXTEND, no NEW layer)
- Compone `dev_preview.{api_endpoints,route,main_component,e2e_test}` de caps
- Produce `vitalia/docs/product/capabilities/_actions-index.json` (gitignored R3)
- Shape: `{cap_id: {map_box, route, api_endpoints, main_component, e2e_test, files}}`

### 3. `scripts/tests/test_map_zones_migration.py` (RED first)

9 contract tests cubriendo SC-1/SC-3/SC-4/SC-5 + casos valeria/user_visible.

### 4. `scripts/validate_system_map.py` (MODIFY — back-compat map_box-aware)

- Nuevo `is_valid_area()` con wildcard `{box}.*` para aceptar nuevos functional_areas post-migración
- `extract_valid_areas()` ahora incluye todas las cajas de `zones[].boxes + target_boxes[]` como prefijos válidos
- Back-compat: sigue aceptando `{agent}.{area}` del legacy format
- T-2 completará la validación positiva de `map_box` (check que map_box ∈ valid_boxes)

### 5. Re-tag 68 caps vitalia

68 caps migradas (48 config/infra/valeria + 20 especialistas que no tenían map_box):
- `agent_owner: config/infra` → reemplazado por target map_box (SC-1 grader: 0 restantes)
- `user_visible` alineado a zona (Infra → false)
- `functional_area` re-mapeado de legacy prefix a nuevo box prefix
- 3 caps con functional_area inválida normalizadas: `config.fiscal`, `ops.reconciliation`, `camila.reactivacion`
- 2ª corrida = 68 ok, 0 updated (idempotencia confirmada)

### 6. `vitalia/docs/product/capabilities/platform/product-map-zonas.yaml` (NUEVO)

- `cap_change_type: new`
- `map_box: plataforma-tecnica`
- `user_visible: false`
- Schema v4 completo con `change_log[0].type: new` + scenarios (3) + access + business_rules (3)

### 7. `vitalia/docs/product/capabilities/_actions-index.json` (GENERADO)

- 69 caps (68 pre-existentes + 1 nuevo)
- 42 con route, 33 con api_endpoints, 51 con code files
- 40 user_visible (Agentes + Plataforma), 29 Infra

## Acceptance validators — ALL GREEN

| Validator | Cmd | Result |
|---|---|---|
| SC-3 test | `pytest test_unmapped_cap_halts` | PASS |
| SC-4 test | `pytest test_rerun_is_noop` | PASS |
| SC-5 test | `pytest test_invalid_box_rejected` | PASS |
| SC-1 test | `pytest test_config_infra_valeria_fully_retagged` | PASS |
| SC-1 state | `grep agent_owner config/infra ... wc -l` | 0 |
| SC-1 grader | `reconcile_capabilities.py --brand vitalia` | exit 0 |
| SC-1 grader | `validate_system_map.py --brand vitalia` | exit 0 |
| SC-7 state | `test -f _actions-index.json` | ok |
| SC-7 grader | `generate_actions_index.py --brand vitalia` | exit 0 |
| AV-4 | `test -f platform/product-map-zonas.yaml` | ok |
| AV-2 | `pytest vitalia/backend/tests/architecture/ -q` | 330 passed |
| ruff check | scripts nuevos/modificados | All checks passed |
| ruff format | scripts nuevos/modificados | 0 files to reformat |

## Native ticket tests: 9/9 PASS

All `scripts/tests/test_map_zones_migration.py` tests GREEN.

## Cross-module reads

- Read-only `scripts/generate_code_to_cap_index.py` — consumed as SSoT for `_code-index.json`
- Read-only `scripts/reconcile_capabilities.py` — verified exit 0 (no changes needed to reconcile logic)
- Read-only `vitalia/docs/architecture/SYSTEM-MAP.yaml` — SSoT for zones.target_boxes.absorbs
- Read-only `vitalia/docs/product/stories/vitalia-paradigm-map-zones/02-impact.md` — mapeo verbatim §1-3

## Files modified/created

| File | Action |
|---|---|
| `scripts/map_zones_migration.py` | NEW |
| `scripts/generate_actions_index.py` | NEW |
| `scripts/tests/test_map_zones_migration.py` | NEW |
| `scripts/validate_system_map.py` | MODIFY (back-compat map_box-aware) |
| `vitalia/docs/product/capabilities/**/*.yaml` (68) | MODIFY (re-tag map_box) |
| `vitalia/docs/product/capabilities/platform/product-map-zonas.yaml` | NEW |
| `vitalia/docs/product/capabilities/_actions-index.json` | GENERATED (gitignored) |

## Forbidden scope check

- Cero `core/luana-core-*` tocados
- Cero `comunify/`, `nicolify/`, `lupulo/` tocados
- Cero `tools/luana-cockpit/` tocados
- Cero `vitalia/backend/src/modules/` tocados
- `git diff --name-only | grep '^(comunify|nicolify|lupulo|core/)' | wc -l` = 0

---

## Auto-fix loop iter 1 response (AUDITOR_AUTO_FIX_LOOP · 2026-05-30)

**Finding addressed:** F-1 from `T-be-review.md` — SYSTEM-MAP v2.0 regression in map_zones_migration.py

**Root cause:** T-2 restructured `SYSTEM-MAP.yaml` to v2.0 where `zones[].boxes` became a list of
objects `{id, name, absorbs, functional_areas}` (not strings) and `target_boxes[]` was eliminated
(promoted directly into `boxes`). Three functions in the migration script crashed:
- `build_valid_boxes`: `valid.update(boxes)` tried to hash dict objects → `TypeError: unhashable type: 'dict'`
- `box_to_zone`: `mapping[box] = zid` tried to use dict as key → same TypeError
- `build_absorbs_table`: only read `target_boxes[]` (now absent in v2.0) → returned `{}`

**Fix applied (Carril B — includes test fixture update):**

1. **`scripts/map_zones_migration.py`**: Updated all three functions to handle v2.0 (boxes as objects with
   `id` + `absorbs` keys) while maintaining v1.x back-compat (boxes as plain strings + legacy `target_boxes[]`).
   Each function now does `isinstance(box, dict)` / `isinstance(box, str)` branching.

2. **`scripts/tests/test_map_zones_migration.py`**: Updated `SYSTEM_MAP_MINIMAL` fixture from v1.1 schema
   (boxes as plain strings + `target_boxes[]`) to v2.0 schema (boxes as objects with `id + absorbs`,
   no `target_boxes[]`). The fixture now matches the real SYSTEM-MAP structure that the script runs against.

**Acceptance gates — ALL GREEN:**

| Gate | Result |
|---|---|
| `pytest scripts/tests/test_map_zones_migration.py -q` | 9/9 PASS |
| `python scripts/map_zones_migration.py --brand vitalia --dry-run` | 69 ok · 0 updated · 0 unmapped · no crash |
| `git diff --quiet vitalia/docs/product/capabilities/ && echo NOOP` | NOOP (SC-4 idempotency confirmed) |
| `ruff check scripts/map_zones_migration.py scripts/tests/...` | All checks passed |
| `ruff format --check` | 2 files already formatted |
| `scripts/reconcile_capabilities.py --brand vitalia` | exit 0 · all capabilities consistent |
| `scripts/validate_system_map.py --brand vitalia` | PASS · cero issues |

**Commit:** `17adec9f` — `fix(vitalia/scripts): update map_zones_migration for SYSTEM-MAP v2.0 schema`
**Files touched:** 2 (`scripts/map_zones_migration.py` · `scripts/tests/test_map_zones_migration.py`)
**Scope discipline:** cero caps modified · cero SYSTEM-MAP.yaml touched · cero frontend · cero core/
