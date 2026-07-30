# T-3 Result — Ribbon organism

**Story:** vitalia-fase1-ribbon-6-tabs (F1-S7)
**Ticket:** T-3 — Ribbon organism root + roving tabindex WAI-ARIA + URL-derived active + navigateTo
**State:** pushed
**Commit SHA:** e073fe48
**Date:** 2026-05-25

## Files Produced

| Action | Path |
|---|---|
| NEW | `vitalia/frontend/src/components/shared/shell-organism/Ribbon.tsx` |
| NEW | `vitalia/frontend/src/components/shared/shell-organism/Ribbon.test.tsx` |
| MODIFY | `vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/06-tickets.yaml` (T-3 state: pushed) |

## Validator Gates

| Gate | Result | Notes |
|---|---|---|
| `tsc --noEmit` (val-fe-tsc) | PASS | 0 errors |
| `eslint src/` (val-fe-lint) | PASS | 0 errors, 0 new warnings |
| `vitest run --coverage` (val-fe-vitest-unit) | PASS | 136/136 files, 1311/1311 tests |
| Architecture fitness (val-fe-arch-fsd + val-fe-arch-server-first) | PASS | All 20 arch tests green |
| val-fe-arch-no-hex | PASS | No hex literals in Ribbon.tsx |
| val-fe-arch-no-voseo | PASS | All strings Spanish neutro LatAm |
| val-fe-arch-no-vt | PASS | No .vt-* classes |

## Native Ticket Tests

**39/39 PASS** (Ribbon.test.tsx)

| Gherkin scenario | Tests | Status |
|---|---|---|
| SC-1 render structure | 5 | PASS |
| SC-1 click navigation | 6 | PASS |
| SC-2 URL deep link active state | 4 | PASS |
| SC-3 ConfigTab navigation | 2 | PASS |
| SC-4 invalid slug no active | 2 | PASS |
| SC-7 roving tabindex keyboard | 15 | PASS |
| defensive tenantId guard | 3 | PASS |
| focus management | 2 | PASS |

## Component Contract

```typescript
// Ribbon.tsx — named export, "use client" first line
export function Ribbon(): React.JSX.Element

// Props: none (self-contained via hooks)
// Reads: usePathname() → URL-derived active state
// Reads: useParams<{tenantId}>() → tenant isolation
// Reads: useRouter() → navigation
// State: focusedIdx (roving tabindex)
// Refs: tabRefs array → programmatic focus
```

## Key Architecture Decisions

1. **Keyboard handler on `<nav>` element** — events bubble from RibbonTab/ConfigTab children. No need to extend T-2 prop interfaces.
2. **URL-derived active state** — `extractAgentFromPath(usePathname())` is single source of truth. No duplicated active state.
3. **`navigateTo` guard** — early return if `!params?.tenantId`. Tenant isolation preserved.
4. **Circular wrap** — `((idx % total) + total) % total` handles negative indices safely.
5. **`"use client"` first line** — required by arch fitness test `test_server_first.test.ts`.
6. **No `<TooltipProvider>`** — ConfigTab's Tooltip auto-wraps provider internally.

## Notes for T-4 (AppPanelSlot integration + arch tests)

- `test_server_first.test.ts` allowlist must be extended to include `Ribbon.tsx`
- `test-no-cross-brand-shell-mirror.test.ts` must add: Ribbon, RibbonTab, ConfigTab, extractAgentFromPath, AGENT_RIBBON_ORDER
- `AppPanelSlot.tsx` must swap skeleton ribbon circles for `<Ribbon />`
- Integration smoke: `data-testid="ribbon"` on the `<nav>` is the integration handle
- `test-ribbon-no-shadcn-tabs.test.ts` (NEW in T-4) verifies no `@/components/ui/tabs` import

## Live Verification

`chrome-devtools-verify` skill is marked DEPRECATED for Linux Mint (2026-05-15). Manual verification escalated to Chris staging gate — full E2E covered in T-5 (Playwright specs + visual goldens + axe).
