<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend/Data/Docs Code Review: vitalia-paradigm-map-zones (migración mapa 3 zonas)

**Date:** 2026-05-30
**Story / pr_folder:** `vitalia/docs/product/stories/vitalia-paradigm-map-zones/`
**Brand:** vitalia
**Tickets reviewed:** T-1 (scripts re-tag + actions-index + cap nueva) · T-2 (SYSTEM-MAP v2.0 + validate map_box-aware) · T-3 (ADRs + rules/skill) · T-4 (rename backlog + map_box checkpoints)
**Commits:** a204b6ec (T-1) · d8dbcf9a (T-2) · d02dd776 (T-3) · 527e85ac (T-4)
**Files reviewed:** ~121 (scripts ×4 · 68 caps re-tag + 1 nueva · SYSTEM-MAP + 5 ADRs/contract/CLAUDE + 2 rules + 1 skill · 22 checkpoints + 5 renames + 2 releases)
**Surface:** scripts/ + vitalia/ (NO core, NO otra brand — scope clean)
**Verdict:** **CHANGES_REQUESTED**

---

## Scope check (Step 3) — PASS

| Check | Result |
|---|---|
| core/luana-core-* tocado | ❌ NONE (clean) |
| comunify/nicolify/lupulo tocado | ❌ NONE (SC-5 grader = 0) |
| modules/vitalia/{copilot,sales_agent}/ código | ❌ NONE (los matches sales_agent son cap YAML docs, no código) |
| Edits SOLO vitalia/ + scripts/ | ✅ confirmado |

Sin cross-scope flags, sin engine-edit flags, sin cross-brand pollution.

---

## Gate Status (validators re-corridos independientemente)

| Validator | Cmd | Result |
|---|---|---|
| reconcile_capabilities | `.venv/bin/python scripts/reconcile_capabilities.py --brand vitalia` | exit 0 ✓ |
| validate_system_map | `.venv/bin/python scripts/validate_system_map.py --brand vitalia` | PASS — 0 issues · 12 boxes · 69 caps · 24 stories ✓ |
| migration tests | `pytest scripts/tests/test_map_zones_migration.py -q` | 9/9 GREEN ✓ |
| ruff check (4 scripts) | — | All checks passed ✓ |
| ruff format --check (4 scripts) | — | 4 already formatted ✓ |
| connectivity map_box | (custom) caps con map_box inválido/faltante | 0 ✓ |
| actions-index re-gen | `generate_actions_index.py --brand vitalia` | exit 0 ✓ |
| **idempotency re-run** | `map_zones_migration.py --brand vitalia --apply` (2ª corrida real) | **exit 1 — TypeError ✗ (ver F-1)** |

> NOTA: gate-output.json ausente al iniciar — validators corridos directo (ya verde por el prompt; el extra fue la idempotency real contra el SYSTEM-MAP committeado).

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | N/A | scripts/docs, sin DDD layers |
| 2 | Tenant Isolation | N/A | sin queries |
| 3 | Soft Deletes | N/A | — |
| 4 | Code Quality (ruff/format) | PASS | 0 |
| 5 | SQLAlchemy 2.0 | N/A | — |
| 6 | Async Consistency | N/A | scripts síncronos |
| 7 | Pydantic v2 / PII | N/A | — |
| 8 | Migration Quality | N/A | no Alembic (migración de datos YAML, no DDL) |
| 9 | Security | N/A | sin endpoints/PII |
| 10 | Tests / TDD | **CHANGES_REQUESTED** | 1 (F-1 — fixture stale enmascara bug) |
| 11 | Cross-cutting (spanish/cap-coherence/native) | PASS | 0 |
| 12 | Mirror / Anti-duplication | PASS | 0 (vitalia-only, actions-index EXTEND de _code-index) |
| 13 | Connectivity (anti-isla) | PASS | 0 (68 caps con hogar zona→caja válido; cero huérfanos) |

