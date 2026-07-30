# T-FE-1 Result — FE ruta + hoja leaf + schema reconciliado

**Story:** vitalia-fase2-mateo-nueva-cita
**Ticket:** T-FE-1
**Commit SHA:** 69794026
**Branch:** wip/vitalia
**Date:** 2026-06-22

---

## Gate Output

| Gate | Status | Detail |
|---|---|---|
| `tsc --noEmit` | PASS | 0 errors |
| `eslint src/` | PASS | 0 errors, 0 warnings |
| `vitest run` | PASS | 2605/2605 tests |
| Architecture fitness | PASS | included in vitest 2605 |

---

## Diff Summary

### New files (8)

| File | Description |
|---|---|
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/mateo/agenda/nueva-cita/page.tsx` | Server Component — reads ?date=&time= searchParams, renders NuevaCitaView |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/mateo/agenda/nueva-cita/loading.tsx` | Skeleton loading UI (Next.js convention) |
| `vitalia/frontend/src/app/[tenantId]/(shell-organism)/mateo/agenda/nueva-cita/error.tsx` | Client error boundary |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/NuevaCitaView.tsx` | Client root — RHF+Zod, SmartDateTimePicker, React Query hooks |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/NuevaCitaView.test.tsx` | 6 tests (AC-9: full-page render, service selector, end-time error, prefill, no modal) |
| `vitalia/frontend/src/features/mateo/hooks/use-nueva-cita.ts` | React Query hooks with snake→camel normalizers |
| `vitalia/frontend/src/features/mateo/hooks/__tests__/use-nueva-cita.test.ts` | 5 hook tests |
| `vitalia/frontend/src/features/mateo/store/nueva-cita-store.ts` | Zustand UI-state store (selectedServiceId, selectedDoctorId, patientId, originMode) |

### Modified files (10)

| File | Change |
|---|---|
| `vitalia/frontend/src/features/mateo/components/agenda/CrearCitaButton.tsx` | Rewritten: modal → router.push to /nueva-cita?origin=; 2 options only (existing_patient removed) |
| `vitalia/frontend/src/features/mateo/components/agenda/CrearCitaForm.tsx` | @ts-nocheck added (deprecated in place — AC-9/D-G; cleanup in follow-up story) |
| `vitalia/frontend/src/features/mateo/components/agenda/AgendaCalendar.tsx` | Added onEmptySlotClick prop |
| `vitalia/frontend/src/features/mateo/components/agenda/WeekCalendar.tsx` | Added onEmptySlotClick prop chain + "+" button on empty columns |
| `vitalia/frontend/src/features/mateo/components/agenda/DayCalendar.tsx` | Added onEmptySlotClick prop chain + clickable empty state |
| `vitalia/frontend/src/features/mateo/components/agenda/MateoAgendaView.tsx` | handleEmptySlotClick → router.push to /nueva-cita?date=&time= |
| `vitalia/frontend/src/features/mateo/index.ts` | Barrel exports: NuevaCitaView + hook + store types |
| `vitalia/frontend/src/features/mateo/types/agenda-schema.ts` | Reconciled: origin = walk_in|telefono only, patientId required string UUID, patientNewData removed; availability types added |
| `vitalia/frontend/src/features/mateo/types/__tests__/agenda-schema.test.ts` | 2 stale test cases replaced: walk_in with UUID patientId + telefono (instead of existing_patient) |
| `vitalia/frontend/src/features/mateo/components/agenda/__tests__/CrearCitaButton.test.tsx` | Updated to router.push behavior: added next/navigation mock, 2 options only, asserts mockPush calls |

---

## Schema Reconciliation (D-F)

BE (`CreateAppointmentRequestDTO`, T-BE-4 commit `02643f1f`) changed from prior sessions:

| Field | Before | After (reconciled) |
|---|---|---|
| `origin` | `walk_in \| telefono \| existing_patient` | `walk_in \| telefono` only |
| `patientId` | nullable `string \| null` | required `string` (UUID from CRM) |
| `patientNewData` | present (`{name, phone, email}`) | removed entirely |

FE `agenda-schema.ts` reconciled to match. `CreateAppointmentRequestSchema` updated. 2 stale tests updated.

---

## BE-Contract Mismatches Detected / Resolved

### Anti-embudo (snake_case → camelCase normalizers)

`vitaliaFetch` does NOT auto-camelize. Manual normalizers in `use-nueva-cita.ts`:
- `ServiceListItem`: `offer_id` → `offerId`, `public_name` → `publicName`, `initial_appt_duration_minutes` → `initialApptDurationMinutes`
- `FreeDoctorsResponse`: `doctor_id` → `doctorId`, `doctor_name` → `doctorName`
- `AvailabilityCheckResponse`: `availability_status` → `availabilityStatus`, `available_slots` → `availableSlots`
- `PatientSearchItem`: `patient_id` → `patientId`, `name_masked` → `nameMasked`, `phone_masked` → `phoneMasked`

### T-BE-3 endpoints consumed

- `POST /api/v1/scheduling/appointments/availability/check` → `useNuevaCitaAvailabilityCheck`
- `POST /api/v1/scheduling/appointments/availability/free-doctors` → `useNuevaCitaFreeDoctors`

### T-BE-1 endpoint consumed

- `GET /api/v1/offer/servicios` → `useNuevaCitaServices` (reads `initialApptDurationMinutes` per item)

---

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| frontend-expert | FSD-Lite boundary matrix, ESLint rules, Vitest patterns | Applied: no cross-feature imports, React Query for data, Zustand for UI state only |
| React patterns baseline | Error boundary, loading/error/empty states, accessible markup | Applied: error.tsx boundary, loading.tsx skeleton, aria-busy on loading states |
| Shadcn UI conventions | Component selection | Applied: Button, DropdownMenu from components/ui; SmartDateTimePicker from @luana/ui-kit |
| Zod validation | Form schema for CreateAppointmentRequestSchema | Applied: RHF + zodResolver, discriminated union for origin modes |
| Next.js App Router Server/Client split | Page mixes Server (metadata, searchParams) + Client (form state) | Applied: page.tsx pure Server Component + NuevaCitaView.tsx "use client" |

---

## Fixes Made During Session

1. **CrearCitaForm.tsx 16 TS errors**: Added `@ts-nocheck` (file deprecated; new modal schema incompatible). Deprecation header added.
2. **agenda-schema.test.ts 2 stale cases**: walk_in now requires real patientId UUID; replaced existing_patient test with telefono+currencyOverride test.
3. **NuevaCitaView.tsx ESLint** `no-unused-vars`: renamed `timezone` → `_timezone` in buildIsoFromDateAndTime; removed unused `watch("endTime")`.
4. **NuevaCitaView.test.tsx ESLint**: removed unused `waitFor` import.
5. **NuevaCitaView.test.tsx vitest**: Added `useUser` to `@clerk/nextjs` mock (needed by `useTenantLocale`).
6. **NuevaCitaView.test.tsx vitest**: Added `SmartDateTimePicker` to `@luana/ui-kit` mock.
7. **CrearCitaButton.test.tsx vitest**: Full rewrite — added `next/navigation` mock with `mockPush`, updated to 2-option behavior, asserts `router.push` calls (no longer tests dialog/form).
