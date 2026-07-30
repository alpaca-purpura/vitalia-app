<!-- voseo-allowed: doc interno de proceso -->
# T-FIX-bug7-round3-result — staff/horarios clon Google Calendar

> **Round 3** del bug7 (`regression_2026-06-12_bug7`) ejecutado por `/dev-team` en conversación fresca según `WORK-ORDER-bug7-round3.md`. **Método**: Playwright REAL-BACKEND (fixtures `base.ts`/`authed-runtime.ts`, cero mocks del surface availability), RED primero, fix, GREEN, live-verify #37 ejercida por el propio dev-team (logs BE + DB audit). 2026-06-12.

## Veredicto

**Los 3 defectos de Chris (D-1/D-2/D-3) reproducidos, fixeados y verificados con la matriz completa de 15 casos contra el stack real.** Se destaparon **8 root causes** (5 más de los 3 esperados) — el más gordo no estaba en el work-order: el calendario pintaba TODOS los bloques con **doble offset vertical**.

## Root causes (8) + fixes

| # | Defecto | Root cause | Fix |
|---|---|---|---|
| RC1 | D-1 botón Guardar invisible | `bg-[--agent-lisa]` (BloquePopover:1015) + `border-[--agent-lisa]` (BioRepoInputs:465) — shorthand Tailwind v3 muerto en v4.1 → sin background | token classes `bg-agent-lisa` / `border-agent-lisa` |
| RC2 | **D-2/D-3 · DOBLE OFFSET de pintado** (no estaba en el work-order) | El wrapper del occurrence setea `top/height` Y `CalendarBlock` adentro volvía a sumar el MISMO `top` → bloque 08:00-13:00 pintaba en 09:00-14:00, 09:00-14:00 en 11:00-16:00. Hitboxes corridas → clicks/drags aterrizaban en bloques invisibles → "sale el popup (de edición) solo" | `CalendarBlock` ahora `inset-y-0` dentro del wrapper (posiciona solo el wrapper) |
| RC3 | D-2 drag-create muere sobre bloques | Drag por `mouseenter`/`mouseup` POR CELDA — el overlay de bloques (`pointer-events-auto`) traga los eventos de las celdas debajo | Drag por **coordenadas** (window `mousemove`/`mouseup` + `hourFromClientY` contra el rect de la columna) + `preventDefault` + `select-none`. GCal parity: el drag iniciado en celda vacía ATRAVIESA bloques existentes, soltar en cualquier lado finaliza, drag inverso normaliza, click simple = 1h |
| RC4 | D-3 "no guarda" (1/3) | Mutations create/update/delete invalidaban SOLO `staffKeys.blocks` — el calendario pinta de `occurrences` (delta v3) → el bloque guardado no aparecía sin reload | invalidación `staffKeys.occurrencesAll(doctorId)` en las 3 mutations |
| RC5 | D-3 "no guarda" (2/3) — calendario vacío | GET occurrences exige Header `X-User-ID` UUID; la query disparaba ANTES de que `/iam/users/me` resolviera → `X-User-ID: ""` → **422** → query en error permanente → calendario pintaba vacío | `enabled` gate: la query espera `clinicId` + `X-User-ID` |
| RC6 | D-3b editar one_off | FE era un **no-op con `toast.success` mentiroso** ("No-op: one_off edits not supported"); el BE SÍ soporta PATCH one_off | PATCH real `{kind:"one_off", start_time, end_time, specific_date}` |
| RC7 | D-3 editar CUALQUIER bloque | BE serializa times `"HH:mm:ss"`; el Zod schema exige `"HH:mm"` → editar un bloque existente fallaba validación EN SILENCIO (PATCH nunca salía) | normalización `hhmm()` en `buildDefaultValues` |
| RC8 | **Toasts del app = no-ops** (sistémico) | `<Toaster/>` de sonner **NUNCA estuvo montado** en ningún layout → `toast.success/error` de TODO el app (lisa/adrian/mateo) no renderizaban nada. **El fix de feedback del round-1 (f85c8ce2) era inoperante live** — por eso Chris siguió sin ver nada | mount `<Toaster position="bottom-right" richColors/>` en `app/layout.tsx` |

## Evidencia RED (pre-fix, corrida por mí)

- D-1: `bug7-r3-d1-save-button.spec.ts` RED — `backgroundColor` transparente light+dark.
- D-2: `bug7-r3-d2-drag-create.spec.ts` "drag ATRAVESANDO un bloque existente" RED contra el código pre-fix (git stash temporal): el gesto terminaba en popover "**Editar bloque**" — exactamente el "sale el popup solo" de Chris. Evidencia: `test-results/.../error-context.md` + screenshot que reveló el doble offset (RC2).
- D-3: matriz RED — toasts inexistentes (RC8), bloque no aparecía tras crear (RC4), GET occurrences 422 (RC5), PATCH nunca salía (RC7), one_off edit sin PATCH (RC6).

## Matriz 15 casos — GREEN real-backend

`bug7-r3-d3-matrix.spec.ts` (casos 1-14) + `bug7-r3-d1-save-button.spec.ts` (caso 15) + `bug7-r3-d2-drag-create.spec.ts` (drag×4):

