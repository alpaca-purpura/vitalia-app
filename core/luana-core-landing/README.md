# luana-core-landing

Version: 0.0.1-alpha

Brand-agnostic landing page generation engine lifted from Nicolify (`backend/src/modules/landing/`).

## Purpose

Multi-tenant landing page generation and management: offer-driven landing page creation,
template selection based on preset flags, SEO metadata, hero sections, and publication
lifecycle. Designed as a brand-agnostic reusable engine consumed by any brand vertical.

## Scope

- Landing page entity and lifecycle (draft, published, archived)
- Offer-driven template selection (IS_LEAD_MAGNET, HIGH_TICKET, RECURRING_BILLING flags)
- Section generation from offer data
- Tenant isolation on all queries
- API: create, read, update, publish, archive landings

## Version

`0.0.1-alpha` — lifted in Story 4 (`luana-crm-analytics-landing-connections`).

## Deferred

- `copilot_provider/` → Story 6 (ChatOrchestrator not yet lifted)

See `core/DEFERRED-FILES.md` for full audit trail.

## Outcome reference

`docs/product/outcomes/luana-platform-migration.md`
