<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review: T-3 — Dashboard welcome + features/dashboard/ (vitalia)

**Date:** 2026-05-19
**PR / CONTRACT / UI-SPEC:** `vitalia/docs/product/stories/vitalia-auth-base-functional/{01-spec.md § SC-06/SC-07, 03-arch-brief.md, 05-guidelines.md}`
**Brand:** vitalia
**Ticket:** T-3 (commit `69aaab1`)
**Files Reviewed:** 7 files (5 NEW dashboard feature, 2 EDIT app pages)
**Domains touched:** dashboard feature (FSD-Lite), `(dashboard)/layout.tsx` + `page.tsx`
**Skills consulted:** frontend-expert, brand-expert (design tokens), tessl__react-patterns, tessl__nextjs-app-router-modularization
**Live-verified:** N (deferred to T-6.b)
**Verdict:** **WARN** (1 unnecessary `"use client"`; rest PASS)

## /test-frontend Gate Status (scoped src/)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors |
| ESLint src/ | PASS | 0 errors, 0 warnings |
| Arch fitness | PASS | 38/38 (incl. server-first ratchet — does NOT detect unnecessary `"use client"`) |
| Vitest dashboard tests | PASS | 3/3 GREEN (renders_welcome_with_tenant_context, renders_onboarding_cta_when_not_onboarded, hides_onboarding_cta_when_onboarded) |
| Full vitest | PASS | 309 tests / 45 files |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | `features/dashboard/{components,types,__tests__}/`; barrel `index.ts` exports named components + types; no default exports; no cross-feature imports |
| 2 | Server/Client | **WARN** | `SliceOneStubsRow.tsx` declares `"use client"` but has NO useState/useEffect/event handlers — static list. Justification "future iterations will add interactive hover state" is **speculation**. Per Server-First default, should be Server Component. |
| 3 | React Patterns | PASS | Error boundary: graceful degradation via try/catch with safe defaults on IAM fetch fail (line 64-80). Loading state: Server-rendered (no loading needed — fetch awaited). Empty state: stub cards always render (static). Keys: `key={card.label}` stable (label unique per data). No `useMemo`/`useCallback` over-memoization. |
| 4 | Code Quality | PASS | TS strict, ESLint clean, no `any`, types explicit (`DashboardUserData`, `DashboardWelcomeProps`). No disabled rules. |
| 5 | Accessibility | PASS | Semantic `<main>` (from layout), `<section aria-label="Bienvenida al panel">`, `<h1>` for greeting, `aria-label` on stubs grid, `data-testid="tenant-badge"`, `role="list"` + `role="listitem"`, `focus-visible:ring-2` on CTA Link. Keyboard nav OK. |
| 6 | Forms | N/A | No forms |
| 7 | Multitenancy | PASS | `fetchDashboardUser` injects `X-Tenant-ID: ${authResult.orgId}` (line 32). Server-side fetch only — no client tenant leak. Clerk JWT auth via `Authorization: Bearer ${token}`. |
| 8 | Master Data / Spanish | PASS | "Hola, {firstName}", "Configurar tu clínica", "Completa la configuración..." — tuteo neutro, tildes correctas. No voseo (verified grep on `dashboard/`). No hardcoded currency. |
| 9 | Security / Deps | PASS | `process.env.NEXT_PUBLIC_API_URL` fallback `http://localhost:8002` — env-driven (P9 anti-pattern guard). No `dangerouslySetInnerHTML`. No eval. JWT consumed server-side, never exposed to client. HIPAA-lite: no PHI in localStorage/sessionStorage (T-3-result.md notes "server-side fetch only"). |
| 10 | Tests / TDD | PASS | RED-first explicit: T-3-result.md "RED: `1 failed (1)` — Cannot find module '../components/DashboardWelcome'" → "GREEN: 3 tests passed". Test file at line 16-145 mocks `@clerk/nextjs/server::auth`, `next/navigation::redirect`, `next/link::default`, and `fetch`. 3 scenarios cover SC-06 + SC-07 (CTA visible + hidden branches). |
| 11 | Domain Alignment | PASS | `DashboardUserData` types as camelCase mirror of `IAMUserResponse` (BE `vitalia/backend/src/modules/vitalia/iam/api/router.py` exists, verified). HIPAA-lite: dashboard surface no PHI display (only identity fields firstName / clinicName / planTier — per hipaa-lite.md SSoT, these are NOT PHI; PHI is patient.name, patient.dni, diagnosis, etc.). |
| 12 | Architecture Fitness | PASS | All 38 tests pass; no allowlist growth. SliceOneStubsRow.tsx's superfluous `"use client"` is NOT flagged by `test_server_first.test.ts` (test catches missing use-client, not excess) — see Cat 2 WARN below. |
| 13 | Mirror detection | PASS | No Nicolify dashboard mirror; features/dashboard/ is brand-specific. `useDashboardData` API hook from 05-guidelines.md whitelist intentionally not implemented (Server Component fetch direct per P5 Pattern — valid simplification, not a guideline breach since fetch+types live where ownership dictates). |
| 14 | Decisions honored cite | PASS | T-3-result.md cites SC-06, SC-07 scenario coverage + HIPAA-lite invariant explicit ("server-side fetch only, no PHI in localStorage/sessionStorage per hipaa-lite.md"). |

## Findings

### WARN: SliceOneStubsRow unnecessarily client-bundled

