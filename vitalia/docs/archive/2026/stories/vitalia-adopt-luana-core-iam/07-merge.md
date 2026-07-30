# Merge artifact — vitalia/vitalia-adopt-luana-core-iam

> Brand: vitalia
> Merged: 2026-05-19
> Commit (squash-merge): TBD (este artifact pre-commit; SHA actualizado post-squash)
> Build commits range: b4cfaf8..HEAD (6 build commits + 1 self-fix during audit)

## § 1 — Gherkin verification matrix

| Scenario (Gherkin) | Test path | Status |
|---|---|---|
| SC-01 "Admin login bcrypt OK → dashboard" | `vitalia/frontend/e2e/admin/admin-login.spec.ts::SC-01` | ✅ PASS |
| SC-02 "Admin crea tenant nuevo" | `vitalia/backend/tests/modules/vitalia/admin/test_tenants_crud.py` + Playwright partial | ⚠️ ADVISORY (backend PASS, E2E partial GAP-1) |
| SC-03 "Admin lista tenants" | `vitalia/backend/tests/modules/vitalia/admin/test_tenants_crud.py` + Playwright partial | ⚠️ ADVISORY |
| SC-04 "Admin crea user + asigna tenant" | `vitalia/backend/tests/modules/vitalia/admin/test_users_crud.py` + Playwright partial | ⚠️ ADVISORY |
| SC-05 "Admin lista users con role per tenant" | backend unit tests + Playwright partial | ⚠️ ADVISORY |
| SC-06 "Admin banea user toggle is_active" | backend unit tests + Playwright partial | ⚠️ ADVISORY |
| SC-07 "Admin suspende tenant" | backend unit tests + Playwright partial | ⚠️ ADVISORY |
| SC-08 "Admin crea clinic asociada a tenant" | `vitalia/backend/tests/modules/vitalia/clinics/test_clinic_repository.py` + Playwright partial | ⚠️ ADVISORY |
| SC-09 "User-tenant dropdown switch → re-fetch" | `vitalia/backend/tests/modules/vitalia/clinics/test_require_clinic_access.py` + Playwright partial | ⚠️ ADVISORY |
| SC-10 "HIPAA cross-clinic query bloqueada" | `vitalia/backend/tests/modules/vitalia/clinics/test_require_clinic_access.py::test_cross_clinic_returns_403` | ✅ PASS (backend) ⚠️ ADVISORY (E2E partial) |
| SC-11 "HIPAA dual filter query PHI" | `vitalia/backend/tests/architecture/test_phantom_tables_zero_refs.py` + decorator tests | ✅ PASS (backend) ⚠️ ADVISORY (E2E partial) |
| SC-12 "Admin logout → session destroyed" | `vitalia/frontend/e2e/admin/admin-login.spec.ts::SC-12` | ✅ PASS |
| SC-13 "Phantom tables DELETED" | `vitalia/backend/tests/architecture/test_phantom_tables_zero_refs.py` + `test_admin_no_raw_sql.py` + Playwright `admin-clinics-extension.spec.ts::SC-13` | ✅ PASS |
| SC-14 "Migrations pending 002-023 aplicadas" | Manual verify `alembic current → 023_vitalia (head)` + `psql \dt` → 33 tablas | ✅ PASS |

**Resumen:** 4/14 PASS direct + 10/14 ADVISORY (backend PASS, E2E partial por pre-existing infra gap GAP-1 orthogonal). Detalle full en `06-audit/gherkin-matrix.md`.

## § 2 — Playwright E2E run

Última corrida E2E admin-smoke project:

```bash
cd vitalia/frontend && \
  E2E_ADMIN_BASE_URL=http://127.0.0.1:8502 \
  VITALIA_ADMIN_PASSWORD='7BFinws7Irux4wUGAzQ4' \
  npx playwright test --project=admin-smoke --reporter=line
```

- Specs configurados: 5 (admin-login.spec.ts + admin-tenants-crud.spec.ts + admin-users-crud.spec.ts + admin-clinics-extension.spec.ts + admin-hipaa-dual-filter.spec.ts) + 1 legacy (tenants-users.spec.ts del story anterior)
- Tests run: 27
- Passed: 12 (login flow + logout + phantom-tables-zero + UI element visibility checks)
- Failed: 11 (todos por backend `/api/v1/vitalia/admin/db-state` HTTP 500 — root cause GAP-1)
- Skipped: 4 (logout scenarios condicionales)
- Trace: `vitalia/frontend/playwright-report/` + `vitalia/frontend/test-results/`

