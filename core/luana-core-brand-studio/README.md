# luana-core-brand-studio

Version: 0.0.1-alpha

Brand identity, personality, and extraction engine lifted from AISALESHT
`backend/src/modules/brand/` (Story 5, 2026-05-11).

## Key exports

`BrandSettings` (aggregate root), `PersonalityCompiler` v2 (ADR-001 §2.4 SSoT — voice
compiler lives in `domain.personality`), `BuyerPersona`, `BRAND_SECTION_MAP`,
`BRAND_FIELD_OVERRIDES`, `BrandReadPortImpl`, StyleAnalyzer LangGraph onboarding agent.

## Deferrals

- `brand/copilot_provider/` (8 files) → Story 6 (copilot lift; imports copilot.domain.{ports,workflow})
- `test_brand_context_injector.py` → Story 6
- `test_buyer_persona_fields_dropped_regression.py` → Story 6
- `test_worker_emits_summary_and_pills.py` → Story 6
