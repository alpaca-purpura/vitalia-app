<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review: T-2 — Clerk SignIn/SignUp pages + DELETE legacy step-{1,2,3} stubs (vitalia)

**Date:** 2026-05-19
**PR / CONTRACT / UI-SPEC:** `vitalia/docs/product/stories/vitalia-auth-base-functional/{01-spec.md, 03-arch-brief.md, 05-guidelines.md}`
**Brand:** vitalia
**Ticket:** T-2 (commit `dcd34d6`)
**Files Reviewed:** 5 (2 EDIT auth pages, 3 DELETE step-{1,2,3})
**Domains touched:** auth pages (Server-rendered pages wrapping Clerk Client components)
**Skills consulted:** frontend-expert, tessl__react-patterns, tessl__shadcn-ui (N/A — no Shadcn), tessl__tailwind, tessl__nextjs-app-router-modularization
**Live-verified:** N (deferred to T-6.a/T-6.b)
**Verdict:** **PASS**

## /test-frontend Gate Status (scoped src/)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors |
| ESLint src/ --max-warnings=0 | PASS | 0 errors, 0 warnings |
| Arch fitness (38) | PASS | FE-A1 (no-hardcoded-colors) PASS via `var(--vitalia-cian-color)` CSS variable refs |
| Vitest 306 (T-2 baseline) | PASS | 306/306 |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | Auth pages live in `app/(auth)/sign-in,sign-up/page.tsx` per Next.js route groups; no cross-feature imports |
| 2 | Server/Client | PASS | Pages are Server Components (export `metadata`, no `"use client"`); Clerk `<SignIn />` / `<SignUp />` are internal Client boundaries — valid Next.js App Router pattern |
| 3 | React Patterns | PASS | No async UI managed by parent; Clerk components handle their own loading/error/success states. No useEffect, no stale closures, no missing keys (no lists). |
| 4 | Code Quality | PASS | TS strict, ESLint 0/0, no `any`, no disabled rules |
| 5 | Accessibility | PASS | Semantic `<main>`; Clerk components are ARIA-compliant out-of-box; focus management delegated to Clerk |
| 6 | Forms | N/A | Forms are owned by Clerk |
| 7 | Multitenancy | PASS | No tenant logic in auth pages (auth precedes tenant context); Clerk JWT carries `orgId` consumed by dashboard later |
| 8 | Master Data / Spanish | PASS | Metadata titles "Iniciar sesión — Vitalia" / "Crear cuenta — Vitalia" use tuteo neutro. No voseo. Clerk component strings localized via Clerk's own i18n (out of FE scope). |
| 9 | Security / Deps | PASS | No `dangerouslySetInnerHTML`, no eval, no secrets in client bundle. Clerk publishable key consumed server-side via `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` env (Clerk recipe; out of scope). |
| 10 | Tests / TDD | WARN | T-2-result.md: "no novel logic to unit-test independently". Structural verification only (tsc + ESLint + arch). Visual SC-03/SC-04 deferred to T-6.a Playwright spec. Acceptable for thin "replace placeholder with vendor component" tickets; spec § 3 SC-03/SC-04 verified via Playwright `sign-in-form.spec.ts`. |
| 11 | Domain Alignment | PASS | Clerk Next.js 16 canonical pattern; appearance API used per Clerk docs (variables block) |
| 12 | Architecture Fitness | PASS | FE-A1 ratchet preserved (no-hardcoded-colors via CSS variable refs in appearance.variables); FSD boundaries clean |
| 13 | Mirror detection | PASS | No Nicolify auth page copy; Clerk SDK direct import. Per anti-duplication.md A4. |
| 14 | Decisions honored cite | PASS | D4 (delete legacy step-{1,2,3}) cited explicitly in commit body + T-2-result.md "Decision D4" |

## Findings

### PASS notes

