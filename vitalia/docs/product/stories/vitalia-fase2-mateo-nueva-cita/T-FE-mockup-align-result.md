# NuevaCita mockup-align result

**Task:** Align "Nueva cita" form to RATIFIED mockup (9 differences closed).
**Branch:** wip/vitalia
**Files touched:** 3 production files

---

## Files modified

1. `vitalia/frontend/src/features/mateo/components/nueva-cita/NuevaCitaView.tsx`
2. `vitalia/frontend/src/features/mateo/components/nueva-cita/PatientPickerWithCreate.tsx`
3. `vitalia/frontend/src/features/mateo/components/nueva-cita/CanalPicker.tsx`

---

## 9 differences — mapping

| # | Difference | Implementation |
|---|---|---|
| 1 | **2-col layout** — form left + availability right | Added `grid grid-cols-1 gap-6 lg:grid-cols-[1fr_380px]` inside `FormPageScaffold` children. Left col = form fields with `data-testid="nc-col-form"`. Right col = availability with `data-testid="nc-col-avail"`. `FormPageScaffold` preserved (test requires `form-page-scaffold` testid). Responsive: collapses to 1-col below lg. |
| 2 | **Field order** — Canal→Paciente→Servicio→[Fecha+Dur row]→Fin→Médico→Notas | Sections reordered in left column to match mockup exactly. Preserved all `data-testid="nc-section-*"` attributes. |
| 3 | **Fecha+Duración 2-up row** | Wrapped both sections in `grid grid-cols-2 gap-4` div with `data-testid="nc-row-2"`. Duration label shortened to "Duración (min)" to fit narrower column. |
| 4 | **Hora de fin = computed read-only + "editar" link** | Added `endTimeEditMode` state (default false). Default: shows `HH:mm` + "⚙ autocalculado" + "editar" button (`data-testid="nc-fin-editar"`). Clicking "editar" reveals `SmartDateTimePicker`. Changing start or duration resets to auto-computed and exits edit mode. |
| 5 | **Paciente rich chip** | Added third render branch in `PatientPickerWithCreate`: when `selectedPatient` is set (and mode=picker), renders chip with avatar initials (`getInitials()` helper), `selectedPatient.name`, `selectedPatient.phoneMasked` sub-line, ✕ button (`data-testid="patient-chip-remove"`). Container: `data-testid="patient-chip"`. |
| 6 | **Crear paciente + Email field** | Added `email` field to `InlineCreateSchema` (same pattern as phone: `""` → null transform, optional). Added email `Input` with `data-testid="patient-inline-email"`. `handleInlineSubmit` now passes `data.email` instead of hardcoded null. |
| 7 | **Canal labels with emoji** | `CanalPicker.tsx`: "Presencial" → "🚶 Walk-in"; "Teléfono" → "📞 Teléfono". Testids `canal-picker-walk-in` and `canal-picker-telefono` unchanged. |
| 8 | **Sticky action bar copy** | `NuevaCitaView.tsx`: removed dynamic `actionHint` memo. Always passes static string `"Sin guardar todavía · los datos no se pierden si navegas dentro de la hoja."` to `NuevaCitaActions`. |
| 9 | **Hierarchy/spacing** | Right column has `h2` heading "Disponibilidad del médico". Left column has `h2` heading "Datos de la cita". Section gaps `gap-5` (left), `gap-4` (right). General parity with mockup hierarchy. |

---

## Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | 0 errors |
| `eslint src/` | 0 errors, 0 warnings |
| `vitest run src/features/mateo/` | 30 files, 371 tests — all PASS |
| Warning baselines | No growth (was 0, still 0) |

---

## Preserved (did NOT break)

- All `data-testid` attributes: `nueva-cita-form`, `nc-section-*`, `canal-picker-walk-in`, `canal-picker-telefono`, `nc-day-strip-container`, `nc-free-doctors-container`, `nc-availability-chip-container`, `nc-duracion-input`, `nc-end-time-error`, `patient-picker`, `patient-inline-*`, `patient-duplicate-*`, `nueva-cita-actions-submit`
- RHF/Zod logic, all hooks, submit logic, RN-10 fail-closed
- CanalPicker radiogroup a11y (role=radiogroup, aria-checked)
- `shouldValidate: !!value` premature-validation fix
- EntityPicker dedup
- Created patient shown in picker chip (via `setSelectedPatient` after create)
- Spanish neutro LatAm ("Walk-in" English exception per mockup)

---

## Promotion notes

No new primitives created locally. All atoms used from `@luana/ui-kit` canon (FormActionBar, SmartDateTimePicker, EntityPicker). The rich-chip patient display and computed-fin display are single-use components inside `PatientPickerWithCreate` and `NuevaCitaView` respectively — no promotion needed (feature-scoped, not shared).

Live verification: `chrome-devtools-verify` skill not invoked (not available in this session context). Escalate to Chris for staging gate manual verification per definition-of-done-live-verify rule.
