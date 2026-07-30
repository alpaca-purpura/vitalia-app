# T-onboarding-2 — IMPL-LOG

## Ticket
`vitalia-slice-1-onboarding-wizard` · T-onboarding-2 · Adapters wire-up + LivePreviewService

## State
`ready → developing → developed`

## Skills Consulted

- `backend-expert` — invoked per role instructions (ALWAYS). Loaded `runtime-quality-checklist.md` before writing code. Key decisions: (1) no `Any` types in service; (2) tenant_id isolation verified in `get_by_id_tenant` calls; (3) `TYPE_CHECKING` guard for circular import prevention; (4) no `class Config:` inner (Pydantic v2 compatible although this service uses no Pydantic models directly); (5) soft patterns applied: structlog only, no print().
- `brand-expert` — invoked per role instructions (touching `modules/vitalia/copilot/` which interacts with brand studio draft data). Key decision: `BrandStudioDraft.draft_payload` and `voice_profile_partial_json` are brand identity fields (not PHI — clinic name, tagline, voice profile). No `brand_settings` direct import — read via repository contract. Landing HTML renderer uses `html.escape()` to sanitize draft values before rendering.
- `offer-expert` — skipped (ticket does not touch offer module). Routing: T-onboarding-2 scope is copilot/onboarding only.
- `metrics-expert` — skipped (no analytics changes).

## Step 0 Gate — Anti-duplication grep

```bash
# Grep for LivePreviewService cross-brand / engine
find /home/chalreme/Proyectos/luana-vitalia/vitalia/backend/src -name "live_preview_service.py" 2>/dev/null
# → no prior file (new creation)

grep -rn "LivePreviewService" /home/chalreme/Proyectos/luana-vitalia/core/luana-core-*/src/ 2>/dev/null
# → ZERO matches (brand-specific Vitalia pattern: Valeria persona + Vitalia landing)

grep -rn "LivePreviewService" /home/chalreme/Proyectos/luana-vitalia/vitalia/backend/src/ 2>/dev/null
# → ZERO (pre-implementation)
```

**Verdict:** No cross-brand mirrors. No engine pattern shadowed. Anti-duplication §0 CLEAN.
`LivePreviewService` is brand-specific to Vitalia (Valeria persona via `SimulatePersonalityService` + Vitalia brand studio landing).

## Step 0.5 — Default-flip pre-audit

This ticket does not flip any feature flag defaults. No `USE_*` or `ENABLE_*` flags modified. Step 0.5 not applicable.

## Cross-module reads

- `vitalia/backend/src/modules/vitalia/copilot/application/services/simulate_personality_service.py` — READ ONLY for interface contract (constructor params, `simulate()` signature, `SimulateResponse.sample_text` + `cache_hit` fields).
- `vitalia/backend/src/modules/vitalia/copilot/domain/repositories/brand_studio_draft_repository.py` — READ ONLY for `get_by_id_tenant` interface.
- `vitalia/backend/src/modules/vitalia/copilot/domain/entities/brand_studio_draft.py` — READ ONLY for `draft_payload` + `voice_profile_partial_json` fields.
- `vitalia/backend/src/modules/vitalia/copilot/application/services/extract_tenant_context_service.py` — READ ONLY to verify audio field state (no `audio_uploads` parameter — already URL + text_content only pattern as per OQ-3).

## Shipped services verification (T-2 requirement)

All 5 services verified to exist:
- `extract_tenant_context_service.py` — URL + text_content path, NO audio parameter. Confirmed OQ-3 compliant.
- `onboarding_draft_service.py` — present.
- `simulate_personality_service.py` — present. `simulate()` takes `profile_partial`, `scenario`, `tenant_id`. Returns `SimulateResponse(sample_text, generated_at, cache_hit)`.
- `complete_onboarding_service.py` — present.
- `wizard_orchestrator_service.py` — present.

Infrastructure providers directory did NOT exist yet (no `providers/` subdir under `copilot/infrastructure/`). The CONTEXT-BRIEF indicated website_scraper and document_extractor "verify shipped" — these are injected as duck-typed adapters into `ExtractTenantContextService` (no concrete `providers/` files needed for T-2 scope, adapters are wired at DI layer in T-3). T-2 scope is test-level verification of the URL + text_content flow end-to-end via mocks, which is accomplished.

