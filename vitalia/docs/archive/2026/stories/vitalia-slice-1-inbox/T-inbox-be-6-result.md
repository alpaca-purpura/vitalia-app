# T-inbox-be-6 result — extensions register retract_last_message + arch test no_hardcoded_strings_inbox

**Ticket:** T-inbox-be-6
**Story:** vitalia-slice-1-inbox
**State:** done
**SHA:** (filled by commit)

## Summary

Extended `vitalia/backend/src/modules/vitalia/extensions.py` to register
`retract_last_message` via Extension SDK EP-3 (`sales_agent_tool_register`).
Added new test file verifying the registration. Added arch fitness gate
scanning inbox + crm Slice 1 source files for hardcoded strings.

## Skills Consulted (must_load enforcement v4.1)

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | Mandatory for all backend tickets | Runtime quality checklist confirmed: no anti-patterns (no SQLAlchemy legacy, no `from_orm()`, no `print()`, no hardcoded USD) |
| `.claude/rules/backend-ddd.md` | Extensions.py is DDD consumer layer | Confirmed: import at module level, no business logic in extension registration; delegate to service per DDD |
| `.claude/rules/anti-duplication.md` | Extension via Extension SDK EP — not direct import | Confirmed: `retract_last_message` is brand-local tool (not cross-brand mirror); EP-3 registration is the correct pattern per SDK CC-4 namespace |
| `.claude/rules/architectural-fitness.md` | Arch test new gate | Ratchet pattern applied: `KNOWN_LEGACY_STRINGS = ()` at inception (shrink-only) |
| `.claude/rules/tdd-mandatory.md` | TDD RED→GREEN contract | RED tests written first, confirmed FAIL before GREEN implementation |
| `.claude/rules/spanish-text.md` | Arch test scans voseo | VOSEO_PATTERN compiled from § R2 glosario verbatim |
| `.claude/rules/hipaa-lite.md` | HIPAA-lite dual filter cardinal | Both `tenant_id` AND `clinic_id` in input_schema + required array |
| `.claude/rules/auditor-self-fix-policy.md` | Loaded per ticket mandate | No auditor self-fix scope triggered |

## Files Changed

| File | Action | Description |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/extensions.py` | EXTEND | Added import for `retract_last_message` + EP-3 ToolDef registration block |
| `vitalia/backend/tests/modules/vitalia/test_extensions_inbox_registration.py` | NEW | 14 tests verifying EP-3 registration (name, handler, input_schema, tool_groups, HIPAA-lite fields) |
| `vitalia/backend/tests/architecture/test_no_hardcoded_strings_inbox.py` | NEW | Arch fitness gate: scans inbox + crm Slice 1 for hardcoded voseo/USD/UUID strings; KNOWN_LEGACY_STRINGS=() ratchet |

## CAVEAT Verification

Checked `extensions.py` for pre-existing `retract_last_message` registration.
**Result: NOT registered** (agentic-1 scope was the tool implementation only;
be-6 scope is the EP-3 registration). Full registration implemented.

## EP-3 ToolDef Registration

```python
registry.sales_agent_tool_register(
    ToolDef(
        name="vitalia.retract_last_message",
        description="Retract a message Adrián sent within the 5-minute undo window. ...",
        input_schema={
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "format": "uuid"},
                "clinic_id": {"type": "string", "format": "uuid"},
                "conversation_id": {"type": "string", "format": "uuid"},
                "message_id": {"type": "string", "format": "uuid"},
                "reason": {"type": "string", "minLength": 10, "maxLength": 500, ...},
            },
            "required": ["tenant_id", "clinic_id", "conversation_id", "message_id", "reason"],
        },
        handler=retract_last_message,  # LangChain StructuredTool from T-inbox-agentic-1
        tool_groups=("sales_agent", "vertical_medical", "inbox", "retract"),
    ),
)
```

## TDD Summary

| Phase | Result |
|---|---|
| RED — test_extensions_inbox_registration.py (14 tests) | FAIL (tool not registered) |
| RED — test_no_hardcoded_strings_inbox.py (3 tests) | PASS (no violations in existing code) |
| GREEN — extensions.py extended | 14/14 PASS |
| Full suite after GREEN | 67/67 PASS |

## Quality Gates

| Gate | Result |
|---|---|
| `ruff check` | 0 errors |
| `ruff format --check` | 0 files to reformat |
| arch fitness full suite | 268/268 PASS |
| test_extensions.py | 39/39 PASS |
| test_extensions_inbox_registration.py | 14/14 PASS |
| test_no_hardcoded_strings_inbox.py | 3/3 PASS |
| test_extension_sdk_registration.py | 11/11 PASS |

## EP-3 Count Post T-inbox-be-6

- 4 T-infra-2 baseline (placeholders)
- 4 Valeria wizard tools (Wave 3 real)
- 3 Adrián MVP tools (Wave 3 real)
- 1 send_proactive_reengagement (T-9)
- 1 retract_last_message (T-inbox-be-6) ← NEW

**Total: 13 tools** (≥12 threshold asserted in test)
