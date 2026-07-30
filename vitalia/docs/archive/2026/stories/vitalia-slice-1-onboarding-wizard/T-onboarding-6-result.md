# T-onboarding-6 Result — Wizard Onboarding FE Feature

**Ticket:** T-onboarding-6
**Story:** vitalia-slice-1-onboarding-wizard
**Brand:** vitalia
**Surface:** frontend
**State:** developed

## Summary

Full React frontend implementation for the Wizard Onboarding feature. 9 components + 6 hooks + API layer + types + E2E smoke spec.

## Files Created / Modified

### Feature module — src/features/onboarding/

| File | Type | Description |
|---|---|---|
| `components/WizardOnboardingLayout.tsx` | Component (Client) | Root layout orchestrating all wizard sub-components. 50/50 split (chat left, preview right). |
| `components/WizardChatThread.tsx` | Component (Client) | Chat message thread with input composer, typing indicator, skip/back buttons. |
| `components/SlotTrackerSticky.tsx` | Component (Client) | Sticky sidebar slot progress tracker. |
| `components/SlotConfirmInline.tsx` | Component (Client) | Inline confirm/reject/edit card for extracted slots. |
| `components/ModeSelector.tsx` | Component (Client) | Mode picker (URL / Document / Audio). |
| `components/LiveWhatsAppPreview.tsx` | Component (Client) | Live WhatsApp message simulation preview. |
| `components/LiveLandingSnippetPreview.tsx` | Component (Client) | Live landing page snippet preview. |
| `components/CloseSetupWarningModal.tsx` | Component (Client) | Alert dialog confirming close with progress save message. |
| `components/WizardCompletionTransition.tsx` | Component (Client) | Fullscreen morph 400ms completion transition. |
| `hooks/use-wizard-url-state.ts` | Hook | Step + mode + draftId from URL search params. |
| `hooks/use-wizard-onboarding-state.ts` | Hook | React Query fetch of draft state (GET /drafts/{draftId}). |
| `hooks/use-wizard-sse-stream.ts` | Hook | SSE connection to wizard event stream with reconnect. |
| `hooks/use-wizard-slot-extraction.ts` | Hook | useMutation for URL/doc/text extraction. |
| `hooks/use-wizard-live-preview.ts` | Hook | Debounced live preview simulation query. |
| `hooks/use-wizard-completion.ts` | Hook | useMutation for finalizing onboarding. |
| `api/wizard-onboarding-api.ts` | API | All fetchClient calls for wizard endpoints. |
| `types/wizard-onboarding.types.ts` | Types | All TypeScript interfaces + DTOs (camelCase mirror of Pydantic). |
| `config/copy.ts` | Config | Spanish neutro LatAm microcopy SSoT (no voseo). |
| `index.ts` | Barrel | Public API exports (no default exports). |

### Tests — src/features/onboarding/__tests__/

| File | Tests |
|---|---|
| `hooks/use-wizard-url-state.test.ts` | 5 passing |
| `hooks/use-wizard-onboarding-state.test.ts` | 5 passing |
| `hooks/use-wizard-sse-stream.test.ts` | 7 passing |
| `components/CloseSetupWarningModal.test.tsx` | 11 passing |
| `components/ModeSelector.test.tsx` | 8 passing |
| `components/SlotTrackerSticky.test.tsx` | 8 passing |
| `components/WizardCompletionTransition.test.tsx` | 10 passing |

**Total onboarding tests: 54 / 54 PASS**

### Page — src/app/onboarding/wizard/

| File | Type |
|---|---|
| `page.tsx` | Next.js Server Component page (renders WizardOnboardingLayout) |

### E2E

| File | Type |
|---|---|
| `e2e/pages/wizard-onboarding.page.ts` | Playwright POM |
| `e2e/specs/vitalia/wizard-onboarding.smoke.spec.ts` | Smoke spec (runs against port 3002 — auditor executes) |

## Quality Gates

| Gate | Status | Notes |
|---|---|---|
| `tsc --noEmit` | PASS | 0 errors strict mode |
| ESLint | PASS | 0 errors |
| Vitest coverage | PASS | 299/299 tests, 26.46% statements (> 20% threshold) |
| Architecture fitness | PASS | 38/38 tests |
| Voseo check | PASS | No voseo verbs in copy.ts |
| FSD boundaries | PASS | No cross-feature imports |

## Fix Applied This Session (Resume)

**Problem:** Previous builder created `// eslint-disable-next-line react-hooks/exhaustive-deps` comment in `WizardOnboardingLayout.tsx` line 281. The `react-hooks` ESLint plugin is not registered in `eslint.config.mjs`, so this comment caused an ESLint error about an unknown rule.

**Fix (Option C — restructure):**
- Added `useRef` for `startDraftMutation.mutate` (stable ref, always current) so the `useEffect` deps array doesn't need the mutation object.
- Added `hasInitializedRef` guard to prevent double-firing.
- The `useEffect` now has proper deps `[isLoaded, isSignedIn, draftId]` with no bogus disable comment.

**Additional test fixes:**
- `CloseSetupWarningModal.test.tsx` line 75: stale assertion `"Salir de todos modos"` → corrected to `"Cerrar por ahora"` (matches mock + component).
- `use-wizard-onboarding-state.test.ts`: `@clerk/nextjs` mock was missing `useOrganization` → added.
- `WizardCompletionTransition.test.tsx`: 5 stale assertions fixed (button label partial → exact, `aria-label` "¡Todo listo!" → actual copy headline, `wrapper.className` → `main.className`).

## Live Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (designed for WSL2+Windows bridge). Live verification escalated to Chris staging gate (port 3002 via `make dev-vitalia`). E2E smoke spec `wizard-onboarding.smoke.spec.ts` exists for auditor to run against the dev stack.
