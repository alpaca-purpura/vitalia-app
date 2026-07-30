<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend Code Review: bug7 rounds 4-6 (clinics · availability)

**Date:** 2026-06-15
**Brand:** vitalia
**Story:** `vitalia-fase2-lisa-doctores`
**Diff range:** `7251cd55..HEAD` (BE clinics + alembic only)
**Files reviewed:** 9 product + 3 tests
**Domains touched:** clinics (availability blocks / projection / scoped-delete)
**Skills consulted:** backend-expert (DDD/migrations/PHI/dual-filter); hipaa-lite overlay
**Process context:** Conv-3 post G (`chris_verify.signoff.result: SATISFIED`, rounds 1-6) + R (`reconciled: true`). Ratified scope read from `checkpoint.md::chris_verify.rounds` + `01-spec.md § "Reconcile bug7 (rounds 4-6)"`. Audited for invariants, NOT against pre-iteration spec.
**Verdict:** **APPROVED**

## Scope check (Step 3)

- ✅ NO `core/luana-core-*/src/` edits in diff (no ENGINE EDIT)
- ✅ NO `{other_brand}/...` product edits (no CROSS-BRAND POLLUTION)
- ✅ NO `copilot/`/`sales_agent/` files (no CROSS-SCOPE)
- ✅ Non-vitalia files in range are harness docs/rules only (`core-harness/rules/parallel-safety.md`, `docs/...`) — not product code, out of audit surface
- ✅ No cross-brand mirror: `availability_block_repository.py` exists only under vitalia. Feature is clinics-vertical-specific (correctly brand-local; not a shared-engine lift candidate)

## /test-backend Gate Status (verified by auditor)

| Gate | Result | Detail |
|---|---|---|
| Lint (ruff check) | PASS | `src/modules/vitalia/clinics/ tests/.../clinics/` — All checks passed |
| Format (ruff format --check) | PASS | 78 files already formatted |
| Clinics suite | PASS | **457 passed** (matches expected) |
| Arch: response_model required | PASS | 14 passed (incl. dual-filter + audit-sync) |
| Arch: full vitalia suite | 353 passed / **1 failed (pre-existing, out-of-scope)** | only `test_pgcrypto_phi_columns` (`treatment_plans.notes TEXT` — CRM module). NOT introduced by these rounds; explicitly excluded by audit brief |
| Migration 044 applied | PASS | `alembic current` = `044_vitalia (head)` |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation (dual filter) | PASS | 0 |
| 3 | Soft Deletes | PASS | 0 |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | PASS | 0 |
| 6 | Async Consistency | PASS | 0 |
| 7 | Pydantic v2 / PII | PASS | 0 |
| 8 | Migration Quality | PASS | 0 |
| 9 | Security | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 (1 nit below) |
| 11 | Cross-cutting (Spanish/UTC) | PASS | 0 |
| 12 | Mirror detection | PASS | 0 |
| 13 | Connectivity (anti-isla) | PASS | 0 |

## Invariant verification (per audit brief)

1. **Migración 044 idempotente + reversible** — ✅ `ADD COLUMN IF NOT EXISTS excluded_dates JSONB` / `DROP COLUMN IF EXISTS`. `down_revision = "043_vitalia"` (043 exists), 044 is a leaf head (no branch). Raw SQL only — no `op.add_column`/`sa.Enum`. Matches the established 042 `days_of_week JSONB` precedent in the same model.
2. **Dual filter tenant_id+clinic_id** — ✅ Present in ALL repo queries including the 4 new methods (`persist_excluded_dates`, `retire_free_slots_on_date`, `truncate_block`, `retire_free_slots_from_date`) + `count_future_confirmed`. Every method calls `validate_dual_filter(...)` first and every `select`/`update` WHERE includes both `tenant_id` and `clinic_id`. Repo inherits `CompoundScopeRepositoryBase(scope_field="clinic_id")`.
3. **Audit SYNC pre-response (hipaa-lite)** — ✅ `exclude_occurrence` writes `doctor.availability_block_occurrence_excluded`; `truncate_from` writes `doctor.availability_block_truncated`; both `await self._audit.write(...)` before the service returns and before the router `db.commit()`. Asserted by tests (`mock_audit.write.assert_called_once()`).
4. **CRITICAL: confirmed slots NEVER deleted** — ✅ Every retire/delete SQL (`retire_free_slots_on_date`, `retire_free_slots_from_date`, `delete_block`, `update_block`) filters `has_confirmed_appointment.is_(False)`. The `count_future_confirmed` path returns the preserved count. Identical SQL pattern to the pre-existing `delete_block` covered by `test_availability_block_service_delete_preserves_confirmed_appointments`.
5. **response_model + 422 Spanish neutro** — ✅ DELETE route has `response_model=DeleteBlockResponse` (line 980). 422 messages are Spanish neutro LatAm, no voseo: "Se requiere el parámetro 'occurrence_date'...", "El parámetro 'scope' debe ser uno de...", "No puedes crear bloques en fechas pasadas.", "La fecha de fin no puede estar en el pasado."
6. **occurrences = N ciclos completos (round-6 ratified)** — ✅ `count = block.occurrences * len(days_of_week)` in `_recurrent_occurrence_dates`. Single-day → N×1 = N (unchanged); multi-day → complete cycles. Matches `01-spec.md § Round-6` (`reconciled: true`). NOT flagged as a bug — this is the Chris-ratified product decision. Tested by `test_sc_d3f_1_mon_thu_biweekly_occurrences_8_complete_cycles` + `test_sc_d3f_2_all_7_days_7_occurrences_complete_weeks`.
7. **past-guard 422** — ✅ `create_block`: `one_off` `specific_date < today` → ValueError; `recurrent` `end_date` condition `end_date < today` → ValueError. Both caught by router `except ValueError → 422`. Tested (`test_post_one_off_past_date_returns_422`, `test_create_recurrent_past_end_date_raises_value_error`).
8. **No core/cross-brand edit, no mirror** — ✅ (see Scope check).

