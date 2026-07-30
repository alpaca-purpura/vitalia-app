# T-1-result.md — FE-tests: de-mock + web-first + fixture forwarding shared + des-quarantine

> Builder: builder-frontend (Sonnet). Ticket T-1 (`production_code: false`, tests-only).
> Branch/worktree: `worktree-agent-a5de519245bc929a2` (isolated, branched from `main` @ `09e12ae9`).
> Phase output state: **tests-passing** (builder phase). Live suite run deferred to orchestrator (see § Verificación).

## Thesis cerrada

La suite lisa-marca era **verde falso** (mockeaba el backend-bajo-prueba con `route.fulfill` sobre
identity/visuals/personality/contact/trust-signals/voice-preview). Ahora es **honesta** (backend real vía
forwarding compartido) y **determinista** (asserts web-first, cero listeners dangling). El forwarding inline
×3 del parent se LIFTeó a una fixture compartida; los 5 `fixme` quarantined se des-quarantinearon con asserts
web-first; el gate anti-burbuja (`base.ts`) se adopta por composición (`mergeTests`).

## Archivos modificados (22 total: 20 M + 1 D + 1 new)

### NEW (1)
- `vitalia/frontend/e2e/fixtures/real-backend-forward.fixture.ts` — **LIFT** del forwarding inline. Compone
  `mergeTests(base.ts anti-burbuja, auth Clerk storageState + forwarding page.route('**/api/v1/**')→page.request.fetch(:8002))`.
  Exporta `test/expect/TENANT_ID/BACKEND_API_URL` + helper `forwardApiToRealBackend(page)`.
  ⚠️ **NO inyecta `X-User-ID: TENANT_ID`** (eso era el B6 mask): reenvía los headers reales del browser
  (`allHeaders()`) → `fetchClient` manda `X-Tenant-ID` de Clerk + el api-layer manda `X-User-ID` = Clerk userId real (T-2).

