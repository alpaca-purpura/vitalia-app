<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review: FE Tenant Resolution — no Clerk Org (T-1, bugfix)

**Date:** 2026-06-01
**Story:** vitalia-fe-tenant-resolution-no-clerk-org · type bugfix (ADR-011)
**Commits:** 3ded799f (refactor, 93 files) + 9148ff6a (live-verify spec) + 79e27a3d (T-1-result.md)
**Files Reviewed:** 93 (all under `vitalia/frontend/src/` + e2e)
**Domains touched:** iam (tenant resolution), cross-feature data layer (crm-shared, fidelizacion, inbox, marketing, lisa)
**Skills consulted:** frontend-expert, tessl__react-patterns, tessl__vitest (forms n/a — no new forms)
**Live-verified:** YES — `systemic-live-check.spec.ts` (authenticated, real stack, no mocks; X-Tenant-ID=UUID, API_5XX=[], doctors 200)
**Verdict:** **APPROVED** (WARN attached — pre-existing same-class debt outside scope, see WARN-1/WARN-2)

## /test-frontend Gate Status (auditor-run; no gate-output.json found → ran directly)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit | PASS | 0 errors strict |
| ESLint (60+ rules) | PASS | 0 errors |
| Arch: test-no-clerk-organizations | PASS | 16/16 (tightened, real) |
| Vitest useTenantId + useCurrentUser + lisa | PASS | 82/82 |
| Vitest inbox+marketing+fidelizacion+crm-shared | PASS | 361/361 |
| Vitest hooks + shared/phi (downstream consumers) | PASS | 41/41 |
| Pre-existing cross-brand-mirror | 23 FAIL | NOT touched by commit; Pendiente D (nicolify/comunify/lupulo bootstrap). NOT a blocker. |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | hook in src/hooks/, mirror of useClinicId; no cross-feature deep imports |
| 2 | Server/Client | PASS | "use client" leaf hook, useUser() direct, no useEffect-for-data |
| 3 | React Patterns | PASS | stable null returns; no conditional hooks; deps n/a |
| 4 | Code Quality | PASS | tsc/eslint 0; minor cosmetic spacing (`getToken}`, `tenantId, method`) — prettier-passed |
| 5 | Accessibility | N/A | no UI markup changed |
| 6 | Forms | N/A | no forms touched |
| 7 | Multitenancy | PASS | fix IMPROVES isolation — X-Tenant-ID now correct UUID from our IAM, not Clerk org |
| 8 | Master Data / Spanish | PASS | guard messages unchanged; no new user-facing strings |
| 9 | Security / Deps | PASS | no eval/dangerouslySetInnerHTML; no secrets |
| 10 | Tests / TDD | PASS | arch test RED(35)→GREEN(0) documented; no fake-green (see Fake-Green Audit) |
| 11 | Domain Alignment | PASS | honors [[no-clerk-organizations]] invariant for orgId vector |
| 12 | Arch Fitness | PASS | arch test real + tightened; ORGID ratchet cap 0; import ratchet shrunk 8→7 (useClinicId fixed) |
| 13 | Mirror detection | PASS | useTenantId is intentional in-brand mirror of useClinicId, documented, no cross-brand mirror |
| 14 | Decisions honored cite | N/A | no `decisions_applicable` field in checkpoint |
| 15 | Connectivity | PASS | hook consumed by 33+ files; not an island |
| 16 | Visual fidelity | N/A | systemic data-layer bugfix, no visual surface |

## Focus checklist (per prompt)

1. **useTenantId correct + zero Clerk org?** PASS. Uses only `useUser()`; reads `user.publicMetadata.tenant_id`; never `orgId`/`useOrganization`. Exact mirror of `useClinicId.ts`.
2. **33 replacements correct?** PASS (sampled staff.ts, use-pause-patient.ts, use-stage-detail.ts). `orgId` removed from `useAuth()` destructure; `useTenantId()` added; guards `if(!token||!orgId)`→`if(!token||!tenantId)`; `tenantId: orgId`→`tenantId`. No orphan orgId.
3. **Tests migrated without weakening?** PASS. PHI header asserts changed `"org-test-tenant"`→`"mock-tenant-id"` (concrete `.toBe`, not loosened). No removed asserts, no `expect(...||true)`, no `.skip`/`.only`, no threshold drops. Leftover `tenant_id: "org-test-tenant"` are mock-response fixture data (not request asserts). Dead `orgId:` mock fields harmless. See Fake-Green Audit.
4. **Arch test tightening real?** PASS. `ORGID_USAGE_EXCLUSIONS` scan (cap 0) genuinely fails if any prod file uses `orgId`; T-1 set is empty. Not a stub.
5. **`grep "tenantId: orgId" src/`** → 0 real uses (only arch-test string literals). PASS.
6. **Scope vitalia/frontend only?** PASS. No core/, no other brands, no backend.

## Fake-Green Audit (per T-HARNESS lesson)

