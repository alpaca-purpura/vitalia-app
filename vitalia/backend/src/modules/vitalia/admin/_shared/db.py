# cap: admin.admin-streamlit-service
# story-origin: TBD
"""Admin DB session helpers — synchronous session for Streamlit compatibility.

Streamlit runs in a synchronous context. Admin modules use synchronous
SQLAlchemy sessions via luana_core_platform.core.database.SessionLocal.

Note: AsyncSession is available for external callers (e.g., tests)
via get_async_session(). Admin UI code always uses get_sync_session().
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import structlog
from sqlalchemy.orm import Session

logger = structlog.get_logger()


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Context manager providing a synchronous SQLAlchemy session.

    Used by admin modules (Streamlit runs synchronously).
    Rolls back on exception, closes on exit.

    Usage:
        with get_sync_session() as session:
            session.execute(text("SELECT ..."))
            session.commit()
    """
    from luana_core_platform.core.database import SessionLocal  # noqa: PLC0415

    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_database_url() -> str:
    """Return the configured database URL for admin diagnostics.

    Returns empty string if not configured (fail-safe for health checks).
    """
    import os  # noqa: PLC0415

    return os.environ.get("DATABASE_URL", os.environ.get("POSTGRES_DSN", ""))
