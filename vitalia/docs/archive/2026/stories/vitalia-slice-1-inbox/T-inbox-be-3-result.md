# T-inbox-be-3 Result — Backend Application Services (Inbox)

> Story: `vitalia-slice-1-inbox`
> Ticket: T-inbox-be-3
> Status: tests-passing
> Tests: 35/35 PASS (inbox) + 265/265 PASS (arch fitness) = 300/300 total

## Summary

Implemented all 9 application services for the vitalia inbox module following TDD (RED → GREEN):

1. `_templates.py` — 5 Meta-approved HSM templates registry (UTILITY + MARKETING categories)
2. `send_message_service.py` — SendMessageService with idempotency + outbox events + audit
3. `retract_message_service.py` — RetractMessageService with 5min window + OCC + fallback
4. `set_mode_service.py` — SetModeService with OCC via expected_updated_at
5. `pause_adrian_service.py` — PauseAdrianService with Redis TTL + DB column
6. `proactive_outbound_service.py` — ProactiveOutboundService with ComplianceService gate
7. `whisper_transcribe_service.py` — WhisperTranscribeService with confidence 0.5 threshold
8. `activity_event_service.py` — ActivityEventService with sanitize_payload defense-in-depth
9. `tools_state_service.py` — ToolsStateService, read-only offer preset mapping
10. `inbox_orchestrator.py` — InboxOrchestrator composing Lead+Conv+Msg+Activity

Plus 7 DTO files and 9 test files (TDD RED first, then GREEN).

## Skills Consulted

| Skill | Invoked | Decision |
|---|---|---|
| `backend-expert` | YES — per Step 0 GATE mandatory | Anti-patterns: no ORM in services, no FastAPI imports, SQLA 2.0 patterns, tenant_id in every query |
| `tessl__fastapi` | YES — mandatory | response_model mandatory, Annotated deps, async throughout, redirect_slashes=False |
| `tessl__pytest-api-testing` | YES — mandatory | AsyncMock pattern, factory fixtures, DB isolation, error flow tests |
| `tessl__graceful-degradation` | YES — external calls exist (Whisper, channel adapters, Redis) | 30s timeout on Whisper, ChannelRetractUnsupportedError fallback, soft-fail on Redis |

## Files Created

### Application Services
- `vitalia/backend/src/modules/vitalia/inbox/application/services/_templates.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/services/send_message_service.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/services/retract_message_service.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/services/set_mode_service.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/services/pause_adrian_service.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/services/proactive_outbound_service.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/services/whisper_transcribe_service.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/services/activity_event_service.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/services/tools_state_service.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/services/inbox_orchestrator.py`

### DTOs
- `vitalia/backend/src/modules/vitalia/inbox/application/dto/send_message_dto.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/dto/retract_message_dto.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/dto/set_mode_dto.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/dto/conversation_list_dto.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/dto/proactive_outbound_dto.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/dto/tools_state_dto.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/dto/activity_event_dto.py`

### Tests (TDD RED → GREEN)
- `vitalia/backend/tests/modules/vitalia/inbox/application/test_send_message_service.py` (5 tests)
- `vitalia/backend/tests/modules/vitalia/inbox/application/test_retract_message_service.py` (6 tests)
- `vitalia/backend/tests/modules/vitalia/inbox/application/test_set_mode_service.py` (3 tests)
- `vitalia/backend/tests/modules/vitalia/inbox/application/test_pause_adrian_service.py` (3 tests)
- `vitalia/backend/tests/modules/vitalia/inbox/application/test_proactive_outbound_service.py` (5 tests)
- `vitalia/backend/tests/modules/vitalia/inbox/application/test_whisper_transcribe_service.py` (4 tests)
- `vitalia/backend/tests/modules/vitalia/inbox/application/test_activity_event_service.py` (3 tests)
- `vitalia/backend/tests/modules/vitalia/inbox/application/test_tools_state_service.py` (3 tests)
- `vitalia/backend/tests/modules/vitalia/inbox/compliance/test_phi_sanitize_and_compliance_gate.py` (3 tests)

### Init files
- `vitalia/backend/src/modules/vitalia/inbox/__init__.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/__init__.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/services/__init__.py`
- `vitalia/backend/src/modules/vitalia/inbox/application/dto/__init__.py`
- `vitalia/backend/src/modules/vitalia/inbox/api/__init__.py`
- `vitalia/backend/tests/modules/vitalia/inbox/__init__.py`
- `vitalia/backend/tests/modules/vitalia/inbox/application/__init__.py`
- `vitalia/backend/tests/modules/vitalia/inbox/compliance/__init__.py`
- `vitalia/backend/tests/modules/vitalia/inbox/api/__init__.py`

## Key Design Decisions

### PHI Dual-Filter (hipaa-lite.md)
Every service call uses `get_by_id(id=..., tenant_id=..., scope_id=clinic_id)` — never tenant-only. CompoundScopeRepositoryBase enforces at infra layer.

### Event Field Alignment
Events built against actual domain event dataclass signatures (discovered via Read):
- `ModeChanged` → `previous_handler_mode`, `new_handler_mode`, `previous_updated_at`
- `AdrianPaused` → `pause_until`, `paused_by_user_id`
- `ProactiveOutboundSent` → `message_id`, `outbound_kind`
- `MessageRetracted` → `retract_succeeded`, `retract_reason` (no `retracted_by_user_id`)

### sanitize_payload
Actual signature: `sanitize_payload(payload: dict) -> dict` — no `compliance_level` parameter. Applied as defense-in-depth in ActivityEventService.

### Pre-existing Failure
`test_manual_call_service.py::test_record_call_creates_event_and_audit` fails due to `ReEngagementOutcome.SCHEDULED` → should be `RESCHEDULED`. This is a fidelizacion module test (parallel T-5 ticket) — pre-existing, unrelated to inbox services.

## Quality Gates

- `ruff check`: 0 errors
- `ruff format --check`: 0 files to reformat
- `pytest vitalia/backend/tests/modules/vitalia/inbox/`: 35/35 PASS
- `pytest vitalia/backend/tests/architecture/`: 265/265 PASS
- Combined: 300/300 PASS
