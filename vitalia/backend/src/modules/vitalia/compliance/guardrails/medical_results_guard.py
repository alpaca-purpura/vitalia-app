# cap: compliance.compliance-hipaa-lite-audit
# story-origin: TBD
"""MedicalResultsChannelGuard — channel guard for PHI transmission.

Implements vitalia/.claude/rules/hipaa-lite.md § Voice patterns:
  "NUNCA discutir diagnósticos/resultados por canales no-encriptados
   (WhatsApp tier free, SMS)."
  "Si paciente pregunta resultados → bot deriva a portal seguro autenticado."

Used by Adrián sales_agent tools BEFORE any outbound message send.
Delegates channel validation to VitaliaComplianceAdapter (never mirrors
ComplianceService per .claude/rules/anti-duplication.md).

downstream-regression-na: brand-local medical guard for vitalia
"""

from __future__ import annotations

import structlog

from src.modules.vitalia.compliance.application.compliance_service_adapter import (
    VitaliaComplianceAdapter,
)

logger = structlog.get_logger()


class MedicalResultsChannelGuard:
    """Guard that blocks PHI result transmission on unencrypted channels.

    Adrián MUST call this guard before every outbound send:

        guard = MedicalResultsChannelGuard()
        guard.validate(message=message_text, channel=channel_slug)
        # If no exception → proceed with send
        # If BlockedChannelError → respond with portal redirect

    Voice pattern enforcement:
        medical_results_only_in_portal: true
        → portal_secure / whatsapp_business_encrypted / https_api: ALLOWED
        → whatsapp_free / sms / email_plaintext: BLOCKED

    The error message included in BlockedChannelError is Spanish neutro
    per .claude/rules/spanish-text.md — NO voseo.
    """

    def __init__(self) -> None:
        """Initialize with a VitaliaComplianceAdapter instance."""
        self._adapter = VitaliaComplianceAdapter()

    def validate(self, message: str, channel: str) -> bool:
        """Validate that a message can be sent on the given channel.

        Args:
            message: The message text to send (reserved for future content-scan).
            channel: Channel slug (e.g. 'whatsapp_free', 'portal_secure').

        Returns:
            True if the channel is allowed for PHI.

        Raises:
            BlockedChannelError: If the channel is in BLOCKED_PHI_CHANNELS.
        """
        logger.debug(
            "medical_results_guard.validate",
            channel=channel,
        )
        return self._adapter.validate_outbound_message(
            message=message,
            channel=channel,
        )
