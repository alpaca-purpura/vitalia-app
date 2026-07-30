# T-inbox-be-4 Result — Backend connections: Whisper STT + WA/IG/Email retract

**Ticket:** T-inbox-be-4
**Story:** vitalia-slice-1-inbox
**State:** tests-passing
**Commit:** pending (see below)
**Date:** 2026-05-20

## Summary

Implemented 4 connection adapters for the vitalia inbox module:
1. **WhisperAdapter** — OpenAI Whisper STT via httpx, timeout 30s, HIPAA-lite (no PHI in logs), confidence from avg_logprob.
2. **WhatsAppAdapter.retract_message_id** — Meta Graph API DELETE, timeout 5s, idempotent (404=success), Bearer auth.
3. **InstagramAdapter.retract_message_id** — Instagram Graph API DELETE, timeout 5s, idempotent (404=success), Bearer auth.
4. **EmailAdapter.retract_message_id** — Raises `ChannelRetractUnsupportedError` (no retract API); caught by RetractMessageService to apply "marcar como erróneo" fallback.

All adapters implement graceful degradation: external call failures return safe fallback values or raise typed exceptions — never unhandled propagation.

## Test Results

- **38 tests PASS** (`vitalia/backend/tests/modules/vitalia/connections/`)
- **265 architecture fitness tests PASS** (`vitalia/backend/tests/architecture/`)
- **Lint:** ruff check 0 errors, ruff format clean

### Gherkin coverage (per 06-tickets.yaml)

| Scenario | Test path | Status |
|---|---|---|
| SC-02 Whisper timeout → fallback | `test_whisper_adapter.py::TestWhisperAdapterTimeout::test_timeout_returns_none` | PASS |
| SC-02 Whisper low confidence returned | `test_whisper_adapter.py::TestWhisperAdapterLowConfidence::test_low_confidence_returned` | PASS |
| SC-01 WA retract success | `test_whatsapp_retract.py::TestWhatsAppRetractSuccess::test_retract_within_5min_succeeds` | PASS |
| SC-03 Email retract unsupported | `test_email_retract_unsupported.py::TestEmailRetractUnsupported::test_retract_raises_unsupported_error` | PASS |

## Files delivered

### New source files (GREEN implementation)
- `vitalia/backend/src/modules/vitalia/connections/whisper/__init__.py`
- `vitalia/backend/src/modules/vitalia/connections/whisper/adapter.py`
- `vitalia/backend/src/modules/vitalia/connections/whatsapp/__init__.py` (T-8 extended to include registry; adapter coexists cleanly)
- `vitalia/backend/src/modules/vitalia/connections/whatsapp/adapter.py`
- `vitalia/backend/src/modules/vitalia/connections/instagram/__init__.py`
- `vitalia/backend/src/modules/vitalia/connections/instagram/adapter.py`
- `vitalia/backend/src/modules/vitalia/connections/email/__init__.py`
- `vitalia/backend/src/modules/vitalia/connections/email/adapter.py`

### New test files (RED written first per TDD)
- `vitalia/backend/tests/modules/vitalia/connections/test_whisper_adapter.py` (10 tests)
- `vitalia/backend/tests/modules/vitalia/connections/test_whatsapp_retract.py` (9 tests)
- `vitalia/backend/tests/modules/vitalia/connections/test_instagram_retract.py` (8 tests)
- `vitalia/backend/tests/modules/vitalia/connections/test_email_retract_unsupported.py` (9 tests)

## Skills Consulted (must_load enforcement v4.1)

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Runtime quality checklist: anti-patterns FastAPI/SQLA/tests/migrations | Confirmed: no SA legacy, structlog only, no `print()`, graceful degradation pattern verified |
| `.claude/rules/backend-ddd.md` | Connections adapters live in infrastructure layer | Adapters are infrastructure (no domain framework imports, no FastAPI routes) — correct layer |
| `.claude/rules/tenant-isolation.md` | Channel adapters don't persist data (no DB queries) | N/A for these adapters — they are stateless HTTP wrappers; RetractMessageService (T-inbox-be-3) owns persistence |
| `.claude/rules/hipaa-lite.md` (vitalia overlay) | Whisper transcribes patient voice messages (PHI risk) | MUST NOT log raw transcript. Test `test_phi_not_logged_raw` enforces. Only confidence + status logged. |
| `.claude/rules/anti-duplication.md` | Could mirror from luana-core-channels | Confirmed: `luana-core-connections` engine exists but does NOT expose Whisper or Meta Graph retract adapters. Brand-local implementation is correct per extension pattern. |
| `.claude/rules/tdd-mandatory.md` | TDD flow enforced | RED tests created FIRST (4 test files) → GREEN implementations → verified 38/38 PASS |
| `.claude/rules/spanish-text.md` | User-facing fallback messages in WhisperAdapter | Fallback message "No se pudo procesar el audio. Por favor escríbelo o inténtalo de nuevo." uses tuteo (NO voseo). |
| `tessl__graceful-degradation` | External HTTP calls (Whisper 30s, WA/IG retract 5s) | timeout + catch TimeoutException + catch HTTPStatusError + catch Exception → return safe fallback, no raise |

## Design decisions

1. **Whisper confidence from avg_logprob**: Linear interpolation `(clamped - (-2.0)) / (0.0 - (-2.0))`. Range [-2, 0] → [0.0, 1.0]. avg_logprob=-2.5 → clamped to -2.0 → confidence=0.0 (< 0.5). avg_logprob=-0.1 → confidence=0.95 (≥ 0.5). Verified by test assertions.

2. **Idempotent retract (404 = success)**: If Meta returns 404 (message already deleted), `RetractResult(succeeded=True)`. This is standard idempotency: the caller's goal (message not visible) is already achieved.

3. **Email ChannelRetractUnsupportedError**: Raised unconditionally. Service layer (T-inbox-be-3) is responsible for catch + fallback logic. Adapter stays thin and typed.

4. **HIPAA-lite log safety**: `whisper/adapter.py` logs only `confidence` (float) + `status` strings. No `audio_url` (could be patient-identifying), no `text` (medical PHI). Enforced by `test_phi_not_logged_raw`.

5. **parallel-safety note**: T-8 (background agent) had already created `whatsapp/registry.py` and updated `whatsapp/__init__.py` to include template registry exports. This PR's `WhatsAppAdapter.retract_message_id` coexists in `whatsapp/adapter.py` without conflict (disjoint scope).

## Validators status

| Validator | Result |
|---|---|
| `be_lint_ruff_check` | PASS (0 errors, 0 format issues) |
| `be_arch_fitness_brand` | PASS (265/265) |
| `be_test_inbox` | PASS (38/38 connections tests) |
