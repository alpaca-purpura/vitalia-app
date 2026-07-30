<!-- voseo-allowed: doc interno de proceso -->
# T-FIX-bug7-round5-result — horarios: borrado recurrente + no-crear-pasado + multi-día

> **Round 5** del bug7 (scope-delta ratificado por Chris en G round-4, AskUserQuestion 2026-06-14). Tres ítems que Chris pidió mientras verificaba el fix día-de-semana. Builders **Sonnet** (BE + FE, en paralelo, contra un contrato definido por el orquestador); el orquestador (Opus) escribió la verificación REAL-backend de integración + DB + live-verify. Consolida `T-FIX-bug7-round5-BE-result.md` + `T-FIX-bug7-round5-FE-result.md`.

## Los 3 ítems

| # | Pedido de Chris | Resolución |
|---|---|---|
| #1 | "Al eliminar un bloque repetido, preguntar: solo ese o todos los futuros" | **NUEVO** — diálogo "Solo este turno / Este y los siguientes" + migración BE de excepciones |
| #2 | "No poder crear bloques en fechas/horas pasadas; marcarlas deshabilitadas" | **NUEVO** — celdas pasadas grisadas + no-interactivas (FE) + guardia BE 422 |
| #3 | "Bloque personalizado L+X+V: el resumen dice los 3 pero solo aparece el lunes" | **YA RESUELTO por round-4** (misma raíz TZ); cerrado con regression test |

### #3 — era el mismo bug TZ de round-4
Pre-fix, `calendarWeek` quedaba anclado en martes (toISOString-drift) → la ventana de occurrences era `[mar..lun]`; para un bloque L+X+V solo el **lunes** caía dentro → solo el lunes se pintaba (el resumen leía bien los 3 días del bloque). Round-4 (ancla lunes real) ya lo arregla. Verificado: API + UI `days_of_week=[0,2,4]` → DB ISODOW `[1,3,5]` → los 3 días pintan en la MISMA semana. Test `#3` cierra el hueco del sweep de round-4 (que unía semanas y podía pasar aunque no todos aparecieran juntos).

## #1 — borrado recurrente con scope (NUEVO)

**Contrato (definido por el orquestador, implementado por ambos builders):**
```
DELETE /api/v1/vitalia/clinics/doctors/{id}/availability-blocks/{blockId}
  ?scope=series|occurrence|this_and_future  &occurrence_date=YYYY-MM-DD
Response: { deleted, preservedAppointments, scope }
  series (default, back-compat): borra todo el bloque (comportamiento previo)
  occurrence: agrega la fecha a excluded_dates; retira slots libres de esa fecha; serie sigue
  this_and_future: end_date = fecha − 1 día; retira slots libres >= fecha; bloque sigue activo
  Confirmados NUNCA se borran en ningún scope. 422 si falta occurrence_date.
```
- **BE** (commit `fe8786d4`): migración **044** `excluded_dates JSONB` (idempotente, down_rev 043); proyección (`AvailabilityProjectionService`) salta `excluded_dates` (one_off + recurrent, helper único `_is_excluded`); `exclude_occurrence()` + `truncate_from()` con audit SYNC (`doctor.availability_block_occurrence_excluded` / `_truncated`) + dual filter; DTO `scope`; router `scope`/`occurrence_date` params; DDD-limpio (router no toca `_repo`, usa `count_future_confirmed()`).
- **FE** (commit `e3c79f3a`): `useDeleteBlock({blockId, scope?, occurrenceDate?})` arma el query; recurrente → diálogo `dialog-delete-scope` (3 botones, fecha mostrada vía Intl es-419), one_off → confirmación directa (sin scope dialog); invalida `occurrencesAll` + `blocks` (calendario refresca); toast.

## #2 — no crear bloques en el pasado (NUEVO)

- **BE** (`fe8786d4`): `create_block` rechaza `one_off` con `specific_date < today` → 422 ("No puedes crear bloques en fechas pasadas."); `recurrent` con `end_date < today` → 422. (recurrente ya proyectaba solo a futuro.)
- **FE** (`e3c79f3a`): `isCellPast(dateIso,hour)` (SSoT `calendarDates`, hora local) → `DroppableCell` `data-past="true"` + `cursor-not-allowed` + `onMouseDown` no-op; `handleCellMouseDown` guard; cabeceras de día pasadas `opacity-50`. Bloques existentes en el pasado siguen pintando (solo se bloquea CREAR).

## Verificación de integración (orquestador, REAL-backend + DB)

El paso que los builders no pueden hacer (cada uno verde en aislamiento ≠ integrado — lección embudo). `bug7-r5-dow.spec.ts` (cero mocks, ground-truth = DB `excluded_dates`/`end_date`/ISODOW + geometría DOM):

