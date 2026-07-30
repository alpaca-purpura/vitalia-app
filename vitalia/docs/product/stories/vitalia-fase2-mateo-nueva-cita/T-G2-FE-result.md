# T-G2-FE — Block past appointments: disablePast + Zod refine

**Story:** vitalia-fase2-mateo-nueva-cita  
**Ticket:** G#1 round-2 FE  
**SHA:** `9948e4ef`  
**Date:** 2026-06-26

## Diff (4 files, +61 -4)

### `vitalia/frontend/src/features/mateo/types/agenda-schema.ts`
Added second `.refine()` chained after the existing `endTime > startTime` refine on `CreateAppointmentRequestSchema`:
```typescript
.refine(
  (s) => new Date(s.startTime).getTime() >= Date.now(),
  {
    message: "No se pueden agendar citas en el pasado",
    path: ["startTime"],
  },
);
```

### `vitalia/frontend/src/features/mateo/components/nueva-cita/NuevaCitaView.tsx`
Added `disablePast` boolean prop to the Fecha `<SmartDateTimePicker showTime={false} ...>`:
```tsx
<SmartDateTimePicker
  showTime={false}
  disablePast          // ← added
  value={...}
  onChange={handleFechaChange}
  timezone={timezone}
  placeholder="DD/MM/AAAA"
/>
```

### `vitalia/frontend/src/features/mateo/types/__tests__/agenda-schema.test.ts`
- 2 new tests in `CreateAppointmentRequestSchema` describe:
  - `rejects startTime clearly in the past` (uses fixed `"2020-01-01T09:00:00Z"`)
  - `accepts startTime clearly in the future` (uses fixed `"2030-06-01T09:00:00Z"`)
- Fixed 2 existing tests that used `"2026-06-0X"` dates (now in past) → updated to `"2030-06-0X"`

### `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/NuevaCitaView.test.tsx`
- Expanded `SmartDateTimePicker` mock to expose `disablePast` as `data-disable-past` attribute
- New test `G-round2: Fecha SmartDateTimePicker receives disablePast prop` asserts `data-disable-past="true"` on picker inside `nc-section-fecha`

## Gate output

```
tsc --noEmit      → 0 errors ✓
eslint src/features/mateo --cache → 0 errors ✓
vitest run src/features/mateo → 433/433 tests PASS ✓
```

## Skills consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | canonical patterns for Zod refine chaining + test strategy | chain second `.refine()` after existing one; fixed-date strategy for flake-free tests |
| `spanish-text.md` | user-facing error message must be Spanish-neutro, no voseo | "No se pueden agendar citas en el pasado" ✓ |

## Notes

- Constraints respected: Fecha/Hora split from round-1 untouched; tz fix untouched; `DayAvailabilityStrip`/`FreeDoctorsList`/`use-availability`/BE not touched.
- The `errors.startTime` display already exists in `nc-section-hora` (RHF surfaces it automatically).
- No new file needed for the component test — added to existing `NuevaCitaView.test.tsx`.
