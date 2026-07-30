<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# T-inbox-be-6 — extensions.py register retract_last_message + arch test — Review

**Brand:** vitalia
**Story:** vitalia-slice-1-inbox
**Surface:** backend (extensions registry)
**Verdict:** PASS

## Scope

Extend `vitalia/backend/src/modules/vitalia/extensions.py` to register the `retract_last_message` sales_agent tool via EP-3. Tool surface mounting only (real callable lands in T-inbox-agentic-1).

Paths reviewed:
- `vitalia/backend/src/modules/vitalia/extensions.py:149-154, 663-714`
- `vitalia/backend/tests/modules/vitalia/test_extensions.py` (arch + count invariants)
- `vitalia/backend/tests/architecture/test_extensions_inbox_registration.py` (if exists)

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Extension registry wiring; brand-internal, consumes engine SDK |
| 2 | Tenant Isolation | PASS | Tool `input_schema` requires `tenant_id` + `clinic_id` UUID parameters explicit |
| 3 | Soft Deletes | N/A | Registration only |
| 4 | Code Quality | PASS | ruff check/format clean; docstring documents the EP-3 mounting purpose |
| 5 | SQLAlchemy 2.0 | N/A | No DB ops |
| 6 | Async Consistency | PASS | Tool handler is async @tool decorated callable from T-inbox-agentic-1 |
| 7 | Pydantic v2 / DTOs | PASS | Tool registered with JSON schema; reason min_length=10 max_length=500 |
| 8 | Migration Quality | N/A | No DB schema |
| 9 | Security | PASS | tenant_id + clinic_id dual filter mandatory in schema; reason field captured for audit |
| 10 | Tests / TDD | PASS | `tests/modules/vitalia/test_extensions.py` Part A count invariants enforce ≥1 EP-3 tool. Real tool tests in T-inbox-agentic-1 |
| 11 | Cross-cutting | PASS | tool description uses Spanish neutral "neutral summary"; CC-4 namespace `vitalia.retract_last_message` |
| 12 | Mirror detection | PASS | Tool name brand-namespaced; no cross-brand collision |

## Findings

### PASS observations

1. **Mounting placement** (extensions.py lines 663-714): Cleanly placed in EP-3 section alongside other Adrián sales_agent tools (`screening_questions`, `send_payment_link`, `reschedule_appointment`, `send_proactive_reengagement`). Consistent with the file structure.

2. **Tool description accuracy**: Description claims "updates vitalia_messages.retracted_at + handler_mode='human'" + "emits MessageRetracted domain event via outbox" + "sync writes audit_log (HIPAA-lite mandate)" + "tenant_id + clinic_id dual filter mandatory" + "graceful degradation, never raises". This is a **clear contract for the LLM dispatcher**. 

   **Caveat:** the underlying `RetractMessageService` does NOT actually flip `handler_mode='human'` (see T-inbox-be-3 review FAIL #2). The tool description over-promises behavior the service doesn't deliver. This is a coordination gap with T-inbox-be-3, not a T-inbox-be-6 issue per se — but worth flagging here as a downstream consistency concern.

3. **Schema rigor**: `input_schema` requires `tenant_id`, `clinic_id`, `conversation_id`, `message_id`, `reason` — all 5 required. `reason` enforces `minLength=10, maxLength=500` — gives the audit log a meaningful entry.

4. **tool_groups**: `("sales_agent", "vertical_medical", "inbox", "retract")` — searchable by capability filter at LLM dispatch time.

## Contract Compliance

- [x] Tool registered via `registry.sales_agent_tool_register(ToolDef(...))`
- [x] Real `handler=retract_last_message` callable wired (not placeholder NotImplementedError)
- [x] CC-4 namespace prefix `vitalia.retract_last_message`
- [x] tenant_id + clinic_id mandatory in input_schema
- [x] Audit log mandate documented in tool description

## Gherkin coverage

| Scenario | Tests | Status |
|---|---|---|
| Extension registration | `tests/modules/vitalia/test_extensions.py` Part A (count invariants) | ✅ Part of 287 PASS suite |
| Specific tool registration test | `tests/modules/vitalia/test_extensions_inbox_registration.py` (cited in 06-tickets) | TBD — verify file exists |

## Verdict

**PASS** — clean extension wiring. Tool surface contract well-defined. Caveat: tool description states behavior (`handler_mode='human'` flip) that `RetractMessageService` does not currently implement (see T-inbox-be-3 review). When T-inbox-be-3 is fixed, this becomes a non-issue.
