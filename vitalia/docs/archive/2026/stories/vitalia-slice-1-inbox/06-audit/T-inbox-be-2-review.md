<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# T-inbox-be-2 — Infrastructure repos + models + migration 024 — Review

**Brand:** vitalia
**Story:** vitalia-slice-1-inbox
**Surface:** backend (infrastructure layer)
**Verdict:** CHANGES_REQUESTED

## Scope

4 SQLAlchemy 2.0 models + 4 repositories (`CompoundScopeRepositoryBase scope_field="clinic_id"`) + Alembic migration `024_inbox_tables.py`.

Paths reviewed:
- `crm/infrastructure/persistence/models/{conversation,message,activity_event,action_receipt}_model.py`
- `crm/infrastructure/persistence/{conversation,message,activity_event,action_receipt}_repository.py`
- `alembic/versions/024_inbox_tables.py`

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Infrastructure layer; ORM-only, no business logic |
| 2 | Tenant Isolation | PASS | All repos inherit `CompoundScopeRepositoryBase` with `scope_field='clinic_id'` (dual filter via `_scope_attr()`) |
| 3 | Soft Deletes | PASS | `deleted_at` excluded in `list_for_inbox`, `list_for_conversation`, `update_handler_mode` |
| 4 | Code Quality | PASS | ruff check/format clean (verified) |
| 5 | SQLAlchemy 2.0 | PASS | `Mapped[]` + `mapped_column()` + `select()` + `update()` (no `session.query`) |
| 6 | Async Consistency | PASS | All repo methods async |
| 7 | Pydantic v2 / DTOs | N/A | Infrastructure only |
| 8 | Migration Quality | PASS | Raw SQL `IF NOT EXISTS` throughout (`024_inbox_tables.py`). No `op.create_table` / `op.add_column` |
| 9 | Security | PASS | OCC via `expected_updated_at` parameter check in `update_handler_mode` |
| 10 | Tests / TDD | PASS | Integration tests `test_inbox_send_retract_audit_log.py` verify dual filter at DB level (7 tests, auto-skip when Postgres down — verified) |
| 11 | Cross-cutting | PASS | All timestamp columns `DateTime(timezone=True)`; no `datetime.utcnow()` (uses `datetime.now(tz=timezone.utc)`) |
| 12 | Mirror detection | PASS | Models brand-local, no cross-brand basename collision (verified) |

## Findings

### FAIL: MessageRepository missing methods called by services
**Category:** 10 (Tests/TDD) — but root cause is infrastructure gap
**File:** `crm/infrastructure/persistence/message_repository.py`
**Issue:** Repository defines only `list_for_conversation` and `soft_delete`. Services in T-inbox-be-3 (`SendMessageService`, `RetractMessageService`, `ProactiveOutboundService`) call:
- `msg_repo.create(...)` — does NOT exist
- `msg_repo.mark_retracted(...)` — does NOT exist
- `msg_repo.find_patient_reply_after(...)` — does NOT exist

These work in unit tests because tests pass `AsyncMock()`, which accepts any attribute. But against a real `MessageRepository` instance the calls would `AttributeError` at runtime.

**Evidence:**
```bash
$ grep -n "def " vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/message_repository.py
46:    def __init__(self, *, session: AsyncSession) -> None:
54:    async def list_for_conversation(...)
100:    async def soft_delete(...)
```
**Fix:** Implement `create`, `mark_retracted`, `find_patient_reply_after` methods with dual-filter SQL. Add infra tests that bind real repo instance.

### FAIL: ConversationRepository missing `get_or_create_for_lead` method
**Category:** 10 (Tests/TDD)
**File:** `crm/infrastructure/persistence/conversation_repository.py`
**Issue:** `ProactiveOutboundService.send_proactive()` line 222 calls `self._conv_repo.get_or_create_for_lead(...)`. Repository does NOT implement this method (only `list_for_inbox` + `update_handler_mode`).
**Fix:** Add `get_or_create_for_lead(tenant_id, clinic_id, lead_id, channel)` with idempotent insert pattern.

### INFO: ActionReceiptRepository missing `create` method
**File:** `crm/infrastructure/persistence/action_receipt_repository.py`
**Issue:** Repo has `get_active_for_message` + `mark_retracted` only. Per spec § 9 and arch § 6.3 `SendMessageService` should create an ActionReceipt for each AI message (5min undo window). Currently `SendMessageService` does not call any receipt creation method, so this gap is not yet breaking — but receipt creation will require a `create()` method.
**Fix:** Add `create(message_id, conversation_id, tenant_id, clinic_id, expires_at)` method. Coordinate with T-inbox-be-3 fix.

## Contract Compliance

- [x] 4 SQLAlchemy 2.0 models with `mapped_column()`, `Mapped[]`, `PG_UUID`, `DateTime(timezone=True)`
- [x] 4 repositories inherit `CompoundScopeRepositoryBase scope_field="clinic_id"`
- [x] Migration 024 raw SQL `IF NOT EXISTS` idempotent
- [x] Composite indexes `(tenant_id, clinic_id, ...)` with partial `WHERE deleted_at IS NULL`
- [ ] **All repo methods called by services are implemented** — FAIL (see above)

## Gherkin coverage

| Scenario | Tests | Status |
|---|---|---|
| SC-04 adversarial dual-filter | `test_conversation_repository.py::test_dual_filter_get_by_id`, `test_dual_filter_list_for_inbox`, `test_message_repository.py::test_dual_filter_get_by_id` | ✅ Tests exist and pass |
| SC-03 OCC | `test_conversation_repository.py::test_update_handler_mode_occ_conflict` | ✅ Test exists and passes |

## Architecture fitness allowlists

No allowlist growth detected. Arch fitness suite 268/268 PASS.

## Verdict

**CHANGES_REQUESTED** — repository method gaps block Slice 1 acceptance.

The dual-filter base, models, migration, and SQL primitives are clean. But T-inbox-be-3 services depend on repo methods that don't exist. End-to-end happy path (send → action receipt → retract) cannot run against real DB. Tests pass only because unit-level mocks accept any method.

**Required fixes:**
1. Add `MessageRepository.create()` async method.
2. Add `MessageRepository.mark_retracted()` async method.
3. Add `MessageRepository.find_patient_reply_after()` async method.
4. Add `ConversationRepository.get_or_create_for_lead()` async method.
5. Add `ActionReceiptRepository.create()` async method (needed when T-inbox-be-3 wires receipt creation).
6. Add integration tests that bind the real repos and verify the methods land rows correctly.
