# cap: fidelizacion.re-engagement
# story-origin: TBD
"""Nivel de urgencia para seguimiento de plan de tratamiento — value object StrEnum."""

from enum import StrEnum


class UrgencyLevel(StrEnum):
    """Nivel de urgencia calculado por el cron de seguimiento multi-sesión.

    Orden ascendente de urgencia:
    - UP_TO_DATE: sin desfase, dentro de ventana esperada
    - WAITING: próxima sesión pronto (dentro de gap_alert_days)
    - NEAR: sesión vencida por pocos días
    - ALERT: sesión vencida por días significativos
    - CRITICAL: sesión vencida por periodo extendido — acción inmediata
    """

    UP_TO_DATE = "up_to_date"
    WAITING = "waiting"
    NEAR = "near"
    ALERT = "alert"
    CRITICAL = "critical"
