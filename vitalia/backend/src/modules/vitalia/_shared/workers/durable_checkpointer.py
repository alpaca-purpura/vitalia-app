# cap: __shared__
"""Vitalia durable-flow checkpointer — single production construction surface.

Lifespan-level lazy singleton that consumes the lifted shared engine provider
``luana_core_flows.checkpointer.make_durable_checkpointer``. This REPLACES the
deleted brand factory mirror (``copilot/workflows/wizard_checkpoint_config.py``,
now removed) per ``.claude/rules/anti-duplication.md`` + promotion proposal
``2026-06-02-durable-flows-engine`` (accepted).

Why a single per-brand accessor:
  - ``langgraph-checkpoint-postgres`` 3.1.0 uses FIXED checkpoint table names
    (``checkpoints`` / ``checkpoint_blobs`` / ``checkpoint_writes`` /
    ``checkpoint_migrations``) — no per-flow ``table_prefix`` knob. Brand
    isolation is therefore at the **database** level (the vitalia Postgres DB
    via ``DATABASE_URL``); tenant isolation is the ``thread_id`` tenant segment
    (``luana_core_flows.build_flow_thread_id`` / ``build_phi_flow_thread_id``).
    A single durable checkpointer per process serves every vitalia durable
    graph (wizard onboarding, lucas daily analysis, treatment follow-up); the
    ``flow_id`` prefix in each ``thread_id`` namespaces the flow kind.
  - The provider opens a long-lived ``AsyncConnectionPool`` + runs ``.setup()``
    ONCE; caching the singleton is the lifespan-safe pattern (O-1).

HIPAA-lite (vitalia overlay): when ``LANGGRAPH_AES_KEY`` is configured, vitalia
checkpoints are encrypted at rest via ``EncryptedSerializer`` (defense in depth
for any PHI-bearing flow such as treatment follow-up). Wizard onboarding + lucas
analysis do not persist PHI in graph state, but the brand encrypts uniformly
when the key is present.
"""

from __future__ import annotations

import os

import structlog
from langgraph.checkpoint.base import BaseCheckpointSaver
from luana_core_flows.checkpointer import make_durable_checkpointer

logger = structlog.get_logger(__name__)

_checkpointer: BaseCheckpointSaver | None = None

# SQLAlchemy driver tags that must be stripped — AsyncPostgresSaver uses psycopg
# (libpq), NOT asyncpg; it needs a plain ``postgresql://`` libpq DSN.
_SQLALCHEMY_DRIVER_TAGS = (
    "postgresql+asyncpg://",
    "postgresql+psycopg://",
    "postgresql+psycopg2://",
)


def resolve_psycopg_dsn() -> str:
    """Resolve the vitalia Postgres DSN in psycopg (libpq) form.

    ``DATABASE_URL`` is the canonical env (docker-compose.dev.yml SSoT, mirrors
    ``src/db.py``). Any SQLAlchemy driver suffix is stripped because the durable
    checkpointer talks to Postgres through psycopg, not asyncpg.
    """
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        user = os.environ.get("POSTGRES_USER", "postgres")
        password = os.environ.get("POSTGRES_PASSWORD", "password")
        host = os.environ.get("POSTGRES_HOST", "localhost")
        port = os.environ.get("POSTGRES_PORT", "5432")
        db = os.environ.get("POSTGRES_DB", "vitalia_dev")
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    for tag in _SQLALCHEMY_DRIVER_TAGS:
        if dsn.startswith(tag):
            return "postgresql://" + dsn.split("://", 1)[1]
    return dsn


async def get_vitalia_durable_checkpointer() -> BaseCheckpointSaver:
    """Return the process-wide durable checkpointer (constructed once).

    Lazily builds the ``AsyncPostgresSaver`` on first call (opens the pool +
    runs ``.setup()``), then caches it for the process lifetime. Production
    composition roots (lucas daily-analysis factory, wizard production factory,
    cron schedulers) consume this — they NEVER construct ``MemorySaver``.
    """
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = await make_durable_checkpointer(
            postgres_dsn=resolve_psycopg_dsn(),
            encryption_key=os.environ.get("LANGGRAPH_AES_KEY"),  # PHI at-rest (hipaa-lite)
        )
        logger.info("vitalia_durable_checkpointer_initialized")
    return _checkpointer


async def reset_vitalia_durable_checkpointer() -> None:
    """Drop the cached singleton (test teardown / lifespan shutdown helper)."""
    global _checkpointer
    _checkpointer = None


__all__ = [
    "get_vitalia_durable_checkpointer",
    "reset_vitalia_durable_checkpointer",
    "resolve_psycopg_dsn",
]
