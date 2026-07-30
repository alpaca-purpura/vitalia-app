<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review: vitalia-bugfix-shell-nav-scroll-errors (6 shell bugs)

**Date:** 2026-06-03
**Story:** `vitalia/docs/product/stories/vitalia-bugfix-shell-nav-scroll-errors/`
**Type:** bugfix-lite (ADR-011) · FE-only · state=developed
**Files Reviewed:** 34 (32 in 132d17f6 + proxy.ts/shell-routes.ts in 1d2a58b5 + tsconfig in aeebe007 + 6 e2e specs reworked in 3dc7982e)
**Commits:** `132d17f6` (6 fixes) · `1d2a58b5` (Bug#1 root-cause edge-redirect) · `aeebe007` (widget tsc env-hygiene) · `3dc7982e` (e2e rework hybrid→real-backend)
**Domains touched:** shell-organism (chrome/routing/scroll/error-boundary) · iam/tenants · lisa/marca (brand-studio FE views)
**Skills consulted:** frontend-expert (FSD-Lite, Shadcn reuse, Server/Client split) · vitalia-design-system context (shell-organism tokens via overlay) · playwright-expert (anti-burbuja base.ts + real-backend fixture) · brand-expert (lisa/marca PresenciaView contract)
**Live-verified:** YES — e2e anti-burbuja gate re-run independently this session = **15/15 passed live** (`:3002` FE + `:8002` real BE). DoD #37 technical evidence present in checkpoint `dod_evidence` (6 testable bugs, real Clerk auth + real backend, writes exercised + console read + effect confirmed). `demo_signoff` PENDING (Chris business gate — separate, does NOT block this technical review).
**Verdict:** **APPROVED**

---

## /test-frontend Gate Status (re-run independently this session — stack UP :3002/:8002)

| Gate | Step | Result | Detail |
|---|---|---|---|
| QUALITY | `tsc --noEmit` | **PASS** | 0 errors strict (widget/vite.config.ts excluded — env-hygiene, widget/src still checked) |
| QUALITY | ESLint `src/` (60+ rules) | **PASS** | 0 errors, 0 warnings (official `fe_lint` validator) |
| QUALITY | ESLint this-story e2e | **PASS** (post self-fix) | 0/0 after removing 3 unused `eslint-disable` in `_live-verify.spec.ts` (Carril A) |
| QUALITY | Arch fitness | **PASS** | 171/171 (FSD boundaries, agent-catalog SSoT, no-clerk-org, subsubtabs SSoT) |
| FUNCTIONAL | Vitest `fe_unit_shell` | **PASS** | 652/652 |
| FUNCTIONAL | Vitest `fe_unit_lisa_marca` | **PASS** | 92/92 |
| FUNCTIONAL | Vitest shell-routes/proxy | **PASS** | 15/15 (incl. +4 bareTenantLandingRedirect behavioral) |
| FUNCTIONAL | **e2e anti-burbuja gate** | **PASS** | **15/15 LIVE** (re-run by auditor this session, `--workers=1`) |
| HEALTH | backend log clean | **PASS** | `verify-no-backend-errors.sh vitalia` → no ERROR/Traceback (marca-404s are 404s, not tracebacks) |
| HEALTH | jscpd | n/a | not run by gate-runner this story (bugfix-lite, orchestrator-driven); diff is small + deletes more than adds |
| HEALTH | knip | **SKIPPED — env gap** | knip NOT installed (not in package.json). Guarded risk (orphan `_fixture.ts`) already resolved: `_fixture.ts` git-rm'd in `3dc7982e` (verified absent). Manual dead-ref check = 0 dangling. NOT a failure. |
| HEALTH | madge | n/a | no new import added that could cycle; proxy.ts → shell-routes.ts is a leaf util import |
| HEALTH | npm audit | n/a | no dependency change in this story |

**Blocker steps (tsc / eslint-src / vitest / arch) ALL GREEN. e2e anti-burbuja gate GREEN. → no automatic FAIL.**

---

## Warning Baseline Movement

This is a **deletion-heavy bugfix** (`900 insertions, 239 deletions` in the main commit; deletes `SubTabHeader.tsx` 89 LOC + `InfoBannerLandingDescoped.tsx` 85 LOC + 2 test files). `src/` eslint warnings did NOT grow (exit 0, 0 warnings). The only warnings observed were 3 unused `eslint-disable` directives in `_live-verify.spec.ts` (e2e, out of `src/` baseline scope) → **self-fixed (Carril A), now 0**. The 42 errors in `eslint e2e/` are all in **pre-existing out-of-scope files** (`responsive-breakpoints`, `treatment-followup-mindful`, `specs/vitalia/*`) — a repo-wide e2e lint baseline that predates this story and is not a story validator. No baseline grew.

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | 0 |
| 3 | React Patterns | PASS | 0 |
| 4 | Code Quality | PASS | 0 (1 self-fixed) |
| 5 | Accessibility | PASS | 0 |
| 6 | Forms (RHF + Zod) | PASS (N/A) | 0 — no forms added/modified |
| 7 | Multitenancy | PASS | 0 |
| 8 | Master Data / Spanish | PASS | 0 |
| 9 | Security / Deps | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 |
| 11 | Domain Alignment / Agentic UI | PASS | 0 |
| 12 | Architecture Fitness (171) | PASS | 0 |
| 13 | Mirror detection | PASS | 0 |
| 14 | Decisions honored cite (R6) | N/A | `decisions_applicable` not set on any ticket |
| 15 | Connectivity (anti-isla) | PASS | 0 — no new surface; error.tsx auto-registered by Next convention |
| 16 | Visual fidelity (design system + scope + states) | PASS | 0 |

---

## Phase D — Gherkin / Business-Rules Matrix (RN-1..RN-6 + scenario coverage)

| RN | Rule | Tag | Scenario | Test(s) | Negative covered | PASS/FAIL/MISSING |
|---|---|---|---|---|---|---|
| RN-1 | Landing post-login SIEMPRE aterriza en ruta válida (nunca 404) | `@rule-routing-valid-landing` | bug1_routing_lands_valid | `bug1-routing-lands-valid.spec.ts` (happy: `/{tenant}`→mateo/agenda, gate ON) + shell-routes.test.ts +4 bareTenantLandingRedirect + not-found/SubSubTabsBar coverage_update | YES — bug1 negative: `valeria/agenda`→404 (gate OFF, intentional not-found) | **PASS** |
| RN-2 | Selector de tenant visible siempre que haya ≥1 tenant | `@rule-tenant-selector-always-visible` | bug2_tenant_selector_visible_single_tenant | `bug2-tenant-selector-visible.spec.ts` (trigger visible w/ 1 tenant, real BE) + `TenantSwitcher.test.tsx` (single-tenant window) | YES — `empty_state_no_tenants`: TenantSwitcher.test:88 "0 tenants → no trigger (preservado)" → fe_unit_shell | **PASS** |
| RN-3 | Ninguna hoja muestra título superior que duplique la nav activa | `@rule-no-redundant-title` | bug3_no_redundant_sheet_title | `bug3-no-redundant-title.spec.ts` (lucas/lanzar placeholder, 0 subtab-header-*) + PresenciaView.test "ya NO h2-eco 'Presencia'" + Identidad/VozTono view tests | YES — intra-content headings PRESERVED: PresenciaView.test renders "Señales de autoridad" + "Ubicaciones" → fe_unit_lisa_marca | **PASS** |
| RN-4 | Contenido scrolleable cuando excede el alto del panel | `@rule-content-scrollable` | bug4_content_scrolls | `bug4-content-scrolls.spec.ts` (app-panel-slot content div overflow-y=auto, gate ON) | (agenda inner-scroll non-broken — verified live in _live-verify; AppPanelSlot.tsx frame stays overflow-hidden) | **PASS** |
| RN-5 | Presencia no muestra "Editor de landing pública — próximamente" | `@rule-no-landing-placeholder` | bug5_no_landing_placeholder_presencia | `bug5-no-landing-placeholder.spec.ts` (scoped gate, 0 "Editor de landing pública") + PresenciaView.test "ya NO banner" | YES — rest of Presencia works: PresenciaView.test "Sitio web"/"Redes sociales"/trust/locations render → fe_unit_lisa_marca | **PASS** |
| RN-6 | Error en una hoja se aísla al panel; nav sigue clickeable | `@rule-error-isolated` | bug7_error_isolated_nav_alive | `bug7-error-isolated-nav-alive.spec.ts` (honest fault-injection marca→500 LIFO, Ribbon+SubTabsBar stay visible) + `error.test.tsx` (6 unit: fallback render, a11y, reset(), panel-scoped, neutro, default-export) | YES — error.test asserts NOT full-screen (no h-screen/fixed) + reset() re-mounts | **PASS** |

**No MISSING rows. All 6 business rules have a real test that PASSES (re-run live this session). All 8 scenario_coverage entries map to passing validators.**

### Rule #37 §3 anti-burbuja verification (REQUIRED)
- ✅ All 6 reworked specs import from `real-backend-forward.fixture` (which `mergeTests(base.ts runtimeGate, authed)` — composes anti-burbuja: pageerror / hydration / api-4xx5xx / Next overlay) — NOT `@playwright/test` directly. Verified by grep. `_live-verify.spec.ts` uses `@playwright/test` only for a type annotation (allowed).
- ✅ **bug5 SCOPED gate is HONEST:** `failOnRuntimeError:false` + `attachRuntimeErrorGuards` + manual re-assert. pageerror/hydration/Next-overlay still fail. Only the `KNOWN_BE_GAP_404` regex (`/api/v1/lisa/marca/(trust-catalog|locations|visuals|identity|contact)`) is allowlisted — pre-existing BE gaps owned by `vitalia-fase2-lisa-marca`. ANY non-allowlisted 4xx fails; ANY 5xx fails. The allowlist is **local to the spec + documented "NO agregar a base.ts global"** — it does NOT widen base.ts's tight global allowlist (which I read: only ClerkJS/CSS-parse/React-DevTools/401-redirect — no hydration/5xx/404).
- ✅ **bug7 honest fault-injection:** route `/api/v1/lisa/marca/**`→500 via LIFO override; everything else still forwards to real BE. Gate OFF by design (the boundary fallback IS the correct response). Asserts Ribbon + SubTabsBar stay visible = Bug #7's nav-isolation invariant. (Minor: spec asserts chrome-alive, not the `agent-error-boundary` testid in-panel; that in-panel render is covered by `error.test.tsx` unit. Acceptable — together they cover RN-6.)
- ✅ bug1-negative (valeria/agenda→404) present; removed bug2-0-tenants → covered by unit `empty_state_no_tenants` (TenantSwitcher.test:88) → fe_unit_shell; removed bug3-presencia variant → covered by fe_unit_lisa_marca (PresenciaView/Identidad/VozTono view tests). Removals documented in checkpoint + commit body. Coverage NOT lost.

### regression_guard verification
- `ShellOrganismLayout.test.tsx` (single-main/single-slot invariants) — **NOT in this story's diff** (last touched b65baae6, unrelated) → unmodified + green.
- `test-no-clerk-organizations.test.ts` — **NOT in diff** → unmodified + green.
- Re-ran both: 38/38 PASS. Full arch 171/171.
- `coverage_update` (not-found.test.tsx + SubSubTabsBar.test.tsx) = `valeria/agenda`→`mateo/agenda` reference update with documented rationale (NOT mechanical `-u`). Verified diff: comment + `mockPathname` + assertion-name updates only; the `no nav rendered` assertion semantics preserved.

---

## Findings

No FAIL findings. No WARN findings remaining after self-fix.

### Self-fix log (Carril A — gate-verified, FE surface, no new test)

**SF-1 — 3 unused `eslint-disable no-console` directives in `_live-verify.spec.ts`**
- **Category:** 4 (Code Quality)
- **File:** `vitalia/frontend/e2e/regression/shell-nav-scroll/_live-verify.spec.ts:35,49,93` (now :34,:47,:90)
- **Issue:** under `--max-warnings 0`, eslint flagged 3 redundant `// eslint-disable-next-line no-console` directives (the config already permits `console` in e2e specs) → "Unused eslint-disable directive" warnings.
- **Fix:** removed the 3 redundant directives. Mechanical, FE surface, no behavior change.
- **Existing test/gate that covers it:** the eslint rule engine itself + the e2e gate `playwright test e2e/regression/shell-nav-scroll/` (15/15 still passes — `_live-verify.spec.ts` is a manual evidence spec, not part of the smoke project's run, but its lint-cleanliness is now part of the same dir's lint surface).
- **Independent verification:** re-ran `eslint e2e/regression/shell-nav-scroll/ e2e/fixtures/{real-backend-forward.fixture,base}.ts --max-warnings 0` → **exit 0, 0 problems**. `eslint src/` → exit 0. ALL GREEN.
- **Stake-asymmetric?** No (lint hygiene on an evidence spec). **New test needed?** No.

> Note: this finding did NOT block the story's validators (`fe_lint` = `eslint src/` was already clean; the e2e gate is `playwright test`, which doesn't lint). It surfaced only under a broader `eslint e2e/` run. Self-fixed to keep the surface clean.

