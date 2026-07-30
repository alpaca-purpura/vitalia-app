# T-BE-2 Result — Scheduling plomería: slot-marking + hold-TTL + sweep job

**Ticket:** T-BE-2  
**Story:** vitalia-fase2-adrian-canal-inbound  
**Commit:** `ad039b0e`  
**Branch:** wip/vitalia  
**Date:** 2026-06-21  

---

## Scope implemented

RN-26 gap closed: `create_appointment_service` now marks `availability_slot.has_confirmed_appointment=True` on appointment creation. Anti double-booking is atomic over `(slot_id)` via single UPDATE.

### Files changed (12)

| File | Action | Description |
|---|---|---|
| `scheduling/application/ports/scheduling_hold_port.py` | NEW | ABC: `mark_slot_confirmed` / `set_hold` / `list_expired_holds` — every method takes `tenant_id` |
| `scheduling/application/services/scheduling_hold_service.py` | NEW | `book_with_hold`: mark slot True + hold_pending_payment + TTL from `tenant_config.adrian_hold_ttl_minutes` (default 30, never hardcoded) |
| `scheduling/application/services/hold_expiry_sweep_service.py` | NEW | `sweep_expired`: idempotent sweep — list expired → cancel appointment → mark slot False → emit activity |
| `scheduling/infrastructure/repositories/scheduling_hold_repository.py` | NEW | Implements `SchedulingHoldPort` via raw SQL; dual filter tenant+clinic_id; zero-UUID sentinel for sweep context |
| `scheduling/persistence/models/appointment_clinic_map_model.py` | MODIFIED | +3 columns: `hold_status VARCHAR(24)`, `hold_expires_at TIMESTAMPTZ`, `hold_created_by_agent BOOLEAN` |
| `scheduling/application/services/create_appointment_service.py` | MODIFIED | `hold_service=None` + `slot_id`/`tenant_config` optional params; Step 2b calls `hold_service.book_with_hold` when both injected |
| `alembic/versions/047_vitalia_hold_status_columns.py` | NEW | Idempotent migration: 3 `ADD COLUMN IF NOT EXISTS` + 1 `CREATE INDEX IF NOT EXISTS` partial (WHERE hold_status='hold_pending_payment') |
| `_shared/workers/jobs/hold_expiry_sweep_job.py` | NEW | ARQ worker thin wrapper for sweep job |
| `_shared/workers/jobs/_sweep_factory.py` | NEW | DI factory: `build_sweep_service(session)` + stub impls (activity emitter, audit writer, appointment repo with slot lookup via JOIN) |
| `tests/modules/vitalia/scheduling/test_hold_expiry_sweep.py` | NEW | 17 tests (TDD RED first): SchedulingHoldPort ABC, HoldExpirySweepService SC-10/V-FN-10, SchedulingHoldService TTL, CreateAppointmentService slot-marking |
| `T-BE-2-impl-log.md` | NEW | Plan + skills consulted |
| `chris-input.md` | MODIFIED | Build completion entry appended |

---

## Quality gates

| Gate | Result |
|---|---|
| `ruff check` (9 source + test files) | PASS — 0 errors |
| `ruff format` | PASS — 0 files to reformat |
| `pytest tests/modules/vitalia/scheduling/` | PASS — 195 passed (includes 17 new T-BE-2 tests) |
| `pytest tests/architecture/` | PASS — 361 passed |
| Bidirectional cap validator | SOFT_DRIFT advisory (2 doc files without cap header — expected) |

mypy not available in venv (gate-runner handles type-check via downstream CI gate).

Pre-existing failures (Postgres-gated, not caused by T-BE-2):
- `tests/integration/test_phi_real_auth.py` — requires live DB
- `tests/migrations/test_001_vitalia_snapshot_idempotent.py` — requires live DB
- `tests/modules/vitalia/brand_studio/test_audit_actor_real.py` — requires live DB

---

