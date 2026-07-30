# Test Design Doctrine — operational detail (loaded on-demand, moved from .claude/rules/ 2026-05-30)

<!-- voseo-allowed: doc interno de doctrina de maquinaria agéntica (no user-facing) -->

**Origen:** sesión 2026-05-28 — Chris pidió que el dev tenga, además de TDD, una **base sólida propia** para diseñar QUÉ probar y CÓMO según la naturaleza del ticket (unitarios, comportamiento/E2E, y todas las pruebas que correspondan), de forma inteligente pero no improvisada. Refuerzo: seguimos usando el stack de calidad de nicolify (ruff, vitest, eslint, mypy, jscpd, etc.) — esta doctrina lo trata como base obligatoria de autoverificación.

**Cement-date:** 2026-05-28. **Aplica a:** `builder-{backend,frontend,agentic}` (diseñan tests), `/architect` (declara el plan en `04-validators.yaml`), `/auditor` (verifica cobertura). **Complementa:** `tdd-mandatory.md` (orden RED→GREEN) + `architectural-fitness.md` + `backend-quality.md` + `frontend-quality.md`.

## Regla cardinal

El builder NO improvisa los tests. Diseña la **batería de tests apropiada a la naturaleza del ticket** (matriz abajo) ANTES de implementar (fase `technical_design`), siguiendo TDD (RED→GREEN→REFACTOR, primera entrada del bitácora = RED). El `04-validators.yaml § test_construction_plan` del architect manda; esta doctrina es el **fallback independiente** cuando el plan es delgado o falta un tipo de test que la naturaleza exige.

## ★ Verificación REAL ≠ "HTTP 200" (cardinal · cement 2026-05-29)

> **Origen:** sesión 2026-05-29 (`vitalia-stub-caps-scenario-backfill` + hotfix lisa-marca). Claude declaró `/lisa/marca/personality` "verificado" porque un `GET` devolvía **200** — pero el 200 era un **placeholder vacío** (la tabla `personality_profiles` no existía) y la acción real del usuario (**cambiar arquetipo → guardar**) fallaba con `PUT → 405` ("Error al guardar"). Un status 200 de un GET NO prueba que la funcionalidad funcione. Chris: *"probar los escenarios es realmente probarlos viendo logs y todo, no solo diciendo está bien porque saco estado 200"*.

**Regla:** un scenario está VERIFICADO solo cuando se **ejerce la acción real del usuario** y se **observa el efecto + los logs**, no cuando un endpoint devuelve 200. Bar mínimo por naturaleza:

| Naturaleza | "Verificado" significa (mínimo honesto) |
|---|---|
| **UI / flujo usuario** | Ejecutar la acción real (crear/editar/**guardar**/eliminar/navegar) en la app corriendo (o E2E que la reproduce) → **resultado esperado visible** (toast OK, fila aparece, valor persistido al recargar) + **logs del backend sin 4xx/5xx inesperado** + (si escribe) **efecto en DB confirmado**. Un `GET 200` o un render de placeholder NO basta. |
| **BE endpoint** | Ejercer el método/payload reales (incluido el **write**: POST/PATCH/PUT/DELETE), no solo el GET. Confirmar status correcto + **leer logs** (sin traceback) + assert del efecto (row escrita/borrada, evento emitido). Verificar el método HTTP correcto (un 405 en logs = contrato FE↔BE roto). |
| **Migración / schema** | Aplicar contra DB real + **confirmar que la tabla/columna existe** + que el endpoint que la usa responde OK ejercido de verdad (no asumir). |
| **Agentic** | Correr el turno/tool real + leer trazas (`copilot_trace_event`) + eval goldens. No "el endpoint respondió". |

