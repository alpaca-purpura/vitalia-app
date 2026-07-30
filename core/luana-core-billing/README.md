# luana-core-billing

**Version:** 0.0.1-alpha  
**Lift origin:** `AISALESHT/backend/src/shared/billing/`  
**Lift commit:** `72d77b7` (feat(luana-core-billing): lift billing package)

## Overview

Budget guard and rate limiter for agent modules. Prevents runaway LLM spend
and enforces per-tenant conversation rate limits before each agent turn.

## Key exports

- `luana_core_billing.budget_guard.BudgetGuard` — checks remaining budget before LLM calls; raises `BudgetExceededError`
- `luana_core_billing.rate_limiter.RateLimiter` — token-bucket rate limiter per tenant + channel
- `luana_core_billing.tenant_billing_config_repository.TenantBillingConfigRepository` — reads per-tenant billing config
- `luana_core_billing.pricing_cache.PricingCache` — TTL cache for model pricing snapshots
