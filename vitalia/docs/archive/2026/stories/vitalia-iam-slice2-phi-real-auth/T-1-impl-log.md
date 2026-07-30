# T-1 Implementation Log — BE-auth core (decoder JWKS real + rol desde DB)

story: vitalia-iam-slice2-phi-real-auth
ticket: T-1
builder: builder-backend (Sonnet 4.6)
date: 2026-05-29
state: IN_PROGRESS

---

## Skills Consulted (must_load enforcement v4.1)

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | IAM auth wiring, Inside-Out DDD, SQLA 2.0 async, runtime-quality-checklist | Use `verify_token_payload` engine import; query async brand-local with UserTenantModel; structlog only |
| `tessl__fastapi` | Annotated deps, response_model, async patterns | `ClinicResolver.resolve()` stays sync (stub path); add `async_resolve()` for DB path; DI pattern per endpoint |
| `tessl__pytest-api-testing` | httpx AsyncClient, monkeypatch fixtures, DB isolation | Use `monkeypatch.setattr` on `verify_token_payload`; integration tests marked `@pytest.mark.integration` |
| `.claude/rules/tenant-isolation.md` | Every query must filter tenant_id | UserTenantModel query filters `(user_id, tenant_id, is_active)` |
| `.claude/rules/backend-ddd.md` | Inside-Out layering, no cross-module imports | Decoder in infrastructure; resolver in application; no business logic in api |
| `.claude/rules/anti-duplication.md` | Never recreate PyJWKClient | IMPORT `verify_token_payload` from engine; zero mirror |
| `.claude/rules/tdd-mandatory.md` | RED tests before GREEN code per layer | First entry = RED test written before implementation |
| `.claude/rules/test-design-doctrine.md` | Test design matrix for BE-auth nature | Unit per layer + integration SC-1/SC-4 + arch stub-env-gate |
| `vitalia/.claude/rules/hipaa-lite.md` | Dual filter tenant+clinic, audit sync, sanitization | JWT decode errors return 401 without data leak; rol from DB enforced |

---

## Plan (technical design)

### Layer 1 — Infrastructure: `clerk_jwt_decoder.py`

**Changes:**
- Import `verify_token_payload` from `luana_core_iam.application.auth` (engine JWKS).
- `decode()` logic: if `VITALIA_AUTH_STUB==1` AND `token.startswith("stub:")` → `_decode_stub()` (unchanged). Else → `verify_token_payload(token)` and map `payload["sub"]` to `ClerkJwtPayload.user_id`.
- `verify_token_payload` raises `HTTPException(401)` on invalid token — catch and re-raise as `JwtDecodeError` (keeps the interface contract for callers).
- `ClerkJwtPayload.role` field kept for shape compat but its value from token is **not authoritative** post-Slice-2 (resolver overwrites with DB role).
- `ClerkJwtPayload.tenant_id` and `clinic_id` are NOT in a real JWT — set empty strings `""` from real tokens (the resolver reads these from headers, not the payload).

**Shape mapping from real Clerk JWT payload:**
```
payload["sub"]   → user_id
payload.get("email", "") → email
payload.get("name", payload.get("full_name", "")) → name
tenant_id = ""   (from header, not JWT)
clinic_id = ""   (from header, not JWT)
role = ""        (from DB, not JWT)
```

### Layer 2 — Application: `clinic_resolver.py`

**Changes:**
- Add `async_resolve()` method: takes `token + session + tenant_id + clinic_id`.
  1. Calls `self._decoder.decode(token)` → get `user_id` (Clerk sub string).
  2. Query `UserModel.clerk_id == user_id` → get `users.id` UUID.
  3. Query `UserTenantModel.role` where `(user_id=uuid, tenant_id=tenant_uuid, is_active=True)`.
  4. Build `ClinicContext` with rol from DB.
- Keep `resolve()` sync method intact for backward compat (callers not yet migrated in T-1 scope).
- `ClinicContext` fields unchanged.

### Cross-ticket contract (for T-2)

**T-2 consumers** (crm/router.py, crm/consent_endpoints.py, marketing/deps.py, marketing/routes.py, inbox/router.py) call `resolver.resolve(token)` synchronously. After T-1:
- `resolve()` still works for the stub path (backward compat during T-2 migration window).
- `async_resolve(token, session, tenant_id_str, clinic_id_str)` is the new async method with DB role resolution.
- T-2 MUST migrate callers to `await resolver.async_resolve(...)` passing the session from `Depends(get_async_session)`.
- The `_get_resolver()` / `_build_resolver()` factory functions in consumers remain as-is for T-2 to update.

### Tests

- **RED first entry:** `test_clerk_jwt_decoder.py` (new tests for JWKS path) — written before implementation.
- **Arch test:** `test_auth_stub_env_gate.py` — asserts runtime config doesn't contain `VITALIA_AUTH_STUB`.
- **Integration:** `test_phi_real_auth.py` SC-1 + SC-4 — uses `monkeypatch.setattr` on `verify_token_payload`.

---

## Iteration Log

### [RED] 2026-05-29 — Unit tests written before implementation

Writing tests first (TDD RED phase):
1. `tests/modules/vitalia/iam/test_clerk_jwt_decoder.py` — new tests for JWKS vs stub gate
2. `tests/architecture/test_auth_stub_env_gate.py` — NEW arch test
3. `tests/integration/test_phi_real_auth.py` — NEW integration tests SC-1 + SC-4

Tests will be RED until implementation is complete.

### [GREEN] 2026-05-29 — Implementation

Modified files:
1. `vitalia/backend/src/modules/vitalia/iam/infrastructure/clerk_jwt_decoder.py`
2. `vitalia/backend/src/modules/vitalia/iam/application/services/clinic_resolver.py`

New files:
1. `vitalia/backend/tests/architecture/test_auth_stub_env_gate.py`
2. `vitalia/backend/tests/integration/test_phi_real_auth.py`

---

## Gate Results

(populated after pytest run)

---

## Cross-ticket contract § T-2

**T-2 (repos-wire) must update these callers when migrating to `async_resolve()`:**

| File | Current call | Must migrate to |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/crm/api/router.py` | `resolver.resolve(token)` | `await resolver.async_resolve(token, session, tenant_id, clinic_id)` |
| `vitalia/backend/src/modules/vitalia/crm/api/consent_endpoints.py` | `resolver.resolve(token)` | idem |
| `vitalia/backend/src/modules/vitalia/marketing/api/deps.py` | `resolver.resolve(token)` | idem |
| `vitalia/backend/src/modules/vitalia/marketing/api/routes.py` | `resolver.resolve(token)` | idem |
| `vitalia/backend/src/modules/vitalia/inbox/api/router.py` | `resolver.resolve(token)` | idem |

`get_async_session` must be added as `Depends` parameter in each endpoint that uses `async_resolve()`.

The sync `resolve()` method remains available for any remaining test fixtures using the stub decoder pattern — it will continue to work for stub tokens (when `VITALIA_AUTH_STUB=1`).