---

## Category detail

### Cat 1 — FSD-Lite — PASS
- All edits in correct slots: `app/`, `components/shared/shell-organism/`, `features/lisa/components/marca/`, `lib/`, `hooks/`, `stores/`. New `error.tsx` in route segment (Next convention). New fixture in `e2e/fixtures/`.
- `proxy.ts` imports `bareTenantLandingRedirect` from `@/lib/shell-routes` (leaf util — allowed). No cross-feature deep import. No new madge cycle. Arch 171/171 (FSD boundaries + no-cross-imports) green.
- `error.tsx` is `default export` — justified Next.js `error.tsx` contract exception (same as `mateo/agenda/error.tsx`); documented in the file + 05-guidelines. Arch test allows error.tsx default exports.

### Cat 2 — Server/Client — PASS
- Bug #1: 3 redirects use `redirect()` server-side (Server Components) + edge `proxy.ts` (the right layer for the Next 16 soft-nav workaround). The root-cause analysis (Server-Component intra-route-group `redirect()` triggering Next 16.2.3 Router soft-nav → "Rendered more hooks") is sound; moving to a 307 edge redirect is the correct, minimal workaround (UUID-only match, runs AFTER `auth.protect()`, Server redirect kept as defense).
- Bug #7 `error.tsx`: correctly `"use client"` (Next requirement) — uses `useEffect`. No Server Component using hooks. `AppPanelSlot` stays a Server Component hosting Client slots.
- Bug #2 `useStoreHydration(useTenantStore)` added inside the `ssr:false` chunk (`ShellOrganismLayoutClient`), unconditionally at the top before any branch → D3 hook-count stable. Correct.

