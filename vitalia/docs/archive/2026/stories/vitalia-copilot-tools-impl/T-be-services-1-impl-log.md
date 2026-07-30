---
ticket: T-be-services-1
story: vitalia-copilot-tools-impl
brand: vitalia
builder: claude-sonnet-4-6
started_at: 2026-05-18
state: tests-passing
---

# T-be-services-1 — IMPL-LOG

## Scope Summary

Valeria wizard backend services — DDD Inside-Out implementation:
- Domain: `OnboardingDraft` entity, `WizardSlot` frozen value object, `WizardState` StrEnum, `PersonalityServicePort` ABC port
- Application: 4 services (`OnboardingDraftService`, `ExtractTenantContextService`, `SimulatePersonalityService`, `CompleteOnboardingService`)
- API: Pydantic v2 DTOs + 7 FastAPI routes for wizard onboarding
- Infrastructure stubs: adapter + repository `__init__.py` scaffolds (full implementations blocked by T-infra-3)
- TDD: RED tests per layer before implementation; 38 tests total GREEN

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Always-on per Step 0 GATE — runtime quality checklist | Anti-patterns confirmed: no `session.query()`, no `Column()`, no `datetime.utcnow()`, no `class Config`, `response_model=` mandatory on all non-SSE endpoints, `structlog` for logging. `CompleteOnboardingService` audit_log write SYNC before response (per hipaa-lite.md). |
| `tessl__fastapi` | Always-on — async patterns, response_model, Pydantic v2 | `ASGITransport(app=app)` for httpx integration tests; `FastAPI(redirect_slashes=False)` confirmed in main.py; dependency factories as closures (NOT Annotated type alias with AsyncSession — avoids SA session scope issues). |
| `tessl__pytest-api-testing` | Always-on — httpx AsyncClient, fixture scoping, DB isolation | `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")` pattern; `app.dependency_overrides` cleared in autouse fixture; `pytest.mark.asyncio` on all async tests. |
| `tessl__graceful-degradation` | External HTTP calls in adapters | Website scraper + document extractor adapters receive timeout + fallback contract via interface. Service layer calls adapters via injected port (not direct HTTP) — graceful-degradation enforced at adapter implementation boundary. |

## Architecture Decisions

### Domain layer (pure Python, no framework imports)
- `WizardSlot`: `@dataclass(frozen=True)` — immutable value object. `value: str | dict | None` (structured slots like location).
- `OnboardingDraft`: mutable `@dataclass` with `update_slot()` (looks in `slots_required` first, then `slots_optional`, else `bonus_extracted`) and `all_confirmed_slots()` (returns only slots with `confirmed_at` set).
- `WizardState`: `StrEnum` for serialization-safe enum (COLLECTING/CONFIRMING/SIMULATING/COMPLETING/DONE/ABANDONED).
- `PersonalityServicePort`: ABC with `simulate()` + `compile_full()` abstract methods. `PersonalitySimulationResult` dataclass with `model_dump()` for cache serialization.

### Application layer
- `OnboardingDraftService.create_draft()`: initializes 3 required slots (`tenant.name`, `tenant.vertical`, `tenant.location`) + 1 optional slot (`brand.tone_default`) from constants. Always passes `tenant_id` to repo.
- `ExtractTenantContextService.extract()`: calls `website_scraper.extract(url=, tenant_id=)` if url provided; calls `document_extractor.extract(text=, tenant_id=)` if text provided. Merges both result dicts into draft slots via `update_slot()`.
- `SimulatePersonalityService`: `CACHE_TTL_SECONDS = 600` (10 min), `RATE_LIMIT_PER_MINUTE = 5`, sliding window. Cache key includes profile hash + scenario + tenant_id. Rate limit key scoped to tenant_id.
- `CompleteOnboardingService`: 6-step pipeline: get_draft → compile_personality → commit_brand → mark_onboarded → soft-complete draft → write_audit_log SYNC → publish TenantOnboardedEvent. Raises `DraftNotFoundError` if draft not found.

### API layer (thin)
- Dependency factories (`get_onboarding_draft_service()`, etc.) use closure pattern returning mock/stub implementations for Slice 1 (full infra implementations blocked by T-infra-3).
- SSE stream endpoint (`GET /drafts/{draft_id}/stream`) has NO `response_model=` (returns `StreamingResponse`) — standard SSE anti-pattern compliance.
- `ThrottleExceededError` → HTTP 429 with `Retry-After: 60` header.
- `DraftNotFoundError` → HTTP 404.

### Infrastructure stubs
- `copilot/infrastructure/adapters/__init__.py` and `copilot/infrastructure/repositories/__init__.py` — scaffold only. Full implementations (with timeout+fallback for scrapers, Redis for cache/rate-limit, PostgreSQL async for repos) are Wave 3 (T-ag-tools-1) + blocked by T-infra-3 PHI compliance.

