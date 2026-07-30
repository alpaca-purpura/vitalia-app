# T-FE-3 Implementation Log — Horarios calendar

## Plan

**Design-system-first (D1):**
- Reused Shadcn atoms: `Button`, `Input`, `Label`, `Select`, `Dialog`, `Skeleton` from `components/ui/`
- `cn()` for conditional classes throughout
- No inline `style={{}}` (only exception: computed pixel values for calendar positioning — can't use Tailwind for dynamic pixel heights)
- Tailwind utility classes + CSS var `--agent-lisa` for block color

**Mockup adherence + scope (D2+D3):**
- Implemented: AvailabilityCalendar week grid + BloquePopover recurrence + DoctorHorariosView wrapper
- Out of scope: full E2E Playwright specs (T-E2E ticket), visual golden snapshots (T-E2E)

**Test battery (TDD RED-first):**
1. `staff-blocks-api.test.ts` — staffKeys.blocks, AvailabilityBlock type assertions, Zod schema validation (11 tests — GREEN from start)
2. `horarios.test.tsx` — component render: 7 days, hour labels, week nav, 24h toggle, BloquePopover recurrence + delete (15 tests — RED then GREEN)

**Integration (CONN — anti-orphan):**
- `horarios/page.tsx` imports `DoctorHorariosView` from `@/features/lisa` barrel (not internal path — arch test enforces)
- `index.ts` exports all 3 new components + BloquePopoverAnchor type
- New hooks (`useAvailabilityBlocks`, `useCreateBlock`, `useUpdateBlock`, `useDeleteBlock`) exported from barrel

## Mockup scope notes

The mockup (`mockups/doctores.html`) shows the full shell including ValeriaChat sidebar. Per D3 scope discipline, this ticket implements ONLY:
- `horarios/page.tsx` (Server Component wrapping DoctorHorariosView)
- `DoctorHorariosView.tsx` (section heading + calendar wrapper)
- `AvailabilityCalendar.tsx` (week grid + drag-to-create + week nav + 24h toggle + block rendering)
- `BloquePopover.tsx` (recurrence form: freq/endCondition + delete with SC-3b warning)
- 4 new API hooks in `staff.ts`
- `AvailabilityCalendarPage.ts` POM

The shell wrapper (Ribbon, SubTabsBar, ValeriaSidebar) is rendered by the existing shell-organism layout — NOT this ticket.

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `frontend-expert` | FSD boundaries, barrel exports, runtime quality checklist | FSD: exports via `index.ts` barrel (not direct internal imports). Anti-orphan: page.tsx routes to DoctorHorariosView. |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, accessible markup, stable keys, memoization | `aria-busy` not applicable (loading shown as Skeleton); `role="grid"` on calendar with `role="gridcell"` on cells; `aria-label` on all interactive elements; `useCallback` for stable event handlers; `key=block.id` (not array index). |
| `tessl__tailwind` | Utility-first, no inline style | CSS var `--agent-lisa` for brand color. Dynamic pixel heights computed inline (only exception: calendar grid requires computed `top`/`height` values). |
| `tessl__zod` | Form schema for BloquePopover | Used existing `availabilityBlockSchema` (discriminated union recurrent/one_off) from `staff-schema.ts`. Added type-cast `errorsAny` for discriminated union field access in JSX. |
| `tessl__vitest` | Test setup, async patterns, mocking | Static imports with `vi.mock` factories. Fixed mock path: `"../../../api/staff"` from `__tests__/` folder (not `../../../../`). |
| `tessl__nextjs-app-router-modularization` | Page mixes Server + Client | `horarios/page.tsx` = pure Server Component. `DoctorHorariosView.tsx` = "use client" (has state: drag state, 24h toggle, popover state). Correct split. |
| `vitalia-design-system` | Shell organism constraints, columna angosta | Calendar must be full-width within the narrow column (Valeria chat ~320px). No fixed width. CSS grid with 7 flex-1 columns. |
| `brand-expert` | N/A — no brand studio touch | Skipped (not touching brand-studio). |

## Technical decisions

1. **@dnd-kit/core** installed (`pnpm add @dnd-kit/core @dnd-kit/utilities`). Custom drag uses mouse events (mousedown/mousemove/mouseup) on grid cells rather than dnd-kit DraggableSensor — more precise for hour-level granularity. dnd-kit DndContext wrapper kept for future enhancement.

2. **Drag interaction pattern**: `mousedown` on cell → sets `dragStartCell` + `isDragging` → `mouseenter` on cells extends range → `mouseup` opens BloquePopover with `draft` (not yet saved). Visual overlay shows drag range during drag.

3. **Recurrence FE→BE**: FE sends block spec (kind/dayOfWeek/startTime/endTime/freq/endConditionKind/endDate/occurrences). Backend resolves recurrence via dateutil.rrule (D-2). FE does NOT expand recurrence client-side.

4. **"Solo esta semana" (one-off)**: When user selects `endConditionKind === "open_ended"` in the popover, FE sends `kind: "one_off"` with `specific_date` computed from calendarWeek + dayOfWeek. This aligns with SC-1c requirement.

5. **Delete with confirmed appointments (SC-3b)**: `useDeleteBlock` returns `{ preservedAppointments: number }`. If > 0, warning dialog shown before confirming delete. The warning copy matches spec verbatim: "Este bloque tiene {N} cita(s) confirmada(s). Si lo eliminas, esas citas seguirán vigentes pero el doctor dejará de estar disponible para nuevas reservas en ese horario."

6. **TypeScript discriminated union errors**: `FieldErrors<AvailabilityBlockFormValues>` (union type) doesn't expose `.endDate` directly in non-narrowed context. Fixed with `errorsAny = errors as Record<string, any>` cast with eslint-disable comment per rule.

7. **Architecture test compliance**: `page.tsx` must import from `@/features/lisa` barrel (FSD boundary rule). Fixed by exporting `DoctorHorariosView` from `index.ts` before updating page import.

## Quality gates

- TSC: 0 errors (exit 0)
- ESLint: 0 errors (no new warnings)
- Vitest: 2411 tests pass (218 test files)
- Architecture tests: 162 pass (0 violations)
- @dnd-kit/core installed in vitalia/frontend/package.json

## Files changed

| File | Action |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/staff/[doctor-id]/horarios/page.tsx` | MODIFIED — Server Component wrapping DoctorHorariosView |
| `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/DoctorHorariosView.tsx` | NEW — "use client" root |
| `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/AvailabilityCalendar.tsx` | NEW — week grid + drag + week nav + 24h toggle |
| `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/BloquePopover.tsx` | NEW — recurrence form + delete dialog |
| `vitalia/frontend/src/features/lisa/api/staff.ts` | MODIFIED — added 4 hooks (useAvailabilityBlocks, useCreateBlock, useUpdateBlock, useDeleteBlock) |
| `vitalia/frontend/src/features/lisa/index.ts` | MODIFIED — added barrel exports for new components + hooks |
| `vitalia/frontend/src/features/lisa/store/staff-ui-store.ts` | PRE-EXISTING (calendarWeek + dragDraft already in store from T-FE-1) |
| `vitalia/frontend/e2e/pages/AvailabilityCalendarPage.ts` | NEW — Playwright POM |
| `vitalia/frontend/src/features/lisa/api/__tests__/staff-blocks-api.test.ts` | NEW — 11 tests (hooks + schema) |
| `vitalia/frontend/src/features/lisa/components/staff/__tests__/horarios.test.tsx` | NEW — 15 component tests |
| `vitalia/frontend/package.json` | MODIFIED — @dnd-kit/core + @dnd-kit/utilities added |
| `vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/06-tickets.yaml` | MODIFIED — T-FE-3 state: pushed |

## Remaining work

- T-E2E: full Playwright specs for SC-1..SC-11 with real backend writes + state_check queries + visual goldens + axe wcag2aa
- Live verification (`chrome-devtools-verify`) requires T-BE-3 (availability-blocks endpoints) to be running (DONE per 7688a96b). Dev stack must be running at localhost:3002.
