# cap: fidelizacion.re-engagement
# story-origin: TBD
"""Patrón de re-engagement del paciente — value object StrEnum."""

from enum import StrEnum


class ReEngagementPattern(StrEnum):
    """Patrones de seguimiento para re-engagement de pacientes.

    - MULTI_SESSION: paciente con plan multi-sesión activo
    - FOLLOW_UP: seguimiento post-tratamiento completado
    - MAINTENANCE: mantenimiento periódico (ej. dental cada 6 meses)
    - ABSENCE: paciente ausente sin cita en ventana definida
    - NPS: encuesta NPS post-atención
    """

    MULTI_SESSION = "multi_session"
    FOLLOW_UP = "follow_up"
    MAINTENANCE = "maintenance"
    ABSENCE = "absence"
    NPS = "nps"
