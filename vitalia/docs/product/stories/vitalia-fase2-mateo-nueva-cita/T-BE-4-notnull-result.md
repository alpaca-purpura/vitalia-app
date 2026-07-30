# T-BE-4-notnull-result — clinic_id + offer_id NOT NULL fix

**Story:** vitalia-fase2-mateo-nueva-cita  
**Ticket:** T-BE-4 (bugfix continuation — bug6b)  
**Date:** 2026-06-23  
**Branch:** wip/vitalia

---

## Root Cause

`agenda_grid_repository_impl.create()` used a raw SQL INSERT that listed 11 columns but omitted `clinic_id` and `offer_id`. Both columns are `NOT NULL` with no DEFAULT in `vitalia_appointments` (created by migration 002). Result: every `POST /api/v1/scheduling/appointments` failed with a Postgres null-constraint violation at the repo layer, surfacing as HTTP 500.

The unit tests (229/229 GREEN) never caught this because they mock `AsyncSession` and never execute the actual SQL against Postgres schema.

---

## Fix

### 1. clinic_id — threaded from X-Clinic-ID header

`clinic_id` was already extracted from the `X-Clinic-ID` header as `cid` in `agenda_router.py` (HIPAA dual-filter). It was passed to the service for audit/clinic_map but NOT forwarded to `repo.create()`. Fix: added `clinic_id: UUID` param to `AgendaGridRepositoryImpl.create()` signature and included it in the INSERT column list and bind params.

### 2. offer_id — approach (a): explicit UUID in DTO

Added `offer_id: UUID` as a required field to `CreateAppointmentRequestDTO`. The FE `nueva-cita-store.ts` holds `selectedServiceId` (= `offerId` UUID emitted by `ServicePicker.onChange({ offerId, durationMinutes })`). This is the clean contract: the real FK, not a fragile label match.

**FE change required:** the `POST /api/v1/scheduling/appointments` payload must include `offer_id: string` (UUID from `selectedServiceId`). This is a FE ticket (T-FE integration fix).

### 3. NOT NULL audit — all columns accounted for

Full NOT NULL column list for `vitalia_appointments` (no default):

| Column | Source |
|---|---|
| `clinic_id` | X-Clinic-ID header (HIPAA dual filter) |
| `doctor_id` | DTO `doctor_id` |
| `duration_minutes` | computed `(end_time - start_time).seconds // 60` |
| `offer_id` | DTO `offer_id` (new — T-BE-4) |
| `patient_id` | DTO `patient_id` |
| `slot_iso` | DTO `start_time` |
| `status` | hardcoded `'SCHEDULED'` |
| `tenant_id` | X-Tenant-ID header |

All columns now present in the INSERT.

---

## Files Modified

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/scheduling/infrastructure/repositories/agenda_grid_repository_impl.py` | Added `clinic_id: UUID`, `offer_id: UUID` params to `create()`; added both to INSERT column list + bind params |
| `vitalia/backend/src/modules/vitalia/scheduling/api/dtos/agenda_dtos.py` | Added `offer_id: UUID` (required) to `CreateAppointmentRequestDTO` |
| `vitalia/backend/src/modules/vitalia/scheduling/application/services/create_appointment_service.py` | Added `offer_id: UUID` to `create_appointment()` signature; forwarded to `repo.create()` |
| `vitalia/backend/src/modules/vitalia/scheduling/api/agenda_router.py` | Forwarded `offer_id=body.offer_id` to `service.create_appointment()` |

## Files Created

| File | Purpose |
|---|---|
| `vitalia/backend/tests/modules/vitalia/scheduling/test_migration_053_notnull_clinic_offer.py` | Regression test (6 tests): schema gate (NOT NULL verified), RED INSERTs without clinic_id/offer_id fail, GREEN full INSERT succeeds, full NOT NULL column audit |

## Files Updated (test propagation)

- `test_create_appointment_service.py` — added `offer_id=OFFER_ID` to all `create_appointment()` calls
- `test_create_appointment_router.py` — added `OFFER_ID` constant + `"offer_id": str(OFFER_ID)` to all POST bodies that reach the service
- `test_hold_expiry_sweep.py` — added `offer_id=uuid4()` to both `create_appointment()` calls in `TestCreateAppointmentServiceSlotMarking`

---

## Test Results

```
tests/modules/vitalia/scheduling/ — 242 passed, 6 warnings in 1.36s
  (excluding test_migration_050_exclude.py — pre-existing asyncpg event-loop
   isolation issue, unrelated to T-BE-4, confirmed pre-existing by stash-verify)

tests/architecture/ — 50 passed, 1 failed (pre-existing)
  FAILED test_ep3_handlers_sync_callable — luana_core_sales_agent.inbound_mode_seam
  missing module, pre-existing, unrelated to this ticket

ruff check — 0 errors (1 fixed: unused asyncpg import in migration test)
ruff format — 0 files to reformat
```

---

## What Remains (FE side)

The FE must add `offer_id` to the `POST /scheduling/appointments` payload:

```typescript
// In use-nueva-cita.ts createAppointment mutation:
offer_id: store.selectedServiceId,   // UUID from ServicePicker.onChange({ offerId })
```

`selectedServiceId` is already in `nueva-cita-store.ts` (Zustand). This is a one-line addition to the mutation payload in the existing hook.
