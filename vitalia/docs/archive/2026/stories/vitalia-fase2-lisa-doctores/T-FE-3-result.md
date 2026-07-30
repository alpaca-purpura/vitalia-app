# T-FE-3 Result — Horarios calendar

## Verdict

PASS — all quality gates GREEN

## Commit

SHA: `29625988` on `wip/vitalia`

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `frontend-expert` | FSD boundaries, barrel exports, runtime quality checklist | FSD enforced: page.tsx imports from `@/features/lisa` barrel. Anti-orphan: all components connected via page route + barrel exports. |
| `vitalia-design-system` | Columna angosta constraint + agent color tokens | Calendar uses full-width column layout (flex-1 days), `--agent-lisa` CSS var for block coloring. |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, accessible markup | `role="grid"` + `role="gridcell"` on calendar, `aria-label` on all interactive elements, `useCallback` for stable refs, `key=block.id` (stable). Loading = Skeleton. |
| `tessl__tailwind` | No inline style, utility-first | Dynamic pixel heights for calendar grid (only valid exception — computed values from block timestamps). |
| `tessl__zod` | Form validation for BloquePopover | Used existing `availabilityBlockSchema` (discriminated union). `errorsAny` cast for discriminated union field access. |
| `tessl__vitest` | Test setup, mocking | Static vi.mock with factories. Fixed module path (3 levels up from `__tests__/`, not 4). |
| `tessl__nextjs-app-router-modularization` | Server/Client split | `page.tsx` = Server Component. `DoctorHorariosView.tsx` = "use client" (drag state, toggle, popover). |

## Deliverables

### New files
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/DoctorHorariosView.tsx` — "use client" root
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/AvailabilityCalendar.tsx` — week grid + drag + nav + 24h
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/BloquePopover.tsx` — recurrence form + delete
- `vitalia/frontend/e2e/pages/AvailabilityCalendarPage.ts` — Playwright POM
- `vitalia/frontend/src/features/lisa/api/__tests__/staff-blocks-api.test.ts` — 11 schema tests
- `vitalia/frontend/src/features/lisa/components/staff/__tests__/horarios.test.tsx` — 15 component tests

### Modified files
- `vitalia/frontend/src/app/.../lisa/staff/[doctor-id]/horarios/page.tsx` — Server Component with DoctorHorariosView
- `vitalia/frontend/src/features/lisa/api/staff.ts` — +4 hooks (useAvailabilityBlocks, useCreateBlock, useUpdateBlock, useDeleteBlock)
- `vitalia/frontend/src/features/lisa/index.ts` — barrel exports for new components + hooks
- `vitalia/frontend/package.json` — @dnd-kit/core + @dnd-kit/utilities
- `vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/06-tickets.yaml` — T-FE-3 state: pushed

## Quality Gates

| Gate | Result |
|---|---|
| TSC `--noEmit` | PASS (0 errors, exit 0) |
| ESLint (all new files) | PASS (0 errors, 0 new warnings) |
| Vitest (all tests) | PASS (2411 tests, 218 test files) |
| Architecture tests (FSD boundaries) | PASS (162 tests, 0 violations) |
| FSD boundary compliance | PASS (page imports from barrel `@/features/lisa`) |

## Validators addressed

- V-FN-1: useAvailabilityBlocks + useCreateBlock — weekly/biweekly block spec sent to BE
- V-FN-2: Zod schema validates biweekly + occurrences=6
- V-FN-3: Week nav (‹/›) via setCalendarWeek; one-off sends kind="one_off" + specificDate
- V-FN-4: useDeleteBlock — delete block; future slots freed (BE responsibility)
- V-FN-7: SC-3b delete flow — warning dialog shows preserved appointment count
- V-VIS-3: Calendar skeleton shown while loading; blocks rendered per day column
- V-ARCH-8: FSD-Lite boundaries enforced (0 cross-feature imports)
- V-ARCH-9: React Query for server data, Zustand for UI state (calendarWeek, dragDraft)
- V-ARCH-11: Spanish neutro LatAm copy (no voseo in user-facing strings)

## Notes

- Bidirectional validator advisory (pre-commit hook): `cross_check_1`/`cross_check_3` drift expected — new `.tsx` files have `// cap: clinics.lisa.doctores` headers but `clinics.lisa.doctores` capability YAML `scenarios[]` not updated yet. This is PM responsibility at Fase F.3 merge. NOT a blocker for `wip/*`.
- Live verification (`chrome-devtools-verify`) skipped — T-BE-3 endpoints required. Manual verification gate: Chris staging when `make dev-vitalia` stack is running.
- Store (`staff-ui-store.ts`) was PRE-EXISTING with `calendarWeek` + `dragDraft` fields (already created in T-FE-1). No changes required.
