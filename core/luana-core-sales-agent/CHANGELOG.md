# Changelog — luana-core-sales-agent

All notable changes to this package are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this package adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-05-19

### Changed

- **BREAKING semantic (engine brand-agnostic principle):** purged 3 residual
  nicolify-specific hardcodes from sales_agent engine code. Continuation of
  cement work started by `luana-core-platform` 0.3.0 (proposal
  [2026-05-19-purge-nicolify-defaults-core-config](../../docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-defaults-core-config.md)).

#### `src/luana_core_sales_agent/application/tools/payment/providers.py`

- Removed 2 hardcoded Stripe checkout fallback URLs:
  - `success_url` default `"https://app.nicolify.com/payment/success"` →
    derived from `settings.FRONTEND_URL` (brand-agnostic per proposal padre)
  - `cancel_url` default `"https://app.nicolify.com/payment/cancel"` →
    derived from `settings.FRONTEND_URL`
- Added module-level helper `_build_payment_url(action, metadata)` that:
  - Honors metadata override (`success_url` / `cancel_url` keys) first
  - Falls back to `{settings.FRONTEND_URL}/payment/{action}`
  - Raises `RuntimeError` failfast if `settings.FRONTEND_URL` is empty
    (no silent leak to nicolify legacy default)

#### `src/luana_core_sales_agent/api/payment_webhooks.py`

- Removed deprecated brand-specific header fallback `x-nicolify-tenant-id`
  from `_resolve_signing_secret()`. Clients MUST send the standard
  `x-tenant-id` header. Cross-codebase grep (engine + 4 brand backends)
  confirmed 0 consumers depending on deprecated header exclusively at the
  time of removal — change is non-breaking in practice.

### Migration notes

- **Brand consumers MUST have `FRONTEND_URL` set** in their
  `{brand}/.env.dev` / `.env.prod` (already enforced by proposal padre
  `luana-core-platform` 0.3.0). Any tenant that creates a Stripe payment
  link via `StripePaymentProvider.create_payment_link()` will now derive
  success/cancel URLs from brand `FRONTEND_URL` automatically — Stripe
  redirect post-payment lands on the correct brand domain.
- **Behavioral verify pre-merge:**
  - nicolify (`FRONTEND_URL=https://app.nicolify.com`): URLs derivadas
    `https://app.nicolify.com/payment/success` + `/cancel` → idéntico al
    hardcoded original → **ZERO REGRESSION**.
  - vitalia (`FRONTEND_URL=https://dev-app.vitalialat.com`): URLs derivadas
    `https://dev-app.vitalialat.com/payment/...` → correcto vitalia (futuro
    payment integration).
- **External clients sending webhooks:** if any external service was
  sending `x-nicolify-tenant-id` header EXCLUSIVELY (without standard
  `x-tenant-id` fallback), they must migrate to standard header. Audit
  pre-lift showed 0 such clients across the monorepo.
- Promotion proposal: [`docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-hardcodes-sales-agent.md`](../../docs/promotion-protocol/proposals/2026-05-19-purge-nicolify-hardcodes-sales-agent.md) (state: migrated).

### Added

- `_build_payment_url(action, metadata)` module-level helper in
  `application/tools/payment/providers.py` — centralizes brand-agnostic
  payment URL derivation. Reusable for future payment providers
  (MercadoPago, PayPal, etc.) that also need success/cancel URLs.

### Notes

- Bump is `minor` (0.1.0 → 0.2.0) — this is the **first CHANGELOG entry**
  for `luana-core-sales-agent`. Initial 0.1.0 release (carve-out
  2026-05-15 from `backend/src/modules/sales_agent/`) was not formally
  changelogged at the time; this entry establishes the cadence going
  forward.
- Behavioral compatibility: zero regression for nicolify (defaults derive
  to the same URLs that were hardcoded). New failfast behavior is desired
  outcome — silent contamination to nicolify defaults is the bug being
  fixed.

## [0.1.0] — 2026-05-15

### Added

- Initial extraction from `backend/src/modules/sales_agent/` to
  `core/luana-core-sales-agent/` as part of multibrand reorg (Story 5+).
  Establishes engine package for sales_agent with brand-extension surface
  in `{brand}/backend/src/modules/{brand}/sales_agent/` (per CLAUDE.md
  ENGINE + BRAND-EXTENSION verdict).
