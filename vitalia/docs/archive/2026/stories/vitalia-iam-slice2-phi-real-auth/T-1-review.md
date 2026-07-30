<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Backend Code Review: Slice 2 PHI — decoder JWKS real + rol desde DB + repos reales

**Date:** 2026-05-30
**Story / folder:** `vitalia/docs/product/stories/vitalia-iam-slice2-phi-real-auth/`
**Tickets covered:** T-1 (decoder JWKS + rol DB) + T-2 (repos PHI reales DI + SC-2/SC-3). T-3 is FE → out of scope (auditor-frontend).
**Brand:** vitalia
**Files Reviewed:** 7 BE (iam decoder + resolver; crm router + consent; marketing deps + routes; inbox router)
**Domains touched:** iam (auth core), crm (+consent), marketing, inbox
**Skills consulted:** backend-expert, tessl__fastapi, tessl__pytest-api-testing, hipaa-lite (overlay), tenant-isolation, backend-ddd, anti-duplication
**Verdict:** **APPROVED**

## /test-backend Gate Status (consumed gate-output.json, any_fail=false)

| Gate | Result | Detail |
|---|---|---|
| pytest integration + modules | PASS | 53 tests (test_phi_real_auth.py SC-1..SC-4 + test_auth_stub_env_gate + inbox routers); 49 deterministic + 7 random seeds, no flakiness |
| ruff check (iam/crm/marketing/inbox) | PASS | 0 errors |
| ruff format --check | PASS | 105 files already formatted |
| arch-fitness | PASS | 277 (gate-output) / 324 (T-2 impl-log) incl. test_phi_dual_filter, test_audit_log_sync_write, test_audit_log_row_per_phi_endpoint, test_response_model_required, test_no_phi_in_url_params, test_auth_stub_env_gate |

