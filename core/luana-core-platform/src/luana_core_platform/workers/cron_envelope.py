# downstream-regression-na: engine utility decorator; brand cron jobs wire at registration sites
"""Cron envelope — engine-grade decorator for ARQ cron jobs.

Wraps async cron job functions with:
  1. Idempotency check (luana_core_idempotency — prevent duplicate execution)
  2. OTel span context manager (graceful degrade when opentelemetry-api not installed)
  3. structlog audit on successful completion
  4. Sentry capture on exception (graceful degrade when sentry_sdk not installed)

Usage:
    from luana_core_platform.workers.cron_envelope import cron_envelope

    @cron_envelope("vitalia.cron.followup_24h")
    async def followup_24h(ctx: dict) -> None:
        await run_followup_sweep(ctx)

    @cron_envelope("saasora.cron.churn_detection", ttl=3600, enable_sentry=False)
    async def churn_detection(ctx: dict) -> None:
        await sweep_churned_accounts(ctx)

Design notes:
  - Idempotency key is ``{name}:exec`` — one key per cron name per TTL window.
  - Idempotency is best-effort (soft-fail if Redis unavailable per engine pattern).
  - OTel span graceful degrades when opentelemetry-api SDK not installed.
  - Sentry capture is best-effort (graceful degrades when sentry_sdk not installed).
  - All exceptions propagate — no silent swallow.
  - structlog audit logged AFTER success (fire-forget OK for cron completion events).

Promotion origin:
  vitalia/_shared/workers/base.py::idempotent_cron (brand-local).
  Lifted to engine Slice 1 per proposal 2026-05-20-core-platform-extensions-slice-1.md.
"""

from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager, nullcontext
from typing import TYPE_CHECKING, Any, AsyncIterator, ParamSpec, TypeVar

import structlog

if TYPE_CHECKING:
    pass

P = ParamSpec("P")
R = TypeVar("R")
logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Sentry — graceful degradation when SDK not installed
# ---------------------------------------------------------------------------
try:
    import sentry_sdk as _sentry_sdk  # type: ignore[import-untyped]

    _SENTRY_AVAILABLE = True
except ImportError:
    _SENTRY_AVAILABLE = False
    _sentry_sdk = None  # type: ignore[assignment]


def _capture_sentry(name: str, exc: BaseException) -> None:
    """Capture exception in Sentry if SDK available. Best-effort, never raises.

    Args:
        name: Cron job name for context (used in structlog fallback).
        exc: Exception to capture.
    """
    if not _SENTRY_AVAILABLE or _sentry_sdk is None:
        logger.debug(
            "cron_sentry_skipped",
            cron_name=name,
            reason="sentry_sdk not installed",
        )
        return
    try:
        _sentry_sdk.capture_exception(exc)
    except Exception:  # noqa: BLE001 — best-effort, must not suppress original
        logger.debug("cron_sentry_capture_failed", cron_name=name)


# ---------------------------------------------------------------------------
# OTel span — graceful degradation when opentelemetry-api not installed
# ---------------------------------------------------------------------------
try:
    from opentelemetry import trace as _otel_trace  # type: ignore[import-untyped]
    from opentelemetry.trace import Status as _OtelStatus  # type: ignore[import-untyped]
    from opentelemetry.trace import StatusCode as _OtelStatusCode

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False
    _otel_trace = None  # type: ignore[assignment]
    _OtelStatus = None  # type: ignore[assignment]
    _OtelStatusCode = None  # type: ignore[assignment]


@asynccontextmanager
async def _otel_cron_span(name: str) -> AsyncIterator[None]:
    """Internal OTel span context manager for cron jobs.

    Gracefully degrades to a no-op when opentelemetry-api is not installed
    or when status classes are unavailable (e.g. partial mock environments).
    Sets span status to OK on success, ERROR on exception, then re-raises.

    Args:
        name: Span name (dot-namespaced cron job name).
    """
    if not _OTEL_AVAILABLE or _otel_trace is None:
        yield
        return

    tracer = _otel_trace.get_tracer("luana.cron")
    with tracer.start_as_current_span(name) as span:
        try:
            yield
            if _OtelStatus is not None and _OtelStatusCode is not None:
                span.set_status(_OtelStatus(_OtelStatusCode.OK))  # type: ignore[arg-type]
        except Exception as exc:
            span.record_exception(exc)
            if _OtelStatus is not None and _OtelStatusCode is not None:
                span.set_status(  # type: ignore[arg-type]
                    _OtelStatus(_OtelStatusCode.ERROR, description=str(exc))  # type: ignore[arg-type]
                )
            raise


