# T-2 Result — FE lib helpers

**Story:** vitalia-fase1-routing-shell (F1-S9)
**Ticket:** T-2 — FE lib helpers: agent-catalog.ts EXTEND validators + lib/iam/api.ts NEW
**State:** developed
**Date:** 2026-05-25

---

## Deliverables

### 1. EXTEND `lib/agent-catalog.ts`

New exports appended to `vitalia/frontend/src/lib/agent-catalog.ts`:

- `isValidAgent(slug: string): slug is RibbonTabSlug` — validates agent slug is a valid ribbon tab (true for lisa/valeria/adrian/lucas/camila/config; false for mateo, empty string, unknown slugs)
- `isValidSubtab(agent: RibbonTabSlug, subtabSlug: string): boolean` — validates subtab belongs to given agent via RIBBON_SUBTABS lookup

Both consumed by `[agent]/layout.tsx` (T-4) for routing guard.

### 2. NEW `lib/iam/types.ts`

`TenantSchema` interface — camelCase mirror of `luana_core_iam.TenantSchema`:
```typescript
export interface TenantSchema { id, name, slug, role }
```

### 3. NEW `lib/iam/api.ts`

- `IamApiError` — structured error class with `code: IamErrorCode` + optional `status`
- `fetchUserTenants(_userId)` — server-safe function consuming core `GET /api/v1/iam/users/me/tenants` via Clerk `auth()`. Returns `TenantSchema[]`. Empty array is valid (no-tenants edge case SC-8).

### 4. NEW `lib/iam/audit.ts`

HIPAA-lite audit helpers (console.warn transport, Fase 2 scope: backend endpoint):
- `logCrossTenantAttempt(payload)` — action=cross_tenant_attempt
- `logNoTenantsAssigned(payload)` — action=no_tenants_assigned

Payloads contain ONLY: action + userId + attemptedTenant (where applicable) + timestamp. **No PHI.**

---

## Test Coverage

| Test file | Tests | Status |
|---|---|---|
| `src/lib/__tests__/agent-catalog.test.ts` (extended) | +~40 new | PASS |
| `src/lib/iam/__tests__/api.test.ts` (new) | 14 | PASS |
| `src/lib/iam/__tests__/audit.test.ts` (new) | 11 | PASS |
| Full vitest run | 1504 total | PASS |

---

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS (0 errors) |
| `eslint src/lib/` | PASS (0 errors, 0 warnings) |
| `vitest run src/lib/` | PASS (185 tests) |
| `vitest run --coverage` | PASS (1504 tests, coverage >20% all) |
| Architecture fitness (118 tests) | PASS |
| ESLint warning baselines | Not grown (check-file/jsdoc/react-perf stable) |

---

## Skills Consulted

| Skill | Decision |
|---|---|
| `frontend-expert` | lib/iam/ placed in lib/ (FSD lib layer); TDD RED-first per tdd-mandatory.md |
| `tessl__react-patterns` | lib/ modules are server-safe utilities — no client-side patterns needed |
| `tessl__vitest` | vi.mock + vi.spyOn + vi.stubGlobal patterns for Clerk + console + fetch mocking |
| `anti-duplication.md` | grep confirmed no existing fetchUserTenants — NEW file safe, no cross-brand mirror |
| `frontend-fsd.md` | lib/iam/ valid FSD placement (lib sub-folder) |
| `tdd-mandatory.md` | RED tests written first, all confirmed failing before implementation |
| `hipaa-lite.md` (vitalia overlay) | Audit payloads HIPAA-lite: userId + attemptedTenant + timestamp only, NO PHI |

---

## Validators Satisfied

Per `06-tickets.yaml` T-2 acceptance validators:

| Validator | Status |
|---|---|
| val-fe-tsc | PASS |
| val-fe-lint | PASS |
| val-fe-prettier | PASS |
| val-fe-vitest-unit-agent-catalog | PASS (isValidAgent + isValidSubtab gherkin coverage) |
| val-fe-vitest-unit-iam-api | PASS (happy 200, empty [], 401/403/500, AbortError, TypeError, null token) |
| val-fe-vitest-unit-audit-helper | PASS ([audit] prefix, action values, ISO timestamp, no PHI) |
| arch-fsd-imports | PASS (lib/iam/ boundary matrix compliant) |
| arch-agent-catalog-ssot | PASS (validators consume AGENT_CATALOG SSoT, no hardcoded lists) |
| arch-no-cross-brand-mirror | PASS (no fetchUserTenants in other brands) |

---

<!-- @pm: build phase done (state: tests-passing). Commit: TBD post-push. Files: 7. Native ticket tests: 65/65 PASS (isValidAgent+isValidSubtab ~40 + fetchUserTenants 14 + audit 11). Awaiting orchestrator → gate-runner → auditor-frontend (independent verdict). -->
