# Anti-Duplication

> **tier: core (W5b harness-refactor 2026-06-09 · materializada single-brand 2026-07-31).** El cardinal grep-before-write (abajo) es always-on y **debe disparar a la hora de crear código nuevo** (no `paths:`-scoped — bug #23478). El inventario engine concreto (stack-specific) vive en `docs/rules-detail/anti-duplication.md`.

**Origen:** PR-1-pi1 2026-05-01. Builder agentic mirror `turn_envelope.py` cross-module → revert + lift shared.

## Regla cardinal

ANTES crear archivo `vitalia/backend/src/modules/vitalia/X/<subsystem>/`: grep cross-codebase (engine `core/luana-core-*` + vitalia). Match → **EXTEND vía herencia DESDE engine `core/luana-core-*/`**. NUNCA mirror: ni recrear en vitalia lo que el engine ya tiene, ni duplicar el mismo patrón dentro de vitalia.

## Inventario engine abstractions (SSoT) — `docs/rules-detail/anti-duplication.md`

El registro canónico de las ~20 abstracciones compartidas de `core/luana-core-*` (turn envelope, callback handler, PII sanitization, FX/pricing resolver, channel format, locale VO, LLM router, outbox, idempotency, billing/compliance guards, extraction orchestrator, …) con su path exacto + consumers vive en `docs/rules-detail/anti-duplication.md`. **Cargalo al hacer el Step 0 grep.** Match en la tabla → CONSUMIR vía import, NUNCA mirror. **Shrink-only:** patrón nuevo cross-agent → lift a core package primer commit (vía flujo engine de `/pm-vitalia`: cambio directo en `core/` con los arch tests como gate).

## Workflow pre-write

WS=`$(git rev-parse --show-toplevel)` (root del repo `vitalia-app/`).

1. **Step 0 GATE** (antes `Write`/`Edit` que crea file): grepeá el engine (`core/luana-core-*`) **+ vitalia** buscando la clase/módulo que vas a crear. El **comando verbatim ejecutable** (con el `find`/`grep` exacto) vive en `docs/rules-detail/anti-duplication.md` — la mitad stack-specific.

2. Match en `core/` → **EXTEND vía import**. Match en otro módulo de vitalia → consolidar (no duplicar dentro de la marca).
3. NO match + categoría coincide tabla → STOP, lift a core package primero (flujo engine de `/pm-vitalia`).
4. `/pm-vitalia` commit decisión a CONTRACT/PR.md con paths exactos.

## Anti-patterns prohibidos

- ❌ Crear un subsistema sin el Step 0 grep cross-codebase (core + vitalia) → riesgo mirror
- ❌ Mirror de una abstracción que ya vive en `core/luana-core-*` — heredar/consumir vía import
- ❌ Duplicar el mismo patrón en dos módulos de vitalia — lift a `core/` (flujo engine de `/pm-vitalia`)

## Enforcement + penalizaciones

PM PR.md "Existing systems audit" grep evidence · Builder Step 0 grep + escalate · Auditor Cat 12 mirror scan · Architect pre-builder si toca `core/` o subsystem compartible. **Penalizaciones:** builder sin Step 0 grep → REVERT · auditor sin Cat 12 → re-audit · PM skip architect → process-learnings case study.

## Engine awareness

Engine SSoT `core/luana-core-*/` (27 pkgs) — modificar el engine se hace directo en `core/` con los arch tests como gate (flujo engine de `/pm-vitalia`; el promotion gate cross-brand NO aplica en este repo standalone). Vitalia extensions `vitalia/backend/src/modules/vitalia/...` heredan/registran vía Extension SDK.

Ejemplos concretos stack-specific (turn_envelope, BaseAgentCallbackHandler, FXResolver, PII sanitization, format_for_channel, …): `docs/rules-detail/anti-duplication.md`.
