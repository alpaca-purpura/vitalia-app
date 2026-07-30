# HARNESS PASS — Seam-testing enforcement (KICKOFF para sesión nueva)

> **Para:** una sesión `/pm-luana` dedicada a mejorar el harness (NO mid-feature).
> **Origen:** `vitalia-fase2-mateo-nueva-cita` (2026-06-23). 9 bugs de integración pasaron **2900+ unit tests verdes** porque cada test mockeaba la costura bajo prueba. Este archivo es self-contained: tiene todo lo aprendido + el plan exacto. Doctrina detallada (provenance): `docs/learnings/2026-06-23-coverage-means-real-collaborator-seam-testing.md` (commit `ce874716` en `wip/vitalia`).
> **Lee también, por path absoluto** (están en el worktree vitalia, no en main): `~/Proyectos/luana-vitalia/docs/learnings/2026-06-23-coverage-means-real-collaborator-seam-testing.md` + `~/Proyectos/luana-vitalia/vitalia/docs/product/stories/vitalia-fase2-mateo-nueva-cita/checkpoint.md` (§ `live_verify_findings` = el ledger de los 9 bugs) + su `chris-input.md`.

## 0. Principio cardinal (lo que hay que volver enforce-able)

> **"Cubierto" debe significar *ejercido contra el colaborador real*, no *existe un test verde*. Un test que mockea el colaborador del otro lado de la costura (seam) bajo prueba NO cuenta como cobertura de esa costura.**

