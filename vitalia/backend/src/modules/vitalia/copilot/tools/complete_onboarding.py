# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""LangChain @tool — complete_onboarding (Valeria wizard).

Wraps :class:`CompleteOnboardingService` (T-be-services-1 produced) which:
  1. Loads the OnboardingDraft (tenant_id filter)
  2. Compiles full personality profile via engine personality_service
  3. Commits brand profile via brand_studio_port
  4. Marks tenant.is_onboarded = True
  5. Writes audit_log SYNC (HIPAA-lite cardinal — pre-response)
  6. Publishes TenantOnboardedEvent via outbox (USE_OUTBOX_PATTERN_COPILOT=True
     default per anti-default-flip-audit.md)

Per 05-guidelines.md § 1.10: audit_log written SYNC before response, never async
fire-forget.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger()


class CompleteOnboardingInput(BaseModel):
    """Args schema for ``complete_onboarding`` tool."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    draft_id: UUID = Field(..., description="OnboardingDraft to finalize.")
    tenant_id: UUID = Field(..., description="Tenant isolation identifier.")
    user_id: UUID = Field(..., description="User completing the onboarding.")


_service_factory: Any = None


def set_complete_onboarding_service_factory(factory: Any) -> None:  # noqa: ANN401
    """Wire the service factory (called by FastAPI lifespan)."""
    global _service_factory  # noqa: PLW0603 — DI hook by design
    _service_factory = factory


def get_complete_onboarding_service() -> Any:  # noqa: ANN401
    """Resolve the service factory. Raises if not wired."""
    if _service_factory is None:
        raise RuntimeError(
            "complete_onboarding_service factory not wired — "
            "call set_complete_onboarding_service_factory at FastAPI lifespan startup.",
        )
    return _service_factory()


@tool("complete_onboarding", args_schema=CompleteOnboardingInput)
async def complete_onboarding(
    draft_id: UUID,
    tenant_id: UUID,
    user_id: UUID,
) -> str:
    """Finalize the wizard onboarding: compile profile, commit brand, activate tenant.

    Service handles: compile_full → brand_studio commit → tenant activation →
    audit_log SYNC → outbox TenantOnboardedEvent.
    """
    service = get_complete_onboarding_service()
    try:
        response = await service.complete(
            draft_id=draft_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )
    except Exception as exc:  # noqa: BLE001 — surface to LLM as error string
        logger.warning(
            "vitalia.copilot.tools.complete_onboarding_failed",
            draft_id=str(draft_id),
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            error=str(exc),
            error_class=type(exc).__name__,
        )
        return f"Error completing onboarding: {type(exc).__name__}: {exc}"

    activated = getattr(response, "tenant_activated", False)
    redirect = getattr(response, "redirect_url", "/inbox")
    state = "activated" if activated else "pending"
    return f"Onboarding {state}. Redirect: {redirect}"


__all__ = [
    "CompleteOnboardingInput",
    "complete_onboarding",
    "get_complete_onboarding_service",
    "set_complete_onboarding_service_factory",
]
