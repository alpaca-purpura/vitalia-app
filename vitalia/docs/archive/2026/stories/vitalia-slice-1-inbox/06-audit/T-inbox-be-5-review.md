<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# T-inbox-be-5 — 8 inbox API endpoints + 4 CRM endpoints — Review

**Brand:** vitalia
**Story:** vitalia-slice-1-inbox
**Surface:** backend (api layer)
**Verdict:** CHANGES_REQUESTED

## Scope

8 inbox endpoints + 4 CRM endpoints (list leads, get lead extended, list conversations, get conversation detail). PHI dual-filter, RBAC, OCC.

Paths reviewed:
- `inbox/api/router.py` (8 endpoints)
- `crm/api/router.py` (8 endpoints total in router; inbox-relevant: leads list, lead detail, conversations list, conversation detail)
- `crm/application/dto/lead_dto.py` (extensions)
- `crm/application/services/lead_service.py` (extensions)

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | API layer thin: header parse → resolver → RBAC → service call → response shape |
| 2 | Tenant Isolation | PASS | All endpoints take `X-Tenant-ID` + `X-Clinic-ID` headers; tenant_id resolved from JWT context |
| 3 | Soft Deletes | N/A | API layer |
| 4 | Code Quality | PASS | ruff check/format clean |
| 5 | SQLAlchemy 2.0 | N/A | API layer |
| 6 | Async Consistency | PASS | All route handlers `async def` |
| 7 | Pydantic v2 / DTOs | PASS | All endpoints declare `response_model=` (8/8 verified) |
| 8 | Migration Quality | N/A | API layer |
| 9 | Security | WARN | PHI access via `_PHI_ROLES = {doctor, nurse, admin_clinic}`. Status codes: 401 token, 403 RBAC, 404 not found, 409 OCC + patient-replied, 410 Gone (expired), 422 template not found, 429 rate limit. PII in response_model = doctor-only — acceptable |
| 10 | Tests / TDD | WARN | Router unit tests with `monkeypatch.setattr` for resolver + service factories pass (4 tests each). Cross-tenant denied verified (3 tests). Real DI not exercised. |
| 11 | Cross-cutting | PASS | Spanish neutro tuteo in all `HTTPException.detail` strings (verified: no voseo) |
| 12 | Mirror detection | PASS | Brand-local; no cross-brand basename hits |

## Findings

### FAIL: Service factory functions return AsyncMock instances in production code
**Category:** 1 (DDD) + 9 (Security)
**File:** `inbox/api/router.py:117-204` (8 factory functions)
**Issue:** Each `_get_*_service()` factory imports `unittest.mock.AsyncMock` and instantiates the service with `AsyncMock()` repos, audit_writer, event_bus, channel_adapters, session.

```python
def _get_send_service() -> SendMessageService:
    """Create SendMessageService with AsyncMock repos (Slice 1 — no live DI)."""
    from unittest.mock import AsyncMock
    return SendMessageService(
        msg_repo=AsyncMock(),
        conv_repo=AsyncMock(),
        receipt_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        channel_adapters={},
        session=None,
    )
```

This is a runtime decision: every production request will instantiate AsyncMocks. The endpoint will return whatever `AsyncMock()` returns by default for `.create()`, `.write()`, `.publish()` (typically another `AsyncMock`), which then fails the response-model serialization or returns nonsense data.

Comparison check shows this pattern pre-exists in `vitalia/crm/api/router.py`, `vitalia/crm/api/consent_endpoints.py`, `vitalia/copilot/api/routes/wizard_onboarding_routes.py` — but pre-existence is not a justification for adding more.

The Slice 1 design intent appears to be "stub the wiring, ship the contract" — but the contract is not just request/response shapes; it includes side effects (audit log row, outbox event). Any live test (E2E smoke) will return an HTTPException or a malformed body.

**Fix:**
- Wire real repos + audit writer + event bus + channel adapters via FastAPI `Depends(...)` and dependency-injected session. Use the existing pre-existing patterns from `iam` or `copilot` Service factories if real ones exist.
- If real wiring is truly out of scope for Slice 1, add a structlog warning on every request: `logger.warning("inbox.<endpoint>.using_mock_dependencies", note="Slice 1 stub")` so the deferred state is observable in prod.
- Document the gap as a follow-up ticket and link it in `T-inbox-be-5-result.md`.

### FAIL: handler_mode='human' override path missing for SendMessageRequest.handler_mode_override
**Category:** spec compliance
**File:** `inbox/api/router.py:301-311` (send_message endpoint)
**Issue:** Per spec § 6 + DTO definition `SendMessageRequest.handler_mode_override: Literal["ai", "human"] | None`, the endpoint should accept a `handler_mode_override` to support the "Yo escribo" UX path where an operator types directly bypassing AI dispatch. The router accepts the field in `SendMessageRequest` (line 31 of `send_message_dto.py`) but never forwards it to `service.send(...)`. The override is silently dropped.

