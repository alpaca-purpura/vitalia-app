<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# T-inbox-be-3 — Inbox application services — Review

**Brand:** vitalia
**Story:** vitalia-slice-1-inbox
**Surface:** backend (application layer)
**Verdict:** CHANGES_REQUESTED

## Scope

8 services: `SendMessageService`, `RetractMessageService`, `SetModeService`, `PauseAdrianService`, `ProactiveOutboundService`, `WhisperTranscribeService`, `ActivityEventService`, `ToolsStateService` + `InboxOrchestrator` + 7 DTOs + `_templates.py`.

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Services orchestrate repos + adapters; no direct DB queries |
| 2 | Tenant Isolation | PASS | Every service method takes tenant_id + clinic_id and passes to repo (via `scope_id=clinic_id`) |
| 3 | Soft Deletes | N/A | Application layer |
| 4 | Code Quality | PASS | ruff check/format clean |
| 5 | SQLAlchemy 2.0 | N/A | Application layer |
| 6 | Async Consistency | PASS | All service methods `async def`; `await` on every repo call |
| 7 | Pydantic v2 / DTOs | PASS | DTOs use `model_config = ConfigDict(from_attributes=True)` |
| 8 | Migration Quality | N/A | Application layer |
| 9 | Security | PASS | RBAC enforced at router; services receive resolved tenant_id from JWT; compliance gate in ProactiveOutboundService |
| 10 | Tests / TDD | WARN | Unit tests pass with AsyncMock repos, but Gherkin-named tests cited in 06-tickets do NOT exist verbatim (see findings) |
| 11 | Cross-cutting | PASS | Spanish neutro in error strings (tuteo); no voseo. `datetime.now(UTC)` (no `datetime.utcnow()`) |
| 12 | Mirror detection | PASS | All services brand-local; consume engine `luana_core_observability.recording.sanitization`, `luana_core_platform.domain.events`, `luana_core_idempotency` — NO mirror of engine abstractions |

## Findings

### FAIL: SendMessageService never creates ActionReceipt for AI messages
**Category:** 10 (Tests/TDD) + spec violation
**File:** `inbox/application/services/send_message_service.py:226, 321`
**Issue:** Per `01-spec-extract.md § 9` (Action Receipts) and `03-arch-be.md § 6.2`, every AI message (handler_mode='ai') MUST create an `ActionReceipt` with `expires_at = sent_at + 5min` so the UI can render the "↩ Revertir (4:58)" chip (SC-01).

Current code:
- Service receives `receipt_repo: ActionReceiptRepository` in `__init__` (line 134) but never calls it.
- Returns `action_receipt_expires_at=None` in BOTH return paths (cache hit line 226 + happy path line 321).
- No `receipt_repo.create(...)` call anywhere.

Net effect: SC-01 Gherkin requirement "el mensaje incluye chip '↩ Revertir (4:58)' debajo con countdown 5 min" is unsatisfied — the FE has nothing to render even if the rest of the flow works.

Test gap: 06-tickets cites `test_ai_message_creates_action_receipt` but no test with this name exists. Existing `test_send_message_ai_path_emits_message_sent_event` does not assert receipt creation.

**Fix:**
- In `SendMessageService.send()`, after `msg_repo.create(...)`, when `conv.handler_mode == "ai"`, call `receipt_repo.create(message_id=msg.id, conversation_id=conversation_id, tenant_id=tenant_id, clinic_id=clinic_id, expires_at=now + timedelta(minutes=_ACTION_RECEIPT_WINDOW_MINUTES))`.
- Set `action_receipt_expires_at=expires_at` in `SendMessageResult` for AI path.
- Add unit test `test_ai_message_creates_action_receipt` asserting `receipt_repo.create.assert_awaited_once()` with correct `expires_at`.

### FAIL: RetractMessageService missing handler_mode='human' flip on retract
**Category:** spec violation
**File:** `inbox/application/services/retract_message_service.py`
**Issue:** Per `01-spec-extract.md § 9` and `03-arch-be.md § 6.3`: "Success → update `vitalia_messages.retract_succeeded=true` + `retracted_at` + flip `handler_mode='human'` in conversation."

The EP-3 tool description in `vitalia/backend/src/modules/vitalia/extensions.py:680-684` also claims this:
> "updates vitalia_messages.retracted_at + handler_mode='human'"

But `RetractMessageService.retract()` does NOT call `conv_repo.update_handler_mode(...)` after a successful retract. Conversation stays in `handler_mode='ai'` even after operator pressed undo.

This breaks the user mental model from SC-01: "click ↩ Revertir → restaura composer con texto retractado para edición + cambia handler_mode='human' automático".

**Fix:**
- After successful retract (`retract_succeeded=True`), call `self._conv_repo.update_handler_mode(conversation_id=conversation_id, tenant_id=tenant_id, clinic_id=clinic_id, new_handler_mode='human', expected_updated_at=conv.updated_at)`.
- Emit a `ModeChanged` event in addition to `MessageRetracted`.
- Add test `test_retract_flips_handler_mode_to_human`.

