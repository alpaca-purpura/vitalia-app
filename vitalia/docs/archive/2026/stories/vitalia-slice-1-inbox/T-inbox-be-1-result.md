# T-inbox-be-1 Result

> Ticket: T-inbox-be-1 — Backend domain — Conversation + Message + ActivityEvent + ActionReceipt entities + events
> Story: vitalia-slice-1-inbox
> Branch: wip/vitalia
> Date: 2026-05-20

## Summary

Implemented 4 PHI domain entities + 6 domain events for Vitalia CRM inbox (Inside-Out DDD domain layer, pure Python, zero ORM imports).

## Validators GREEN

| Validator | Command | Result |
|---|---|---|
| be_lint_ruff_check | `ruff check vitalia/backend/src/modules/vitalia/crm/domain/ vitalia/backend/tests/modules/vitalia/crm/domain/ --no-cache` | GREEN — 0 errors |
| be_format_ruff_check | `ruff format --check vitalia/backend/src/modules/vitalia/crm/domain/ vitalia/backend/tests/modules/vitalia/crm/domain/` | GREEN — 14 files formatted |
| be_test_inbox | `pytest vitalia/backend/tests/modules/vitalia/crm/domain/ -v` | GREEN — 116 passed |

## Files delivered

### Domain entities (src/modules/vitalia/crm/domain/)

| File | LOC | Key exports |
|---|---|---|
| `conversation.py` | ~94 | `Conversation`, `VALID_CHANNELS`, `VALID_STATUSES`, `VALID_HANDLER_MODES`, `VALID_STAGE_DECISIONS` |
| `message.py` | ~98 | `Message`, `VALID_SENDER_TYPES`, `VALID_MEDIA_KINDS` |
| `activity_event.py` | ~78 | `ActivityEvent`, `VALID_AGENT_IDS` |
| `action_receipt.py` | ~71 | `ActionReceipt`, `VALID_RETRACT_REASONS`, `ACTION_RECEIPT_WINDOW_MINUTES` |
| `events.py` | ~147 | `ConversationStarted`, `MessageSent`, `MessageRetracted`, `ModeChanged`, `AdrianPaused`, `ProactiveOutboundSent` |

### Tests (tests/modules/vitalia/crm/domain/)

| File | Tests | Coverage |
|---|---|---|
| `test_conversation.py` | 26 | PHI dual-filter, OCC updated_at, soft delete, 3 handler modes, enum values, pause_until |
| `test_message.py` | 18 | PHI dual-filter, sender types, media kinds, retraction state machine, SC-02 audio confidence, media_phi_flagged |
| `test_activity_event.py` | 19 | PHI dual-filter, description_es, source_trace_event_id optional, payload_sanitized, agent_ids |
| `test_action_receipt.py` | 20 | PHI dual-filter, 5min expiry window, state machine, VALID_RETRACT_REASONS |
| `test_events.py` | 33 | All 6 events, event_name strings, PHI dual-filter in events, SC-01 + SC-03 OCC via ModeChanged |

**Total: 116 tests passing**

## Gherkin coverage

| Scenario | Tests that cover it |
|---|---|
| SC-01: Adrián closes appointment, ActivityStream events | `test_conversation.py::TestConversationHandlerModes::test_handler_mode_ai_adrian_decide` · `test_message.py::TestMessageSentType::test_sender_type_agent_ai_marks_ai_action` · `test_action_receipt.py::TestActionReceiptExpiryWindow::test_expires_at_5_minutes_from_creation` · `test_events.py::TestMessageSent`, `TestConversationStarted`, `TestAdrianPaused` |
| SC-03: Concurrent edit OCC | `test_conversation.py::TestConversationOCC::test_updated_at_is_occ_token` · `test_events.py::TestModeChanged::test_occ_previous_updated_at_present` |
| SC-02: Audio low confidence (covered in domain) | `test_message.py::TestMessageWhisperSTT::test_transcription_confidence_below_0_5_triggers_fallback` |
| SC-04: PHI dual-filter adversarial | All test classes have `test_action_receipt_has_tenant_id` + `test_action_receipt_has_clinic_id` patterns across all 4 entities |

## Key design decisions

1. **Pure Python @dataclass** — domain layer zero ORM imports per `backend-ddd.md`. No Pydantic in domain entities.
2. **PHI dual-filter on ALL entities** — `tenant_id: UUID` + `clinic_id: UUID` on every entity per `hipaa-lite.md § Regla cardinal`.
3. **DomainEvent inheritance** — all 6 events extend `luana_core_platform.domain.events.DomainEvent` via `from luana_core_platform.domain.events import DomainEvent`. No reimplementation per `anti-duplication.md`.
4. **`frozenset[str]` constants** — `VALID_CHANNELS`, `VALID_SENDER_TYPES`, etc. exported from entity modules for runtime validation and test assertions.
5. **OCC via updated_at** — `Conversation.updated_at` is the SC-03 OCC token; `ModeChanged` event carries `previous_updated_at` for conflict detection.
6. **5min window constant** — `ACTION_RECEIPT_WINDOW_MINUTES = 5` exported constant (not magic number) per SC-01 spec.
7. **ActivityEvent anti-duplication** — explicit docstring noting "NOT a mirror of copilot_trace_event" + `source_trace_event_id` optional FK for projection origin tracking.
8. **email NOT in ChannelType** — per arch spec § 3.1 `ChannelType = Literal["whatsapp", "instagram", "facebook_messenger", "web", "walk_in", "phone"]`. Email is used for retraction fallback only (retract_succeeded=False), not a conversation channel.

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When consulted | Decision made |
|---|---|---|---|
| `backend-expert` | CONSULTED | Before writing domain entities | Used pure @dataclass (not Pydantic) for domain layer; frozenset constants for enum values |
| `.claude/rules/tenant-isolation.md` | CONSULTED | Before writing entities | Every entity carries tenant_id; every event carries tenant_id + clinic_id |
| `.claude/rules/backend-ddd.md` | CONSULTED | Before writing entities | Domain layer = pure Python, zero ORM imports. Inside-Out layering confirmed. |
| `.claude/rules/spanish-text.md` | CONSULTED | Before writing ActivityEvent | `description_es` field docstring: "3rd person narrated form" not tuteo/voseo. No voseo in any user-facing string. |
| `.claude/rules/anti-duplication.md` | CONSULTED | Before writing events.py | Verified DomainEvent in `luana_core_platform.domain.events` — consumed via import, not reimplemented. No cross-brand mirrors. |
| `.claude/rules/tdd-mandatory.md` | CONSULTED | Before any implementation | RED phase confirmed (ImportError before entities existed). GREEN after implementation. |
| `vitalia/.claude/rules/hipaa-lite.md` | CONSULTED | Before writing entity fields | PHI dual-filter (tenant_id + clinic_id) mandatory on ALL PHI entities per § Regla cardinal. clinic_id added to all domain events too. |
| `.claude/rules/auditor-self-fix-policy.md` | CONSULTED | On ruff lint failures | Auto-fixed unused imports (whitelist category #16) — 8 fixable ruff issues resolved. |

## Notes for T-inbox-be-2 (migrations)

- `CompoundScopeRepositoryBase` from `luana_core_platform` (v0.4.0) is already shipped. T-inbox-be-2 will implement repositories inheriting from it with PHI dual-filter (`tenant_id` + `clinic_id`).
- 4 new Postgres tables needed: `vitalia_conversations`, `vitalia_messages`, `vitalia_activity_events`, `vitalia_action_receipts`.
- All migrations must use `CREATE TABLE IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS` (idempotent raw SQL).
