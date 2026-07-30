<!-- voseo-allowed: internal architect documentation -->
---
story_id: vitalia-fase1-routing-shell
brand: vitalia
surface: backend
type: ui-story
last_modified: 2026-05-26
parent_arch: 03-arch.md
---

# F1-S9 · `03-arch-be.md` — backend slice (BE-only)

See consolidated `03-arch.md` for full context. This file is the BE-scoped view used by `builder-backend` + `auditor-backend`.

## § 1 — Scope (BE)

Single deliverable: wire core `auth_router` into vitalia FastAPI app + delete vitalia legacy `/me` stub. Net diff: ~6 lines mounted + 1 file deleted + 1 test file deleted.

## § 2 — Files

| File | Action |
|---|---|
| `vitalia/backend/src/main.py` | MODIFY (add import + include_router; remove vitalia-local iam_router import + mount) |
| `vitalia/backend/src/modules/vitalia/iam/api/router.py` | DELETE |
| `vitalia/backend/tests/modules/vitalia/iam/test_router.py` (if exists) | DELETE |
| `vitalia/backend/tests/test_main_iam_routes_mounted.py` | NEW (RED first) |

## § 3 — Diff (verbatim)

```python
# vitalia/backend/src/main.py
# REMOVE imports (lines 25-26 era):
- from src.modules.vitalia.iam.api.router import router as iam_router

# ADD import (paridad nicolify/backend/src/main.py:92):
+ from luana_core_iam.api.routers import auth_router as iam_users

# REMOVE include_router (line 47 era):
- # T-infra-9: IAM + CRM modules (Slice 1 scaffold)
- app.include_router(iam_router, prefix="/api/v1/iam")

# ADD include_router (paridad nicolify:543):
+ # F1-S9: REUSE core IAM auth router (anti-duplication — deleted vitalia local /me stub).
+ app.include_router(
+     iam_users.router,
+     prefix="/api/v1/iam/users",
+     tags=["IAM - Users"],
+ )
```

## § 4 — Endpoints exposed post-merge

| Method | Path | Provided by | Used by |
|---|---|---|---|
| GET | `/api/v1/iam/users/me` | core `luana_core_iam` `auth_router::get_current_user_profile` | (F1-S9 not consumed by FE — available for future) |
| GET | `/api/v1/iam/users/me/tenants` | core `luana_core_iam` `auth_router::get_my_tenants` | F1-S9 FE `lib/iam/api.ts::fetchUserTenants` (server-side from `(shell-organism)/layout.tsx`) |

Endpoint signatures (verbatim from core):
```python
@router.get("/me")
async def get_current_user_profile(user: Annotated[User, Depends(get_user_from_token)]) -> User: ...

@router.get("/me/tenants")
async def get_my_tenants(
    user: Annotated[User, Depends(get_user_from_token)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TenantSchema]: ...
```

Auth: `Depends(get_user_from_token)` parses Clerk JWT from `Authorization: Bearer <token>` header. Tenant isolation enforced at `UserService` layer (core IAM).

## § 5 — Test surface (TDD RED first)

```python
# vitalia/backend/tests/test_main_iam_routes_mounted.py (NEW)
"""F1-S9 — verify core IAM auth router is mounted + vitalia legacy /me is gone."""
import pytest
from fastapi.testclient import TestClient
from src.main import app


def test_core_me_tenants_route_registered():
    """GET /api/v1/iam/users/me/tenants must be registered (mounted from core)."""
    routes = {r.path for r in app.routes}
    assert "/api/v1/iam/users/me/tenants" in routes
    assert "/api/v1/iam/users/me" in routes


def test_vitalia_local_me_route_removed():
    """GET /api/v1/iam/me (vitalia legacy stub) must NOT be registered."""
    routes = {r.path for r in app.routes}
    assert "/api/v1/iam/me" not in routes


def test_core_me_tenants_requires_auth():
    """Endpoint enforces Bearer token via core Depends(get_user_from_token)."""
    client = TestClient(app)
    response = client.get("/api/v1/iam/users/me/tenants")
    assert response.status_code in (401, 403, 422)  # depends on core exception
```

## § 6 — Constraints

- **Engine boundary**: `core/luana-core-iam/src/` is READ-ONLY. F1-S9 only IMPORTS + MOUNTS the existing router. Zero edit to core engine code.
- **Anti-duplication**: deleting `vitalia/backend/src/modules/vitalia/iam/api/router.py` (vitalia local `/me` stub) is mandatory — leaving both creates parallel layer violating `.claude/rules/anti-duplication.md`.
- **No DDL**: zero migration. No schema change.
- **response_model=**: core router already defines return types (`User`, `list[TenantSchema]`); `response_model=` PII gate satisfied automatically.
- **redirect_slashes=False**: unchanged in `main.py:39`.
- **HIPAA-lite**: `/me/tenants` returns user identity + tenant list (NO PHI per `vitalia/.claude/rules/hipaa-lite.md` PHI canonical list). Dual-filter exempt.

## § 7 — Verification (post-merge)

```bash
WS=$(git rev-parse --show-toplevel)

# 1. Arch tests still green
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -x -q

# 2. New mount test
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/test_main_iam_routes_mounted.py -v

# 3. Live curl (requires backend running + Clerk JWT)
curl -H "Authorization: Bearer ${CLERK_TOKEN}" http://localhost:8002/api/v1/iam/users/me/tenants
# Expect 200 + JSON array

# 4. Confirm legacy /me 404
curl -H "Authorization: Bearer ${CLERK_TOKEN}" http://localhost:8002/api/v1/iam/me
# Expect 404
```