### FAIL (cascades from T-inbox-be-2): Services call repo methods that don't exist
**Category:** 10 (Tests/TDD)
**File:** Multiple services
**Issue:** Services depend on methods that do not exist on the concrete repo classes; tests only pass because they use `AsyncMock`:
- `send_message_service.py:242` → `msg_repo.create(...)` (not implemented)
- `retract_message_service.py:175` → `msg_repo.find_patient_reply_after(...)` (not implemented)
- `retract_message_service.py:214` → `msg_repo.mark_retracted(...)` (not implemented)
- `proactive_outbound_service.py:222` → `conv_repo.get_or_create_for_lead(...)` (not implemented)
- `proactive_outbound_service.py:233` → `msg_repo.create(...)` (not implemented)

**Fix:** Implement missing methods in T-inbox-be-2 (cross-referenced).

### WARN: ActivityEventService discards sanitize_payload result
**Category:** 11 (Cross-cutting)
**File:** `inbox/application/services/activity_event_service.py:113`
**Issue:** Code calls `_ = sanitize_payload(evt.payload_sanitized or {})` but throws the result away. The DTO returned only includes `description_es`, `event_kind`, `agent_id`, `occurred_at` (no raw payload), so PHI doesn't actually leak — but the call is dead code.

Two valid fixes:
1. Remove the call entirely (since payload not returned).
2. If a future DTO field exposes payload, assign sanitized output: `safe_payload = sanitize_payload(evt.payload_sanitized or {})` and include `payload=safe_payload` in the returned item.

Document intent in a code comment either way.

### WARN: audit_writer contract mismatch with vitalia/audit module
**Category:** 11 (Cross-cutting)
**File:** Multiple services
**Issue:** All 5 inbox mutation services expect `audit_writer.write(...)` as an async coroutine (`await self._audit_writer.write(...)`). But the shipped `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` exposes `write_audit_log_sync(db, *, ...)` as a **synchronous** function with positional Session.

Tests pass because they pass `AsyncMock()` which exposes async `.write`. At composition root, there is no real adapter that wires the sync write into an async `audit_writer.write` interface. HIPAA-lite mandate (sync write pre-response) will fail in production.

**Fix:**
- Define a small async adapter `AsyncAuditWriter` in `vitalia/audit/` that takes an `AsyncSession` and exposes `async def write(...) -> None` calling the underlying sync writer inside a sync executor, OR write a parallel async implementation that uses `await db.execute(insert(...))`.
- Wire the real adapter into the router service factories.

### INFO: Test names cited in 06-tickets.yaml::gherkin_coverage don't exist verbatim
**Category:** 10 (Tests/TDD) / process
**File:** Multiple
**Issue:** Story-closure-gate Phase D requires `06-tickets.yaml::gherkin_coverage::tests` to map to real test paths. Examples:
- `test_send_message_service.py::test_ai_message_creates_action_receipt` — NOT FOUND
- `test_send_message_service.py::test_audio_fallback_switches_to_human` — NOT FOUND
- `test_set_mode_service.py::test_occ_conflict_returns_409` — must verify
- `test_retract_message_service.py::test_patient_replied_409` — must verify

Tests with these names should be added (and `test_ai_message_creates_action_receipt` will be the assertion for the action-receipt fix above).

## Contract Compliance

- [x] 8 services + InboxOrchestrator implemented
- [x] DTOs Pydantic v2 with `ConfigDict(from_attributes=True)`
- [x] Idempotency support via optional `IdempotencyStore` in `SendMessageService`
- [x] Compliance gate in `ProactiveOutboundService` (lead.marketing_opt_in + ComplianceService.check)
- [x] Whisper graceful degradation (confidence < 0.5 → fallback)
- [x] 5 HSM templates registered in `_templates.py`
- [ ] **AI message creates ActionReceipt** — FAIL (see findings)
- [ ] **Retract success flips handler_mode='human'** — FAIL (see findings)

## Gherkin coverage

| Scenario | Tests | Status |
|---|---|---|
| SC-01 happy (ai msg + ActionReceipt 5min) | `test_send_message_service.py::test_ai_message_creates_action_receipt` | ❌ Test name NOT FOUND + receipt not created |
| SC-02 negative (Whisper low confidence → fallback) | `test_whisper_transcribe_service.py::test_low_confidence_triggers_fallback`, `test_send_message_service.py::test_audio_fallback_switches_to_human` | ⚠ Whisper test exists; audio fallback handler_mode switch test NOT FOUND |
| SC-03 edge (OCC 409, retract 409 patient-replied) | `test_set_mode_service.py::test_occ_conflict_returns_409`, `test_retract_message_service.py::test_patient_replied_409` | Names cited; verify they exist |
| SC-04 adversarial (PHI sanitize + compliance gate) | `test_proactive_outbound_service.py::test_marketing_opt_in_required`, `test_activity_event_service.py::test_payload_sanitized` | Names cited; verify they exist |

## Verdict

**CHANGES_REQUESTED** — two functional gaps block SC-01 acceptance:
1. AI messages don't create ActionReceipt → undo chip ("↩ Revertir") cannot render → SC-01 fails end-to-end.
2. Retract success doesn't flip `handler_mode='human'` → operator left in inconsistent state → SC-01 narrative violated.
3. Service code references repo methods that don't exist in concrete repos (works only with AsyncMock).

Plus minor:
- audit_writer interface unbound to real implementation.
- ActivityEventService sanitize call discards result (dead code).
- Several Gherkin-named tests cited in 06-tickets.yaml don't exist.

Lint/format/typing clean. Tenant isolation + PHI dual filter correct at the service signatures. Spanish neutro correct in error strings.
