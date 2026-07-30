# T-FE-3 Result — FE Disponibilidad (chip + mini-vista + reasignar)

**Story:** vitalia-fase2-mateo-nueva-cita  
**Ticket:** T-FE-3  
**Date:** 2026-06-22  
**Branch:** wip/vitalia  

---

## Diff (new files only — DISJOINT-FILE guardrail respected)

### New production files

| File | Purpose |
|---|---|
| `vitalia/frontend/src/features/mateo/hooks/use-availability.ts` | Debounced `useAvailabilityCheck` (400ms) + `useDayStrip` hook; `availabilityKeys` query key factory |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/AvailabilityChip.tsx` | 4-state badge (success/warning from @luana/ui-kit); aria-live="polite"; syncs to store; fail-closed |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/DayAvailabilityStrip.tsx` | Horizontal timeline 07:00–21:00; working_hours/busy/selected-slot highlight (AC-8 mini-vista) |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/FreeDoctorsList.tsx` | One-click doctor pills; empty/loading/no-slot states (AC-5 reasignar) |

### New test files

| File | Tests |
|---|---|
| `__tests__/AvailabilityChip.test.tsx` | 10 tests — all 4 states + loading + error + store sync + unmount cleanup |
| `__tests__/DayAvailabilityStrip.test.tsx` | 6 tests — loading/error/blocks/selected-slot |
| `__tests__/FreeDoctorsList.test.tsx` | 6 tests — SC-reasignar/SC-reasignar-vacio/SC-empty-medicos/click |
| `hooks/__tests__/use-availability.test.ts` | 8 tests — key factory + disabled states + normalization + error |

### Files NOT touched (DISJOINT-FILE guardrail)
- `NuevaCitaView.tsx` — owned by T-FE-4 wiring
- `nueva-cita-store.ts` — owned by T-FE-1 (reads `setAvailabilityStatus` only)
- `agenda-schema.ts` — owned by T-FE-1
- `features/mateo/index.ts` — T-FE-4 will add exports
- `core/@luana/ui-kit/src/` — consume only (Badge, FormActionBar already promoted P-0)

---

## Gate Output

### TypeScript (tsc --noEmit)
Zero errors in T-FE-3 files. Pre-existing T-FE-2 errors (DoctorPicker, PatientPickerWithCreate missing) — not introduced by T-FE-3.

### ESLint
Zero errors on all 4 new production files.

### Vitest — T-FE-3 files
**30/30 PASS**
- AvailabilityChip: 10/10
- DayAvailabilityStrip: 6/6  
- FreeDoctorsList: 6/6
- use-availability: 8/8 (hook tests)

### Full mateo suite (pre-existing failures excluded)
355/358 PASS. The 3 failing are T-FE-2 pre-existing RED tests (DoctorPicker, ServicePicker, use-patients — components not yet built by T-FE-2).

---

## ANTI-EMBUDO Contract Verification

Verified against T-BE-3 DTOs (`availability_dtos.py`):

| Endpoint | BE field (snake_case) | FE normalized (camelCase) |
|---|---|---|
| POST /availability/check | `status`, `conflict_label`, `conflict_start` | `status`, `conflictLabel`, `conflictStart` |
| GET /availability/day-strip | `doctor_id`, `date`, `blocks[{kind, start, end}]` | `doctorId`, `dateLocal`, `blocks[{kind, start, end}]` |
| Day-strip query params | `doctor_id`, `date` | `URLSearchParams({doctor_id, date})` |

No imagined fields. All normalizers verified against real BE response_models.

---

## Store/Schema contract for T-FE-4

T-FE-4 (`NuevaCitaView.tsx` wiring) needs to:

1. **Wire `AvailabilityChip`** next to Médico selector:
   ```tsx
   <AvailabilityChip
     tenantId={tenantId}
     token={token}
     doctorId={selectedDoctorId}
     startIso={startTime}
     durationMinutes={durationMinutes}
   />
   ```
   Chip auto-writes `store.availabilityStatus` → read with:
   ```ts
   const availabilityStatus = useNuevaCitaStore((s) => s.availabilityStatus);
   const isBlocked = availabilityStatus !== null && availabilityStatus !== "available";
   ```

2. **Wire `DayAvailabilityStrip`** below Médico selector:
   ```tsx
   <DayAvailabilityStrip
     tenantId={tenantId}
     token={token}
     doctorId={selectedDoctorId}
     dateLocal={startTime ? startTime.slice(0, 10) : ""}
     selectedStartIso={startTime || null}
     selectedEndIso={endTime || null}
   />
   ```

3. **Wire `FreeDoctorsList`** for reassignment (pass data from existing `useNuevaCitaFreeDoctors`):
   ```tsx
   <FreeDoctorsList
     tenantId={tenantId}
     token={token}
     startIso={startTime}
     durationMinutes={durationMinutes}
     doctors={freeDoctorsData?.doctors ?? []}
     isPending={doctorsLoading}
   />
   ```

4. **Submit block** remains unchanged: `!isValid || isAvailabilityBlocked` (T-FE-1 pattern already correct). T-FE-4 should replace `isAvailabilityBlocked` derivation with store read:
   ```ts
   // In NuevaCitaView.tsx (T-FE-4 owns this file):
   const availabilityStatus = useNuevaCitaStore((s) => s.availabilityStatus);
   const isAvailabilityBlocked = availabilityStatus !== null && availabilityStatus !== "available";
   ```

---

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary, React patterns baseline, TDD | FSD paths confirmed; RED-first enforced; hook `use-availability.ts` in `hooks/`, components in `components/nueva-cita/` |
| `frontend-fsd` (rule) | Boundary matrix, no cross-feature imports | All imports are within `features/mateo/` or `@luana/ui-kit` |
| `frontend-visual-fidelity` (rule) | D1 design-system-first | Badge from `@luana/ui-kit` (P-0 promoted); no custom primitives |
| `hipaa-lite` (rule) | PHI constraints | No PHI in any new component; `conflict_label` = time string only; `doctor_label` = professional name |

---

## Gherkin Coverage

| Scenario | Component | Covered |
|---|---|---|
| SC-sin-horario | AvailabilityChip | ✓ (no_schedule → warning badge) |
| SC-fuera-horario | AvailabilityChip | ✓ (out_of_hours → warning badge) |
| SC-solape | AvailabilityChip | ✓ (busy → warning + conflictLabel) |
| SC-reasignar | FreeDoctorsList | ✓ (doctor pills + 1-click) |
| SC-reasignar-vacio | FreeDoctorsList | ✓ (empty state "Sin médicos disponibles") |
| SC-mini-vista | DayAvailabilityStrip | ✓ (working_hours/busy blocks + selected slot) |
| SC-revalida-cambio | useAvailabilityCheck | ✓ (key changes on slot/doctor/duration) |
| SC-disponibilidad-falla | AvailabilityChip | ✓ (isError → error chip + Reintentar) |
| SC-empty-servicios | not T-FE-3 scope | — |
| SC-empty-medicos | FreeDoctorsList | ✓ (empty state + no-slot state) |

---

## Notes for T-FE-4

- `FreeDoctorsList` receives `doctors[]` + `isPending` as props (parent already has `useNuevaCitaFreeDoctors`). No duplicate query.
- `AvailabilityChip` uses its own debounced hook (`useAvailabilityCheck` from `use-availability.ts`) — different from the non-debounced version in `use-nueva-cita.ts`. T-FE-4 should use the Chip directly (it manages the hook internally).
- `DayAvailabilityStrip` strips clips to 07:00–21:00 UTC. For clinics in non-UTC timezones this may need offset adjustment in a future story (out of T-FE-3 scope).
- `isAvailable` is exported from `useAvailabilityCheck` as a derived boolean for T-FE-4 if needed without reading the store.