| Test | Qué prueba | Result |
|---|---|---|
| #3 | multi-día [L,X,V] pinta los 3 en una MISMA semana | ✅ |
| #1a | scope=occurrence: DB excluded_dates incluye la fecha, slots de esa fecha retirados, resto intacto; FE no la pinta | ✅ 200 |
| #1b | scope=this_and_future: end_date = corte−1, slots >= corte retirados, previos intactos; FE no pinta >= corte | ✅ 200 |
| #1c-rec | UI: borrar recurrente abre `dialog-delete-scope`; "Solo este turno" → DELETE real scope=occurrence&occurrence_date | ✅ |
| #1c-one | UI: borrar one_off NO abre el diálogo de scope | ✅ |
| #2-FE | celda de semana pasada `data-past` + no abre popover; celda futura (+2 sem) sí | ✅ |

**#2-BE (422 fecha pasada)** vive en pytest del builder (`test_availability_block_scoped_delete.py` + `test_availability_blocks_api.py`), NO en e2e: provocar un 422 a propósito dispara (correctamente) el gate anti-burbuja de `base.ts`.

## Gates

- **e2e round-5: 8/8 GREEN** real-backend (`bug7-r5-dow.spec.ts`).
- **Regresión: r4 matriz 22 + r3 = 24 passed** (1 flaky case-5 reintento OK — timing geometría, conocido). El fix día-de-semana intacto.
- **BE: clinics 455/455** + ruff clean + migración 044 aplicada (`alembic current` = 044). 
- **FE: vitest 525/525** (49 files, incl. tests nuevos del builder FE) + tsc 0 + eslint 0.
- **Live-verify (orquestador):** Chrome MCP locked (browser de Chris) → render real Chromium + screenshots que MIRÉ: diálogo de scope ("¿Eliminar este bloque repetido? · Solo este turno (mié 17 jun) · Este y los siguientes · Cancelar") + semana pasada (8–14 jun) grisada. `/tmp/bug7-r5-{delete-dialog,past-cells}.png`.
- Cleanup: bloques de prueba borrados; DB final = solo los 3 bloques manuales de Chris ([0,1,3],[1],[0]), sin `excluded_dates` (intactos).

## Pre-existente (NO round-5 — flag al auditor)

- Arch test `test_pgcrypto_phi_columns::test_no_phi_column_uses_text_or_varchar_unencrypted` falla: **`treatment_plans.notes` definido como TEXT en vez de BYTEA** (módulo CRM, deuda PHI-encryption). round-4/5 NO tocaron `treatment_plans`. Es deuda de otra story (probable delta v3 / CRM). 1 failed / 353 passed en `tests/architecture/`. (`payment_intents` tenant_id fue artefacto de orden con `-x`; pasa en corrida limpia.)
- Harness: `apiDeleteBlock` de cleanup no asserta el status del DELETE → huérfanos silenciosos si `/me` 401ea (round-4 dejó 2; este round limpió OK). Robustecer (capturar X-User-ID + assert DELETE 200).

## Método (proceso)

Builders **Sonnet** en paralelo (mandato Chris token-cost): BE (migración + endpoint + guardia) + FE (diálogo + past-disable), contra contrato definido por el orquestador. El orquestador (Opus) hizo: contrato/arquitectura del delta, verificación de integración real-backend + DB, live-verify, anti-flake (#1c usa miércoles sin solape con los bloques manuales de Chris; #2-FE date-robust con semana previa/+2), cleanup, docs. #3 diagnosticado inline (repro) → cerrado sin código nuevo.

## Archivos

**BE (`fe8786d4`):** migración 044 + `availability_block_model.py` + `domain/availability_block.py` + `availability_projection_service.py` + `ports/availability_repo_port.py` + `availability_block_repository.py` + `availability_block_service.py` + `api/dtos.py` + `api/doctors_router.py` + tests (`test_availability_block_scoped_delete.py` nuevo + extiende suites). Detalle: `T-FIX-bug7-round5-BE-result.md`.
**FE (`e3c79f3a`):** `api/staff.ts` + `BloquePopover.tsx` + `AvailabilityCalendar.tsx` + tests (vitest). Detalle: `T-FIX-bug7-round5-FE-result.md`.
**e2e/docs (orquestador):** `bug7-r5-dow.spec.ts` (nuevo) + `bug7-r4-helpers.ts` (apiDeleteScoped + dbBlockMeta) + este doc + checkpoint.

## Cómo correr

```bash
cd vitalia/frontend
E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-lisa-doctores/bug7-r5-dow.spec.ts --project=smoke --workers=1
cd ../backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/clinics/ -q
```
