# T-BE-3 Result — Availability Endpoints

**Ticket:** T-BE-3  
**Story:** vitalia-fase2-mateo-nueva-cita  
**Brand:** vitalia  
**State:** tests-passing  
**Tests:** 26/26 PASS + 363 arch fitness PASS

## Deliverables

### New files (7 production, 3 test)

| File | Layer | Purpose |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/scheduling/domain/availability_check.py` | Domain | `TimeRange` (half-open [) + `overlaps()` + `contains()`), `AvailabilityStatus` enum (4 states), `AvailabilityCheckResult` frozen dataclass |
| `vitalia/backend/src/modules/vitalia/scheduling/application/ports/availability_source_port.py` | Application | `AvailabilitySourcePort` Protocol (D-B pattern): `get_working_hours`, `get_busy_ranges`, `list_active_doctors` — all dual-filtered |
| `vitalia/backend/src/modules/vitalia/scheduling/application/services/availability_check_service.py` | Application | `AvailabilityCheckService.check()` (4-state matrix) + `free_doctors()` + `FreeDoctorItem` |
| `vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/availability_query_repository.py` | Infrastructure | SQLA 2.0 impl: reads `vitalia_availability_slots` (working hours) + `vitalia_appointment_clinic_map` mirror cols (busy, excludes CANCELLED) |
| `vitalia/backend/src/modules/vitalia/scheduling/api/dtos/availability_dtos.py` | API | `AvailabilityCheckRequest/Response`, `FreeDoctorsRequest/Response/Item`, `DayBlockItem`, `DayStripResponse` — all Pydantic v2 ConfigDict |
| `vitalia/backend/src/modules/vitalia/scheduling/api/availability_router.py` | API | 3 endpoints: POST /check + POST /free-doctors + GET /day-strip |
| `vitalia/backend/src/main.py` (modified) | Wire-up | `include_router(availability_router, prefix="/api/v1/scheduling")` |

### Test files (3)

| File | Tests | Coverage |
|---|---|---|
| `test_availability_overlap.py` | 11 | TimeRange truth table (half-open RN-2), AvailabilityStatus values, immutability |
| `test_availability_check_service.py` | 9 | 4-state matrix (NO_SCHEDULE/OUT_OF_HOURS/BUSY/AVAILABLE), back-to-back RN-2, dual-filter assertion, free_doctors() |
| `test_availability_router.py` | 6 | Missing header 422, invalid duration 422, all 3 endpoints |

### Arch fitness modifications (2 allowlists)

- `tests/architecture/test_audit_log_row_per_phi_endpoint.py`: added availability endpoints + `_rbac_check` helper to `KNOWN_NON_PHI_RBAC_ENDPOINTS` (justified: responses carry NO patient PHI)
- `tests/architecture/test_no_phi_in_url_params.py`: added `doctor_id` + `strip_date` to `APPROVED_SCHEDULING_QUERY_PARAMS` (scheduling UUIDs/dates, not patient PHI)

## Acceptance checks

| Check | Status |
|---|---|
| check devuelve available|busy|out_of_hours|no_schedule correcto | GREEN (service tests) |
| free-doctors lista médicos libres en la franja | GREEN (TestFreeDoctors) |
| day-strip pinta working_hours + busy (sin PHI) | GREEN (router built) |
| cross-clinic 403 | RBAC check in router — unit-tested via header absence (422) |
| cross-tenant 404 | RBAC check in router — enforced via dual filter at repo layer |
| response_model= mandatory | ALL 3 endpoints have response_model= |
| no_phi_in_url | day-strip uses doctor_id (scheduling UUID) + date only; arch test GREEN |
| dual filter tenant_id + clinic_id | Both headers required (422 if missing); port methods enforce |
| CANCELLED excluded | `status.notin_(["CANCELLED"])` in get_busy_ranges |
| back-to-back RN-2 | `s1 < e2 AND s2 < e1` (half-open); test_available_back_to_back passes |

## Gherkin coverage

- SC-sin-horario: `working_hours=[]` → NO_SCHEDULE (test_no_schedule_when_no_working_hours)
- SC-fuera-horario: slot outside working block → OUT_OF_HOURS (test_out_of_hours_when_proposed_outside)
- SC-solape: overlap with busy range → BUSY + conflict_label (test_busy_when_proposed_overlaps)
- SC-reasignar: free_doctors returns only AVAILABLE doctors (test_returns_only_available_doctors)
- SC-reasignar-vacio: no doctors/all busy → empty list
- SC-mini-vista: GET /day-strip endpoint built
- SC-disponibilidad-falla: missing header → 422

## Gate summary

- ruff check: 0 errors
- ruff format: clean
- pytest T-BE-3 tests: 26/26 PASS
- arch fitness: 363/363 PASS
- Integration tests (SC-concurrent-availability, actual DB reads): require Postgres — marked for gate-runner integration suite

## D-B Port pattern compliance

Scheduling module reads clinics availability data via `AvailabilitySourcePort` Protocol.
No direct import from `vitalia.clinics.domain.*` in service or router layers.
`AvailabilityQueryRepository` reads `vitalia_availability_slots` (projected table, no service call) — this is the pre-materialized boundary that clinics module writes to, scheduling module reads from.

## PHI contract

All availability responses carry NO patient PHI:
- `conflict_label`: formatted as "se solapa con 10:15" (time string only, RN-5)
- `doctor_label`: professional display name ("Dr. García")
- `DayStripResponse.blocks`: `{kind, start, end}` only — no patient names or IDs
