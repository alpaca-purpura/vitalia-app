---
module: payment
brand: vitalia
last_updated: 2026-05-16
---

# payment — Gateways LATAM + recurring

3 adapters: MercadoPago (LATAM primary, LIFT shared a `core/luana-core-channels`), Stripe Connect (cross-border + fallback), tokenized recurring (paquetes + treatment installments). 5 webhook receivers HMAC + idempotency. NO usa stripe_healthcare per D7 (hipaa_lite).

## Capabilities

<!-- auto-list:start -->
- `payment-gateways-latam-recurring` (live)
<!-- auto-list:end -->
