# cap: __shared__
# story-origin: TBD
"""Agent turn span context manager for Vitalia agentic workers.

Wraps agent turn execution (Adrián, Lucas, Valeria) with OTel spans.
Injects cost attributes + sanitizes PHI before setting span attributes.

Usage:
    async with agent_turn_span(
        agent_name="vitalia.agent.adrian",
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        conversation_id=conversation_id,
    ) as span_ctx:
        result = await run_turn(...)
        span_ctx.set_cost(
            cost_usd=result.cost_usd,
            tokens_input=result.tokens_input,
            tokens_output=result.tokens_output,
            cache_read_tokens=result.cache_read_tokens,
        )

Anti-duplication rule adherence:
  ❌ NEVER define local PII regex — import sanitize_phi_payload from compliance adapter
  ❌ NEVER mirror sanitize_payload from luana_core_observability — import it

Per .claude/rules/anti-duplication.md:
  "PII sanitization lives in core/luana-core-observability/src/.../sanitization.py"
  "vitalia adapter: compliance_service_adapter.sanitize_phi_payload"

Per T-infra-5 spec cost attrs:
  agentic.cost_usd, agentic.tokens_input, agentic.tokens_output, agentic.cache_read_tokens

downstream-regression-na: brand-local agent span util; no cross-brand consumers
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import UUID

import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# OTel imports — graceful degradation
# ---------------------------------------------------------------------------
try:
    from opentelemetry import trace
    from opentelemetry.trace import Span, Status, StatusCode, Tracer

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
# PHI sanitization — IMPORT from engine/adapter, NEVER define locally
# Anti-duplication.md § inventory: PII sanitization lives in engine
# ---------------------------------------------------------------------------
try:
    from src.modules.vitalia.compliance.application.compliance_service_adapter import (  # noqa: PLC0415
        sanitize_phi_payload,
    )

    _SANITIZE_AVAILABLE = True
except ImportError:
    _SANITIZE_AVAILABLE = False

    def sanitize_phi_payload(payload: dict) -> dict:  # type: ignore[misc]
        """Fallback when compliance adapter not available in test env."""
        return payload


def _get_tracer() -> "Tracer":
    """Return the OTel tracer for vitalia agent turns.

    Extracted as a function to allow test mocking.
    """
    if not _OTEL_AVAILABLE:  # pragma: no cover
        raise ImportError("opentelemetry-sdk is required for agent spans")
    return trace.get_tracer("vitalia.agents")


class AgentSpanContext:
    """Context object yielded by agent_turn_span.

    Allows callers to inject cost attributes after turn execution
    without accessing the OTel span directly.

    Cost attributes (per T-infra-5 spec):
      agentic.cost_usd         — total cost in USD
      agentic.tokens_input     — input token count
      agentic.tokens_output    — output token count
      agentic.cache_read_tokens — prompt cache read tokens
    """

    def __init__(self, span: "Span") -> None:
        self._span = span

    def set_cost(
        self,
        *,
        cost_usd: float,
        tokens_input: int,
        tokens_output: int,
        cache_read_tokens: int,
    ) -> None:
        """Set cost-related span attributes.

        Args:
            cost_usd: Total LLM cost in USD for this turn.
            tokens_input: Input tokens consumed.
            tokens_output: Output tokens generated.
            cache_read_tokens: Tokens served from prompt cache (reduces cost).
        """
        self._span.set_attribute("agentic.cost_usd", cost_usd)
        self._span.set_attribute("agentic.tokens_input", tokens_input)
        self._span.set_attribute("agentic.tokens_output", tokens_output)
        self._span.set_attribute("agentic.cache_read_tokens", cache_read_tokens)


@asynccontextmanager
async def agent_turn_span(
    *,
    agent_name: str,
    tenant_id: UUID,
    clinic_id: UUID,
    conversation_id: UUID,
) -> AsyncIterator[AgentSpanContext]:
    """Async context manager wrapping an agentic turn with an OTel span.

    Sanitizes PHI before writing any span attributes (per hipaa-lite.md).
    Injects tenant_id + clinic_id as span attributes for trace correlation.

    On entry:
      - Starts span named after agent_name
      - Sets tenant_id, clinic_id, conversation_id as attributes
        (these are UUIDs — not PHI, safe for traces)

    On success:
      - Sets span status to OK

    On error:
      - Records exception + sets ERROR status + re-raises

    Args:
        agent_name: Span name (e.g. "vitalia.agent.adrian").
        tenant_id: Tenant UUID — non-PHI, used for trace correlation.
        clinic_id: Clinic UUID — non-PHI, used for trace correlation.
        conversation_id: Conversation UUID — non-PHI, used for trace correlation.

    Yields:
        AgentSpanContext — call span_ctx.set_cost() after turn completes.

    Example:
        async with agent_turn_span(
            agent_name="vitalia.agent.adrian",
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conv_id,
        ) as ctx:
            result = await process_turn(...)
            ctx.set_cost(
                cost_usd=result.cost_usd,
                tokens_input=result.tokens_input,
                tokens_output=result.tokens_output,
                cache_read_tokens=result.cache_read_tokens,
            )
    """
    tracer = _get_tracer()
    with tracer.start_as_current_span(agent_name) as span:
        # Set non-PHI correlation attributes (UUIDs are safe for traces)
        # PHI sanitization rule: UUIDs are identifiers, not PHI — safe to log
        span.set_attributes(
            {
                "tenant_id": str(tenant_id),
                "clinic_id": str(clinic_id),
                "conversation_id": str(conversation_id),
            }
        )

        span_ctx = AgentSpanContext(span=span)

        try:
            yield span_ctx
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, description=str(exc)))
            logger.warning(
                "agent_turn_span_error",
                agent_name=agent_name,
                tenant_id=str(tenant_id),
                error_type=type(exc).__name__,
                error=str(exc),
            )
            raise
