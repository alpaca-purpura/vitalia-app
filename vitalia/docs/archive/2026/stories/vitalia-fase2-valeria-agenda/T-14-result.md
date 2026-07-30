---
ticket: T-14
story_id: vitalia-fase2-valeria-agenda
brand: vitalia
type: result
builder: builder-frontend (claude-sonnet-4-6)
state: developed
commit_sha: ed4171d3
files_changed: 13
native_tests: 31/31
created_at: 2026-05-27
---

# T-14 — FE AppointmentDrawer — Result

## Deliverables

| File | Status | Notes |
|---|---|---|
| `vitalia/frontend/src/components/ui/accordion.tsx` | CREATED | Shadcn Accordion (@radix-ui/react-accordion) |
| `vitalia/frontend/src/features/valeria/store/agenda-store.ts` | MODIFIED | Added staleDetected + setStaleDetected (session-only) |
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawer.tsx` | CREATED | Main Sheet wrapper + 5 accordions + resize + stale banner |
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawerHeader.tsx` | CREATED | PHI-masked patient identity + disabled "Ver ficha completa" |
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawerSkeleton.tsx` | CREATED | Loading skeleton matching 5-section layout |
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawerStaleBanner.tsx` | CREATED | Concurrent-edit warning banner |
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawerTurnoSection.tsx` | CREATED | fecha/hora/duración/doctor/servicio/estado + actions |
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawerPagoSection.tsx` | CREATED | payment status + balance + CobrarSaldoSubform slot |
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawerNotasSection.tsx` | CREATED | Staff notes textarea + last activity |
| `vitalia/frontend/src/features/valeria/components/agenda/AppointmentDrawerAccionesAvanzadasSection.tsx` | CREATED | WhatsApp reminder + disabled advanced actions |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/AppointmentDrawer.test.tsx` | CREATED | 11 tests — A1..A8 acceptance criteria |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/AppointmentDrawerTurnoSection.test.tsx` | CREATED | 11 tests — status badges, action gates, Q8 confirms |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/AppointmentDrawerPagoSection.test.tsx` | CREATED | 9 tests — payment status, balance, placeholder |

## Acceptance Criteria Results

| # | Criterion | Status |
|---|---|---|
| A1 | ARIA role=dialog + aria-modal on Sheet | PASS |
| A2 | Turno + Pago expanded by default (Accordion defaultValue) | PASS |
| A3 | Drag resize handle 440-640px + pointer events + debounced localStorage | PASS |
| A4 | Esc closes drawer via Sheet onOpenChange → closeDrawer | PASS |
| A5 | Stale banner when staleDetected=true (Zustand) | PASS |
| A6 | AlertDialog confirm for Cancelar + No-show (Q8) | PASS |
| A7 | "Ver ficha completa" disabled + Tooltip "Próximamente" (Q7) | PASS |

## Quality Gates

| Gate | Result |
|---|---|
| TypeScript strict (`tsc --noEmit`) | 0 errors |
| ESLint | 0 errors |
| Vitest (31 new tests) | 31/31 PASS |
| Full suite | 1896/1897 pass (pre-existing T-13 hardcoded colors in AgendaSlotInteractive.tsx — not my files) |
| Coverage | 82.35% statements (all files) — above 20% threshold |

## Architecture Notes

### HIPAA-lite compliance
- AppointmentDrawerHeader renders only server-masked strings (patientNameMasked, patientDniMasked)
- `data-phi` + `data-phi-type` attributes on masked fields (display audit trail)
- No raw PHI ever in component props or state
- Notes textarea has explicit copy "NO incluir diagnósticos ni datos clínicos aquí"

### CobrarSaldoSubform slot (T-15)
- `AppointmentDrawerPagoSection` includes `id="cobrar-saldo-subform-slot"` placeholder div
- Disabled state + Tooltip communicates upcoming feature
- T-15 builder replaces this component in-place

### Stale detection (§ 6.11)
- `useDrawerStore.staleDetected` added to existing store (session-only, NOT persisted)
- `openDrawer` + `closeDrawer` reset staleDetected to false
- Grid polling (30s) detects updated_at mismatch → sets staleDetected=true → banner renders

### Resize handle
- Pointer events (not mouse events) — works on touch + stylus
- Debounced 100ms to localStorage via `useDrawerWidth` (Zustand persists width)
- Clamped [440, 640] px per spec

### Barrel exports
- All 8 new components exported from `vitalia/frontend/src/features/valeria/index.ts`
- Named exports only — no default exports (FSD-Lite arch test)

## Skills Consulted

| Skill | Decision |
|---|---|
| frontend-expert | FSD-Lite paths, barrel exports, named exports only |
| tessl__react-patterns | Error boundary at route level, loading/error/empty states on all async UI, aria-busy, stable keys |
| tessl__shadcn-ui | Reused Sheet, Accordion, Dialog, Tooltip, Badge, Alert, Button, Textarea from ui/ (no recreation) |
| tessl__tailwind | cn() for conditional classes, CSS vars for colors, no inline style, no hex literals |
| tessl__vitest | Async tests, vi.mock hoisting, ESM imports in beforeEach |
| tessl__nextjs-app-router-modularization | Sheet is client-side interactive — AppointmentDrawer uses "use client" |

## Known Pre-existing Issues (NOT from this ticket)

1. `AgendaSlotInteractive.tsx` + `MonthCalendar.tsx` (T-13 files): hardcoded hex colors violate FE-A1 arch test. These are T-13 deliverables unrelated to T-14. T-13 should fix before merge.

## Next Tickets That Unblock

- T-15: CobrarSaldoSubform (slot placeholder at `id="cobrar-saldo-subform-slot"` ready)
- T-17: Integration tests (drawer is now fully implemented)