**Cómo (checklist de verificación honesta):**
1. **Ejercer**, no asumir: disparar la acción real del usuario / el método real del endpoint (especialmente los **writes** — son los que rompen, no los reads).
2. **Leer logs** del backend durante/después (`docker logs <container> --tail N | grep -iE '4|5..|traceback|error|does not exist'`). Un 200 con un 405/500 al lado en otra ruta del mismo flujo = NO verificado.
3. **Confirmar el efecto** (DB row, archivo, evento, valor persistido al recargar) — no solo el código HTTP.
4. **Round-trip** cuando aplique: escribir → releer → el valor cambió.
5. Si no podés ejercerlo de verdad (ej. auth real) → **decilo explícito** ("verifiqué routing, falta el save autenticado"), NO lo declares verificado.

**Anti-patrón estrella (prohibido):** declarar una funcionalidad "verificada"/"verified-live"/"funciona" porque un `GET` dio 200, sin ejercer la acción real ni leer logs. El 200 de un read es necesario pero **nunca suficiente**.

## ★ Cobertura = colaborador real, no mock (seam testing · cardinal · cement 2026-06-23 · HB-94)

> **Origen:** `vitalia-fase2-mateo-nueva-cita` — 9 bugs de integración pasaron **2900+ unit tests verdes** porque cada test mockeaba el colaborador del otro lado de la costura. Extiende § "HTTP 200": aquélla dice "ejercé la acción real"; ésta dice **qué hace verde a un test mentiroso** y cómo el gate lo caza ANTES del live-verify. SSoT: `docs/learnings/2026-06-23-coverage-means-real-collaborator-seam-testing.md`.

**Regla:** un test que **mockea el colaborador del otro lado de la costura (seam) bajo prueba NO cuenta como cobertura de esa costura**. "Cubierto" = *ejercido contra el colaborador real*, no *existe un test verde*. Coverage alto + mutación NO lo cazan (son ortogonales: miden el rigor de asserts sobre lógica *ejercida*, no si la costura se toca).

**Tabla costura → test que SÍ la cubre (vs mock que miente):**

