# T-FIX-1-FE — Result

**Ticket:** T-FIX-1-FE — Keystone doctors-500 frontend clinic-id resolution + Clerk-org cleanup
**Story:** vitalia-fase2-lisa-doctores
**Brand:** vitalia
**Commit:** 99589cb2 (+ 81a32173 for useClinicId.test.tsx)
**Branch:** wip/vitalia
**Date:** 2026-06-01

## Summary

Fixed the frontend root cause of the doctors-500 bug: `useClinicId.ts` was importing and calling `useOrganization()` from `@clerk/nextjs` as a fallback for clinic_id resolution. Since Luana does NOT use Clerk Organizations (MEMORY.md::no-clerk-organizations 2026-05-20), `organization` was always `null` and `orgLoaded` was always flipping state — causing the hook to return `null` even when `user.publicMetadata.clinicId` was set and valid.

Tightened the architecture test to catch this class of bug for the entire `src/` tree going forward.

## Files Changed

| File | Change | Type |
|---|---|---|
| `src/hooks/useClinicId.ts` | Removed `useOrganization` import + org fallback block. Now reads only from `user.publicMetadata.clinicId`. | Fix |
| `src/hooks/__tests__/useClinicId.test.tsx` | 7 new unit tests (TDD RED→GREEN). Covers all cases + "never calls useOrganization" assertion. | Tests |
| `src/__tests__/architecture/test-no-clerk-organizations.test.ts` | New full-src import scan (describe block). Detects @clerk org hook imports across ALL src/ files. LEGACY_EXCLUSIONS ratchet reduced 2→1. CLERK_ORG_IMPORT_EXCLUSIONS baseline=7 (shrink-only). | Arch test |
| `src/lib/api/fetchClient.ts` | Fixed stale JSDoc comments ("Clerk org ID" → "luana-core-iam tenant ID"). No logic change. | Docs |

## TDD Sequence

1. **RED** — Tightened `test-no-clerk-organizations.test.ts` with full src/ scan. Test failed on `useClinicId.ts` (imports `useOrganization` from `@clerk/nextjs`).
2. **GREEN** — Fixed `useClinicId.ts`: removed `useOrganization` import and org fallback. Arch test passed.
3. **Unit tests** — 7 tests added covering: clinicId present, absent, empty, wrong-type, loading state, null user, and "no useOrganization" assertion.

## Quality Gates (G5)

| Gate | Result |
|---|---|
| `tsc --noEmit` | 0 errors |
| `eslint <changed files>` | 0 errors |
| `vitest run useClinicId.test.tsx` | 7/7 PASS |
| `vitest run test-no-clerk-organizations.test.ts` | 14/14 PASS |
| **Total** | **21/21 PASS** |

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite hook patterns, test setup, TDD workflow | Used `renderHook` from `@testing-library/react`, `vi.mock` for `@clerk/nextjs` — no QueryClient wrapper needed (hook doesn't use React Query) |
| `.claude/rules/tdd-mandatory.md` | RED before GREEN enforcement | Wrote arch test tightening first (RED), then fixed hook (GREEN), then added unit tests |
| `.claude/rules/frontend-fsd.md` | FSD-Lite boundaries, hook location | Hook stays in `src/hooks/` (global hook, not feature-scoped) |
| `vitalia/.claude/rules/hipaa-lite.md` | Clinic ID dual-filter requirement | `useClinicId` must return clinic_id reliably for HIPAA-lite X-Clinic-ID header |
| `MEMORY.md::no-clerk-organizations` | Constraint: NO Clerk Orgs | clinic_id comes exclusively from `user.publicMetadata.clinicId` (luana-core-iam writes this) |

## Architecture Constraint Enforced

The `useOrganization()` fallback was incorrect by design — per MEMORY.md::no-clerk-organizations (cement 2026-05-20), Luana does NOT use Clerk Organizations at any stage. `clinic_id` and `tenant_id` are luana-core-iam data, written into Clerk `user.publicMetadata` by our IAM module for read convenience. They are never sourced from Clerk org APIs.

The tightened arch test (`CLERK_ORG_IMPORT_EXCLUSIONS` ratchet, baseline=7, shrink-only) ensures this cannot regress silently.

## Arch Test Ratchet State Post-Fix

| Ratchet | Before | After | Direction |
|---|---|---|---|
| `LEGACY_EXCLUSIONS` (F1-S3 scope) | 2 files | 1 file | SHRUNK ✓ |
| `MAX_LEGACY_EXCLUSIONS` cap | 2 | 1 | SHRUNK ✓ |
| `CLERK_ORG_IMPORT_EXCLUSIONS` (NEW — full src/ scan) | n/a | 7 files (baseline) | ESTABLISHED |

## Pre-existing violations (not in scope — tracked in ratchet)

The full src/ scan found 7 additional files with Clerk org imports. These are pre-existing violations added to `CLERK_ORG_IMPORT_EXCLUSIONS` with a shrink-only ratchet cap of 7:
- `src/hooks/useTenantLocale.ts`
- `src/components/shared/phi/AuditedSection.tsx`
- `src/features/onboarding/components/WizardOnboardingLayout.tsx`
- `src/features/onboarding/hooks/use-wizard-completion.ts`
- `src/features/onboarding/hooks/use-wizard-live-preview.ts`
- `src/features/onboarding/hooks/use-wizard-onboarding-state.ts`
- `src/features/onboarding/hooks/use-wizard-slot-extraction.ts`

These are tracked for future migration — NOT in scope for this ticket.

## Note for Orchestrator (live-verify)

Per ticket NOTA: with this FE fix, `useClinicId` will now correctly return the `clinicId` from `user.publicMetadata`. However, if `dr.demo@vitalialat.com` does not have a valid clinic UUID in their `public_metadata.clinicId` (pointing to a real row in the `clinics` table), the endpoint will return 422 (better than 500, but doctors still won't load). That seed/data fix (Clerk user metadata + clinic row) is a data concern for the orchestrator live-verify phase, not this code fix.

<!-- @pm: build phase done (state: tests-passing). Commit: 99589cb2. Files: 4 (3 in this commit + 1 in 81a32173). Native ticket tests: 21/21 PASS. Awaiting orchestrator → gate-runner → auditor-frontend (independent verdict). -->
