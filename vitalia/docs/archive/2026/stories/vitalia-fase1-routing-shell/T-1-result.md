# T-1 Result — BE wiring: mount auth_router + delete vitalia local /me stub

**Story:** vitalia-fase1-routing-shell (F1-S9)
**Ticket:** T-1
**Brand:** vitalia
**State:** tests-passing (awaiting gate-runner + auditor-backend)
**Date:** 2026-05-25

## Diff Summary

### Files MODIFIED

**`vitalia/backend/src/main.py`** (+6 lines / -2 lines net):
```python
# REMOVED (Slice 1 legacy):
- from src.modules.vitalia.iam.api.router import router as iam_router
- app.include_router(iam_router, prefix="/api/v1/iam")

# ADDED (F1-S9 core reuse, paridad nicolify:92+543):
+ from luana_core_iam.api.routers import auth_router as iam_users
+ app.include_router(
+     iam_users.router,
+     prefix="/api/v1/iam/users",
+     tags=["IAM - Users"],
+ )
```

### Files CREATED

**`vitalia/backend/tests/test_main_iam_routes_mounted.py`** (new, ~75 LOC):
- `test_core_me_tenants_route_registered` — asserts core endpoint mounted
- `test_vitalia_local_me_route_removed` — asserts legacy stub gone
- `test_core_me_tenants_requires_auth` — asserts auth enforced

### Files DELETED

- `vitalia/backend/src/modules/vitalia/iam/api/router.py` (Slice 1 vitalia-local `/me` stub — anti-duplication)
- `vitalia/backend/tests/modules/vitalia/iam/test_iam_api.py` (tests for deleted stub endpoint)

### Endpoints post-merge

| Method | Path | Source |
|---|---|---|
| GET | `/api/v1/iam/users/me` | core `luana_core_iam` auth_router |
| GET | `/api/v1/iam/users/me/tenants` | core `luana_core_iam` auth_router |
| ~~GET~~ | ~~`/api/v1/iam/me`~~ | ~~vitalia local stub (DELETED)~~ |

## Validator Output

| Validator ID | Command | Status | Output |
|---|---|---|---|
| `val-be-pytest-mount-test` | pytest tests/test_main_iam_routes_mounted.py -v | ✅ PASS | 3 passed |
| `val-be-ruff` | ruff check src/main.py tests/test_main_iam_routes_mounted.py | ✅ PASS | All checks passed |
| `val-be-ruff-format` | ruff format --check src/ tests/ | ✅ PASS | 821 files already formatted |
| `val-be-arch-tests` | pytest tests/architecture/ -x -q | ✅ PASS | 270 passed, 2 warnings |
| `arch-be-response-model` | pytest tests/architecture/test_response_model_required.py | ✅ PASS | 3 passed |
| iam module remaining tests | pytest tests/modules/vitalia/iam/ -v | ✅ PASS | 35 passed |

Migration: N/A (no schema change).

Arch fitness: 270/270 PASS (unchanged, no allowlist growth).

## Gherkin Coverage

| Scenario | Test | Status |
|---|---|---|
| SC-1 · BE endpoint `/api/v1/iam/users/me/tenants` disponible | `test_core_me_tenants_route_registered` | ✅ PASS |
| SC-1 · Auth enforced | `test_core_me_tenants_requires_auth` | ✅ PASS |
| AC-17 · vitalia legacy `/me` stub eliminated | `test_vitalia_local_me_route_removed` | ✅ PASS |

## Skills Consulted (must_load enforcement v4.1)

| Skill/Rule | Status | Key decision |
|---|---|---|
| `backend-expert` | ✅ invoked | Runtime quality checklist loaded; verified no anti-patterns introduced |
| `anti-duplication.md` | ✅ invoked (CRITICAL) | EXTEND core via mount; DELETE vitalia stub; no parallel layer |
| `tenant-isolation.md` | ✅ invoked | `/me/tenants` returns user's own tenants; core IAM enforces isolation |
| `backend-ddd.md` | ✅ invoked | Engine read-only; zero edit to `core/luana-core-iam/src/` |
| `tdd-mandatory.md` | ✅ invoked | RED tests created first; 1 test failed RED; GREEN after changes |
| `hipaa-lite.md` | ✅ invoked | `/me/tenants` = no PHI; dual-filter exempt; no audit log row needed |
| `tessl__fastapi` | ✅ invoked | Router mount patterns; response_model via core router signatures |

## Commit SHA

`8561f196` (pushed to `wip/vitalia`)

## Acceptance Notes

- Anti-duplication enforcement: REUSE `core/luana-core-iam` auth_router (paridad nicolify:543 verbatim) — no new vitalia-local endpoint created.
- Engine boundary: zero edits to `core/luana-core-iam/src/` (read-only per `.claude/rules/backend-ddd.md`).
- FE consumers of legacy `/api/v1/iam/me` (DashboardWelcome.tsx + test + DashboardData.ts) will be deleted in T-5. Safe to delete BE stub now (T-1 is parallelizable with T-2, T-5 follows T-4).
- HIPAA-lite: `/me/tenants` exempt from dual-filter (returns identity + tenant list, no PHI).
- `redirect_slashes=False` confirmed unchanged in main.py line 41.
- `test_iam_api.py` deleted alongside router.py (it was the test for the deleted endpoint — keeping it would cause import errors on the deleted module).
