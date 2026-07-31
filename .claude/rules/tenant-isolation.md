# Tenant Isolation

Every data op tenant-scoped. Sin excepciones.

- BE: `.where(Model.tenant_id == tenant_id)` en TODA query (incluye `get_by_id`). `tenant_id` from `X-Tenant-ID` header (middleware). Repos reciben `tenant_id` required param.
- FE: `fetchClient` auto-inyecta `X-Tenant-ID` from Clerk. Routes incluyen `[tenantId]`. NUNCA hardcode.

## FE — fuente del `tenant_id` (PROHIBIDO Clerk org)

- El `tenant_id` del FE SALE de `useTenantId()` — **NUNCA** de `useAuth().orgId` / `useOrganization()`. Luana **no usa Clerk Organizations** en esta etapa: el multi-tenant vive en `luana-core-iam` (tenants + users propios); Clerk es solo identity provider.
- ❌ `const tenantId = useAuth().orgId` (o pasar `orgId` como header `X-Tenant-ID`) → 500 en todo PHI/data real. Vuln sistémica: 35 archivos del FE vitalia (fix 2026-06-01).
- Enforce: arch-test `vitalia/frontend/src/__tests__/architecture/test-no-clerk-organizations.test.ts`. Learning: `vitalia/docs/learnings/2026-06-01-fe-tenant-from-clerk-org-systemic.md`. MEMORY: `no-clerk-organizations`.
