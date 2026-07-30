# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""CRM domain exceptions — funnel-specific errors.

Domain layer — pure Python. No framework imports.

StaleStateError: raised when optimistic lock detects version mismatch (SC-5).
  Maps to 409 Conflict at API layer (T-BE-2 wires the HTTP mapping).

InvalidTransitionError: raised when a stage transition is not allowed by
  the STAGE_MACHINE (e.g., interesado → plan_presentado = skip).
  Maps to 422 Unprocessable Entity with allowed_next in body.

ManualReservadoForbiddenError: raised when operator tries to manually set
  reservado stage (only webhook is allowed, RN-4).
  Maps to 403 Forbidden.
"""

from __future__ import annotations


class StaleStateError(Exception):
    """Raised when optimistic lock detects a version mismatch (SC-5).

    Indicates the lead was modified concurrently between read and write.
    Service layer catches this and re-raises for the API to map to 409.
    """

    def __init__(
        self,
        lead_id: object,
        expected_version: int,
        *,
        message: str | None = None,
    ) -> None:
        """Initialize StaleStateError.

        Args:
            lead_id: UUID of the lead that had a version conflict.
            expected_version: The version the caller expected.
            message: Optional custom message.
        """
        self.lead_id = lead_id
        self.expected_version = expected_version
        default_msg = (
            f"Lead {lead_id} stage update conflict: "
            f"expected version {expected_version} but row was already updated. "
            "Reload and retry."
        )
        super().__init__(message or default_msg)


class InvalidTransitionError(Exception):
    """Raised when a funnel stage transition is not permitted by STAGE_MACHINE.

    API layer maps to 422 with body: {"detail": "...", "allowed_next": [...]}
    """

    def __init__(
        self,
        from_stage: str,
        to_stage: str,
        allowed_next: list[str],
        *,
        message: str | None = None,
    ) -> None:
        """Initialize InvalidTransitionError.

        Args:
            from_stage: Current lead stage.
            to_stage: Attempted target stage.
            allowed_next: Stages that ARE allowed from from_stage.
            message: Optional custom message.
        """
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.allowed_next = allowed_next
        default_msg = f"Transición inválida: {from_stage} → {to_stage}. Etapas permitidas: {allowed_next}"
        super().__init__(message or default_msg)


class ManualReservadoForbiddenError(Exception):
    """Raised when operator attempts to manually set reservado stage (RN-4).

    reservado can ONLY be set via webhook (payment confirmation).
    API layer maps to 403 Forbidden.
    """

    def __init__(self, *, message: str | None = None) -> None:
        default_msg = (
            "La etapa 'Reservado' solo puede establecerse mediante confirmación de pago. "
            "No se puede asignar manualmente."
        )
        super().__init__(message or default_msg)


class ReasonRequiredError(Exception):
    """Raised when a stage transition skip or backward requires a reason but none provided.

    Jumps (non-adjacent forward) and backward transitions require a reason
    to be submitted for the override context (RN-4.1).
    API layer maps to 400 Bad Request.
    """

    def __init__(self, *, message: str | None = None) -> None:
        default_msg = "Se requiere una razón para este cambio de etapa. Por favor ingresa un motivo."
        super().__init__(message or default_msg)
