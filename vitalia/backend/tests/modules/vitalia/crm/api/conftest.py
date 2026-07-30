"""Conftest for CRM API router tests — KEK stub + DB session stub + auth stub.

T-2: adds fixtures so all CRM API unit tests can run without:
  - VITALIA_PHI_KEK env var set (KEKClient patched)
  - Live Postgres connection (get_async_session patched)
  - Real JWKS / Clerk auth (stub token decoder patched)

Pattern mirrors vitalia/backend/tests/modules/vitalia/inbox/api/conftest.py.

downstream-regression-na: brand-local vitalia CRM API test helpers
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.encryption.kek_client import KEKClient


class _StubSessionCtx:
    """Async context manager que entrega un AsyncMock session (sin DB viva).

    Extended to cover all SQLA 2.0 async access patterns used by repos:
    - session.execute (covered)
    - session.get  → AsyncMock
    - session.scalar / scalar_one_or_none (on result)
    - session.begin → async context manager stub
    - session.commit / session.rollback / session.close → AsyncMock
    """

    def __init__(self) -> None:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_result.fetchall.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value = mock_result
        mock_result.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        # session.get() used by some repos — return None (not found)
        mock_session.get = AsyncMock(return_value=None)
        # scalar helpers that some repos call directly on session
        mock_session.scalar = AsyncMock(return_value=None)
        mock_session.scalar_one_or_none = AsyncMock(return_value=None)
        # begin() used as async context manager for explicit transactions
        _begin_ctx = MagicMock()
        _begin_ctx.__aenter__ = AsyncMock(return_value=None)
        _begin_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session.begin = MagicMock(return_value=_begin_ctx)
        self._session = mock_session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *_exc: object) -> bool:
        return False


def _make_stub_ctx_from_token(authorization: str, x_tenant_id: str, x_clinic_id: str = "") -> object:
    """Parse a stub token and return a ClinicContext-like object.

    Stub token format: stub:{tenant_id}:{clinic_id}:{role}:{user_id}

    Used by _patch_stub_auth to give each test the RBAC context that
    matches the role encoded in its stub token — preserving the RBAC
    semantics (403 for marketing, 200 for doctor, etc.).

    Falls back to x_tenant_id/x_clinic_id header values if the token
    does not follow the stub format.
    """
    from src.modules.vitalia.iam.application.services.clinic_resolver import ClinicContext

    token = authorization.removeprefix("Bearer ").strip()
    if token.startswith("stub:"):
        parts = token.split(":", 4)
        # parts: ["stub", tenant_id, clinic_id, role, user_id]
        _tenant_id = parts[1] if len(parts) > 1 else x_tenant_id
        _clinic_id = parts[2] if len(parts) > 2 else (x_clinic_id or "00000000-0000-0000-0000-000000000000")
        _role = parts[3] if len(parts) > 3 else ""
        _user_id = parts[4] if len(parts) > 4 else "00000000-0000-0000-0000-000000000001"
    else:
        # Non-stub token in an autouse fixture context — treat as invalid
        # so 401 tests still get the right error via the real resolver.
        # Returning a synthetic context with empty role won't produce 401;
        # instead, raise to let the caller propagate via the real path.
        raise ValueError("non-stub token — defer to real resolver")

    try:
        tenant_uuid = UUID(_tenant_id)
    except (ValueError, AttributeError):
        tenant_uuid = UUID(x_tenant_id) if x_tenant_id else UUID(int=0)

    try:
        clinic_uuid = UUID(_clinic_id)
    except (ValueError, AttributeError):
        clinic_uuid = UUID(int=0)

    return ClinicContext(
        user_id=_user_id,
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
    """Stub for _resolve_context_async — parses stub tokens, raises HTTP 401 for bad ones.

    Replaces real async_resolve (which requires JWKS + live DB) with a pure
    in-memory parser for the stub token format used in unit tests.
    """
    from fastapi import HTTPException

    from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import JwtDecodeError

    token = authorization.removeprefix("Bearer ").strip()
    if not token.startswith("stub:"):
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    try:
        return _make_stub_ctx_from_token(authorization, x_tenant_id, x_clinic_id)
    except JwtDecodeError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")


@pytest.fixture(autouse=True)
def _patch_kek_and_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auto-patch KEKClient.from_env + sessionmaker para todos los CRM API unit tests.

    - KEKClient.from_env: mock KEK con fake 64-char hex key.
    - src.db._AsyncSessionLocal: el PUNTO correcto de patch (fix 2026-06-11).
      Patchear get_async_session/get_async_session_committing NO funciona:
      FastAPI Depends() captura el objeto función al import del router —
      monkeypatchear el attr del módulo después no cambia la referencia
      capturada. Ambos generadores hacen lookup de _AsyncSessionLocal en
      módulo-globals AT CALL TIME → patchear ahí cubre los dos deps
      (committing y no-committing) sin DB viva.
    """
    # Patch KEKClient.from_env at class level (works regardless of import path)
    mock_kek = MagicMock(spec=KEKClient)
    mock_kek.get_key.return_value = "a" * 64
    monkeypatch.setattr(KEKClient, "from_env", classmethod(lambda cls, *a, **kw: mock_kek))

    monkeypatch.setattr("src.db._AsyncSessionLocal", lambda: _StubSessionCtx())


@pytest.fixture(autouse=True)
def _patch_stub_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auto-patch _resolve_context_async in router + consent_endpoints for stub tokens.

    Tests that use `from src.main import app` send stub tokens of the form
    `stub:{tenant_id}:{clinic_id}:{role}:{user_id}`. The real async_resolve
    requires JWKS (Clerk) + live DB — neither of which exists in unit tests.

    This fixture wires _stub_resolve_context_async (above) into both modules
    that expose a _resolve_context_async at module scope, preserving:
      - 401 for real (non-stub) tokens (invalid JWKS path)
      - 403 for roles without PHI access (RBAC logic remains in service layer)
      - 200 for allowed roles

    Tests that manage their own monkeypatch (conversations/leads router tests)
    patch at a finer level and are not affected by this fixture — their
    monkeypatch overrides run AFTER this one in the same scope.
    """
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._resolve_context_async",
        _stub_resolve_context_async,
    )
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.consent_endpoints._resolve_context_async",
        _stub_resolve_context_async,
    )
