# T-onboarding-6 Implementation Log

**Ticket:** T-onboarding-6 (RESUME session)
**Story:** vitalia-slice-1-onboarding-wizard
**Brand:** vitalia
**Builder:** Claude Sonnet 4.6

## Resume Context

Previous builder session (agentId aab28544abba0d0de) created the full FE structure (~4585 LOC) but hit an ESLint blocker and ran out of iterations. All files were untracked (not committed). This session resumed to:

1. Fix the ESLint issue in `WizardOnboardingLayout.tsx`
2. Run validators until GREEN
3. Fix test failures found during validation
4. Commit all files

## Skills Consulted

| Skill | Why Invoked | Decision |
|---|---|---|
| `frontend-expert` | ALWAYS - FSD-Lite patterns, runtime quality checklist | Confirmed useRef pattern for stable mutation reference is correct approach; no `eslint-disable` comments for unknown rules |
| `brand-expert` | ALWAYS for brand-studio features | Confirmed no brand-studio module touched; wizard onboarding is a separate feature |
| `offer-expert` | Domain routing check | Not applicable; no offer-studio code touched |
| `offer-type-preset-expert` | Domain routing check | Not applicable |
| `copilot-expert` | Domain routing check | Not applicable; wizard uses SSE but does not touch copilot module |
| `sales-agent-expert` | Domain routing check | Not applicable |
| `metrics-expert` | Domain routing check | Not applicable |
| `chrome-devtools-verify` | Live verification gate | DEPRECATED for Linux Mint — escalated to Chris staging gate |
| `tessl__react-patterns` | ALWAYS - error boundaries, loading/error/empty states | Applied throughout: aria-busy on loading, role="alertdialog", aria-live on streaming, stable keys |

## Issue 1 — ESLint Unknown Rule Reference

**File:** `src/features/onboarding/components/WizardOnboardingLayout.tsx`
**Line:** 281

**Root cause:** Previous builder added `// eslint-disable-next-line react-hooks/exhaustive-deps -- only on mount` but the `react-hooks` ESLint plugin is NOT registered in `vitalia/frontend/eslint.config.mjs`. When ESLint processes an `eslint-disable-next-line` comment for an unknown rule, it reports an error.

**Fix chosen:** Option C (restructure) — use `useRef` pattern:
- `startDraftMutateRef` holds current `startDraftMutation.mutate` reference (updated every render via sync effect, always stable).
- `hasInitializedRef` prevents double-firing of the init effect.
- `useEffect` deps: `[isLoaded, isSignedIn, draftId]` — all genuine dependencies, no disable comment needed.

This is the correct long-term pattern: when a function reference changes identity every render but behavior is stable, capture it in a ref rather than disabling lint.

## Issue 2 — Test: CloseSetupWarningModal stale assertion

**File:** `src/features/onboarding/__tests__/components/CloseSetupWarningModal.test.tsx:75`

**Problem:** Test expected button `"Salir de todos modos"` but the mock set `confirmButton: "Cerrar por ahora"` (matching copy.ts). Stale text from a draft version.

**Fix:** Updated assertion to `"Cerrar por ahora"` (consistent with mock + copy.ts).

## Issue 3 — Test: useWizardOnboardingState missing mock

**File:** `src/features/onboarding/__tests__/hooks/use-wizard-onboarding-state.test.ts`

**Problem:** `@clerk/nextjs` mock only exported `useAuth` but `use-wizard-onboarding-state.ts` also imports `useOrganization`. Vitest reported `[vitest] No "useOrganization" export is defined on the "@clerk/nextjs" mock`.

**Fix:** Added `useOrganization` to the mock, returning `{ organization: { id: "test-tenant-id" }, isLoaded: true }`.

## Issue 4 — Test: WizardCompletionTransition 5 stale assertions

**File:** `src/features/onboarding/__tests__/components/WizardCompletionTransition.test.tsx`

**Problems:**
1. Button lookup used `"Ir al panel"` (partial) — `getByRole` uses exact name matching, actual label is `"Ir al panel principal"`.
2. `aria-label` expected `"¡Todo listo!"` but component sets it to `copy.headline` (mocked as `"¡Tu clínica está configurada!"`).
3. `wrapper.className` looked at `main.parentElement` for `"fixed"`, but in this component the `role="main"` element IS the fixed overlay div — no parent wrapper.

**Fix:** Updated all 5 assertions to match actual component behavior.

## Validation Results

| Step | Command | Result |
|---|---|---|
| TSC | `npx tsc --noEmit` | PASS — 0 errors |
| ESLint | `npx eslint src/ --cache` | PASS — 0 errors |
| Vitest onboarding | `npx vitest run src/features/onboarding/__tests__/` | PASS — 54/54 |
| Vitest architecture | `npx vitest run src/__tests__/architecture/` | PASS — 38/38 |
| Vitest full coverage | `npx vitest run --coverage` | PASS — 299/299, 26.46% stmts |
| Voseo check | grep voseo verbs in copy.ts | PASS — 0 voseo |

## Scope Adherence

- Did NOT modify `eslint.config.mjs` (per constraint: "DO NOT modify eslint.config.mjs — out of scope")
- Did NOT install new ESLint plugins (per constraint)
- Did NOT add more `eslint-disable` comments
- Did NOT touch `core/luana-core-*` or other brands
- All files are brand-scoped to `vitalia/frontend/`

## Live Verification Note

`chrome-devtools-verify` skill is marked DEPRECATED for Linux Mint. Per the role prompt: "If unavailable, document manual verification steps in IMPL-LOG and escalate to Chris staging gate."

**Manual verification steps:**
1. `make dev-vitalia` (starts postgres + vitalia backend port 8002 + frontend port 3002)
2. Navigate to `http://localhost:3002/onboarding/wizard`
3. Verify: auth redirect works, wizard loads, chat thread initializes with welcome message
4. Verify: mode selector appears, URL input triggers extraction SSE
5. Verify: slot confirm inline appears after extraction, confirm/reject works
6. Verify: live preview panels update after slot confirmation
7. Run E2E smoke: `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/specs/vitalia/wizard-onboarding.smoke.spec.ts`
