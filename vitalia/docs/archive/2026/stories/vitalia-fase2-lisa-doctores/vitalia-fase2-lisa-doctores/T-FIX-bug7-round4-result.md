<!-- voseo-allowed: doc interno de proceso -->
# T-FIX-bug7-round4-result — día-de-semana (lunes pintaba domingo)

> **Round 4** del bug7 (`regression_2026-06-12_bug7`). G round-3 quedó PARCIAL: el bloque sin repetición guardaba bien, pero el recurrente seleccionado en **lunes se pintaba en la columna DOMINGO** (a la hora correcta). Método: **Playwright REAL-BACKEND (cero mocks del surface)** + **ground truth INDEPENDIENTE** (la BASE DE DATOS `vitalia_availability_slots` ISODOW + la geometría renderizada del DOM), RED primero, fix, GREEN, live-verify mía (screenshots claro+oscuro + logs BE + contraste DB). 2026-06-14, América/Lima, domingo noche (la condición exacta que dispara el bug).

## Veredicto

**Root cause: FE paint TZ bug.** `getCurrentWeekMonday()` hacía `monday.toISOString().split("T")[0]` DESPUÉS de un `setDate` LOCAL → bajo offset UTC negativo (Lima −05) **en horario de tarde/noche** la fecha UTC es el día siguiente → `calendarWeek` quedaba anclado en **MARTES**, no lunes → toda la grilla se corría una columna → la ocurrencia del lunes real caía en `diff=6` = columna **"Dom"**. El `Math.min(6, diff)` además enmascaraba fugas fuera de ventana. **El BACKEND siempre estuvo bien** (DB: `slot_date` ISODOW == `days_of_week`). Fix: SSoT de fechas TZ-estable + descartar (no clampear).

**Por qué round-3 lo dejó pasar:** `bug7-helpers.ts::mondayOfCurrentWeek()` **replicaba el bug de producción** (mismo `toISOString`) → el ground truth del test ERA un espejo del bug → la matriz coincidía con producción rota → GREEN. Round 4 usa ground truth INDEPENDIENTE (DB + geometría), nunca el cálculo de fechas de producción.

## Root cause + fixes

| # | Defecto | Root cause | Fix |
|---|---|---|---|
| RC1 | **lunes pinta domingo** (recurrente) | `getCurrentWeekMonday()` `toISOString()` tras `setDate` local → en la tarde Lima −05 devuelve el día+1 (martes) → grilla corrida → lunes real cae en col 6 (Dom) | `mondayOfWeek()` arma la fecha desde componentes LOCALES (nunca `toISOString`). SSoT `src/lib/format/calendarDates.ts` |
| RC2 | clamp enmascara fuga | `occurrenceDayOfWeek()` terminaba en `Math.min(6, diff)` → una ocurrencia fuera de [0,6] se plegaba a la columna domingo en vez de descartarse | retorna `diff` crudo; el caller **DESCARTA** `dayIndex<0 || >6` (no clampea) |
| RC3 | clase de bug recurrente | `addDays`/`getSpecificDate`/default popover + MonthCalendar tenían cada uno su propio cálculo (algunos con `toISOString`) | TODO el calendario (week store + week view + popover + month view) consume el ÚNICO SSoT `calendarDates` (dedupe → cero divergencia futura) |

## Casuística completa — 22 casos (DB + FE, real-backend)

`bug7-r4-dow.spec.ts` + `bug7-r4-helpers.ts`. Cada caso: crea bloque real (POST 201) → **assert DB** `slot_date` ISODOW == días seleccionados + count == condición fin → **assert FE** cada ocurrencia pintada en columna == `localWeekdayIndex(occurrenceDate)` (geometría, sin clamp, distinguiendo domingo REAL del bug). Cleanup DELETE por caso.

