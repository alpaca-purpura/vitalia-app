# T-onboarding-2 — Result

## Ticket
`vitalia-slice-1-onboarding-wizard` · T-onboarding-2 · Adapters wire-up + LivePreviewService

## State
`developing → developed` (this ticket)

## Commit
Pending push — see git commit SHA below after push.

## Validators GREEN

| Validator | Command | Result |
|---|---|---|
| `be_lint_ruff_check` | `.venv/bin/ruff check src/...live_preview_service.py tests/...application/ --no-cache` | 0 errors |
| `be_format_ruff` | `.venv/bin/ruff format --check` | 4 files already formatted |
| `be_arch_fitness_brand` | `.venv/bin/pytest vitalia/backend/tests/architecture/ -x -q` | 245/245 PASS |
| `be_test_onboarding` | `.venv/bin/pytest vitalia/backend/tests/modules/vitalia/copilot/ -v` | 35 passed, 1 skipped |

## Files produced

### New files
- `vitalia/backend/src/modules/vitalia/copilot/application/services/live_preview_service.py`
- `vitalia/backend/tests/modules/vitalia/copilot/application/__init__.py`
- `vitalia/backend/tests/modules/vitalia/copilot/application/services/__init__.py`
- `vitalia/backend/tests/modules/vitalia/copilot/application/services/test_live_preview_service.py`

### Story artifacts
- `vitalia/docs/product/stories/vitalia-slice-1-onboarding-wizard/T-onboarding-2-impl-log.md`
- `vitalia/docs/product/stories/vitalia-slice-1-onboarding-wizard/T-onboarding-2-result.md` (this file)

## Test coverage
9 tests (8 passed, 1 skipped):
- `TestLivePreviewServiceWhatsApp`: happy path, cached flag, missing draft ValueError
- `TestLivePreviewServiceLanding`: brand payload HTML, empty payload HTML, missing draft ValueError
- `TestExtractTenantContextIntegration`: URL-only flow, text_content-only flow, audio skip marker

## Key decisions

1. **LivePreviewService as thin wrapper**: Delegates to SimulatePersonalityService without adding a second cache layer. Service owns throttle + cache per its design.

2. **Audio path deferred**: `extract_tenant_context_service.py` was already OQ-3 compliant (no `audio_uploads` parameter). Marked via `@pytest.mark.skip` in integration test to document the deferred path explicitly.

3. **Providers directory**: `infrastructure/providers/` directory not created — adapters (`website_scraper`, `document_extractor`) are duck-typed and injected at DI layer (T-3 scope). T-2 verifies the adapter dispatch contract via mock-based integration tests.

4. **HTML renderer**: Minimal BE-only template for Slice 1. XSS-safe via `html.escape()`. Renders known brand identity fields. No React dependency.

## Notes for next tickets

- T-onboarding-3: Replace any remaining `AsyncMock()` DI in wizard routes with real `Depends(get_live_preview_service)` factory. Wire `LivePreviewService` into the simulate endpoint.
- T-onboarding-4/5: Tools + graph smoke — `production_code=false`, Sonnet-eligible per OQ-1 ratification.