Gates 3-7/11-13 (the ones that don't depend on Postgres) GREEN. No auto-FAIL trigger.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation | PASS | 0 |
| 3 | Soft Deletes | PASS (N/A — no deletes) | 0 |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | PASS | 0 |
| 6 | Async Consistency | PASS | 0 |
| 7 | Pydantic v2 / PII | PASS | 0 |
| 8 | Migration Quality | PASS (N/A — no DDL) | 0 |
| 9 | Security (auth/JWKS) | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 |
| 11 | Cross-cutting (HIPAA-lite) | PASS | 0 |
| 12 | Mirror detection | PASS | 0 |
| 13 | Connectivity (anti-isla) | PASS | 0 |

## Cross-scope flags

| Surface | Action |
|---|---|
| `core/luana-core-*/src/` | NONE in diff — engine consumed via import only (clean) |
| `{other_brand}/...` | NONE — cross-brand mirror scan empty |
| `copilot`/`sales_agent` | NONE in diff |
| `vitalia/frontend/.../useCurrentUser.ts` (T-3) | FE — deferred to auditor-frontend (NOT scored here) |

## Findings

### PASS — ENGINE BOUNDARY (HARD gate)
`git diff --name-only HEAD~5..HEAD` includes ZERO `core/luana-core-*/src/` files. Engine is consumed via import only:
- `from luana_core_iam.application.auth import verify_token_payload` (decoder, JWKS reuse — NO PyJWKClient recreation)
- `from luana_core_iam.infrastructure.models.user_tenant_model import UserTenantModel` + `user_model.UserModel` (role query, no table/mirror)
No engine edit → no /pm-luana escalation needed.

### PASS — cat-1 Auth JWKS real (Security)
`clerk_jwt_decoder.py`: `decode()` delegates to `verify_token_payload` (engine JWKS, RS256). Stub path is fully env-gated: `if os.environ.get("VITALIA_AUTH_STUB")=="1" and token.startswith("stub:")` (line 91) — test-only. Runtime → JWKS real. HTTPException(401) from engine mapped to `JwtDecodeError("Token inválido o expirado.")` with NO internal detail leak (line 118-122, structlog warning only). `test_auth_stub_env_gate.py` enforces `.env.dev.template` + `docker-compose.dev.yml` never set the env, and decoder rejects `stub:` when env absent. 401 honesto, sin leak.

### PASS — cat-2 Rol desde DB (Tenant Isolation + DDD)
`clinic_resolver.async_resolve` resolves role from `user_tenants.role` via `_resolve_role` querying `(user_id, tenant_id, is_active=True)` (lines 199-204, SQLA 2.0 `select().where()` async). `sub`→UUID via `UserModel.clerk_id` (`_resolve_user_uuid`). Role NO longer from token (decoder sets `role=""` for real JWTs, line 131). `ClinicContext` dataclass fields unchanged → consumers reading `ctx.role` need zero change. DDD layering correct: decoder in infrastructure, resolver in application, no business logic in api.

### PASS — cat-3 Repos reales (no inline AsyncMock runtime)
`grep AsyncMock` in crm/marketing/inbox `api/` returns ZERO inline runtime mocks (only doc-comment references). All 4 consumers wired to `async_resolve` via `Depends(get_async_session)`:
- crm/router `_resolve_context_async` (line 120), crm/consent (line 97), marketing/deps `get_clinic_context_async` (line 77), inbox/router (line 305).
Repos instantiated real: PatientRepository, LeadRepository (crm); LucasRecommendationRepository et al. (marketing); MessageRepository, ConversationRepository et al. (inbox).

**OQ-1 outbox fallback (evaluated — ACCEPTABLE):** `inbox/api/router.py:130-142` retains a pre-existing import-guarded `_AsyncMock()` fallback for `luana_core_events.outbox.adapter_bus` (`except ImportError`). This is NOT a PHI repo, NOT the auth/resolve path; it's the offline-env fallback for the outbox event bus (runtime uses the real `adapter_bus`). It pre-dates T-2 (not introduced by this story) and is consistent with the engine-import-with-offline-guard pattern. Honest sub-scope follow-up (offline-bus cleanup), not a blocker for this auth story.

### PASS — cat-4 HIPAA-lite
- Dual filter tenant+clinic: enforced by `PhiRepositoryBase` (`get_by_id(*, tenant_id, clinic_id, user_id)`); arch `test_phi_dual_filter.py` GREEN.
- Audit sync write: `patient_repository.py` writes `AuditLogEntry` via `self._audit_repo.write(...)` on every patient access (lines 124/271/332/395); arch `test_audit_log_sync_write.py` + `test_audit_log_row_per_phi_endpoint.py` GREEN.
- `@require_phi_access(roles=_PHI_ROLES, ...)` at service layer (patient_service, patient_consent_service); `_PHI_ROLES = {doctor, nurse, admin_clinic}` gate at conversation endpoints (crm/router:618/661 → 403). `PHIAccessDeniedError`→403.
- Cross-tenant→404 / cross-clinic→403: covered by integration tests (test_cross_tenant_404_no_phi_leak, test_cross_clinic_403_no_phi_leak) with explicit no-PHI-leak body assertions.

### PASS — Non-PHI lead sync `resolve()` path (verified safe)
crm/router.py:153 `resolver.resolve(token)` (sync) remains for non-PHI **lead** endpoints (leads are tenant-scoped, not clinic-scoped; `lead_service.py:34` explicitly "No @require_phi_access — Lead data accessible to all roles"). The sync path still validates the token through `decoder.decode()` → `verify_token_payload` (JWKS real). It cannot reach PHI data (separate PHI endpoints use `_resolve_context_async`). Deliberate, documented, no leak risk.

## Cross-scope flags / Engine-edit / Cross-brand: 0 / 0 / 0

## Contract Compliance (business surface)

- [x] Decoder reuses engine JWKS (verify_token_payload import); no PyJWKClient recreation
- [x] Role from `user_tenants.role` DB; ClinicContext shape intact
- [x] Repos real DI via Depends(get_async_session); no inline AsyncMock runtime (outbox offline-guard excepted, documented OQ-1)
- [x] HIPAA-lite: dual filter + audit sync + @require_phi_access + cross-tenant 404 / cross-clinic 403
- [x] response_model= on every endpoint (arch test_response_model_required GREEN)
- [x] § 8 Agentic Surfaces: N/A (no copilot/sales_agent)
- [x] Test surfaces SC-1..SC-4 present (Phase D below)

## Downstream regression scope

| Surface modified | Downstream test targets | gate-runner status |
|---|---|---|
| `iam/{decoder,resolver}` + `{crm,marketing,inbox}/api/` | covered by full vitalia suite (integration + arch 277/324) | PASS — no `shared/` / engine surface touched → no extra spawn needed |

## Phase D — Scenario → test coverage

| Scenario | Test method(s) | Status |
|---|---|---|
| SC-1 happy (doctor JWT real ve PHI + rol DB) | test_doctor_jwt_real_sees_phi, test_decoder_calls_verify_token_payload_not_stub, test_role_resolved_from_db_not_token | PASS |
| SC-2 negative (recepcion/marketing → 403) | test_recepcion_403_on_get_patient, test_marketing_403_on_marketing_opt_in | PASS |
| SC-3 edge (cross-tenant 404 / cross-clinic 403) | test_cross_tenant_404_no_phi_leak, test_cross_clinic_403_no_phi_leak | PASS |
| SC-4 adversarial (invalid/expired/forged/legacy-stub → 401) | test_invalid_token_401, test_expired_token_401, test_legacy_stub_token_rejected_in_runtime_401, test_error_body_does_not_leak_phi_on_401 | PASS |
| Q2 stub env gate | test_env_dev_template_does_not_contain_auth_stub, test_docker_compose_dev_does_not_contain_auth_stub, test_decoder_rejects_stub_token_when_stub_env_absent, test_decoder_accepts_stub_token_only_when_stub_env_set | PASS |

## ★ Live verification (anti-teatro) assessment

`VERIFICATION-godmatrix-live.md`: orchestrator exercised the **real god-matrix** with a real Clerk JWT (minted via Clerk Backend API) against dev-app `:8002` — NOT monkeypatch:
- doctor JWT real → GET /crm/conversations **200** (JWKS verified + DB role granted)
- marketing JWT real → **403** (DB role denies, no leak)
- doctor + cross-tenant → **403** (no role in tenant)
- forged token → **401**; legacy `stub:...` → **401** (stub not accepted in runtime)
Logs read (no JWT/PHI/secret printed). This is genuine "ejercer la acción real + leer logs", not "saqué 200 = funciona". The story's central objective (PHI surfaces rejected real Clerk JWT → 401 with stub; now real JWT → correct RBAC) is **PROVEN LIVE**.

**2 pre-existing gaps (do NOT affect this story's verdict):**
1. `vitalia_patients` + `vitalia_leads` tables missing in dev DB → lead/patient endpoints 500 in dev. Pre-existing migration/seed gap, NOT caused by this auth story; documented in `vitalia/docs/observed-bugs/2026-05-30-vitalia-patients-leads-tables-missing-dev.md`. Audit-on-patient-access is proven by code + integration tests (assert audit write in patient path), live exercise blocked by this table gap. Legitimate follow-up (dev migration/seed) — out of scope for Slice 2 auth.

Scope assessment: ESTA story is **auth** (decoder/resolver + repos-wire). The auth behavior is fully verified (code + integration tests + live JWT). The missing-tables gap is downstream of auth and orthogonal; it does not invalidate the auth desentubado. Verdict stands.

## Connectivity (anti-isla CONN)

- **Consumed:** decoder real + async_resolve wired in crm(router+consent), marketing(deps+routes), inbox(router) DI. Real repos consumed by their endpoints.
- **Notarized:** routers already mounted in main.py (no new route); engine `/me` mounted. Wiring is internal DI.
- **Navigable:** FE sends real JWT + X-Tenant-ID + X-Clinic-ID → PHI endpoints reachable with DB-sourced role.
- **On-the-map:** cap_target `iam.iam-scaffold-slice-1` exists; cap_change_type extend. `03-arch.md § Integration design (CONN)` present with concrete reachability path.

## Allowlist Movement
- No allowlist grew. Replacing stub + inline AsyncMock with real wiring REMOVES debt (arch allowlists shrink-only honored).

## Native-First Audit
- No `docker exec ... ruff|pytest` in commits. No `git add .`/`-A`/`-u`. Commits scoped by path (per git log). PASS.

## Verdict Math
- No FAIL in cat 1/2/8/9/12. Engine boundary clean (0 core/src). Cross-brand mirror clean (0). All gates (3-7/11-13) GREEN. IMPL-LOG § Skills Consulted populated (baseline + hipaa-lite domain). 0 category WARNs.
- → **APPROVED**

## Suggested learning capture (advisory)
Pattern "engine sync repo doesn't fit async path → brand-local async query consuming the engine MODEL (not mirroring the table) = EXTEND not NEW" (AD-2) is a clean, reusable resolution of the sync/async impedance without engine edit. Candidate for `docs/learnings/` if it recurs.