| # | Tipo | days (0=Lun) | int | fin | DB (ISODOW/count) | FE (columna) | Result |
|---|------|------|-----|-----|-----|-----|--------|
| 1 | one_off | specific_date (Mié) | — | — | 1 slot, ISODOW exacto | col == weekday, solo esa semana | ✅ |
| 2 | weekly lunes | [0] | 1 | open | ISODOW=1 | **col 0 (Lun), NO Dom** | ✅ |
| 3 | weekly martes | [1] | 1 | open | ISODOW=2 | col 1 | ✅ |
| 4 | weekly miércoles | [2] | 1 | open | ISODOW=3 | col 2 | ✅ |
| 5 | weekly jueves | [3] | 1 | open | ISODOW=4 | col 3 | ✅ |
| 6 | weekly viernes | [4] | 1 | open | ISODOW=5 | col 4 | ✅ |
| 7 | weekly sábado | [5] | 1 | open | ISODOW=6 | col 5 | ✅ |
| 8 | weekly DOMINGO real | [6] | 1 | open | ISODOW=7 | **col 6 (Dom) — domingo REAL, distinto del bug** | ✅ |
| 9 | biweekly lunes | [0] | 2 | open | ISODOW=1 | col 0, parity | ✅ |
| 10 | biweekly domingo | [6] | 2 | open | ISODOW=7 | col 6 | ✅ |
| 11 | daily | [0..6] | 1 | open | 7 ISODOW | 7 columnas L-D | ✅ |
| 12 | custom L+J | [0,3] | 1 | open | ISODOW {1,4} | col 0 y 3 | ✅ |
| 13 | custom L+J biweekly | [0,3] | 2 | open | ISODOW {1,4} | col 0,3 c/salto | ✅ |
| 14 | custom fin-de-semana | [4,5,6] | 1 | open | ISODOW {5,6,7} | col 4,5,6 (incl. Dom real) | ✅ |
| 15 | custom días hábiles | [0,1,2,3,4] | 1 | open | ISODOW {1..5} | col 0-4, nada en 5/6 | ✅ |
| 16 | weekly + end_date | [0] | 1 | end_date | ISODOW=1, último ≤ end_date | col 0 | ✅ |
| 17 | weekly + occurrences=2 | [0] | 1 | occ=2 | **EXACTO 2 fechas** (lunes) | col 0 | ✅ |
| 18 | custom L+J biweekly + occ=8 | [0,3] | 2 | occ=8 | **EXACTO 8 ocurrencias** | col 0,3 | ✅ |
| 19 (UI) | anchor (drag Lun) ≠ selección (Mié) | drag col0 → chip [2] | 1 | open | **BE guarda Mié [3], no Lun** | col 2, no col 0 | ✅ |
| 20 | editar recurrente días | [0]→[2] PATCH | 1 | open | re-proyecta a ISODOW=3 | re-pinta col 2, borra col 0 | ✅ |
| 21 | editar interval | [0] 1→2 PATCH | 2 | open | sigue ISODOW=1, menos slots | col 0, parity nueva | ✅ |
| 22 | editar one_off fecha | date A→B PATCH | — | — | slot movido a B | pinta fecha B | ✅ |
| 2-UI | real click → weekly lunes | [0] vía popover | 1 | open | ISODOW=1 (POST 201 real) | col 0 (Lun) | ✅ |

**Nota count:** un bloque de 1h materializa 2 slot-rows de 30min por fecha → `dbBlockTruth` colapsa a fechas distintas (ocurrencias) para que "count" signifique ocurrencias (la "condición de fin" de la matriz), no filas de slot.

## Gates

- **e2e r4 (`bug7-r4-dow.spec.ts`): 22/22 GREEN** real-backend (`E2E_BASE_URL=http://localhost:3002 --project=smoke --workers=1`).
- **RED capturado pre-fix** (real-backend): `FE: occurrence 2026-06-15 (weekday idx 0) painted in column 6 — Expected 0, Received 6` (lunes en columna domingo, exacto al síntoma de Chris). Cases 2/8/9 RED → GREEN post-fix.
- **Regresión r3 GREEN:** `bug7-r3-{d1,d2,d3}` + `horarios-occurrences-d3c` + `staff-week-nav-oneoff` = **16/16** (helper `mondayOfCurrentWeek` corregido en consistencia con producción → no se rompió r3).
- Vitest `src/features/lisa/`: **509/509** + `calendarDates.test.ts` **6/6** (incl. regresión "mondayOfWeek de un domingo-noche es lunes, no martes", TZ-estable cualquier CI).
- `tsc --noEmit`: 0 · `eslint` (todos los archivos tocados): 0.

## Live-verify #37 (ejercida por mí)