| Costura | Test que SÍ la cubre | Mock que NO la cubre |
|---|---|---|
| **código ↔ DB** | integration real-DB: INSERT/query real contra Postgres (sin mock de sesión/repo) | mock de sesión/repo "acepta cualquier columna" → oculta columna inexistente / FK no resoluble / NOT NULL faltante |
| **FE ↔ BE** | contract test: payload/tipos FE = DTO BE (schemathesis BE + assert de shape compartido) | cada isla verde contra un contrato imaginado (`offer_id` vs `service_label`) |
| **service ↔ router/response** | integration a nivel ROUTER (TestClient end-to-end) que construye el response DTO | test solo-service que nunca serializa el response (null en campo `str`) |
| **código ↔ Clerk/auth** | **live-verify obligatoria (#37)** — NO unit-testeable con mock | `useAuth` mockeado "siempre cargado" + token estático → timing/expiry real irreproducible |
| **componente ↔ padre/shell** | render DENTRO del contenedor real (`<form>`/shell) + axe + `assertShellMounted` | componente aislado que nunca vive dentro del `<form>`/shell real |

**Cómo se aplica (sin fase nueva — endurece "cubierto" donde ya existe):**
- `/architect` declara por escenario la **costura** + el **tipo de test real-collaborator** en `04-validators § test_construction_plan.seam_coverage`; prohíbe `unit-mocked` para escenario de costura (HB-95).
- El builder construye el test del **tipo requerido** (`integration-realdb` / `contract` / `router` / `e2e-live` / `live-verify`), no un unit mockeado.
- Phase D (dev-team local Step 4.5 + auditor) marca **MOCK-ONLY (= MISSING)** un escenario de costura cubierto solo por test mockeado (HB-96 · `scripts/check_seam_coverage.py`).

## Verificación por naturaleza + gate anti-burbuja + modificación (Critical Rule #37)

**Naturaleza de la capability define la batería:**
- **técnica** (sin UI): gates automáticos — tsc/mypy strict → ruff/eslint --max-warnings 0 → arch-fitness → unit/integration. Opt-in por naturaleza: Schemathesis (endpoint nuevo), Hypothesis (domain logic). ★ **mutation gate diff-scoped** (`scripts/mutation_gate.py` · mutmut/Stryker · proceso v5 §5.6) en superficies mutation-críticas que `/architect` marca (commit/persistencia · dinero · PHI · state-machines · transforms-contrato): survivor en líneas-nuevas = CHANGES_REQUESTED (mata "tests verdes mockeados"); survivor heredado → CIL L4; degrada advisory si el tool no está. "Tests verdes" ≠ done: coverage es el piso, no el objetivo — ¿un test fallaría si revierto el comportamiento principal?
- **funcional** (user-reachable): cada **regla de negocio** del spec → scenario Gherkin `@rule-ID` (happy + ≥1 negative/edge) + **gate anti-burbuja** + demo manual.

**★ Gate anti-burbuja (runtime-error gate):** el `GET 200` mide SOLO el servidor; la burbuja de Next vive en el cliente post-hidratación. Los specs FE usan `{brand}/frontend/e2e/fixtures/base.ts` (pageerror + console.error + hidratación + `/api/` 4xx-5xx + diálogo de error Next, asertados vacíos al teardown) + `scripts/verify-no-backend-errors.sh` (grep `docker logs` backend). Importar de `base.ts`, NO de `@playwright/test`.

**Modificación (no rehacer):** `regression_guard` (tests viejos verdes sin tocarse) + `coverage_update` (revisando el diff del snapshot — nunca `vitest -u` mecánico = "documentación mentirosa") + `new_coverage` (TDD RED primero). Bug fix → test que reproduce el bug PRIMERO. Blast radius por dependencias (TIA); `make ci-parity` = gate final.

Ref: `.claude/rules/definition-of-done-live-verify.md` §1-§6.

## Matriz: naturaleza del ticket → tests requeridos

| Naturaleza del ticket | Tests obligatorios (RED primero, por capa) |
|---|---|
| **BE endpoint** (API) | unit (domain/service) + **integration API** (happy + **cross-tenant 403** + validación 422) + migration idempotency (si toca schema) + `response_model` PII check |
| **BE service / use-case** | unit por capa: domain (lógica pura) → infra (repo con tenant_id) → application (orquestación). RED por capa antes de implementarla |
| **BE repository** | integration con DB de test: get_by_id filtra tenant_id · soft-delete respetado · no cross-tenant leak |
| **BE migration** | idempotencia (re-run = no-op) · upgrade/downgrade · `IF NOT EXISTS`/`IF EXISTS` |
| **FE component** | Vitest component: render + props + estados (default/empty/loading/error/success) + interacción (click/submit) |
| **FE hook (data)** | Vitest: success + error + loading · React Query keys/invalidation correctas |
| **FE form** | RHF + Zod: validación happy + cada regla de error + submit · estados disabled/pending |
| **FE route/page nueva** | **E2E Playwright smoke** (la ruta carga + elemento clave visible) + visual fidelity scoped (`frontend-visual-fidelity.md`) |
| **Flujo crítico FE modificado** | E2E regression del flujo (no solo smoke) |
| **Agentic tool** | unit del tool (input/output schema + tenant_id) + graph integration (RED) + **≥3 eval goldens** + voice fidelity grader (si toca voz) |
| **Agentic prompt slot / persona** | eval goldens del comportamiento + no-hallucination + no-overpromise + voice fidelity |
| **Bug fix / hot-fix** | **regression test PRIMERO** (RED reproduce el bug) → fix → GREEN. Sin repro test, no hay fix (ver `hotfix-repro-mandatory.md`) |
| **Refactor (sin cambio de comportamiento)** | los tests existentes pasan ANTES y DESPUÉS (no se escriben tests nuevos; si hacen falta, no era refactor) |
| **Config / docs / tooling puro** | TDD NO aplica (ver `tdd-mandatory.md`); igual corre lint/format |

> Regla de inteligencia: si la naturaleza del ticket exige un tipo de test que el `04-validators.yaml` NO incluye → el builder lo agrega y lo nota en `T-{n}-impl-log.md § Test design`. Si el architect lo declaró de más (test irrelevante a la naturaleza) → el builder lo cuestiona, no lo cumple ciegamente.

## Bases de calidad de test (cómo, no solo qué)

- **Comportamiento, no implementación** — testear la conducta observable (entrada→salida, efecto), no detalles internos que romperían en cada refactor.
- **AAA** (Arrange-Act-Assert) · un concepto por test · nombre que describe el comportamiento (`test_create_rejects_cross_tenant`).
- **Determinista** — sin dependencias de orden, reloj real (usar `utc_now()` mockeable), red real, ni estado compartido entre tests. Fixtures tenant-scoped.
- **Sin interdependencia** — cada test corre aislado (un test no prepara estado para otro).
- **Negativos + bordes** — no solo happy path: cross-tenant, input inválido, empty, límites, concurrencia donde aplique.

## Toolchain de calidad = base obligatoria de autoverificación

El builder corre (vía gate-runner) y deja verde ANTES de cerrar — esto es la "base sólida" heredada de nicolify, ahora innegociable:

| Gate | Qué protege | Nota Chris |
|---|---|---|
| **ruff** (70+) + `ruff format` | lint + estilo BE | — |
| **mypy --strict** | tipos BE | — |
| **tsc --noEmit** strict + **eslint** (60+) | tipos + lint FE | — |
| **pytest** + **vitest** + cobertura (BE ≥43% / FE ≥20%) | comportamiento + no bajar cobertura | — |
| **jscpd** | **detección de duplicación** | ★ clave para "cero duplicación" — bloquea copy-paste |
| **arch-fitness** (ratchet shrink-only) | DDD/FSD boundaries, tenant isolation, no cross-brand mirror | ★ estructura senior |
| **interrogate** | docstring coverage BE | — |
| **knip** + **madge** | dead code + ciclos de deps FE | — |
| **pip-audit** / **npm audit** | vulnerabilidades deps | — |

jscpd + arch-fitness son **first-class**: un fix que pasa tests pero duplica código (jscpd) o rompe boundaries (arch-fitness) NO está verde.

## Anti-patterns prohibidos

- ❌ **Declarar "verificado"/"funciona" porque un GET dio 200, sin ejercer la acción real (write/save) ni leer logs** (ver § Verificación REAL ≠ "HTTP 200")
- ❌ Implementar sin diseñar la batería de tests (improvisar al final)
- ❌ Solo happy path (sin cross-tenant / negativos / bordes)
- ❌ Testear implementación interna (test frágil que rompe en cada refactor)
- ❌ Saltar el tipo de test que la naturaleza exige porque "el validators no lo pidió"
- ❌ Cerrar con jscpd o arch-fitness en rojo (duplicación / boundary roto = NO verde)
- ❌ Bug fix sin regression test que reproduzca el bug primero (RED)
- ❌ Tests con orden/estado compartido (no deterministas)

## Enforcement layers

| Layer | Mecanismo | Status |
|---|---|---|
| 1 | `/architect` `04-validators § test_construction_plan` deriva de esta matriz | ✅ schema existe |
| 2 | `builder-*` fase `technical_design` diseña la batería según matriz (antes de codear) | ⏳ builder update (Fase 3) |
| 3 | gate-runner corre el toolchain completo (jscpd + arch-fitness incluidos) | ✅ existe |
| 4 | `/auditor` verifica cobertura por naturaleza + jscpd/arch-fitness verde | ✅ parcial |

## Referencias

- `.claude/rules/tdd-mandatory.md` — orden RED→GREEN→REFACTOR
- `.claude/rules/architectural-fitness.md` — arch gates
- `.claude/rules/backend-quality.md` · `.claude/rules/frontend-quality.md` — gates por surface
- `.claude/rules/hotfix-repro-mandatory.md` — repro test primero
- `.claude/rules/frontend-visual-fidelity.md` — visual como parte del test FE
- `docs/specs/templates/04-validators-template.yaml` — test_construction_plan
