# T-BE-4 Implementation Log — BioGenerationService + generate-bio endpoint

**Ticket:** T-BE-4
**Story:** vitalia-fase2-lisa-doctores
**Builder:** builder-backend (Sonnet)
**Date:** 2026-05-31
**State:** tests-passing

---

## § Plan (technical design pre-code)

### Architecture alignment

Per 03-arch D-4: `BioGenerationService` is a deterministic single-shot extractive service
living in `clinics/application/`. NOT agentic — no LangGraph, no copilot/sales_agent surface.
R23 N/A → Sonnet-eligible.

### DDD layers by this ticket

1. **Domain** — `BioPublic` already exists (T-BE-1). No new domain entities needed.
2. **Application** — NEW `bio_generation_service.py`:
   - `BioGenerationService.generate(doctor) -> BioPublic` (no-raise, fallback)
   - `BioGenerationService.generate_with_error(doctor) -> tuple[BioPublic, str | None]`
   - Consumes `luana_core_llm.factory.LLMFactory` (read-only, NOT edited)
   - Protocol-based DI for testability (no real LLM calls in tests)
3. **API** — MODIFY `doctors_router.py`:
   - Add `POST /{doctor_id}/generate-bio -> GenerateBioResponse`
   - Add `GenerateBioRequest` + `GenerateBioResponse` DTOs to `dtos.py`

### Test battery (TDD order)

1. RED: `test_bio_generation_service.py` fails (ModuleNotFoundError — service not yet created)
2. Implement `BioGenerationService` 
3. GREEN: service unit tests pass
4. Add endpoint + DTOs
5. GREEN: all 12 tests pass

Tests designed per `test-design-doctrine.md` for `application/service` nature:
- `test_generate_returns_bio_public_from_notes` — happy path
- `test_generate_sends_material_in_prompt` — material inclusion guardrail
- `test_generate_prompt_includes_no_invent_guardrail` — "usa SOLO" in system_prompt
- `test_generate_empty_inputs_returns_placeholder_sections` — empty material edge case
- `test_fallback_on_llm_exception_returns_empty_bio` — LLM failure graceful fallback
- `test_fallback_error_message_is_set` — error message returned on failure
- `test_fallback_message_no_voseo` — Spanish neutro validation
- `test_fallback_on_json_parse_error` — malformed JSON fallback
- `test_fallback_on_missing_sections_in_response` — partial JSON fallback
- `test_generate_bio_endpoint_route_exists` — route registration check
- `test_generate_bio_endpoint_returns_200_on_success` — endpoint 200 + correct response
- `test_generate_bio_endpoint_fallback_on_llm_error` — endpoint 200 fallback

### Integration (CONN)

- **Consumer:** FE `BioRepoInputs` calls `POST /{doctor_id}/generate-bio` (T-FE-2)
- **Registered:** endpoint in `doctors_router` (already registered in main.py under T-BE-1)
- **Home cap:** `clinics.lisa.doctores` (header `# cap: clinics.lisa.doctores`)

---

## § Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | DDD Inside-Out + FastAPI patterns + SA 2.0 + tenant isolation | Protocol-based DI for LLM service. Lazy import for `luana_core_llm.factory`. `generate_with_error` returns tuple to decouple error from HTTP decision. No `response_model=` skipped. |
| `brand-expert` | Voice anchor optional reading per 03-arch D-4 | Consume `PersonalityProfile.system_instruction` as string only (pass as `voice_anchor` param). Do NOT write to brand aggregates. Port exists but not used in MVP bio-gen. |
| `tessl__graceful-degradation` | External LLM call — timeout + fallback required | `generate_with_error()` catches ALL exceptions. Returns `(BioPublic(), BIO_GENERATION_FALLBACK_MESSAGE)` on any LLM failure. HTTP 200 (not 500) — fallback doesn't break autosave of rest of profile. `_LLM_TIMEOUT_SECONDS = 30` documented. |

**Step 0 GATE status:** Skills declared upfront + invoked + cited above. ✅

---

## § Step 0.5 Default Flip Detection

No feature flags touched. No call-path defaults changed. Not applicable. ✅

---

## § TDD Evidence

**First entry = RED test:**

```
ERROR collecting tests/modules/vitalia/clinics/test_bio_generation_service.py
ModuleNotFoundError: No module named 'src.modules.vitalia.clinics.application.bio_generation_service'
```

After implementation: `12 passed in 0.46s` ✅

---

## § Files Created/Modified

| File | Operation | Notes |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/clinics/application/bio_generation_service.py` | NEW | BioGenerationService + BIO_GENERATION_FALLBACK_MESSAGE + LLMServiceProtocol |
| `vitalia/backend/src/modules/vitalia/clinics/api/dtos.py` | MODIFY | Add GenerateBioRequest + GenerateBioResponse |
| `vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py` | MODIFY | Add POST /{doctor_id}/generate-bio endpoint + import BioGenerationService |
| `vitalia/backend/tests/modules/vitalia/clinics/test_bio_generation_service.py` | NEW | 12 tests TDD RED-first |

---

## § Quality Gates

| Gate | Result | Notes |
|---|---|---|
| `ruff check` | PASS | 0 errors |
| `ruff format --check` | PASS | 0 files to reformat |
| `mypy` | SKIP | mypy not installed in workspace venv (not a regression — pre-existing) |
| Clinics suite: `pytest tests/modules/vitalia/clinics/` | PASS | 138 passed |
| Bio generation tests (V-FN-9): 12 tests | PASS | All 12 pass |
| Architecture fitness: `pytest tests/architecture/` | PASS (1 pre-existing skip) | `treatment_plans.notes BYTEA` is pre-existing CRM debt noted in ticket instructions ("ignore pre-existing treatment_plans.notes CRM debt"). Not introduced by T-BE-4. |

---

## § Cross-module reads (read-only)

- Read `core/luana-core-llm/src/luana_core_llm/router.py` — understand `MultiRoleLLMRouter.generate_response` signature. CONSUME via import only. NOT edited.
- Read `vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/lucas_re_engagement_service.py` — pattern reference for LLM service Protocol usage in brand services.

---

## § Anti-duplication check

- `luana_core_llm.factory.LLMFactory` — existing engine, consumed via lazy import
- No new LLM adapter created
- No new LangGraph/copilot/sales_agent surface
- No engine package edited

---

## § Default flip audit (Step 0.5)

N/A — no feature flags touched, no call-path defaults changed.

---

## § Spanish neutro compliance

<!-- voseo-allowed: doc interno de maquinaria — lista patrones voseo como referencia técnica para tests de regresión, NO son strings user-facing -->

`BIO_GENERATION_FALLBACK_MESSAGE = "No pudimos generar la bio. Por favor, intenta de nuevo."`
- Uses `intenta` (tuteo) ✅
- No voseo (intentá, podés, etc. — these patterns are excluded from the fallback message) ✅
- Test `test_fallback_message_no_voseo` validates this ✅