### Cat 3 — React Patterns — PASS
- Bug #7 error boundary present (was the gap — only `mateo/agenda/error.tsx` existed; now generic `[agent]/error.tsx`). loading/error/empty states intact on the views.
- Bug #2: the new hook is unconditional + top-level (no conditional/looped hooks) — D3 honored; the diff comment explicitly calls out "ANTES de cualquier branch — hook-count estable". Verified by reading the diff: `useStoreHydration(useShellStore)` then `useStoreHydration(useTenantStore)` both before the first `useShellStore((s) => ...)` selector.
- `useEffect([error])` dep array correct in error.tsx.

### Cat 5 — Accessibility — PASS
- `error.tsx`: `role="alert"` + `aria-live="assertive"`, semantic `<Button>`, `aria-hidden` on decorative icons, Shadcn `Alert` primitives. Unit test asserts role/aria-live. Strong.

### Cat 7 — Multitenancy — PASS
- Bug #2 touches only the non-PHI tenant bootstrap. Hooks use `useTenantId()` (post-2026-06-01 fix), NOT Clerk org — `test-no-clerk-organizations.test.ts` green. `proxy.ts` UUID match never touches `X-Tenant-ID` injection. No hardcoded tenantId.

### Cat 8 — Master Data / Spanish — PASS
- `error.tsx` user-facing strings in Spanish neutro (tuteo): "No se pudo cargar esta sección", "Puedes intentar recargarla", "Reintentar". `error.test.tsx` asserts anti-voseo regex + presence of "Puedes"/"Reintentar". No voseo. No hardcoded currency/date.

