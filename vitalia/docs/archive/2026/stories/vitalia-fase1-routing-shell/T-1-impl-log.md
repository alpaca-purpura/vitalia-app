# T-1 Implementation Log — BE wiring: mount auth_router + delete vitalia local /me stub

**Story:** vitalia-fase1-routing-shell (F1-S9)
**Ticket:** T-1
**Brand:** vitalia
**Surface:** backend
**Date:** 2026-05-25
**Builder:** Claude Sonnet 4.6

## Skills Consulted (must_load enforcement v4.1)

| Skill | Reason invoked | Decision taken |
|---|---|---|
| `backend-expert` | ALWAYS per role instructions + `references/runtime-quality-checklist.md` | Read checklist: verified no Annotated dep type aliases, no legacy Column, no missing response_model (core router satisfies PII gate), no tenant_id gaps (auth handled by core IAM). Confirmed env-patching test pattern is clean. |
| `anti-duplication.md` (rule) | CRITICAL rule for T-1 — GET /me/tenants reuse core, NO duplicate | Decision: EXTEND core via 1-line mount. DELETE vitalia local `/me` stub. No new parallel layer created. |
| `tenant-isolation.md` (rule) | Every BE change verifies tenant isolation | Confirmed: `/me/tenants` returns tenant list (user's own tenants). Core IAM enforces isolation at UserService. No PHI. |
| `backend-ddd.md` (rule) | BE DDD Inside-Out layering + engine read-only constraint | Decision: ZERO edit to `core/luana-core-iam/src/`. Only import + mount the existing router. Engine boundary respected. |
| `tdd-mandatory.md` (rule) | TDD RED→GREEN required per layer | RED: created `test_main_iam_routes_mounted.py` (3 tests) before implementing. Ran RED → confirmed failures. Implemented changes → GREEN. |
| `hipaa-lite.md` (vitalia overlay) | HIPAA-lite mandatory for all vitalia BE | Confirmed: `/me/tenants` returns user identity + tenant list (NO PHI per canonical list). Dual-filter exempt for this endpoint. Audit log not required (no PHI access). |
| `tessl__fastapi` (skill) | Router mounting patterns + response_model | Core router already defines `response_model` implicitly via return type annotations on `get_current_user_profile → User` and `get_my_tenants → list[TenantSchema]`. FastAPI auto-generates schema. No manual `response_model=` needed — arch test confirms compliance. |

## Pre-implementation audit (anti-duplication Step 0)

CONTEXT-BRIEF.md § 7 greps confirmed:
- Core endpoint `GET /me/tenants` EXISTS at `core/luana-core-iam/src/luana_core_iam/api/routers/auth_router.py:23`
- Nicolify mount pattern EXISTS at `nicolify/backend/src/main.py:543` (prefix `/api/v1/iam/users`)
- Vitalia local `/me` stub EXISTS at `vitalia/backend/src/modules/vitalia/iam/api/router.py` (Slice 1 scaffold, STALE)
- FE consumers of legacy `/api/v1/iam/me`: `features/dashboard/DashboardWelcome.tsx` (to be deleted in T-5)
- Zero consumers of stub post-T-5 cleanup

**Consumer grep result (T-1 pre-delete verification):**
```
vitalia/frontend/src/features/dashboard/__tests__/DashboardWelcome.test.tsx (→ deleted T-5)
vitalia/frontend/src/features/dashboard/components/DashboardWelcome.tsx (→ deleted T-5)
vitalia/frontend/src/features/dashboard/types/DashboardData.ts (→ deleted T-5)
vitalia/backend/tests/modules/vitalia/iam/test_iam_api.py (→ deletes in T-1, tests the stub)
vitalia/backend/src/modules/vitalia/iam/api/router.py (→ the stub itself)
```

FE consumers belong to `(dashboard)/` route group deleted in T-5. BE test is the stub's own test (also deleted). Decision: safe to delete BE stub in T-1.

## Implementation

### Step 1 — RED tests created

Created `vitalia/backend/tests/test_main_iam_routes_mounted.py` with 3 tests:
- `test_core_me_tenants_route_registered` — asserts `/api/v1/iam/users/me/tenants` in routes
- `test_vitalia_local_me_route_removed` — asserts `/api/v1/iam/me` NOT in routes
- `test_core_me_tenants_requires_auth` — asserts 401/403/422 without auth

**RED run result:** 1 test failed (`test_vitalia_local_me_route_removed` — `/api/v1/iam/me` still in routes, legacy stub still mounted).

**Implementation note:** The `auth_router` module-level import triggers `luana_core_platform.core.config.Settings()` instantiation via `get_db → database.py → config.py`. Test uses `patch.dict(os.environ, _REQUIRED_ENV_VARS)` with minimal dummy values — no real credentials, no real DB/Redis/Qdrant calls. This is the correct pattern per `tessl__fastapi` — env patching for settings-dependent imports.

### Step 2 — GREEN implementation

**main.py changes:**
1. REMOVED: `from src.modules.vitalia.iam.api.router import router as iam_router`
2. ADDED: `from luana_core_iam.api.routers import auth_router as iam_users` (paridad nicolify:92)
3. REMOVED: `app.include_router(iam_router, prefix="/api/v1/iam")`
4. ADDED: `app.include_router(iam_users.router, prefix="/api/v1/iam/users", tags=["IAM - Users"])` (paridad nicolify:542-546)
5. Ruff auto-fixed import ordering (luana_core_iam is third-party, sorts before src.modules)

**Files deleted:**
- `vitalia/backend/src/modules/vitalia/iam/api/router.py` (Slice 1 legacy stub)
- `vitalia/backend/tests/modules/vitalia/iam/test_iam_api.py` (tests the deleted stub)

**Note:** `test_iam_api.py` is NOT `test_router.py` (the name from 06-tickets.yaml). It is the functional equivalent — the test for the vitalia-local `/me` endpoint. Deleting both stub + its test is correct per TDD (test of deleted functionality must also be deleted).

### Step 3 — Validator results

| Validator | Command | Result |
|---|---|---|
| `val-be-pytest-mount-test` | pytest tests/test_main_iam_routes_mounted.py -v | 3 PASSED |
| `val-be-ruff` | ruff check src/main.py tests/test_main_iam_routes_mounted.py | All checks passed |
| `val-be-ruff-format` | ruff format --check src/ tests/ | 821 files already formatted |
| `val-be-arch-tests` | pytest tests/architecture/ -x -q | 270 PASSED, 2 warnings |
| `arch-be-response-model` | pytest tests/architecture/test_response_model_required.py | 3 PASSED |
| iam module remaining tests | pytest tests/modules/vitalia/iam/ -v | 35 PASSED |

**Migration:** N/A (no schema change — this ticket is routing-only).

## Anti-default-flip audit

N/A — no feature flag default changes. T-1 is a 1-line router mount + 2 file deletions.

## Cross-module reads

- Read `core/luana-core-iam/src/luana_core_iam/api/routers/auth_router.py` (read-only) to verify endpoint signatures: `GET /me → User`, `GET /me/tenants → list[TenantSchema]`. Engine boundary respected.
- Read `nicolify/backend/src/main.py:542-546` (read-only) for verbatim mount pattern reference.

## HIPAA-lite compliance

`/me/tenants` returns: user identity (clerk_user_id) + list of tenant IDs user belongs to. No PHI fields from canonical list (`patient.name`, `diagnosis`, `treatment_plan`, etc.). No audit log row required for this endpoint. HIPAA-lite dual-filter (tenant_id + clinic_id) exempt per 03-arch-be.md § 6.