`SendMessageService.send()` (line 159-171) also does not accept a `handler_mode_override` parameter — so the field is dead at every layer.

**Fix:**
- Add `handler_mode_override` parameter to `SendMessageService.send()`.
- Route handler passes `handler_mode_override=body.handler_mode_override`.
- Service: if `handler_mode_override` is set, override `conv.handler_mode` for the sender_type computation (`agent_human` for human override).
- Add test `test_send_human_override_bypasses_ai_dispatch`.

### WARN: PHI fields in response model
**Category:** 7 (Pydantic / PII)
**File:** `inbox/application/dto/send_message_dto.py::MessageResponse`
**Issue:** `MessageResponse` exposes `body_text`, `transcription_text`, `media_url` — all PHI per `vitalia/.claude/rules/hipaa-lite.md` § "PHI fields canónicos" (patient.* + lab_results + medical_notes etc.). Access is gated by `_PHI_ROLES` (doctor, nurse, admin_clinic) so it's not a leak — but per backend-expert PII rule, PHI in `response_model=` warrants justification.

**Status:** Justified — these are the values doctors need to see in the inbox. RBAC enforces gate. The mockup HTML (02-design-ui-mockup.html) shows MessageBubble rendering body_text. This is an architectural decision, not an oversight.

**Recommendation:** Add a code comment on `MessageResponse` explaining the RBAC gate justifies PHI exposure. Optional: ensure `media_url` is short-lived pre-signed URL with TTL ≤ 5 min (defense-in-depth) — confirm at infra ticket.

### INFO: `_get_resolver()` re-instantiates ClerkJwtDecoder per request
**Category:** 4 (Code Quality)
**File:** `inbox/api/router.py:112-114`
**Issue:** `_get_resolver()` constructs `ClerkJwtDecoder()` on every request. Decoder probably loads JWKS keys per construction → adds latency + potential request to Clerk infra per HTTP call.
**Fix:** Use FastAPI `Depends(...)` with module-level singleton or cache the JWKS in the decoder. Low priority — performance optimization for later, not Slice 1 blocker.

### INFO: PATCH /mode vs POST /mode inconsistency with arch spec
**Category:** spec compliance
**File:** `inbox/api/router.py:447` and `03-arch-be.md § 4.1`
**Issue:** Arch spec table § 4.1 lists `POST /api/v1/vitalia/inbox/conversations/{conv_id}/mode` for SetMode. Router implements `@router.patch("/conversations/{conv_id}/mode", ...)`. PATCH is more idiomatic REST for partial update; arch spec is slightly wrong.
**Action:** Either update arch spec to PATCH or update router to POST. Minor consistency note.

## Contract Compliance

- [x] 8 inbox endpoints registered with `response_model=`
- [x] Bearer + X-Tenant-ID + X-Clinic-ID header parsing
- [x] RBAC via `_assert_phi_access` for doctor/nurse/admin_clinic
- [x] Status codes per spec (401, 403, 404, 409, 410, 422, 429)
- [x] CRM router has list leads, lead detail, list conversations, conversation detail
- [ ] **Production DI wiring** — FAIL (factories return AsyncMock)
- [ ] **handler_mode_override forwarded to service** — FAIL (dropped)
- [x] PII gate: response_model on every endpoint

## Gherkin coverage

| Scenario | Tests | Status |
|---|---|---|
| SC-01 happy | `test_router_send_message.py::test_send_ai_message_201` | Test exists; passes against AsyncMock service |
| SC-02 negative | `test_router_transcribe_audio.py::test_low_confidence_fallback` | ✅ |
| SC-03 edge | `test_router_mode.py::test_occ_409`, `test_router_revert.py::test_410_gone_after_5min` | ✅ |
| SC-04 adversarial | `test_cross_tenant_denied.py` (3 tests) | ✅ |

## Architecture fitness

- `test_response_model_required.py`: PASS (8 inbox + 4 crm endpoints declare response_model)
- `test_audit_log_sync_write.py`: services call `await audit_writer.write(...)` pre-response — but real binding missing (see findings)

## Verdict

**CHANGES_REQUESTED** — primary issue is router service factories returning AsyncMock instances. While the pattern pre-exists in vitalia, adding 8 more endpoints with the same pattern fails the spec's "8 endpoints inbox-specific" delivered as wired production code.

**Required fixes:**
1. Wire real services in `_get_*_service()` factories (real repos via session DI, real audit_writer, real event_bus).
2. Forward `body.handler_mode_override` through `send_message` route → `SendMessageService.send()`.

**Non-blocking notes:**
- Document PHI-in-response-model justification (RBAC gated).
- Re-instantiation of `ClerkJwtDecoder()` per request (perf opt).
- PATCH vs POST naming for /mode endpoint (cosmetic).
