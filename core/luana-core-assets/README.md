# luana-core-assets

Brand-agnostic asset management package for the Luana Platform.

## Lift origin

Lifted verbatim from `AISALESHT/backend/src/modules/assets/` (Story 3 — 2026-05-11).
Tests lifted from `AISALESHT/backend/tests/modules/assets/`.

## Key exports

- `luana_core_assets.domain.entity.Asset` — asset aggregate root
- `luana_core_assets.domain.enums.{AssetType,AssetStatus,AssetScope,AssetPurpose,StorageProvider}`
- `luana_core_assets.application.assets_service.AssetsService`
- `luana_core_assets.application.gallery_service.GalleryService`
- `luana_core_assets.infrastructure.repositories.{asset_repository,gallery_repository,asset_link_repository}`
- `luana_core_assets.infrastructure.storage.{local,r2}` — storage strategies
- `luana_core_assets.api.router` — FastAPI router with file upload + promote endpoints

## Notes

- `offer_id` FK references `products` table (offer module, Story 4). Tests use a stub products
  table in db_engine until `luana-core-offer` lifts.

## Version

0.0.1-alpha (Story 3 lift)