- **D4 honored**: legacy `app/onboarding/step-1/page.tsx`, `step-2/page.tsx`, `step-3/page.tsx` deleted via `git rm` (commit diff shows -27 / -28 / -28 LOC each). Verified post-commit: `ls vitalia/frontend/src/app/onboarding/` returns only `layout.tsx` + `wizard/`. ✅
- **Appearance tokens correctly applied**: `colorPrimary: var(--vitalia-cian-color)`, `colorTextSecondary: var(--vitalia-text-muted-color)`, `borderRadius: 0.5rem`, `fontFamily: inherit`. Bypasses FE-A1 ratchet correctly (test T-2-result.md notes initial `hsl(198 99% 49%)` hard-coded literal was caught and corrected → CSS var ref).
- **Server Component preserved**: both pages export `metadata: Metadata` (Server-only API); no `"use client"`. Clerk handles Client boundary internally.
- **Spanish neutro**: "Iniciar sesión", "Crear cuenta" — tuteo per spec § 5.

### WARN: TDD per T-2 weak by ticket design

**Category:** 10
**File:** `vitalia/frontend/src/app/(auth)/{sign-in,sign-up}/page.tsx`
**Issue:** T-2 ticket scope is "replace placeholder with `<SignIn />` / `<SignUp />`" — minimal logic. T-2-result.md justifies "no novel logic to unit-test". Structural-only verification (no unit test of page composition, e.g., snapshot test confirming `<SignIn />` is rendered + appearance prop applied).
**Fix:** Acceptable for thin pages; visual + behavior verified via Playwright `sign-in-form.spec.ts` (SC-03 + SC-04). For future: a thin Vitest snapshot (`<SignIn />` import-mock + appearance-prop assertion) would close the structural gap (~10 lines).
**Skill ref:** `.claude/rules/tdd-mandatory.md` § "Aplica: modificación existente". Not blocking per "config pura / docs / styling sin lógica" exception when reasoning applies (vendor component + appearance config).

### Minor observations

- Wrapping `<main>` is plain Tailwind utility classes — clean, no inline styles, no hex literals. ✅
- DELETE was correctly performed (git rm with paths, not `git add -A` per `.claude/rules/parallel-safety.md` M5). Verified in commit diff (5 files staged by exact name).

## Contract / UI-SPEC Compliance

- [x] SC-03: `<SignIn />` rendered (sign-in/page.tsx line 21-30)
- [x] SC-04: `<SignUp />` rendered (sign-up/page.tsx line 20-29)
- [x] No placeholder text "pendiente T-fe-3" in either file
- [x] D4 — DELETE legacy step-{1,2,3}/ (verified via FS listing)
- [x] Spanish neutro metadata titles
- [x] Appearance tokens from design system (no hex literals)

## Allowlist Movement

- FE-A1 ratchet preserved (CSS var refs accepted). No shrink/growth.

## Native-First Audit

- [x] No Docker test runs
- [x] No `git add .`
- [x] Conventional commit `feat(vitalia/frontend): T-2 ...` ✅

## Live Verification Audit

- [WARN] Live verification deferred to T-6.a (Playwright local smoke) + T-6.b (LIVE). Per chrome-devtools-verify DEPRECATION notice (skill marked unusable on Linux Mint), structural + downstream Playwright coverage is the substitute. Acceptable per project_context Step 4 + skill deprecation header.

## Downstream regression scope

| Surface modified | Downstream | Verified? |
|---|---|---|
| `vitalia/frontend/src/app/(auth)/sign-in/page.tsx` (EDIT) | None — auth page consumed only by Next.js router | YES |
| `vitalia/frontend/src/app/(auth)/sign-up/page.tsx` (EDIT) | None | YES |
| `vitalia/frontend/src/app/onboarding/step-{1,2,3}/page.tsx` (DELETE) | grep cross-codebase confirms no imports/links to these paths (legacy stubs, only placeholder text) | YES (commit dcd34d6 diff shows 0 referencing files updated) |

No cross-brand mirror, no engine edit. Scope contained.

## Verdict Math

- Categories all PASS, 1 WARN (TDD weak by ticket design, justified)
- Live-verified deferred → WARN documented, gated to T-6.a/T-6.b
- D4 honored explicitly
- Overall: **PASS** (single WARN acceptable + design-justified)
