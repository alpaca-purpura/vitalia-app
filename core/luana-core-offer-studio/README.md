# luana-core-offer-studio

Version: 0.0.1-alpha

Lift origin: `backend/src/modules/offer/` (AISALESHT monorepo)

## Key exports

Offer domain engine: 7 catalogs DAG (archetype, value level, section, format, variant structure, offer ladder hints, type presets with 84 presets), offer aggregate root, field contract + section catalog, infrastructure models/repositories, application services (offer lifecycle, asset, completion, counts, knowledge, landing generation), and FastAPI api layer.

## Story 5 lift

Lifted as part of `luana-brand-offer-studios` story.

## Deferrals

- `backend/src/modules/offer/copilot_provider/` (5 files) → Story 6 (imports `src.modules.copilot`)
- `backend/src/modules/offer/api/offer_ai.py` → Story 6 (imports `src.modules.copilot.application.services.offer_psychology_service`)
- `backend/src/modules/offer/api/counts.py` → Story 8 (imports `src.modules.advertising`)
- `backend/src/modules/offer/api/campaigns.py` → Story 8 (idem)
- `backend/tests/modules/offer/test_offer_data_access_provider.py` → Story 6
