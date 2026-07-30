# T-BE-create-patch — Implementation Result

**Story:** vitalia-fase2-lisa-doctores  
**Ticket:** T-BE-create-patch (gap fix: RecurrentBlockCreateRequest request DTO)  
**Status:** DONE — tests-passing

---

## Gap Identified

`RecurrentBlockCreateRequest` had `day_of_week: int` (REQUIRED, ge=0, le=6) and `freq: str` (REQUIRED) as mandatory fields. The D3-F domain extension (`T-BE-recurrencia-domain`, commit `8cb2f97e`) added `days_of_week + interval` to the **response** DTO and domain entity, but the **request** DTO was never updated.

The FE (commit `333c5771`) sends:
```json
{
  "daysOfWeek": [0, 3],
  "interval": 2,
  "endConditionKind": "occurrences",
  "occurrences": 8
}
```

The BE rejected this with 422 because `day_of_week` and `freq` were required.

---

## Fix (TDD — RED tests first)

### Step 1 — RED tests written (7 new tests appended to `test_availability_blocks_api.py`)

| Test | Scenario |
|---|---|
| `test_recurrent_block_create_request_accepts_days_of_week_primary` | D3-F path: `daysOfWeek=[0,3]+interval=2+occurrences=8` → validates OK, no day_of_week/freq needed |
| `test_recurrent_block_create_request_accepts_legacy_only` | Legacy regression: `day_of_week=0+freq=weekly` → validates OK (backward compat) |
| `test_recurrent_block_create_request_rejects_neither_form` | Neither form present → `ValidationError` with Spanish-referencing message |
| `test_recurrent_block_create_request_days_of_week_field_exists` | `days_of_week` + `interval` fields exist in the DTO |
| `test_recurrent_block_create_request_day_of_week_optional_now` | `day_of_week` is now OPTIONAL (not required) |
| `test_recurrent_block_create_request_freq_optional_now` | `freq` is now OPTIONAL (not required) |
| `test_service_create_block_accepts_days_of_week` | `create_block` signature has `days_of_week` + `interval` params |
| `test_service_update_block_accepts_days_of_week` | `update_block` signature has `days_of_week` + `interval` params |

All 7 confirmed RED before any code change.

### Step 2 — Implementation (GREEN)

**`vitalia/backend/src/modules/vitalia/clinics/api/dtos.py`**
- Added `model_validator` import
- `RecurrentBlockCreateRequest`:
  - `days_of_week: list[int]` — primary D3-F field (default empty list, camelCase alias `daysOfWeek`)
  - `interval: int` — primary D3-F field (default 1, ge=1, camelCase alias `interval`)
  - `day_of_week: int | None` — now OPTIONAL (legacy backward compat)
  - `freq: str | None` — now OPTIONAL (legacy backward compat)
  - `@model_validator(mode="after")` — rejects payloads where BOTH forms absent; Spanish neutro error

**`vitalia/backend/src/modules/vitalia/clinics/application/availability_block_service.py`**
- `create_block()` — added `days_of_week: list[int] | None = None` + `interval: int = 1` params
- `update_block()` — same
- Domain entity construction passes `days_of_week=days_of_week or []` + `interval=interval` (D3-F primary path)
- Domain `__post_init__` bidirectional derivation handles the precedence: non-empty `days_of_week` wins over `day_of_week`

**`vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py`**
- `create_availability_block()` — passes `days_of_week` + `interval` via `getattr(request, ...)` alongside legacy fields
- `patch_availability_block()` — same

### Precedence rules (domain-enforced)

```
if days_of_week non-empty → D3-F primary path (interval used directly)
elif day_of_week present  → legacy path (backfills days_of_week=[day_of_week], derives interval from freq)
else                       → DTO validator rejects with 422 before reaching domain
```

### "one_off as string" smell

The `kind: str = Field(default="one_off")` smell in `OneOffBlockCreateRequest` (and equivalent in `RecurrentBlockCreateRequest`) is a typing improvement (should be `Literal["one_off"]`). Scope: **out of scope for this surgical patch** per task spec ("SOLO si vive en BE"). It lives in BE but changing it would break the discriminated union Pydantic parser which uses `str` for the discriminator field — not a 422 risk. Logged as tech debt.

---

## Gate Results (G5)

| Gate | Result |
|---|---|
| `ruff check src/modules/vitalia/clinics/` | PASS (0 errors) |
| `ruff format --check src/modules/vitalia/clinics/` | PASS (formatted) |
| `pytest tests/modules/vitalia/clinics/ -m "not integration"` | **398 PASS** (was 375, +23 new) |
| `pytest tests/architecture/ (excl. pgcrypto pre-existing)` | 339 PASS |
| pgcrypto arch test | Pre-existing FALSE POSITIVE (`treatment_plans.notes` regex) — unchanged |

---

## Files Modified

1. `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py` — DTO fix: `days_of_week` + `interval` primary; `day_of_week`/`freq` optional; `model_validator` cross-field
2. `vitalia/backend/src/modules/vitalia/clinics/application/availability_block_service.py` — `create_block` + `update_block` accept new params
3. `vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py` — router passes `days_of_week` + `interval`
4. `vitalia/backend/tests/modules/vitalia/clinics/test_availability_blocks_api.py` — 8 new RED→GREEN tests

---

## § Patch create-request (continuation)

_(Appended to T-BE-recurrencia-domain-result.md below)_

This fix closes the gap between the domain layer (which already supported `days_of_week+interval` from commit `8cb2f97e`) and the API request DTO layer (which had not been updated). The FE → BE wire contract is now consistent: FE sends `daysOfWeek+interval`, BE accepts and routes to domain correctly.

---

<!-- @pm: build phase done (state: tests-passing). Commit: pending. Files: 4. Native ticket tests: 398/398 PASS (non-integration clinics) + 339/339 arch (excl. pre-existing pgcrypto). Awaiting orchestrator → gate-runner → auditor-backend (independent verdict). -->