## Findings

### WARN (non-blocking · Category 10): service-level scope tests mock the repo; confirmed-preservation SQL for the 2 NEW retire paths is asserted only indirectly

**Files:** `test_availability_block_scoped_delete.py::test_service_exclude_occurrence_retires_free_slots_not_confirmed`, `::test_service_truncate_from_retires_future_free_slots`
**Observation:** These tests use `AsyncMock` repos and assert the service calls `retire_free_slots_on_date` / `retire_free_slots_from_date` with the right args — they do NOT exercise the actual `has_confirmed_appointment.is_(False)` WHERE clause against a real session. The clause is correct on inspection and is the *identical* SQL pattern already covered by the real-path `series`-scope test (`test_availability_block_service_delete_preserves_confirmed_appointments`).
**Why non-blocking:** the invariant's enforcement point (the WHERE clause) is byte-for-byte the same predicate already integration-covered for `delete_block`; the new methods only change the date filter (`== slot_date` / `>= from_date`), not the confirmed-preservation predicate. Chris live-verified the scope behavior (rounds 5-6, screenshots) and `chris_verify.signoff: SATISFIED`. Risk of regression on the confirmed predicate is low.
**Suggested follow-up (not required for merge):** add a real-DB integration test that seeds one confirmed + one free slot on the excluded/truncated date and asserts only the free slot is soft-deleted, to lock the predicate per-path. Capture as tech-debt (CIL L3) rather than blocking this hotfix series.

## Contract Compliance (business surface)

- ✅ `DeleteBlockResponse.scope` added (echoed `series|occurrence|this_and_future`)
- ✅ DELETE endpoint: `?scope=&occurrence_date=` with 422 when `occurrence_date` missing for occurrence/this_and_future; `scope=series` default = back-compat
- ✅ Port `AvailabilityRepoPort` declares all 4 new methods; concrete repo implements all
- ✅ Domain `excluded_dates: list[str]` pure Python; model `excluded_dates: Mapped[list[str] | None]` JSONB — no framework leak into domain

## Allowlist Movement

- No architecture-fitness allowlist grew. The single arch failure is a pre-existing CRM-module assertion (`treatment_plans.notes`), unrelated to this diff.

## Native-First / parallel-safety Audit

- ✅ Gates run native (`${WS}/.venv/bin/{ruff,pytest}`), no `docker exec` for lint/tests
- ✅ Migration applied via the documented `docker exec ... alembic` runtime path (allowed)

## Downstream regression scope

| Surface modified | Downstream test targets | Status |
|---|---|---|
| `clinics/application/availability_block_service.py`, `availability_projection_service.py`, `infrastructure/repositories/availability_block_repository.py`, `api/doctors_router.py`, `api/dtos.py`, `domain/availability_block.py`, `infrastructure/models/availability_block_model.py` | `tests/modules/vitalia/clinics/` (brand-local; no cross-brand/engine consumers — feature is vitalia clinics-specific) | PASS (457) |

No shared/ or engine surface touched → no cross-consumer downstream targets.

## Verdict Math

- No FAIL in categories 1/2/8/9/12/13 → no auto-FAIL
- No `/test-backend` gate FAIL introduced (only pre-existing out-of-scope pgcrypto)
- No allowlist growth
- Ratified scope (chris_verify.rounds) honored; invariants intact
- One Category-10 WARN (mocked scope tests) → does not reach two-WARN threshold
- **Result: APPROVED**

## Self-fix log

None required — no Carril A/R fixes applied (all gates green on inspection).
