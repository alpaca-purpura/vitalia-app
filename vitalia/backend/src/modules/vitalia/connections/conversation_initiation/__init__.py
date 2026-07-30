# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Vitalia conversation initiation registry (proactive outbound dispatch)."""

from .registry import (
    CONVERSATION_INITIATION_REGISTRY,
    ConversationInitiationDef,
    get_conversation_initiation,
    list_conversation_initiations,
)

__all__ = (
    "CONVERSATION_INITIATION_REGISTRY",
    "ConversationInitiationDef",
    "get_conversation_initiation",
    "list_conversation_initiations",
)