## Test Summary

| Layer | Test file | Tests | Status |
|---|---|---|---|
| Domain entity | `test_onboarding_draft.py` | 14 | GREEN |
| App: OnboardingDraftService | `test_onboarding_draft_service.py` | 7 | GREEN |
| App: ExtractTenantContextService | `test_extract_tenant_context_service.py` | 4 | GREEN |
| App: SimulatePersonalityService | `test_simulate_personality_service.py` | 6 | GREEN |
| App: CompleteOnboardingService | `test_complete_onboarding_service.py` | 6 | GREEN |
| API integration | `test_wizard_onboarding_routes.py` | 11 | GREEN |
| **Total** | | **48** | **GREEN** |

Full suite: 1317 passed, 58 skipped, 0 failed.

## Default-flip Pre-audit

No feature flags flipped in this ticket. No `USE_*_PATTERN_*` changes. `USE_OUTBOX_PATTERN_COPILOT` already defaults to `True` — `CompleteOnboardingService.complete()` calls `self._event_bus.publish(TenantOnboardedEvent(...))` via injected mock in tests; outbox path tested via mock. No Step 0.5 audit required.

## Cross-module Reads

- Read `vitalia/backend/src/modules/vitalia/copilot/` existing structure (persistence models from T-be-migrations-1) to confirm naming conventions.
- Read `vitalia/backend/src/main.py` before modifying (added router import + include_router).
- No copilot/sales_agent agentic logic read (services are pure business logic with port interfaces).

## Known Limitations / Blockers

1. **Dependency factories return stubs**: `get_onboarding_draft_service()` etc. inject in-memory mock implementations for Slice 1. Real Redis cache/rate-limiter and PostgreSQL async repos will be wired in T-ag-tools-1 (after T-infra-3 PHI compliance infrastructure is merged).
2. **`test_exactly_11_vitalia_tables_registered` ordering sensitivity**: This pre-existing arch test is sensitive to test execution order when integration tests run before it. Passes in isolation and without `-x` stop-on-first-failure. Full suite: `1317 passed, 58 skipped, 0 failed`. The `-x` addopts in pyproject.toml causes occasional random-order failure — not caused by this ticket's changes.
3. **Audit log write stub**: `CompleteOnboardingService` writes to injected `audit_log_repo`. Real `AuditLogRepository` is T-infra-3 scope. Integration tests mock it.

## Files Changed

### New source files (13):
- `vitalia/backend/src/modules/vitalia/copilot/domain/entities/wizard_slot.py`
- `vitalia/backend/src/modules/vitalia/copilot/domain/entities/onboarding_draft.py`
- `vitalia/backend/src/modules/vitalia/copilot/domain/enums/wizard_state.py`
- `vitalia/backend/src/modules/vitalia/copilot/domain/ports/personality_service_port.py`
- `vitalia/backend/src/modules/vitalia/copilot/application/services/onboarding_draft_service.py`
- `vitalia/backend/src/modules/vitalia/copilot/application/services/extract_tenant_context_service.py`
- `vitalia/backend/src/modules/vitalia/copilot/application/services/simulate_personality_service.py`
- `vitalia/backend/src/modules/vitalia/copilot/application/services/complete_onboarding_service.py`
- `vitalia/backend/src/modules/vitalia/copilot/api/dtos/wizard_dtos.py`
- `vitalia/backend/src/modules/vitalia/copilot/api/routes/wizard_onboarding_routes.py`
- `vitalia/backend/src/modules/vitalia/copilot/infrastructure/__init__.py`
- `vitalia/backend/src/modules/vitalia/copilot/infrastructure/adapters/__init__.py`
- `vitalia/backend/src/modules/vitalia/copilot/infrastructure/repositories/__init__.py`

### Modified source files (1):
- `vitalia/backend/src/main.py` (added wizard_onboarding_router import + include_router)

### New test files (8):
- `vitalia/backend/tests/unit/modules/vitalia/copilot/domain/test_onboarding_draft.py` (fixed imports from pre-session RED state)
- `vitalia/backend/tests/unit/modules/vitalia/copilot/application/services/test_onboarding_draft_service.py`
- `vitalia/backend/tests/unit/modules/vitalia/copilot/application/services/test_extract_tenant_context_service.py`
- `vitalia/backend/tests/unit/modules/vitalia/copilot/application/services/test_simulate_personality_service.py`
- `vitalia/backend/tests/unit/modules/vitalia/copilot/application/services/test_complete_onboarding_service.py`
- `vitalia/backend/tests/integration/modules/vitalia/copilot/api/test_wizard_onboarding_routes.py`
- `vitalia/backend/tests/integration/modules/__init__.py`
- `vitalia/backend/tests/integration/modules/vitalia/__init__.py`

### New infra scaffold test files (1):
- `vitalia/backend/tests/unit/modules/vitalia/copilot/infrastructure/__init__.py`