No fake-green detected:
- Arch test `ORGID_USAGE_EXCLUSIONS` empty, cap 0, full-src scan — would fail on any real regression.
- useTenantId.test.tsx has strong negative asserts (`.not.toMatch(/^org_/)`, `not.toBe(orgStyleId)`).
- PHI X-Tenant-ID asserts (use-transcribe-audio, use-attach-media) assert concrete `"mock-tenant-id"`.
- Mock `useTenantId: () => "mock-tenant-id"` is a legitimate unit-isolation mock (hook tested directly in useTenantId.test.tsx); does not mask the prod path.
- Live-verify spec is authenticated against real stack, captures actual sent header + status, asserts zero 5xx — honest (not GET-200 sham).

## Downstream regression scope (auditor-downstream-regression.md)

| Surface changed | Downstream consumers | Test status |
|---|---|---|
| hooks/useTenantId.ts (NEW global) | 33 api hooks + useCurrentUser | GREEN (all feature suites) |
| hooks/useCurrentUser.ts (cross-feature) | usePiiRoleGate, RequireRole, fidelizacion/marketing components | GREEN (hooks + shared/phi 41/41) |
| crm-shared/api (shared consumer) | inbox, conversations | GREEN (361/361 feature) |

Full per-consumer vitest GREEN → downstream scope satisfied. No regression.

## WARN-1 (out of declared scope, PRE-EXISTING, tracked) — AuditedSection.tsx still sends Clerk org id as X-Tenant-ID to a PHI endpoint
- **Category:** 7/11 (Multitenancy / domain invariant)
- **File:** `src/components/shared/phi/AuditedSection.tsx:53,62,71`
- **Issue:** Still uses `useOrganization()` and sends `"X-Tenant-ID": organization.id` (`org_xxx`, non-UUID) to `POST /api/v1/vitalia/audit-log`. This is the SAME bug-class the story claims to systemically resolve. Verified PRE-EXISTING (identical in 3ded799f~1) and NOT touched by this commit; captured in `CLERK_ORG_IMPORT_EXCLUSIONS` ratchet (cap 7, shrink-only). Now that the Clerk org was deleted (live-verify), `organization?.id` is null → the `if (!userId || !organization?.id) return;` guard makes the **HIPAA-lite audit log silently never fire** (audit gap).
- **Why not FAIL:** story scope (checkpoint + observed-bug) was explicitly the `tenantId: orgId` 500 vector. AuditedSection is tracked debt in the import ratchet; this commit shrunk that ratchet (fixed useClinicId), did not regress it.
- **Recommended follow-up:** migrate AuditedSection to `useTenantId()` + `useClinicId()` in a dedicated ticket BEFORE relying on PHI audit logs in prod (HIPAA-lite obligation per hipaa-lite.md § Audit log).

## WARN-2 (out of scope, PRE-EXISTING, tracked) — useTenantLocale.ts reads from deleted Clerk org
- **Category:** 8 (Master Data)
- **File:** `src/hooks/useTenantLocale.ts:19,41`
- **Issue:** Resolves currency/timezone from `useOrganization().publicMetadata`. With the Clerk org deleted, always returns hardcoded default `ARS / America/Argentina/Buenos_Aires` — incorrect for the MX tenant (Sanaré MX). Pre-existing, in import ratchet (cap 7).
- **Recommended follow-up:** migrate locale source to tenant store / GET /me or publicMetadata; otherwise non-AR tenants get wrong currency/timezone.

## Allowlist / Baseline Movement
- `CLERK_ORG_IMPORT_EXCLUSIONS` ratchet **shrunk** 8→7 (useClinicId.ts fixed). Cap honored. ✅
- `ORGID_USAGE_EXCLUSIONS` = 0 (target met). ✅
- LEGACY_EXCLUSIONS shrunk 2→1. ✅
- No allowlist grew.

## Native-First Audit
- No docker exec for tsc/eslint/vitest in commits. ✅
- Live-verify spec uses authenticated Playwright fixture (native), not `make e2e`. ✅
- Commits staged by pathspec (no `git add .`). ✅

## Live Verification Audit
- User-reachable change → live-verify present + honest (authenticated, real stack, header+status captured, zero-5xx assert). Evidence in checkpoint `dev_app_verified.evidence` (X-Tenant-ID UUID, API_5XX=[], doctors 500→200, Clerk org deleted). ✅

## Verdict Math
- Cat 1/2/3/7/11/12/14 → all PASS/N/A → no FAIL trigger.
- No allowlist/baseline grew without justification (ratchet shrunk).
- No /test-frontend blocker FAIL (tsc/eslint/vitest GREEN; 23 mirror failures pre-existing, file untouched).
- Arch fitness GREEN.
- Downstream regression GREEN.
- No fake-green.
- WARN-1 + WARN-2 are PRE-EXISTING, out-of-declared-scope, tracked in shrink-only ratchet → do not block this bugfix; flagged as mandatory follow-up.
- **Overall: APPROVED** with 2 tracked WARNs for follow-up (AuditedSection PHI audit + useTenantLocale).
