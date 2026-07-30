# T-3 Result — SubTab molécula

**Story:** vitalia-fase1-sub-tabs-line2 (F1-S8)
**Ticket:** T-3 — SubTab molécula button + forwardRef + active/inactive states + exceptions
**Date:** 2026-05-25
**State:** pushed

## Summary

Created `SubTab.tsx` molécula and `SubTab.test.tsx` with 34 tests.

SubTab renders a single tab button in the horizontal sub-tabs bar:
- `forwardRef<HTMLButtonElement, SubTabProps>` pattern (verbatim from RibbonTab.tsx reference)
- `role="tab"` + `aria-selected` + `data-testid="sub-tab-{id}"` + `data-active`
- Emoji `aria-hidden="true"` (decorative) + visible label span
- Active state: `bg-agent-{slug}-soft` + `agentTextClassSubTab(color)` + `font-semibold`
- Inactive state: `text-muted-foreground` + `font-medium` + `hover:bg-muted hover:text-foreground`
- Lucas exception (D18): active → `text-foreground` (not `text-agent-lucas`)
- Config exception (D19): active → `bg-muted text-foreground` (not agent color)
- Roving tabindex via `tabIndex: 0 | -1` prop
- Focus-visible ring only (no plain `focus:` classes)
- `whitespace-nowrap` on button (HARD — label NO wrap per Q4 cement)

## Files Created

| File | Type | Lines |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/SubTab.tsx` | Production | 95 |
| `vitalia/frontend/src/components/shared/shell-organism/SubTab.test.tsx` | Test | 34 tests |

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS (0 errors) |
| `eslint` (new files) | PASS (0 errors) |
| `vitest run` (SubTab.test.tsx) | PASS (34 tests, 34 passed) |
| Prettier | PASS |

## Design Decisions

- `isConfig` flag isolates Config exception branch cleanly without adding to agentBgSoftClass
- `Exclude<RibbonTabSlug, "config">` cast for agentBgSoftClass (accepts AgentSlug, not RibbonTabSlug)
- Active hover preserves agent tint (no competing `hover:bg-muted` in active branch — Q16 paridad F1-S7)
- `transition-all` (not `transition-colors`) for smooth opacity transitions on dark/light toggle
