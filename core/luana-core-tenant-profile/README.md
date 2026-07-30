# luana-core-tenant-profile

Brand-agnostic tenant profile package for the Luana Platform.

## Lift origin

Lifted verbatim from `AISALESHT/backend/src/modules/tenant_profile/` (Story 3 — 2026-05-11).
Tests lifted from `AISALESHT/backend/tests/modules/tenant_profile/`.

## Key exports

- `luana_core_tenant_profile.domain.tenant_profile.TenantProfile` — aggregate root
- `luana_core_tenant_profile.domain.tenant_profile.RATE_LIMIT_WINDOW` — 30-day rate limit constant
- `luana_core_tenant_profile.infrastructure.repositories.tenant_profile_repository.SqlTenantProfileRepository`
- `luana_core_tenant_profile.api.router` — FastAPI router (mount at `/api/v1/tenant/profile`)
- `luana_core_tenant_profile.api.business_types_catalog` — catalog router (mount at `/api/v1/catalogs/business-types`)

## Version

0.0.1-alpha (Story 3 lift)