| # | Caso | Resultado |
|---|---|---|
| 1 | Click simple → "No se repite" → Crear | ✅ POST `one_off` **201** (★ primer one_off de la historia en logs) · specific_date exacto · NO aparece otra semana |
| 2 | Drag 9-12 → "No se repite" | ✅ one_off 09:00-12:00 exacto |
| 3 | Weekly open_ended | ✅ interval=1 · semana actual + siguiente |
| 4 | "Todos los días" | ✅ days_of_week=[0..6] · semana siguiente pinta 7/7 |
| 5 | "Cada 2 semanas" | ✅ interval=2 · semana+1 VACÍA · semana+2 pintada |
| 6 | Personalizado L+J interval=2 occurrences=8 | ✅ payload exacto · resumen "Se repite cada 2 semanas los lunes y jueves, 8 veces" · proyección BE corta en 8 (GET real 12 semanas) |
| 7 | Termina en fecha | ✅ end_date INCLUSIVO (último sábado pinta) · semana+2 no |
| 8 | occurrences=2 | ✅ EXACTO 2 semanas · tercera vacía (regresión D3-C) |
| 9 | Editar recurrente | ✅ PATCH **200** · calendario actualiza sin reload (RC7) |
| 9b | Editar one_off | ✅ PATCH **200** (RC6 — antes no-op) |
| 10 | Eliminar | ✅ DELETE **200** · desaparece sin reload |
| 11 | Validación (occurrences vacío) | ✅ toast "Revisa los campos del bloque" · **0 POST** · popover abierto |
| 12 | Error server real (end<start → BE 422) | ✅ toast "No pudimos guardar el bloque" · popover abierto |
| 13 | Toast success en creates | ✅ "Bloque guardado" (asertado en 1/2/3) — funcionaba recién tras RC8 |
| 14 | Vista mes | ✅ `month-chip-{fecha}-{id}` visible en MonthCalendar |
| 15 | Botón visible ambos themes | ✅ computed-style alpha>0 + ≠ fondo popover, light Y dark (`data-theme`) · screenshots `/tmp/bug7-r3-d1-{light,dark}.png` |

## Gates

- e2e story suite COMPLETA (`e2e/regression/vitalia-fase2-lisa-doctores/`): **45 passed · 0 failed · 2 skipped** (los 2 skip = `test.fixme` pre-existentes de live-seed). Nota: "drag ATRAVESANDO" fue flaky 1 vez en una corrida (timing de mouse) — pasó limpio en la corrida final completa.
- Vitest `src/features/lisa/`: **509/509** (incl. `horarios.test.tsx`, `month-calendar.test.tsx`, `bloque-popover-save.test.tsx` 3/3, nuevo `hour-from-client-y.test.ts` 5/5).
- `tsc --noEmit`: 0 · `eslint` src tocados + e2e: **0 errors** (fix mecánico: 3 vars muertas pre-existentes en `horarios-occurrences-d3c.spec.ts`).
- Suites previas del surface intactas: `horarios-occurrences-d3c` 3/3 · `staff-week-nav-oneoff` · vista mes (caso 14 + month-calendar.test 23/23). DndContext NO removido (scope discipline).

## Live-verify #37 (ejercida por mí — logs + DB)

- BE logs (`docker logs luana-dev-vitalia_backend_dev-1`): `POST /availability-blocks → 201` repetidos **incluyendo `kind=one_off`** (`availability_block_created ... kind=one_off slots_materialized=2`) · `PATCH → 200` (recurrent y one_off: `availability_block_updated kind=one_off new_slots=4`) · `DELETE → 200` con `availability_block_deleted` · el único 422 de blocks = caso 12 (provocado).
- PHI audit (HIPAA-lite, DB real): `vitalia_audit_log` → **63 rows `doctor.availability_block_created` + 62 `doctor.availability_block_deleted`** en la ventana de la corrida (write sync pre-response).
- Cleanup: TODOS los bloques creados por los tests borrados vía DELETE real (verificado en DB: solo quedan los 3 bloques manuales de Chris del round-2, ahora pintando en su posición CORRECTA). 1 huérfano de una corrida intermedia (cleanup 422 por race de /me en el helper — robustecido con captura de X-User-ID) se limpió manualmente.

## Archivos tocados

**Producto (5):** `app/layout.tsx` (Toaster) · `features/lisa/api/staff.ts` (occurrencesAll + invalidaciones + enabled gate + UpdateBlockPayload) · `horarios/AvailabilityCalendar.tsx` (doble offset + drag coordenadas + hourFromClientY + select-none) · `horarios/BloquePopover.tsx` (token class + one_off PATCH + hhmm) · `perfil/BioRepoInputs.tsx` (token class).
**Tests (6):** `__tests__/hour-from-client-y.test.ts` (new) · e2e `bug7-helpers.ts` + `bug7-r3-d1-save-button.spec.ts` + `bug7-r3-d2-drag-create.spec.ts` + `bug7-r3-d3-matrix.spec.ts` (new) · `horarios-occurrences-d3c.spec.ts` (vars muertas).

## Decisiones de proceso

- **Builders Sonnet (mandato)**: este round fue fix-loop diagnóstico-intensivo; el round-2 falló exactamente por indirection sin verificación propia. Los fixes son <120 LOC mecánicos POST-diagnóstico (análogo Carril R) — los apliqué inline y corrí TODO yo mismo, que es la exigencia central del work-order ("NADA se declara arreglado sin que VOS lo ejerzas"). Cero spawns de builder = menos tokens que un handoff Sonnet + re-verificación.
- RC8 (Toaster) es **sistémico** (adrian/mateo también emiten toasts a la nada hasta este fix) — candidato a nota cross-feature en el auditor.

## Cómo correr

```bash
cd vitalia/frontend
E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-lisa-doctores/bug7-r3-*.spec.ts --project=smoke --workers=1
```