Extiende `verificación REAL ≠ HTTP 200` (`test-design-doctrine.md`) + `definition-of-done-live-verify.md` (#37). Aquéllas dicen "ejercé la acción real"; ésta dice **qué hace verde a un test mentiroso** y cómo el gate lo detecta ANTES del live-verify.

## 1. Evidencia (los 9 bugs, generalizados a costuras)

| # | Bug (mateo) | Costura | Por qué el test verde mintió |
|---|---|---|---|
| 1 | token effect sin `isLoaded` → form en skeleton eterno | código ↔ Clerk | `useAuth` mockeado "siempre cargado" |
| 2 | JWT 60s cacheado → todo write 307→sign-out | código ↔ Clerk | token estático en el mock |
| 3 | patient repo `channel_first`/`notes` columnas inexistentes → 500 | código ↔ DB | sesión/repo mockeada acepta cualquier columna |
| 4 | `<form>` anidado (hydration) → submit tragado | componente ↔ shell/padre | componente testeado aislado, nunca dentro del `<form>` real |
| 5 | inline create no POSTeaba (era artefacto MCP-click, ver §6) | — | — |
| 6 | appt INSERT `notes_internal` columna inexistente → 500 | código ↔ DB | mock DB |
| 6b | appt INSERT sin `clinic_id`+`offer_id` (NOT NULL) → 500 | código↔DB + FE↔BE | mock DB + contrato imaginado (FE mandaba `service_label`, no `offer_id`) |
| 8 | mirror clinic_map FK ORM no resoluble → flush 500 | código ↔ DB/ORM | mock DB (el FK ORM no se resuelve en mock) |
| 9 | `AppointmentDetailDTO.currency` requería `str` pero era None → 500 | service ↔ router/response | el test del service nunca construyó el response DTO del router |

Hilo común: la lógica **nunca se ejerció contra el colaborador real**. Coverage + mutación tampoco los cazan (son ortogonales: miden rigor de asserts sobre lógica *ejercida*, no si la costura se toca).

## 2. Objetivo de la pasada

Implementar **HB-94..98** (abajo, self-contained) + arreglar el tooling + reparar el runner E2E, de modo que "cubierto = colaborador real" sea **parte natural del ciclo** (no agrega fase — endurece la definición de "cubierto" donde ya existe: `test_construction_plan`, Phase D, technical_gates).

> ⚠️ Los HB-94..98 fueron appendeados a `harness-backlog.md` en `wip/vitalia` (`ce874716`), NO en main. Esta pasada corre off main → re-agregarlos / reconciliarlos ahí (el contenido está abajo, completo).

## 3. Setup (HARD)

- **Off MAIN, worktree dedicado.** NO editar main directo (PRINCIPAL = read-only).
- ⚠️ **Gap de tooling (parte del trabajo):** `scripts/git/new-session.sh` NO soporta un type `protocol` (solo `vitalia|nicolify|comunify|lupulo|core`); el mensaje del scope-gate sugiere `new-session.sh protocol exp <slug>` que **no existe**. Opciones: (a) crear el worktree a mano `git worktree add -b wip/protocol-seam-testing <dir> origin/main`; (b) arreglar `new-session.sh` + el mensaje del scope-gate como primer ítem (recomendado — es harness).
- **NO tocar la story mateo** (sigue en `developing`; se cierra en OTRA sesión con el harness ya mejorado).
- **Meta-disciplina (la ironía a evitar):** cada cambio de maquinaria se VERIFICA — `make machinery-check` (validate_machinery CHECKs) + `make ci-parity`. Y para cada gate nuevo: probarlo contra un caso que ANTES pasaba falso-verde (ej. un test que mockea la DB → el gate debe marcarlo MOCK-ONLY).

## 4. Trabajo — HB-94..98 (contenido completo)

### HB-94 🔴 — Doctrina + matriz costura→test
Cementar en `.claude/rules/test-design-doctrine.md` + `.claude/rules/definition-of-done-live-verify.md`:
- El principio cardinal (§0).
- La tabla **costura → tipo-de-test-que-la-cubre-de-verdad**:

| Costura | Test que SÍ la cubre | Mock que NO la cubre |
|---|---|---|
| código ↔ DB | integration real-DB (INSERT/query real contra Postgres) | mock de sesión/repo |
| FE ↔ BE | contract test (payload/tipos FE = DTO BE; schemathesis BE + assert shape) | cada isla con contrato imaginado |
| service ↔ router/response | integration a nivel ROUTER (TestClient end-to-end) | test solo-service |
| código ↔ Clerk/auth | **live-verify obligatoria (#37)** — NO unit-testeable | `useAuth` mockeado |
| componente ↔ padre/shell | render DENTRO del contenedor real + axe + `assertShellMounted` | componente aislado |

### HB-95 🔴 — Architect declara seam + test_type por escenario
`/architect` `04-validators.yaml § test_construction_plan`: cada SC declara `seam` (`code-db|fe-be|router|auth|component-shell`) + `test_type` requerido (`integration-realdb|contract|router|e2e-live|live-verify`) + `target`. Prohibir `unit-mocked` para escenario de costura. Tocar: `docs/specs/templates/04-validators-template.yaml` + `.claude/skills/architect/` (+ references).

### HB-96 🔴 — Phase D rechaza cobertura mock-only de escenarios de costura
`/dev-team` Phase D local (Step 4.5) + `/auditor` Phase D: el gate gherkin-matrix marca `MOCK-ONLY` (= `MISSING`) un escenario de costura cubierto solo por test mockeado. Tocar: `.claude/skills/dev-team/` + `.claude/skills/auditor/` (+ `story-closure-gate` si aplica). Idealmente un check mecánico (grep: un test que importa el mock del colaborador de la costura bajo prueba ≠ cobertura).

### HB-97 🔴 — Enforce que los technical_gates declarados CORRAN
En mateo `04-validators` declaró `mutation: diff-scoped-HARD` (4 targets) + `schemathesis: enabled`; mutmut 3.5.0 instalado (sin excusa de degrade); **ningún result-file reportó score → nunca corrieron**, y el pipeline lo dio "GREEN" por conteo unit. Fix: `/dev-team` G5 DEBE correr los technical_gates declarados + el result-file DEBE incluir su salida; `/auditor` verifica (si `enabled: true` y no hay evidencia → CHANGES_REQUESTED). Tocar: `.claude/skills/dev-team/` (G5) + `.claude/skills/auditor/`.

### HB-98 🔴 — Reparar runner E2E (platform-wide)
`{brand}/frontend/e2e/clerk.setup.ts:31 setup.describe.configure(...)` → `"did not expect test.describe.configure() to be called here"` → NINGÚN smoke/regression corre (las 4 marcas). Es la infra que habilita HB-96 para la capa FE. Verificado pre-existente (git stash + inbox.smoke mismo error). Diagnosticar (Playwright 1.60 + el patrón clerk.setup) + arreglar en las 4 marcas.

## 5. Extras aprendidos (capturar como HB nuevos + arreglar en esta pasada)

- **pre-commit con marcadores de conflicto:** `scripts/git-hooks/pre-commit` tiene una modificación de +1655 líneas SIN commitear con **marcadores de conflicto git** → rompió el sweep-guard HB-31 (M15) → contaminación cross-sesión (un builder vio sus archivos barridos por otra sesión). Reparar el hook + `make install-hooks`. (Encontrado a turn 1 de la sesión origen; nunca se HB-eó formal → crear HB.)
- **Worktree tooling (§3):** `new-session.sh` sin `protocol` + mensaje del scope-gate inexacto → crear HB + arreglar.
- **MCP-click artifact (operacional, para live-verify):** el `click()` de Chrome DevTools MCP es sintético y **NO dispara el `onClick` de React** en algunos botones (los que usan `onClick` puro, ej. FreeDoctorsList, "Crear paciente", "Crear cita"). Síntoma: el click "funciona" pero no pasa nada (sin error, sin POST). **Workaround verificado:** `evaluate_script` con `el.click()` nativo SÍ dispara React. Documentar en `.claude/skills/chrome-devtools-verify/` (y/o e2e) para que futuras live-verifies no pierdan tiempo (perdí ~15 turnos creyendo que era un bug de la app, cuando era el harness de testing). Los pickers/combobox de Radix SÍ responden al MCP-click; los botones con onClick puro NO.

## 6. Lo que SÍ funcionó (no romper)

- **Live-verify (Chrome MCP, ejercer la acción real + leer logs BE + confirmar fila DB)** cazó los 9. Reafirma #37 como backstop NO-opcional.
- Los **2 bugs de Clerk (#1 timing, #2 expiry)** SOLO los caza la live-verify (no unit-testeables con mock) → la live-verify cubre la costura `código↔Clerk`, los tests no pueden.

## 7. Definición de DONE de la pasada

- HB-94..98 implementados + (HB nuevos: pre-commit, worktree-tooling) arreglados.
- `make machinery-check` verde + `make ci-parity` verde.
- Cada gate nuevo probado contra un caso que ANTES pasaba falso-verde.
- Promover a main (`make promote-to-main SHA=... && make sync-all`) — la doctrina + el enforcement llegan a las 4 marcas.
- Reconciliar la doctrina `ce874716` (está en wip/vitalia): al correr off main + agregar HB-94..98 ahí, evitar duplicar (el learning doc es archivo nuevo, no conflicta; las filas HB sí — resolver al promover).

## 8. Lo que NO es de esta pasada (sesión siguiente)

`vitalia-fase2-mateo-nueva-cita` está en `developing`, **happy-path live-verificado** (cita-create 201 + patient-create 201, filas reales — `dod_live_verified: true` ya escrito). Falta para `done`: G de Chris (re-login → 409 solape / toast / grilla refleja / demo-script) + `/auditor` sobre los 9 fixes + aplicar el **test-hardening como PILOTO de esta doctrina nueva**. Eso es otra sesión, con el harness ya mejorado.
