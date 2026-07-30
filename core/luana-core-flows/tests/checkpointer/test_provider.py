"""Unit tests — make_durable_checkpointer (T-flows-2).

The native/CI env has no libpq wrapper, so the real ``AsyncPostgresSaver`` /
``psycopg`` cannot import. We stub the postgres modules in ``sys.modules`` so the
factory's deferred imports resolve to fakes — exercising the WIRING (serde,
setup, pool, never-MemorySaver) without a live DB. A real Postgres is exercised
by the ``integration``-marked test below + the brand-side live-verify.
"""

import asyncio
import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest

from luana_core_flows.checkpointer import make_durable_checkpointer

_DSN = "postgresql://u:p@localhost:5432/brand_db"


@pytest.fixture
def fake_pg(monkeypatch: pytest.MonkeyPatch) -> types.SimpleNamespace:
    saver = MagicMock(name="AsyncPostgresSaverInstance")
    saver.setup = AsyncMock()
    async_postgres_saver = MagicMock(name="AsyncPostgresSaver", return_value=saver)
    pg_aio = types.ModuleType("langgraph.checkpoint.postgres.aio")
    pg_aio.AsyncPostgresSaver = async_postgres_saver  # type: ignore[attr-defined]
    pg_parent = types.ModuleType("langgraph.checkpoint.postgres")

    psycopg_mod = types.ModuleType("psycopg")
    psycopg_rows = types.ModuleType("psycopg.rows")
    psycopg_rows.dict_row = object()  # type: ignore[attr-defined]
    psycopg_mod.rows = psycopg_rows  # type: ignore[attr-defined]

    pool_instance = MagicMock(name="poolInstance")
    pool_instance.open = AsyncMock()
    async_connection_pool = MagicMock(name="AsyncConnectionPool", return_value=pool_instance)
    psycopg_pool_mod = types.ModuleType("psycopg_pool")
    psycopg_pool_mod.AsyncConnectionPool = async_connection_pool  # type: ignore[attr-defined]

    enc_serde = MagicMock(name="EncryptedSerializerInstance")
    encrypted_serializer = MagicMock(name="EncryptedSerializer")
    encrypted_serializer.from_pycryptodome_aes = MagicMock(return_value=enc_serde)
    enc_mod = types.ModuleType("langgraph.checkpoint.serde.encrypted")
    enc_mod.EncryptedSerializer = encrypted_serializer  # type: ignore[attr-defined]

    for name, mod in (
        ("langgraph.checkpoint.postgres", pg_parent),
        ("langgraph.checkpoint.postgres.aio", pg_aio),
        ("psycopg", psycopg_mod),
        ("psycopg.rows", psycopg_rows),
        ("psycopg_pool", psycopg_pool_mod),
        ("langgraph.checkpoint.serde.encrypted", enc_mod),
    ):
        monkeypatch.setitem(sys.modules, name, mod)

    return types.SimpleNamespace(
        saver=saver,
        async_postgres_saver=async_postgres_saver,
        pool_instance=pool_instance,
        async_connection_pool=async_connection_pool,
        encrypted_serializer=encrypted_serializer,
        enc_serde=enc_serde,
    )


def test_returns_postgres_saver_never_memory(fake_pg: types.SimpleNamespace) -> None:
    result = asyncio.run(make_durable_checkpointer(postgres_dsn=_DSN))
    assert result is fake_pg.saver
    assert "Memory" not in type(result).__name__
    fake_pg.async_postgres_saver.assert_called_once()
    fake_pg.pool_instance.open.assert_awaited_once()


def test_run_setup_true_calls_setup(fake_pg: types.SimpleNamespace) -> None:
    asyncio.run(make_durable_checkpointer(postgres_dsn=_DSN, run_setup=True))
    fake_pg.saver.setup.assert_awaited_once()


def test_run_setup_false_skips_setup(fake_pg: types.SimpleNamespace) -> None:
    asyncio.run(make_durable_checkpointer(postgres_dsn=_DSN, run_setup=False))
    fake_pg.saver.setup.assert_not_awaited()


def test_encryption_key_wires_encrypted_serde(fake_pg: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGGRAPH_AES_KEY", raising=False)
    asyncio.run(make_durable_checkpointer(postgres_dsn=_DSN, encryption_key="aes-key-xyz"))
    fake_pg.encrypted_serializer.from_pycryptodome_aes.assert_called_once()
    _, kwargs = fake_pg.async_postgres_saver.call_args
    assert kwargs.get("serde") is fake_pg.enc_serde


def test_no_encryption_key_no_serde(fake_pg: types.SimpleNamespace) -> None:
    asyncio.run(make_durable_checkpointer(postgres_dsn=_DSN, encryption_key=None))
    fake_pg.encrypted_serializer.from_pycryptodome_aes.assert_not_called()
    _, kwargs = fake_pg.async_postgres_saver.call_args
    assert "serde" not in kwargs


@pytest.mark.integration
def test_setup_idempotent_real_postgres() -> None:
    """Integration (real Postgres): setup() twice on a clean DB = no error (O-2).

    Requires a live Postgres + libpq (dev stack). Skipped when unavailable.
    """
    dsn = _real_dsn_or_skip()
    saver = asyncio.run(make_durable_checkpointer(postgres_dsn=dsn, run_setup=True))
    # Second setup must be idempotent (internal IF NOT EXISTS).
    asyncio.run(saver.setup())


def _real_dsn_or_skip() -> str:
    import os

    dsn = os.environ.get("FLOWS_TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("FLOWS_TEST_POSTGRES_DSN not set (needs dev stack + libpq)")
    try:
        import psycopg  # noqa: F401
    except ImportError:
        pytest.skip("psycopg/libpq not available natively")
    return dsn
