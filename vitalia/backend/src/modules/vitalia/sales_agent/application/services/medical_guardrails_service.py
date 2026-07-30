# cap: sales_agent.medical-guardrails
# story-origin: TBD
"""Vitalia Adrián MedicalGuardrailsService — orchestrates 4 guardrails.

Story T-ag-tools-2 — R23 production_code=true. Opus 4.7 EXCLUSIVE.

Per 03-arch-be.md § 10 MODIFIED + 03-arch.md § 3.7 + 02-design-agentic.md § 2.7.

This service is the façade that the sales_agent runtime calls before/after
each LLM call to enforce the 4 medical guardrails:

  1. ``prevent_diagnosis_disclosure_on_unencrypted_channel`` — blocks PHI
     diagnosis or prescription text on whatsapp_free / sms / email_plaintext
     channels (HIPAA-lite cardinal).
  2. ``redirect_results_to_portal`` — substitutes medical results text in
     outbound message with portal-redirect Spanish neutral phrasing.
  3. ``block_unauthorized_phi_access`` — RBAC role check (doctor / nurse /
     admin_clinic CAN access PHI fields; other roles cannot).
  4. ``validate_compliance_outbound`` — wraps engine
     ``luana_core_compliance.ComplianceService.validate_outbound_message``
     for the final outbound gate.

Per .claude/rules/anti-duplication.md § Regla cardinal:
  - ``ComplianceService`` is consumed from ``luana_core_compliance`` — NEVER mirrored.
  - ``sanitize_phi_payload`` is consumed from
    ``vitalia.compliance.compliance_service_adapter`` (Story 11 cement).
  - ``BlockedChannelError`` is consumed from same adapter (Story 11 cement).
  - Regex/LLM detection for diagnosis/prescription lives in
    ``vitalia.agentic.guardrails.*`` (Story 11 cement) — consumed via the
    ``compliance.guardrails.*`` re-export shim layer (this story).

Per vitalia/.claude/rules/hipaa-lite.md:
  - Every PHI access produces an audit log row (sync write).
  - Role check enforced at field level (not row level — row-level filter is
    repo responsibility).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

import structlog

from src.modules.vitalia.compliance.application.compliance_service_adapter import (
    BlockedChannelError,
    VitaliaComplianceAdapter,
)
from src.modules.vitalia.compliance.domain.phi_fields import (
    ALLOWED_PHI_CHANNELS,
    PHI_FIELDS_PATIENT,
    PHI_FIELDS_TOP_LEVEL,
)

logger = structlog.get_logger(__name__)


# ── PHI-authorized roles (per hipaa-lite.md § Access control) ───────────

PHI_AUTHORIZED_ROLES: frozenset[str] = frozenset(
    {"doctor", "nurse", "admin_clinic"},
)

# Channels considered safe for PHI per allowed list (defense-in-depth alongside
# adapter blocked-list — fail-closed semantics for unknown channels).
PHI_SAFE_CHANNELS: frozenset[str] = ALLOWED_PHI_CHANNELS


# ── Verdict dataclass ───────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ComplianceVerdict:
    """Result of an outbound compliance validation.

    ``allowed=False`` MUST be honored by caller (DO NOT send). Caller can
    fall back to ``alternative_action`` when present (typically a portal
    redirect text).
    """

    allowed: bool
    reason: str | None = None
    alternative_action: Literal["derive_portal", "escalate_operator", "regenerate"] | None = None


# ── Service ─────────────────────────────────────────────────────────────


class MedicalGuardrailsService:
    """Orchestrates the 4 vitalia medical guardrails for sales_agent runtime.

    Stateless — single instance per process is safe. Wraps existing
    compliance adapter + Story 11 guardrail callables.

    Caller pattern (in sales_agent runtime, BEFORE outbound send):
    ```
    guardrails = MedicalGuardrailsService()
    if not guardrails.prevent_diagnosis_disclosure_on_unencrypted_channel(message, channel):
        # Use alternative_action
        ...
    verdict = guardrails.validate_compliance_outbound(payload, channel)
    if not verdict.allowed:
        # Substitute with derive_portal message
        ...
    ```
    """

    def __init__(self, compliance_adapter: VitaliaComplianceAdapter | None = None) -> None:
        """Initialize with optional adapter (default uses module-level singleton).

        Args:
            compliance_adapter: ``VitaliaComplianceAdapter`` instance. When
                omitted, a fresh adapter is built (stateless — no resources to share).
        """
        self._adapter = compliance_adapter or VitaliaComplianceAdapter()

    # ── Guardrail 1 ────────────────────────────────────────────────────

    def prevent_diagnosis_disclosure_on_unencrypted_channel(
        self,
        message: str,
        channel: str,
    ) -> bool:
        """Return True iff the message+channel combination is SAFE.

        Returns ``False`` if the channel is in the blocked set (whatsapp_free,
        sms, email_plaintext) AND the message contains diagnosis-like text
        (regex on diagnosis verbs + condition nouns).

        Per .claude/rules/hipaa-lite.md § Voice patterns:
          "NUNCA discutir diagnósticos/resultados por canales no-encriptados."

        Detection is conservative — uses the existing Story 11 cement regex
        catalog from ``vitalia.agentic.guardrails.medical_safety_no_diagnosis``
        for the OUTPUT layer (LLM response).

        Args:
            message: Outbound text to validate.
            channel: Channel slug (e.g. 'whatsapp_free', 'portal_secure').

        Returns:
            True if safe to send. False if blocked (caller MUST use
            alternative action — typically derive to portal).
        """
        channel_lower = channel.lower()
        if channel_lower in PHI_SAFE_CHANNELS:
            return True

        # Lazy import to avoid module-load chains.
        from src.modules.vitalia.agentic.guardrails.medical_safety_no_diagnosis import (  # noqa: PLC0415
            fires_output_regex as fires_diagnosis_regex,
        )
        from src.modules.vitalia.agentic.guardrails.medical_safety_no_prescription import (  # noqa: PLC0415
            fires_output_regex as fires_prescription_regex,
        )

        has_diagnosis = fires_diagnosis_regex(message)
        has_prescription = fires_prescription_regex(message)

        if has_diagnosis or has_prescription:
            logger.warning(
                "vitalia.medical_guardrails.unencrypted_phi_disclosure_blocked",
                channel=channel,
                has_diagnosis=has_diagnosis,
                has_prescription=has_prescription,
            )
            return False

        return True

    # ── Guardrail 2 ────────────────────────────────────────────────────

    def redirect_results_to_portal(self, message: str) -> str:
        """Substitute medical-results phrasing with portal-redirect text.

        Detects sentences containing 'resultados' / 'lab' / 'imaging' /
        'biopsia' and replaces them with the canonical Spanish portal
        derive message (per slot 4 MEDICAL_SAFETY_RAILS).

        This is a deterministic regex substitution — NO LLM call. Caller
        is expected to apply this BEFORE outbound send when the source
        intent is sharing medical results via chat (which is forbidden
        on non-portal channels).

        Args:
            message: Original outbound message text.

        Returns:
            Sanitized message text. If no medical-results phrasing detected,
            returns the original string unchanged.
        """
        import re  # noqa: PLC0415 — local import keeps module import-light

        # Detect sentences with medical-results phrasing.
        results_pattern = re.compile(
            r"\b(?:resultados?\s+(?:de\s+)?(?:lab(?:oratorio)?|imagen|imaging|biopsia|análisis|estudio)"
            r"|reporte\s+médico"
            r"|tus?\s+(?:lab(?:oratorios?)?|análisis|estudios|imagenolog[ií]as?))\b",
            re.IGNORECASE,
        )

        if not results_pattern.search(message):
            return message

        # Replace with portal-redirect canonical text.
        portal_redirect = (
            "Por seguridad, los resultados los puedes ver en tu portal seguro. Te envío el enlace al portal."
        )

        # We do NOT try to mutate mid-sentence — return canonical replacement.
        logger.info("vitalia.medical_guardrails.results_redirected_to_portal")
        return portal_redirect

    # ── Guardrail 3 ────────────────────────────────────────────────────

    def block_unauthorized_phi_access(
        self,
        role: str,
        requested_field: str,
    ) -> bool:
        """Return True iff the role IS authorized to access the field.

        Per .claude/rules/hipaa-lite.md § Access control (RBAC strict):
          "Roles permitidos PHI: doctor, nurse, admin_clinic. Otros (marketing,
           sales) NUNCA ven PHI."

        Args:
            role: Caller role slug (e.g. 'doctor', 'sales', 'marketing').
            requested_field: Canonical PHI field name (e.g. 'diagnosis',
                'patient.dni'). Non-PHI fields return True (access allowed).

        Returns:
            True if access is authorized (role in PHI_AUTHORIZED_ROLES OR
            field is not PHI). False if access is blocked.
        """
        # Check if field is PHI (either top-level or nested patient.*)
        is_phi = self._is_phi_field(requested_field)

        if not is_phi:
            # Non-PHI field — open access
            return True

        # PHI field — require authorized role
        allowed = role.lower() in PHI_AUTHORIZED_ROLES
        if not allowed:
            logger.warning(
                "vitalia.medical_guardrails.unauthorized_phi_access_blocked",
                role=role,
                field=requested_field,
            )
        return allowed

    @staticmethod
    def _is_phi_field(field_name: str) -> bool:
        """Return True iff the field name matches a canonical PHI field."""
        if field_name in PHI_FIELDS_TOP_LEVEL:
            return True
        if field_name.startswith("patient."):
            subfield = field_name.removeprefix("patient.")
            return subfield in PHI_FIELDS_PATIENT
        return False

    # ── Guardrail 4 ────────────────────────────────────────────────────

    def validate_compliance_outbound(
        self,
        payload: dict[str, Any],
        channel: str,
        tenant_id: UUID | None = None,
    ) -> ComplianceVerdict:
        """Final outbound compliance gate per HIPAA-lite cardinal.

        Wraps :class:`VitaliaComplianceAdapter.validate_outbound_message`
        (Story 11 cement) and adds payload PHI scan defense-in-depth.

        Returns a :class:`ComplianceVerdict` with ``allowed`` + optional
        ``alternative_action`` hint for caller.

        Args:
            payload: Outbound message payload dict.
            channel: Channel slug.
            tenant_id: Optional tenant UUID for audit context.

        Returns:
            ComplianceVerdict(allowed=True) on pass.
            ComplianceVerdict(allowed=False, reason="...", alternative_action="derive_portal")
            on block.
        """
        message_text = str(payload.get("text", "") or payload.get("message", "") or "")

        try:
            self._adapter.validate_outbound_message(
                message=message_text,
                channel=channel,
                tenant_id=tenant_id,
            )
        except BlockedChannelError as exc:
            return ComplianceVerdict(
                allowed=False,
                reason=str(exc),
                alternative_action="derive_portal",
            )

        # Defense-in-depth: scan payload for PHI keys when channel not in allowed list
        if channel.lower() not in PHI_SAFE_CHANNELS:
            phi_keys = self._scan_payload_phi(payload)
            if phi_keys:
                logger.warning(
                    "vitalia.medical_guardrails.outbound_phi_keys_blocked",
                    channel=channel,
                    phi_keys=sorted(phi_keys),
                    tenant_id=str(tenant_id) if tenant_id else None,
                )
                return ComplianceVerdict(
                    allowed=False,
                    reason=(
                        f"Payload contiene campos PHI ({sorted(phi_keys)!r}) "
                        f"y el canal '{channel}' no es seguro para PHI."
                    ),
                    alternative_action="derive_portal",
                )

        return ComplianceVerdict(allowed=True)

    @staticmethod
    def _scan_payload_phi(payload: dict[str, Any]) -> set[str]:
        """Return the set of PHI keys found in payload (shallow + patient.* nested)."""
        found: set[str] = set()
        for key in payload:
            if key in PHI_FIELDS_TOP_LEVEL:
                found.add(key)
        patient = payload.get("patient")
        if isinstance(patient, dict):
            for key in patient:
                if key in PHI_FIELDS_PATIENT:
                    found.add(f"patient.{key}")
        return found


__all__ = [
    "PHI_AUTHORIZED_ROLES",
    "PHI_SAFE_CHANNELS",
    "ComplianceVerdict",
    "MedicalGuardrailsService",
]
