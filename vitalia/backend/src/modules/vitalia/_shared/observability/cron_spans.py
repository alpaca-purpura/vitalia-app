# cap: workers.idempotent-cron-arq-scaffold
# story-origin: TBD
"""Cron job span context manager for Vitalia ARQ workers.

Wraps each of the 11 named ARQ cron job functions with an OTel span
that records span name, entry/exit status, and captures exceptions.

Usage:
    async with cron_span("vitalia.cron.followup_24h", attributes={"tenant_id": str(tid)}):
        await run_followup_sweep(tenant_id=tid)

Named spans (11 total, matching 03-arch-be.md § 4):
    vitalia.cron.followup_24h
    vitalia.cron.reactivation_45d
    vitalia.cron.maintenance_90d
    vitalia.cron.deposit_reminder_24h
    vitalia.cron.appointment_reminder_24h
    vitalia.cron.appointment_reminder_2h
    vitalia.cron.nps_request_24h_post_appointment
    vitalia.cron.brand_studio_audit_30d
    vitalia.cron.lucas_weekly_recommendations
    vitalia.cron.channel_sync_state_15min
    vitalia.cron.audit_log_retention_sweep_monthly

Anti-patterns avoided:
  ❌ No sync export / SimpleSpanProcessor (uses batch setup from otel_setup.py)
  ❌ No hardcoded endpoints
  ❌ No PHI in span attributes (cron spans are non-PHI; agent_spans handles PHI)

downstream-regression-na: brand-local cron span util; no cross-brand consumers
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# OTel imports — graceful degradation
# ---------------------------------------------------------------------------
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode, Tracer

    _OTEL_AVAILABLE = True
except ImportError:
    import enum

    class StatusCode(enum.Enum):  # type: ignore[no-redef]
        """Fallback StatusCode sentinel when opentelemetry-sdk not installed."""

        OK = "OK"
        ERROR = "ERROR"
        UNSET = "UNSET"

    class Status:  # type: ignore[no-redef]
        """Fallback Status sentinel when opentelemetry-sdk not installed."""

        def __init__(self, status_code: StatusCode, description: str = "") -> None:
            self.status_code = status_code
            self.description = description

    _OTEL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Canonical span name catalog (11 named spans per spec)
# ---------------------------------------------------------------------------
CRON_SPAN_NAMES: tuple[str, ...] = (
    "vitalia.cron.followup_24h",
    "vitalia.cron.reactivation_45d",
    "vitalia.cron.maintenance_90d",
    "vitalia.cron.deposit_reminder_24h",
    "vitalia.cron.appointment_reminder_24h",
    "vitalia.cron.appointment_reminder_2h",
    "vitalia.cron.nps_request_24h_post_appointment",
    "vitalia.cron.brand_studio_audit_30d",
    "vitalia.cron.lucas_weekly_recommendations",
    "vitalia.cron.channel_sync_state_15min",
    "vitalia.cron.audit_log_retention_sweep_monthly",
)


def _get_tracer() -> "Tracer":
    """Return the OTel tracer for vitalia cron jobs.

    Extracted as a function to allow test mocking.
    """
    if not _OTEL_AVAILABLE:  # pragma: no cover
        raise ImportError("opentelemetry-sdk is required for cron spans")
    return trace.get_tracer("vitalia.cron")


@asynccontextmanager
async def cron_span(
    name: str,
    *,
    attributes: dict[str, str | int | float | bool] | None = None,
) -> AsyncIterator[None]:
    """Async context manager wrapping an ARQ cron job with an OTel span.

    On entry:
      - Starts a new span with the given name
      - Sets any provided attributes via span.set_attributes()

    On success (no exception):
      - Sets span status to OK

    On error (exception):
      - Records the exception via span.record_exception()
      - Sets span status to ERROR
      - Re-raises the exception

    Args:
        name: Span name — should be one of CRON_SPAN_NAMES but not enforced
              at runtime (allows test spans).
        attributes: Optional dict of span attributes (key=str, value=primitive).
                    No PHI allowed here — cron spans are non-PHI context.

    Yields:
        None — the span is accessible via trace.get_current_span() inside the block.

    Example:
        async with cron_span("vitalia.cron.followup_24h", attributes={"run_id": "abc"}):
            await sweep_followups()
    """
    tracer = _get_tracer()
    with tracer.start_as_current_span(name) as span:
        if attributes:
            span.set_attributes(attributes)

        try:
            yield
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, description=str(exc)))
            logger.warning(
                "cron_span_error",
                span_name=name,
                error_type=type(exc).__name__,
                error=str(exc),
            )
            raise