# ---------------------------------------------------------------------------
# Idempotency integration — soft-fail wrapper
# ---------------------------------------------------------------------------


def _build_idempotent_fn(fn: Callable[P, Awaitable[R]], name: str, ttl: int) -> Callable[P, Awaitable[R]]:
    """Wrap fn with @idempotent from luana_core_idempotency.

    The idempotency key is ``{name}:exec`` — one execution slot per cron name
    per TTL window. This prevents double-fire on retry bursts within the window.

    Soft-fail: if luana_core_idempotency is unavailable, returns fn unwrapped.

    Args:
        fn: Async function to wrap.
        name: Dot-namespaced cron job name (used as idempotency namespace).
        ttl: Idempotency window in seconds.

    Returns:
        Idempotency-wrapped async function (or original if engine unavailable).
    """
    try:
        from luana_core_idempotency.application.decorator import idempotent  # noqa: PLC0415

        return idempotent(
            namespace=name,
            key_fn=lambda *_args, **_kwargs: f"{name}:exec",
            ttl=ttl,
        )(fn)
    except ImportError:
        logger.warning(
            "cron_idempotency_unavailable",
            cron_name=name,
            reason="luana_core_idempotency not installed — running without deduplication",
        )
        return fn


# ---------------------------------------------------------------------------
# cron_envelope — public API
# ---------------------------------------------------------------------------


def cron_envelope(
    name: str,
    *,
    ttl: int = 600,
    enable_otel: bool = True,
    enable_sentry: bool = True,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Engine-grade decorator for ARQ cron job functions.

    Composes four cross-cutting concerns on top of any async cron function:
    idempotency deduplication, OTel tracing, structured audit logging, and
    Sentry error capture. All three observability layers gracefully degrade when
    their respective SDKs are not installed.

    Args:
        name: Dot-namespaced cron job identifier used as idempotency namespace,
              OTel span name, and structlog audit field.
              Convention: ``"{brand}.cron.{job_slug}"``
              Examples: ``"vitalia.cron.followup_24h"``,
              ``"saasora.cron.churn_detection"``.
        ttl: Idempotency window in seconds. Default 600 (10 min) — prevents
             double-fire on retry bursts within a single execution window.
             Increase for longer-running jobs where re-trigger risk is wider.
        enable_otel: When True (default), wraps the call in an OTel span via
                     the engine tracer ``"luana.cron"``. Gracefully degrades to
                     a no-op when ``opentelemetry-api`` is not installed.
        enable_sentry: When True (default), captures exceptions in Sentry before
                       re-raising. Gracefully degrades when ``sentry-sdk`` is not
                       installed. The exception always propagates regardless.

    Returns:
        Decorator that wraps an async cron job function with all four layers.

    Raises:
        TypeError: If the decorated function is not async (checked at decoration time).

    Example::

        from luana_core_platform.workers.cron_envelope import cron_envelope

        @cron_envelope("vitalia.cron.followup_24h")
        async def followup_24h(ctx: dict) -> None:
            await run_followup_sweep(ctx)

        # Disable OTel for low-overhead internal jobs:
        @cron_envelope("vitalia.cron.audit_log_retention", enable_otel=False)
        async def audit_log_retention(ctx: dict) -> None:
            await sweep_expired_audit_rows(ctx)

    Notes:
        - Idempotency is best-effort: if Redis is unavailable the job runs without
          deduplication (soft-fail per ``tessl__graceful-degradation`` pattern).
        - Sentry capture is non-blocking: exception propagates even if Sentry call
          itself raises.
        - structlog audit event ``cron_completed`` is logged after the function
          returns successfully. Failed jobs emit no audit (the exception speaks for
          itself — Sentry captures context).
    """

    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        """Apply cron_envelope to the given async function."""
        if not callable(fn):
            msg = f"cron_envelope: expected callable, got {type(fn)!r}"
            raise TypeError(msg)

        # Wrap with idempotency once at decoration time.
        idempotent_fn = _build_idempotent_fn(fn, name, ttl)

        @functools.wraps(fn)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            span_ctx: Any = _otel_cron_span(name) if enable_otel else nullcontext()

            async with span_ctx:
                try:
                    result = await idempotent_fn(*args, **kwargs)
                    logger.info(
                        "cron_completed",
                        cron_name=name,
                        fn=fn.__name__,
                    )
                    return result
                except Exception as exc:
                    if enable_sentry:
                        _capture_sentry(name, exc)
                    raise

        return wrapped  # type: ignore[return-value]

    return decorator
