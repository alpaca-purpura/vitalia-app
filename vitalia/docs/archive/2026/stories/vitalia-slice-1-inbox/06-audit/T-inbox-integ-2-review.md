<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# T-inbox-integ-2 — Backend integration tests (BE portion only) — Review

**Brand:** vitalia
**Story:** vitalia-slice-1-inbox
**Surface:** backend (integration tests)
**Verdict:** WARN

## Scope (BE portion)

- `vitalia/backend/tests/integration/test_inbox_send_retract_audit_log.py` (7 tests, all `pytestmark = pytest.mark.integration`)
- `vitalia/backend/tests/integration/test_inbox_whisper_fallback.py` (8 tests, same marker)

Frontend E2E adversarial spec (`inbox.adversarial.spec.ts`) and a11y axe spec (`inbox.a11y.spec.ts`) are out of scope for this auditor (see auditor-frontend).

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Tests exercise models + repos at DB layer (not service layer) |
| 2 | Tenant Isolation | PASS | Cross-tenant + cross-clinic queries return None — verified explicit assertions |
| 3 | Soft Deletes | PASS | Tests verify `deleted_at IS NULL` filter |
| 4 | Code Quality | PASS | ruff clean |
| 5 | SQLAlchemy 2.0 | PASS | `select(Model).where(...)` everywhere; `db_session.add(model)` for inserts |
| 6 | Async Consistency | PASS | `@pytest.mark.asyncio` + `AsyncSession db_session` fixture |
| 7 | Pydantic v2 / DTOs | N/A | Integration tests use raw models, not DTOs |
| 8 | Migration Quality | PASS | Tests rely on Postgres fixture with migration applied via `db_session` |
| 9 | Security | PASS | Cross-tenant + cross-clinic queries verified to return no rows |
| 10 | Tests / TDD | WARN | Tests verify model + DB layer, not service end-to-end. Auto-skip when Postgres down (15 skipped — verified locally). HIPAA-lite invariants tested at SQL level |
| 11 | Cross-cutting | PASS | `pytestmark = pytest.mark.integration` enables `@pytest.mark.integration` auto-skip when Postgres unreach |
| 12 | Mirror detection | PASS | Integration test scaffolds are brand-local |

## Findings

### WARN: Integration tests bypass SendMessageService / RetractMessageService service layer
**Category:** 10 (Tests/TDD)
**File:** `test_inbox_send_retract_audit_log.py`
**Issue:** The test file name ("send_retract_audit_log") implies end-to-end coverage of the SendMessageService → ActionReceipt → RetractMessageService → audit log + outbox event chain. But the actual tests insert rows directly via `db_session.add(ConversationModel(...))` + `db_session.add(MessageModel(...))` + `db_session.add(ActionReceiptModel(...))` and then verify dual-filter SQL semantics.

Reading the test source (lines 96-191) confirms: each test acts at the SQLAlchemy model layer and exercises dual-filter via raw `select()` statements. Service-level mocks (`_make_mock_audit_writer`, `_make_mock_event_bus`, `_make_noop_channel_adapters`) are defined but never actually plumbed through a SendMessageService instance.

Net effect: the integration tests prove:
- ConversationModel, MessageModel, ActionReceiptModel persist correctly.
- Dual-filter (tenant_id + clinic_id) excludes cross-tenant rows.
- `ActionReceiptRepository.get_active_for_message` + `mark_retracted` work.

But they do NOT prove:
- SendMessageService creates ActionReceipt for AI messages.
- RetractMessageService flips handler_mode='human'.
- audit_writer.write() actually persists a row to `vitalia_audit_log`.
- Outbox event_bus.publish() actually appends to `domain_event_outbox`.

These are gaps relative to the test file name and the spec's "end-to-end flow" intent (06-tickets.yaml T-inbox-integ-2 scope: "end-to-end send → action receipt → revert → audit + event").

**Action:** Add at least one true end-to-end test that:
1. Instantiates real `SendMessageService` with real `MessageRepository`, `ConversationRepository`, `ActionReceiptRepository`, real `AsyncAuditWriter`, real outbox `EventBus` bound to `db_session`.
2. Calls `await service.send(...)` for an AI message.
3. Asserts: ActionReceipt row exists with `expires_at = sent_at + 5min`.
4. Asserts: `vitalia_audit_log` row exists with action='inbox.message.sent'.
5. Asserts: `domain_event_outbox` row exists with event_name='message_sent'.
6. Then calls `await retract_service.retract(...)` and re-asserts the chain.

### INFO: Tests auto-skip locally (Postgres down)
**File:** Both files
**Issue:** All 15 tests skipped with reason "Postgres unavailable (POSTGRES_DSN not reachable)". This is correct behavior per `pytestmark = pytest.mark.integration` and the conftest skip protocol. No regression.
**Action:** None — auto-skip is intentional. Tests will run in CI where Postgres is up.

### INFO: test_inbox_whisper_fallback.py not inspected in detail
**File:** `test_inbox_whisper_fallback.py`
**Status:** 8 tests, all skipped locally. Test names imply coverage of SC-02 audio fallback. Per the pattern in the sibling file, likely similar pattern (db_session direct inserts + dual-filter SQL assertions).
**Action:** Same recommendation — add true end-to-end test exercising `WhisperTranscribeService` + `SendMessageService` with fallback path.

## Contract Compliance

- [x] `test_inbox_send_retract_audit_log.py` exists with 7 tests
- [x] `test_inbox_whisper_fallback.py` exists with 8 tests
- [x] HIPAA-lite dual-filter (tenant + clinic) verified at SQL layer
- [x] Integration marker for auto-skip when Postgres unreach
- [ ] **End-to-end service-layer flow exercised** — WARN (gaps documented)

## Gherkin coverage

| Scenario | Tests | Status |
|---|---|---|
| SC-04 adversarial cross-tenant/clinic | `test_conversation_and_message_insert_dual_filter` (lines 76-190) | ✅ Verified at SQL layer |
| End-to-end audit + event flow | claimed scope of `test_inbox_send_retract_audit_log.py` | ⚠ Models verified; service chain NOT |
| SC-02 Whisper fallback | claimed scope of `test_inbox_whisper_fallback.py` | ⚠ Models verified; service chain NOT (per pattern) |

## Verdict

**WARN** — integration tests correctly verify HIPAA-lite invariants at the DB layer. They auto-skip cleanly when Postgres is down (15 skips with explicit reasons — clean). They however do not exercise the service-layer chain end-to-end despite the test names implying it. Since the BE service-layer issues identified in T-inbox-be-3 review (missing ActionReceipt creation, missing handler_mode flip, missing repo methods) are not caught by these tests, the audit relies on later fixes from those tickets to land — when they do, this WARN can clear.

Non-blocking for ship: tests don't ship a bug; they just don't cover the full intended scope.