---

## Findings

### CHANGES_REQUESTED · F-1 — `map_zones_migration.py` crashea en re-run contra el SYSTEM-MAP v2.0 real (SC-4 idempotencia no satisfecho de verdad)

**Category:** 10 (Tests/correctness · downstream-regression cross-ticket)
**Files:**
- `scripts/map_zones_migration.py:106` (`build_valid_boxes`), `:117` (`box_to_zone`), `:95` (`build_absorbs_table`)
- `scripts/tests/test_map_zones_migration.py:48-128` (`SYSTEM_MAP_MINIMAL` fixture)

**Issue:**
T-2 reestructuró `SYSTEM-MAP.yaml` a v2.0: promovió las cajas de `zones[].target_boxes[]` (objetos con `id`) a `zones[].boxes[]` como **objetos dict** (con `functional_areas[]`) y **vació `target_boxes`**. Pero el script de migración de T-1 sigue asumiendo el shape pre-T-2 (boxes = lista de **strings**, cajas en `target_boxes`). Contra el SYSTEM-MAP committeado:

```
$ .venv/bin/python scripts/map_zones_migration.py --brand vitalia --apply
  File ".../scripts/map_zones_migration.py", line 106, in build_valid_boxes
    valid.update(boxes)
TypeError: unhashable type: 'dict'      ← exit 1
```

Tres funciones rotas: `build_valid_boxes` y `box_to_zone` crashean (dict no hashable); `build_absorbs_table` devuelve `{}` silenciosamente (target_boxes ya no existe).

El grader de SC-4 (`git diff --quiet vitalia/docs/product/capabilities/ && echo clean`) da "clean" **por accidente**: el crash ocurre ANTES de cualquier escritura, así que el árbol queda intacto — pero el script ya NO es re-ejecutable, que es exactamente lo que SC-4 / AC#... / `business_rules.idempotent-migration` exigen.

Por qué el test no lo detecta: `SYSTEM_MAP_MINIMAL` (test fixture, líneas 48-128) declara `version: "1.1"`, `boxes` como **strings** y conserva el bloque `target_boxes` — es el shape **pre-T-2**. Los 9 tests pasan contra un fixture obsoleto que ya no coincide con el SYSTEM-MAP v2.0 que el propio story produjo. El `business_rules.idempotent-migration` del cap nuevo (`product-map-zonas.yaml:139-147`) cita `test_rerun_is_noop` como enforcement — pero ese test prueba el shape viejo.

Impacto real: la migración YA corrió bien (las 68 caps están correctamente tagueadas, tree limpio, validators verdes). Es un **bug latente**: el invariante declarado (re-run = no-op) está roto contra el estado real. Si alguien corre la migración de nuevo (o un futuro re-tag), explota.

**Fix (Carril B — requiere builder-backend, NO self-fix):**
1. Actualizar `build_valid_boxes`, `box_to_zone`, `build_absorbs_table` para leer el shape v2.0 (boxes como objetos `{id, functional_areas[]}`; derivar absorbs de `functional_areas[]` ya que `target_boxes` desapareció) — manteniendo back-compat con el shape v1.x si se desea.
2. **Actualizar el fixture `SYSTEM_MAP_MINIMAL`** al shape v2.0 (boxes objetos, sin target_boxes, version 2.0) para que los 9 tests ejerciten el contrato real. RED→GREEN: el fixture v2.0 debe hacer fallar el script actual (reproduce el crash) ANTES del fix.
3. Re-correr `map_zones_migration.py --brand vitalia --apply` → debe ser exit 0 + `git diff --quiet` clean (no-op real).

> Esto cae en **Carril B** (no Carril A): el fix correcto requiere **modificar/actualizar el test fixture** — el auditor NUNCA escribe ni modifica tests (`auditor-self-fix-policy.md`). Handoff a builder-backend mode AUDITOR_AUTO_FIX_LOOP.

