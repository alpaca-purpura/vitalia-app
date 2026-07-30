# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""Marketing domain exceptions for vitalia brand."""

from __future__ import annotations


class MarketingDomainError(Exception):
    """Base exception for marketing domain errors."""


class InvalidStateTransitionError(MarketingDomainError):
    """Raised when a state transition is not allowed for current status."""

    def __init__(self, current_status: str, attempted_action: str) -> None:
        super().__init__(f"No se puede ejecutar '{attempted_action}' cuando el estado es '{current_status}'.")
        self.current_status = current_status
        self.attempted_action = attempted_action


class ExpiredRecommendationError(MarketingDomainError):
    """Raised when attempting to act on an expired recommendation."""

    def __init__(self) -> None:
        super().__init__("La recomendación ha expirado y no puede ser aprobada o rechazada.")


class UndoWindowExpiredError(MarketingDomainError):
    """Raised when the undo window (5 min after approval) has passed."""

    def __init__(self) -> None:
        super().__init__("El período de deshacer ha expirado. No es posible revertir la aprobación.")
