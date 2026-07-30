# cap: crm.crm-consent-optout
"""Regression tests for ``get_async_session_committing`` (src/db.py).

Origin: live god-matrix verification of vitalia-crm-phi-base-tables-migration
surfaced that CRM endpoints used ``get_async_session`` (which never commits) →
PHI audit-log rows + writes (e.g. POST /leads → HTTP 201) were flushed then
rolled back at session close (no DB row). The committing dependency owns the
unit-of-work: commit on clean return, rollback + re-raise on exception.

These guard the contract deterministically (no DB needed). The end-to-end
persistence proof lives in the live verification (T-3-result.md) + the
integration suite (tests/integration/test_crm_phi_real_tables.py, run with DB).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import src.db as db_module


class _FakeSessionCM:
    """Minimal async context manager returning a mock session."""

    def __init__(self, session: AsyncMock) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncMock:
        return self._session

    async def __aexit__(self, *_exc: object) -> bool:
        return False


async def test_committing_session_commits_on_clean_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    """A handler that returns cleanly triggers a single commit, no rollback."""
    session = AsyncMock()
    monkeypatch.setattr(db_module, "_AsyncSessionLocal", lambda: _FakeSessionCM(session))

    agen = db_module.get_async_session_committing()
    yielded = await agen.__anext__()
    assert yielded is session
    with pytest.raises(StopAsyncIteration):
        await agen.__anext__()  # resume past yield → commit branch

    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


async def test_committing_session_rolls_back_and_reraises_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An exception in the handler triggers rollback + re-raise, never commit."""
    session = AsyncMock()
    monkeypatch.setattr(db_module, "_AsyncSessionLocal", lambda: _FakeSessionCM(session))

    class _Boom(Exception):
        pass

    agen = db_module.get_async_session_committing()
    await agen.__anext__()
    with pytest.raises(_Boom):
        await agen.athrow(_Boom())

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
