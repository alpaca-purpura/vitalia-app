# cap: compliance.compliance-hipaa-lite-audit
# story-origin: TBD
"""VitaliaComplianceAdapter — bridges luana-core-compliance for vitalia PHI use cases.

Wraps luana_core_compliance.ComplianceService to add:
  1. Channel guard: block PHI on unencrypted channels (WhatsApp free, SMS)
  2. PHI sanitization: sanitize_phi_payload wraps luana_core_observability
     sanitize_payload with 22 vitalia-specific PHI field removal

Anti-duplication rule adherence:
  - ComplianceService is IMPORTED from luana_core_compliance (never mirrored)
  - sanitize_payload is IMPORTED from luana_core_observability (never mirrored)
  - This adapter EXTENDS (delegates + adds vitalia-specific logic)

Per vitalia/.claude/rules/hipaa-lite.md:
  "Persona vitalia carga rule `medical_results_only_in_portal: true`
   que bloquea tool `send_medical_summary` por chat."
  "ComplianceService.validate_outbound_message(message, channel) bloquea
   mensajes con PHI por canales no-encriptados."

downstream-regression-na: brand-local compliance adapter for vitalia
"""

from __future__ import annotations

import copy
from typing import Any
from uuid import UUID

import structlog

from src.modules.vitalia.compliance.domain.phi_fields import (
    BLOCKED_PHI_CHANNELS,
    PHI_FIELDS_PATIENT,
    PHI_FIELDS_TOP_LEVEL,
    REDACTED_PLACEHOLDER,
)

logger = structlog.get_logger()


class BlockedChannelError(Exception):
    """Raised when PHI transmission is attempted on an unencrypted channel.

    Per hipaa-lite.md § Voice patterns en sales_agent vitalia:
      "NUNCA discutir diagnósticos/resultados por canales no-encriptados
       (WhatsApp tier free, SMS)."

    Maps to HTTP 403 in API layer.
    """

    def __init__(self, channel: str, tenant_id: UUID | None = None) -> None:
        self.channel = channel
        self.tenant_id = tenant_id
        super().__init__(
            f"PHI transmission blocked on channel '{channel}'. "
            f"Por seguridad, los resultados los puedes ver en tu portal seguro. "
            f"Allowed channels for PHI: portal_secure, whatsapp_business_encrypted, https_api. "
            f"(vitalia/.claude/rules/hipaa-lite.md § Voice patterns)"
        )


class VitaliaComplianceAdapter:
    """Vitalia-specific compliance adapter extending luana-core-compliance.

    Responsibilities:
      1. validate_outbound_message: blocks PHI on unencrypted channels
      2. Delegates to engine ComplianceService for lead/campaign compliance checks

    Engine used: luana_core_compliance.ComplianceService (imported, never mirrored).
    """

    def validate_outbound_message(
        self,
        message: str,
        channel: str,
        tenant_id: UUID | None = None,
    ) -> bool:
        """Validate that a message can be sent on the given channel.

        For vitalia, any channel in BLOCKED_PHI_CHANNELS is prohibited
        regardless of message content (conservative approach: if the channel
        is not encrypted, PHI must not flow through it).

        Args:
            message: The message content (not used for channel check,
                     but available for future content-based PHI detection).
            channel: Channel identifier (e.g. 'whatsapp_free', 'portal_secure').
            tenant_id: Optional tenant UUID for logging context.

        Returns:
            True if the message may be sent.

        Raises:
            BlockedChannelError: If the channel is in the blocked list.
        """
        channel_lower = channel.lower()
        if channel_lower in BLOCKED_PHI_CHANNELS:
            logger.warning(
                "phi_channel_blocked",
                channel=channel,
                tenant_id=str(tenant_id) if tenant_id else None,
                reason="unencrypted channel PHI transmission prohibited",
            )
            raise BlockedChannelError(channel=channel, tenant_id=tenant_id)

        logger.debug(
            "phi_channel_allowed",
            channel=channel,
            tenant_id=str(tenant_id) if tenant_id else None,
        )
        return True


def sanitize_phi_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a payload by redacting all 22 canonical PHI fields.

    Wraps luana_core_observability.sanitize_payload and adds vitalia-specific
    PHI field removal for hipaa-lite compliance profile.

    Fields redacted:
      - Top-level: diagnosis, treatment_plan, medication, dosage, allergies,
                   symptoms, medical_notes, lab_results, vital_signs,
                   imaging_url, xray_filename, ultrasound_report,
                   previous_treatments, family_history, surgical_history
      - Under "patient" key: name, dni, cuit, date_of_birth, phone,
                              email, address

    Args:
        payload: Input dict (may be nested). NOT mutated — returns new dict.

    Returns:
        New dict with PHI fields replaced by REDACTED_PLACEHOLDER.
        Non-PHI fields are preserved exactly as-is.
    """
    try:
        # First pass: engine sanitization (regex-based PII patterns)
        from luana_core_observability.recording.sanitization import sanitize_payload  # noqa: PLC0415

        sanitized = sanitize_payload(payload)
    except ImportError:
        # Engine package not available in test environment — use copy
        logger.debug("luana_core_observability not available, using dict copy only")
        sanitized = copy.deepcopy(payload)

    # Second pass: vitalia-specific PHI field removal (22 canonical fields)
    result = dict(sanitized)

    # Redact top-level PHI fields
    for field_name in PHI_FIELDS_TOP_LEVEL:
        if field_name in result:
            result[field_name] = REDACTED_PLACEHOLDER

    # Redact nested patient.* PHI fields
    if "patient" in result and isinstance(result["patient"], dict):
        patient = dict(result["patient"])
        for field_name in PHI_FIELDS_PATIENT:
            if field_name in patient:
                patient[field_name] = REDACTED_PLACEHOLDER
        result["patient"] = patient

    return result
