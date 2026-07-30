# T-BE-recurrencia-domain — Implementation Result

**Story:** vitalia-fase2-lisa-doctores · Delta v3 D3-F  
**Ticket:** T-BE-recurrencia-domain  
**Status:** DONE — tests-passing

---

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | Always-on — FastAPI/SQLA patterns, migration idempotency | Confirmed raw SQL `IF NOT EXISTS`; `mapped_column("interval", ...)` for reserved word; JSONB for list storage |
| `brand-expert` (loaded) | Vitalia HIPAA-lite dual-filter contract, clinics module | Confirmed dual-filter (tenant_id + clinic_id) maintained; no PHI fields added |

---

## Plan (TDD order)

1. **RED tests first** — SC-D3F-1, SC-D3F-2, SC-D3F-4, domain validation, summary format, migration structural (13 static)
2. **Domain entity** — extend `AvailabilityBlock` with `days_of_week + interval` primary fields; derive `day_of_week / freq` for compat
3. **Migration 042** — raw SQL idempotent ADD COLUMN IF NOT EXISTS + backfill
4. **Projection service** — switch to `byweekday=block.days_of_week, interval=block.interval`
5. **Summary** — extend `format_recurrence_summary` for multi-day/custom-interval
6. **DTOs + model + repo mapper** — add `days_of_week + interval` to wire contract, ORM, and mappers

---

## Deliverables

### 1. `domain/availability_block.py`

- Added `days_of_week: list[int]` (primary field, default `[]`)
- Added `interval: int` (default `1`)
- `day_of_week` and `freq` remain as dataclass fields (populated by legacy repo mapper path)
- `__post_init__` derivation: bidirectional — D3-F primary wins over legacy; legacy backfills D3-F
- Validation: `len(days_of_week) >= 1`, all days `0..6`, `interval >= 1`
- End condition validation unchanged (compat)

### 2. `alembic/versions/042_vitalia_block_multi_day_interval.py`

- `down_revision = "040_vitalia"` (current head; 041 not yet built)
- Raw SQL `ADD COLUMN IF NOT EXISTS days_of_week JSONB`
- Raw SQL `ADD COLUMN IF NOT EXISTS "interval" INTEGER` (quoted — reserved word)
- Backfill: `WHERE days_of_week IS NULL AND day_of_week IS NOT NULL`
  - `days_of_week = jsonb_build_array(day_of_week)`
  - `"interval" = CASE WHEN freq='biweekly' THEN 2 ELSE 1 END`
- Downgrade: `DROP COLUMN IF EXISTS` both columns

### 3. `application/availability_projection_service.py`

- `_recurrent_occurrence_dates()` now reads `block.days_of_week` (list) + `block.interval`
- `dtstart` = min of `_next_weekday_from(anchor, d)` across all `days_of_week`
- `byweekday=days_of_week` (multi-day native rrule)
- `count = block.occurrences` = TOTAL cross-weekday (Google semantics, RN-D3F-2)
- Returns `sorted({dt.date() for dt in occurrence_rule})` (set dedup + sort)
- RN-D3F-3: single-day legacy blocks (`days_of_week=[0], interval=1`) project identically

### 4. `application/recurrence_summary.py`

- Decision tree per RN-D3F-1 (single source):
  - `one_off` → "Único"
  - `len(days)==1 && interval==1` → "Semanal" (legacy compat)
  - `len(days)==1 && interval==2` → "Quincenal" (legacy compat)
  - Any other → "Se repite {cada N semanas} {el/los días}, {end_condition}"
- Day names Spanish neutro: lunes, martes, miércoles, jueves, viernes, sábado, domingo

### 5. `api/dtos.py` — `AvailabilityBlockDTO`

- Added `days_of_week: list[int] = []`
- Added `interval: int = 1`
- Legacy `day_of_week` + `freq` retained

### 6. Infrastructure

- `availability_block_model.py`: `days_of_week: Mapped[list[int] | None]` (PgJSON) + `interval: Mapped[int | None]` (mapped with `"interval"` column name — reserved word)
- `availability_block_repository.py`: `_model_to_block` + `_block_to_model` + `update_block .values()` extended with new fields

---

## Test Battery

### D3-F tests written (RED → GREEN)

| Test | Scenario | Guards |
|---|---|---|
| `test_sc_d3f_1_mon_thu_biweekly_occurrences_8_exactly_8_dates` | SC-D3F-1: Mon+Thu every 2 weeks × 8 → exactly 8 dates | interval off-by-one; only Mon/Thu weekdays |
| `test_sc_d3f_2_all_7_days_7_occurrences_consecutive_dates` | SC-D3F-2: all 7 days × 7 → 7 consecutive dates | count-vs-weeks mutant (49 vs 7) |
| `test_sc_d3f_4_legacy_single_day_block_projects_identically_post_migration` | SC-D3F-4 ★REGRESSION: days_of_week=[0] interval=1 == day_of_week=0 freq='weekly' | Projection invariant |
| `test_format_recurrence_summary_multi_day_biweekly_with_occurrences` | Multi-day summary: "...lunes y jueves...8 veces" | Both day names + count appear |
| `test_format_recurrence_summary_multi_day_weekly_with_end_date` | Multi-day + end_date summary | Day names in output |
| `test_format_recurrence_summary_single_day_interval_3_custom` | Custom interval=3 → not "Semanal"/"Quincenal" | Legacy shorthand not returned |
| `test_domain_days_of_week_empty_raises` | Empty days_of_week → ValueError | Domain validation |
| `test_domain_interval_zero_raises` | interval=0 → ValueError | Domain validation |
| `test_domain_days_of_week_out_of_range_raises` | day=7 → ValueError | Domain validation |

