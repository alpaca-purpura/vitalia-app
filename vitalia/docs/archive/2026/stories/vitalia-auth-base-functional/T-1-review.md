<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review: T-1 — Clerk Middleware (vitalia)

**Date:** 2026-05-19
**PR / CONTRACT / UI-SPEC:** `vitalia/docs/product/stories/vitalia-auth-base-functional/{01-spec.md, 03-arch-brief.md, 05-guidelines.md, 06-tickets.yaml}`
**Brand:** vitalia
**Ticket:** T-1 (commit `e80c806`)
**Files Reviewed:** 2 (`src/middleware.ts` NEW, `src/__tests__/middleware.test.ts` NEW)
**Domains touched:** auth/middleware (Edge Runtime)
**Skills consulted:** frontend-expert, tessl__react-patterns (N/A baseline confirmed), tessl__nextjs-app-router-modularization
**Live-verified:** N (chrome-devtools-verify deprecated for Linux Mint; runtime-gated to T-6.b post-deploy)
**Verdict:** **PASS**

## /test-frontend Gate Status (scoped src/ per validator nf-fe-eslint)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors strict mode |
| ESLint src/ --max-warnings=0 | PASS | 0 errors, 0 warnings (validator scope src/) |
| Arch fitness (38 tests) | PASS | 38/38 |
| Vitest (309 total, middleware: 7) | PASS | 7/7 middleware tests GREEN |

Note: gate-output.json reports eslint FAIL with 42 errors — those are in `e2e/` PRE-EXISTING from prior stories (booking/onboarding specs), NOT in T-1 scope. Validator `nf-fe-eslint` scopes to `src/` per 04-validators.yaml → T-1 is GREEN.

## Warning Baseline Movement

Vitalia FE has its own ratchet (no luana root baselines apply post-multibrand reorg). Existing arch fitness allowlists not modified by T-1.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | middleware.ts at top-level `src/` per Next.js convention (Edge Runtime, not a feature) |
| 2 | Server/Client | PASS | Edge Runtime module, no `"use client"`, no React |
| 3 | React Patterns | N/A | Not a React component |
| 4 | Code Quality | PASS | TS strict, ESLint clean, no `any`, no disabled rules |
| 5 | Accessibility | N/A | Middleware (no UI) |
| 6 | Forms | N/A | No forms |
| 7 | Multitenancy | PASS | Webhook route `/api/v1/vitalia/webhooks(.*)` explicitly public (BE validates HMAC). No tenant hardcode. |
| 8 | Master Data / Spanish | N/A | No user-facing strings |
| 9 | Security / Deps | PASS | No secrets, no eval/dangerouslySetInnerHTML, no client-bundled tokens; webhook routes correctly public to allow BE HMAC validation |
| 10 | Tests / TDD | PASS | RED-first explicit (T-1-result.md: "test failing → middleware.ts not found"). 7 tests cover structural invariants (public routes, matcher excludes _next, auth.protect(), no manual redirect, no RBAC, no `"use client"`) |
| 11 | Domain Alignment | PASS | Clerk Next.js 16 canonical pattern (`clerkMiddleware` + `createRouteMatcher`) |
| 12 | Architecture Fitness | PASS | All 38 ratchet tests preserved |
| 13 | Mirror detection | PASS | Per anti-duplication.md A4: Clerk SDK direct, not Nicolify copy; matcher patterns Clerk-canonical (no brand-specific lift candidate detected) |
| 14 | Decisions honored cite | N/A | Ticket has no `decisions_applicable` per 06-tickets.yaml; story-level decisions (D1, D5) cited in commit body via T-1-result.md |

## Findings

### PASS notes

- **A10 anti-pattern resolved**: `/api/v1/vitalia/webhooks(.*)` explicitly public (matcher line 21). Webhook user.created from Clerk reaches BE without 401. Test `middleware.test.ts:58` enforces.
- **Matcher excludes static assets correctly**: `_next` + html/css/js/images/fonts/icons per Clerk recipe (line 34).
- **No manual redirect**: `auth.protect()` delegates to Clerk (test line 99-102 enforces absence of `NextResponse.redirect(...sign-in)`).
- **No RBAC in middleware**: per spec § 3 D5 — defer RBAC to BE; test line 105-110 enforces absence of `role === | sessionClaims.role | user.role`.
- **TDD discipline cemented**: T-1-result.md documents RED-first commit ordering; tests written → fail → middleware created → pass.

### Minor observations (informational, not blocking)

- Middleware tests are **structural** (regex on source string), not runtime (clerkMiddleware not directly unit-testable without Next.js runtime). This is per `playwright-expert` SSoT — runtime semantics (SC-01/SC-02 redirect behavior) deferred to E2E (T-6.a + T-6.b post-deploy). Acceptable tradeoff documented in test header comments.
- `auth.protect()` is awaited but Clerk's API returns a Promise that resolves to undefined on auth pass — fine since rejection branch is uncatchable redirect.

## Contract / UI-SPEC Compliance

- [x] SC-01 root protected → matcher includes default path (covered by `auth.protect()` else branch)
- [x] SC-02 `/public(.*)` returns 200 without redirect (matcher line 20)
- [x] Webhook route `/api/v1/vitalia/webhooks(.*)` public (A10 anti-pattern guard)
- [x] No RBAC in middleware (D5 defer)
- [x] Decision D5 (single-branch worktree `wip/vitalia`) honored — commit on canonical branch

## Allowlist Movement

- No FE arch fitness allowlist modified. Ratchet preserved.

## Native-First Audit

- [x] No `docker exec ... tsc|eslint|vitest`
- [x] No `make e2e*`
- [x] No `git add .` / `-A` / `-u` (commit shows 3 specific files staged)

## Live Verification Audit

- [WARN] `chrome-devtools-verify` skill deprecated for Linux Mint native (designed for WSL2+Windows bridge). T-1-result.md documents fallback: "Live verification documented for Chris staging gate once T-3 completes env setup". Acceptable per skill deprecation notice. Runtime SC-01/SC-02 verification gated on T-6.b LIVE smoke post-deploy.

## Downstream regression scope

| Surface modified | Downstream coverage | Verified? |
|---|---|---|
| `vitalia/frontend/src/middleware.ts` | vitalia FE only — middleware is Edge Runtime, no cross-feature consumers | YES (no other feature imports middleware.ts) |
| `vitalia/frontend/src/__tests__/middleware.test.ts` | brand-local arch fitness; magic comment `downstream-regression-na` line 16 documented | YES |

No engine edit, no cross-brand mirror. Scope contained.

## Verdict Math

- Categories all PASS / N/A → **PASS**
- Live verification skill deprecated → WARN documented, gated on T-6.b
- No arch fitness regression
- TDD evidence explicit
