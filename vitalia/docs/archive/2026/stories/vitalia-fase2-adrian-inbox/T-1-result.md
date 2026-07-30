# T-1 Result — BE un-stub ComplianceService real + PhiChannelPolicy

**Story:** vitalia-fase2-adrian-inbox
**Ticket:** T-1
**Commit:** `86e75e3d`
**Branch:** `worktree-agent-ac459e9936e378c2e` (agent worktree off wip/vitalia)

---

## Diff Summary

### Files Created (NEW)

| File | Purpose |
|---|---|
| `vitalia/backend/src/modules/vitalia/inbox/application/policies/__init__.py` | Package init for policies layer |
| `vitalia/backend/src/modules/vitalia/inbox/application/policies/phi_channel_policy.py` | PhiChannelPolicy — implements CompliancePolicy Protocol, blocks PHI clinical keywords on whatsapp/sms |
| `vitalia/backend/tests/modules/vitalia/inbox/application/test_phi_channel_policy.py` | 9 unit tests (TDD RED-first, all GREEN) |
| `vitalia/backend/tests/modules/vitalia/inbox/compliance/test_phi_voice_redirect.py` | 4 integration tests (stub filled) |

### Files Modified

| File | Changes |
|---|---|
| `vitalia/backend/src/modules/vitalia/inbox/application/services/send_message_service.py` | Added optional `compliance_service` + `activity_event_repo` params; PHI compliance gate before send |
| `vitalia/backend/src/modules/vitalia/inbox/api/router.py` | Removed `_NoOpComplianceService`; added `_get_compliance_service()` factory; wired real ComplianceService in send + proactive paths |

---

## Validator Gate Output (literal)

```
Tests (native Linux host, ${WS}/.venv/bin/pytest):

  Inbox test suite:
    84 passed in 0.99s

  Architecture fitness:
    335 passed, 2 warnings in 3.43s

  Ruff lint:
    All checks passed!

  Ruff format:
    50 files already formatted
```

### Acceptance validators satisfied

| Validator ID | Result | Notes |
|---|---|---|
| fn-be-phi-policy | PASS | 9 tests: PHI block whatsapp/sms, allow web/email/instagram, Protocol compliance |
| av-be-arch-fitness | PASS | 335 arch tests green (DDD boundaries, response_model, PHI dual filter, etc.) |
| av-no-sales-agent-import | PASS | No imports from `sales_agent/` in any modified file |
| av-no-core-edit | PASS | No files in `core/**` modified |

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Mandatory for BE implementation — DDD patterns, FastAPI DI, SQLA 2.0, audit sync write | Followed `runtime-quality-checklist.md` patterns; optional compliance_service param for backward-compat; activity event via `session.add()` + `flush()` |
| `sales-agent-expert` | Anti-duplication check: verify we consume `send_proactive_reengagement` tool via resolver (NOT direct import) | Confirmed T-1 does NOT import `sales_agent/` — PhiChannelPolicy only affects inbox DI wiring |
| `tenant-isolation.md` | Every query dual filter tenant+clinic | `compliance_service.check()` carries `tenant_id`; conversation fetched with `scope_id=clinic_id` before gate runs |
| `backend-ddd.md` | Inside-Out layering; response_model= mandatory; NO business logic in api/ | Policy lives in `application/policies/` (not api/ or domain/); router stays thin |
| `hipaa-lite.md` | Vitalia overlay: dual filter + audit sync + PHI no-leak in descriptions | Activity event `description_es` has no raw PHI; audit row `compliance_block_outbound_phi` written sync pre-response |
| `tdd-mandatory.md` | RED tests before implementation | 9 + 4 tests written first (confirmed ModuleNotFoundError RED), then implementation → GREEN |

---

## Technical Decisions

### PhiChannelPolicy design

**Protocol extension, not mirror:**
`PhiChannelPolicy` implements `CompliancePolicy` Protocol from `core/luana-core-compliance/`. This is an EXTENSION (brand-local policy wired via DI) — no engine code modified, no cross-module mirror. Per `anti-duplication.md` engine inventory table.

**`identifier` param adapter:**
The Protocol's `identifier: str` was designed for phone number / recipient ID. In the inbox context, we repurpose it to carry the outbound message body text for PHI heuristic check. Documented in the policy docstring. `lead_id` is not available in `SendMessageService.send()` — we pass `conversation_id` as a sentinel (PhiChannelPolicy ignores it).

**Keyword heuristic is the last-resort net:**
The primary guard for PHI channel violations is the sales_agent voice instruction (`system_instruction` from `PersonalityProfile`). PhiChannelPolicy is the infrastructure fallback (defense in depth, per hipaa-lite.md § Voice patterns). 23 Spanish LatAm clinical keywords.

**Channels in scope: `whatsapp` + `sms` only:**
Instagram is NOT in `_UNENCRYPTED_CHANNELS` (Meta E2E encrypted, different risk profile per hipaa-lite.md).

### SendMessageService changes

Added optional `compliance_service` + `activity_event_repo` params (backward-compatible — all existing tests pass without modification). The compliance gate runs only when `compliance_service is not None AND body_text is not None`. On block:
1. `body_text` replaced with `_PORTAL_REDIRECT_MICROCOPY` (Spanish neutro LatAm, no PHI)
2. Activity event `compliance_block_outbound_phi` written (description_es sanitized, no raw PHI per RN-10)
3. Audit row `compliance_block_outbound_phi` written sync pre-response (HIPAA-lite)

### Router DI wiring

- Removed `_NoOpComplianceService` (Slice 1 stub)
- Added `_get_compliance_service()` factory → `ComplianceService([PhiChannelPolicy()])`
- `_get_send_service()`: wires `compliance_service=_get_compliance_service()` + `activity_event_repo=ActivityEventRepository(session)`
- `_get_proactive_service()`: wires `compliance_service=_get_compliance_service()` (replaces `_NoOpComplianceService()`)
- `ComplianceService` import has graceful fallback (no-op class) for offline environments

---

## Test Coverage

| Test file | Tests | Coverage |
|---|---|---|
| `test_phi_channel_policy.py` | 9 | PHI block whatsapp/sms; non-PHI allow; web/email/instagram allow; empty msg allow; Protocol isinstance |
| `test_phi_voice_redirect.py` | 4 | ComplianceService+PhiChannelPolicy integration; ProactiveOutbound with real compliance |
| Regression guard (all inbox tests) | 84 | All pass — no breakage to existing 80 tests |

---

## Pending (outside T-1 scope)

- T-2: NudgeService + POST /nudge endpoint (depends on T-1)
- T-6: E2E SC-3 test (Playwright, live-verify PHI redirect against dev-app) — depends T-2 + FE lanes
