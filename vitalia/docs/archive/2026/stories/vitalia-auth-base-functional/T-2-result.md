# T-2 Result — FE Clerk SignIn/SignUp real pages + DELETE legacy step-{1,2,3}

**Story:** vitalia-auth-base-functional
**Ticket:** T-2 — FE — Pages Clerk reales + cleanup step-{1,2,3}
**Surface:** frontend
**Brand:** vitalia
**Branch:** wip/vitalia
**Commit:** dcd34d6

## Files Modified

| File | Action | LOC delta |
|---|---|---|
| `vitalia/frontend/src/app/(auth)/sign-in/page.tsx` | EDIT | +26 / -19 |
| `vitalia/frontend/src/app/(auth)/sign-up/page.tsx` | EDIT | +26 / -19 |
| `vitalia/frontend/src/app/onboarding/step-1/page.tsx` | DELETE (git rm) | -27 |
| `vitalia/frontend/src/app/onboarding/step-2/page.tsx` | DELETE (git rm) | -28 |
| `vitalia/frontend/src/app/onboarding/step-3/page.tsx` | DELETE (git rm) | -28 |

## Implementation Summary

### SC-03 — sign-in page

`vitalia/frontend/src/app/(auth)/sign-in/page.tsx` now renders `<SignIn />` from `@clerk/nextjs` (v6.36.8) with vitalia appearance tokens:
- `colorPrimary`: `var(--vitalia-cian-color)` — hero/CTA cian (#01B2F8)
- `colorTextSecondary`: `var(--vitalia-text-muted-color)` — texto secundario (#6B7280)
- `borderRadius`: `0.5rem` — consistent with vitalia radius-md
- `fontFamily`: `inherit` — uses brand font

Wrapper `<main>` uses `bg-vitalia-bg` Tailwind token (safe, no inline hsl).

Page remains a **Server Component** (exports `metadata`, no `"use client"`) — imports `<SignIn />` which Clerk renders as a Client Component boundary internally. This is valid Next.js App Router pattern.

### SC-04 — sign-up page

`vitalia/frontend/src/app/(auth)/sign-up/page.tsx` same pattern with `<SignUp />` component. Same appearance tokens.

### DELETE legacy stubs (Decision D4)

Three legacy onboarding step directories removed per checkpoint.md Decision D4:
- "Wizard único vive en `/onboarding/wizard` (Story vitalia-slice-1-onboarding-wizard DONE 2026-05-18) — DELETE legacy `step-1/step-2/step-3/` stubs."
- All three were placeholder pages (`pendiente T-fe-3`) with no functional content.
- `git rm -r` used — clean deletion tracked in git history.

### Architecture fitness notes

The arch test `test_no_hardcoded_colors.test.ts` (FE-A1 ratchet) detects `hsl(...)` literals. Initial implementation used `hsl(198 99% 49%)` values which triggered the test. Fixed by replacing with `var(--vitalia-cian-color)` CSS variable references (defined in `globals.css` as computed values — the arch test exempts `globals.css`).

## TDD Flow

T-2 scope is replacement of placeholder text with Clerk components — no novel logic to unit-test independently. The implementation is structurally verified by:
1. TypeScript strict (component props type-checked against `@clerk/nextjs` types)
2. ESLint (component imports validated)
3. Architecture fitness tests (FE-A1 color ratchet + FSD boundaries)

Note: SC-03/SC-04 full Gherkin verification (Clerk form inputs visible in browser) requires running dev stack with Clerk keys configured. This is gated by T-5 (deploy) + T-6.a (local smoke).

## Validator Gate Outputs

### nf-fe-tsc (`npx tsc --noEmit`)
```
Exit code: 0 — 0 errors
```

### nf-fe-eslint (`npx eslint src/ --cache --max-warnings=0`)
```
Exit code: 0 — 0 errors, 0 warnings
```

### nf-fe-arch-fitness (`npx vitest run src/__tests__/architecture/`)
```
Test Files  9 passed (9)
Tests       38 passed (38)
EXIT 0

FE-A1 (no-hardcoded-colors): PASS — var(--vitalia-cian-color) reference passes ratchet
FSD boundaries: PASS
No voseo: PASS
Server-first: PASS
```

### Full vitest suite with coverage (`npx vitest run --coverage`)
```
Test Files  44 passed (44)
Tests       306 passed (306)
Coverage (v8):
  All files | % Stmts: 26.46 | % Branch: 58.59 | % Funcs: 33.33 | % Lines: 26.46
  Threshold: ≥20% all categories — PASS
EXIT 0
```

## Gherkin Coverage

Per `06-tickets.yaml::gherkin_coverage`:

| Scenario | Verification | Status |
|---|---|---|
| SC-03: Sign-in form visible — `<SignIn />` rendered, no placeholder | `page.tsx` imports + renders `<SignIn />` (tsc validates import type). FE-A1 arch test passes. Visual verification pending T-6.a (Playwright local smoke). | STRUCTURAL PASS |
| SC-04: Sign-up form visible — `<SignUp />` rendered, no placeholder | Same pattern for `<SignUp />`. | STRUCTURAL PASS |

Note: Clerk renders form inputs client-side on mount. Full visual assertion (email+password inputs visible) verified in T-6.a Playwright smoke test against running dev stack.

## Skills Consulted (Step 0 GATE)

| Skill | Invocada? | Decision |
|---|---|---|
| `frontend-expert` | ✅ yes | Server Component default — page exports `metadata`, no `"use client"` needed; Clerk `<SignIn />` is internally client-rendered, parent page stays Server. |
| `tessl__react-patterns` | ✅ yes (baseline) | No useEffect, no stale closures, no async UI needing loading state — Clerk component handles its own loading/error states internally. |
| `tessl__shadcn-ui` | ✅ yes | Clerk components are external (not Shadcn) — no recreating primitives. Tailwind `bg-vitalia-bg` applied to wrapper. |
| `tessl__tailwind` | ✅ yes | `cn()` not needed (single class). `bg-vitalia-bg` token from design system. No inline `style={{}}`. |
| `tessl__nextjs-app-router-modularization` | ✅ yes | Page is thin Server Component importing Clerk — no Server+Client mixing concern; Clerk handles boundary internally. No `<PageClient.tsx>` split needed. |
| `chrome-devtools-verify` | N/A (deprecated for Linux Mint) | Documented: live verification pending T-6.a Playwright smoke with Clerk keys. Escalated to Chris staging gate. |
| Domain skills (brand-expert, offer-expert, etc.) | Not applicable — auth pages touch no brand/offer/analytics/copilot domain. | — |

## Notes

- `--vitalia-cian-color` and `--vitalia-text-muted-color` confirmed defined in `globals.css` (computed values, not partial HSL tokens).
- `CONTEXT-BRIEF.md` `Validator pass: PENDING` noted — `Faithfulness flag: clean` — proceeded per R24 rules (no blocking flag).
- Spanish neutro confirmed: page metadata uses "Iniciar sesión" / "Crear cuenta". Clerk appearance API doesn't surface user-facing strings (Clerk handles its own localization).
- Legacy `step-{1,2,3}/` directories fully removed — no references to them in other files (verified via tsc + arch tests passing).
