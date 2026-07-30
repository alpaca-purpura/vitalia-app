# T-4 IMPL-LOG — Admin Streamlit Vitalia + 3 Integration Tests

**Brand:** vitalia  
**Ticket:** T-4 (BE — Admin Streamlit Vitalia + 3 integration tests)  
**Date:** 2026-05-18  
**Branch:** wip/vitalia

---

## § Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `backend-expert` | ALWAYS (runtime-quality-checklist, FastAPI/SQLA anti-patterns, TDD mandatory) | Runtime checklist loaded: response_model= mandatory, tenant_id every query, soft deletes only, AsyncSession, structlog not print. No legacy Column(), no datetime.utcnow(), no from_orm(). |
| `tessl__fastapi` | ALWAYS (Annotated deps, response_model, async lifespan) | Admin Streamlit does NOT use FastAPI routes — is a separate application-layer entry point. FastAPI patterns apply only to integration test fixtures (httpx AsyncClient). |
| `tessl__pytest-api-testing` | ALWAYS (httpx AsyncClient, fixture scoping, factory fixtures) | Integration tests use httpx.AsyncClient with ASGITransport against FastAPI app for webhook endpoints. pytest.mark.integration for Postgres-required tests. |
| `tessl__graceful-degradation` | Admin modules call Clerk SDK directly (external HTTP) | Clerk SDK calls wrapped with try/except + structlog fallback. Admin modules never let Clerk failure propagate unhandled. |

**Step 0.5 default-flip detection:** No config.py flag changes in T-4 scope. SKIP.

## § Scope Verification

PR touches business modules only:
- `vitalia/backend/src/modules/vitalia/admin/` (NEW — admin application-layer)
- `vitalia/backend/src/modules/vitalia/compliance/` (NEW `audit.py` — admin log_admin_action helper)
- `vitalia/backend/tests/admin/` (NEW — contract tests)
- `vitalia/backend/tests/integration/admin/` (NEW — integration tests)
- `vitalia/backend/pyproject.toml` (EDIT — add deps)

No copilot/sales_agent edits. No core/luana-core-* edits. No other brand edits.

## § Cross-module reads (read-only references)

- `nicolify/backend/src/modules/nicolify/admin/app.py` — PageSpec pattern reference
- `nicolify/backend/src/modules/nicolify/admin/modules/tenants.py` — structure reference (rewrite for vitalia)
- `nicolify/backend/src/modules/nicolify/admin/modules/users.py` — structure reference (rewrite for vitalia)
- `vitalia/backend/src/modules/vitalia/infrastructure/adapters/clerk_webhook_adapter.py` — HMAC verify adapter (existing)
- `vitalia/backend/src/modules/vitalia/api/webhook_routes.py` — existing webhook route (stub noted)
- `vitalia/backend/alembic/versions/013_vitalia_audit_log.py` — audit_log table schema
- `vitalia/backend/src/modules/vitalia/compliance/application/compliance_service_adapter.py` — sanitize_phi_payload

## § Key Decisions

**D1:** `compliance/audit.py` (log_admin_action) does NOT exist from Story 11 — creating it as part of T-4. It wraps raw SQL INSERT into `vitalia_audit_log` via AsyncSession. This is a helper, NOT a DDD entity (admin is a special application-layer surface per admin-panel.md).

**D2:** Integration test `test_clerk_webhook_integration.py` (SC-05) tests the existing webhook route `POST /api/v1/vitalia/webhooks/clerk` via httpx.AsyncClient + ASGITransport. The test does NOT require Postgres (tests HMAC + response code). The route returns HTTP 400 on HMAC failure (per design comment in webhook_routes.py), NOT 401. Tests align with actual behavior.

**D3:** SC-08 (admin creates tenant) and SC-13 (audit_log compliance) are tested via `test_audit_log_verify.py` and `test_cross_tenant_isolation.py` using direct admin module calls with pytest.mark.integration (Postgres-required).

**D4:** Admin modules use SYNCHRONOUS `psycopg2` session (via `SessionLocal` from `luana_core_platform.core.database`) for Streamlit compatibility (Streamlit is synchronous). The async session is for integration tests only.

**D5:** UUIDv5 namespace for deterministic tenant IDs: `uuid.NAMESPACE_DNS` + `f"{slug}.vitalia.com"`.

**D6:** `vitalia/backend/src/modules/vitalia/compliance/audit.py` is a separate file (not modifying existing compliance files) to avoid scope creep.

## § Default-flip detection

Not applicable — no flag changes in T-4.

## § Anti-duplication check

Checked: no existing `admin/` directory in vitalia/backend. Checked: nicolify/admin/modules/ exists but vitalia implementation must differ ≥50 lines (unique: UUIDv5, clinics table, locations table, HIPAA audit_log with clinic_id, Clerk SDK direct, BYTEA payload_redacted, dual filter tenant+clinic).

## § Files Created

### NEW (Production)
1. `vitalia/backend/src/modules/vitalia/compliance/audit.py` — log_admin_action() helper
2. `vitalia/backend/src/modules/vitalia/admin/__init__.py`
3. `vitalia/backend/src/modules/vitalia/admin/app.py`
4. `vitalia/backend/src/modules/vitalia/admin/pages/__init__.py`
5. `vitalia/backend/src/modules/vitalia/admin/pages/tenants.py`
6. `vitalia/backend/src/modules/vitalia/admin/pages/usuarios.py`
7. `vitalia/backend/src/modules/vitalia/admin/modules/__init__.py`
8. `vitalia/backend/src/modules/vitalia/admin/modules/tenants.py`
9. `vitalia/backend/src/modules/vitalia/admin/modules/users.py`
10. `vitalia/backend/src/modules/vitalia/admin/_shared/__init__.py`
11. `vitalia/backend/src/modules/vitalia/admin/_shared/auth.py`
12. `vitalia/backend/src/modules/vitalia/admin/_shared/db.py`

### NEW (Tests)
13. `vitalia/backend/tests/admin/__init__.py`
14. `vitalia/backend/tests/admin/test_admin_contract.py`
15. `vitalia/backend/tests/integration/admin/__init__.py`
16. `vitalia/backend/tests/integration/admin/conftest.py`
17. `vitalia/backend/tests/integration/admin/test_clerk_webhook_integration.py`
18. `vitalia/backend/tests/integration/admin/test_audit_log_verify.py`
19. `vitalia/backend/tests/integration/admin/test_cross_tenant_isolation.py`

### EDIT
20. `vitalia/backend/pyproject.toml` — add streamlit, passlib[bcrypt] deps

## § HIPAA-lite invariants enforced

- `log_admin_action()` sync write BEFORE returning from admin actions
- `payload_redacted`: identity fields OK (clinic_name, country, email), NO PHI fields (no diagnosis, treatment_plan, medication, etc.)
- `sanitize_phi_payload()` called before any log write
- Dual filter `tenant_id + clinic_id` on all queries (admin is super-admin but enforces per-clinic scope)
- Admin auth via `bcrypt.checkpw` vs `VITALIA_ADMIN_PASSWORD_HASH` env-var
