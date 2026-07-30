# T-D1 result — `GET /availability/service-day` (delta mateo nueva-cita)

**State:** tests-passing · **Commit:** `0b2adb07` (pushed `wip/vitalia`, ff `f38e0978..0b2adb07`)
**Cap:** `scheduling.mateo-agenda` · **Scope:** business-module only (scheduling) · read-only, NO migration, NO audit write.

## What was built

Read-only endpoint returning the day availability of ALL doctors of a service.
**Composes existing free/busy compute** (`get_working_hours` / `get_busy_ranges` /
`list_active_doctors`) — ZERO new free/busy SQL. Only new SQL = link resolution
(`offer_service_specialist_links`, dual-filter `tenant_id`+`offer_id`+`deleted_at IS NULL`).

`GET /api/v1/scheduling/availability/service-day?serviceId={offerId}&date=YYYY-MM-DD`
Headers `X-Tenant-ID` + `X-Clinic-ID` (dual filter) · `X-User-Role` (RBAC PHI gate) · `X-User-ID`.
PHI-safe DTO: `kind` + `start` + `end` + professional `doctor_label` only — NEVER any patient field.

## Diff (9 files, +794 / -1)

DDD Inside-Out — repo returns tuples → service composes frozen app dataclasses → router maps to DTOs (no infra→api import):

| Layer | File | Change |
|---|---|---|
| infra | `scheduling/infrastructure/repositories/availability_query_repository.py` | `get_service_day_strips` — link SELECT ∩ dual-filtered `list_active_doctors`; fallback all clinic-active when no links; reuses `get_working_hours`/`get_busy_ranges` |
| app/port | `scheduling/application/ports/availability_source_port.py` | Protocol method `get_service_day_strips` |
| app | `scheduling/application/services/availability_check_service.py` | `service_day()` + 2 frozen dataclasses `ServiceDayBlock`/`ServiceDayDoctorResult`; sorts blocks by start |
| api/dto | `scheduling/api/dtos/availability_dtos.py` | `ServiceDayDoctor` / `ServiceDayResponse` (reuse `DayBlockItem`) |
| api | `scheduling/api/availability_router.py` | `get_service_day` route mirroring `get_day_strip`; `response_model=ServiceDayResponse`; RBAC check; `INVALID_DATE` 422 |
| arch | `tests/architecture/test_no_phi_in_url_params.py` | allowlist `service_id` (offer UUID, not patient ref) + justification comment |
| test | `tests/modules/.../scheduling/_availability_seed.py` | shared real-DB seed helpers (no `test_` prefix) — doctor/slot/link/busy (FK parent appointment + clinic_map mirror, synthetic patient_id) |
| test | `tests/modules/.../scheduling/test_service_day_strips_realdb.py` | `@integration` repo seam — 7 tests (links, fallback, busy, RN-6 cancelled excl, cross-clinic + cross-tenant no-leak) |
| test | `tests/modules/.../scheduling/test_service_day_router_phi.py` | router seam — no-DB 422/403 validation (4) + real-DB 200 shape no-patient-field + cross-clinic/cross-tenant no-leak (2) |

## Gates (native, `${WS}/.venv/bin/`)

- `ruff check` 9 files → **All checks passed!**
- `ruff format --check` 9 files → **9 files already formatted**
- 13 new T-D1 tests → **13 passed** (integration ran — PG up, FK-parent seeds)
- full scheduling module suite → **285 passed**
- touched arch test `test_no_phi_in_url_params.py` → **7 passed**
- rest of arch suite (≈360 tests) → **EXIT=0, all pass**

### Pre-existing baseline failures (NOT T-D1 — proven unrelated)

Two arch failures on `wip/vitalia` baseline, neither table/module in my scheduling-only changeset:
1. `test_ep3_handlers_sync_callable.py` + `test_ep3_resolvers_wired.py` — `ModuleNotFoundError: luana_core_sales_agent.application.orchestrator.inbound_mode_seam` (sales_agent ENGINE wiring; FORBIDDEN scope, never touched).
2. `test_pgcrypto_phi_columns.py::test_no_phi_column_uses_text_or_varchar_unencrypted` — `treatment_plans.notes defined as TEXT instead of BYTEA` (treatment_plans table; no migration/model added by T-D1).

Bidirectional validator advisory SOFT_DRIFT (commit non-blocking): G10 `sales_agent.honor-mode-bridge` stale forward-decl + cross_check_4 `compliance.hipaa-lite` — both pre-existing, NOT `scheduling.mateo-agenda` (my cap clean).

## Skills consulted

- `backend-expert` (`references/runtime-quality-checklist.md`) — FastAPI Annotated deps, `response_model=`, SQLA 2.0 `select().where()`, tenant-isolation pattern, no infra→api import.
- FastAPI canonical patterns — `response_model=ServiceDayResponse` mandatory, `Header(alias=...)`, thin router → service.
- pytest async testing patterns — two seams: `@integration` + `db_session` raw `text()` seeds (auto-skip if PG down) + no-DB `AsyncClient(ASGITransport)` with `dependency_overrides[_get_db]` for header/param/RBAC 422.
- (vitalia overlay) `hipaa-lite.md` — dual filter `tenant_id`+`clinic_id`, RBAC PHI roles, no PHI in URL, read-only → no audit write.

## Forbidden-scope respected

Engine `core/luana-core-*/src` untouched · other brands untouched · `modules/vitalia/{copilot,sales_agent}` untouched · the 9 base tickets' create-path/patient-inline files untouched · existing free/busy compute reused (never mirrored) · NO migration · NO audit write (read-only).