**Nota ADVISORY:** GAP-1 (pre-existing infra incompleteness en `vitalia/.env.dev`) bloquea endpoint `/db-state` que necesita Settings completo. Recommended follow-up story: `vitalia-env-dev-settings-completeness`.

## § 3 — Capabilities updated/created

- `vitalia/docs/product/capabilities/iam/luana-core-adoption.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/admin/tenants-crud.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/admin/users-crud.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/admin/clinics-crud.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/admin/admin-streamlit-service.yaml` — NEW (status: live, port 8502)
- `vitalia/docs/product/capabilities/clinics/clinics-brand-extension.yaml` — NEW (status: live, FK tenants engine)
- `vitalia/docs/product/capabilities/clinics/hipaa-dual-filter-decorator.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/audit/audit-writer-ssot.yaml` — NEW (status: live, sync-write helper)

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/iam.md` — NEW (engine adoption + repos consumed)
- `vitalia/docs/product/modules/admin.md` — UPDATE (auto-list incluye tenants-crud + users-crud + clinics-crud + admin-streamlit-service)
- `vitalia/docs/product/modules/clinics.md` — NEW (brand-extension module + HIPAA dual filter)
- `vitalia/docs/product/modules/audit.md` — UPDATE o NEW (audit_writer SSoT helper)

## § 5 — How to verify (reproducible commands)

```bash
# Setup (asumiendo stack vitalia + admin corriendo):
WS=$(git rev-parse --show-toplevel)
docker compose -f docker-compose.dev.yml -f vitalia/docker-compose.dev.yml --profile admin up -d
sleep 8
curl -sS http://127.0.0.1:8002/health     # Expected: {"status":"ok",...}
curl -sS http://127.0.0.1:8502/_stcore/health  # Expected: "ok"

# 1. Backend unit + integration tests
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/{admin,clinics,audit}/ -v --override-ini="addopts="

# 2. Architecture fitness (incluye 4 NEW tests)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/test_admin_consumes_engine_repos.py tests/architecture/test_admin_no_raw_sql.py tests/architecture/test_clinics_domain_no_engine_imports.py tests/architecture/test_phantom_tables_zero_refs.py -v

# 3. Lint + format
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/ruff check src/modules/vitalia/{admin,clinics,audit}/ tests/
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/ruff format --check src/modules/vitalia/{admin,clinics,audit}/ tests/

# 4. Migrations verify (DB at head)
docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && uv run alembic current"
# Expected: 023_vitalia (head)
docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev -c "\dt" | grep -E "users|tenants|user_tenants|vitalia_clinic_branches"
# Expected: 4 rows (engine: users, tenants, user_tenants + brand-ext: vitalia_clinic_branches)

# 5. Phantom code verify (SC-13)
grep -rn "vitalia_user_profiles" ${WS}/vitalia/backend/src/modules/vitalia/admin/ | wc -l   # Expected: 0
grep -rnE "session\.execute\([^)]*(SELECT|INSERT|UPDATE|DELETE)" ${WS}/vitalia/backend/src/modules/vitalia/admin/modules/tenants.py ${WS}/vitalia/backend/src/modules/vitalia/admin/modules/users.py | wc -l   # Expected: 0

# 6. Engine boundary verify
git diff origin/main..HEAD --name-only | grep -E '^core/luana-core-[^/]+/src/' | wc -l   # Expected: 0
git diff origin/main..HEAD --name-only | grep -E '^(nicolify|comunify|lupulo)/' | wc -l   # Expected: 0

# 7. Playwright admin-smoke (post GAP-1 follow-up story para coverage completo)
cd ${WS}/vitalia/frontend && E2E_ADMIN_BASE_URL=http://127.0.0.1:8502 VITALIA_ADMIN_PASSWORD='<from .env.dev>' npx playwright test --project=admin-smoke --reporter=line
# Expected actual: 12 PASS, 11 FAIL (GAP-1), 4 SKIP. Post GAP-1 fix: ≥24/27 PASS.
```

**Expected actual:** commands 1-6 retornan exit code 0. Command 7 retorna parcial (12/27 PASS) hasta GAP-1 resuelto en follow-up story.
