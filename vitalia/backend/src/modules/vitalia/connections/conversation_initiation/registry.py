# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Conversation initiation registry (Vitalia proactive outbound dispatch).

Per `03-arch-be.md` § 6.4 — channel + template mapping for inbound /
outbound conversation kick-off:

- inbound:    ManyChat, WhatsApp Cloud API, Instagram DM, Web chat widget
- outbound:   scheduled-followup, reactivation-cron

Slice 1 (T-infra-2) ships ONLY `whatsapp_template_meta` slot with placeholder
handler (gated on side story for the real WhatsApp adapter). The Meta UTILITY
vs MARKETING distinction is encoded as `requires_opt_in_if_marketing=True` to
ensure the `ComplianceService` (engine `core/luana-core-compliance/`) auto-blocks
MARKETING categories without an opt-in row in `vitalia_marketing_consent`.

Slice 2 candidates: sms_twilio, email_sendgrid.
Slice 3 candidates: voice_call_agent_twilio.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Literal


def _conversation_not_implemented(initiation_id: str, side_story: str):
    """Build placeholder callable for conversation initiation handlers."""

    def _placeholder(*args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            f"vitalia.connections.conversation_initiation kind={initiation_id!r} "
            f"handler is a placeholder — real implementation lands in side story "
            f"{side_story!r}. T-infra-2 scope mounts the slot only."
        )

    return _placeholder


@dataclass(frozen=True)
class ConversationInitiationDef:
    """Metadata + handler for a Vitalia conversation initiation kind.

    Attributes:
        initiation_id: canonical slug
        kind: high-level family — `whatsapp_template | sms | email | voice_call`
        category: optional template category. For Meta WhatsApp templates this
                  must be one of `"UTILITY" | "MARKETING"` (None for non-template
                  channels). MARKETING requires opt-in per § 2.6 channel guards.
        requires_opt_in_if_marketing: enforces opt-in lookup before sending
                                      MARKETING templates (defense-in-depth on
                                      top of `core/luana-core-compliance/`).
        handler: callable. Slice 1 raises NotImplementedError.
        handler_ref: dotted path under `vitalia.connections.*` for documentation.
    """

    initiation_id: str
    kind: Literal["whatsapp_template", "sms", "email", "voice_call"]
    category: Literal["UTILITY", "MARKETING"] | None
    requires_opt_in_if_marketing: bool
    handler: Any
    handler_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


CONVERSATION_INITIATION_REGISTRY: dict[str, ConversationInitiationDef] = {
    "whatsapp_template_meta": ConversationInitiationDef(
        initiation_id="whatsapp_template_meta",
        kind="whatsapp_template",
        category=None,  # category resolved per-send at runtime (UTILITY or MARKETING)
        requires_opt_in_if_marketing=True,
        handler=_conversation_not_implemented(
            "whatsapp_template_meta",
            "vitalia-copilot-tools-impl (real WhatsApp adapter)",
        ),
        handler_ref="vitalia.connections.whatsapp.adapter:send_template",
        metadata={
            "channel_type": "whatsapp_business_api",
            "compliance_level": "hipaa_lite",  # per brand.yaml
        },
    ),
}


def get_conversation_initiation(initiation_id: str) -> ConversationInitiationDef | None:
    """Return the registered conversation initiation def or None if unknown."""
    return CONVERSATION_INITIATION_REGISTRY.get(initiation_id)


def list_conversation_initiations() -> tuple[str, ...]:
    """Return the tuple of registered initiation slugs (deterministic order)."""
    return tuple(CONVERSATION_INITIATION_REGISTRY.keys())


__all__: Iterable[str] = (
    "CONVERSATION_INITIATION_REGISTRY",
    "ConversationInitiationDef",
    "get_conversation_initiation",
    "list_conversation_initiations",
)
