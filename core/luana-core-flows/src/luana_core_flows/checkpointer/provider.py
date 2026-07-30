# cap: __shared__
"""Brand-agnostic durable checkpointer provider for Luana flows.

Lifts the per-brand checkpointer factory mirror (vitalia
``copilot/workflows/wizard_checkpoint_config.py::build_production_checkpointer`` +
comunify inline equivalents) into a single shared engine factory, per
anti-duplication.md and proposal ``2026-06-02-durable-flows-engine`` (accepted).

Cardinal rule (copilot-expert): the PRODUCTION checkpointer is NEVER a
``MemorySaver``/``InMemorySaver`` — those are tutorial/test-only and are injected
directly at the composition root by tests, NOT produced by this factory.

Design notes (verified against installed libs 2026-06-02):
  - **O-1 lifespan-safe construction.** ``AsyncPostgresSaver.from_conn_string`` is
    an async context manager (scoped). For an app-lifetime checkpointer we build a
    pooled ``AsyncConnectionPool`` (``autocommit=True`` + ``dict_row`` +
    ``prepare_threshold=0``, the LangGraph-canonical Postgres kwargs) and hand it
    to ``AsyncPostgresSaver``. The pool is a long-lived process singleton — the
    composition root constructs the checkpointer ONCE at startup.
  - **No ``table_prefix``.** ``langgraph-checkpoint-postgres`` 3.1.0 uses FIXED
    table names (``checkpoints``, ``checkpoint_blobs``, ``checkpoint_writes``,
    ``checkpoint_migrations``) — it has no table-prefix knob. Brand isolation is
    therefore at the **database** level (each brand has its own Postgres DB via
    its ``postgres_dsn``); tenant isolation is the ``thread_id`` tenant segment
    (see ``thread_id.py``). This corrects the original arch assumption that a
    per-brand ``table_prefix`` would be honored.
  - **Deferred imports.** ``psycopg``/``AsyncPostgresSaver`` are imported INSIDE
    the factory so this module stays importable in environments without a libpq
    wrapper (CI/native unit tests). Unit tests stub the postgres modules; the real
    drivers are exercised by the integration + live-verify gates.
  - PHI (vitalia hipaa-lite): pass ``encryption_key`` → checkpoints are encrypted
    at rest via ``EncryptedSerializer.from_pycryptodome_aes()``.
"""

from __future__ import annotations

import os

import structlog
from langgraph.checkpoint.base import BaseCheckpointSaver

logger = structlog.get_logger(__name__)

_DEFAULT_POOL_MAX_SIZE = 20


async def make_durable_checkpointer(
    *,
    postgres_dsn: str,
    encryption_key: str | None = None,
    run_setup: bool = True,
    pool_max_size: int = _DEFAULT_POOL_MAX_SIZE,
) -> BaseCheckpointSaver:
    """Construct the production durable checkpointer (``AsyncPostgresSaver``).

    Args:
        postgres_dsn: Async-capable Postgres DSN. Per-brand DB = brand isolation.
        encryption_key: When set, checkpoints are encrypted at rest
            (vitalia PHI). Bridged to ``LANGGRAPH_AES_KEY`` for
            ``EncryptedSerializer.from_pycryptodome_aes()``. ``None`` (comunify) =
            default serializer.
        run_setup: When ``True`` (default), ``await saver.setup()`` runs ONCE at
            construction (idempotent, internal ``IF NOT EXISTS``). NEVER per-turn.
        pool_max_size: Connection pool ceiling.

    Returns:
        A ``BaseCheckpointSaver`` (concrete ``AsyncPostgresSaver``). NEVER a
        ``MemorySaver``.

    Raises:
        RuntimeError: if ``langgraph-checkpoint-postgres`` / ``psycopg`` is not
            importable (e.g. libpq wrapper missing).
    """
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg.rows import dict_row
        from psycopg_pool import AsyncConnectionPool
    except ImportError as exc:  # pragma: no cover - env-dependent
        msg = (
            "Durable checkpointer requires `langgraph-checkpoint-postgres` + a working "
            "`psycopg` (libpq). Install `psycopg[binary]` for native runs, or run inside "
            "the brand backend container. Tests inject InMemorySaver directly."
        )
        raise RuntimeError(msg) from exc

    serde = None
    if encryption_key:
        from langgraph.checkpoint.serde.encrypted import EncryptedSerializer

        # Bridge the explicit param to the env var the factory reads.
        os.environ.setdefault("LANGGRAPH_AES_KEY", encryption_key)
        serde = EncryptedSerializer.from_pycryptodome_aes()

    pool = AsyncConnectionPool(
        conninfo=postgres_dsn,
        max_size=pool_max_size,
        open=False,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    await pool.open()

    saver: BaseCheckpointSaver = (
        AsyncPostgresSaver(pool, serde=serde) if serde is not None else AsyncPostgresSaver(pool)
    )

    if run_setup:
        await saver.setup()

    logger.info(
        "durable_checkpointer_ready",
        encrypted=bool(encryption_key),
        run_setup=run_setup,
        saver=type(saver).__name__,
    )
    return saver


__all__ = ["make_durable_checkpointer"]
