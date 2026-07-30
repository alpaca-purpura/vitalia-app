"""Tests for CRM API — patients and leads endpoints.

TDD: RED tests defined before implementation (T-infra-9).

Uses httpx.AsyncClient with ASGITransport (no live server needed).

downstream-regression-na: brand-local CRM API tests
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.encryption.kek_client import KEKClient

# ---------------------------------------------------------------------------
# Stub auth helpers — parse stub:{tenant}:{clinic}:{role}:{user} tokens
# ---------------------------------------------------------------------------


def _parse_stub_token(authorization: str, x_tenant_id: str, x_clinic_id: str = "") -> object:
    """Return a ClinicContext built from a stub token.

    Stub format: stub:{tenant_id}:{clinic_id}:{role}:{user_id}
    """
    from src.modules.vitalia.iam.application.services.clinic_resolver import ClinicContext

    token = authorization.removeprefix("Bearer ").strip()
    parts = token.split(":", 4)
    _tid = parts[1] if len(parts) > 1 else x_tenant_id
    _cid = parts[2] if len(parts) > 2 else (x_clinic_id or "00000000-0000-0000-0000-000000000000")
    _role = parts[3] if len(parts) > 3 else ""
    _uid = parts[4] if len(parts) > 4 else "00000000-0000-0000-0000-000000000001"

    try:
        tenant_uuid = UUID(_tid)
    except (ValueError, AttributeError):
        tenant_uuid = UUID(x_tenant_id) if x_tenant_id else UUID(int=0)
    try:
        clinic_uuid = UUID(_cid)
    except (ValueError, AttributeError):
        clinic_uuid = UUID(int=0)

    return ClinicContext(
        user_id=_uid,
        tenant_id=tenant_uuid,
        clinic_id=clinic_uuid,
        role=_role,
        email=None,
        name=None,
    )


async def _stub_resolve_context_async(
    authorization: str,
    x_tenant_id: str,
    x_clinic_id: str,
    session: object,
) -> object:
    """Stub for async resolver — parses stub tokens; raises 401 for non-stub."""
    from fastapi import HTTPException

    token = authorization.removeprefix("Bearer ").strip()
    if not token.startswith("stub:"):
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")
    return _parse_stub_token(authorization, x_tenant_id, x_clinic_id)


def _stub_resolve_context_sync(authorization: str, x_tenant_id: str) -> object:
    """Stub for sync resolver (leads) — parses stub tokens; raises 401 for non-stub."""
    from fastapi import HTTPException

    token = authorization.removeprefix("Bearer ").strip()
    if not token.startswith("stub:"):
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")
    return _parse_stub_token(authorization, x_tenant_id)


class _StubSessionCtx:
    """Async context manager returning an AsyncMock DB session (no live DB)."""

    def __init__(self) -> None:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_result.fetchall.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value = mock_result
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.get = AsyncMock(return_value=None)
        mock_session.scalar = AsyncMock(return_value=None)
        _begin_ctx = MagicMock()
        _begin_ctx.__aenter__ = AsyncMock(return_value=None)
        _begin_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session.begin = MagicMock(return_value=_begin_ctx)
        self._session = mock_session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *_exc: object) -> bool:
        return False


@pytest.fixture(autouse=True)
def _patch_crm_api_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auto-patch auth + KEK + DB session for test_crm_api.py tests.

    Allows tests using `from src.main import app` with stub tokens to:
    - Bypass JWKS auth (no Clerk creds in test env)
    - Bypass live DB (no Postgres needed for unit tests)
    - Bypass KEK env var requirement

    RBAC semantics are preserved: the stub token encodes the role, and
    the endpoint's PHIAccessDeniedError check still runs via PatientService.
    """
    # KEKClient — fake key so PatientRepository doesn't need VITALIA_PHI_KEK env
    mock_kek = MagicMock(spec=KEKClient)
    mock_kek.get_key.return_value = "a" * 64
    monkeypatch.setattr(KEKClient, "from_env", classmethod(lambda cls, *a, **kw: mock_kek))

    # DB session — no live Postgres
    monkeypatch.setattr("src.db._AsyncSessionLocal", lambda: _StubSessionCtx())

    # Async resolver (PHI endpoints: get_patient, patch_patient) in router.py
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._resolve_context_async",
        _stub_resolve_context_async,
    )
    # Async resolver in consent_endpoints.py (opt-out, marketing-opt-in)
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.consent_endpoints._resolve_context_async",
        _stub_resolve_context_async,
    )
    # Sync resolver (non-PHI leads endpoints) in router.py
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._resolve_context_sync",
        _stub_resolve_context_sync,
    )


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
class TestPatientsEndpoints:
    """CRM patients endpoints — RBAC + response_model enforcement."""

    async def test_get_patient_returns_403_for_marketing_role(self) -> None:
        """Marketing role must not access PHI endpoints."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:marketing:user_mkt"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/crm/patients/{patient_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )
        assert response.status_code == 403

    async def test_get_patient_returns_403_for_receptionist_role(self) -> None:
        """Receptionist role must not access PHI endpoints."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:receptionist:user_recep"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/crm/patients/{patient_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )
        assert response.status_code == 403

    async def test_get_patient_requires_auth_header(self) -> None:
        """Request without Authorization header returns 422 or 401."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/crm/patients/{patient_id}",
                headers={"X-Tenant-ID": tenant_id, "X-Clinic-ID": clinic_id},
            )
        assert response.status_code in (422, 401, 400)

    async def test_opt_out_requires_clinic_header(self) -> None:
        """POST /patients/{id}/opt-out must require X-Clinic-ID header."""
        from src.main import app

        tenant_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{uuid4()}:admin_clinic:user_admin"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/crm/patients/{patient_id}/opt-out",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    # X-Clinic-ID intentionally absent
                },
                json={"reason": "requested"},
            )
        # Missing required header → 422
        assert response.status_code in (422, 400)

    async def test_patch_patient_blocked_for_marketing(self) -> None:
        """PATCH /patients/{id} blocked for marketing role."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:marketing:user_mkt2"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/crm/patients/{patient_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
                json={"phone": "555-1234"},
            )
        assert response.status_code == 403


@pytest.mark.anyio
class TestLeadsEndpoints:
    """CRM leads endpoints — non-PHI, single tenant filter."""

    async def test_get_lead_requires_auth_header(self) -> None:
        """Request without Authorization returns 422/401."""
        from src.main import app

        tenant_id = str(uuid4())
        lead_id = str(uuid4())

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/crm/leads/{lead_id}",
                headers={"X-Tenant-ID": tenant_id},
            )
        assert response.status_code in (422, 401, 400)

    async def test_get_lead_accessible_without_clinic_header(self) -> None:
        """Lead is non-PHI — X-Clinic-ID is optional (no dual filter required)."""
        from src.main import app

        tenant_id = str(uuid4())
        lead_id = str(uuid4())
        token = f"stub:{tenant_id}:{uuid4()}:marketing:user_mkt3"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/crm/leads/{lead_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    # X-Clinic-ID intentionally absent
                },
            )
        # Expect 404 (lead not found) not 422/403 — lead endpoint accessible without clinic_id
        assert response.status_code in (404, 200)
