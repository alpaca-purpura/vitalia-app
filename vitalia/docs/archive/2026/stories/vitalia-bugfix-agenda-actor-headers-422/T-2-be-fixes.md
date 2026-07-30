# T-2 — BE fixes: agenda RBAC (owner) + repo SQLA-2.0 crash + audit-commit

**Story:** vitalia-bugfix-agenda-actor-headers-422
**Ticket:** T-2 (Carril R fix-and-own, bugfix lite, TDD)
**Brand:** vitalia
**Scope:** `vitalia/backend/src/modules/vitalia/scheduling/` only. No core, no FE, no other modules/brands.
**State:** tests-passing + live-verified.

The FE 422 fix (T-1) made actor headers reach the service. Two ratified bugs surfaced
(403 RBAC, 500 repo crash) + a THIRD bug surfaced via the ratified live-verify of the
audit row (audit never persisted because the endpoint used a non-committing session).

---

## Bug 1 — 403 RBAC: clinic `owner` denied (Chris ratified: add `owner`)

**Root cause:** `agenda_router.py::ALLOWED_PHI_ROLES` = `{valeria_assistant, doctor, nurse, admin_clinic}` — no `owner`. The clinic owner (`user_tenants.role = owner`) got 403 on their own agenda. The same frozenset was DUPLICATED in `notify_router.py::_PHI_ROLES`.

**Fix (single SSoT):**
- New `scheduling/api/rbac.py::SCHEDULING_PHI_ROLES` = `{owner, admin_clinic, doctor, nurse, valeria_assistant}` — the single source of truth for scheduling PHI-access roles.
- `agenda_router.ALLOWED_PHI_ROLES` and `notify_router._PHI_ROLES` now both re-export `SCHEDULING_PHI_ROLES` (no divergent duplicate). Adding/removing a role = one edit.
- notify_router 403 message generated from the frozenset (was a hardcoded stale list).
- Dual-filter (tenant+clinic), PHI masking, audit log NOT weakened — they remain enforced at the repo/service layer for every role. `owner` is gated for ACCESS only.

**TDD:** `test_agenda_rbac_owner.py` — RED (owner→403) → GREEN. Covers: owner→200, disallowed role (marketing)→403, the 4 existing clinical roles still allowed, SSoT identity (`agenda_router.ALLOWED_PHI_ROLES is SCHEDULING_PHI_ROLES` and same for notify), owner allowed on notify router.

---

## Bug 2 — 500 repo crash: `'TextClause' object has no attribute 'selectable'`

**Exact broken construct** (`agenda_grid_repository_impl.py` `list_slots` ~line 239-285 + `get_by_id` ~line 110, and the identical pattern in `appointment_detail_repository.py::get_by_id`):

```python
select(text("va.id AS ..."), ...)
    .select_from(text("vitalia_appointments va"))   # raw text() FROM
    .outerjoin(AppointmentClinicMapModel, text(...))  # ORM-model join target
    .outerjoin(AppointmentPaymentModel, text(...))
```

**Why it crashed at COMPILE time (before the DB):** mixing a `text()` `select_from` with ORM-model join targets makes the statement ORM-enabled. The ORM compile path `ORMSelectCompileState._create_orm_context` → `_normalize_froms` iterates `select_statement._from_obj` (populated by `select_from(text(...))`) and reads `info.selectable` on each entry. A `TextClause` has no `.selectable` → `AttributeError`. (Reproduced verbatim; see RED test below.) The f-strings also interpolated UUIDs directly (SQL-injection surface) and the SQL referenced columns that **don't exist** in the real schema (`patient_name_masked`, `dni_masked`, `summary`).

**Fix (idiomatic SQLA 2.0):** rewrote each broken statement as a single parameterized `text()` statement:
- Dual filter `tenant_id` + `clinic_id` + date range + ids as **bound params** (`bindparam(...)`) — kills the f-string injection surface, keeps HIPAA-lite dual filter.
- Projects only columns that EXIST in the real `vitalia_appointments` schema (verified against `vitalia_dev` + `vitalia_test`): `id`, `patient_id`, `doctor_id`, `slot_iso`, `duration_minutes`, `status`, `payment_status`, `origin`, `currency` + JOINed `map.service_label/origin/currency_override` + `SUM(pay.amount)`.
- Router-aligned aliases (`appointment_id`, `start_time`, `end_time`, `appointment_status`, `service_label`, `balance_amount_cents`) so the router DTO mapper no longer KeyErrors on `start_time`/`end_time` (the old repo returned `start_at`/`end_at`).
- Preset-filter branches kept as static SQL (no user input); doctor filter bound as param.
- LEFT OUTER JOIN to `vitalia_appointment_clinic_map` + `vitalia_appointment_payments` preserved (03-arch A12).

**PHI name/DNI:** projected as masked placeholder `'—'`. `vitalia_appointments` has NO name column, and the patient name/DNI live encrypted (`bytea`, pgcrypto) in `vitalia_patients`. The grid never carries raw PHI. Real masked-name resolution from the encrypted source needs pgcrypto decryption + a patient JOIN — that is feature scope, not this bugfix (see § Upstream deficiency).

**TDD:** `test_agenda_grid_repository_compiles.py`:
- `TestAgendaGridStatementCompiles` (pure unit, no Postgres) — a `_CompileCaptureSession` calls `str(stmt.compile(...))` on execute(), exactly reproducing the production AttributeError RED → GREEN. Covers `list_slots` + `get_by_id` + every preset branch + dual-filter-still-required guard.
- `TestAgendaGridExecutesAgainstRealSchema` (`@integration`, `vitalia_test` :5435) — executes the real query → returns `list` (empty, seed-free DB) without `AttributeError` or `UndefinedColumn`, proving every projected column exists.

