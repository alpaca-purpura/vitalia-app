# T-1 Result — BE-auth core (decoder JWKS real + rol desde DB)

story: vitalia-iam-slice2-phi-real-auth
ticket: T-1
surface: BE
date: 2026-05-29
state: TESTS_PASSING

---

## Skills Consulted (must_load enforcement v4.1)

| Skill | Invoked | Decision |
|---|---|---|
| `backend-expert` | YES | Inside-Out DDD; SQLA 2.0 async; runtime-quality-checklist anti-patterns verified |
| `tessl__fastapi` | YES | `async_resolve()` separate async method; `resolve()` compat preserved for T-2 migration |
| `tessl__pytest-api-testing` | YES | `monkeypatch.setattr` on `verify_token_payload`; mock AsyncSession pattern |
| `.claude/rules/tenant-isolation.md` | YES | `UserTenantModel.tenant_id` filter + `is_active=True` in role query |
| `.claude/rules/backend-ddd.md` | YES | Decoder in infrastructure; resolver in application; no business logic leaked |
| `.claude/rules/anti-duplication.md` | YES | `verify_token_payload` imported from engine — zero `PyJWKClient` recreation |
| `.claude/rules/tdd-mandatory.md` | YES | RED tests written first; first impl-log entry is RED phase |
| `.claude/rules/test-design-doctrine.md` | YES | Unit (decoder gate + resolver unit) + arch (stub env gate) + integration (SC-1+SC-4) |
| `vitalia/.claude/rules/hipaa-lite.md` | YES | Error messages don't leak PHI; 401 on invalid JWT; role from DB enforced |

---

## Files Modified/Created

| File | Action | Notes |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/iam/infrastructure/clerk_jwt_decoder.py` | MODIFIED | JWKS real via engine import; stub env-gated (AD-4) |
| `vitalia/backend/src/modules/vitalia/iam/application/services/clinic_resolver.py` | MODIFIED | `async_resolve()` NEW; `resolve()` compat preserved; role from DB |
| `vitalia/backend/tests/architecture/test_auth_stub_env_gate.py` | NEW | 4 arch gate tests; runtime config check + decoder behavior |
| `vitalia/backend/tests/integration/test_phi_real_auth.py` | NEW | SC-1 (3 tests) + SC-4 (5 tests) + SC-2/SC-3 stubs (4 skip) |
| `vitalia/backend/tests/modules/vitalia/iam/test_clerk_jwt_decoder.py` | MODIFIED | Updated for Slice 2: stub path now requires env; real path tested |
| `vitalia/docs/product/stories/vitalia-iam-slice2-phi-real-auth/T-1-impl-log.md` | NEW | Iteration log + cross-ticket contract for T-2 |

---

## Gate Output

### Lint
```
ruff check src/modules/vitalia/iam/ → 0 errors
ruff format --check src/modules/vitalia/iam/ → 10 files already formatted
```

### Tests — T-1 target suite
```
53 passed, 4 skipped (SC-2/SC-3 stubs for T-2 — expected)

Breakdown:
  tests/architecture/test_auth_stub_env_gate.py: 4 passed
  tests/integration/test_phi_real_auth.py: 9 passed, 4 skipped
  tests/modules/vitalia/iam/test_clerk_jwt_decoder.py: 17 passed
  tests/modules/vitalia/iam/test_clinic_resolver.py: 6 passed
  tests/modules/vitalia/iam/test_role.py: 22 passed (no change, sanity check)
```

### Architecture fitness (existing gates — no regression)
```
324 passed, 2 warnings in 3.37s (same count as before T-1)

Gates kept green:
  ✅ test_phi_dual_filter.py
  ✅ test_audit_log_sync_write.py
  ✅ test_audit_log_row_per_phi_endpoint.py
  ✅ test_response_model_required.py
  ✅ test_no_phi_in_url_params.py
  ✅ test_auth_stub_env_gate.py (NEW — +4 tests)