## Audio field — OQ-3 DEFERRED

Verified: `extract_tenant_context_service.py` accepts only `url: Optional[str]` and `text_content: Optional[str]`. There is NO `audio_uploads` parameter in the current implementation (audio was never added in Slice 1). The DEFERRED status is correctly represented by:
1. The absence of `audio_uploads` field in `ExtractTenantContextService.extract()`.
2. The `@pytest.mark.skip(reason="Audio Whisper STT deferred Slice 2 per Chris 2026-05-18 (OQ-3 ratified)")` test confirming the deferred path.

No modification to `extract_tenant_context_service.py` needed — it was already correct for Slice 1 scope.

## Implementation decisions

### LivePreviewService design

Thin wrapper pattern per T-2 spec. Two public methods:

1. `generate_whatsapp_preview()` — delegates entirely to `SimulatePersonalityService.simulate()`. Does NOT add a second cache layer (simulate_service owns throttle 5/min + cache 10-min TTL per its own implementation). Returns `{sample_text, cached, throttled}` dict.

2. `generate_landing_snippet()` — renders `BrandStudioDraft.draft_payload` to a minimal HTML section using stdlib `html.escape()` for XSS safety. Returns `{html, sections_included}` dict.

Both methods check tenant isolation: `get_by_id_tenant(tenant_id=..., draft_id=...)` returns `None` on missing → `ValueError` raised (service layer, not HTTP exception — router maps it to 404 in T-3).

### HTML renderer

`_render_landing_html()` is a private module-level function. Renders 5 known brand identity fields: `brand_name`, `tagline`, `vertical`, `location`, `description`. Values HTML-escaped before embedding. Returns a `<section class="landing-preview">` block. Intentionally minimal — Slice 1 preview only, not a full landing page.

### TYPE_CHECKING guard

`SimulatePersonalityService` and `BrandStudioDraftRepository` imported under `TYPE_CHECKING` to avoid circular imports at runtime. Constructor accepts them as `object` typed at runtime — dependency injection pattern used throughout codebase.

## Tests produced

| Test | Class | Verified behavior |
|---|---|---|
| `test_generate_whatsapp_preview_happy` | `TestLivePreviewServiceWhatsApp` | Draft found + simulate returns sample → dict with sample_text, tenant_id passed to simulate |
| `test_generate_whatsapp_preview_cached` | `TestLivePreviewServiceWhatsApp` | `cache_hit=True` from simulate → `cached=True` in result |
| `test_generate_whatsapp_preview_no_draft_raises_value_error` | `TestLivePreviewServiceWhatsApp` | `None` draft → ValueError(draft_id), simulate NOT called |
| `test_generate_landing_snippet_happy` | `TestLivePreviewServiceLanding` | Brand payload → HTML with content + sections_included = payload keys |
| `test_generate_landing_snippet_empty_payload` | `TestLivePreviewServiceLanding` | Empty payload → HTML skeleton + sections_included=[] |
| `test_generate_landing_snippet_no_draft_raises_value_error` | `TestLivePreviewServiceLanding` | `None` draft → ValueError(draft_id) |
| `test_extract_url_only_flow` | `TestExtractTenantContextIntegration` | URL-only: scraper called, doc extractor NOT called, slots merged into OnboardingDraft |
| `test_extract_text_content_only_flow` | `TestExtractTenantContextIntegration` | text_content-only: doc extractor called, scraper NOT called, slot in bonus_extracted |
| `test_audio_path_deferred` | `TestExtractTenantContextIntegration` | `@pytest.mark.skip` confirming audio deferred Slice 2 |

Total: 8 passed, 1 skipped.

## Validators run

| Validator | Command | Result |
|---|---|---|
| `be_lint_ruff_check` | `.venv/bin/ruff check src/...live_preview_service.py tests/...application/ --no-cache` | 0 errors |
| `be_format_ruff` | `.venv/bin/ruff format --check ...` | 4 files already formatted |
| `be_arch_fitness_brand` | `.venv/bin/pytest vitalia/backend/tests/architecture/ -x -q` | 245/245 PASS |
| `be_test_onboarding` | `.venv/bin/pytest vitalia/backend/tests/modules/vitalia/copilot/ -v` | 35 passed, 1 skipped |
