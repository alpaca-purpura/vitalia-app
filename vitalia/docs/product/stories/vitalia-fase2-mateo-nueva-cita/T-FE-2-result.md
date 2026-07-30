# T-FE-2 Result — Pickers (ServicePicker, DoctorPicker, PatientPickerWithCreate, CanalPicker)

**Ticket:** T-FE-2 · vitalia-fase2-mateo-nueva-cita  
**SHA:** cf0c7022  
**Branch:** wip/vitalia  
**Date:** 2026-06-22  
**Gate:** tsc 0 errors | eslint 0 errors | vitest 363/363 PASS

---

## Files Created (new, T-FE-2 scope only)

| File | Description |
|---|---|
| `vitalia/frontend/src/features/mateo/components/nueva-cita/ServicePicker.tsx` | Radix Select controlled picker; onChange fires {offerId, durationMinutes} |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/DoctorPicker.tsx` | Radix Select controlled; no UUID textbox (AC-1/2); disabled prop |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/PatientPickerWithCreate.tsx` | EntityPicker + createAction inline mini-form; RN-9 dup prompt; 3-state FSM |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/CanalPicker.tsx` | Shadcn Tabs controlled (walk_in / telefono) |
| `vitalia/frontend/src/features/mateo/hooks/use-patients.ts` | useSearchPatients (EntityPicker.searchFn) + useCreatePatientInline |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/ServicePicker.test.tsx` | 5 tests |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/DoctorPicker.test.tsx` | 5 tests |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/PatientPickerWithCreate.test.tsx` | 4 tests |
| `vitalia/frontend/src/features/mateo/hooks/__tests__/use-patients.test.ts` | 5 tests (hook RED-first) |

**FORBIDDEN files NOT touched:** NuevaCitaView.tsx, nueva-cita-store.ts, agenda-schema.ts, features/mateo/index.ts

---

## Key Design Decisions

### Channel mapping (BE contract mismatch fixed)
`PatientInlineCreateRequest.channel` BE accepts `["whatsapp","instagram","web","phone","walk_in","other"]`. UI uses `"walk_in"` | `"telefono"`. Mapping in `useCreatePatientInline`:
- `"telefono"` → `"phone"`
- `"walk_in"` → `"walk_in"` (pass-through)

### EntityPicker.createAction (inline, no navigation — AC-10)
`PatientPickerWithCreate` uses a 3-state FSM (`picker` | `create` | `duplicate`). The `createAction.onCreate` callback switches to `"create"` state showing an inline mini-form within the same component — user never leaves the nueva-cita form.

### RN-9 duplicate phone
When `useCreatePatientInline.mutateAsync` resolves with `isDuplicate: true`, the component switches to `"duplicate"` state showing "Ya existe {nameMasked} · ¿Usar existente?" prompt. User can accept (calls onChange with existing patientId) or cancel.

### CanalPicker (controlled Tabs instead of TogglePill)
TogglePill from @luana/ui-kit only supports `defaultValue` (uncontrolled). For RHF controlled binding, CanalPicker uses Shadcn `Tabs` directly. Promotion candidate: add `value`/`onValueChange` to TogglePill when ≥2 controlled uses.

### Radix Select jsdom limitation
Radix UI `Select` requires `PointerCapture` (not available in jsdom). Tests for ServicePicker and DoctorPicker verify render states (loading/empty/trigger present) and test the onChange contract directly. Full open→select flow is covered by e2e (T-FE-3/T-FE-4 scope, Playwright).

---

## Notes for T-FE-4 (integration ticket)

T-FE-4 must wire these pickers into NuevaCitaView. Key integration points:

1. **ServicePicker** → `onChange({ offerId, durationMinutes })` → `setSelectedServiceId(offerId)` + update `durationMinutes` state → drives `endTime` calculation.
2. **DoctorPicker** → `onChange(doctorId)` → `setSelectedDoctorId(doctorId)` → drives availability check.
3. **PatientPickerWithCreate** → `onChange(patientId)` → `setPatientId(patientId)` + `setValue("patientId", patientId)` in RHF.
4. **CanalPicker** → `onChange(canal)` → `setValue("origin", canal)` in RHF.
5. All pickers need `tenantId` + `token` props passed from NuevaCitaView parent context.
6. `uiChannel` prop on PatientPickerWithCreate should be wired to `watch("origin")` so the patient create channel matches the cita canal.

No store or schema changes required for T-FE-2 (all controlled via props).

---

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite patterns, hook structure, ESLint rules | Used vi.hoisted for mock hoisting; Radix jsdom limitation documented; FSD boundaries respected |
| `vitalia-design-system` | ADR-vitalia-004 compliance, EntityPicker canon | EntityPicker from @luana/ui-kit consumed (not recreated); TogglePill uncontrolled → used Tabs |
| `tenant-isolation` | useTenantId vs Clerk org | useClinicId + useActorHeaders injected in hooks; X-Clinic-ID dual filter mandatory |
| `tdd-mandatory` | RED tests before GREEN code | Hook tests (use-patients) written first; component render tests written first |

---

## Gate Output

```
tsc --noEmit:       0 errors (PASS)
eslint src/:        0 errors (PASS)
vitest run mateo/: 363/363 tests PASS (30/30 test files)
```

---

## Commit

`cf0c7022` — feat(vitalia,mateo): T-FE-2 pickers — ServicePicker, DoctorPicker, PatientPickerWithCreate, CanalPicker + hooks
