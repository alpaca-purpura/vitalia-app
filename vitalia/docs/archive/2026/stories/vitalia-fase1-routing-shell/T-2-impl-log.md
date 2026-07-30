# T-2 Implementation Log — FE lib helpers

**Story:** vitalia-fase1-routing-shell (F1-S9)
**Ticket:** T-2 — FE lib helpers: agent-catalog.ts EXTEND validators + lib/iam/api.ts NEW
**Date:** 2026-05-25
**Branch:** wip/vitalia

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `frontend-expert` | Always-on: FSD-Lite boundary matrix, ESLint config, Vitest patterns | lib/iam/ placed in `lib/` (not features/) per FSD lib classification; TDD RED-first per tdd-mandatory.md |
| `tessl__react-patterns` | Always-on: error boundaries, loading states, accessible markup, stable keys, memoization | lib/ modules are server-safe utilities, not React components — no client-side patterns needed |
| `tessl__vitest` | New Vitest test files for iam/api + iam/audit + agent-catalog validators | vi.mock for @clerk/nextjs/server before import; vi.spyOn for console.warn; vi.stubGlobal for fetch |
| `anti-duplication.md` | fetchUserTenants consumes core endpoint — must verify no cross-brand mirror | grep confirmed: zero existing `fetchUserTenants` or `me/tenants` in vitalia/frontend → NEW file safe, no mirror |
| `frontend-fsd.md` | FSD-Lite boundary check for lib/ placement | lib/iam/ is a sub-folder of lib/ — valid FSD placement (lib → util, not feature) |
| `tdd-mandatory.md` | RED-first mandatory | Tests written first, confirmed failing, then implementation made them GREEN |
| `hipaa-lite.md` | vitalia-specific HIPAA-lite compliance for audit payloads | Audit payload: userId + attemptedTenant + timestamp ONLY — NO PHI fields. IamApiError includes no patient data |

---

## Files Modified / Created

| File | Action | Lines |
|---|---|---|
| `vitalia/frontend/src/lib/agent-catalog.ts` | EXTEND | +25 lines (isValidAgent + isValidSubtab) |
| `vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts` | EXTEND | +~130 lines (isValidAgent + isValidSubtab test suites) |
| `vitalia/frontend/src/lib/iam/types.ts` | NEW | 26 lines |
| `vitalia/frontend/src/lib/iam/api.ts` | NEW | 128 lines |
| `vitalia/frontend/src/lib/iam/audit.ts` | NEW | 67 lines |
| `vitalia/frontend/src/lib/iam/__tests__/api.test.ts` | NEW | 311 lines |
| `vitalia/frontend/src/lib/iam/__tests__/audit.test.ts` | NEW | ~130 lines |

---

## TDD Flow

### RED phase
Tests written first, all failing as expected:
- `isValidAgent` tests: function not yet exported → `isValidAgent is not a function`
- `isValidSubtab` tests: function not yet exported → `isValidSubtab is not a function`
- `fetchUserTenants` tests: `lib/iam/api.ts` not yet created → module not found
- `IamApiError` tests: class not yet created → module not found
- `logCrossTenantAttempt` tests: `lib/iam/audit.ts` not yet created → module not found

### GREEN phase
Implementation created, all tests passing:
- `isValidAgent(slug)`: explicit `mateo` guard (returns false) before AGENT_CATALOG lookup; explicit `config` guard (returns true)
- `isValidSubtab(agent, subtabSlug)`: checks RIBBON_SUBTABS[agent] for non-empty + subtab id match
- `fetchUserTenants(_userId)`: server-safe via `auth()` from @clerk/nextjs/server; IamApiError hierarchy
- `logCrossTenantAttempt`, `logNoTenantsAssigned`: console.warn with structured JSON, HIPAA-lite clean

---

## Key Design Decisions

### isValidAgent mateo exclusion
mateo is in `AgentSlug` union and `AGENT_CATALOG` map but is transversal (excluded from `AGENT_RIBBON_ORDER`). Naive `slug in AGENT_CATALOG` would return true for mateo. Solution: explicit `if (slug === "mateo") return false` guard before catalog check. This satisfies SC-2 gherkin (mateo → false) without removing mateo from AGENT_CATALOG (which is correct — mateo exists, just not as a ribbon tab).

### config in RibbonTabSlug
`RibbonTabSlug = AgentSlug | "config"`. The `isValidAgent` function accepts "config" (valid ribbon tab) returning true. `RIBBON_SUBTABS.config` has 3 subtabs: cuenta, conexiones, avanzado.

### fetchUserTenants server-safety
Uses `import { auth } from "@clerk/nextjs/server"` — NOT React hooks. This makes the function callable only from Server Components or Server Actions. The `_userId` parameter is received for logging context but NOT sent to the API (spec design note: the API uses the Clerk JWT to identify the user server-side).

### Error code mapping
- null token → `unauthorized` (no status)
- 401 → `unauthorized` (status: 401)
- 403 → `forbidden` (status: 403)
- AbortError / TypeError → `network_failure` (no status — network-level failure)
- Other non-2xx → `unknown` (status: N)

### Double-await test bug fixed
Initial test for 401 called `fetchUserTenants` twice (once for `rejects.toThrow` + once for `rejects.toMatchObject`). The `mockResolvedValueOnce` was consumed after first call, second call got undefined → `TypeError: Cannot read properties of undefined`. Fixed: single `.catch()` pattern with `mockResolvedValue` (not Once).

### HIPAA-lite audit payloads
Audit payloads contain ONLY: `action`, `userId`, `attemptedTenant`, `timestamp`. NO PHI fields (no patient name, no diagnosis, no medical data). `userId` is a Clerk opaque ID — not PII in isolation per HIPAA-lite. Transport: `console.warn` (F1-S9). Fase 2 scope: replace with POST to `/api/v1/audit/iam-events`.

---

## Quality Gate Results

| Gate | Status | Detail |
|---|---|---|
| `tsc --noEmit` | PASS | 0 errors, strict mode |
| `eslint src/lib/agent-catalog.ts src/lib/iam/ --cache` | PASS | 0 warnings, 0 errors |
| `vitest run src/lib/` | PASS | 185 tests, 6 test files, all PASS |
| `vitest run --coverage` | PASS | 1504 tests, 142 test files, coverage >20% all categories |
| Architecture fitness | PASS | 118 tests, 18 files, all PASS |
| Warning baselines | PASS | No new warnings vs baselines (check-file/jsdoc/react-perf) |
