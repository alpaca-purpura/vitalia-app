# cap: fidelizacion.re-engagement
# story-origin: TBD
"""Resultado del intento de re-engagement — value object StrEnum."""

from enum import StrEnum


class ReEngagementOutcome(StrEnum):
    """Resultado del evento de re-engagement enviado al paciente.

    - SENT: mensaje enviado, sin respuesta aún
    - RESPONDED: paciente respondió
    - RESCHEDULED: paciente reagendó cita
    - DECLINED: paciente declinó explícitamente
    - NOT_RESPONSIVE: sin respuesta tras reintentos
    - OPTED_OUT: paciente se dio de baja de comunicaciones
    - FAILED_SENDING: error técnico en envío
    """

    SENT = "sent"
    RESPONDED = "responded"
    RESCHEDULED = "rescheduled"
    DECLINED = "declined"
    NOT_RESPONSIVE = "not_responsive"
    OPTED_OUT = "opted_out"
    FAILED_SENDING = "failed_sending"
