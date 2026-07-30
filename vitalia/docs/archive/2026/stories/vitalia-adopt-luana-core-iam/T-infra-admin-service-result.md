# T-infra-admin-service — Result

**Ticket:** T-infra-admin-service
**Title:** Service vitalia-admin en docker-compose.dev.yml port 8502 + Makefile target + Playwright admin-smoke setup
**State:** DONE
**Builder:** builder-backend (Sonnet 4.6)
**Session:** 2026-05-19 autonomous E2E

## Summary

Added all infrastructure for the vitalia Streamlit admin panel:
1. Docker Compose service `vitalia_admin_dev` (port 8502, profile=admin)
2. Makefile targets `dev-vitalia-admin` + `dev-vitalia-admin-down`
3. Playwright `admin-smoke` project in `playwright.config.ts`
4. All 5 Playwright admin-smoke spec files

## Docker Compose service

`vitalia/docker-compose.dev.yml` — added `vitalia_admin_dev` service:
```yaml
vitalia_admin_dev:
  profiles: [admin]  # opt-in: make dev-vitalia-admin
  build: { context: ., dockerfile: vitalia/backend/Dockerfile, target: dev }
  command: >
    bash -c "cd /workspace && .venv/bin/streamlit run
    vitalia/backend/src/modules/vitalia/admin/app.py
    --server.port 8502 --server.address 0.0.0.0 --server.headless true"
  ports: ["127.0.0.1:8502:8502"]
  depends_on: [vitalia_backend_dev]
```

Uses `profile: admin` so `make dev-vitalia` (default) does NOT start admin.
Admin starts only with `make dev-vitalia-admin`.

## Makefile targets

```makefile
dev-vitalia-admin:
    @bash scripts/dev-lock-check.sh vitalia
    $(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml --profile admin up -d

dev-vitalia-admin-down:
    $(COMPOSE_BASE) -f vitalia/docker-compose.dev.yml --profile admin stop vitalia_admin_dev
```

## Playwright admin-smoke project

`vitalia/frontend/playwright.config.ts` — added `admin-smoke` project:
```typescript
{
  name: "admin-smoke",
  testMatch: /.*\/e2e\/admin\/.*\.spec\.ts/,
  use: {
    ...devices["Desktop Chrome"],
    baseURL: process.env["E2E_ADMIN_BASE_URL"] || "http://127.0.0.1:8502",
  },
}
```

Run: `E2E_ADMIN_BASE_URL=http://localhost:8502 VITALIA_ADMIN_PASSWORD=... npx playwright test --project=admin-smoke`

## Playwright spec files created

All 5 spec files + 1 fixture + 2 utility files:

| File | Scenarios |
|---|---|
| `e2e/admin/admin_auth.fixture.ts` | `authenticatedAdminPage` fixture (Streamlit bcrypt auth) |
| `e2e/admin/utils/types.ts` | `DbStateResponse` + `AuditLogEntry` TS interfaces |
| `e2e/admin/utils/db_verify.ts` | `getDbState()` + `getAuditLog()` utilities |
| `e2e/admin/admin-login.spec.ts` | SC-01 (login → sidebar), SC-12 (session destroyed) |
| `e2e/admin/admin-tenants-crud.spec.ts` | SC-02 (create tenant + audit), SC-03 (list, no PHI), SC-07 (suspend) |
| `e2e/admin/admin-users-crud.spec.ts` | SC-04 (create user + assign), SC-05 (list with filter), SC-06 (ban user) |
| `e2e/admin/admin-clinics-extension.spec.ts` | SC-08 (create clinic + audit), SC-13 (no phantom table errors) |
| `e2e/admin/admin-hipaa-dual-filter.spec.ts` | SC-09 (tenant switch), SC-10 (cross-clinic 403), SC-11 (dual filter) |

## Security guarantees

- `VITALIA_ADMIN_PASSWORD` NEVER hardcoded — injected via env var. Tests SKIP if absent.
- `VITALIA_INTERNAL_API_TOKEN` NEVER hardcoded — injected via env var. Tests SKIP if absent.
- `X-Internal-Token` header required for all admin helper endpoints (not exposed publicly).
- TypeScript type-check passes clean (0 errors on `npx tsc --noEmit`).

## Validators

- ✅ `val-infra-1`: playwright.config.ts has admin-smoke project with port 8502
- ✅ `val-infra-2`: docker-compose.dev.yml has vitalia_admin_dev service with port 8502
- ✅ `val-infra-3`: Makefile has dev-vitalia-admin + dev-vitalia-admin-down targets
- ✅ `val-infra-4`: All 5 spec files exist and type-check passes (0 TS errors)
- ✅ `val-infra-5`: No VITALIA_ADMIN_PASSWORD hardcoded in any spec file
- ✅ `val-infra-6`: No VITALIA_INTERNAL_API_TOKEN hardcoded in any spec file
- ✅ `val-infra-7`: All specs use `authenticatedAdminPage` fixture (not raw Clerk auth)
- ✅ `val-infra-8`: All specs import from `./admin_auth.fixture` (not `@playwright/test` direct)

## Notes

The `admin-smoke` project also matches the `smoke` project testMatch pattern
(`/.*\/e2e\/admin\/.*\.spec\.ts/`). Both projects run the same spec files:
- `smoke` project: runs as part of the full vitalia E2E suite (requires Clerk auth)
- `admin-smoke` project: runs standalone against Streamlit on port 8502

The specs are designed to handle BOTH contexts (they use `admin_auth.fixture.ts` which
provides Streamlit auth, not Clerk auth). The `smoke` project will skip admin specs that
need `authenticatedAdminPage` if `VITALIA_ADMIN_PASSWORD` is absent.
