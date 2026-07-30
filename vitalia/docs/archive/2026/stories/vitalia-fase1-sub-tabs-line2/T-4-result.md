# T-4 Result — SubTabsBar organism

**Story:** vitalia-fase1-sub-tabs-line2 (F1-S8)
**Ticket:** T-4 — SubTabsBar organism + roving tabindex + URL-derived active state + return null guard
**Date:** 2026-05-25
**State:** pushed

## Summary

Created `SubTabsBar.tsx` organism and `SubTabsBar.test.tsx` with 36 tests.

SubTabsBar renders the horizontal sub-tabs navigation bar (line 2 of shell):
- URL-derived state: `extractAgentFromPath` + `extractSubtabFromPath` from `agent-catalog.ts`
- Q5 cement: `return null` when `activeAgent === null || subtabs.length === 0`
- Q4 cement: container `min-h-[42px] bg-card border-b border-border flex items-center px-4 gap-1 overflow-x-auto`
- Roving tabindex pattern verbatim from Ribbon.tsx (F1-S7): Arrow L/R/Home/End + Enter/Space
- `aria-label="Sub-secciones {name}"` dynamic per agent (config → "Sub-secciones Configuración")
- `SubTab` keyed by `subtab.id` (stable — no array index)
- `navigateTo` guards `params?.tenantId` — null/undefined → no `router.push`

## Files Created

| File | Type | Lines |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.tsx` | Production | 130 |
| `vitalia/frontend/src/components/shared/shell-organism/SubTabsBar.test.tsx` | Test | 36 tests |

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS (0 errors) |
| `eslint` (new files) | PASS (0 errors) |
| `vitest run` (SubTabsBar.test.tsx) | PASS (36 tests, 36 passed) |
| Prettier | PASS |

## Design Decisions

- `getAriaLabel(slug)` pure function for dynamic aria-label — Config is hardcoded "Configuración" (not in AGENT_CATALOG)
- `initialFocusIdx` uses `subtabs.findIndex` for deep-link focus sync (first render starts focused at URL subtab)
- `useState(initialFocusIdx)` — React state only computes from initial value on mount; re-renders with new subtabs use the existing state (per React behavior; focus sync is via onFocus handler for user nav)
- Mateo (empty subtabs) returns null gracefully via Q5 guard
