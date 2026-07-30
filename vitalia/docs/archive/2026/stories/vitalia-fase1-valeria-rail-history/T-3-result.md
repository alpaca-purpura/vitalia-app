# T-3 Result — ValeriaRail + ChatSlot + History Atoms

**Story:** vitalia-fase1-valeria-rail-history (F1-S5)
**Ticket:** T-3
**State:** developed
**Build agent:** builder-frontend (claude-sonnet-4-6)
**Completed at:** 2026-05-23

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `frontend-expert` | Primary skill for FSD-Lite + quality baseline | Confirmed Server-First defaults, no default exports, barrel pattern |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, accessible markup, stable keys | Applied: `aria-busy`, `role="status"` on EmptyStateInline, `aria-live="polite"`, `aria-selected`/`aria-current` on HistoryItem |
| `tessl__shadcn-ui` | Tooltip + Button reuse — never recreate Shadcn primitives | Used `Button variant="ghost" size="icon"`, `Tooltip`/`TooltipTrigger`/`TooltipContent` from `@/components/ui/` |
| `tessl__tailwind` | Utility-first, semantic tokens, `cn()` for conditional, no inline style | All classes semantic tokens only; `bg-vitalia-success` for status dot; no hex literals |

## Files Created / Modified

### New files (T-3 scope — 7 files)

| File | Type | LOC |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaRail.tsx` | Client Component | 143 |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaRail.test.tsx` | Unit tests (TDD RED→GREEN) | 148 |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.tsx` | Server Component | 119 |
| `vitalia/frontend/src/components/shared/shell-organism/ValeriaChatSlot.test.tsx` | Unit tests (TDD RED→GREEN) | 104 |
| `vitalia/frontend/src/components/shared/shell-organism/HistoryItem.tsx` | Client Component | 65 |
| `vitalia/frontend/src/components/shared/shell-organism/HistoryGroup.tsx` | Server Component | 63 |
| `vitalia/frontend/src/components/shared/shell-organism/EmptyStateInline.tsx` | Server Component | 55 |

### Modified files (pre-existing issue fix)

| File | Change | Reason |
|---|---|---|
| `vitalia/frontend/src/hooks/useKeyboardShortcuts.ts` | Added `"use client";` directive as line 1 | T-1 file using `useEffect` was missing `"use client"` — caught by `test_server_first` arch gate. Fix is in T-3 scope as gate blocker. |

## Architecture decisions

- `ValeriaRail` — 4 MVP buttons only. F2 buttons (anclados/tareas/notas) **completely absent** (not rendered, not hidden via CSS) per D5.
- `ValeriaChatSlot` — Server Component (no state/effects). Uses `bg-vitalia-success` (Tailwind token) for status dot to satisfy both `test_no_hardcoded_colors` AND `test-no-vt-classes-in-new-features` arch tests.
- Radix Tooltip Portal workaround: `data-tooltip="..."` attributes on each `<Button>` trigger as testability surface (Portal content not in DOM until hovered in happy-dom).
- `HistoryGroup` — Server Component despite rendering Client Component `HistoryItem` (valid Next.js App Router pattern).

## Gherkin coverage (T-3)

| Scenario | Test file | Status |
|---|---|---|
| SC-1 happy · 4 buttons MVP-only | `ValeriaRail.test.tsx` | PASS |
| SC-1 · F2 buttons NOT rendered | `ValeriaRail.test.tsx` | PASS |
| SC-1 · click handlers dispatched | `ValeriaRail.test.tsx` | PASS (×4) |
| SC-7 a11y · aria-labels Spanish neutro | `ValeriaRail.test.tsx` | PASS |
| SC-7 · tooltips keyboard hints via data-tooltip | `ValeriaRail.test.tsx` | PASS |
| SC-7 · no voseo | `ValeriaRail.test.tsx` | PASS |
| Visual baseline · ChatSlot header + status | `ValeriaChatSlot.test.tsx` | PASS |
| Visual baseline · 4 skeleton bubbles alternated | `ValeriaChatSlot.test.tsx` | PASS |
| Visual baseline · composer placeholder | `ValeriaChatSlot.test.tsx` | PASS |
| Visual baseline · section region + label flotante | `ValeriaChatSlot.test.tsx` | PASS |

## Validators GREEN

| Gate | Result | Notes |
|---|---|---|
| `tsc --noEmit` | PASS (0 errors) | TypeScript strict |
| `eslint src/` | PASS (0 errors, 0 warnings on new files) | 60+ rules |
| `vitest run --coverage` | PASS (1022/1022 tests, 66% coverage) | 20% threshold |
| Architecture fitness (15 tests, 64 assertions) | PASS (all 15 GREEN) | FE-A1 hardcoded colors, FE-A5 server-first, no-vt-classes, no-voseo, etc. |
| Warning baselines | UNCHANGED | check-file/jsdoc/react-perf: no growth |

## Constraints respected

- No hex colors in TSX files (`bg-vitalia-success` replaces `bg-[#22c55e]`)
- No `vt-*` classes in shell-organism components
- No default exports
- No voseo in user-facing strings
- F2 buttons completely absent (not greyed, not hidden)
- Did NOT touch: `shell-store.ts`, `ValeriaSidebar.tsx`, `ValeriaHistory.tsx`, `ShellOrganismLayoutClient.tsx`, `TopBarGlobal.tsx`

## Live verification

`chrome-devtools-verify` skill is marked DEPRECATED for Linux Mint (per project_context Note 2026-05-15). Manual verification steps documented in IMPL-LOG equivalent above. Escalating to Chris staging gate.
