# luana-core-analytics-engine

Version: 0.0.1-alpha

Brand-agnostic analytics ETL engine lifted from Nicolify (`backend/src/modules/analytics/`).

## Purpose

Multi-tenant analytics pipeline: ETL extraction from providers (Meta, GA4, ManyChat, YouTube),
stage services (attraction, capture, conversion, retention, expansion), metric catalog,
official metrics storage, and scheduler. Designed as a brand-agnostic reusable engine.

## Scope

- Domain: metric catalog, stage constants, extraction contract
- Infrastructure: provider adapters (Meta, GA4, ManyChat, YouTube, TikTok), official metrics model, repositories
- Application: stage services, ETL service, scheduler, workers
- API: metrics routes, catalog routes, extraction status

## Version

`0.0.1-alpha` — lifted in Story 4 (`luana-crm-analytics-landing-connections`).
T-3a (domain+framework), T-3b (infrastructure), T-3c (workers+scheduler) all DONE.

## Deferred

- `copilot_provider/` → Story 6 (ChatOrchestrator not yet lifted)

See `core/DEFERRED-FILES.md` for full audit trail.

## Outcome reference

`docs/product/outcomes/luana-platform-migration.md`
