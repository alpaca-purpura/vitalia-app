# T-onboarding-3 — Implementation Log

## Ticket

**T-onboarding-3**: Wizard routes DI audit + response_model verification + 9 integration tests

**Depends on**: T-onboarding-1 (DONE commit `135ffe0`), T-onboarding-2 (DONE commit `7039d69`)

**Branch**: `wip/vitalia`

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` (runtime-quality-checklist.md) | ALWAYS per role requirements — anti-patterns FastAPI/SQLA/tests | Used `dependency_overrides` lambda-closure pattern (zero-param factories). Confirmed `Annotated[T, Depends(f)]` inline (not type alias). Cross-tenant: returns 404 not 403. `response_model=` mandatory on all non-SSE routes. |
| `tessl__fastapi` | Async DI patterns, response_model enforcement, lifespan | Confirmed all 6 non-SSE routes already had `response_model=`. Header alias `X-Tenant-ID` via `Annotated[str, Header(alias="X-Tenant-ID")]` pattern confirmed correct. |
| `tessl__pytest-api-testing` | `httpx.AsyncClient` + `ASGITransport`, fixture scoping, factory stubs | Used yield fixture for `app_with_stubs` with proper teardown (`pop` overrides). `async with AsyncClient(...)` per-test isolation. |

---

## Scope discovery

### Pre-existing state (from T-1 and T-2)

T-1 already wired real SQLA 2.0 repos for:
- `get_onboarding_progress_repo` — real `SqlAlchemyOnboardingProgressRepository`
- `get_brand_studio_draft_repo` — real `SqlAlchemyBrandStudioDraftRepository`
- `get_onboarding_draft_service` — real `OnboardingDraftService`

T-2 added:
- `get_extract_service` — real `draft_repo` + stub `website_scraper`/`document_extractor` (Slice 1 acceptable)
- `get_simulate_service` — stub adapters (personality, cache, rate_limiter — Slice 1 acceptable; no DB needed)
- `get_complete_service` — real `draft_repo` + stub ports (personality_adapter, brand_studio_port, tenant_port, event_bus — Slice 1 acceptable)

T-3 scope was: **write 9 integration tests** exercising all 7 endpoints + cross-tenant 404 + missing-header 422. No changes needed to routes code itself (already compliant).

### `response_model=` audit (arch fitness V-AE-2)

Verified all 6 non-SSE routes in `wizard_onboarding_routes.py`:

| Route | response_model | Status |
|---|---|---|
| `POST /drafts` | `StartDraftResponse` | ✅ |
| `GET /drafts/{draft_id}` | `DraftResponse` | ✅ |
| `POST /drafts/{draft_id}/extract` | `ExtractResponse` | ✅ |
| `POST /drafts/{draft_id}/slots/{slot_id}/confirm` | `ConfirmSlotResponse` | ✅ |
| `POST /drafts/{draft_id}/simulate` | `SimulateResponse` | ✅ |
| `POST /drafts/{draft_id}/complete` | `CompleteResponse` | ✅ |
| `GET /drafts/{draft_id}/stream` | (SSE — no response_model, correct) | ✅ |

### `X-Tenant-ID` header audit

All route handlers use `x_tenant_id: TenantIdHeader` where `TenantIdHeader = Annotated[str, Header(alias="X-Tenant-ID")]`. All confirmed present.

---

## Implementation decisions

### Test stub design

Per `runtime-quality-checklist.md` § "Test fixture override — bare params son Pydantic field":

- Each stub factory (`_make_stub_draft_service`, `_make_stub_extract_service`, etc.) returns a `MagicMock(spec=ServiceClass)` with async methods replaced
- `app.dependency_overrides[factory_fn] = lambda: stub_instance` — zero-param lambda closures, NOT bare function refs
- Single `app_with_stubs` yield fixture wires all 4 DI factories; teardown uses `.pop()` to restore defaults
- `client_a` fixture uses `headers={"X-Tenant-ID": str(TENANT_A)}` per ASGI transport

### `test_get_draft_not_found` — bug found and fixed

Initial stub `get_draft_dispatch` only checked `tenant_id` match, not `draft_id`. So `GET /drafts/{unknown_id}` with valid tenant header returned 200 (draft found).

Fix: added `draft_id == draft.id` check:
```python
async def get_draft_dispatch(*, draft_id: UUID, tenant_id: UUID) -> ...:
    if draft_id == draft.id and tenant_id == draft.tenant_id:
        return draft
    return None
```

### `test_cross_tenant_returns_404`

Tests that TENANT_B (different header) requesting draft owned by TENANT_A gets 404. Dispatched by `tenant_id` mismatch in stub → service returns `None` → route raises `HTTPException(404)`. Confirmed correct per `tenant-isolation.md`.

---

## Files modified

| File | Change |
|---|---|
| `vitalia/backend/tests/modules/vitalia/copilot/api/__init__.py` | Created (empty — test package marker) |
| `vitalia/backend/tests/modules/vitalia/copilot/api/routes/__init__.py` | Created (empty — test package marker) |
| `vitalia/backend/tests/modules/vitalia/copilot/api/routes/test_wizard_onboarding_routes.py` | Created (9 tests, 4 stub factories, 3 fixtures) |

**No changes to production routes code** — `wizard_onboarding_routes.py` was already compliant.

---

## Test results

```
vitalia/backend/tests/modules/vitalia/copilot/ — 44 passed, 1 skipped
vitalia/backend/tests/architecture/            — 245 passed, 2 warnings
```

Baseline (pre-T-3): 35 passed, 1 skipped. Delta: +9 tests (9 new route tests).

---

## Default-flip pre-audit

No feature flag defaults touched. Step 0.5 N/A.

---

## Cross-module reads

None required. All imports from `vitalia/backend/src/` scope only.

---

## HIPAA-lite compliance

Wizard onboarding tables store brand config only (tenant name, vertical, location, tone preference). No PHI fields in scope. Dual filter (`tenant_id + clinic_id`) not required for wizard tables — single `tenant_id` filter sufficient per `hipaa-lite.md` (PHI dual filter applies to `patient_*`, `medical_*`, `treatment_*`, `appointment_*` tables).
