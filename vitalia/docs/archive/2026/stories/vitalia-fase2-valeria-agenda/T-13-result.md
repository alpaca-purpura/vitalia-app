# T-13 Result — FE AgendaCalendar + 3 variants + FreshnessIndicator

**Ticket:** T-13  
**Story:** vitalia-fase2-valeria-agenda (F2-S1)  
**Branch:** wip/vitalia  
**Commit:** 35b353e0  
**State:** developed  
**Date:** 2026-05-26  
**Owner:** claude-sonnet

---

## Acceptance criteria status

| # | Criterion | Status |
|---|---|---|
| A1 | Each variant (Day/Week/Month) renders slots correctly per view | PASS |
| A2 | AgendaSlot border-left 3px per payment_status (via vitalia CSS vars) | PASS |
| A3 | Origin badge emoji + ARIA label + PHI-masked patient name | PASS |
| A4 | DayCalendar uses react-window List when >50 slots | PASS |
| A5 | MonthCalendar consumes aggregates (not bulk slots) — dots only | PASS |
| A6 | FreshnessIndicator updates on dataUpdatedAt + refresh button | PASS |

---

## Files shipped

### New files (T-13)
- `vitalia/frontend/src/features/valeria/components/agenda/AgendaCalendar.tsx` — dispatcher: reads view from useAgendaFilters, renders Day/Week/Month/Skeleton
- `vitalia/frontend/src/features/valeria/components/agenda/AgendaSlotInteractive.tsx` — interactive slot cell (button, ARIA, PHI-masked, border-status, origin-badge)
- `vitalia/frontend/src/features/valeria/components/agenda/DayCalendar.tsx` — single-day timeline, react-window v2 `List` when >50 slots (A4)
- `vitalia/frontend/src/features/valeria/components/agenda/WeekCalendar.tsx` — 7-column Mon–Sun grid, default view
- `vitalia/frontend/src/features/valeria/components/agenda/MonthCalendar.tsx` — 5-week aggregate dots (A5), per-day click → onDayClick
- `vitalia/frontend/src/features/valeria/components/agenda/SkeletonCalendar.tsx` — 7-column loading skeleton
- `vitalia/frontend/src/features/valeria/components/agenda/FreshnessIndicator.tsx` — "Actualizado hace X" live label + refresh button
- `vitalia/frontend/src/features/valeria/components/agenda/__tests__/AgendaCalendar.test.tsx` — 19 tests (TDD RED→GREEN)
- `vitalia/frontend/src/features/valeria/components/agenda/__tests__/AgendaSlotInteractive.test.tsx` — 14 tests (TDD RED→GREEN)

### Modified files
- `vitalia/frontend/src/features/valeria/components/agenda/ValeriaAgendaView.tsx` — renders AgendaCalendar in content section + sr-only empty state text
- `vitalia/frontend/src/app/globals.css` — added `--vitalia-warning-color` + `--vitalia-muted-status-color` CSS vars

### Barrel (index.ts) already updated by T-16 background agent
- T-13 exports were pre-added in the barrel from T-16 session (linter sync)

---

## Test results

```
Test Files: 179 passed (179)
Tests: 1897 passed (1897)
T-13 specific:
  AgendaCalendar.test.tsx: 19/19 PASS
  AgendaSlotInteractive.test.tsx: 14/14 PASS
TypeScript: 0 errors (strict)
ESLint: 0 errors, 0 warnings (T-13 files)
Architecture test (hardcoded colors): PASS
```

---

## Key technical decisions

### react-window v2 API (A4)
react-window v2 uses `List` (not `FixedSizeList` from v1). API: `rowComponent`/`rowProps`/`rowCount`/`rowHeight`. Test mock updated to match v2 API.

### Color tokens (arch gate compliance)
Used `border-l-[color:var(--vitalia-success-color)]` (CSS var shortcut defined as `hsl(...)` in globals.css) instead of `hsl(var(--vitalia-success))` arbitrary values — the latter triggers the `test_no_hardcoded_colors` arch fitness test because its regex catches `hsl(`.

Added to globals.css:
- `--vitalia-warning-color: hsl(33 91% 44%)` 
- `--vitalia-muted-status-color: hsl(220 9% 65%)`

### Badge ARIA disambiguation (A3)
Button aria-label does NOT include the badge ariaLabel text to prevent `getByLabelText` collision. The badge span has `role="img" aria-label="Walk-in"` as the accessible name. The button provides full context via `Slot HH:MM · PatientMasked · ServiceLabel · estado {status}`.

### HIPAA-lite compliance
- `AgendaSlotInteractive` only renders `patientNameMasked` (never raw `patient.name`)
- MonthCalendar renders NO individual slot data (aggregate counts only)
- PHI never in URL params (slot click passes only `appointmentId`)

---

## Skills consulted

- `tessl__react-patterns` — error boundary at route level (existing in page.tsx), loading/error/empty states per component, aria-busy, aria-live
- `tessl__tailwind` — `cn()` for conditional classes, CSS var tokens, no inline style
- `tessl__shadcn-ui` — Skeleton, Button from `components/ui/`
- `tessl__vitest` — TDD RED→GREEN, mock react-window, mock useAgendaFilters/useDrawerStore
- `frontend-expert` — FSD-Lite structure, barrel exports, no default exports
- `vitalia/.claude/rules/hipaa-lite.md` — PHI masking enforcement

---

## Live verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (designed for WSL2+Windows bridge). Escalated to Chris staging gate per role instructions. Manual verification required before merging to main.

---

## Downstream

- T-14 (AppointmentDrawer) — parallel agent handles this. AgendaCalendar receives `onSlotClick` callback which T-14 connects to `useDrawerStore.openDrawer`.
- T-16 (Filters + CrearCita + Mobile) — barrel already updated, no further action needed.
