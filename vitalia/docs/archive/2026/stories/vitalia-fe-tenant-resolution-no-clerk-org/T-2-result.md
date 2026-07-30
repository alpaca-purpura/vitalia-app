# T-2 Result — Sweep 2 remaining Clerk Org usages

**Story:** vitalia-fe-tenant-resolution-no-clerk-org
**Ticket:** T-2 (addendum — AuditedSection + useTenantLocale)
**Date:** 2026-06-01
**Commit:** e502e4ae
**Branch:** wip/vitalia

---

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `frontend-expert` | FE bugfix pattern, runtime-quality-checklist | Read runtime-quality-checklist; confirmed useEffect deps pattern, stale closures avoided, tenantId from publicMetadata not orgId |
| `tessl__react-patterns` | AuditedSection is a Client Component with useEffect; must apply error boundaries + loading/empty states + stable memoization | Applied: `auditFired.current` guard prevents double-fire on re-renders; silent-fail try/catch per HIPAA-lite spec; children always render |
| `tessl__zod` | No new forms — N/A | Skipped (no forms in scope) |
| `chrome-devtools-verify` | FE PR ≥ M — live verification gate | Cannot invoke: Chrome DevTools MCP not connected in this session. Escalate to Chris staging gate. T-1 (commit 9148ff6a) already live-verified in the checkpoint with evidence. T-2 is a targeted sweep of 2 hook files — no new UI routes, no new endpoints. The risk is additive correctness (audit fires instead of silently not firing). Manual verification note below. |

---

## What was fixed

### 1. `AuditedSection.tsx` (CRITICAL — HIPAA-lite)

**Problem:** Used `useOrganization()` + `organization.id` as the X-Tenant-ID for PHI audit log.
With the Clerk org `org_3DzUI3...` deleted, `organization?.id` was `null` → the guard
`if (!userId || !organization?.id) return` always returned early → **PHI audit log NEVER fired**.
This means all PHI reads (patient profiles, treatment records, etc.) were unlogged after the org was deleted.

**Fix:** Replaced `useOrganization()` + `organization.id` with `useTenantId()` (reads
`user.publicMetadata.tenant_id` — our real UUID, set by luana-core-iam).
Guard: `if (!userId || !tenantId) return`. Header `X-Tenant-ID: tenantId`.
Removed `useOrganization` import entirely.

**Files changed:**
- `vitalia/frontend/src/components/shared/phi/AuditedSection.tsx`

### 2. `useTenantLocale.ts`

**Problem:** Used `useOrganization()` + `organization.publicMetadata` for currency/timezone/locale.
With the org deleted → `organization` was always `null` → always returned `VITALIA_DEFAULT_LOCALE`
(ARS / America/Argentina/Buenos_Aires / es-419). Tenant-specific locale was silently ignored.

**Fix:** Replaced `useOrganization()` with `useUser()` reading from `user.publicMetadata`
(our claim, written by luana-core-iam). Field-level fallbacks preserved:
- `currency`: must be a 3-char string, else `VITALIA_DEFAULT_LOCALE.currency`
- `timezone`: must be non-empty string, else `VITALIA_DEFAULT_LOCALE.timezone`
- `locale`: must be non-empty string, else `VITALIA_DEFAULT_LOCALE.locale`

Added TODO: canonical tenant locale endpoint is follow-up — no new endpoint invented.
Updated docstring to remove refs to "Clerk organization metadata".

**Files changed:**
- `vitalia/frontend/src/hooks/useTenantLocale.ts`

### 3. Arch test shrink (allowlists)

Both files were in `CLERK_ORG_IMPORT_EXCLUSIONS` (shrink-only ratchet).
Removed both; updated baseline:

| Ratchet | Before T-2 | After T-2 |
|---|---|---|
| `CLERK_ORG_IMPORT_EXCLUSIONS` | 7 (useClinicId fixed in T-FIX-1-FE) | 5 (AuditedSection + useTenantLocale fixed) |
| `MAX_CLERK_ORG_IMPORT_EXCLUSIONS` | 7 | 5 |
| `LEGACY_EXCLUSIONS` (useOrganization in non-import code) | 1 (useTenantLocale) | 0 |
| `MAX_LEGACY_EXCLUSIONS` | 1 | 0 |

