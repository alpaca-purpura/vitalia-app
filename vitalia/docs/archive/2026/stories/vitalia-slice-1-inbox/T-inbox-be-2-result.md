# T-inbox-be-2 Result — Backend infrastructure (repos + models + migration 024)

**Ticket:** T-inbox-be-2
**Story:** vitalia-slice-1-inbox
**Surface:** backend infrastructure
**Commit:** 42a039f
**Branch:** wip/vitalia
**Status:** DONE

## Deliverables

### Files created (16 files, 1962 insertions)

**Models (SQLAlchemy 2.0):**
- `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/models/__init__.py`
- `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/models/conversation_model.py`
- `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/models/message_model.py`
- `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/models/activity_event_model.py`
- `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/models/action_receipt_model.py`

**Repositories (CompoundScopeRepositoryBase, scope_field='clinic_id'):**
- `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/conversation_repository.py`
- `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/message_repository.py`
- `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/activity_event_repository.py`
- `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/action_receipt_repository.py`

**Migration:**
- `vitalia/backend/alembic/versions/024_inbox_tables.py` (revision=024_vitalia, down_revision=023_vitalia)

**Tests:**
- `vitalia/backend/tests/modules/vitalia/crm/infrastructure/__init__.py`
- `vitalia/backend/tests/modules/vitalia/crm/infrastructure/test_conversation_repository.py`
- `vitalia/backend/tests/modules/vitalia/crm/infrastructure/test_message_repository.py`
- `vitalia/backend/tests/modules/vitalia/crm/infrastructure/test_activity_event_repository.py`
- `vitalia/backend/tests/modules/vitalia/crm/infrastructure/test_action_receipt_repository.py`
- `vitalia/backend/tests/migrations/test_slice1_inbox_migration.py`

## Test results

| Suite | Result |
|---|---|
| Repo tests (36) | 36 PASSED |
| Migration static tests (17 + 1 skipped) | 17 PASSED, 1 SKIPPED (live Postgres) |
| Architecture fitness (265) | 265 PASSED |
| Ruff lint | 0 errors |
| Ruff format | 0 violations |

## PHI compliance (hipaa-lite.md)

- tenant_id + clinic_id dual filter: enforced via `CompoundScopeRepositoryBase(scope_field="clinic_id")` on all 4 repos
- Soft-delete only: `deleted_at TIMESTAMPTZ NULL` on conversations + messages; present on activity_events + action_receipts for base compatibility
- No hard DELETE ever issued
- All timestamps TIMESTAMPTZ (timezone=True)
- structlog used throughout (no print/stdlib logging)

## Key decisions

1. **CompoundScopeRepositoryBase** (engine e8d3c04) used — supersedes brand-local `PhiRepositoryBase`
2. **ActivityEventModel + ActionReceiptModel**: added `deleted_at` column for `CompoundScopeRepositoryBase.get_by_id` compatibility (always NULL — these are append-only/state machines)
3. **OCC** implemented in `ConversationRepository.update_handler_mode` via `expected_updated_at` WHERE clause
4. **list_for_activity_stream** default limit=8 (SC-01 ActivityStream spec)

## Skills consulted (must_load enforcement v4.1)

| Skill | Invoked | Decision |
|---|---|---|
| `backend-expert` | Yes | runtime-quality-checklist: SQLA 2.0 Mapped[], DateTime(timezone=True), CompoundScopeRepositoryBase pattern |
| `tessl__fastapi` | N/A | No routes in this ticket (infra layer only) |
| `tessl__pytest-api-testing` | Yes | AsyncMock + MagicMock pattern for async repos; `pytest.mark.integration` skip for live DB tests |
| `tessl__graceful-degradation` | N/A | No external HTTP calls in infra layer |
| `hipaa-lite.md` | Yes | PHI dual filter (tenant_id + clinic_id), soft-delete mandatory, TIMESTAMPTZ |
