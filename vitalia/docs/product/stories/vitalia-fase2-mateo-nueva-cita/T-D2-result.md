# T-D2 Result — Separar Fecha/Hora nueva-cita

**Ticket:** T-D2 (delta disponibilidad G #1)
**Brand:** vitalia
**Fecha:** 2026-06-25
**Scope:** `vitalia/frontend/src/features/mateo/components/nueva-cita/**` ÚNICAMENTE

## Qué se hizo

Split del control combinado `SmartDateTimePicker` (fecha+hora) en dos controles distintos dentro de `NuevaCitaView.tsx`:

- **FECHA** → `<SmartDateTimePicker showTime={false} ...>` (calendar-only, emite ISO UTC)
- **HORA** → `<TimePicker value="HH:MM" onChange>` (átomo de hora, nuevo en `@luana/ui-kit@0.8.0`)

Ambos del kit (`@luana/ui-kit@0.8.0` ya shippeado — cero edits a `core/`).

### Cambios en `NuevaCitaView.tsx`

1. **Import:** `TimePicker` sumado al import de `@luana/ui-kit` (junto a `EntitySubNavBar`, `SmartDateTimePicker`).
2. **Estado local split:** `startDateStr: string` ("YYYY-MM-DD") + `startHourStr: string` ("HH:mm"), inicializados desde `prefillDate`/`prefillTime`.
3. **Handlers:** `handleFechaChange(iso)` + `handleHoraChange(hhmm)` — ambos con `useCallback` + deps correctas. Llaman `buildIsoFromDateAndTime(dateStr, hhmm, timezone)` → `setValue("startTime", composed)` solo cuando AMBOS presentes. Cascada `endTime` autocalc preservada (`!endTimeEditMode` → `addMinutesToIso`).
4. **Layout:** `nc-row-2` pasa de `grid-cols-2` a `grid-cols-3` (Fecha | Hora | Duración). Sin arbitrary values.
5. **`Controller`** sigue en uso para `origin`, `endTime`, `notesInternal` (no se tocaron).

### Cambios en `NuevaCitaView.test.tsx`

- `fireEvent` + `within` agregados al import `@testing-library/react`.
- Mock de `TimePicker` dentro del bloque `vi.mock("@luana/ui-kit")` — renderiza como `<input data-testid="time-picker" aria-label="...">`.
- 3 tests T-D2 nuevos:
  1. `T-D2: Fecha and Hora render as separate sections` — aserta `nc-section-fecha` y `nc-section-hora` con sus controles internos.
  2. `T-D2: changing Fecha alone does not compose startTime` — sin hora, `startTime` no se compone (avail-intro visible).
  3. `T-D2: Fecha then Hora compose startTime and trigger endTime autocalc` — secuencia completa → `nc-fin-editar` aparece, avail-intro desaparece.

## Gates

| Gate | Resultado |
|---|---|
| `npx tsc --noEmit` | ✅ 0 errores |
| `npx eslint src/features/mateo --cache` | ✅ 0 errores |
| `npx vitest run src/features/mateo` | ✅ 398/398 PASS (21 en NuevaCitaView.test.tsx, 3 nuevos T-D2) |

## Notas

- Warnings pre-existentes en stderr (`act()`, key de react-window) — no introducidos por este diff, confirmados con scope anterior.
- Live-verify: Chrome DevTools MCP no disponible en esta sesión — la verificación del flujo Fecha/Hora en dev-app forma parte del G de Chris (story en `developed · AWAIT_CHRIS_VERIFY`).
- `core/` intacto — se consume `@luana/ui-kit@0.8.0` via `workspace:*`, cero edits al kit.

## DO NOT TOUCH (preservado)

- `DayAvailabilityStrip`, `FreeDoctorsList`, `use-availability.ts` (T-D3) — sin cambios.
- `handleCancel`, `endTime` autocalc, Patient inline, tokens obs#4 — sin cambios.
