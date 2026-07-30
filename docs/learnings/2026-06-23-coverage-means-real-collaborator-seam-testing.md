---
date: 2026-06-23
slug: coverage-means-real-collaborator-seam-testing
type: technical-process
brand: cross-brand
promotable: yes
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo, all]
target: harness (process enforcement — Phase D / test_construction_plan / technical_gates / definition-of-done)
applied: pending
origin: vitalia-fase2-mateo-nueva-cita (live-verify destapó 9 bugs en código "verde")
related: [[verification-real-not-200]], [[dod-live-verify]], [[user-story-no-es-ssot]], [[unit-green-not-runtime-truth]]
---

# Cobertura = colaborador real, no mock (seam testing como gate)

## Principio cardinal (durable)

> **"Cubierto" en la matriz Gherkin / test_construction_plan debe significar *ejercido contra el colaborador real*, no *existe un test verde*. Un test que mockea el colaborador del otro lado de la costura (seam) bajo prueba NO cuenta como cobertura de esa costura.**

Extiende la doctrina ya cementada `verificación REAL ≠ HTTP 200` (`test-design-doctrine.md`) y `definition-of-done-live-verify.md` (#37): aquellas dicen "ejercé la acción real"; ésta dice **qué hace verde a un test mentiroso** y cómo el gate lo detecta antes del live-verify.

## Evidencia (caso origen)

`vitalia-fase2-mateo-nueva-cita`: 9 tickets, **2900+ unit tests verdes**, mutation/schemathesis declarados. La live-verify (Chrome MCP contra el stack real) destapó **9 bugs de integración**, ninguno visto por los tests. **Todos viven en una costura, y todos los tests mockeaban el otro lado.**

## Taxonomía de costuras → tipo de test que la cubre de verdad

| Costura | Clase de bug que oculta (vistos en mateo) | Test que SÍ la cubre | Por qué el unit mockeado NO la cubre |
|---|---|---|---|
| **código ↔ DB** | columna inexistente, FK no resoluble, NOT NULL faltante, constraint | **integration real-DB**: INSERT/query real contra Postgres (sin mock de sesión/repo) | el mock acepta cualquier columna → "INSERT OK"; la DDL real grita |
| **FE ↔ BE** | contrato imaginado (campos, casing, required), `offer_id` vs `service_label` | **contract test**: payload/tipos FE = DTO BE (schemathesis BE + assert de shape compartido) | cada isla verde contra un contrato inventado; nadie cruza la costura |
| **service ↔ router/response** | DTO de respuesta (null en campo `str`, tipos) | **integration a nivel ROUTER** (TestClient end-to-end), no solo service | el test del service nunca construye el response DTO del router |
| **código ↔ Clerk/auth** | session timing (`isLoaded`), JWT expiry 60s, refresh no-eligible-non-get | **live-verify obligatoria** (#37) — NO unit-testeable con mock | `useAuth` mockeado "siempre cargado" + token estático → timing real irreproducible |
| **componente ↔ padre/shell** | `<form>` anidado/hydration, context faltante, portal/focus | **render DENTRO del contenedor real** (no aislado) + axe + `assertShellMounted` | el componente aislado nunca vive dentro del `<form>`/shell real |

Hilo común: la lógica **nunca se ejerció contra el colaborador real**. Por eso coverage alto + **mutación tampoco los cazan** — mutación mide "¿tus asserts sobre lógica *ejercida* son fuertes?", no "¿ejerciste contra el colaborador real?". Son ortogonales: mutación endurece el unit; seam-testing garantiza que la costura se toca.

## Diseño de enforcement (cómo se vuelve parte natural del proceso — NO una fase nueva)

Se **endurece la definición de "cubierto"** en los gates que YA existen. Por artefacto:

1. **`test-design-doctrine.md` + `definition-of-done-live-verify.md`** — agregar el principio cardinal + la tabla de costuras→tipo-de-test. Regla: "test que mockea la costura bajo prueba ≠ cobertura de esa costura".
2. **`/architect` · `04-validators.yaml § test_construction_plan`** — cada escenario declara la **COSTURA que cruza** + el **tipo de test real-collaborator requerido** (real-DB / contract / router / E2E-live / live-verify). No se permite "unit (mocked)" para un escenario de costura. Schema nuevo: `seam_coverage: { sc: SC-x, seam: code-db|fe-be|router|auth|component-shell, test_type: integration-realdb|contract|router|e2e-live|live-verify, target: <path> }` (clave `seam_coverage` porque `scenario_to_test` ya existe en el template con otra forma — gherkin→e2e file). Gate mecánico: `scripts/check_seam_coverage.py`.
3. **`/dev-team` Phase D local + `/auditor` Phase D (gherkin-matrix)** — el gate de cobertura verifica que cada SC mapea a un test del **tipo requerido**, no solo "existe un test". Nuevo check: marcar `MOCK-ONLY` un escenario de costura cubierto solo por test mockeado → cuenta como `MISSING`.
4. **Gate estándar nuevo: contract test FE↔BE** (HB-42 ya lo pedía) — para toda story con costura FE↔BE: schemathesis BE (ya se declara, hay que CORRERLO) + un assert de shape compartido FE↔BE. Technical_gate estándar.
5. **Enforcement de los technical_gates declarados** — `/dev-team` DEBE correr mutation + schemathesis declarados y reportar score; `/auditor` verifica que corrieron (en mateo se declararon HARD y se saltaron silenciosamente — el builder reportó solo conteo unit). Gate: si `04-validators` declara `mutation.enabled`/`schemathesis.enabled`, el result file DEBE incluir su salida.
6. **Reparar el runner E2E** (`clerk.setup.ts:31 describe.configure`, roto platform-wide) — sin él los escenarios funcionales no corren contra el stack real en CI; la live-verify queda como muestreo manual. Es la infra habilitante de #3/#4.

## Por qué es "natural" y no burocrático

No agrega una fase ni un artefacto nuevo: re-define "cubierto" en `test_construction_plan` + Phase D (que ya existen) y exige correr los gates que el architect ya declara. El costo marginal es escribir el tipo-de-test por escenario (el architect ya escribe el plan) y correr lo declarado (el dev-team ya corre gates). El verde deja de mentir.

## Anti-patterns (los 9 bugs, generalizados)

- ❌ Test de repo/service con sesión/DB mockeada presentado como cobertura de un escenario que toca la DB.
- ❌ FE y BE testeados cada uno en su isla contra un contrato imaginado (sin contract test que cruce).
- ❌ Test del service que no construye el response DTO del router (deja pasar bugs de serialización).
- ❌ `useAuth`/Clerk mockeado como "siempre cargado" presentado como cobertura del flujo auth (solo la live-verify lo cubre).
- ❌ Componente testeado aislado presentado como cobertura de su integración en el shell/form padre.
- ❌ Phase D que cuenta "existe un test" en vez de "existe un test del tipo que ejerce la costura".
- ❌ technical_gate (mutation/schemathesis) declarado HARD y salteado sin reportar (verde de conteo unit ≠ gate corrido).

## How to apply

Trigger: cualquier story con costuras (casi todas). El `/architect` declara seam+test_type por escenario; `/dev-team` los construye contra colaboradores reales + corre los gates declarados; `/auditor` Phase D rechaza cobertura mock-only de escenarios de costura. La live-verify (#37) sigue siendo el backstop para la costura auth (no unit-testeable).

## Routing CIL

- **L2 (este doc)** — doctrina/diseño durable.
- **L1 (harness-backlog HB-94..HB-99)** — los edits concretos de maquinaria (enforce en architect/dev-team/auditor/rules + contract gate + e2e runner + technical-gate-run enforcement). Implementar en pasada `/harnesses-improvement` dedicada — NO mid-feature.
