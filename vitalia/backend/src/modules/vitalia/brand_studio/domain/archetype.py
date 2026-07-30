# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""SaludArchetype — 4 Jung archetypes salud-friendly (OQ-B resolution 2026-05-27).

Omit Outlaw/Magician/Lover/Innocent (problematic tone para health context).
Default: CAREGIVER.

Anti-creep: NUNCA importar aquí validadores LLM ni brand_voice_summary.
downstream-regression-na: brand-local enum for vitalia health overlay
"""

from __future__ import annotations

from enum import StrEnum


class SaludArchetype(StrEnum):
    """4 Jung archetypes salud-friendly.

    Resolution OQ-B 2026-05-27:
    - Omit Outlaw/Magician/Lover/Innocent (problematic tone for health context)
    - Default: CAREGIVER
    """

    CAREGIVER = "caregiver"  # calidez, cuidado, prioriza paciente — DEFAULT
    SAGE = "sage"  # expertise, datos, educativo
    HEALER = "healer"  # tono empático, sanación, proceso restaurador
    HERO = "hero"  # transformación, superación, inspirador