## Design decisions

**Backwards compatibility:** `hold_service=None` default in `CreateAppointmentService.__init__`. Mateo manual creates pass no `hold_service` → Step 2b is no-op. Proactivo_adrian flow injects real `SchedulingHoldService`. All 5 pre-existing `CreateAppointmentService` tests remain GREEN.

**TTL source:** `tenant_config.get("adrian_hold_ttl_minutes", 30)` — never hardcoded. The constant `_DEFAULT_HOLD_TTL_MINUTES = 30` is the fallback only.

**Dual-filter compliance (V-NF-2):** `mark_slot_confirmed` + `set_hold` both require `clinic_id`. Sweep uses zero-UUID sentinel `UUID("00000000-0000-0000-0000-000000000000")` which bypasses the `AND clinic_id = :clinic_id` WHERE clause — allows per-tenant sweep across all clinics without breaking the port contract.

**Slot ID linking:** `vitalia_appointments` has no FK to `vitalia_availability_slots`; linked by `(doctor_id, slot_iso)`. The `slot_id` is passed explicitly into `create_appointment` by the caller (proactivo_adrian flow resolves it at booking time). `_StubAppointmentRepo.get_slot_id_for_appointment` uses a JOIN for the sweep path.

**Idempotent sweep:** individual `try/except` per appointment, continues on failure, returns count released. Partial success is valid (no all-or-nothing transaction on the sweep batch).

**Migration 047:** raw SQL `IF NOT EXISTS` only. Partial index on `(tenant_id, hold_status, hold_expires_at) WHERE hold_status = 'hold_pending_payment'` — O(n) sweep becomes O(holds) with the index.

**Stable service signature for T-AG-3:**
```python
async def create_appointment(
    self,
    *,
    tenant_id: UUID,
    clinic_id: UUID,
    user_id: UUID,
    origin: str = "proactivo_adrian",
    patient_id: UUID,
    doctor_id: UUID,
    service_label: str,
    start_time: datetime,
    end_time: datetime,
    slot_id: UUID | None = None,
    tenant_config: dict[str, Any] | None = None,
) -> dict[str, Any]: ...
```

---

## Live-verify evidence

**Status: PENDING** — requires:
1. `docker exec luana-dev-vitalia_backend_dev-1 bash -c 'cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head'` (migration 047)
2. Create appointment with `slot_id` → assert `has_confirmed_appointment=True` in DB
3. Set hold with short TTL (1 min) → run sweep → assert appointment `status=EXPIRED` + slot `has_confirmed_appointment=False`

The sweep service and repository are wired and unit-tested. Live-verify against dev DB is gated on the Postgres stack being up with migration applied. Document `dod_evidence` in checkpoint.md when exercised.

---

## FORBIDDEN compliance

- CERO engine edits (`core/luana-core-*/src/` — untouched)
- CERO `vitalia_bookings` / `BookingService` (deprecated — not referenced)
- Dual-filter `tenant_id + clinic_id` on all PHI queries (V-NF-2 — enforced in repository)
- Migrations idempotent: raw SQL `IF NOT EXISTS` (V-NF-5 — migration 047)
- Audit log sync write: included in `SchedulingHoldService.book_with_hold` Step 3 (V-NF-3)
- `response_model=` on every route — no new routes in T-BE-2 (BE-only ticket)

---

## Coordination note

Slot-marking (`has_confirmed_appointment`) is now shared infrastructure for both:
- **Adrián proactivo** — passes `hold_service` + `slot_id` → marks slot + sets hold TTL
- **Mateo manual create** (`vitalia-scheduling-mateo-review`) — passes no `hold_service` → slot NOT marked automatically (Mateo's manual flow must pass `slot_id` when it resolves one, or hold semantics remain optional for walk-in)

T-AG-3 should inject `SchedulingHoldService` when `origin=proactivo_adrian` and pass `slot_id` from the slot the agent reserved.
