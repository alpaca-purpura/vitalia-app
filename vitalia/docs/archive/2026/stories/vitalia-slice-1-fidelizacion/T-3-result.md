# T-3 Result — Architecture fitness NEW gates: test_cron_envelope_used + test_compound_scope_repository_used

**Ticket:** T-3
**Story:** vitalia-slice-1-fidelizacion
**Brand:** vitalia
**State:** done
**Date:** 2026-05-20
**production_code:** false (tests only — Sonnet OK per R23)

## Skills Consulted (must_load enforcement v4.1)

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Mandatory always — anti-patterns FastAPI/SQLA/tests/migrations | Loaded runtime-quality-checklist. Confirmed test-only ticket: no routes/services/migrations needed. Arch fitness ratchet pattern per `references/architectural-fitness.md`. |
| `tessl__fastapi` | Mandatory always | N/A — no FastAPI routes in this ticket. Confirmed. |
| `tessl__pytest-api-testing` | Mandatory always | Used `ast.parse()` + `ast.walk()` for AST-based scanning (same pattern as existing `test_phi_dual_filter.py`). No `httpx.AsyncClient` needed — pure filesystem/AST tests. |

**Scope note:** No domain skills (`brand-expert`, `offer-expert`, `metrics-expert`) required — ticket touches only architecture fitness test files, no business module code.

## Implementation Summary

Two new architecture fitness test files created implementing the ratchet (shrink-only) pattern per `03-arch-be.md § 10`.

### Files created

| File | Tests | Coverage |
|---|---|---|
| `vitalia/backend/tests/architecture/test_cron_envelope_used.py` | 4 | cron decorator enforcement |
| `vitalia/backend/tests/architecture/test_compound_scope_repository_used.py` | 5 | PHI repo engine base enforcement |

### test_cron_envelope_used.py

**Purpose:** Enforce that all cron-decorated functions in vitalia workers use `@cron_envelope` from engine (`luana_core_platform.workers.cron_envelope`), never brand-local alternatives (`@idempotent_cron`).

**Ratchet baseline:**
```python
KNOWN_LEGACY_CRONS = {
    "lucas_weekly_recommendations": "Uses brand-local @idempotent_cron — pre-dates engine cron_envelope lift (2026-05-20)..."
}
baseline_count = 1  # must never grow
```

**Tests (4):**
1. `test_no_non_engine_cron_decorators` — AST scan over `_shared/workers/jobs/` + `fidelizacion/application/workers/`. Violations fail unless in allowlist.
2. `test_fidelizacion_workers_use_engine_cron_envelope` — pre-emptive gate for 6 T-6 workers (SKIP if dir doesn't exist yet).
3. `test_allowlist_does_not_grow` — ratchet count `<= 1` assertion.
4. `test_engine_cron_envelope_importable` — import smoke test.

**Result:** 4/4 PASS. `lucas_weekly_recommendations` correctly captured in allowlist. No new violations.

### test_compound_scope_repository_used.py

**Purpose:** Enforce that all vitalia PHI repositories inherit `CompoundScopeRepositoryBase` from engine (`luana_core_platform.repositories.compound_scope_repository`), not brand-local `PhiRepositoryBase`.

**Ratchet baseline:**
```python
KNOWN_LEGACY_PHI_REPOS = {
    "patient_repository.py": "Uses brand-local PhiRepositoryBase — pre-dates lift (2026-05-20)...",
    "lead_screening_event_repository.py": "Uses brand-local PhiRepositoryBase — pre-dates lift (2026-05-20)...",
}
baseline_count = 2  # must never grow
```

**Tests (5):**
1. `test_no_new_brand_local_phi_repos` — AST scan over all vitalia `*_repository.py` (excluding copilot/sales_agent — builder-agentic exclusive). Any `PhiRepositoryBase` subclass not in allowlist = FAIL.
2. `test_fidelizacion_phi_repos_use_engine_base` — pre-emptive gate for 3 T-4 PHI repos (SKIP if dir doesn't exist yet). New repos must use engine base from day 1.
3. `test_allowlist_does_not_grow` — ratchet count `<= 2` assertion.
4. `test_engine_compound_scope_importable` — import smoke test + `scope_field` parameter existence check.
5. `test_existing_phi_repos_have_dual_filter` — verifies allowlisted legacy repos still reference `clinic_id` (HIPAA-lite dual filter integrity).

**Result:** 5/5 PASS. Two legacy repos correctly captured in allowlist. Engine base confirmed importable with `scope_field` param.

## Test Run Results

```
vitalia/backend/tests/architecture/ — 265 passed, 2 warnings (pre-existing unrelated)

Before T-3: 256 tests
After T-3:  265 tests (+9 new, all GREEN)

test_cron_envelope_used.py ....                     4/4 PASS
test_compound_scope_repository_used.py .....        5/5 PASS
```

## Quality Gates

| Gate | Status | Notes |
|---|---|---|
| G1 ruff check | PASS | 0 errors both files |
| G2 ruff format | PASS | Auto-formatted, clean |
| G3 pytest arch tests | PASS | 265 passed (265/265) |
| G4 No regression | PASS | All 256 prior tests still pass |
| G5 HARD — engine importable | PASS | `cron_envelope` importable; `CompoundScopeRepositoryBase` importable with `scope_field` |
| G6 Allowlists baseline | PASS | cron baseline=1, PHI baseline=2 |

## Ratchet State (for T-6 follow-up)

When T-6 migrates legacy repos to engine bases:

**To migrate `lucas_weekly_recommendations`:**
1. Replace `from src.modules.vitalia._shared.workers.base import idempotent_cron`
2. Add `from luana_core_platform.workers.cron_envelope import cron_envelope`
3. Change `@idempotent_cron(...)` to `@cron_envelope("vitalia.cron.lucas_weekly_recommendations")`
4. Remove entry from `KNOWN_LEGACY_CRONS` in `test_cron_envelope_used.py`
5. Reduce `baseline_count = 1` to `baseline_count = 0`

**To migrate `patient_repository.py`:**
1. Replace `class PatientRepository(PhiRepositoryBase)` with `class PatientRepository(CompoundScopeRepositoryBase[PatientModel, UUID])`
2. Add `from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase`
3. Update constructor: `super().__init__(session=session, scope_field="clinic_id")`
4. Remove `validate_dual_filter()` calls (engine base handles contract)
5. Remove entry from `KNOWN_LEGACY_PHI_REPOS` in `test_compound_scope_repository_used.py`

Same pattern for `lead_screening_event_repository.py`.

## Commit SHA

See git log for commit pushed to `wip/vitalia`.
