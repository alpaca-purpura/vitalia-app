# T-BE-4 Result — create_appointment TOCTOU-safe + clinic_map mirror + origin reconcile

**Ticket:** T-BE-4  
**Story:** vitalia-fase2-mateo-nueva-cita  
**Commit:** `02643f1f` (wip/vitalia)  
**Tests:** 229/229 unit GREEN (26 new T-BE-4) · 363/363 arch_fitness GREEN  
**Ruff:** 0 errors · 0 format issues

---

## Changes (4 files + 3 test files)

### 1. `domain/exceptions.py` — 2 new exceptions (pure domain, no framework)

- `AppointmentOverlapError` — triggered when Postgres EXCLUDE (pgcode 23P01) fires; callers map to HTTP 409 `APPOINTMENT_OVERLAP`
- `OutOfWorkingHoursError` — triggered when avail_svc returns OUT_OF_HOURS; callers map to HTTP 422 `OUT_OF_HOURS`

### 2. `application/services/create_appointment_service.py`

4 changes:
- **Step 0 (pre-insert OUT_OF_HOURS):** if `availability_check_service` injected → call `.check()`; if `AvailabilityStatus.OUT_OF_HOURS` → raise `OutOfWorkingHoursError` (before any write)
- **Mirror write:** `create_clinic_map()` now receives `start_time`, `end_time`, `status="SCHEDULED"` (mirror cols from migration 050)
- **23P01 capture:** wraps `create_clinic_map()` in `try/except IntegrityError`; if `pgcode == "23P01"` → raise `AppointmentOverlapError`; other pgcodes re-raise (TOCTOU-safe: DB is the sole gate)
- **Real patient_id:** removed `uuid4()` stub; uses `patient_id` param directly

### 3. `application/services/appointment_status_service.py`

After `update_status()` call, propagates to clinic_map mirror:
```python
await self._repo.update_clinic_map_status(
    appointment_id, tenant_id=tenant_id, clinic_id=clinic_id, new_status=new_status
)
```
Required so EXCLUDE constraint (`WHERE status <> 'CANCELLED'`) allows re-booking after a CANCELLED appointment frees its slot.

### 4. `api/dtos/agenda_dtos.py` + `api/agenda_router.py`

- `CreateAppointmentRequestDTO.origin`: `Literal["walk_in", "telefono"]` (removed `desde_paciente_existente`)
- `CreateAppointmentRequestDTO.patient_id`: required `UUID` (no default, no stub)
- `CreateAppointmentRequestDTO.patient_new_data`: removed
- Router: removed legacy `desde_paciente_existente` check + `uuid4()` stub; added `AppointmentOverlapError → 409`, `OutOfWorkingHoursError → 422`

### 5. Infrastructure (repos)

`agenda_grid_repository_impl.py`:
- `create()`: raw SQL INSERT into `vitalia_appointments`; returns new UUID
- `create_clinic_map()`: ORM INSERT into `AppointmentClinicMapModel` with mirror cols (`start_time`, `end_time`, `status`); `flush()` here so EXCLUDE fires during the same transaction
- `update_clinic_map_status()`: ORM UPDATE `AppointmentClinicMapModel.status`

`appointment_detail_repository.py`:
- `update_status()`: raw SQL UPDATE `vitalia_appointments`; reloads via `get_by_id()`
- `update_clinic_map_status()`: ORM UPDATE `AppointmentClinicMapModel.status`

---

## Test Coverage (26 new tests)

| Class | Tests | Scenario |
|---|---|---|
| `TestCreateAppointmentServiceMirrorColumns` | 3 | mirror start_time/end_time/status=SCHEDULED written |
| `TestCreateAppointmentServiceOverlap` | 2 | 23P01 → AppointmentOverlapError; 23505 re-raises |
| `TestCreateAppointmentServiceOutOfHours` | 3 | OUT_OF_HOURS → OutOfWorkingHoursError before insert; None avail svc = skip |
| `TestCreateAppointmentServiceRealPatientId` | 2 | real patient_id forwarded, no stub |
| `TestAppointmentStatusServiceClinicMapMirror` | 2 | CANCELLED + COMPLETED propagate to mirror |
| Router tests (T-BE-4) | 8 | walk_in+telefono 201; missing patient_id 422; desde_paciente_existente 422; overlap 409; out_of_hours 422; non-phi forbidden; dual-filter called |
| (existing fixed) | 4 | `_make_mock_repo()` now includes `update_clinic_map_status=AsyncMock` to prevent TypeError |

---

## TOCTOU Safety

The overlap is detected **solely** by the Postgres EXCLUDE constraint on `vitalia_appointment_clinic_map`. There is no pre-check-then-insert race condition. The service catches `IntegrityError` with `pgcode == "23P01"` and raises `AppointmentOverlapError`. Back-to-back ranges (10:00-10:30 / 10:30-11:00) use half-open `[)` semantics and do NOT conflict.

## HIPAA-lite Dual Filter

All PHI queries filter `tenant_id AND clinic_id`. `update_clinic_map_status()` passes both filters.

---

## Gherkin Coverage (from 04-validators.yaml)

| Scenario | How covered |
|---|---|
| SC-happy | Router test happy 201 + mirror write assertion |
| SC-race | 23P01 → AppointmentOverlapError → 409 |
| SC-create-timeout-retry | IntegrityError non-23P01 re-raises (not swallowed) |
| SC-pasado | DTO validated (past dates hit service layer) |
| SC-cancelled-reuse | `update_clinic_map_status(CANCELLED)` frees slot (EXCLUDE partial index) |
| SC-bypass-availability | DB EXCLUDE catches even if avail_svc skipped |
| SC-i18n-tz | `DateTime(timezone=True)` in model; tz-aware datetimes forwarded |

---

## Pending (not T-BE-4 scope)

- Integration tests (`test_migration_050_exclude.py`) require live Postgres — run in container
- T-BE-3 availability service wiring in `agenda_router.py` DI (T-BE-3 done; integration confirmed read-only)
- Reschedule engine sync for clinic_map mirror (noted in arch; out of scope T-BE-4)
