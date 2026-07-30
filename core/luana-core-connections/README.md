# luana-core-connections

Version: 0.0.1-alpha

Brand-agnostic connections and channel management engine lifted from Nicolify (`backend/src/modules/connections/`).

## Purpose

Multi-tenant external channel and platform connection management: OAuth flows for
Google/Meta/ManyChat/Shopify/Mailerlite, webhook routing for WhatsApp/Telegram/Instagram,
and marketing connector adapters. Designed as a brand-agnostic reusable engine.

## Scope

- Channel connection entity (OAuth tokens, provider mapping, soft-delete)
- Communication channel adapters: WhatsApp (v1/v2), Telegram, Instagram, YouTube, Webhook
- Marketing connectors: ManyChat, Mailerlite, Shopify
- Webhook security: Meta signature verification, Shopify HMAC
- API: connection status, channel info, OAuth callbacks, webhook ingestion

## Version

`0.0.1-alpha` — lifted in Story 4 (`luana-crm-analytics-landing-connections`).

## Deferred

- `copilot_provider/` → Story 6 (ChatOrchestrator not yet lifted)
- `api/dependencies/__init__.py` real wiring → Story 7 (ChatOrchestrator composition root)
  — a NotImplementedError stub is in place for import-compatibility.

See `core/DEFERRED-FILES.md` for full audit trail.

## Outcome reference

`docs/product/outcomes/luana-platform-migration.md`