### Cat 9 — Security / Deps — PASS
- No `dangerouslySetInnerHTML`, no `eval`, no secrets in client. `error.tsx` logs `error.message` only (NO-PHI, dev-only display). No dependency change. proxy.ts edge redirect runs after `auth.protect()` (anonymous users already sent to sign-in).

### Cat 11 — Domain Alignment (lisa/marca brand-studio FE) — PASS
- Bug #3/#5 touch `PresenciaView`/`IdentidadView`/`VozTonoView` (lisa/marca). Only the top echo-h2 + the descoped landing banner removed. The brand-studio field-contract surfaces (AutosaveBadge, trust signals, locations, website, redes) PRESERVED + tested. No FieldContract/form-runtime change. No hardcoded labels added.

### Cat 13 — Mirror detection — PASS
- New files `error.tsx` + `real-backend-forward.fixture.ts` have NO cross-brand basename collision (nicolify/comunify/lupulo searched → none).
- Bug #1 `DEFAULT_LANDING_SUBPATH`/`bareTenantLandingRedirect` defined ONCE in `lib/shell-routes.ts`, consumed by 3 redirects + proxy via import (no string-literal repetition — exactly the SSoT the guidelines required). No `valeria/agenda` literal remains.
- The forwarding fixture is a deliberate LIFT (docstring cites anti-duplication.md — forwarding lives once, not inline ×14 specs). Good.

