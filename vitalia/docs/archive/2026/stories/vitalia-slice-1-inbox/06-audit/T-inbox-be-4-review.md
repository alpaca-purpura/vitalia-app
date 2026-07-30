<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# T-inbox-be-4 — Whisper adapter + WA/IG/Email retract — Review

**Brand:** vitalia
**Story:** vitalia-slice-1-inbox
**Surface:** backend (connections)
**Verdict:** PASS

## Scope

NEW Whisper STT adapter + EXTEND WhatsApp/Instagram/Email adapters with `retract_message_id` method (email raises `ChannelRetractUnsupportedError`).

Paths reviewed:
- `connections/whisper/{__init__,adapter}.py`
- `connections/whatsapp/adapter.py` (retract_message_id)
- `connections/instagram/adapter.py`
- `connections/email/adapter.py`

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Adapters in connections module; no domain logic leakage |
| 2 | Tenant Isolation | N/A | Adapters operate on external resources (audio URL, message wamid); tenant context flows via service caller |
| 3 | Soft Deletes | N/A | External API operations |
| 4 | Code Quality | PASS | ruff check/format clean |
| 5 | SQLAlchemy 2.0 | N/A | No DB operations |
| 6 | Async Consistency | PASS | `httpx.AsyncClient` everywhere; `async def` on all public methods |
| 7 | Pydantic v2 / DTOs | PASS | `TranscriptionResult`, `RetractResult` are `@dataclass` (acceptable for internal adapter contracts) |
| 8 | Migration Quality | N/A | No DB schema |
| 9 | Security | PASS | Bearer token via `Authorization` header; no key leakage in logs |
| 10 | Tests / TDD | PASS | Connection tests cited in 06-tickets.yaml exist (`test_whisper_adapter.py`, `test_whatsapp_retract.py`, `test_instagram_retract.py`, `test_email_retract_unsupported.py`) |
| 11 | Cross-cutting | PASS | HIPAA-lite: NO `audio_url` or transcript text in logs (only confidence + status metadata); explicit comments document the choice |
| 12 | Mirror detection | PASS | Brand-local adapters; no engine mirror |

## Findings

### PASS observations

1. **Whisper graceful degradation** (whisper/adapter.py):
   - Timeout 30s per `_TIMEOUT_SECONDS`.
   - Three `except` branches (TimeoutException, HTTPStatusError, generic Exception) — all return `TranscriptionResult(text=None, confidence=0.0)` (no raise).
   - PHI: `audio_url` never logged in error branches. Only `timeout_seconds`, `status_code` (no body).
   - `_logprob_to_confidence` clamps log_prob → [0.0, 1.0] linear scale (defensive bounds).

2. **WhatsApp retract** (whatsapp/adapter.py):
   - Timeout 5s per `_RETRACT_TIMEOUT_SECONDS`.
   - 404 treated as idempotent success (`already_deleted` path returns `succeeded=True`).
   - Logs `message_id` (not PHI — it's `wamid.*` external identifier, not patient data).
   - All exception branches return `RetractResult(succeeded=False)` (no raise).

3. **Email retract** (email/adapter.py):
   - Always raises `ChannelRetractUnsupportedError` (caught by RetractMessageService → fallback "marcar como erróneo").
   - Documents the rationale in the docstring.

4. **Instagram retract** — analogous to WhatsApp.

## Contract Compliance

- [x] Whisper adapter wraps OpenAI Whisper API with timeout 30s, graceful degradation
- [x] WhatsApp + Instagram adapters have `retract_message_id(message_id)` method
- [x] Email adapter raises `ChannelRetractUnsupportedError` (caught by RetractMessageService)
- [x] HIPAA-lite: NO raw transcript or `audio_url` in logs

## Gherkin coverage

| Scenario | Tests | Status |
|---|---|---|
| SC-02 negative (Whisper failure) | `test_whisper_adapter.py::test_timeout_returns_none`, `test_low_confidence_returned` | ✅ Tests exist |
| SC-01 happy (retract via WA Cloud) | `test_whatsapp_retract.py::test_retract_within_5min_succeeds` | ✅ Test exists |
| SC-03 edge (channel unsupported → fallback) | `test_email_retract_unsupported.py` | ✅ Test exists |

## Verdict

**PASS** — connections layer clean. Graceful degradation respected per `tessl__graceful-degradation` rule. Timeout + fallback + no PHI leakage in logs. Idempotent 404 handling.
