# cap: agentic.medical-agentic-tools
# story-origin: TBD
"""ToolsStateService — vitalia inbox application layer.

Read-only service deriving tool states from offer.tools_enabled mapping.

PHI obligations (hipaa-lite.md § Regla cardinal):
1. tenant_id + clinic_id dual filter on conversation fetch
2. No PHI fields exposed (tools_enabled is configuration, not patient data)
3. No audit log required (read-only observability endpoint)

Per 03-arch-be.md § 6.9:
- Read offer.tools_enabled mapping (engine OfferTypePreset)
- Last-used timestamp from copilot_llm_call filter by (conversation_id, tool_name)
- Read-only: no mutation methods Slice 1

downstream-regression-na: brand-local vitalia inbox service
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
        ConversationRepository,
    )

logger = structlog.get_logger()

# Default tool names per arch spec §6.9 + offer preset mapping
_DEFAULT_TOOLS: list[tuple[str, str]] = [
    ("send_medical_summary", "Resumen médico"),
    ("schedule_appointment", "Agendar cita"),
    ("send_proactive_outbound", "Mensaje proactivo"),
    ("whisper_transcribe", "Transcripción de audio"),
    ("check_patient_history", "Historial del paciente"),
]


class ConversationNotFoundError(Exception):
    """Raised when conversation does not exist for tenant+clinic."""

    def __init__(self, conversation_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"Conversation {conversation_id} not found or access denied")
        self.conversation_id = conversation_id


@dataclass
class ToolStateItem:
    """Single tool state entry for UI consumption."""

    tool_name: str
    enabled: bool
    last_used_at: datetime | None
    display_name_es: str


@dataclass
class ToolsStateResult:
    """Result from ToolsStateService.get_tools_state()."""

    conversation_id: UUID
    tools: list[ToolStateItem]
    read_only: bool = True


class ToolsStateService:
    """Read-only service for tools state in a conversation.

    Derives tool states from offer.tools_enabled mapping (engine OfferTypePreset).
    Last-used timestamps from copilot_llm_call filter by (conversation_id, tool_name).

    Slice 1: read-only. No mutation methods exposed.
    PHI note: tools_enabled is configuration data, not patient PHI.
    """

    def __init__(
        self,
        *,
        conv_repo: ConversationRepository,
        llm_call_repo: object | None = None,
        offer_tools_enabled: dict[str, bool] | None = None,
    ) -> None:
        """Initialize ToolsStateService.

        Args:
            conv_repo: ConversationRepository (dual-filter enforced).
            llm_call_repo: Optional LLM call repository for last-used timestamps.
                           If None, last_used_at will be None for all tools.
            offer_tools_enabled: Optional dict mapping tool_name -> enabled.
                                 If None, all default tools are enabled.
        """
        self._conv_repo = conv_repo
        self._llm_call_repo = llm_call_repo
        self._offer_tools_enabled = offer_tools_enabled or {}

    def _is_tool_enabled(self, tool_name: str) -> bool:
        """Derive tool enabled state from offer.tools_enabled mapping.

        Defaults to True (all tools enabled) when offer_tools_enabled not provided.
        Per arch spec §6.9: read from OfferTypePreset.tools_enabled.
        """
        if not self._offer_tools_enabled:
            # No explicit mapping → all tools enabled (Slice 1 default)
            return True
        return self._offer_tools_enabled.get(tool_name, False)

    async def get_tools_state(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
    ) -> ToolsStateResult:
        """Get tools state for a conversation.

        PHI dual-filter: conv fetch includes tenant_id AND clinic_id.
        Read-only: no mutations. Last-used from copilot_llm_call if repo available.

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            conversation_id: Target conversation UUID.

        Returns:
            ToolsStateResult with tool list and read_only=True.

        Raises:
            ConversationNotFoundError: If conversation not found for tenant+clinic.
        """
        # Verify conversation exists (dual-filter applied by repo)
        conv = await self._conv_repo.get_by_id(
            id=conversation_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )
        if conv is None:
            raise ConversationNotFoundError(conversation_id)

        # Build tool state list from offer mapping
        tools: list[ToolStateItem] = []
        for tool_name, display_name_es in _DEFAULT_TOOLS:
            enabled = self._is_tool_enabled(tool_name)

            # Fetch last_used_at from copilot_llm_call if repo available
            last_used_at: datetime | None = None
            if self._llm_call_repo is not None and hasattr(self._llm_call_repo, "get_last_used_for_conversation_tool"):
                try:
                    last_used_at = await self._llm_call_repo.get_last_used_for_conversation_tool(
                        conversation_id=conversation_id,
                        tenant_id=tenant_id,
                        tool_name=tool_name,
                    )
                except Exception:
                    # Soft-fail: last_used_at unavailable (not critical)
                    logger.warning(
                        "tools_state.last_used_fetch_failed",
                        tool_name=tool_name,
                        conversation_id=str(conversation_id),
                    )

            tools.append(
                ToolStateItem(
                    tool_name=tool_name,
                    enabled=enabled,
                    last_used_at=last_used_at,
                    display_name_es=display_name_es,
                )
            )

        logger.debug(
            "tools_state.fetched",
            tenant_id=str(tenant_id),
            conversation_id=str(conversation_id),
            tools_count=len(tools),
        )

        return ToolsStateResult(
            conversation_id=conversation_id,
            tools=tools,
            read_only=True,
        )
