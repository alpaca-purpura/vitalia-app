# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""LangChain @tool — confirm_slot (Valeria wizard).

Wraps :meth:`OnboardingDraftService.update_slot` (T-be-services-1 produced) to
mark a wizard slot as confirmed by the user.

Per design § 1.2 wizard state machine: user confirmation flips the slot's
``source`` from ``"extracted"`` → ``"user_text"`` (or ``"user_correction"`` if
the user typed a different value than what was extracted), sets
``confirmed_at`` to UTC now, and bumps confidence to 1.0.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Union
from uuid import UUID

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

logger = structlog.get_logger()


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


class ConfirmSlotInput(BaseModel):
    """Args schema for ``confirm_slot`` tool."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    draft_id: UUID = Field(..., description="OnboardingDraft to update.")
    tenant_id: UUID = Field(..., description="Tenant isolation identifier.")
    slot_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Dot-notation slot identifier (e.g. 'tenant.name', 'tenant.vertical').",
    )
    value: Union[str, dict, None] = Field(  # noqa: UP007 — Pydantic JSON-schema friendly
        ...,
        description="Confirmed value (string for simple slots, dict for compound slots, None to clear).",
    )
    source: Literal["user_text", "user_correction"] = Field(
        default="user_text",
        description=(
            "How the user supplied the value: 'user_text' for direct entry, "
            "'user_correction' if the user changed a previously extracted value."
        ),
    )


_service_factory: Any = None


def set_confirm_slot_service_factory(factory: Any) -> None:  # noqa: ANN401
    """Wire the service factory (called by FastAPI lifespan)."""
    global _service_factory  # noqa: PLW0603 — DI hook by design
    _service_factory = factory


def get_onboarding_draft_service() -> Any:  # noqa: ANN401
    """Resolve the service factory. Raises if not wired."""
    if _service_factory is None:
        raise RuntimeError(
            "onboarding_draft_service factory not wired — "
            "call set_confirm_slot_service_factory at FastAPI lifespan startup.",
        )
    return _service_factory()


@tool("confirm_slot", args_schema=ConfirmSlotInput)
async def confirm_slot(
    draft_id: UUID,
    tenant_id: UUID,
    slot_id: str,
    value: Union[str, dict, None],  # noqa: UP007 — Pydantic JSON-schema friendly
    source: str = "user_text",
) -> str:
    """Persist a user-confirmed slot value to the wizard draft.

    Bumps confidence to 1.0, sets ``confirmed_at`` to UTC now, and persists
    via the draft repository (tenant_id-filtered).
    """
    service = get_onboarding_draft_service()
    new_slot = WizardSlot(
        slot_id=slot_id,
        value=value,
        confidence=1.0,
        confirmed_at=_utc_now(),
        source=source,
    )
    try:
        await service.update_slot(
            draft_id=draft_id,
            tenant_id=tenant_id,
            slot_id=slot_id,
            new_slot=new_slot,
        )
    except Exception as exc:  # noqa: BLE001 — surface to LLM as error string
        logger.warning(
            "vitalia.copilot.tools.confirm_slot_failed",
            draft_id=str(draft_id),
            tenant_id=str(tenant_id),
            slot_id=slot_id,
            error=str(exc),
        )
        return f"Error confirming slot {slot_id}: {type(exc).__name__}"

    return f"Slot {slot_id} confirmed. Draft: {draft_id}"


__all__ = [
    "ConfirmSlotInput",
    "confirm_slot",
    "get_onboarding_draft_service",
    "set_confirm_slot_service_factory",
]