### DELETED (1)
- `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/fixtures/voice-preview-mock.ts` — obsoleto.
  voice-preview es **determinístico** (`VoicePreviewService`: "Zero LLM calls — PersonalityCompiler.compile() is
  purely deterministic") → de-mockeado (M3). 0 consumidores restantes.

### MODIFIED — fixtures (3)
- `…/vitalia-fase2-lisa-marca/fixtures/lisa-marca.fixture.ts` — **REMOVE `setupLisaMarcaMocks`** + todos los
  `buildMock*` (era el bug). `test/marcaPage/marcaContext` se componen desde la shared (auth + forwarding +
  anti-burbuja). `LISA_MARCA_FIXTURE` constants preservadas como seed esperado. Re-export `forwardApiToRealBackend` + `gotoMarca`.
- `…/vitalia-fase2-lisa-marca/fixtures/large-dataset.fixture.ts` — **REMOVE** mock canned de 50 trust-signals
  (M3: trust-signals es read real; el grep-gate ahora lo cubre). `largeDatasetPage` = página honesta forwardeada.
  `buildLargeTrustSignals/Team` quedan como data in-memory para aserciones unit del builder.
- `…/vitalia-fase2-lisa-marca/fixtures/network-failure.ts` — `route.continue()` → `route.fallback()` en reads
  (delegan al forwarding del fixture → backend real). Las fallas inyectadas (503/abort en PATCH) se **CONSERVAN**
  (error-path legítimo, no mock del happy-path; pattern variable `page.route(p,…)` no matchea el grep literal SC-2).

### MODIFIED — POMs (3)
- `…/vitalia-fase2-lisa-marca/poms/voz-tono-section.pom.ts` — `+waitForSelectedArchetype(slug,{timeout})` web-first
  (`expect(card).toHaveAttribute('data-selected','true')`). `getSelectedArchetype` once-read marcado diagnostics-only (B3).
- `…/vitalia-fase2-lisa-marca/poms/lisa-marca-page.pom.ts` — `+waitForActiveSubsubtab(slug)` web-first.
  `getActiveSubsubtab` once-read marcado diagnostics-only.
- `…/arreglar-guardado-voz-y-tono/poms/voz-tono-section.pom.ts` — `+waitForSelectedArchetype(slug,{timeout})` web-first (B3, template del fix de determinismo).

### MODIFIED — specs lisa-marca (11)
Todos importan `test/expect` de la shared `lisa-marca.fixture` (→ `base.ts` vía `mergeTests`), cero `@playwright/test` directo:
- `lisa-marca-identidad-autosave.spec.ts` — round-trips reales (PATCH→200 vía `page.on response`), `toHaveValue` web-first, `waitForActiveSubsubtab`. Test "seed loads" tolerante a DB real (`not.toHaveValue("")`).
- `lisa-marca-empty-state.spec.ts` — de-mockeado. Sin tenant vacío real, asserta lo comprobable con datos reales: placeholders/CTA sin voseo + sección renderiza (lista O empty-state). Aserciones tolerantes.
- `lisa-marca-autosave-timeout.spec.ts` — `failOnRuntimeError:false`. GET real; PATCH error-injectado vía `abortAutosaveRoute` (network-failure.ts). Restore→reintento contra backend real.
- `lisa-marca-concurrent-owners.spec.ts` — 2 owners forwardeados al backend real; guards anti-burbuja de base.ts en ambas páginas. voice-preview real (determinístico). PATCH→200 ambos.
- `lisa-marca-cross-tenant.spec.ts` — **de-mockeado el 403** (era inyectado): navega a tenant ajeno → el BE real (dual filter) enforce → FE error / no leak. `failOnRuntimeError:false`. PHI-URL + tenant-match = inspección pura.
- `lisa-marca-race-autosave.spec.ts` — 2 tabs mismo contexto forwardeadas al backend real; PATCH→200 ambas; `waitForActiveSubsubtab`.
- `lisa-marca-voice-warning.spec.ts` — warning real del BE (soft, sobre el voice-blocklist seed); save NUNCA bloqueado (PATCH→200); alerta tolerante.
- `lisa-marca-logo-upload-size.spec.ts` — validación size/type client-side; "no upload" observado con `page.on("request")` (no mock del endpoint visuals).
- `lisa-marca-large-dataset.spec.ts` — render+perf sobre datos reales; builder 50-item verificado in-memory (unit). Nota scope M3: "50 items puro" requiere seed (fuera de scope).
- `lisa-marca-keyboard.spec.ts` — import desde fixture; `waitForActiveSubsubtab` web-first; resto inspección a11y.
- `lisa-marca-i18n.spec.ts` — import desde fixture; scans de voseo/tildes (inspección).

### MODIFIED — specs parent arreglar-guardado-voz-y-tono (3)
- `voz-arquetipo-autosave.spec.ts` — import desde shared; forwarding inline ELIMINADO; **1 fixme des-quarantined** (reload-persist web-first `waitForSelectedArchetype`); listeners `page.on response` con `.catch()` + `page.off` (RN-4).
- `voz-bloque-autosave.spec.ts` — idem; **1 fixme des-quarantined** (textarea `toHaveValue` web-first).
- `voz-autosave-error.spec.ts` — `failOnRuntimeError:false`; GET real + PATCH 503 inyectado vía `route.fulfill`+`route.fallback()`; **3 fixme des-quarantined** (error/retry/interactive web-first).

**Des-quarantine total: 5 `fixme` → 0** (1 arquetipo + 1 bloque + 3 error).

## Grep-gate outputs (literales, corridos en el worktree)

```
════ SC-2 (M1 new pattern: page.route over backend-under-test) ════
PASS: 0 mocks

════ SC-3 (no direct @playwright/test import in lisa-marca specs) ════
PASS: 0 direct imports

════ SC-5 (no dangling void listeners) ════
PASS: 0 dangling

════ arch_no_new_forwarding_duplication ════
inline forwarding in regression specs: 0 (must be 0)

════ fixme count (des-quarantine) ════
arreglar-guardado fixme: 0
lisa-marca fixme: 0

════ test.skip permanente in scope ════
skip count: 0
```

## tsc + eslint (builder gates) — corridos vía deps symlinkeados del shared checkout (worktree aislado sin pnpm install propio)

```
tsc --noEmit                                   → 0 errores (worktree source + deps shared, tsc 5.9.3)
eslint <MIS 22 archivos> --max-warnings 0      → 0 errores · 0 warnings
```

⚠️ `eslint e2e/` (todo el dir, sin scope) reporta errores PRE-EXISTENTES en archivos fuera de mi scope
(`e2e/specs/vitalia/*.smoke.spec.ts` unused-vars, `e2e/fixtures/{aurora,mindful,sanare}*.fixture.ts` no-empty-pattern,
`e2e/admin/*`). **Verificado vía `git status`: ninguno de esos archivos está en mi diff** — existen en `main` y NO
los introduje. El validator `fe_lint` (`eslint e2e/ --max-warnings 0`) podría fallar por ellos; es un baseline
pre-existente para el auditor/orchestrator, ortogonal a T-1.

## M1 — FIX del grep-gate sc2 (deliverable 7) — PATCH para el orchestrator

El `04-validators.yaml` vive en `wip/vitalia` (committed @ `22f25e4d`), **no en este worktree aislado** (branched
from `main`, story folder solo tiene checkpoint.md + chris-input.md). El harness bloquea editar el shared checkout
desde esta sesión. **El orchestrator aplica este patch verbatim al integrar en `wip/vitalia`:**

`vitalia/docs/product/stories/estabilizar-harness-e2e-lisa-marca/04-validators.yaml` § `sc2_no_mock_backend_bajo_prueba`:

```diff
-    cmd: "! grep -rEn 'route\\.fulfill' vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/ | grep -E 'lisa/marca/(identity|visuals|personality)'"
+    cmd: "! grep -rEn 'page\\.route\\(.*api/v1/lisa/marca/(identity|visuals|personality|contact|trust-signals)' vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/"
```
+ actualizar `description:` a:
```
"0 ocurrencias de page.route sobre identity/visuals/personality/contact/trust-signals (mock del backend-bajo-prueba). Las fallas inyectadas 503/abort van por network-failure.ts (pattern variable) — error-path, no happy-path mock."
```

**Por qué (M1, del impl-log §11):** el pattern previo `route\.fulfill ... lisa/marca/(identity|visuals|personality)`
daba **0 vacuo** porque el mock es **multi-línea** (`page.route("…identity")` en una línea, `route.fulfill()` líneas
después) → nunca matcheaba aunque había 53 `route.fulfill`. La señal real es `page.route(…lisa/marca/<endpoint>)`.
Se amplió a `contact|trust-signals` (M3: también eran reads reales mockeados). Las fallas inyectadas usan el helper
`network-failure.ts` con pattern variable (`page.route(p, …)`) → NO matchean el literal (error-path legítimo).

Es una corrección de **correctness del gate**, no scope creep (PERMITIDO explícitamente en el prompt: `04-validators.yaml (solo el pattern sc2)`).

## Decisiones de de-mock por excepción (M3 — documentadas)

| Mock | Decisión | Razón |
|---|---|---|
| identity/visuals/personality/contact/trust-signals reads | **DE-MOCK** | backend-bajo-prueba real (RN-1) |
| voice-preview | **DE-MOCK** | determinístico (`VoicePreviewService`: zero LLM) — no hay justificación de no-determinismo |
| 503/abort en PATCH (autosave-timeout, voz-autosave-error) | **CONSERVADO** | error-path inyectado, NO mock del happy-path. Helper `network-failure.ts` con pattern variable + `route.fallback()` en reads |
| 403 cross-tenant (era inyectado) | **DE-MOCK** | el BE real (dual filter) enforce la aislación — mejor verificación honesta |
| large-dataset 50-item canned | **DE-MOCK** | trust-signals es read real (grep-gate lo cubre). Builder 50-item → aserción unit in-memory. "50 items puro" en página requiere seed (fuera de scope, M3) |

## Verificación (split builder ↔ orchestrator)

**Builder (hecho):** tsc 0 · eslint scoped 0 · grep-gates SC-2/SC-3/SC-5 + forwarding-dup + fixme=0 + cross-brand(mis archivos)=0 + skip=0.

**Live suite — DEFERIDA AL ORCHESTRATOR** (razones, no inventé verde):
1. Este worktree está **aislado y branched de `main`** (`09e12ae9`), NO de `wip/vitalia` (`4bf94366`) donde viven T-2/T-3.
   El prod fix de T-2 (`marca-voice-api.ts` → `X-User-ID: opts.userId`) **NO está en este worktree** (acá sigue `opts.tenantId`).
   Correr la suite acá fallaría SC-6/SC-7 por falta del actor real BE (#2b) + el header del FE (#2).
2. El worktree no tiene `pnpm install`/browsers propios (corrí tsc/eslint vía symlink temporal a los deps del shared
   checkout, ya removido). Playwright necesita el stack `make dev-vitalia` UP (BE :8002 + FE :3002) + storageState Clerk.

El orchestrator corre LIVE en su worktree `wip/vitalia` (con T-2/T-3 integrados + stack UP):
- SC-1: `e2e/regression/vitalia-fase2-lisa-marca/ --repeat-each=3 --workers=1` → 0 flaky · 0 failed.
- SC-4: `e2e/regression/arreglar-guardado-voz-y-tono/ --repeat-each=5` → 5 fixme deterministas.
- SC-3b runtime base.ts gate + SC-5b dangling runtime + SC-6 audit actor DB + SC-7 prohibited-phrases 200.

## Skills consulted (must_load enforcement v4.1)

| Skill / rule | Por qué | Decisión tomada (cita) |
|---|---|---|
| **playwright-expert** (vía CONTEXT-BRIEF §5.5 SSoT + canonical docs §15) | web-first assertions, mergeTests, setupClerkTestingToken, locator priority, NATIVE | Apliqué web-first ONLY (`expect(locator).toHaveAttribute/toHaveValue/toBeVisible/toHaveCount`) en lugar de once-reads (B3); `mergeTests(base, auth)` para componer anti-burbuja + forwarding; `setupClerkTestingToken({page})` por fixture; NATIVE (nunca `make e2e*`); locators por `data-testid` (POMs existentes, no CSS/XPath). |
| **frontend-expert** (`references/runtime-quality-checklist.md` mock anti-patterns + live verification) | de-mock anti-patterns, live-verify gate | De-mockeé los reads del backend-bajo-prueba; removí listeners dangling (`page.on` sin `page.off`); documenté que la live-verify la corre el orchestrator (no inventé verde). |
| **.claude/rules/e2e-testing.md** | NATIVE only, NEVER `make e2e*`, `E2E_BASE_URL=http://localhost:3002` | Comandos live documentados con `E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke`; cero `make e2e*`. |
| **.claude/rules/definition-of-done-live-verify.md** | base.ts anti-burbuja obligatorio | Adopté `base.ts` por composición (`mergeTests`) → todos los specs heredan pageerror/console/hydration/api-4xx5xx/Next-overlay. Specs que ejercen error a propósito (503/abort/403) usan `failOnRuntimeError:false`. |
| **.claude/rules/anti-duplication.md** | LIFT forwarding a fixture compartida, NO copiar inline ×11 | Forwarding vive SOLO en `real-backend-forward.fixture.ts` (`page.request.fetch` count en regression specs = 0). LIFT del template `voz-arquetipo:81-89`. |
| **.claude/rules/tdd-mandatory.md** | tests primero; des-quarantine = re-habilitar comportamiento cubierto | Des-quarantine de 5 fixme con asserts web-first sobre la race ya resuelta (14af22b2 + retry:5). |
| **.claude/rules/auditor-self-fix-policy.md** | carril/escalación | N/A para builder; T-1 es tests-only (production_code:false → Sonnet OK, no Opus). |

## Anti-burbuja / scope notes

- **B6 mask removido:** el forwarding compartido NO inyecta `X-User-ID: TENANT_ID` (era el enmascaramiento del sub-bug #1/#2). Reenvía headers reales del browser.
- **Imports type-only:** `import type { Route } from "@playwright/test"` se conserva donde se usa el tipo `Route` (voz-autosave-error). Es type-only (erased en runtime), no afecta la composición anti-burbuja; SC-3 scopea solo specs lisa-marca.
- **Falsos positivos pre-existentes (no míos):** (a) `clerk.setup.ts:4` matchea `arch_no_cross_brand_imports` por un COMENTARIO ("Adapted from nicolify…"), no un import; fuera de mi diff. (b) eslint errors en `e2e/specs/vitalia/*` + `{aurora,mindful,sanare}*.fixture.ts`, pre-existentes en `main`.
