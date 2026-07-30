<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# T-inbox-be-1 — Backend domain entities + events — Review

**Brand:** vitalia
**Story:** vitalia-slice-1-inbox
**Surface:** backend (domain layer)
**Verdict:** PASS

## Scope

4 NEW PHI domain entities (Conversation, Message, ActivityEvent, ActionReceipt) + 6 domain events (ConversationStarted, MessageSent, MessageRetracted, ModeChanged, AdrianPaused, ProactiveOutboundSent).

Paths reviewed:
- `vitalia/backend/src/modules/vitalia/crm/domain/conversation.py`
- `vitalia/backend/src/modules/vitalia/crm/domain/message.py`
- `vitalia/backend/src/modules/vitalia/crm/domain/activity_event.py`
- `vitalia/backend/src/modules/vitalia/crm/domain/action_receipt.py`
- `vitalia/backend/src/modules/vitalia/crm/domain/events.py`

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Pure Python dataclasses, no ORM/framework imports in domain |
| 2 | Tenant Isolation | PASS | All entities carry tenant_id + clinic_id (PHI dual filter) |
| 3 | Soft Deletes | PASS | `deleted_at: datetime \| None = None` on Conversation + Message |
| 4 | Code Quality | PASS | ruff check/format clean (verified) |
| 5 | SQLAlchemy 2.0 | N/A | Pure domain layer |
| 6 | Async Consistency | N/A | Pure domain layer |
| 7 | Pydantic v2 / DTOs | PASS | DomainEvent inherited from `luana_core_platform.domain.events` |
| 8 | Migration Quality | N/A | Covered by T-inbox-be-2 |
| 9 | Security | PASS | OCC token (`updated_at`) on Conversation for SC-03 |
| 10 | Tests / TDD | PASS | Domain tests cover invariants + enums + state machine (4 test files, 287 tests pass) |
| 11 | Cross-cutting | PASS | `datetime` types use timezone-aware via `field(default_factory=lambda: datetime.now(UTC))` |
| 12 | Mirror detection | PASS | `DomainEvent` imported from engine (luana_core_platform); NO mirror |

## Findings

### INFO: PatientOptedOut event appears in events.py with T-2 attribution
**File:** `crm/domain/events.py:132-153`
**Issue:** `PatientOptedOut` event is included; comment says "T-2: emitted by PatientConsentService". This is a fidelización event, not strictly an inbox event per 03-arch-be.md § 3.5 (which lists 6 events).
**Action:** No action required — pre-existing from sibling story (vitalia-slice-1-fidelizacion). Not introduced by T-inbox-be-1.

## Contract Compliance

- [x] All 4 entities present (Conversation, Message, ActivityEvent, ActionReceipt)
- [x] All 6 NEW events present (ConversationStarted, MessageSent, MessageRetracted, ModeChanged, AdrianPaused, ProactiveOutboundSent)
- [x] Enums via `Literal[...]` per spec
- [x] OCC token (`updated_at`) on Conversation for SC-03

## Gherkin coverage

| Scenario | Tests | Status |
|---|---|---|
| SC-01 happy (entities valid) | `crm/domain/test_conversation.py`, `test_message.py`, `test_action_receipt.py` | ✅ Tests exist and pass |
| SC-03 edge (OCC updated_at) | `crm/domain/test_conversation.py::test_occ_updated_at_present` | ✅ Test exists and passes |

## Verdict

**PASS** — clean domain layer. Pure Python, no ORM/framework imports. PHI dual-filter keys present on every entity. OCC token in place. Tests cover invariants.
