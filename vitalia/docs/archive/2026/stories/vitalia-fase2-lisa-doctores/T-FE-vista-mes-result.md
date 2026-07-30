# T-FE-vista-mes — Result

**Ticket:** T-FE-vista-mes (D3-E: Month Calendar View)
**Story:** vitalia-fase2-lisa-doctores
**Brand:** vitalia
**State:** tests-passing

## Deliverables shipped

### New files
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/MonthCalendar.tsx`
  - 6×7 grid, chips per day (agent-lisa tint), overflow "+N más", click day→switch to Semana
  - Nav: prev / hoy / next
  - States: skeleton / empty / error+retry / grid
  - a11y: `role="grid"` + `role="gridcell"` + `aria-label` per day + keyboard nav
  - Data: `useAvailabilityOccurrences(doctorId, firstVisibleDay, lastVisibleDay)`
  - Paints EXACTLY BE-projected occurrences (RN-D3E-1, zero client expansion)
  - `MAX_CHIPS_PER_DAY = 2` with "+N más" overflow (SC-D3E-4)
  - master-data: `Intl.DateTimeFormat("es-419")` — NEVER `toLocaleDateString()`
  - Layout: semantic elements (`<section>`, `<header>`, `<ul>`, `<li>`) to keep arch test baseline ≤301

- `vitalia/frontend/src/features/lisa/components/staff/__tests__/month-calendar.test.tsx`
  - 23 vitest tests (RED-first TDD): grid structure, RN-D3E-1, SC-D3E-2..4, skeleton, error, nav, toggle
  - All 23 GREEN

- `vitalia/frontend/e2e/specs/vitalia/horarios-month-view.spec.ts`
  - SC-D3E-1..4 e2e specs via `authed-runtime.ts` + `page.route()` mocks
  - All 4 GREEN vs localhost:3002

### Modified files
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/DoctorHorariosView.tsx`
  - Added `useState<CalendarView>("semana")` toggle (default=semana)
  - Toggle pills: `data-testid="toggle-semana"` / `data-testid="toggle-mes"`
  - `handleSwitchToWeek(mondayIso)` — `setCalendarWeek(mondayIso)` + `setView("semana")`
  - Conditional render: `<AvailabilityCalendar>` (semana) or `<MonthCalendar>` (mes)
  - Drag-create preserved only in week view (RN-D3E-2)

- `vitalia/frontend/src/features/lisa/index.ts`
  - Added: `export { MonthCalendar }` + `export type { MonthCalendarProps }`

- `vitalia/frontend/playwright.config.ts`
  - Added `/.*\/e2e\/specs\/vitalia\/.*\.spec\.ts/` to smoke project testMatch

## Quality gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS (0 errors) |
| `eslint src/features/lisa/` | PASS (0 errors) |
| Vitest month-calendar.test.tsx | 23/23 PASS |
| Vitest architecture (30 tests) | 30/30 PASS |
| Vitest full suite | 2356/2356 PASS |
| Arch: test-no-div-layout | PASS (300 ≤ baseline 301) |
| E2E SC-D3E-1..4 vs localhost:3002 | 4/4 PASS |

## Architecture notes

- Layout div count: MonthCalendar uses 2 layout divs (grid+gridcell with flex-col+gap). Total 300 < baseline 301.
- Semantic HTML: `<section>` for states, `<header>` for day headers, `<ul>`/`<li>` for chips — avoids layout div inflation.
- Constraint honored: ⛔ NO EDIT to `features/lisa/api/staff.ts`
- Constraint honored: ⛔ NO EDIT to BioRepoInputs/perfil
- FSD-Lite: `features/lisa/components/staff/workspace/horarios/MonthCalendar.tsx`
- Barrel: exported via `features/lisa/index.ts`
- cap header: `// cap: clinics.lisa.doctores` on all new files

## Live verification

Stack: localhost:3002 (vitalia frontend) + localhost:8002 (vitalia backend)
- SC-D3E-1: month view chips appear on exactly 2 projected dates, zero on others — VERIFIED via e2e
- SC-D3E-2: click day cell → AvailabilityCalendar (week view) shown, toggle-semana aria-checked=true — VERIFIED via e2e
- SC-D3E-3: empty occurrences → month-empty-state visible — VERIFIED via e2e
- SC-D3E-4: 5 occs/day × 7 days → 2 chips + "+3 más" overflow — VERIFIED via e2e

## Skills consulted

- `frontend-expert`: FSD boundary matrix, ESLint rules, Vitest patterns, arch fitness baseline
- React patterns baseline: error boundary (route-level), loading/error/empty states, a11y ARIA, stable keys, memoization
- Zod validation: N/A (no forms in this ticket)
- Next.js App Router Server/Client split: MonthCalendar is `"use client"` (state + event handlers)
- master-data.md: `Intl.DateTimeFormat("es-419")` for all date formatting
- Spanish neutro LatAm: "Semana", "Mes", "Sin horarios definidos para este mes", "Reintentar", "Hoy", "Mes anterior/siguiente" — no voseo
