# cap: inbox.adrian-inbox
"""PhiChannelPolicy — Vitalia inbox PHI channel compliance policy.

Implements the CompliancePolicy Protocol from luana_core_compliance.
Blocks outbound messages containing clinical PHI keywords on unencrypted
channels (WhatsApp free tier, SMS) per hipaa-lite.md RN-7 + SC-3/AC-9.

Design decisions:
- EXTENSION of engine CompliancePolicy Protocol (not a mirror of the engine).
- `identifier` param carries the outbound message text (adapter reuse of the
  Protocol field — the Protocol uses `identifier` for phone/channel identifier;
  in the inbox send path this carries the message body for PHI heuristic check).
- Unencrypted channels in scope: 'whatsapp', 'sms' (tier free). Instagram DMs
  are NOT in this set (end-to-end encrypted in Meta's infrastructure).
- PHI heuristic is keyword-based (last-resort net, not the primary guard;
  the primary guard is the sales_agent voice instruction not to discuss results).
- On BLOCK: caller is responsible for redirecting to portal with microcopy SSoT.

References:
- 03-arch-be.md § 6.1 ComplianceService un-stub
- hipaa-lite.md § Voice patterns en sales_agent vitalia
- core/luana-core-compliance/src/luana_core_compliance/application/compliance_service.py

downstream-regression-na: brand-local vitalia inbox policy (no cross-module consumers)
"""

from __future__ import annotations

from uuid import UUID

import structlog
from luana_core_compliance.domain.check_result import CheckResult

logger = structlog.get_logger(__name__)

# PHI clinical result keywords (Spanish LatAm — heuristic detection, not exhaustive).
# The primary safeguard is the agent voice instruction (system_instruction → sales agent).
# This policy is the infrastructure-level fallback net for outbound messages.
_PHI_RESULT_KEYWORDS: frozenset[str] = frozenset(
    {
        "diagnóstico",
        "diagnostico",
        "resultado",
        "resultados",
        "estudio",
        "estudios",
        "laboratorio",
        "biopsia",
        "análisis",
        "analisis",
        "informe",
        "histología",
        "histologia",
        "patología",
        "patologia",
        "tratamiento médico",
        "tratamiento medico",
        "medicación",
        "medicacion",
        "dosis",
        "prescripción",
        "prescripcion",
        "pronóstico",
        "pronostico",
    }
)

# Unencrypted channels where PHI clinical data MUST NOT be transmitted (RN-7).
# WhatsApp free tier (non-WABA) and SMS are the primary risk vectors in LatAm.
_UNENCRYPTED_CHANNELS: frozenset[str] = frozenset({"whatsapp", "sms"})

_PORTAL_REDIRECT_MICROCOPY = (
    "Por seguridad, tus resultados y datos clínicos están disponibles en tu portal. Ingresa en: {portal_link}"
)


class PhiChannelPolicy:
    """Block outbound messages with PHI clinical keywords on unencrypted channels.

    Implements CompliancePolicy Protocol from luana_core_compliance.
    Used by ComplianceService in the inbox send path (Slice 2 un-stub).

    The `identifier` parameter (per Protocol) carries the outbound message body
    text in the inbox context. This is a deliberate reuse of the Protocol's
    generic `identifier` field to pass the message content for PHI heuristics.

    Channels in scope: 'whatsapp', 'sms'. Instagram is NOT restricted
    (Meta E2E encrypted; different risk profile).
    """

    name: str = "phi_unencrypted_channel"

    async def evaluate(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        identifier: str,
        campaign_id: UUID | None,
    ) -> CheckResult:
        """Evaluate PHI channel policy for an outbound message.

        Args:
            tenant_id: Root tenant UUID (unused — channel + content check only).
            lead_id: Lead UUID (unused — channel + content check only).
            channel: Outbound channel slug ('whatsapp', 'sms', 'web', 'email', ...).
            identifier: Outbound message body text (repurposed from Protocol generic field).
            campaign_id: Campaign UUID (unused).

        Returns:
            CheckResult(allowed=False, failed_policy='phi_unencrypted_channel')
            if the channel is unencrypted AND the message text contains PHI keywords.
            CheckResult(allowed=True) otherwise.
        """
        if channel not in _UNENCRYPTED_CHANNELS:
            return CheckResult(allowed=True)

        message_lower = identifier.lower()
        matched_keyword = next(
            (kw for kw in _PHI_RESULT_KEYWORDS if kw in message_lower),
            None,
        )

        if matched_keyword is None:
            return CheckResult(allowed=True)

        logger.info(
            "phi_channel_policy.blocked",
            channel=channel,
            matched_keyword=matched_keyword,
            tenant_id=str(tenant_id),
        )

        return CheckResult(
            allowed=False,
            failed_policy="phi_unencrypted_channel",
            reason=(
                f"Contenido clínico detectado ('{matched_keyword}') en canal no cifrado ({channel}). "
                f"Derivar al portal seguro. {_PORTAL_REDIRECT_MICROCOPY}"
            ),
            evidence={
                "channel": channel,
                "matched_keyword": matched_keyword,
                "redirect_action": "portal",
            },
        )
