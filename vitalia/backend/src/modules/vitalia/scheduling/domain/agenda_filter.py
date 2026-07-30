# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Preset filter enum for the Valeria Agenda cockpit.

Whitelist of valid preset filter chip values — any query-param outside this
enum is rejected at the API layer (prevents PHI enumeration attacks).

Per 03-arch § 2.1 + CONTEXT-BRIEF § 2 (A10: test_no_phi_in_url_params).
Brand-local: vitalia scheduling module.
"""

from __future__ import annotations

from enum import StrEnum


class AgendaPresetFilter(StrEnum):
    """Whitelist preset filter chips for the Agenda calendar view.

    These map 1:1 to the HTML mockup filter chips ratified by Chris
    (vitalia-fase2-valeria-agenda/mockups/preset-filters.html).

    Values are lowercase Spanish (neutro LatAm) for URL safety and FE parity.
    """

    HOY = "hoy"
    """Todas las citas del día de hoy."""

    POR_CONFIRMAR_MANANA = "por_confirmar_manana"
    """Citas de mañana pendientes de confirmación del paciente."""

    REAGENDAR_PENDIENTES = "reagendar_pendientes"
    """Citas marcadas para re-agendar (status RESCHEDULED o faltó turno)."""

    NO_SHOWS_DIA = "no_shows_dia"
    """Pacientes que no se presentaron al turno de hoy."""

    SALDOS_PENDIENTES = "saldos_pendientes"
    """Citas con balance pendiente de pago (balance_amount_cents > 0)."""
