# T-FE-uxfix — UX Fix-Loop Result
<!-- cap: scheduling.mateo-agenda -->

**Story:** vitalia-fase2-mateo-nueva-cita  
**Task:** UX-FIXLOOP-2026-06-24.md (16 findings)  
**Commit:** `8075cd86`  
**Branch:** wip/vitalia  
**Date:** 2026-06-24  

---

## Findings table

| ID | Severity | Type | Status | Files touched | Test |
|----|----------|------|--------|---------------|------|
| H1 | HIGH | BUG | RESOLVED | NuevaCitaView.tsx · DayAvailabilityStrip.tsx | nueva-cita-helpers.test.ts (3 cases) |
| H2 | HIGH | BUG+DESIGN | RESOLVED | NuevaCitaView.tsx | NuevaCitaView.test.tsx (blockingReason) |
| H3 | HIGH | DIVERGE | RESOLVED | DayAvailabilityStrip.tsx | DayAvailabilityStrip.test.tsx (enriched strip) |
| H4 | HIGH | BUG | RESOLVED | ServicePicker.tsx · DoctorPicker.tsx | ServicePicker.test.tsx · DoctorPicker.test.tsx |
| M1 | MEDIUM | DIVERGE | RESOLVED | NuevaCitaView.tsx | NuevaCitaView.test.tsx (nc-avail-intro) |
| M2 | MEDIUM | DIVERGE | RESOLVED | NuevaCitaView.tsx | NuevaCitaView.test.tsx (HIPAA placeholder) |
| M3 | MEDIUM | DIVERGE | RESOLVED | NuevaCitaView.tsx | NuevaCitaView.test.tsx (nc-duracion-hint) |
| M4 | MEDIUM | BUG | RESOLVED (brand-local) | NuevaCitaView.tsx | — (engine boundary, no code change to engine) |
| M5 | MEDIUM | DESIGN | RESOLVED | NuevaCitaView.tsx | — (visual, Chris verifies live) |
| M6 | MEDIUM | BUG | RESOLVED | ServicePicker.tsx · DoctorPicker.tsx | — (controlled Select, tsc enforces) |
| L1 | LOW | DESIGN | RESOLVED + DIVERGE ANNOTATED | CanalPicker.tsx | NuevaCitaView.test.tsx (canal label) |
| L2 | LOW | BEHAVIOR | RESOLVED | NuevaCitaView.tsx | nueva-cita-helpers.test.ts (L2 guard) |
| L3 | LOW | DATA | ESCALATED as HB | DoctorPicker.tsx (defensive fallback) | nueva-cita-helpers.test.ts (L3 UUID) · DoctorPicker.test.tsx |
| L4 | LOW | CONSISTENCY | RESOLVED | PatientPickerWithCreate.tsx | PatientPickerWithCreate.test.tsx (opcional) |
| L5 | LOW | PULIDO | RESOLVED | PatientPickerWithCreate.tsx | PatientPickerWithCreate.test.tsx (typed name) |
| L6 | LOW | PULIDO | RESOLVED | NuevaCitaView.tsx | NuevaCitaView.test.tsx (counter /500) |

---

## Finding details

### H1 — UTC bug in time display (RESOLVED)
`isoToHHMM` and `isoToStripMinutes` were using UTC hours. Fixed both to use
`Intl.DateTimeFormat.formatToParts` with the tenant timezone. `NuevaCitaView`
passes `timezone` down to `DayAvailabilityStrip`.

### H2 — No blocking reason shown (RESOLVED)
Added `blockingReason` useMemo in `NuevaCitaView` that returns a Spanish neutro
string for each blocked state (no patient / no service / no startTime / no doctor /
endTime ≤ startTime / checking availability / not available). Rendered as
`<p role="status" aria-live="polite" data-testid="nc-blocking-reason">`.

### H3 — DayAvailabilityStrip bare (RESOLVED)
Component enriched in-place: header (date + "07:00–21:00" range), hour axis
(AXIS_HOURS = [8,10,12,14,16,18,20]), busy block labels (Ocupado: HH:mm–HH:mm),
legend (Atención / Ocupado / Cita nueva). Arbitrary `text-[10px]` → `text-xs`
(ESLint `@luana/ds/no-arbitrary-value`).

### H4 — No error state on picker failure (RESOLVED)
`ServicePicker` and `DoctorPicker` each got `error?: boolean` + `onRetry?: () => void`
props. Error block renders before empty state with destructive styling + retry button.
`NuevaCitaView` wires `isError`/`refetch` from both React Query hooks.

### M1 — Right column blank before startTime (RESOLVED)
Added intro block (`data-testid="nc-avail-intro"`) with dashed border explaining
what the right column will show once startTime is selected.

### M2 — Notes placeholder not HIPAA-compliant (RESOLVED)
Changed to: `"Solo logística — sin información clínica. Ej: la paciente prefiere las mañanas."`

### M3 — Duration field opaque (RESOLVED)
Helper text `<p data-testid="nc-duracion-hint">Viene del servicio · editable</p>`
added below the duration input. BE field `initialApptDurationMinutes` confirmed
as `number | null` in hook types — field exists, no BE change needed.