### Cat 15 — Connectivity (anti-isla) — PASS
- No new user-facing surface (bugfix corrects existing). `error.tsx` auto-registered by Next.js `error.tsx` filename convention (no manual include needed). 03-arch § Integration design present + correct.

### Cat 16 — Visual fidelity — PASS
- No Shadcn primitive reinvented (error.tsx reuses `Alert`/`Button`/`AlertTitle`/`AlertDescription`). No hardcoded hex/px (semantic tokens: `variant="destructive"`, `text-muted`, etc.). Scope discipline honored: only the 6 bugs' surfaces touched; `lisa/staff` (non-egoísmo) NOT touched; `features/mateo` NOT touched (flake was Next-framework, not agenda code); `components/ui/` NOT touched. Required states present (error boundary = the error state; the scroll/title/banner fixes preserve existing loading/empty states). Live-verified.

---

## Contract / UI-SPEC Compliance
- [x] No new TypeScript types/DTOs (bugfix). Existing types intact (tsc 0 errors).
- [x] Component hierarchy preserved (AppPanelSlot Server hosting Client slots; error.tsx in segment).
- [x] Server/Client boundaries correct (redirects server + edge; error.tsx client).
- [x] Test surfaces exist (TDD repro-first per ADR-011: error.test.tsx, shell-routes.test +4, 6 e2e specs).
- [x] capability change_log `type: fix` on `shell-organism.shell-vitalia` (+ `brand_studio.lisa-marca` for #3/#5) to be actioned by /pm-vitalia at merge (Fase F.3).

## Allowlist Movement
- [x] No FE arch fitness allowlist grew (171/171, no allowlist edits in diff).
- [x] No warning baseline grew (src/ eslint 0/0; the 3 e2e warnings self-fixed to 0).

## Native-First Audit
- [x] No `docker exec ... tsc|eslint|vitest|playwright` in commits.
- [x] No `make e2e` / `make e2e-smoke` in commits (e2e run native via `E2E_BASE_URL` + `--project=smoke`).
- [x] No `git add .` / `-A` / `-u` evident (scoped FE paths in commits).

## Live Verification Audit
- [x] User-facing change → live verification present: e2e anti-burbuja gate 15/15 (re-run by auditor this session) + checkpoint `dod_evidence` (real Clerk auth + real backend, 6 testable bugs exercised, console read, effect confirmed).
- [x] Bug #1 "Rendered more hooks" concern RESOLVED: root-caused as Next 16.2.3 Router soft-nav (not features/mateo) + the build-deps-stale artifact; edge-redirect fix validated `/{tenant}` 0/5 crashes. Backend log clean.
- Note: `demo_signoff` (Chris business gate, DoD #37 §5) PENDING — separate from this technical review, does NOT block APPROVED. Orchestrator stops for it after the auditor.

---

## Verdict Math
- No FAIL in cat 1/2/3/7/11/12/14 → no automatic FAIL.
- Cat 16 PASS (no reinvented primitive, no scope creep, required error state present, no hardcoded token) → no FAIL.
- No allowlist/baseline grew without justification → no FAIL.
- No `/test-frontend` blocker (tsc/eslint-src/vitest/arch) FAIL → no FAIL.
- 171/171 arch fitness PASS → no FAIL.
- Downstream regression scope: changes touch `lib/shell-routes.ts` (consumed by proxy + redirects + SubSubTabsBar) and `stores/tenant-store` (via rehydration) + `components/shared/shell-organism/` (cross-feature shell consumer). Coverage: full vitest run was green at build (2493/2493 per BUILD-LOG) + I independently re-ran fe_unit_shell 652/652 + arch 171/171 + e2e 15/15 → downstream covered, no regression.
- Skills consulted documented (frontend-expert + design-system + playwright-expert + brand-expert) — present in 05-guidelines must_load_skills + reflected in code.
- Live verification gate met (e2e 15/15 + dod_evidence). No UX_HANDOFF gap (bugfix-lite ADR-011: no new UI surface, checkpoint = spec-lite, ratified by Chris).
- Two or more category WARNs? No (0 WARN after self-fix).

→ **APPROVED**

## Downstream regression scope

| Surface modified | downstream_test_targets (FE) | gate status |
|---|---|---|
| `lib/shell-routes.ts` (DEFAULT_LANDING_SUBPATH + bareTenantLandingRedirect) | shell-routes.test.ts, proxy.test.ts, SubSubTabsBar.test, not-found.test, e2e bug1 | PASS (15/15 unit + e2e bug1 live) |
| `stores/tenant-store` (rehydration call) | fe_unit_shell (TenantSwitcher.test + store), e2e bug2 | PASS (652/652 + e2e bug2 live) |
| `components/shared/shell-organism/AppPanelSlot,SubTabContent,TenantSwitcher,ShellOrganismLayoutClient` | fe_unit_shell, arch_fsd, e2e bug2/3/4/7 | PASS (652/652 + 171/171 + e2e) |
| `features/lisa/components/marca/*` (Presencia/Identidad/VozTono) | fe_unit_lisa_marca, e2e bug3/5 | PASS (92/92 + e2e) |

No scoped-out downstream consumer left unverified.

---

## Re-audit iteration (bug#2 delta) 2026-06-03

**Commit:** `b2d1dfd4` — 4 files (useTenants.ts · types.ts · TenantOption.tsx · bug2-tenant-selector-visible.spec.ts)
**Scope:** delta-only re-audit; bugs #1/#3/#4/#5/#7 unchanged + APPROVED from prior review. Prior verdict STALE for bug#2 only (live-verify on dev-app revealed selector hidden due to /api/tenants 404).
**Auditor:** claude-sonnet-4-6
**Date:** 2026-06-03

### Gates re-run independently (stack UP :3002/:8002)

| Gate | Result | Detail |
|---|---|---|
| `tsc --noEmit` | **PASS** | 0 errors (exit 0, no output) |
| `eslint` (4 delta files, `--max-warnings 0`) | **PASS** | 0 errors, 0 warnings (exit 0) |
| `test-no-clerk-organizations.test.ts` (arch) | **PASS** | 16/16 — `useTenants.ts` uses `useAuth()` userId NOT orgId; no-clerk-org invariant preserved |
| Vitest full suite | **PASS** | **2502/2502** — includes TenantOption.test (4), TenantSwitcher.test (24), tenant-store.test, tenant-store-hydration.test (18), TenantStoreBootstrap.test (18). All tenant-surface tests pass with the new bare-array + optional city shape. |
| e2e `bug2-tenant-selector-visible.spec.ts` (cold-start) | **PASS** | 15/15 (full shell-nav-scroll suite, `--workers=1`). Bug2 cold-start: `addInitScript` clears `vitalia-tenant-state` localStorage key → no activeTenant seeded → fetch to `/api/v1/iam/users/me/tenants` hits real BE → selector "Sanaré LATAM" visible within 15 s timeout. |

### Specific checks for this delta

**§ Tenant isolation — endpoint scope confirmed CLEAN**
- `/api/v1/iam/users/me/tenants` maps to `auth_router.get_my_tenants` in `core/luana-core-iam/src/luana_core_iam/api/routers/auth_router.py:23-33`. The endpoint calls `UserService.get_user_tenants(user.id)` — **user-scoped**: returns only the tenants the JWT-authenticated user belongs to. Derived from JWT identity (via `get_user_from_token` dependency), NOT from an admin scan.
- The admin "list ALL tenants" endpoint is `tenant_router.list_tenants` at `GET /` (routed separately as `/tenants`, NOT `/api/v1/iam/users/me/tenants`). `useTenants.ts` does **NOT** use it. Zero cross-tenant leak risk.

**§ No-clerk-organizations — CONFIRMED CLEAN**
- `useTenants.ts` uses `const { getToken, userId, isLoaded, isSignedIn } = useAuth()` — no `orgId`, no `useOrganization`. Comment on line 24 explicitly documents this.
- Arch test `test-no-clerk-organizations.test.ts` 16/16 PASS (re-run this session). The new file is scanned by the test; no violation introduced.

**§ Backward compatibility of Tenant.city optional**
- `city` is now `readonly city?: string` in `types.ts` (was required before). Only consumer in non-test code: `TenantOption.tsx:55` — already guarded with `{tenant.city ? (<span>...) : null}`. No other component in `shell-organism/` accesses `.city` (grep confirmed). `TenantBadge.tsx` does not use city. All Vitest tests for `TenantOption` pass (4/4 — testid, data-active, named export).
- The `TenantsApiResponse = ReadonlyArray<Tenant>` (bare array) is correctly handled: `useTenants` calls `setAvailableTenants(query.data)` directly (not `.tenants`). The store's `setAvailableTenants` accepts `ReadonlyArray<Tenant>` — type-safe.

**§ Cold-start honesty — spec GENUINELY exercises real fetch**
- `addInitScript(() => localStorage.removeItem("vitalia-tenant-state"))` runs BEFORE page navigation — clears any persisted `activeTenant` from Zustand persist (key `vitalia-tenant-state`). This forces the React Query bootstrap to cold-start: `useTenants` fires the real `GET /api/v1/iam/users/me/tenants` via the forward fixture to real BE :8002. Only if that call returns populated data does the store hydrate and the trigger render. If the endpoint URL regressed back to `/api/tenants` (404), `availableTenants` would stay empty → `TenantSwitcher` returns null → `toBeVisible` fails. The regression signal is real and would have caught the original bug.
- Gate anti-burbuja inherited from `real-backend-forward.fixture` (composes `base.ts` with pageerror/hydration/api-4xx5xx/Next-overlay guards). The `lucas/lanzar` route has no pre-existing BE 404s of its own, so no allowlist needed — gate is fully tight. The spec imports from `../../fixtures/real-backend-forward.fixture` (NOT `@playwright/test` directly). Verified.

**§ Spanish neutro in comments/docs**
- All new comments/docstrings in the 4 delta files use Spanish neutro or English. No voseo detected. (`"selector oculto"`, `"lista vacía"`, `"Subtítulo opcional"` — all compliant).

**§ No new FSD violation**
- `useTenants.ts` lives in `src/hooks/` (global hooks layer — correct for shell-organism bootstrap). Import of `TenantsApiResponse` from `@/components/shared/shell-organism/types` is allowed (feature importing from shared). No cross-feature boundary crossed.

### Verdict for bug#2 delta

All checks PASS. The fix is minimal, correct, and honest:
- Endpoint corrected to the real BE path (`/api/v1/iam/users/me/tenants`)
- Response shape aligned to real BE contract (bare array, `city` optional)
- E2e spec reworked to genuinely exercise the cold-start fetch path (the old spec masked the bug by relying on seeded storageState — the new spec cannot pass if the endpoint regresses)
- No cross-tenant leak (user-scoped endpoint, JWT-derived)
- No Clerk org usage reintroduced
- All gates GREEN (tsc/eslint/arch/vitest 2502/vitest-e2e 15)

→ **APPROVED (confirmed, delta merged into prior APPROVED)**

**Overall story verdict: APPROVED** (bugs #1/#3/#4/#5/#7 unchanged APPROVED + bug#2 delta now APPROVED)

**Remaining pre-done gates (not blocking technical APPROVED):**
- `demo_signoff` Chris (DoD #37 §5 — business gate, separate from auditor)
- `/pm-vitalia` Fase F merge (including `git mv` archive + cap YAML update)
