# T-be-migrations-1 — Result

**Ticket:** T-be-migrations-1 — Migrations 017-021 idempotent + schema mirror persistence models
**Story:** vitalia-copilot-tools-impl
**Date:** 2026-05-18
**Branch:** wip/vitalia-slice-1-shipping
**Developer:** Claude Sonnet 4.6 (builder-backend)

## Verdict: tests-passing

## Files created

### Alembic migrations (5 files, ~250 LOC)

| File | Description |
|---|---|
| `vitalia/backend/alembic/versions/017_vitalia_lead_screening_events.py` | `lead_screening_events` table + 2 composite indexes. PHI table with tenant+clinic dual filter. |
| `vitalia/backend/alembic/versions/018_vitalia_attribution_matrix_snapshots.py` | `attribution_matrix_snapshots` table + 2 indexes (one partial UNIQUE WHERE deleted_at IS NULL). |
| `vitalia/backend/alembic/versions/019_vitalia_referrals_leaderboard_snapshots.py` | `referrals_leaderboard_snapshots` table + 2 indexes (same partial UNIQUE pattern). |
| `vitalia/backend/alembic/versions/020_vitalia_langgraph_checkpoint_tables.py` | 6 LangGraph AsyncPostgresSaver tables for 2 prefixes: `vitalia_wizard_onboarding_` + `vitalia_lucas_analysis_`. |
| `vitalia/backend/alembic/versions/021_vitalia_screening_outcome_check.py` | CHECK constraint on `lead_screening_events.outcome` with DO...EXCEPTION WHEN duplicate_object idempotency pattern. |

### Schema mirror persistence models (8 files, ~350 LOC)

| File | Model class | Mapped table | Brand-specific columns |
|---|---|---|---|
| `vitalia/backend/src/modules/vitalia/copilot/persistence/models/copilot_trace_event.py` | `CopilotTraceEventVitalia` | `copilot_trace_event` | `clinic_id`, `compliance_level`, `medical_guardrail_check_passed` |
| `vitalia/backend/src/modules/vitalia/copilot/persistence/models/copilot_llm_call.py` | `CopilotLLMCallVitalia` | `copilot_llm_call` | `clinic_id`, `compliance_level`, `medical_guardrail_check_passed` |
| `vitalia/backend/src/modules/vitalia/sales_agent/persistence/models/sales_agent_trace_event.py` | `SalesAgentTraceEventVitalia` | `sales_agent_trace_event` | `clinic_id`, `compliance_level`, `medical_guardrail_check_passed` |
| `vitalia/backend/src/modules/vitalia/sales_agent/persistence/models/sales_agent_llm_call.py` | `SalesAgentLLMCallVitalia` | `sales_agent_llm_call` | `clinic_id`, `compliance_level`, `medical_guardrail_check_passed` |
| `vitalia/backend/src/modules/vitalia/sales_agent/persistence/models/lead_screening_event.py` | `LeadScreeningEventModel` | `lead_screening_events` | `clinic_id` (NOT NULL — PHI dual filter) |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/persistence/models/stage_recommendation.py` | `LucasStageRecommendationModel` | `vitalia_lucas_recommendations` | `clinic_id` |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/persistence/models/attribution_matrix_snapshot.py` | `AttributionMatrixSnapshotModel` | `attribution_matrix_snapshots` | `clinic_id`, `currency` (from tenant locale) |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/persistence/models/referrals_leaderboard_snapshot.py` | `ReferralsLeaderboardSnapshotModel` | `referrals_leaderboard_snapshots` | `clinic_id` |

### Support __init__.py files (9 files)

`vitalia/backend/src/modules/vitalia/copilot/persistence/__init__.py`,
`vitalia/backend/src/modules/vitalia/copilot/persistence/models/__init__.py`,
`vitalia/backend/src/modules/vitalia/sales_agent/__init__.py`,
`vitalia/backend/src/modules/vitalia/sales_agent/persistence/__init__.py`,
`vitalia/backend/src/modules/vitalia/sales_agent/persistence/models/__init__.py`,
`vitalia/backend/src/modules/vitalia/agentic/__init__.py`,
`vitalia/backend/src/modules/vitalia/agentic/lucas/__init__.py`,
`vitalia/backend/src/modules/vitalia/agentic/lucas/persistence/__init__.py`,
`vitalia/backend/src/modules/vitalia/agentic/lucas/persistence/models/__init__.py`

### Test files (1 file created, 1 file modified)

| File | Tests | Status |
|---|---|---|
| `vitalia/backend/tests/unit/modules/vitalia/copilot/persistence/test_schema_mirror.py` | 34 | CREATED |
| `vitalia/backend/tests/migrations/test_slice1_migrations.py` | 143 collected (131 pass, 12 skip) | MODIFIED (extended with 017-021 coverage) |

## Test results

```
Architecture fitness:   216 passed  (0.84s)
Schema mirror unit:      34 passed  (0.26s)
Migration tests:        131 passed, 12 skipped  (0.20s)
```

Skipped tests: DB-connection-dependent tests (Postgres not running in this environment). Gated with `pytest.mark.integration` / `@pytest.mark.skipif`. This is expected per gate-runner docs (gates 8/9/10 SKIP if Postgres down).

## Quality gate results

- `ruff check` — 0 errors on created files
- `ruff format --check` — 0 files to reformat (1 fixed: `test_slice1_migrations.py`)
- Architecture fitness — 216/216 PASS (no ratchet regression)

## Key design decisions

1. **Migration chain:** 017 → 018 → 019 → 020 → 021. Alembic `down_revision` chain correct.
2. **Idempotency:** All DDL uses `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`. Migration 021 uses `DO...EXCEPTION WHEN duplicate_object THEN NULL` pattern for CHECK constraint.
3. **PHI dual filter:** `lead_screening_events`, `copilot_trace_event`, `copilot_llm_call`, `sales_agent_trace_event`, `sales_agent_llm_call` all have `clinic_id` column per `vitalia/.claude/rules/hipaa-lite.md`.
4. **Currency:** `attribution_matrix_snapshots.currency CHAR(3)` nullable (from tenant locale at compute time). Never hardcoded per `.claude/rules/currency-handling.md`.
5. **SA 2.0:** All models use `Mapped[T] = mapped_column(...)` syntax. No legacy `Column()`.
6. **Schema-mirror exception:** Per `.claude/rules/backend-ddd.md`, `builder-backend` MAY create persistence models under `{brand}/copilot/persistence/models/` and `{brand}/sales_agent/persistence/models/` as schema mirrors. `downstream-regression-na:` magic comment in model files.

## Scope note

Additional files under `vitalia/backend/src/modules/vitalia/agentic/` (guardrails, prompts, tools) were created by the prior agent as stubs for upcoming tickets T-ag-tools-* and T-ag-workflows-*. These are committed as-is per the brief — they are brand extensions (copilot/sales_agent exclusive owner is `builder-agentic`; these are stubs only, not logic). The agentic production logic tickets (T-ag-tools-1, T-ag-tools-2, T-ag-tools-3) are R23 Opus 4.7 required and are NOT implemented in this ticket.

## Next ticket

T-be-services-1, T-be-services-2, T-be-services-3 (parallel, unblocked after this commit merges).