Also fixed the identical crash + schema mismatch in `appointment_detail_repository.py::get_by_id` (same module, same root cause, reached by the FE drawer `GET /appointments/{id}`) — consistent per Chris's "aplicá consistente". `_get_payments` already used proper `select(Model)` (untouched).

---

## Bug 3 (surfaced by ratified live-verify) — audit row never persisted

**Root cause:** `agenda_router._get_db` used `get_async_session` which NEVER commits ("caller responsible"). `AgendaGridService` writes the mandatory `appointment.agenda_read` audit row (hipaa-lite.md § Audit log: sync write pre-response), but the INSERT was flushed-then-rolled-back at session close → HTTP 200 with NO audit row. This was hidden by the 403 (Bug 1) then 500 (Bug 2) — the request never reached the audit write before. Chris explicitly asked to "confirmá que el audit log row se escribió" — that check exposed it. Same class as the documented CRM fix that created `get_async_session_committing`.

**Fix:** `_get_db` now uses `get_async_session_committing` (commits on clean return, rolls back on error). The `suspicious_request` security audit (400 path) now `await db.commit()` explicitly before the caller raises HTTP 400, so it survives the committing-dependency's rollback-on-exception. No new infra — uses the existing brand-local `src.db` factory.

---

## Gate status

| Gate | Result |
|---|---|
| RED tests reproduce bugs | ✅ Bug 1 (owner→403), Bug 2 (`TextClause` AttributeError verbatim) |
| `ruff check` (scheduling src + tests) | ✅ All checks passed |
| `ruff format --check` (scheduling) | ✅ 58 files already formatted |
| `mypy` | ⚠️ not installed in this venv (`No module named mypy`) — gate-runner gate 5 to run |
| scheduling suite (`pytest tests/modules/vitalia/scheduling/`) | ✅ 173 passed, 0 failed |
| scheduling + crm suites | ✅ 499 passed |
| arch fitness (`tests/architecture/`) | ✅ 353 passed (1 deselected = pre-existing CRM `treatment_plans.notes` pgcrypto debt, unrelated, out of scope) |
| HIPAA-lite gates (dual_filter, audit_log_sync_write, audit_log_row_per_phi, response_model) | ✅ 26 passed |
| Live request (dev stack :8002, real seed tenant/clinic/owner) | ✅ see below |

## Live verification (dev stack :8002, real seed data = exact repro)

tenant `e69a691d-070e-5caf-a053-6e74642ec100`, clinic `f035be5b-0ac4-5210-8fc3-395650ca2b83`, owner user `527050c3-1b2b-5e4f-b85d-394bbd0b796d`:

- `GET /agenda/grid` **owner → HTTP 200** (was 403 pre-Bug1, 500 pre-Bug2). Body: valid grid `slots:[]` (DB has 0 seed appointments → correct empty-without-crash).
- `GET /agenda/grid` **doctor → HTTP 200**; **recepcion → HTTP 403** (`PHI_RBAC_DENIED`).
- `appointment.agenda_read` audit row **PERSISTED** in `vitalia_audit_log` (user_id = owner, occurred_at set).
- `GET /agenda/grid?...&diagnosis=test` → **HTTP 400** + `suspicious_request` audit row **PERSISTED** (survives the 400 rollback).
- `GET /agenda/aggregates` owner → **HTTP 200**.

## Upstream deficiency (Carril R — responsabilizar upstream)

The repos shipped with an **imagined schema**: the SQL referenced `vitalia_appointments.patient_name_masked / dni_masked / summary` columns that the migrations (`002_vitalia_appointments_columns.py`, `032_f2_s1_vitalia_agenda.py`) never create. The architect's 03-arch § 2.2 documents a "patient_name_masked computed column" that does not exist; the patient name lives encrypted in `vitalia_patients`. Real masked-name on the grid (decrypt pgcrypto bytea + JOIN patients) is a follow-up FEATURE, not this bugfix — flagged here so it does not silently degrade to `'—'` forever. Also: the false-green mock-only repo tests (`test_agenda_grid_repository.py`, one of which literally documented "avoids full compile which fails on mixed text()+ORM select_from patterns") let the broken construct ship — a contract-test / compile-test gate was missing (cross-ref HB-42 FE↔BE contract gap + the mocked-service learning 2026-06-11).

## Files touched (scheduling only)

- `src/modules/vitalia/scheduling/api/rbac.py` (NEW — SSoT roles + `owner`)
- `src/modules/vitalia/scheduling/api/agenda_router.py` (consume SSoT, committing session, commit suspicious audit)
- `src/modules/vitalia/scheduling/api/notify_router.py` (consume SSoT)
- `src/modules/vitalia/scheduling/infrastructure/repositories/agenda_grid_repository_impl.py` (SQLA-2.0 text() rewrite)
- `src/modules/vitalia/scheduling/infrastructure/repositories/appointment_detail_repository.py` (same SQLA-2.0 fix)
- `tests/modules/vitalia/scheduling/test_agenda_rbac_owner.py` (NEW)
- `tests/modules/vitalia/scheduling/test_agenda_grid_repository_compiles.py` (NEW)
- `tests/modules/vitalia/scheduling/test_agenda_grid_repository.py` (updated: whereclause→bound-param assertions, module-source JOIN check)
- `tests/modules/vitalia/scheduling/test_phi_url_protection.py` (fake_db commit/rollback awaitable)
