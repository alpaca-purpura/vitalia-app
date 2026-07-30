# luana-core-iam

Brand-agnostic IAM (Identity & Access Management) package for the Luana Platform.

## Lift origin

Lifted verbatim from `AISALESHT/backend/src/modules/iam/` (Story 3 — 2026-05-11).
Tests lifted from `AISALESHT/backend/tests/modules/iam/`.

## Key exports

- `luana_core_iam.domain.user.User` — User aggregate root
- `luana_core_iam.domain.tenant.Tenant` — Tenant aggregate root
- `luana_core_iam.api.dependencies.get_current_user` — FastAPI Depends for auth
- `luana_core_iam.api.dependencies.get_current_tenant_id` — FastAPI Depends for tenant
- `luana_core_iam.application.auth.verify_clerk_token` — Clerk JWT verification (brand-agnostic via env config)

## Brand-agnostic IAM

ClerkService reads `settings.CLERK_SECRET_KEY` from env/DI. Zero hardcoded Clerk app IDs or brand-specific control flow. Each brand wires its own Clerk app via env vars.

## Deferred

- `TenantModel.leads` relationship → Story 4 (CRM lift brings `LeadModel`)
- Alembic migration test assertions (test_t6a/t6c) → Story 10 (AISALESHT migrations)

## Version

0.0.1-alpha (Story 3 lift)
