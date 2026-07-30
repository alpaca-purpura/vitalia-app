# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""LangChain @tool — simulate_personality (Valeria wizard).

Wraps :class:`SimulatePersonalityService` (T-be-services-1 produced) which
provides:
  - Rate limit: 5 calls/min/tenant (Redis sliding window)
  - Cache: 10 min TTL per (profile_partial, scenario) combination
  - LLM call: engine LiteLLMService with role classifier nano (deepseek-v4-flash)

Per 03-arch-agentic.md § 4.1: cost typical $0.005-0.01 USD per call. Cache hits
bring marginal cost to ~$0 (cache_read_input_tokens dominate).

Per claude-api: cache_creation_input_tokens + cache_read_input_tokens logged
per LLM call by the engine ``BaseAgentCallbackHandler`` — silent invalidators
caught by ``ae_cache_hit_rate_smoke`` validator.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger()


class SimulatePersonalityInput(BaseModel):
    """Args schema for ``simulate_personality`` tool."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    tenant_id: UUID = Field(..., description="Tenant isolation identifier.")
    profile_partial: dict[str, Any] = Field(
        ...,
        description=(
            "Partial slot values defining the personality preview (clinic name, "
            "vertical, tone). Must be JSON-serializable. NEVER include PHI."
        ),
    )
    scenario: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description=("Scenario context for the sample (e.g. 'primera_respuesta', 'agendar_cita', 'objection_price')."),
    )


_service_factory: Any = None


def set_simulate_personality_service_factory(factory: Any) -> None:  # noqa: ANN401
    """Wire the service factory (called by FastAPI lifespan)."""
    global _service_factory  # noqa: PLW0603 — DI hook by design
    _service_factory = factory


def get_simulate_personality_service() -> Any:  # noqa: ANN401
    """Resolve the service factory. Raises if not wired."""
    if _service_factory is None:
        raise RuntimeError(
            "simulate_personality_service factory not wired — "
            "call set_simulate_personality_service_factory at FastAPI lifespan startup.",
        )
    return _service_factory()


@tool("simulate_personality", args_schema=SimulatePersonalityInput)
async def simulate_personality(
    tenant_id: UUID,
    profile_partial: dict[str, Any],
    scenario: str,
) -> str:
    """Generate a personality-aligned sample text for live wizard preview.

    Service handles cache + throttle. Returns a short summary of the sample
    plus a cache-hit indicator. The actual sample text is also surfaced via
    the tool message so the LangGraph supervisor can stream it as a
    ``voice_preview`` block to the FE.
    """
    service = get_simulate_personality_service()
    try:
        response = await service.simulate(
            profile_partial=profile_partial,
            scenario=scenario,
            tenant_id=tenant_id,
        )
    except Exception as exc:  # noqa: BLE001 — surface to LLM as error string
        # ThrottleExceededError is one of the expected exception types — caller
        # downstream interprets the message and asks the user to wait.
        logger.warning(
            "vitalia.copilot.tools.simulate_personality_failed",
            tenant_id=str(tenant_id),
            scenario=scenario,
            error=str(exc),
            error_class=type(exc).__name__,
        )
        return f"Error simulating personality: {type(exc).__name__}: {exc}"

    cache_str = " (from cache)" if getattr(response, "cache_hit", False) else ""
    sample_text = getattr(response, "sample_text", "")
    return f"Sample for '{scenario}'{cache_str}: {sample_text}"


__all__ = [
    "SimulatePersonalityInput",
    "get_simulate_personality_service",
    "set_simulate_personality_service_factory",
    "simulate_personality",
]