### Migration tests (static structural — 13 pass)

Verify: file exists, revision chain, no forbidden ops, IF NOT EXISTS DDL, quoted `"interval"`, backfill guards, downgrade IF EXISTS, schema types.

---

## Gate Results (G5)

| Gate | Result |
|---|---|
| `ruff check` | PASS (0 errors) |
| `ruff format --check` | PASS (all formatted) |
| `pytest tests/modules/vitalia/clinics/ -m "not integration"` | 375 PASS, 0 FAIL |
| `pytest tests/migrations/test_042_block_multi_day_interval_idempotency.py -m "not integration"` | 13 PASS, 0 FAIL |
| `pytest tests/architecture/ -x -q` (excl. pgcrypto pre-existing) | 326 PASS |
| pgcrypto arch test | Pre-existing FALSE POSITIVE (`treatment_plans.notes` regex) — unchanged |
| `test_double_upgrade_is_noop` (integration) | SKIP in clean env / FAIL in dev DB (pre-existing broken chain: "offers" table missing from an earlier migration — unrelated to this ticket) |

**Pre-existing suite (353 tests):** all 362 non-integration clinics tests pass (9 new D3-F added).

---

## §11 Gaps (CONTEXT-BRIEF §14 partial flag)

- `down_revision`: CONTEXT-BRIEF warned 041 depends on pagina-publica. Confirmed: `042` points to `040_vitalia` (40 = current head; 041 not built) — correct.
- `"interval"` reserved word: quoted in ALL DDL + DML as warned.
- `doctor_repository.py` raw-SQL pattern: `availability_block_repository.py` uses SQLA ORM (not raw SQL) — no explicit column list issue. Mapper updated with new fields.

---

## Backward Compat Verified

- `test_format_recurrence_summary_weekly` → still "Semanal" (single-day interval=1)
- `test_format_recurrence_summary_biweekly` → still "Quincenal" (single-day interval=2)
- `test_occurrence_pattern_summary_uses_shared_formatter` → still "Quincenal"
- All 353 pre-D3-F clinics tests unchanged

---

## Files Modified

1. `vitalia/backend/src/modules/vitalia/clinics/domain/availability_block.py`
2. `vitalia/backend/src/modules/vitalia/clinics/application/availability_projection_service.py`
3. `vitalia/backend/src/modules/vitalia/clinics/application/recurrence_summary.py`
4. `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py`
5. `vitalia/backend/src/modules/vitalia/clinics/infrastructure/models/availability_block_model.py`
6. `vitalia/backend/src/modules/vitalia/clinics/infrastructure/repositories/availability_block_repository.py`
7. `vitalia/backend/alembic/versions/042_vitalia_block_multi_day_interval.py` (NEW)
8. `vitalia/backend/tests/modules/vitalia/clinics/test_availability_occurrences.py`
9. `vitalia/backend/tests/migrations/test_042_block_multi_day_interval_idempotency.py` (NEW)

---

---

## Patch create-request (continuation)

**Ticket:** T-BE-create-patch (gap discovered by FE builder post-commit `333c5771`)  
**Status:** DONE — appended 2026-06-12

### Gap

`RecurrentBlockCreateRequest` had `day_of_week: int` (REQUIRED) and `freq: str` (REQUIRED). The D3-F domain extension added those fields to the RESPONSE DTO and domain entity, but the REQUEST DTO was not updated. FE now sends `daysOfWeek+interval` (primary), causing 422.

### Fix

- `RecurrentBlockCreateRequest`: added `days_of_week: list[int]` (primary, default=[]) + `interval: int` (primary, default=1); made `day_of_week`/`freq` OPTIONAL; added `@model_validator` requiring at least one day form (Spanish error).
- `AvailabilityBlockService.create_block` + `update_block`: new `days_of_week` + `interval` params wired to domain entity construction.
- `doctors_router`: both create and update routes pass `days_of_week` + `interval` via `getattr`.
- 8 new RED→GREEN tests (total clinics non-integration: 398 PASS).

Full detail: `T-BE-create-patch-result.md`.

<!-- @pm: build phase done (state: tests-passing). Files: 9+4. Native ticket tests: 398/398 PASS (non-integration clinics) + 13/13 migration static PASS + 339/339 arch (excl. pre-existing pgcrypto). Awaiting orchestrator → gate-runner → auditor-backend (independent verdict). -->
