# VERIFICATION FINDINGS — vitalia-bugfix-shell-nav-scroll-errors

> Live e2e run against the real dev stack (`localhost:3002`, real Clerk auth via storageState +
> CLERK_TESTING_TOKEN). Date: 2026-06-02. This is the DoD #37 attempt (Chrome DevTools MCP was NOT
> connected this session, so the e2e gate was the only live path available).

## Result: 6 passed / 5 failed — but the failures are NOT (mostly) my fixes

### What the live run PROVED works
- **Shell renders fully** (page snapshot shows TopBar + LogoMark + Valeria sidebar + history + ribbon
  + main content) on the presencia routes → bugs #3/#4/#5 surfaces render.
- **Bug #2 (tenant selector):** the snapshot shows `TenantSwitcher` rendering **"Clínica Sanaré" (CS
  badge + name)** — the selector IS visible with the real single tenant. Positive signal for the fix.
- tsc (0 source errors) · eslint clean · vitest **2493/2493** · arch **171/171** (all static gates green).

### Why the 5 e2e specs failed (root-caused)

| Spec | Failure | Cause | My fix? |
|---|---|---|---|
| bug3 / bug4 / bug5 | anti-burbuja gate: `console.error 404` on `/api/v1/lisa/marca/{visuals,identity,contact}` | **Pre-existing backend 404s** — the lisa/marca feature calls endpoints that return 404 for the test tenant in dev. The shell + page render fine; the strict gate flags the 404s. | ❌ NO (unrelated backend) |
| bug1 | `Rendered more hooks than during the previous render` on `mateo/agenda` | **Pre-existing render error on the agenda route.** Proof it's not mine: my added hook (`useStoreHydration(useTenantStore)`) lives in the **shared** `ShellOrganismLayoutClient` (wraps ALL routes); presencia routes render that same layout WITHOUT the hook error → my hook is hook-count-stable. The error is specific to `mateo/agenda` (the migrated agenda view), likely triggered by the e2e's failing backend. Bug #1's fix correctly redirects there; the agenda route's own error is separate. | ❌ NO (pre-existing agenda route) |
| bug7 | `ribbon` not visible; page shows `{"detail":"boom (e2e forced error)"}` | **Spec design issue:** the spec forces a 500 on an API that the agenda page fetches **server-side** → Next renders the error response directly (not the client `[agent]/error.tsx` boundary). The boundary catches client-render throws, not server-fetch 500s. The spec's error-injection approach doesn't exercise the boundary correctly. | ❌ spec rework |

### The e2e specs are a HYBRID MOCK → not a clean verification environment
`_fixture.ts` uses **real Clerk auth** (good) but **mocks only the client-side `/api/tenants`** while the
shell layout resolves tenants **server-side** (`fetchUserTenants` in the route-group layout) against the
**real backend**, AND the lisa/marca pages call real backend endpoints that 404 for the test tenant.
This hybrid produces artifacts (404s + an agenda hooks error) that are NOT production bugs. Per DoD #37 /
verification-real-not-200, these specs do not constitute valid live-verification as written.

## Conclusion — DoD #37 NOT satisfied yet (honest) ⟵ ★ SUPERSEDED por la RE-VERIFICACIÓN LIMPIA abajo (build fix → 6/6 PASS)

> Esta sección reflejaba la PRIMERA corrida (entorno con build error). Tras arreglar el entorno
> (deps del container) la re-verificación limpia dio 6/6 PASS — ver § RE-VERIFICACIÓN LIVE LIMPIA.

The 6 code fixes are **correct** (read-verified + 2493 unit tests + the shell renders live), committed,
and pushed (`132d17f6` + `98061462`). But a **clean** live-verification was not achieved:
- Chrome DevTools MCP not connected → no conversational live-verify.
- The e2e specs need rework (clean environment: either fully-seeded real backend for the test tenant,
  or consistent mocking incl. server-side; + fix the bug7 error-injection to exercise the client boundary).
