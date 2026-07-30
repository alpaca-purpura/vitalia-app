"""F1-S9 — verify core IAM auth router is mounted + vitalia legacy /me is gone.

TDD RED first (03-arch-be.md § 5):
- test_core_me_tenants_route_registered: RED until auth_router mounted in main.py
- test_vitalia_local_me_route_removed: RED until iam_router import removed from main.py
- test_core_me_tenants_requires_auth: RED until auth_router mounted

downstream-regression-na: brand-local mount verification test (vitalia F1-S9)
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

# Minimal env vars to satisfy luana_core_platform.core.config.Settings.__init__
# when auth_router is imported (triggers Settings() at module level via get_db import).
# These are non-secret test-only values — no production credentials.
_REQUIRED_ENV_VARS = {
    "LOG_LEVEL": "DEBUG",
    "DOMAIN_NAME": "localhost",
    "TRAEFIK_NETWORK": "traefik",
    "API_SECRET_KEY": "test-secret-key-for-mount-test",
    "WHATSAPP_API_TOKEN": "test-token",
    "WHATSAPP_PHONE_NUMBER_ID": "1234567890",
    "WHATSAPP_VERIFY_TOKEN": "test-verify",
    "OPENAI_API_KEY": "sk-test-0000000000000000000000000000000000000000000000000",
    "REDIS_URL": "redis://localhost:6379/0",
    "QDRANT_URL": "http://localhost:6333",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "postgres",
    "POSTGRES_DB": "vitalia_test",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "API_URL": "http://localhost:8002",
}


@pytest.fixture(autouse=True, scope="module")
def _set_env_for_core_iam_settings():
    """Inject minimal env vars required by luana_core_platform.core.config.Settings.

    auth_router import triggers Settings() instantiation via get_db → config module.
    Tests only verify route registration; no real DB/Redis/Qdrant calls are made.
    """
    with patch.dict(os.environ, _REQUIRED_ENV_VARS):
        yield


def test_core_me_tenants_route_registered() -> None:
    """GET /api/v1/iam/users/me/tenants must be registered (mounted from core).

    F1-S9 anti-duplication: REUSE core luana_core_iam auth_router, not a vitalia-local endpoint.
    Paridad nicolify/backend/src/main.py:543 (prefix='/api/v1/iam/users').
    """
    with patch.dict(os.environ, _REQUIRED_ENV_VARS):
        from src.main import app

        routes = {r.path for r in app.routes}
        assert "/api/v1/iam/users/me/tenants" in routes, (
            "Core auth_router GET /me/tenants must be mounted at prefix /api/v1/iam/users. "
            "Check main.py: from luana_core_iam.api.routers import auth_router as iam_users "
            "+ app.include_router(iam_users.router, prefix='/api/v1/iam/users', tags=['IAM - Users'])"
        )
        assert "/api/v1/iam/users/me" in routes, (
            "Core auth_router GET /me must also be mounted at /api/v1/iam/users/me."
        )


def test_vitalia_local_me_route_removed() -> None:
    """GET /api/v1/iam/me (vitalia legacy stub) must NOT be registered.

    F1-S9 anti-duplication enforcement: DELETE vitalia local /me stub router.
    See .claude/rules/anti-duplication.md — parallel layer violates SSoT.
    """
    with patch.dict(os.environ, _REQUIRED_ENV_VARS):
        from src.main import app

        routes = {r.path for r in app.routes}
        assert "/api/v1/iam/me" not in routes, (
            "Vitalia legacy /me stub (Slice 1 scaffold) must be removed from main.py. "
            "The stub at src/modules/vitalia/iam/api/router.py is deleted in F1-S9 T-1. "
            "core auth_router at /api/v1/iam/users/me is the canonical endpoint."
        )


def test_core_me_tenants_requires_auth() -> None:
    """Endpoint enforces Bearer token via core Depends(get_user_from_token).

    GET /api/v1/iam/users/me/tenants without valid JWT must return 401, 403, or 422.
    Tenant isolation enforced at UserService layer (core IAM).
    HIPAA-lite: /me/tenants returns user identity + tenant list (NO PHI).
    """
    with patch.dict(os.environ, _REQUIRED_ENV_VARS):
        from fastapi.testclient import TestClient

        from src.main import app

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/iam/users/me/tenants")
        assert response.status_code in (401, 403, 422), (
            f"Expected 401/403/422 for unauthenticated request, got {response.status_code}. "
            "Core auth_router must enforce get_user_from_token dependency."
        )
