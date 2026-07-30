# luana-core-tenant-domains

Brand-agnostic tenant custom domain management package for the Luana Platform.

## Lift origin

Lifted verbatim from `AISALESHT/backend/src/modules/tenant_domains/` (Story 3 — 2026-05-11).
Tests lifted from `AISALESHT/backend/tests/modules/tenant_domains/`.

## Key exports

- `luana_core_tenant_domains.domain.domain_entity.TenantDomain` — domain aggregate root
- `luana_core_tenant_domains.infrastructure.domain_repository_impl.SqlTenantDomainRepository`
- `luana_core_tenant_domains.infrastructure.cloudflare_client.CloudflareClient`
- `luana_core_tenant_domains.api.domain_router` — FastAPI router
- `luana_core_tenant_domains.workers.tasks` — ARQ async worker tasks

## Version

0.0.1-alpha (Story 3 lift)
