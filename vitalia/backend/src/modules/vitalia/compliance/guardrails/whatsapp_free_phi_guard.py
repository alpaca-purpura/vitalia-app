# cap: compliance.whatsapp-template-registry
# story-origin: TBD
"""WhatsAppFreePhiGuard — payload-level PHI scanner for WhatsApp free tier.

Complements MedicalResultsChannelGuard at the payload level:
blocks any message payload that contains known PHI field keys
from being sent via the WhatsApp free (unencrypted) channel.

Per vitalia/.claude/rules/hipaa-lite.md:
  - PHI_FIELDS_TOP_LEVEL and nested patient.* fields are blocked on
    whatsapp_free / sms / email_plaintext channels.
  - Encrypted channels (portal_secure, whatsapp_business_encrypted, https_api)
    are allowed to carry PHI payloads.

Channel-level guard (MedicalResultsChannelGuard) blocks on channel type alone.
This guard adds PAYLOAD CONTENT scanning as defense-in-depth.

downstream-regression-na: brand-local WhatsApp PHI payload guard for vitalia
"""

from __future__ import annotations

from typing import Any

import structlog

from src.modules.vitalia.compliance.application.compliance_service_adapter import (
    BlockedChannelError,
)
from src.modules.vitalia.compliance.domain.phi_fields import (
    ALLOWED_PHI_CHANNELS,
    PHI_FIELDS_PATIENT,
    PHI_FIELDS_TOP_LEVEL,
)

logger = structlog.get_logger()


class WhatsAppFreePhiGuard:
    """Payload-level guard that scans message payloads for PHI field keys.

    Acts as defense-in-depth layer alongside MedicalResultsChannelGuard:
      1. If channel is in BLOCKED_PHI_CHANNELS: scan payload for PHI keys.
         Any PHI key found → BlockedChannelError.
      2. If channel is in ALLOWED_PHI_CHANNELS: pass through (encrypted).
      3. Unknown channel: conservative — treat as blocked.

    Usage in Adrián tools:
        guard = WhatsAppFreePhiGuard()
        guard.scan_payload(payload={"text": "...", "diagnosis": "..."}, channel="whatsapp_free")
        # Raises BlockedChannelError if PHI found on blocked channel
    """

    def scan_payload(
        self,
        payload: dict[str, Any],
        channel: str,
    ) -> bool:
        """Scan payload for PHI keys when on a blocked channel.

        Args:
            payload: Message payload dict to scan.
            channel: Channel slug.

        Returns:
            True if the payload may be sent on this channel.

        Raises:
            BlockedChannelError: If PHI fields detected on a blocked channel.
        """
        channel_lower = channel.lower()

        # Encrypted channels — PHI allowed
        if channel_lower in ALLOWED_PHI_CHANNELS:
            return True

        # For blocked (and unknown) channels: scan payload for PHI keys
        phi_keys_found = self._scan_for_phi(payload)

        if phi_keys_found:
            logger.warning(
                "whatsapp_free_phi_guard.phi_detected_in_payload",
                channel=channel,
                phi_keys=sorted(phi_keys_found),
            )
            raise BlockedChannelError(channel=channel)

        return True

    def _scan_for_phi(self, payload: dict[str, Any]) -> set[str]:
        """Return the set of PHI field keys found in the payload.

        Scans:
          - Top-level keys against PHI_FIELDS_TOP_LEVEL
          - Nested 'patient' dict keys against PHI_FIELDS_PATIENT

        Args:
            payload: Dict to scan (shallow — one level deep).

        Returns:
            Set of PHI field names found in the payload (empty if clean).
        """
        found: set[str] = set()

        # Top-level PHI fields
        for key in payload:
            if key in PHI_FIELDS_TOP_LEVEL:
                found.add(key)

        # Nested patient.* PHI fields
        patient_data = payload.get("patient")
        if isinstance(patient_data, dict):
            for key in patient_data:
                if key in PHI_FIELDS_PATIENT:
                    found.add(f"patient.{key}")

        return found
