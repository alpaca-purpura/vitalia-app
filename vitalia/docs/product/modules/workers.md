---
module: workers
brand: vitalia
last_updated: 2026-05-18
---

# workers — ARQ + idempotent_cron

ARQ workers scaffold con `idempotent_cron` decorator que wraps engine `luana_core_idempotency.IdempotentStore` + OTel cron_span + structlog audit + Sentry capture/re-raise. 11 cron job scaffolds raise NotImplementedError con story citations (fail-loud pattern).

Promotion candidate cross-brand (todas las brands eventualmente tendrán cron jobs — pattern repetible). Lift candidate a `core/luana-core-workers/` o extender `core/luana-core-platform/workers/`.

## Capabilities

<!-- auto-list:start -->
- `vitalia-idempotent-cron-arq-scaffold` (live)
<!-- auto-list:end -->
