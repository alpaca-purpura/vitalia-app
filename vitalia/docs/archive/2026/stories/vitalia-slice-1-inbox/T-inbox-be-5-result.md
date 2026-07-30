# T-inbox-be-5 — Result

**Story:** vitalia-slice-1-inbox
**Ticket:** T-inbox-be-5 (Inbox API layer — 8 endpoints + CRM lead endpoints + router mount)
**State:** DONE — all validators GREEN
**Completed:** 2026-05-20
**Builder:** claude-sonnet-4-6 (finalization run — commit + push pending from prior builder session)

---

## Summary

Implemented the thin FastAPI API layer for the vitalia inbox module:

- **8 inbox endpoints** in `vitalia/backend/src/modules/vitalia/inbox/api/router.py`:
  - `POST /inbox/conversations/{conv_id}/messages` — send AI/human message (PHI gated)
  - `POST /inbox/conversations/{conv_id}/messages/{msg_id}/revert` — retract within 5min (PHI gated)
  - `PATCH /inbox/conversations/{conv_id}/mode` — set handler mode with OCC (PHI gated)
  - `POST /inbox/conversations/{conv_id}/pause` — pause Adrián 60min (PHI gated)
  - `GET /inbox/conversations/{conv_id}/tools` — tool state read-only (PHI gated)
  - `GET /inbox/conversations/{conv_id}/activity-stream` — activity log (PHI gated)
  - `POST /inbox/proactive-outbound` — HSM template send (PHI gated)
  - `POST /inbox/transcribe` — audio transcription (PHI gated)

- **4 CRM lead endpoints** extended in `vitalia/backend/src/modules/vitalia/crm/api/router.py`:
  - `GET /crm/leads` — list leads with pagination + filters
  - `GET /crm/leads/{lead_id}` — lead detail
  - `GET /crm/conversations/{conv_id}` — conversation detail
  - `GET /crm/conversations` — conversations list

- **Router mount** in `vitalia/backend/src/main.py`:
  - `app.include_router(inbox_router, prefix="/api/v1/vitalia/inbox")`

- **Supporting files:**
  - `vitalia/backend/src/modules/vitalia/crm/application/dto/lead_dto.py` — LeadSummaryDTO, ConversationSummaryDTO
  - `vitalia/backend/src/modules/vitalia/crm/application/services/lead_service.py` — LeadService (list_leads, get_lead, list_conversations, get_conversation)
  - `vitalia/backend/tests/modules/vitalia/inbox/api/` — 9 test files (36 tests)

---

## Validators Table

| Validator | Command | Result |
|---|---|---|
| ruff check | `ruff check src/modules/vitalia/inbox/ src/modules/vitalia/crm/... tests/...` | GREEN — 0 errors |
| ruff format | `ruff format --check src/modules/vitalia/inbox/ ...` | GREEN — 36 files formatted |
| arch fitness | `pytest tests/architecture/ -v` | GREEN — 268/268 passed |
| inbox API tests | `pytest tests/modules/vitalia/inbox/api/ -v` | GREEN — 36/36 passed |

---

## Key Design Decisions

1. **response_model= mandatory** on all 8 inbox endpoints (PII gate + arch fitness V-AE-2)
2. **PHI dual-filter**: every service call carries `tenant_id` + `clinic_id` (HIPAA-lite overlay)
3. **RBAC** via `PHIAccessDeniedError` mapped to 403 in all PHI endpoints
4. **OCC** (Optimistic Concurrency Control) on PATCH /mode via `If-Match` header + `ETag` response
5. **Clerk JWT decode** + clinic resolver in every handler; errors mapped to 401/403/404
6. **DDD thin layer**: routers delegate to application services, zero business logic in `api/`
7. **No cross-module imports** from inbox: CRM lead endpoints live in `crm/api/router.py`

---

## Skills Consulted

| Skill | Invocation reason | Decision cited |
|---|---|---|
| `backend-expert` | Runtime quality checklist — FastAPI Annotated deps, response_model, SQLA patterns | Used `Annotated` deps, `response_model=` on all endpoints, SQLA 2.0 `select()` pattern in lead_service |
| `brand-expert` | NOT invoked — no brand module touched | N/A |
| `offer-expert` | NOT invoked — no offer module touched | N/A |
| `metrics-expert` | NOT invoked — no analytics module touched | N/A |

---

## Files in Scope

**New files:**
- `vitalia/backend/src/modules/vitalia/inbox/api/router.py`
- `vitalia/backend/src/modules/vitalia/inbox/api/__init__.py`
- `vitalia/backend/src/modules/vitalia/crm/application/dto/lead_dto.py` (new DTOs)
- `vitalia/backend/src/modules/vitalia/crm/application/services/lead_service.py`
- `vitalia/backend/tests/modules/vitalia/inbox/api/test_router_send_message.py`
- `vitalia/backend/tests/modules/vitalia/inbox/api/test_router_revert.py`
- `vitalia/backend/tests/modules/vitalia/inbox/api/test_router_mode.py`
- `vitalia/backend/tests/modules/vitalia/inbox/api/test_router_pause_adrian.py`
- `vitalia/backend/tests/modules/vitalia/inbox/api/test_router_tools.py`
- `vitalia/backend/tests/modules/vitalia/inbox/api/test_router_activity_stream.py`
- `vitalia/backend/tests/modules/vitalia/inbox/api/test_router_proactive_outbound.py`
- `vitalia/backend/tests/modules/vitalia/inbox/api/test_router_transcribe_audio.py`
- `vitalia/backend/tests/modules/vitalia/inbox/api/test_cross_tenant_denied.py`
- `vitalia/backend/tests/architecture/test_no_hardcoded_strings_inbox.py`
- `vitalia/backend/tests/modules/vitalia/test_extensions_inbox_registration.py`
- `vitalia/backend/tests/modules/vitalia/crm/api/test_router_leads_list.py`
- `vitalia/backend/tests/modules/vitalia/crm/api/test_router_conversations_list.py`
- `vitalia/backend/tests/modules/vitalia/crm/api/test_router_conversation_detail.py`
- `vitalia/backend/tests/integration/test_cross_story_contracts.py`
- `vitalia/backend/src/modules/vitalia/fidelizacion/api/` (fidelizacion — adjacent, not T-inbox-be-5 scope)

**Modified files (T-inbox-be-5 scope):**
- `vitalia/backend/src/main.py` — inbox router mount added
- `vitalia/backend/src/modules/vitalia/crm/api/router.py` — lead + conversation endpoints extended
- `vitalia/backend/src/modules/vitalia/extensions.py` — inbox extension registered
