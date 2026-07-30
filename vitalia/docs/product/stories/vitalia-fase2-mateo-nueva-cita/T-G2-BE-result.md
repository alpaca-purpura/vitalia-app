# T-G2-BE-result.md · vitalia-fase2-mateo-nueva-cita

**Ticket:** G#1 round-2 fix (BE authority — no citas en el pasado)
**Date:** 2026-06-26
**Commit:** `179fdc6c`
**Branch:** `wip/vitalia` (pushed)

---

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `backend-expert` | Runtime quality checklist — anti-patterns FastAPI/SQLA/tests | utc_now() over datetime.now(), lazy import pattern for domain exceptions in service, no new migration (runtime guard) |

---

## Diff Summary

### New code (5 files, 163 insertions / 14 deletions)

**`vitalia/backend/src/modules/vitalia/scheduling/domain/exceptions.py`**
- Added `PastAppointmentError(SchedulingDomainError)`: pure Python, no framework imports, mirrors `OutOfWorkingHoursError` pattern
- Default message: `"No se pueden agendar citas en el pasado."` (Spanish neutro LatAm)

**`vitalia/backend/src/modules/vitalia/scheduling/application/services/create_appointment_service.py`**
- Added `from luana_core_platform.domain.datetime_utils import utc_now` (module-level import)
- Added Step 0a guard at the top of `create_appointment()`, before availability check and before any DB write:
  ```python
  if start_time < utc_now():
      raise PastAppointmentError()
  ```
- Semantics: `>=` now is allowed (walk-in "right now"), only strictly past is rejected

**`vitalia/backend/src/modules/vitalia/scheduling/api/agenda_router.py`**
- Added `PastAppointmentError` to import block
- Added handler: `PastAppointmentError → HTTP 422 PAST_APPOINTMENT`
- Detail: `{"error_code": "PAST_APPOINTMENT", "message": "No se pueden agendar citas en el pasado."}`

**`vitalia/backend/tests/modules/vitalia/scheduling/test_create_appointment_service.py`**
- Updated all input date fixtures from 2026 → 2027 (existing dates were now in the past, triggering the new guard)
  - `_make_create_request()`: `datetime(2026, 5, 28, ...)` → `datetime(2027, 5, 28, ...)`
  - Inline dates `datetime(2026, 6, 22, ...)` → `datetime(2027, 6, 22, ...)`
- Added `TestCreateAppointmentServicePastGuard` with 2 tests:
  - `test_past_start_time_raises_past_appointment_error` — year 2000 → `PastAppointmentError`; `repo.create.assert_not_called()`
  - `test_future_start_time_is_allowed` — year 2030 → happy path proceeds; `repo.create.assert_called_once()`

**`vitalia/backend/tests/modules/vitalia/scheduling/test_create_appointment_router.py`**
- Added `test_create_appointment_past_start_time_returns_422`:
  - Mocks `CreateAppointmentService` to raise `PastAppointmentError`
  - Asserts `resp.status_code == 422`
  - Asserts `body["detail"]["error_code"] == "PAST_APPOINTMENT"`
  - Asserts `"pasado" in body["detail"]["message"]`

---

## Gate Results

| Gate | Result | Notes |
|---|---|---|
| ruff check | PASS | "All checks passed!" |
| ruff format --check | PASS | "82 files already formatted" |
| pytest tests/modules/vitalia/scheduling/ | **22/22 PASS** | Includes 3 new tests (2 service + 1 router) |
| pytest tests/architecture/ | 361/366 | 5 pre-existing failures: `inbound_mode_seam` ×4 + `treatment_plans pgcrypto` ×1 — no new failures from this change |

---

## No-Migration Rationale

Guard is a pure runtime check (`start_time < utc_now()`). No schema change. No new column. No DDL.

---

## Scope Boundary

- Did NOT touch: `core/luana-core-*/src/`, other brands, copilot/sales_agent, availability surface (service-day/day-strip)
- `utc_now()` consumed via import from `luana_core_platform.domain.datetime_utils` (engine package, read-only consumer pattern)

---

## Pending (DAG)

- **Kit** (`SmartDateTimePicker` `disablePast` prop, 0.9.0 bump) — parallel session
- **FE** (`disablePast` on Fecha picker + Zod refine `startTime >= now` + error inline + submit disabled) — after kit closes
