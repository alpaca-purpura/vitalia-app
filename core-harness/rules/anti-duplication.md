# Anti-Duplication

> **tier: core (W5b harness-refactor 2026-06-09).** El cardinal grep-before-write (abajo) es always-on y **debe disparar a la hora de crear código nuevo** (no `paths:`-scoped — bug #23478). El inventario engine concreto (stack-specific) vive en `docs/rules-detail/anti-duplication.md`. La doctrina de acá es agnóstica: los paths/marcas se escriben como **`{slot}`** y se resuelven del seam `project.config.yaml` (`engine_prefix`, `sistemas`) — ver `scripts/harness_config.py`.

**Origen:** PR-1-pi1 2026-05-01. Builder agentic mirror `turn_envelope.py` cross-module → revert + lift shared.

## Regla cardinal

ANTES crear archivo `{sistema}/backend/src/modules/{sistema}/X/<subsystem>/`: grep cross-codebase (engine + todos los sistemas activos). Match → **EXTEND vía herencia DESDE engine `{engine_prefix.python_glob}/`** (resuelto de `project.config.yaml`). NUNCA mirror cross-sistema ni dentro del mismo sistema.

## Inventario engine abstractions (SSoT) — `docs/rules-detail/anti-duplication.md`

El registro canónico de las ~20 abstracciones compartidas de `{engine_prefix.python_glob}` (turn envelope, callback handler, PII sanitization, FX/pricing resolver, channel format, locale VO, LLM router, outbox, idempotency, billing/compliance guards, extraction orchestrator, …) con su path exacto + consumers vive en `docs/rules-detail/anti-duplication.md` (stack-specific · seam `engine_prefix`). **Cargalo al hacer el Step 0 grep.** Match en la tabla → CONSUMIR vía import, NUNCA mirror. **Shrink-only:** patrón nuevo cross-agent → lift a core package primer commit (vía `/pm-{platform}` promotion gate).

## Workflow pre-write

WS=`$(git rev-parse --show-toplevel)` (root del workspace `{workspace.repo_prefix}-platform/`).

1. **Step 0 GATE** (antes `Write`/`Edit` que crea file): grepeá el engine (`{engine_prefix.python_glob}`) **+ cada sistema de `{sistemas.active}`** (resueltos del seam `project.config.yaml` vía `scripts/harness_config.py`) buscando la clase/módulo que vas a crear. El **comando verbatim ejecutable** (con el `find`/`grep` exacto + el loop sobre los sistemas) vive en `docs/rules-detail/anti-duplication.md` — la mitad stack-specific.

2. Match en `core/` → **EXTEND vía import**. Match en otro sistema → ESCALATE `/pm-{platform}` (candidate lift to core).
3. NO match + categoría coincide tabla → STOP, lift a core package primero (promotion gate).
4. `/pm-{sistema}` commit decisión a CONTRACT/PR.md con paths exactos.

## Anti-patterns prohibidos

- ❌ Crear un subsistema sin el Step 0 grep cross-codebase (core + sistemas) → riesgo mirror
- ❌ Mirror de una abstracción que ya vive en `{engine_prefix.python_glob}` — heredar/consumir vía import
- ❌ Mirror cross-sistema (dos sistemas replican el mismo patrón) — lift a `core/` vía promotion gate

Ejemplos concretos stack-specific (turn_envelope, BaseAgentCallbackHandler, FXResolver, PII sanitization, format_for_channel, …): `docs/rules-detail/anti-duplication.md`.

## Enforcement + penalizaciones

PM PR.md "Existing systems audit" grep evidence · Builder Step 0 grep + escalate · Auditor Cat 12 mirror scan · Architect Opus pre-builder si toca `core/` o subsystem cross-sistema. **Penalizaciones:** builder sin Step 0 grep → REVERT · auditor sin Cat 12 → re-audit · PM skip architect → process-learnings case study.

## Multisistema awareness

Engine SSoT `{engine_prefix.python_glob}/` (`{engine_prefix.python_package_count}` pkgs) — modificar requiere el lift gate del engine (`{engine_prefix.lift_gate}`). Sistema extensions `{sistema}/backend/src/modules/{sistema}/...` heredan/registran vía Extension SDK. Cross-sistema mirror ban: dos sistemas replican mismo patrón → lift a un paquete del engine.
