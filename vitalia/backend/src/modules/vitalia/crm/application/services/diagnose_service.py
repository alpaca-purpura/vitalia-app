# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""DiagnoseService — deterministic frozen lead diagnosis.

Application layer — pure business logic, no DB access.

Derives a recommendation for a frozen lead based on:
  - frozen_reason (inactividad_lead | sin_respuesta_presupuesto | agente_trabado)
  - stage at freeze
  - buying_signals present

Pattern references engine closer_studio.diagnose (NON-import — reimplemented
brand-local per 03-arch.md § 2: auth/runtime mismatch prevents direct engine use).

Lift candidate: per anti-duplication.md, do NOT lift to core until 2nd brand needs it.
"""

from __future__ import annotations

import structlog

from src.modules.vitalia.crm.domain.lead import Lead

logger = structlog.get_logger()


class DiagnoseService:
    """Deterministic rule-based diagnosis for frozen leads.

    Returns a recommendation (Spanish neutro, NON-PHI) and suggested action.
    No ML. All rules deterministic from frozen_reason + stage + signals.
    """

    def diagnose(self, lead: Lead) -> tuple[str, str]:
        """Diagnose a frozen lead and return recommendation.

        Args:
            lead: Lead domain entity (should have is_frozen=True or stage='decidio_no').

        Returns:
            Tuple of (recommendation_es: str, suggested_action: str).
            suggested_action ∈ {reactivate, schedule_call, send_discount, wait}.

        Notes:
            recommendation_es: Spanish neutro LatAm, sin voseo.
            Non-PHI: based on commercial stage/signals, never clinical data.
        """
        reason = lead.frozen_reason or ""
        stage = lead.stage
        signals = set(lead.buying_signals)
        score = lead.score

        # decidio_no: gentle reintroduction via Camila 90d cohort
        if stage == "decidio_no":
            return (
                "El prospecto decidió no continuar. "
                "Se recomienda incluirlo en la campaña de reenganche de 90 días de Camila.",
                "wait",
            )

        # High-intent signals present: schedule a call
        if "presupuesto_ok" in signals or "consulto_fecha" in signals:
            return (
                "El prospecto mostró interés en precio o fecha. Comunícate directamente para confirmar disponibilidad.",
                "schedule_call",
            )

        # Stalled at plan stage with good score: offer discount to close
        if stage == "plan_presentado" and score >= 60:
            return (
                "El plan fue presentado pero no avanzó. "
                "Considera ofrecer un descuento de presentación o un plan de pago.",
                "send_discount",
            )

        # Agent stuck (no response from agent side)
        if reason == "agente_trabado":
            return (
                "El agente Adrián no logró avanzar la conversación. "
                "Tomar el control manualmente y retomar el contacto.",
                "reactivate",
            )

        # No response from lead: standard reactivation
        if reason == "inactividad_lead":
            return (
                "El prospecto no respondió en el tiempo esperado. Envía un mensaje de seguimiento personalizado.",
                "reactivate",
            )

        # Budget not confirmed: re-present offer
        if reason == "sin_respuesta_presupuesto":
            return (
                "El prospecto no confirmó el presupuesto. Re-presenta la propuesta con beneficios concretos.",
                "reactivate",
            )

        # Default: standard reactivation
        logger.debug(
            "diagnose_default_recommendation",
            lead_id=str(lead.id),
            stage=stage,
            reason=reason,
        )
        return (
            "Reinicia el contacto con un mensaje personalizado sobre el tratamiento de interés.",
            "reactivate",
        )
