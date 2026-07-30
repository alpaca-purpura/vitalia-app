<!-- voseo-allowed: internal result document -->
# T-4 Result — F1-S9 vitalia-fase1-routing-shell

**Ticket:** T-4 — FE routing pages (5 NEW + 2 MODIFY + 1 DELETE catchall)
**Brand:** vitalia
**Date:** 2026-05-25
**State:** tests-passing

---

## Summary

T-4 implemented the core routing pages for `app/[tenantId]/(shell-organism)/`:

1. **MODIFIED** `(shell-organism)/page.tsx` — redirect changed from `lisa/marca` → `valeria/agenda` (Chris dictum Q1).
2. **CREATED** `(shell-organism)/not-found.tsx` — outer 404 (invalid agent slug). Server Component. Full viewport, no chrome. Spanish neutro microcopy verbatim per spec.
3. **CREATED** `[agent]/layout.tsx` — validates agent slug via `isValidAgent()`, calls `notFound()` if invalid. Server Component.
4. **CREATED** `[agent]/page.tsx` — redirects to agent's defaultSubtab (handles 'config' specially). Server Component.
5. **CREATED** `[agent]/not-found.tsx` — inner 404 (invalid subtab within valid agent). Client Component (justified: needs `useParams()`). Contextual label from agent catalog.
6. **CREATED** `[agent]/[subtab]/page.tsx` — validates both agent + subtab; renders F1-S10 placeholder if valid. Server Component.
7. **DELETED** `[...slug]/page.tsx` — F1-S7 stub, obsolete post-F1-S9.
8. **CREATED** arch test `test-no-dashboard-route-group.test.ts` — 2 expected RED (T-5 cleans them), 1 GREEN.

---

## Files Produced

### New (7 source + 4 test + 1 arch test)

| Path | Type |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/not-found.tsx` | Server Component |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/not-found.test.tsx` | Unit test (9 cases) |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/layout.tsx` | Server Component |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/layout.test.tsx` | Unit test (7 cases) |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/page.tsx` | Server Component |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/page.test.tsx` | Unit test (8 cases) |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/not-found.tsx` | Client Component |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx` | Server Component |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.test.tsx` | Unit test (11 cases) |
| `vitalia/frontend/src/__tests__/architecture/test-no-dashboard-route-group.test.ts` | Arch test |

### Modified

| Path | Change |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/page.tsx` | redirect target `valeria/agenda` |

### Deleted

| Path | Reason |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/[...slug]/page.tsx` | F1-S7 stub obsolete |

---

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS — 0 errors |
| `eslint src/ --cache` | PASS — 0 errors, 0 warnings added |
| `vitest run` | 1550 PASS / 2 expected RED (arch test T-5 scope) |
| Coverage thresholds | Not applicable (new pages in `src/app/`, not in coverage paths) |

---

## Arch Test Status

The 2 RED tests in `test-no-dashboard-route-group.test.ts` are **intentionally RED** at T-4 per spec:
- `app/(dashboard)/ MUST NOT exist` — RED because (dashboard) still exists, GREEN after T-5
- `app/(app)/ MUST NOT exist` — RED because (app) still exists, GREEN after T-5
- `app/[tenantId]/(shell-organism)/ MUST exist` — GREEN (created by F1-S4 + this ticket)

This is documented in `04-validators.yaml test_construction_plan` line 4.

---

## Notes for T-5

T-5 (legacy cleanup) must:
- `rm -rf vitalia/frontend/src/app/(dashboard)/`
- `rm -rf vitalia/frontend/src/app/(app)/`
- After deletion, `test-no-dashboard-route-group.test.ts` will turn GREEN (3/3)
