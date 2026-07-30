# cap: __shared__
"""Database engine, session factory, and Redis client initialization.

T-1 (copilot-chat-mountable): all three eager module-load inits have been
deferred to lazy @lru_cache factory functions so that importing this module
does NOT instantiate Settings, create DB engines, or connect to Redis.

Public API (lazy):
    get_engine()        -> sqlalchemy.Engine  (sync, @lru_cache)
    get_async_engine()  -> AsyncEngine        (@lru_cache)
    get_redis_client()  -> redis.Redis | None (@lru_cache, graceful-degrade)
    get_db()            -> Generator[Session] (FastAPI dependency, unchanged)

Back-compat: module-level names ``engine``, ``async_engine``,
``async_session_maker``, ``redis_client`` are kept as properties via
module-level __getattr__ with a DeprecationWarning (shim) so existing
off-path callers keep working during T-4 migration.
"""

from __future__ import annotations

import warnings
from functools import lru_cache
from typing import TYPE_CHECKING

import redis as redis_mod
import structlog
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy import Engine
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = structlog.get_logger(__name__)


# ─── Lazy factory functions ──────────────────────────────────────────────────


@lru_cache
def get_engine() -> "Engine":
    """Return the singleton sync SQLAlchemy engine (lazy, created on first call).

    Calls get_settings() inside so importing this module is safe with
    multibrand-only env (no POSTGRES_* legacy vars needed at import time).
    """
    from luana_core_platform.core.config import get_settings

    s = get_settings()
    return create_engine(
        s.database_url,
        pool_pre_ping=True,
        pool_recycle=300,
    )


@lru_cache
def get_async_engine() -> "AsyncEngine":
    """Return the singleton async SQLAlchemy engine (lazy, created on first call)."""
    from luana_core_platform.core.config import get_settings

    s = get_settings()
    async_url = s.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(
        async_url,
        pool_pre_ping=True,
        pool_recycle=300,
    )


@lru_cache
def get_async_session_maker() -> "async_sessionmaker[AsyncSession]":
    """Return the async session factory (lazy, singleton via lru_cache)."""
    return async_sessionmaker(
        get_async_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )


@lru_cache
def get_redis_client() -> "redis_mod.Redis | None":
    """Return a connected Redis client or None if Redis is unavailable.

    Graceful degradation: connection errors are caught and logged as warnings.
    The app boots and runs without Redis; cache/rate-limit features degrade.
    """
    from luana_core_platform.core.config import get_settings

    s = get_settings()
    try:
        client: redis_mod.Redis = redis_mod.from_url(s.REDIS_URL, decode_responses=True)
        client.ping()
        logger.info("redis_connected", url=s.REDIS_URL)
        return client
    except (redis_mod.ConnectionError, redis_mod.TimeoutError, OSError) as exc:
        logger.warning(
            "redis_unavailable",
            url=s.REDIS_URL,
            error=str(exc),
            hint="App will start without Redis; cache/queue features degraded",
        )
        return None


# ─── FastAPI dependency (unchanged public surface) ───────────────────────────


def get_db() -> "Generator[Session, None, None]":
    """Dependency for FastAPI routers to get a database session."""
    db = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())()
    try:
        yield db
    finally:
        db.close()


def init_db(base_metadata: MetaData | None = None) -> None:
    """Initialize database tables."""
    if base_metadata:
        base_metadata.create_all(bind=get_engine())


# ─── Back-compat shim (PEP 562 module __getattr__) ───────────────────────────
# Off-path callers using `from luana_core_platform.core.database import engine`
# (or redis_client / async_engine / async_session_maker) continue to work
# but receive a DeprecationWarning.  Migrate in T-4.

_COMPAT_MAP = {
    "engine": "get_engine",
    "async_engine": "get_async_engine",
    "async_session_maker": "get_async_session_maker",
    "redis_client": "get_redis_client",
    "SessionLocal": None,  # lazy proxy — see _LazySessionLocal below
}


class _LazySessionLocal:
    """Lazy drop-in for the legacy ``SessionLocal = sessionmaker(bind=engine)`` pattern.

    T-2 fix (copilot-chat-mountable): the old shim called ``get_engine()`` the
    moment ``SessionLocal`` was imported — instantiating Settings() eagerly.
    This proxy defers engine binding until the first ``.call()`` (i.e. ``db =
    SessionLocal()``) so that ``from luana_core_platform.core.database import
    SessionLocal`` is safe in a multibrand env that lacks legacy env vars.

    Behaves identically to the original ``sessionmaker`` factory for the
    two usage patterns that exist in the codebase:
      1. ``db = SessionLocal()``          — create a Session
      2. ``SessionLocal.configure(...)``  — not used today; raises AttributeError
         so it surfaces immediately rather than silently misbehaving.
    """

    def __call__(self) -> "Session":
        """Create and return a new sync Session, binding the engine lazily."""
        return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())()

    def __repr__(self) -> str:
        return "<_LazySessionLocal (deferred engine binding)>"


# Singleton proxy — safe to import at module level; engine binding deferred.
_lazy_session_local = _LazySessionLocal()


def __getattr__(name: str) -> object:
    """Module-level back-compat shim for legacy attribute access."""
    if name in _COMPAT_MAP:
        warnings.warn(
            f"luana_core_platform.core.database.{name} is deprecated — "
            f"use the lazy accessor function instead (T-4 off-path migration).",
            DeprecationWarning,
            stacklevel=2,
        )
        if name == "engine":
            return get_engine()
        if name == "async_engine":
            return get_async_engine()
        if name == "async_session_maker":
            return get_async_session_maker()
        if name == "redis_client":
            return get_redis_client()
        if name == "SessionLocal":
            # Return the lazy proxy — defers get_engine() until db = SessionLocal()
            return _lazy_session_local
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
