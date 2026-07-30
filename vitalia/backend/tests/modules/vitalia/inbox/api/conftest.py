"""Conftest for inbox API router tests — Slice 2 migration helpers.

Provides:
  - mock_async_resolve fixture: patches ClinicResolver.async_resolve (Slice 2 path).
  - stub_get_async_session: overrides get_async_session for tests that use
    Depends(get_async_session) in inbox endpoints (added in Slice 2 migration).

Prior to Slice 2, inbox tests patched `_get_resolver` to return a sync
`MagicMock(**{"resolve.return_value": ctx})`. After Slice 2 migration, the
router calls `async_resolve()` (not `resolve()`). Tests that create a minimal
FastAPI app via `_make_app()` must also override `get_async_session` to avoid
live DB connection attempts in unit tests.

Usage pattern for new tests:
    from tests.modules.vitalia.inbox.api.conftest import (
        stub_async_session,
    )
    # or via monkeypatch:
    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=ctx),
    )
    app.dependency_overrides[get_async_session] = stub_async_session

downstream-regression-na: brand-local test helpers (vitalia inbox — no cross-module consumers)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession


async def stub_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Stub get_async_session for inbox router unit tests.

    Yields an AsyncMock instead of a real DB session.
    Used to avoid live DB connection attempts in tests that use
    Depends(get_async_session) in inbox endpoints (Slice 2 migration).
    """
    mock_session = AsyncMock(spec=AsyncSession)
    yield mock_session


def apply_session_stub(app: FastAPI) -> FastAPI:
    """Override get_async_session in the test app with a stub.

    Call this in tests that create a minimal FastAPI app via _make_app()
    to avoid live DB connection attempts.

    Args:
        app: FastAPI app instance (from _make_app()).

    Returns:
        The same app with dependency_overrides set.
    """
    from src.db import get_async_session  # noqa: PLC0415

    app.dependency_overrides[get_async_session] = stub_async_session
    return app
