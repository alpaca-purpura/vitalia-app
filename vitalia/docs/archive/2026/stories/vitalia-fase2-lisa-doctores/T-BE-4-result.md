# T-BE-4 Result — BioGenerationService + generate-bio endpoint

**Ticket:** T-BE-4
**Story:** vitalia-fase2-lisa-doctores
**State:** tests-passing (awaiting gate-runner + auditor-backend)

---

## Summary

Implemented `BioGenerationService` (deterministic extractive, NOT agentic) + POST `/{doctor_id}/generate-bio` endpoint per 03-arch D-4.

### Deliverables completed

1. **`clinics/application/bio_generation_service.py`** (NEW)
   - `BioGenerationService.generate(doctor) -> BioPublic` — no-raise shorthand
   - `BioGenerationService.generate_with_error(doctor) -> tuple[BioPublic, str | None]` — endpoint uses this
   - `BIO_GENERATION_FALLBACK_MESSAGE` constant (Spanish neutro, no voseo)
   - `LLMServiceProtocol` — Protocol for DI + testability without real LLM calls
   - Extractive prompt: system_prompt says "usa SOLO el material; no inventes" (no-invent guardrail)
   - Optional `voice_anchor` param (reads PersonalityProfile.system_instruction as tone anchor only — does NOT write to brand aggregates)
   - LLM via `luana_core_llm.factory.LLMFactory` (shared engine — consumed, NOT edited)
   - Graceful degradation: any exception → `(BioPublic(), BIO_GENERATION_FALLBACK_MESSAGE)`
   - JSON parse fallback: malformed LLM output → empty `BioPublic` (no raise)

2. **`clinics/api/dtos.py`** (MODIFY — add DTOs)
   - `GenerateBioRequest` — explicit empty request body (arch convention)
   - `GenerateBioResponse` — `{bio: BioPublicDTO, error_message: str | None}`

3. **`clinics/api/doctors_router.py`** (MODIFY — add endpoint)
   - `POST /{doctor_id}/generate-bio` with `response_model=GenerateBioResponse`
   - RBAC: `admin_clinic` required
   - Returns 200 on success AND on LLM failure (fallback + error_message)
   - Imports `BioGenerationService` + new DTOs

4. **`tests/modules/vitalia/clinics/test_bio_generation_service.py`** (NEW)
   - 12 tests — TDD RED-first
   - Covers V-FN-9: no-invent guardrail + fallback on LLM fail

### Quality gates

| Gate | Status |
|---|---|
| `ruff check` | PASS |
| `ruff format --check` | PASS |
| `pytest tests/modules/vitalia/clinics/` (138 tests) | PASS |
| V-FN-9 (12 tests) | PASS |
| Architecture fitness (excluding pre-existing treatment_plans debt) | PASS |

### Pre-existing issue (not introduced by T-BE-4)

`test_pgcrypto_phi_columns::test_no_phi_column_uses_text_or_varchar_unencrypted` fails on `treatment_plans.notes TEXT` — this is explicitly cited in T-BE-4 instructions as "ignore pre-existing treatment_plans.notes CRM debt". Not introduced by this ticket.

### Files changed

```
vitalia/backend/src/modules/vitalia/clinics/application/bio_generation_service.py  (NEW)
vitalia/backend/src/modules/vitalia/clinics/api/dtos.py                            (MODIFY)
vitalia/backend/src/modules/vitalia/clinics/api/doctors_router.py                  (MODIFY)
vitalia/backend/tests/modules/vitalia/clinics/test_bio_generation_service.py       (NEW)
vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/T-BE-4-impl-log.md        (NEW)
vitalia/docs/product/stories/vitalia-fase2-lisa-doctores/T-BE-4-result.md          (NEW)
```

### Key design decisions

- **No PHI in bio generation**: bio_inputs_notes/bio_links are promotional material (CV/diploma), NOT patient PHI. Audit log NOT written for this endpoint (confirmed per 03-arch D-4).
- **HTTP 200 on LLM failure**: fallback returns 200 + `error_message` — does NOT return 5xx. This prevents breaking autosave of the rest of the doctor profile.
- **Lazy LLM import**: `LLMFactory` imported lazily to avoid import errors in test environments without LiteLLM configured.
- **Protocol-based DI**: `LLMServiceProtocol` allows pure-unit tests without importing engine.
- **Voice anchor optional**: `voice_anchor` param passed to `__init__` — MVP doesn't wire it to PersonalityProfile port, but the param is available for T-FE-2 to optionally pass it.
