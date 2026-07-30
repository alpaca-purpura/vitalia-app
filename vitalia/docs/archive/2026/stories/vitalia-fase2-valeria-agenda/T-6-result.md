# T-6 Result — BE API agenda_router (5 endpoints)

**Ticket:** T-6 — BE API agenda_router (GET grid + aggregates + detail + POST create + PATCH status)
**Story:** vitalia-fase2-valeria-agenda
**Branch:** wip/vitalia
**State at commit:** tests-passing

## Summary

5 FastAPI endpoints implemented per 03-arch § 5 with full HIPAA-lite compliance:

| Endpoint | Response model | Auth | Audit |
|---|---|---|---|
| GET /api/v1/scheduling/agenda/grid | AgendaGridResponseDTO | ALLOWED_PHI_ROLES | suspicious_request if PHI params |
| GET /api/v1/scheduling/agenda/aggregates | AgendaAggregatesResponseDTO | ALLOWED_PHI_ROLES | none (PHI-free) |
| GET /api/v1/scheduling/appointments/{id} | AppointmentDetailDTO | ALLOWED_PHI_ROLES | sync pre-response |
| POST /api/v1/scheduling/appointments | AppointmentDetailDTO | ALLOWED_PHI_ROLES | sync via service |
| PATCH /api/v1/scheduling/appointments/{id}/status | AppointmentDetailDTO | ALLOWED_PHI_ROLES | sync via service |

## Files created/modified

### New files

- `vitalia/backend/src/modules/vitalia/scheduling/api/agenda_router.py` — 5 endpoints
- `vitalia/backend/src/modules/vitalia/scheduling/api/_date_utils.py` — compute_date_range(view, date_str) helper
- `vitalia/backend/src/modules/vitalia/scheduling/api/dtos/__init__.py` — package init
- `vitalia/backend/tests/modules/vitalia/scheduling/test_phi_url_protection.py` — A1 (6 tests)
- `vitalia/backend/tests/modules/vitalia/scheduling/test_dual_filter_clinic_isolation.py` — A2 (4 tests)
- `vitalia/backend/tests/modules/vitalia/scheduling/test_audit_log_drawer.py` — A3 implied (4 tests)
- `vitalia/backend/tests/modules/vitalia/scheduling/test_create_appointment_router.py` — A4 (6 tests)
- `vitalia/backend/tests/modules/vitalia/scheduling/test_patch_status_router.py` — A3 (8 tests)

### Modified files

- `vitalia/backend/src/modules/vitalia/scheduling/api/dtos/agenda_dtos.py` — removed T-8 DTOs (belong to notify_dtos.py)
- `vitalia/backend/src/main.py` — registered agenda_router at /api/v1/scheduling

## Skills consulted

| Skill | Why | Decision taken |
|---|---|---|
| `backend-expert` | Runtime quality checklist: SQLA 2.0, tenant isolation, response_model, async patterns | No `session.query()`, no `Column()`, all routes have `response_model=` |
| `tessl__fastapi` | Annotated deps, response_model, async lifespan, redirect_slashes | Used `Depends(_get_db)`, `redirect_slashes=False` confirmed in main.py |
| `tessl__pytest-api-testing` | httpx AsyncClient, DI override, factory fixtures, mocking services | `dependency_overrides[_get_db]`, `patch()` service constructors |
| `vitalia/.claude/rules/hipaa-lite.md` | PHI dual filter, audit log mandatory, cross-clinic 404 | `ALLOWED_GRID_PARAMS` whitelist, sync AsyncAuditWriter, 404 not 403 for cross-clinic |

## Security decisions (HIPAA-lite)

- **Cross-clinic = 404** (NOT 403): Router catches `AppointmentNotFoundError` → HTTP 404. Returning 403 would confirm existence — HIPAA-lite substrate.
- **PHI URL param whitelist**: `ALLOWED_GRID_PARAMS = frozenset(["view", "date", "preset_filter"])`. ANY unknown param → `suspicious_request` audit row written sync + HTTP 400.
- **RBAC gate fires first**: ALLOWED_PHI_ROLES = `frozenset(["valeria_assistant", "doctor", "nurse", "admin_clinic"])`. Non-PHI role → 403 before any other processing.
- **Audit writer per-request**: `AsyncAuditWriter(session=db)` constructed inside each route handler, passed to service.
- **PHI field detection patterns**: 9 regex patterns guard against patient_name, patient_dni, patient_phone, diagnosis, medication, etc. in URL query params.

## T-8 coordination

`notify_router.py` (T-8) was already built as a separate file. Removed duplicate `SendNotificationRequestDTO` and `NotifyResponseDTO` from `agenda_dtos.py` (those DTOs live in `notify_dtos.py`). Both routers registered in `main.py` at `/api/v1/scheduling`.

## Test results

| Suite | Result |
|---|---|
| test_phi_url_protection.py | 6/6 PASS |
| test_dual_filter_clinic_isolation.py | 4/4 PASS |
| test_audit_log_drawer.py | 4/4 PASS |
| test_create_appointment_router.py | 6/6 PASS |
| test_patch_status_router.py | 8/8 PASS |
| All scheduling tests | 158/158 PASS |
| Architecture fitness | 270/270 PASS |
| ruff check | 0 errors |
| ruff format | 0 files to reformat |

## Acceptance criteria verification

| AC | Description | Status |
|---|---|---|
| A1 | GET /agenda/grid PHI URL params rejected + suspicious audit row | PASS (test_phi_url_protection) |
| A2 | Cross-clinic query returns 404 + audit written | PASS (test_dual_filter_clinic_isolation) |
| A3 | PATCH status emits status_change audit row with from→to | PASS (test_patch_status_router) |
| A4 | POST create emits create_appointment audit row + persists clinic_map | PASS (test_create_appointment_router) |
| A5 | response_model= en cada endpoint | PASS (arch test test_response_model_required.py) |

## Out of scope (per 06-tickets.yaml)

- Charge router (T-7) — separate ticket
- Notify router (T-8) — already built, registered in this PR