**Category:** 2 (Server/Client)
**File:** `vitalia/frontend/src/features/dashboard/components/SliceOneStubsRow.tsx:1`
**Issue:** Component declares `"use client"` directive but contains no client-only APIs:
- No `useState` / `useEffect` / `useRef` / etc.
- No event handlers (`onClick` / `onChange` / etc.)
- No browser-only APIs (`window`, `document`)

Verified via grep: 0 matches for `useState|useEffect|onClick|onChange|useRouter|onMouseEnter` in this file.

Justification in line 9-11: *"Client Component: uses `"use client"` because future iterations will add interactive hover state and progressive disclosure"* — this is **speculative**. Per Server-First default and `tessl__nextjs-app-router-modularization`, components should be Server-rendered unless current functionality requires Client. Speculative future needs are an anti-pattern (premature client bundling).

**Impact:** Static stub cards (~5 items) ship as client JS bundle (~1-2KB minified after tree-shake). Minor footprint, but contributes to Server-First erosion.

**Fix:** Remove `"use client"` directive (line 1). Component renders as plain HTML Server Component. If interactive hover requires Client conversion later, do it then with measured justification.

```diff
-"use client";
-
 /**
  * SliceOneStubsRow — 5 coming-soon stub cards for Slice 1 features.
```

**Skill ref:** `tessl__nextjs-app-router-modularization` (Server-First default), `frontend-expert/references/component-rules.md` ("`"use client"` is FORBIDDEN for files that only use Server-safe APIs"). Arch fitness `test_server_first.test.ts` does NOT catch this (checks INVERSE: missing use-client on hook-using files), so this is a manual code-review finding, not arch ratchet violation.

### Minor observations

- **Server Component pattern correct on DashboardWelcome**: `auth()` + `redirect()` + server fetch — no client overhead, no JWT exposure. ✅
- **Graceful degradation**: try/catch around `fetchDashboardUser` with safe defaults (line 64-80) — per `tessl__graceful-degradation`. ✅
- **Test mocking patterns clean**: `vi.mock(...)` declared BEFORE component import (hoisting safe, comment on line 21), proper `vi.clearAllMocks()` in `beforeEach`. ✅
- **HIPAA-lite invariant 1 honored**: no PHI fields rendered (no `patient.name`, `diagnosis`, etc. — verified grep). Dashboard surface is identity-only.
- **AppShell wrap is Server → Client boundary**: `layout.tsx` is Server (exports metadata), `AppShell` is `"use client"` (preexisting infrastructure). Valid pattern.
- **`useDashboardData.ts` hook omitted**: 05-guidelines.md whitelist mentions it, but T-3 chose direct Server fetch — simpler + correct given no client-side refetch need. Acceptable deviation since Server-First design supersedes optional React Query (per P5 Pattern in 05-guidelines.md: "React Query hook `useDashboardData` SOLO si necesita refetch cliente (sino server fetch directo)").

## Contract / UI-SPEC Compliance

- [x] SC-06: h1 "Hola, {firstName}" + tenant badge "{clinicName} · {planTier}" + slice stubs row visible
- [x] SC-07: CTA "Configurar tu clínica" → `/onboarding/wizard` visible iff `!isOnboarded`
- [x] Wireframe match (spec § 4 dashboard): Vitalia logo + UserButton in TopBar (from AppShell); greeting + badge + CTA + stubs grid in main
- [x] Spanish neutro microcopy (no voseo)
- [x] Server Component default honored (DashboardWelcome.tsx, page.tsx, layout.tsx)
- [x] HIPAA-lite: no PHI client-side
- [x] Tests cover positive + negative CTA branches (3 scenarios)

## Allowlist Movement

- No FE arch fitness allowlist modified.

## Native-First Audit

- [x] No Docker test runs
- [x] No `git add .`
- [x] Conventional commit prefix `feat(vitalia/frontend): T-3 ...` ✅

## Live Verification Audit

- [WARN] `chrome-devtools-verify` deprecated for Linux Mint — gated to T-6.b post-deploy LIVE smoke + visual baseline (`e2e/visual/visual-smoke.spec.ts::dashboard.png`). T-3-result.md explicitly escalates: "Manual verification required — escalated to Chris staging gate per project_context Step 4."

## Downstream regression scope

| Surface modified | Downstream | Verified? |
|---|---|---|
| `features/dashboard/{components,types}/` NEW | brand-local; no cross-feature consumers (barrel `index.ts` exports for internal use within `app/(dashboard)/page.tsx` only) | YES |
| `app/(dashboard)/page.tsx` EDIT | route consumer of `features/dashboard` barrel; no breaking change | YES |
| `app/(dashboard)/layout.tsx` EDIT | delegates to existing `AppShell` (preexisting); no break | YES |
| BE dependency `/api/v1/iam/me` | exists at `vitalia/backend/src/modules/vitalia/iam/api/router.py` (verified grep) | YES |

No cross-brand mirror. No engine edit. Scope contained.

## Verdict Math

- Categories: 13 PASS, 1 WARN (Cat 2 — superfluous `"use client"`)
- Live-verified WARN documented + gated to T-6.b
- Allowlist preserved
- TDD discipline explicit + verified
- **Overall: WARN** (single Cat 2 WARN, fix is 1-line removal of directive; not blocking but should be addressed in follow-up commit or merge prep)

## Recommended remediation

Single 1-line edit at `vitalia/frontend/src/features/dashboard/components/SliceOneStubsRow.tsx:1`:
- Remove `"use client";` directive
- Update header comment (line 9-12) to remove speculative justification

If/when interactive hover state is genuinely needed in a follow-up, re-add `"use client"` with measured justification. Until then, Server Component default is the correct choice. Bundle size + Server-First principle benefit.
