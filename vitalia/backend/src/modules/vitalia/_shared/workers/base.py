# cap: __shared__
# story-origin: TBD
"""Base helper for Vitalia ARQ cron jobs: idempotent_cron decorator.

Wraps each cron job function with:
  1. cron_span context manager (OTel tracing — T-infra-5)
  2. Idempotency key check (luana_core_idempotency — prevent duplicate execution)
  3. structlog audit on completion
  4. Sentry capture on exception (best-effort, does not suppress)

Usage:
    from src.modules.vitalia._shared.workers.base import idempotent_cron

    @idempotent_cron("vitalia.cron.followup_24h")
    async def followup_24h(ctx: dict) -> None:
        await run_followup_sweep()

Design decisions:
  - Idempotency is best-effort (soft-fail if Redis unavailable per engine pattern)
  - TTL 10min per cron execution window (prevent double-fire on retry bursts)
  - Sentry capture BEFORE re-raise (non-blocking)
  - structlog audit AFTER success (fire-forget OK for cron completion events)
  - cron_span handles OTel graceful degradation already (T-infra-5)

Anti-patterns avoided:
  ❌ No silent fallback that swallows exceptions (all exceptions propagate)
  ❌ No hardcoded tenant_id (cron workers iterate over tenants in real impl)
  ❌ No TZ-naive datetime (UTC is engine default)
  ❌ No cross-brand import

downstream-regression-na: brand-local cron decorator; no cross-brand consumers
"""

from __future__ import annotations

import functools
from collections.abc import Callable, Coroutine
from typing import Any

import structlog

from src.modules.vitalia._shared.observability.cron_spans import cron_span

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Sentry — graceful degradation when SDK not installed
# ---------------------------------------------------------------------------
try:
    import sentry_sdk  # type: ignore[import-untyped]

    _SENTRY_AVAILABLE = True
except ImportError:
    _SENTRY_AVAILABLE = False

    class _SentrySentinel:
        """Fallback no-op when sentry-sdk is not installed."""

        @staticmethod
        def capture_exception(exc: BaseException | None = None) -> None:
            """No-op fallback."""

    sentry_sdk = _SentrySentinel()  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Idempotency store — soft-fail when Redis unavailable
# ---------------------------------------------------------------------------
_IDEM_TTL_SECONDS = 600  # 10 minutes — cron execution deduplication window


def _get_idem_store() -> Any:  # noqa: ANN401
    """Return an IdempotencyStore instance from the engine, or None for soft-fail.

    Extracted as a function to allow test mocking.
    Returns None when Redis is not configured (soft-fail mode).
    """
    try:
        import os  # noqa: PLC0415

        from luana_core_idempotency.domain.key import IdempotencyKey  # noqa: PLC0415, F401
        from luana_core_idempotency.infrastructure.redis_store import (  # noqa: PLC0415
            RedisIdempotencyStore,
        )

        redis_url = os.environ.get("REDIS_URL")
        if not redis_url:
            return None

        import redis.asyncio as aioredis  # noqa: PLC0415

        redis_client = aioredis.from_url(redis_url, decode_responses=False)
        return RedisIdempotencyStore(redis_client=redis_client)
    except Exception:  # noqa: BLE001 — soft-fail, cron continues without idempotency
        return None


# ---------------------------------------------------------------------------
# idempotent_cron decorator
# ---------------------------------------------------------------------------


def idempotent_cron(
    span_name: str,
    *,
    idem_ttl_seconds: int = _IDEM_TTL_SECONDS,
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Callable[..., Coroutine[Any, Any, Any]]]:
    """Decorator factory for ARQ cron job functions.

    Wraps the decorated async function with:
      1. Idempotency key check (skip if already running in this TTL window)
      2. OTel cron_span context manager (from T-infra-5)
      3. structlog audit on successful completion
      4. Sentry capture + re-raise on exception

    Args:
        span_name: OTel span name (should be one of CRON_SPAN_NAMES from cron_spans.py).
        idem_ttl_seconds: Redis TTL for the idempotency key (default 600 = 10min).

    Returns:
        Decorated async function preserving __name__ via functools.wraps.

    Example:
        @idempotent_cron("vitalia.cron.followup_24h")
        async def followup_24h(ctx: dict) -> None:
            await sweep_followups()
    """

    def decorator(
        fn: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Callable[..., Coroutine[Any, Any, Any]]:
        @functools.wraps(fn)
        async def wrapper(ctx: dict, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            job_id = ctx.get("job_id", "unknown")

            # ------------------------------------------------------------------
            # 1. Idempotency check — prevent duplicate execution on retry bursts
            # ------------------------------------------------------------------
            idem_store = _get_idem_store()
            if idem_store is not None:
                try:
                    from luana_core_idempotency.domain.key import IdempotencyKey  # noqa: PLC0415

                    idem_key = IdempotencyKey(
                        namespace=f"vitalia.cron.{fn.__name__}",
                        key=job_id,
                        ttl_seconds=idem_ttl_seconds,
                    )
                    claimed = await idem_store.claim(idem_key)
                    if not claimed:
                        logger.info(
                            "cron_skipped_duplicate",
                            span_name=span_name,
                            fn_name=fn.__name__,
                            job_id=job_id,
                        )
                        return None
                except Exception:  # noqa: BLE001 — soft-fail idempotency
                    logger.warning(
                        "cron_idempotency_check_failed_softfail",
                        span_name=span_name,
                        fn_name=fn.__name__,
                        exc_info=True,
                    )

            # ------------------------------------------------------------------
            # 2. OTel span + execution
            # ------------------------------------------------------------------
            async with cron_span(span_name, attributes={"job_id": job_id}):
                try:
                    result = await fn(ctx, *args, **kwargs)
                except Exception as exc:
                    # 4. Sentry capture (best-effort, does not suppress)
                    sentry_sdk.capture_exception(exc)
                    raise
                else:
                    # 3. structlog audit on successful completion
                    logger.info(
                        "cron_completed",
                        span_name=span_name,
                        fn_name=fn.__name__,
                        job_id=job_id,
                    )
                    return result

        return wrapper

    return decorator
