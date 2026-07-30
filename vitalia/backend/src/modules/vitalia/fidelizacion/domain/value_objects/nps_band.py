# cap: patients.nps-tracking
# story-origin: TBD
"""Banda NPS (Promoter / Passive / Detractor) — value object StrEnum con factory."""

from enum import StrEnum


class NPSBand(StrEnum):
    """Clasificación estándar NPS según score 0-10.

    - DETRACTOR: score 0-6
    - PASSIVE: score 7-8
    - PROMOTER: score 9-10
    """

    DETRACTOR = "detractor"
    PASSIVE = "passive"
    PROMOTER = "promoter"

    @classmethod
    def from_score(cls, score: int) -> "NPSBand":
        """Deriva la banda NPS desde el score numérico (0-10).

        Args:
            score: Puntuación NPS entre 0 y 10 inclusive.

        Returns:
            Banda correspondiente al score.

        Raises:
            ValueError: Si el score está fuera del rango 0-10.
        """
        if not (0 <= score <= 10):
            raise ValueError(f"NPS score debe estar entre 0 y 10, recibido: {score}")
        if score >= 9:
            return cls.PROMOTER
        if score >= 7:
            return cls.PASSIVE
        return cls.DETRACTOR
