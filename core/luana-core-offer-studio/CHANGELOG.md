# Changelog — luana-core-offer-studio

All notable changes to this package are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this package adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-05-17

### Added

- `MaintenanceScheduleEnum` in `src/luana_core_offer_studio/domain/enums.py`
  (`NONE | MONTHLY | QUARTERLY | BIANNUAL | ANNUAL | CUSTOM`). Used by brand
  cron jobs that detect tenants whose offers have lapsed their maintenance
  window. Default `NONE` preserves one-shot semantics for legacy offers.
- `OfferAdherenceContract` Protocol in
  `src/luana_core_offer_studio/domain/offer.py`. Universal columns brand
  `offers` tables MUST implement: `requires_multi_session` (bool default
  False), `sessions_expected` (int >= 1 nullable), `gap_alert_days` (int
  nullable), `maintenance_schedule` (MaintenanceScheduleEnum default NONE),
  `maintenance_custom_days` (int >= 1 nullable, required when
  `maintenance_schedule == CUSTOM`). Enables multi-session adherence flows
  + periodic maintenance re-engagement cron jobs cross-brand. Promotion
  proposal:
  [`docs/promotion-protocol/proposals/2026-05-17-offer-studio-multi-session-maintenance.md`](../../docs/promotion-protocol/proposals/2026-05-17-offer-studio-multi-session-maintenance.md)
  (state: migrated).
- Contract tests at `tests/domain/test_offer_adherence_contract.py` (Protocol
  shape + 6 maintenance schedule values + multi-session validation +
  non-conforming fail).

### Notes

- Backward-compatible minor bump. All new fields are nullable or default-safe
  (`NONE` / `False`); existing brand `offers` tables remain valid until they
  opt-in via local Alembic migration (`ADD COLUMN IF NOT EXISTS` +
  `CREATE TYPE IF NOT EXISTS`).
- `_CATALOG_VERSION` constants in `src/luana_core_offer_studio/api/*.py`
  remain at `2026-04-*` (NOT bumped). `OfferAdherenceContract` is a Protocol
  contract layer (typing only), NOT a catalog enum. The 7 catalog axes
  (archetype, value_level, format, section, variant, biz_type, ladder_hints,
  preset) are unchanged.
- `docs/core-modules/offer-studio.md` engine-docs file pending creation
  (deferred to a follow-up engine-docs cementing pass — see TODO in promotion
  proposal Cross-references section).
- Brand consumer opt-in tracking: Vitalia (origen, T-be-migration-015) opt-in
  immediate in Slice 1. Comunify reconciliation check pending (Story 12's
  `sessions_expected` column should align with engine canonical default).
  Fitflow/Saasora/Retailly/Guestly/Inmoflow/Fixia bootstrap pendings inherit
  contract at brand bootstrap time.

## [0.1.0] — 2026-05-15

### Added

- Initial extraction from `backend/src/modules/offer/` to
  `core/luana-core-offer-studio/` as part of multibrand reorg (Story 5+).
  7 catalog axes (archetype, value_level, format, section, variant, biz_type,
  ladder_hints, preset), domain models (Offer, PricingStructure,
  DeliverableItem, ObjectionItem), Pydantic schemas (`offer_ai_schemas.py`),
  copilot provider entry point, extraction orchestrator hook.
