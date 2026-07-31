# Auditor Downstream Regression Scope

> **Slim stub (context-rot pass 2026-05-30 · materializada single-brand 2026-07-31).** Detalle operativo completo (workflow pseudocode 8 pasos verbatim, tabla SSoT secciones A-I, ejemplos CORRECTO/INCORRECTO, pre-commit freshness gate, enforcement layers, penalizaciones) en `docs/rules-detail/auditor-downstream-regression.md` + `docs/rules-detail/auditor-downstream-targets.md` — load on-demand. **Origen:** PI-12 S1 Story A T-1 (2026-05-04). Severidad: CRÍTICA.

## Regla cardinal

Cuando auditor reviewing PR toca `core/luana-core-*/` (engine), extensión de vitalia `vitalia/backend/src/modules/vitalia/...`, o módulo con consumers conocidos, MUST ejecutar los checks en orden:

1. **Engine edit detection** — si toca `core/luana-core-*/src/`, verificar que el cambio pasó por el flujo engine de `/pm-vitalia` (cambio directo en `core/` con los arch tests como gate) y que los arch tests del paquete están GREEN. Cambio de engine "de contrabando" dentro de un ticket de marca sin declararlo → FAIL.
2. **Mirror scan** — detectar duplicación: código nuevo en vitalia que replica una abstracción del engine (mismo `basename`/clase bajo `core/luana-core-*/src`), o el mismo patrón repetido en dos módulos de vitalia. Match diff >50% → FAIL automático.
3. **Downstream test run** — ejecutar tests de consumers per tabla SSoT (`auditor-downstream-targets.md`): engine tocado → suite del paquete + suite vitalia consumer.

## Cuándo carga el detalle

- Lookup de `downstream_test_targets` por surface tocada (tabla SSoT secciones A-I)
- Workflow completo pseudocode 8 pasos (scope=ENGINE vs VITALIA, spawn gate-runner adicional)
- Ejemplos verbatim CORRECTO (caso origen D4 observability + mirror scheduler_tool)

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ APPROVED PR `core/luana-core-*/src/` sin arch tests del paquete GREEN ni cambio declarado como engine-change
- ❌ APPROVED PR `vitalia/.../modules/vitalia/` con código que mirrorea una abstracción de `core/luana-core-*`
- ❌ APPROVED PR engine (observability/llm/platform enums) sin run downstream tests de vitalia consumer

## Referencias

- `docs/rules-detail/auditor-downstream-regression.md` — **detalle completo** (workflow, ejemplos, scopes, layers)
- `docs/rules-detail/auditor-downstream-targets.md` — **tabla SSoT secciones A-I** (load on-demand por auditor)
- `.claude/rules/anti-duplication.md` — inventario shared abstractions engine