**Skill ref:** `.claude/rules/auditor-downstream-regression.md` (T-2 cambió un artefacto consumido por T-1 sin reconciliar el consumer) · `.claude/rules/tdd-mandatory.md` (fixture debe ejercer el contrato real) · 01-spec SC-4 + 06-tickets covers_scenarios:[SC-4].

---

## Connectivity / anti-isla (★ paradigma) — PASS

- 68 caps re-taggeadas: **cero** con `map_box`/`functional_area` huérfano (validate_system_map PASS + custom check = 0 inválidos/faltantes).
- Cada cap tiene hogar zona→caja válido ∈ {12 cajas} del SYSTEM-MAP v2.0.
- Cap nueva `platform.product-map-zonas` → `map_box: plataforma-tecnica` (hogar en Infra), schema v4 completo, consumida por validate + cockpit (F3 tool-scope) + actions-index.
- 3 caps con functional_area inválida pre-existente (camila.reactivacion → camila.reactivar · config.fiscal → configuracion.fiscal · ops.reconciliation → plataforma-tecnica.reconciliation) normalizadas correctamente.
- Valeria fuera de `zones[agentes].boxes` (SC-2 ✓); agenda/bookings → mateo (SC-2 grep = 0).

## Cross-cutting (Cat 11) — PASS

- spanish-text: 01-spec.md + 02-impact.md llevan `<!-- voseo-allowed -->` magic comment (docs internos citando glosario). ✓
- cap_change_type coherence: `cap_change_type: new` ↔ `product-map-zonas.yaml` creado con `change_log[0].type: new` + scenarios(3) + access + business_rules(3). ✓
- Native-first: validators corridos con `.venv/bin/python` (no docker exec). ✓
- R1 (no MDs sueltos en vitalia/docs/ raíz): 0 archivos nuevos sueltos. ✓
- R3 (auto-gen gitignored): `_actions-index.json` gitignored ✓ + no committeado ✓.
- R2 (archive done): N/A — las 5 stories renombradas están en `state: idea`, no `done`; rename via `git mv` preservando dir completo (chris-input.md incluido). ✓
- Idempotencia actions-index + reconcile + validate: re-run limpio ✓.

## Anti-duplication (Cat 12) — PASS

- Migración vitalia-only; `map_box` es brand-local (ADR-vitalia-005). Cero cross-brand mirror.
- `generate_actions_index.py` = EXTEND/compositor sobre `_code-index.json` existente (no nuevo grep-layer). ✓

---

## Verdict Math

- Categorías 1/2/8/9/12 → todas PASS/N/A → no AUTO-FAIL por esas.
- Allowlists: sin cambios (arch fitness no tocado por scripts/docs).
- Gates 3/4/11/12/13: PASS (los aplicables; ruff/format verde).
- **F-1 (Cat 10)**: bug de correctness latente que viola un AC declarado (SC-4) + business_rule + grader, enmascarado por fixture stale → **CHANGES_REQUESTED** (Carril B, requiere builder para actualizar fixture + funciones).

**Overall: CHANGES_REQUESTED** — la migración funcionó y el estado committeado es correcto (caps tagueadas, validators verdes, cero huérfanos, cero cross-brand), pero `map_zones_migration.py` ya no es re-ejecutable contra el SYSTEM-MAP v2.0 que la propia story produjo, y el test no lo detecta. Fix quirúrgico (3 funciones + 1 fixture) antes de cerrar.

## Self-fix log
- (vacío) — F-1 es Carril B (requiere modificar test fixture → builder-backend). El auditor no escribe/modifica tests.

## Handoff
→ `builder-backend` (mode AUDITOR_AUTO_FIX_LOOP, T-1 scope): aplicar fix F-1 (RED con fixture v2.0 → GREEN funciones map_box-aware) → re-correr `map_zones_migration.py --apply` no-op + 9 tests + validators verdes → re-audit.
