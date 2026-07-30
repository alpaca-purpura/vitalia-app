# T-16 Result — FE AgendaPresetFilters + CrearCitaButton + CrearCitaForm + PatientAutocomplete + MobileBottomSheet

**Ticket:** T-16
**Story:** vitalia-fase2-valeria-agenda
**Brand:** vitalia
**Status:** done
**Completed at:** 2026-05-26T23:16:00-05:00

---

## Deliverables

### Files created

| File | Description |
|---|---|
| `vitalia/frontend/src/features/valeria/components/agenda/AgendaPresetFilters.tsx` | 5 preset filter chips single-select, ScrollArea horizontal on mobile, ARIA role=switch, Tailwind agent-valeria token active state |
| `vitalia/frontend/src/features/valeria/components/agenda/CrearCitaButton.tsx` | DropdownMenu 3 opciones (walk_in/telefono/existing_patient), Dialog wrapper, FAB variant fixed bottom-right with side=top dropdown |
| `vitalia/frontend/src/features/valeria/components/agenda/CrearCitaForm.tsx` | RHF + Zod (CreateAppointmentRequestSchema), 3 origin variants, Sonner toast on success, inline ErrorAlert on error |
| `vitalia/frontend/src/features/valeria/components/agenda/PatientAutocomplete.tsx` | Debounced 300ms typeahead via GET /api/v1/crm/patients, PHI-masked display, only patient_id returned to form |
| `vitalia/frontend/src/features/valeria/components/agenda/MobileBottomSheet.tsx` | Sheet side="bottom" 95vh, drag handle visual, accessible title/description |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/AgendaPresetFilters.test.tsx` | 18 tests: chip rendering, ARIA state, interaction, accessibility |
| `vitalia/frontend/src/features/valeria/components/agenda/__tests__/CrearCitaButton.test.tsx` | 17 tests: desktop render, dropdown interaction, FAB variant (A4) |

### Files modified

| File | Change |
|---|---|
| `vitalia/frontend/src/features/valeria/index.ts` | Added T-16 barrel exports |
| `vitalia/frontend/package.json` | Added react-hook-form + @hookform/resolvers dependencies |
| `vitalia/frontend/src/components/ui/form.tsx` | Shadcn form component installed via `npx shadcn@latest add form` |
| `vitalia/frontend/src/components/ui/label.tsx` | Shadcn label component (already existed, skipped overwrite) |

---

## Acceptance Criteria

| AC | Status | Notes |
|---|---|---|
| A1: 5 preset chips filter URL params + visual active state | PASS | `setPresetFilter` called, `aria-checked` correct, `bg-agent-valeria-soft text-agent-valeria border-agent-valeria` active classes |
| A2: CrearCitaButton DropdownMenu 3 opciones + form variants render | PASS | walk_in/telefono/existing_patient tested via userEvent (Radix Portal) |
| A3: PatientAutocomplete debounced search + PHI-masked results (only patient_id to form) | PASS | 300ms debounce, `onChange(result.patientId)` ONLY, masked name for display |
| A4: Mobile FAB position + dropdown UP direction | PASS | `fixed bottom-4 right-4`, `side="top"` on DropdownMenuContent |

---

## Quality Gates

| Gate | Status | Notes |
|---|---|---|
| TypeScript strict (`tsc --noEmit`) | PASS (T-16 files) | 0 errors in T-16 files; 8 pre-existing errors from T-13/T-14 concurrent agents |
| ESLint (60+ rules) | PASS | 0 errors on all T-16 files |
| Vitest tests | 35/35 PASS | AgendaPresetFilters.test.tsx (18) + CrearCitaButton.test.tsx (17) |
| Architecture color test (FE-A1) | PASS for T-16 files | Switched from `hsl(var(--agent-valeria))` to `bg-agent-valeria`/`text-agent-valeria` Tailwind utility classes |
| HIPAA-lite PHI compliance | PASS | PatientAutocomplete: only `patient_id` in `onChange` callback; masked display only |
| FSD-Lite boundaries | PASS | Named exports, correct feature path, no cross-feature imports |
| Spanish neutro LatAm | PASS | No voseo, tildes/ñ correct in all user-facing strings |

---

## HIPAA-lite Compliance Notes

- `PatientAutocomplete` returns ONLY `patient_id` (UUID) to the RHF form via `onChange` callback
- Display shows `patientNameMasked` only (server-generated masked string, e.g., "P. Hernández")
- PHI not stored in FE state beyond current session
- Search query `q` sent via URL params (not PHI keys — server rejects DNI/name as query keys per `ALLOWED_GRID_PARAMS` whitelist)
- No PHI in console logs or telemetry — pattern compliant with `sanitize_payload` server-side

---

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundaries, naming, barrel exports | Named exports, `features/valeria/components/agenda/` paths, no default exports |
| `tessl__react-patterns` | Error boundaries, loading states, ARIA, memoization | useCallback for handlers, aria-busy, aria-checked, aria-label, stable keys on filter ID |
| `tessl__shadcn-ui` | Component selection — never recreate primitives | Sheet/DropdownMenu/Dialog/Input/Button/Alert/Textarea from `components/ui/`, installed form.tsx |
| `tessl__tailwind` | cn() pattern, agent-valeria tokens | `bg-agent-valeria`, `text-agent-valeria`, `border-agent-valeria` — NO hsl() literals (arch test) |
| `tessl__zod` | Form schema + RHF resolver | `zodResolver(CreateAppointmentRequestSchema)` from T-11 |
| `tessl__vitest` | Test setup, Radix portal, userEvent | userEvent.setup() for DropdownMenu (Radix Portal requires pointer events, not fireEvent.click) |
| `hipaa-lite overlay` | PHI field handling in PatientAutocomplete | patient_id only in onChange; patientNameMasked display only |

---

## Pre-existing Issues (NOT T-16)

Pre-existing TypeScript errors and test failures from concurrent T-13/T-14 background agents:
- `AppointmentDrawer.tsx` — TS errors from T-14 agent (pre-existing)
- `DayCalendar.tsx` — TS errors from T-13 agent (pre-existing)
- `AgendaSlotInteractive.tsx` + `MonthCalendar.tsx` — hardcoded color literals from T-13 (pre-existing)
- `AppointmentDrawer.test.tsx` — test failures from T-14 (pre-existing)

These are tracked in respective T-13/T-14 result files.

---

## Chrome DevTools Verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (designed for WSL2+Windows bridge, per project_context Note 2026-05-15). Manual verification steps documented:

1. Start dev server: `make dev-vitalia`
2. Navigate to `http://localhost:3002/{tenant}/valeria/agenda`
3. Verify 5 preset chips render in filter row, click each to confirm URL param updates
4. Verify "Nueva cita" button (desktop) + FAB (mobile viewport <768px)
5. Click each dropdown option to confirm correct form variant opens
6. Verify PatientAutocomplete: type 2+ chars, confirm masked names appear, select → patient_id in form state
7. Submit form → confirm Sonner toast "Cita creada"

Escalated to Chris staging gate per DEPRECATED skill note.
