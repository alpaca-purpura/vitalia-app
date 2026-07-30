<!-- voseo-allowed: doc interno de proceso -->
# Gherkin verification matrix — vitalia/vitalia-fase2-lisa-doctores · bug7 rounds 4-6

> Auditor Phase D · 2026-06-15 · scope = deltas bug7 (la matriz delta-v3 base ya verificada antes).
> Ground truth INDEPENDIENTE: DB (ISODOW/excluded_dates/end_date) + geometría DOM. Real-backend, cero mocks del surface.

| Regla / Scenario | Test | Status |
|---|---|---|
| RN-D3F-4 día-de-semana (lunes pinta Lun, no Dom) | bug7-r4-dow.spec.ts (22 casos · DB ISODOW + geometría) | ✅ PASS |
| RN-D3F-4 mondayOfWeek TZ-estable | calendarDates.test.ts (6) | ✅ PASS |
| RN-D3G-1 delete scope=occurrence (excluye fecha, serie sigue) | bug7-r5-dow.spec.ts #1a + diálogo #1c | ✅ PASS |
| RN-D3G-1 delete scope=this_and_future (trunca, pasado intacto) | bug7-r5-dow.spec.ts #1b | ✅ PASS |
| RN-D3G-1 one_off borra sin diálogo | bug7-r5-dow.spec.ts #1c-one + bloque-popover-delete-scope.test.tsx | ✅ PASS |
| RN-D3G-1 confirmados nunca se borran | BE test_availability_block_scoped_delete.py | ✅ PASS |
| RN-D3G-2 no crear en pasado (FE celda deshabilitada) | bug7-r5-dow.spec.ts #2-FE + availability-calendar-past-cell.test.tsx | ✅ PASS |
| RN-D3G-2 no crear en pasado (BE 422) | BE test_availability_block_scoped_delete.py | ✅ PASS |
| RN-D3F-2 occurrences = N ciclos completos (multi-día) | bug7-r5-dow.spec.ts #R6 + bug7-r4-dow case 18 + BE test_availability_projection.py + SC-D3F-1/2 | ✅ PASS |
| RN-D3F-2 single-día sin cambio (N×1=N) | BE test_project_single_day_occurrences_unchanged | ✅ PASS |
| Resumen "N repeticiones" | recurrence-summary.test.ts (11) | ✅ PASS |
| Regresión round-3 intacta | bug7-r3-{d1,d2,d3} + horarios-occurrences-d3c + staff-week-nav | ✅ PASS (24, 1 flaky retry-OK) |

**Sin MISSING. Sin FAIL.** Verificación REAL: writes ejercidos (POST 201 / PATCH 200 / DELETE) + efecto en DB + render DOM, nunca GET 200 ni e2e mockeado.
