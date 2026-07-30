# T-FIX-bug7-round5-FE — Resultado

**Story:** vitalia-fase2-lisa-doctores  
**Ticket:** T-FIX-bug7-round5  
**Fase:** Round 5 — seguimientos #1 y #2 del bug7  
**Fecha:** 2026-06-14  
**Estado:** tests-passing

---

## Resumen

Dos mejoras al calendario de horarios de Lisa (staff/workspace/horarios):

1. **FEATURE #1 — Delete de bloque recurrente con scope** (`BloquePopover` + `staff.ts`)
2. **FEATURE #2 — Celdas pasadas deshabilitadas** (`AvailabilityCalendar`)

---

## FEATURE #1 — Eliminar bloque recurrente con scope

### Problema
Al eliminar un bloque recurrente, el sistema eliminaba toda la serie sin preguntar. El doctor no podía borrar solo un turno puntual ni "este y los siguientes".

### Implementación

**`vitalia/frontend/src/features/lisa/api/staff.ts`**
- `DeleteBlockResponse` ampliado: agrega `deleted: boolean` y `scope: string`
- Nuevo tipo `DeleteBlockParams`: `{ blockId, scope?, occurrenceDate? }`
- `useDeleteBlock`: firma cambia de `(blockId: string)` a `(params: DeleteBlockParams)`
- Construye query string `?scope=...&occurrence_date=...` cuando se pasan esos params
- Retrocompatible: sin scope → no se agrega `?scope=` (el backend usa `series` por defecto)

**`vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/BloquePopover.tsx`**
- Prop nueva: `occurrenceDate?: string` (la fecha ISO de la ocurrencia clickeada)
- Estado nuevo: `showRecurrentDeleteDialog` (Dialog de scope)
- `handleDeleteClick` bifurca por `block.kind`:
  - `recurrent` → abre el Dialog de scope
  - `one_off` → abre el Dialog de confirmación simple (comportamiento anterior)
- Handlers nuevos: `handleDeleteOccurrence`, `handleDeleteThisAndFuture`
- Formato de fecha para el Dialog: `Intl.DateTimeFormat("es-419", { weekday:"short", day:"numeric", month:"short" })`
- Nuevo Dialog con `data-testid="dialog-delete-scope"` y tres botones:
  - `btn-delete-occurrence` → scope=occurrence + occurrenceDate
  - `btn-delete-this-and-future` → scope=this_and_future + occurrenceDate
  - `btn-delete-scope-cancel` → no-op, cierra
- Botón confirm del dialog simple: agrega `data-testid="btn-delete-confirm"`
- Toast: `"Bloque eliminado"` / `"Turno eliminado"` / `"Turnos eliminados"` según scope
- Toast error en cada handler

**`vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/AvailabilityCalendar.tsx`**
- `popoverState` type: agrega `occurrenceDate?: string`
- `handleOccurrenceClick`: pasa `occurrence.occurrenceDate` al `popoverState`
- `BloquePopover` en render: recibe `occurrenceDate={popoverState.occurrenceDate}`

---

## FEATURE #2 — Celdas pasadas deshabilitadas

### Problema
El doctor podía arrastrar para crear bloques en el pasado, lo que causaba errores silenciosos en el backend.

### Implementación

**`vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/AvailabilityCalendar.tsx`**
- Import: `toLocalIsoDate` desde `calendarDates` SSoT
- Computa `todayIso = toLocalIsoDate(new Date())` y `currentLocalHour = new Date().getHours()` en render
- Función `isCellPast(dateIso, hour)` con `useCallback`:
  - `dateIso < todayIso` → toda la columna es pasada
  - `dateIso === todayIso && hour <= currentLocalHour` → la celda puntual es pasada
- `DroppableCell`: agrega prop `isPast?: boolean`
  - `data-past="true"` cuando `isPast`
  - `onMouseDown` hace early return si `isPast`
  - `aria-disabled={isPast}` para accesibilidad
  - Clases: `bg-muted/20 opacity-60 cursor-not-allowed` (tokens, no valores arbitrarios)
- `handleCellMouseDown`: guard adicional (`isCellPast`) antes de iniciar el drag
- Header de columna: `opacity-50` en días pasados completos
- Occurrencias en celdas pasadas: siguen renderizando (no se filtran)
- Prop `mondayIso?` añadida al interface para facilitar tests sin modificar el store

---

## Tests

### Nuevos (TDD RED→GREEN)

| Archivo | Tests | Estado |
|---|---|---|
| `bloque-popover-delete-scope.test.tsx` | 6 | PASS |
| `availability-calendar-past-cell.test.tsx` | 4 | PASS |

### Cobertura

- RED 1–6: dialog scope recurrente (3 opciones + cancelar + one_off simple + one_off sin scope params)
- RED 1–4: past-cell data-past, mousedown no-op, futuro sin data-past, visual cue

### Regresión full suite

```
Test Files  48 passed (48)
Tests  519 passed (519)
```

Anterior: 509 (incluía 6 calendarDates) → 519 (+10 nuevos).

---

## Gates

- `npx tsc --noEmit` → 0 errores
- `npx eslint src/features/lisa/...` → 0 errores en archivos tocados
- `npx vitest run src/features/lisa/` → 519/519 PASS
- Sin voseo en strings user-facing
- Sin valores arbitrarios (tokens Tailwind: `bg-muted/20`, `opacity-60`, `opacity-75`, `opacity-50`)
- `fetchClient` no modificado — `X-Tenant-ID` sigue siendo auto-inyectado
- No se tocó backend ni core

---

## Archivos modificados

- `vitalia/frontend/src/features/lisa/api/staff.ts`
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/BloquePopover.tsx`
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/AvailabilityCalendar.tsx`
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/__tests__/bloque-popover-delete-scope.test.tsx` (nuevo)
- `vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/__tests__/availability-calendar-past-cell.test.tsx` (nuevo)
