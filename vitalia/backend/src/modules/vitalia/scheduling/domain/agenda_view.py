# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Agenda calendar display view mode.

Controls the calendar rendering mode. Persisted in URL params + localStorage
('lastView') per the visual spec ratified in the HTML mockups.

Default is SEMANA per 03-arch § 2.1 + checkpoint batch_2 decision.
"""

from __future__ import annotations

from enum import StrEnum


class AgendaView(StrEnum):
    """Calendar display mode for the Valeria Agenda sub-tab.

    Values are lowercase Spanish for URL-param safety and FE parity.
    Persisted in: URL ?view= param + localStorage key 'lastView'.
    Mobile: DIA forced (dia-only per mockup mobile-drawer-fullscreen.html).
    """

    DIA = "dia"
    """Vista diaria — columnas por hora, citas como bloques verticales."""

    SEMANA = "semana"
    """Vista semanal — DEFAULT. 7 columnas, citas agrupadas por día."""

    MES = "mes"
    """Vista mensual — grilla 5×7, react-window virtualized para performance."""