- Two **pre-existing** issues surfaced (worth their own follow-up, NOT this story's fixes):
  - Backend 404s on `/api/v1/lisa/marca/{visuals,identity,contact}` for the test tenant.
  - `Rendered more hooks` on the `mateo/agenda` route (the Bug #1 landing target). ⚠️ This matters:
    Bug #1 lands users on `mateo/agenda`; if that route has a real hook bug (vs e2e artifact), the
    landing is degraded. **Needs investigation in dev-app with real seeded data** (likely related to
    the agenda view migrated in paradigm-map-zones, or the same family as bug #6 folded to lisa-doctores).

## Recommended path to DONE (Chris decision)

1. **Chris manual demo** against dev-app (the DoD #37 §5 `demo_signoff` gate — required anyway): exercise
   the 6 bugs with real data. This doubles as the live evidence. → `demo-script.md` provided.
2. **Investigate `mateo/agenda` "Rendered more hooks"** in dev-app (is it real or e2e-artifact?). If real,
   it's a separate bug (possibly fold to lisa-doctores / a new bugfix).
3. **Rework the e2e specs** to a clean environment (builder-frontend follow-up), so the `runtime_error_gate`
   is a true signal before `/auditor`.
4. Resolve the pre-existing lisa/marca backend 404s (separate backend story).

Story held at `state: developing` (`dod_live_verified: false`) — NOT advanced to developed, because the
DoD #37 live gate is not cleanly met and the agenda landing has an open question.

---

## RE-VERIFICACIÓN LIVE LIMPIA (2026-06-02, post arreglo de entorno) ★ DoD #37 satisfecho (6/6 testables)

**Bloqueo encontrado + resuelto:** el dev-server FE tenía un **build error global** (`Module not found:
sonner, react-window, react-hook-form`) → el Toaster global (`ui/sonner.tsx`) rompía TODA ruta, incl.
`/sign-in` → Clerk no cargaba → la re-auth de Playwright fallaba. **Causa: node_modules del CONTAINER
stale** (deps declaradas en package.json + código committeado por stories en `developing` —
mateo/agenda + lisa/staff — pero el volumen del container nunca se reinstaló). Fix no-destructivo:
`docker exec -w /app … pnpm install` + restart FE. **Esto es dominio de la story `estabilizar-harness-
e2e-lisa-marca`** (dev-env/e2e harness), no de este bugfix — pero bloqueaba la verificación.

**Spec de verificación limpia:** `e2e/regression/shell-nav-scroll/_live-verify.spec.ts` — real Clerk
auth (storageState + testing token) + **real backend** vía `real-backend-forward.fixture` (forward
`/api/v1/**` → :8002). **NO mock** → entorno honesto.

**Resultado:** `exit 0` · 7 passed + 1 flaky (Bug #1 passed on retry; el flaky fue
`route.fetch: Target page closed` = race de teardown del forward helper, NO la redirección).

| Bug | Verificación live | Veredicto |
|---|---|---|
| #1 | `/{tenant}` → URL termina en `/mateo/agenda` (no 404) | ✅ PASS |
| #1b | `/{tenant}/valeria/agenda` → 404 contextual | ✅ PASS |
| #2 | `tenant-switcher-trigger` visible con 1 tenant | ✅ PASS |
| #3 | ruta placeholder (lucas/lanzar): 0 `subtab-header-*` (SubTabHeader removido) | ✅ PASS |
| #4 | `app-panel-slot` content div `overflow-y = auto` | ✅ PASS |
| #5 | Presencia: 0 ocurrencias "Editor de landing pública" | ✅ PASS |
| #7 | error boundary `[agent]/error.tsx` presente + wired (estructural) | ⚠️ code-verified · live-trigger NO ejercido (forzar error client real es no-trivial) |

**`Rendered more hooks` en mateo/agenda: ERA ARTEFACTO DE BUILD** (deps faltantes → árbol React roto).
Con build limpio, el redirect a agenda corre **console-limpio**. Concern del Bug #1 landing: RESUELTO.

**Ruido residual (pre-existente, NO de este fix):** 404 backend en `/api/v1/lisa/marca/{trust-catalog/PE,
locations,visuals,identity,contact}` para el test tenant — gaps reales del BE; la página renderiza igual.

## Estado DoD
- `dod_live_verified: true` para los 6 bugs testables (acción real + console leída + efecto confirmado, real backend).
- Pendiente para `done`: (a) `demo_signoff` de Chris (DoD #37 §5, demo_required:true — separado del técnico);
  (b) opcional: live-trigger de Bug #7; (c) rework de los 6 e2e regression specs (hybrid-mock → real-backend pattern, como `_live-verify.spec.ts`); (d) /auditor.
