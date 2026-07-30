# luana-core-idempotency

**Version:** 0.0.1-alpha  
**Lift origin:** `AISALESHT/backend/src/shared/idempotency/`  
**Lift commit:** `3cc9c36` (feat(luana-core-idempotency): lift idempotency package)

## Overview

Idempotency key management for background tasks and webhooks. Prevents duplicate
processing of retried operations across all consumer modules.

## Key exports

- `luana_core_idempotency.service.IdempotencyService` — check / claim / release idempotency keys
- `luana_core_idempotency.models.IdempotencyKeyModel` — SQLAlchemy persistence model
- `luana_core_idempotency.repository.IdempotencyRepository` — data access layer