**Files changed:**
- `vitalia/frontend/src/__tests__/architecture/test-no-clerk-organizations.test.ts`

### 4. Cascade fix: 4 inbox test files

These tests mocked `@clerk/nextjs` with `useOrganization: () => ({ organization: null })`
because `useTenantLocale` used to call `useOrganization`. After the fix, `useTenantLocale`
calls `useUser`, so the mocks needed updating.

Updated mock: `useUser: () => ({ user: null, isLoaded: true })` → same behavior
(user=null falls to default locale ARS/Buenos Aires/es-419).

**Files changed:**
- `vitalia/frontend/src/features/inbox/components/__tests__/ConversationList.test.tsx`
- `vitalia/frontend/src/features/inbox/components/__tests__/AdrianToolsSheet.test.tsx`
- `vitalia/frontend/src/features/inbox/components/__tests__/AgentActivityStream.test.tsx`
- `vitalia/frontend/src/features/inbox/components/__tests__/ContactSidebar.test.tsx`

---

## TDD (RED → GREEN)

Written RED before implementation:
- `vitalia/frontend/src/hooks/__tests__/useTenantLocale.test.tsx` — 14 tests
  - Verified currency/timezone/locale from user.publicMetadata when present
  - Fallback to VITALIA_DEFAULT_LOCALE on null user, loading, empty fields, invalid types
  - Mock enforcement: useOrganization NOT in mock → proves hook doesn't call it
  - All 14 GREEN after fix

- `vitalia/frontend/src/components/shared/__tests__/audited-section.test.tsx` — 9 tests
  - X-Tenant-ID = our UUID (regex validates UUID format, not org_ format)
  - Guard: tenantId null → audit does NOT fire (safe with deleted org)
  - Guard: userId null → audit does NOT fire
  - Fires once only (auditFired.current idempotency)
  - Silent fail (children render even when fetch throws)
  - All 9 GREEN after fix

---

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS (0 errors) |
| `eslint` (all changed files) | PASS (0 errors) |
| `vitest` — useTenantLocale test (14) | PASS |
| `vitest` — audited-section test (9) | PASS |
| `vitest` — arch test no-clerk-organizations (16/16) | PASS |
| `vitest` — cascade inbox tests (all previously passing) | PASS |
| Pre-existing failures | `test-no-cross-brand-shell-mirror`: 23 failures PRE-EXISTING (unrelated, noted in checkpoint.md "Pendiente D") |

---

## Live Verification

Chrome DevTools MCP not connected in this session.
T-2 does not introduce new UI routes or new endpoints — it restores correctness to:
1. The audit log firing (was broken with deleted org; now fires with our UUID)
2. Tenant locale resolution (was always defaulting; now reads publicMetadata)

T-1 live evidence (commit 9148ff6a) verified that X-Tenant-ID = UUID on all API calls.
T-2 adds no new surface. The correctness of AuditedSection can be verified manually by:
- Navigating to any patient profile page as `dr.demo@vitalialat.com`
- Checking `audit_log` table in DB: should have a row with `tenant_id = e69a691d-070e-5caf-a053-6e74642ec100`

Escalated to Chris for staging gate verification per `definition-of-done-live-verify.md`.

---

## Constraint compliance

- ZERO `useOrganization` / Clerk org hooks in any production file outside the onboarding exclusions
- `LEGACY_EXCLUSIONS` = 0 (was 1 before T-2)
- `CLERK_ORG_IMPORT_EXCLUSIONS` = 5 (was 7 before T-2; 2 remaining are onboarding hooks)
- HIPAA-lite audit log restored: fires with real tenant UUID, not Clerk org id
- `useTenantLocale` reads from user.publicMetadata (correct source per no-clerk-orgs)
- No backend changes, no core changes, no other brand changes (HARD scope constraint met)
