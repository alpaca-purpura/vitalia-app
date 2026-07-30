# Test Design Doctrine (bases sólidas de desarrollo — qué probar según la naturaleza del ticket)


> **Slim stub (context-rot pass 2026-05-30).** Cuerpo operativo completo en `.claude/skills/dev-team/references/test-design-doctrine.md` — carga on-demand cuando el skill `/dev-team` se activa. **Origen:** sesión 2026-05-28. **Cement-date:** 2026-05-28.

## Regla cardinal

El builder NO improvisa los tests. Diseña la **batería de tests apropiada a la naturaleza del ticket** ANTES de implementar (fase `technical_design`), siguiendo TDD (RED→GREEN→REFACTOR). El `04-validators.yaml § test_construction_plan` del architect manda; esta doctrina es el fallback independiente.

**★ Verificación REAL ≠ "HTTP 200" (cement 2026-05-29):** un scenario está VERIFICADO solo cuando se ejerce la **acción real del usuario** (especialmente los writes: POST/PATCH/PUT/DELETE) y se **observan los logs + el efecto en DB**. Un `GET 200` sobre un placeholder NO es verificación. Declarar "funciona" porque un GET dio 200 = anti-patrón estrella prohibido.

**★ Cobertura = colaborador real, no mock (seam testing · cement 2026-06-23 · HB-94):** un test que **mockea el colaborador del otro lado de la costura (seam) bajo prueba NO cuenta como cobertura de esa costura**. Cubierto = *ejercido contra el colaborador real*, no *existe un test verde* (coverage + mutación son ortogonales: no detectan si la costura se toca). Por costura: código↔DB → integration real-DB · FE↔BE → contract · service↔router → router end-to-end · código↔auth → live-verify (#37, no unit-testeable) · componente↔shell → render en el contenedor real. `/architect` lo declara por escenario (`04-validators § test_construction_plan.seam_coverage`); Phase D marca **MOCK-ONLY (= MISSING)** la cobertura mock-only de un escenario de costura.

## Cuándo carga el detalle

- `builder-*` arranca la fase `technical_design` → leer la **Matriz: naturaleza del ticket → tests requeridos** completa (13 naturalezas cubiertas: BE endpoint, service, repo, migration, FE component, hook, form, route nueva, flujo crítico, agentic tool, prompt slot, bug fix, refactor).
- `gate-runner` necesita el **Toolchain de calidad** del proyecto (lint/format · typecheck · test/coverage · dup · arch-fitness · docstring · dead-code · deps-audit).
- `/auditor` verifica cobertura por naturaleza → leer la matriz + enforcement layers completos.

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ **Declarar "verificado" porque un GET dio 200, sin ejercer la acción real ni leer logs**
- ❌ **Test que mockea el colaborador del otro lado de la costura bajo prueba, presentado como cobertura de esa costura** (HB-94 — cubierto = colaborador real)
- ❌ Cerrar con jscpd o arch-fitness en rojo (duplicación / boundary roto = NO verde)
- ❌ Bug fix sin regression test que reproduzca el bug primero (RED)

## Referencias

- `.claude/skills/dev-team/references/test-design-doctrine.md` — **cuerpo operativo completo** (matriz 13 naturalezas, toolchain, verificación REAL, enforcement layers)
- `.claude/rules/tdd-mandatory.md` — orden RED→GREEN→REFACTOR
- `.claude/rules/architectural-fitness.md` — arch gates
- `.claude/rules/backend-quality.md` · `.claude/rules/frontend-quality.md` — gates por surface
- `.claude/rules/hotfix-repro-mandatory.md` — repro test primero
- `docs/specs/templates/04-validators-template.yaml` — test_construction_plan
