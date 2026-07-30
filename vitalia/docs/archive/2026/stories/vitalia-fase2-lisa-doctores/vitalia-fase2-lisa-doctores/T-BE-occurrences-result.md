# T-BE-occurrences-endpoint — result

Ticket: D3-C BE availability-occurrences range endpoint · Builder: builder-backend (Fable 5, mandato checkpoint).
Estado: **tests-passing** (build phase — auditoría pendiente downstream).

## Diff resumen (6 archivos código + 2 docs)

| Archivo | Cambio |
|---|---|
| `vitalia/backend/src/modules/vitalia/clinics/application/recurrence_summary.py` | **NEW** — `format_recurrence_summary(block)` SSoT del resumen humano (RN-D3F-1). Pre-D3-F: "Único"/"Semanal"/"Quincenal" (+ fallback defensivo "Recurrente"). D3-F extiende AQUÍ, no forkea |
| `vitalia/backend/src/modules/vitalia/clinics/application/availability_projection_service.py` | **EXTEND** — `occurrence_dates_in_range(block, range_start, range_end, series_anchor=None)` (público) + refactor `_recurrent_occurrence_dates()` extraído de `_project_recurrent` (ÚNICO builder rrule — cero duplicación; contrato de `_project_recurrent` intacto, 12/12 tests previos verdes) |
| `vitalia/backend/src/modules/vitalia/clinics/application/availability_block_service.py` | **EXTEND** — dataclass `BlockOccurrence` + `list_occurrences()` : valida rango (to≥from, ≤62d → ValueError), repo dual-filter, colapsa a 1 ocurrencia por (block, date), ordena por (date, start_time), structlog `availability_occurrences_projected` |
| `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py` | **EXTEND** — `AvailabilityOccurrenceDTO {block_id, occurrence_date, start_time, end_time, kind, freq, pattern_summary}` (camelCase wire vía `to_camel`) + `AvailabilityOccurrencesResponse {occurrences}` |
| `vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py` | **EXTEND** — `GET /{doctor_id}/availability-occurrences?from=&to=` con `response_model=` + `response_model_by_alias=True`, headers UUID X-Tenant-ID/X-Clinic-ID/X-User-ID (consistencia useStaffActorHeaders), ValueError→422 `invalid_range`. Router ya montado en `main.py` (cero wiring nuevo — CONN ✓; consumer: T-FE-occurrences-consume `depends_on` este ticket) |
| `vitalia/backend/tests/modules/vitalia/clinics/test_availability_occurrences.py` | **NEW** — batería 26 tests SC-D3C-1..8 + rango + formatter + contrato HTTP camelCase |

## ★ Decisión clave (divergencia documentada vs sketch 03-arch-delta § 4.3)

El sketch literal `project_block(block, reference_date=from)` **reintroduce el bug server-side**:
`rrule(count=N)` con dtstart derivado del window start REINICIA la serie en cada ventana → N fechas en
TODA ventana = pintado indefinido (lo que V-D3C-1 prohíbe), y flipea la paridad quincenal (V-D3C-2).
**Implementado:** la serie ancla en `block.created_at.date()` (== reference_date usado al materializar
slots en create; estable ante edits → SC-D3C-5). `open_ended` usa horizonte rodante `hoy+90d` (bloque
viejo sigue pintando — "ni corta ni infinita", SC-D3C-4). Los validators mandan sobre el one-liner.
Tests `test_sc_d3c_1_regression_later_window_is_empty` + `test_sc_d3c_2_biweekly_off_parity_week_is_empty`
pinnean el invariante.

## RED → GREEN (TDD evidencia — detalle en T-BE-occurrences-impl-log.md § Bitácora)

1. **RED:** batería escrita ANTES de tocar src/ → `--maxfail=100` = **26/26 FAILED**
   (`AttributeError: list_occurrences` + `ModuleNotFoundError recurrence_summary` + route ausente).
2. **GREEN:** implementación inside-out (application → api) → **26/26 PASSED** (0.42s).

## Gates (G5)

| Gate | Resultado |
|---|---|
| Batería ticket | ✅ 26/26 PASSED |
| Suite módulo entera `tests/modules/vitalia/clinics/` | ✅ **322/322 PASSED** (296 previos intactos — regression_guard OK; `test_doctor_cross_tenant.py` pasó, no se tocó) |
| `ruff check` (src clinics + test nuevo) | ✅ All checks passed |
| `ruff format --check` | ✅ 42 files formatted |
| Arch fitness `tests/architecture/` | ✅ 340 passed / ⚠️ 1 failed **PRE-EXISTENTE**: `test_pgcrypto_phi_columns` (`treatment_plans.notes` TEXT→BYTEA en migración `005_vitalia_treatment_plans.py`, committed pre-ticket; el test scannea SOLO `alembic/versions/` y este diff toca 0 migrations — deuda BYTEA conocida, MEMORY cierre 2026-06-01; ticket prohíbe migrations) |
| mypy | ⚠️ binario ausente en `${WS}/.venv` — gate-runner tools-verify lo reportará |

## Skills Consulted (resumen — tabla completa en impl-log)

`backend-expert` + runtime-quality-checklist (deps inline sin type-alias Annotated; query `date` typed;
override `_get_db` sin params) · FastAPI canonical (response_model + by_alias camelCase; `Query(alias="from"/"to")`)
· pytest async (AsyncMock repo + TestClient con monkeypatch `_build_block_service` → servicio REAL) ·
graceful-degradation N/A (cero calls externos) · brand/offer/preset/metrics N/A (módulo clinics).
Rules: hipaa-lite (dual filter delegado a repo; read no-PHI sin audit row, espeja list_blocks) ·
tenant-isolation · tdd-mandatory · hotfix-repro (trace_evidence del ticket citada) · master-data (UTC).

## Commit

Pathspec-only (6 código + 2 docs story). Sin push (mandato caller). SHA en footer del builder.