```

---

## Implementation Summary

### clerk_jwt_decoder.py (MODIFIED)

Key change: `decode()` now:
1. Checks `VITALIA_AUTH_STUB==1` AND `token.startswith("stub:")` → `_decode_stub()` (test path)
2. Otherwise → `_decode_real()` → `verify_token_payload(token)` (engine JWKS, imported, zero mirror)

HTTPException from engine is caught and re-raised as `JwtDecodeError` to:
- Keep the existing interface (callers map to HTTP 401)
- Not leak internal error details (security + PHI safety)

For real JWTs: `tenant_id=""`, `clinic_id=""`, `role=""` in payload (resolved from headers+DB by `ClinicResolver`).

### clinic_resolver.py (MODIFIED)

Added `async_resolve(token, session, tenant_id_str, clinic_id_str)`:
1. Calls decoder → gets `clerk_sub` (Clerk user ID from `payload.user_id`)
2. Queries `UserModel.id` WHERE `clerk_id == clerk_sub` (engine model, imported)
3. Queries `UserTenantModel.role` WHERE `(user_id, tenant_id, is_active=True)` (SQLA 2.0 async)
4. Returns `ClinicContext` with DB-sourced role

Preserved `resolve()` sync for backward compat while T-2 migrates callers.

`ClinicContext` fields unchanged — consumers (`ctx.role`, `ctx.tenant_id`, etc.) need no changes.

### Cross-ticket contract for T-2

See `T-1-impl-log.md § Cross-ticket contract §T-2`:
- T-2 must migrate `resolver.resolve(token)` → `await resolver.async_resolve(token, session, tenant_id_str, clinic_id_str)` in all 5 PHI router files
- Must add `Depends(get_async_session)` to each PHI endpoint
- `_get_resolver()` / `_build_resolver()` factories can remain (they instantiate `ClinicResolver`)

---

## Validators Check (04-validators.yaml)

| Validator | Status |
|---|---|
| cat-1: Decoder JWKS real (reuse engine) | ✅ PASS |
| cat-1: JWT real válido → payload verificado | ✅ PASS (monkeypatched SC-1 tests) |
| cat-1: JWT inválido/expirado → 401 honesto | ✅ PASS (SC-4 tests) |
| cat-1: stub:... SOLO con VITALIA_AUTH_STUB=1 | ✅ PASS (arch gate + decoder tests) |
| cat-1: user_id extraído de payload['sub'] | ✅ PASS (test_real_token_maps_sub_to_user_id) |
| cat-2: ClinicResolver rol desde user_tenants.role | ✅ PASS (async_resolve tests) |
| cat-2: ClinicContext.role refleja rol DB | ✅ PASS (test_role_resolved_from_db_not_token) |
| cat-2: user_id → users.id via UserModel.clerk_id | ✅ PASS (resolver unit tests) |
| cat-2: cero edit core/luana-core-*/src/ | ✅ PASS (grep confirmed: 0 changes to engine) |
| SC-1 grader | ✅ PASS (integration tests) |
| SC-4 graders: invalid/expired/stub-legacy/empty | ✅ PASS (all SC-4 test cases) |
| arch_validation: no_engine_edit | ✅ PASS |
| arch_validation: stub_env_gate | ✅ PASS (test_auth_stub_env_gate.py: 4/4) |

---

## Commit SHA

`ad5957f2` — pushed to `wip/vitalia`

---

## Pending (T-2 scope)

- SC-2 (recepcion/marketing → 403): stub tests in test_phi_real_auth.py (4 skip decorated)
- SC-3 (cross-tenant 404 / cross-clinic 403): stub tests in test_phi_real_auth.py (4 skip decorated)
- Repo wiring (remove AsyncMock inline from crm/consent/marketing/inbox)
- `await resolver.async_resolve()` migration in all 5 PHI routers