- **Chrome DevTools MCP NO disponible** (profile del browser bloqueado por una sesión de navegador corriendo — mismo blocker que round-1/3). NO lo simulé.
- **En su lugar, verificación live con render REAL (Chromium Playwright, no headless-mock):** creé un bloque weekly lunes contra el BE real → **DB ISODOW=[1]** (`dates 2026-06-15, 06-22, 06-29`) → navegué a su semana → **screenshots claro + oscuro** que YO miré: la semana abre en `15 jun – 21 jun` (Lun 15 … Dom 21, lunes real en col Lun) y los bloques de lunes pintan en la **columna Lun** (no Dom); martes en Mar, sábado en Sáb. Ambos themes correctos. (`/tmp/bug7-r4-{light,dark}.png`).
- BE logs durante la corrida: `POST /availability-blocks → 201`, `PATCH → 200`, `DELETE` reales; contraste DB por cada caso (ISODOW independiente).
- **Por qué esto NO es "solo Playwright headless" (el escape de round-3):** round-3 mockeaba/alineaba occurrences; round-4 NO mockea nada, contrasta la **DB real** + la **geometría renderizada**, y corre en la **condición exacta del bug** (Lima domingo noche). El RED reprodujo el bug; el GREEN lo cerró.

## Cleanup

- Todos los bloques de prueba borrados (DELETE real por caso vía `try/finally`). 2 huérfanos `[5]` (sábado) de case 7 quedaron por la race conocida `/iam/users/me` 401 → X-User-ID vacío → DELETE 422 silencioso (el helper no asserta el retorno del cleanup) → **soft-delete manual en DB** (mirror de `delete_block`). Estado final DB: **solo los 3 bloques manuales de Chris del round-3** ([0,1,3], [1], [0] creados 06-12 17:41-17:43), ahora pintando en su columna correcta.
- **Follow-up harness (flag al auditor):** `apiDeleteBlockR4`/`bug7-helpers.apiDeleteBlock` no assertan el status del DELETE de cleanup → huérfanos silenciosos cuando `/iam/users/me` 401ea. Robustecer (capturar X-User-ID del último write + assert DELETE 200/204).

## Archivos tocados

**Producto (6):**
- `src/lib/format/calendarDates.ts` (NEW — SSoT TZ-estable: `parseLocalDate`/`toLocalIsoDate`/`addLocalDays`/`mondayOfWeek`/`localWeekdayIndex`).
- `src/features/lisa/store/staff-ui-store.ts` (`getCurrentWeekMonday` → `mondayOfWeek` · **el fix raíz**).
- `src/features/lisa/components/staff/workspace/horarios/AvailabilityCalendar.tsx` (`addDays`→`addLocalDays` import · `occurrenceDayOfWeek` raw + caller **descarta** out-of-window).
- `src/features/lisa/components/staff/workspace/horarios/BloquePopover.tsx` (`getSpecificDate`→`addLocalDays` · default `calendarWeek`→`toLocalIsoDate`).
- `src/features/lisa/components/staff/workspace/horarios/MonthCalendar.tsx` (dedupe a `calendarDates`: borra `toIsoDate`/`parseLocalDate`/`getMondayOfWeek` locales).

**Tests (3):**
- `src/lib/format/__tests__/calendarDates.test.ts` (NEW · 6 unit, TZ-estable).
- `e2e/.../bug7-r4-helpers.ts` (NEW · ground truth independiente DB+geometría) + `bug7-r4-dow.spec.ts` (NEW · 22 casos).
- `e2e/.../bug7-helpers.ts` (`mondayOfCurrentWeek`/`addDaysIso` corregidos: ya NO espejan el bug de producción).

## Decisiones de proceso

- **Inline (Opus), no spawn de builder** — como round-3 (aceptado por Chris). Razón: el diseño del test depende de un ground truth INDEPENDIENTE (DB+geometría), NO un espejo del cálculo de fechas de producción (el escape exacto de round-3). Esa sutileza es razonamiento-intensiva; delegar arriesga repetir el escape. Los fixes son <60 LOC mecánicos post-diagnóstico (análogo Carril R). Cero spawns = menos tokens que un handoff Sonnet + re-verificación, y la live-verify la exige Chris que la haga yo.

## Cómo correr

```bash
cd vitalia/frontend
# matriz round-4 (22 casos, real-backend, contraste DB)
E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-lisa-doctores/bug7-r4-dow.spec.ts --project=smoke --workers=1
# regresión round-3 (debe seguir verde)
E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-lisa-doctores/bug7-r3-*.spec.ts --project=smoke --workers=1
# unit TZ
npx vitest run src/lib/format/__tests__/calendarDates.test.ts
```