### M4 — FormActionBar hint visible on mobile (RESOLVED, brand-local)
Engine boundary respected (cannot edit `@luana/ui-kit`). Fixed brand-locally by
wrapping hint text: `<span className="hidden sm:inline">Sin guardar todavía…</span>`.

### M5 — Availability chip only in right column (RESOLVED)
Added inline `AvailabilityChip` below DoctorPicker with `lg:hidden` so it's visible
on narrow viewports where the right column is collapsed.

### M6 — Uncontrolled Select flash (RESOLVED)
`value={value ?? undefined}` → `value={value ?? ""}` in both ServicePicker and
DoctorPicker. Select is now always controlled.

### L1 — Emoji walk-in label (RESOLVED + DIVERGE ANNOTATED)
`CanalPicker` labels changed: "🚶 Walk-in" → "Sin cita", "📞 Teléfono" → "Teléfono".
**DIVERGE NOTE:** signed mockup shows "Walk-in" with emoji. Applied cleaner labels
per UX finding but added comment in code: `// ponytail: DIVERGE from signed mockup
(L1 UX-FIXLOOP-2026-06-24) — removed emoji/walk-in, using neutral LatAm labels`.
Annotation for PM/auditor awareness.

### L2 — endTime overwritten when manually set (RESOLVED)
Added `endTimeEditMode` guard in two places in `NuevaCitaView`:
- `startTime` onChange: only recomputes `endTime` when `!endTimeEditMode`
- `durationMinutes` onChange: same guard

### L3 — UUID doctor labels (ESCALATED as HB + defensive fallback)
Root cause is dirty seed data, not code. Code fix: added `UUID_RE` regex +
defensive fallback in `DoctorPicker` map: if label matches UUID pattern →
"Médico sin nombre". Unit test in `nueva-cita-helpers.test.ts`.
**HB to log:** seed fixture for doctors should use real names not UUIDs.

### L4 — Optional phone/email not labeled (RESOLVED)
PatientPickerWithCreate: phone label now renders
`Teléfono <span className="font-normal text-muted-foreground">(opcional)</span>`,
same for email.

### L5 — Patient chip shows masked name (RESOLVED)
`setSelectedPatient` call changed from `name: result.nameMasked` to `name: data.name`
(uses the full name from the create response). Added `min-h-[40px]` to chip div
for stable height before selection.

### L6 — Notes field has no length indicator (RESOLVED)
Character counter added below Textarea:
`<p data-testid="nc-notas-counter">{(field.value ?? "").length}/500</p>`
with `aria-live="polite"`.

---

## Skills consulted

| Skill | Why | Decision |
|-------|-----|----------|
| `frontend-expert` | FSD-Lite boundaries, ESLint config, Vitest patterns | Confirmed `react-hooks/exhaustive-deps` not in config → removed disable comment; added `watch` to deps |
| React patterns baseline | Error states, ARIA, memoization | `role="status"` + `aria-live="polite"` for H2; `aria-busy` on strip loading |
| Shadcn UI conventions | Select controlled pattern | `value={value ?? ""}` to keep always-controlled |
| Tailwind conventions | `@luana/ds/no-arbitrary-value` rule | All `text-[10px]` → `text-xs` |
| Zod/RHF | Forms already wired, no new schema needed | — |
| `chrome-devtools-verify` | Live verify | NOT invoked — Chris verifies live per task spec |

---

## Quality gates

```
tsc --noEmit:          0 errors  ✅
eslint src/features/mateo: 0 errors  ✅
vitest run src/features/mateo: 393 passed (31 files)  ✅
```

---

## Escalations

**L1 DIVERGE:** "Sin cita"/"Teléfono" applied per UX finding but diverges from
signed mockup (which shows "🚶 Walk-in"/"📞 Teléfono"). Annotated in code.
PM/auditor should ratify or revert to mockup labels.

**L3 HB:** Doctor labels showing UUIDs = dirty seed data issue.
Code fallback added ("Médico sin nombre") but root fix is updating the seed fixture.
Recommend: create HB entry targeting `vitalia/backend/tests/fixtures/eval/` doctor seed data.

---

## Files changed

Production:
- `vitalia/frontend/src/features/mateo/components/nueva-cita/NuevaCitaView.tsx`
- `vitalia/frontend/src/features/mateo/components/nueva-cita/DayAvailabilityStrip.tsx`
- `vitalia/frontend/src/features/mateo/components/nueva-cita/ServicePicker.tsx`
- `vitalia/frontend/src/features/mateo/components/nueva-cita/DoctorPicker.tsx`
- `vitalia/frontend/src/features/mateo/components/nueva-cita/CanalPicker.tsx`
- `vitalia/frontend/src/features/mateo/components/nueva-cita/PatientPickerWithCreate.tsx`

Tests:
- `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/nueva-cita-helpers.test.ts` (NEW — H1/L2/L3)
- `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/NuevaCitaView.test.tsx`
- `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/DayAvailabilityStrip.test.tsx`
- `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/ServicePicker.test.tsx`
- `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/DoctorPicker.test.tsx`
- `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/PatientPickerWithCreate.test.tsx`

---

<!-- @pm: build phase done (state: tests-passing). Commit: 8075cd86. Files: 14 changed (12 production+test, 2 docs). Native ticket tests: 393/393 PASS. Awaiting orchestrator → gate-runner → auditor-frontend (independent verdict). -->
