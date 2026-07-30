# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Appointment origin enum — vitalia-brand-local.

Indicates how the appointment was created. Used to render the origin badge
on the slot cell in the agenda cockpit grid (mockup: slot-states-matrix.html).

Per 03-arch § 2.1: brand-local, NOT in engine luana-core-scheduling.
Engine Appointment is origin-agnostic.
"""

from __future__ import annotations

from enum import StrEnum


class AppointmentOrigin(StrEnum):
    """How the appointment was created — shown as badge on slot cell.

    Brand-local enum: vitalia scheduling domain.
    NOT candidate for engine lift (vitalia-specific agentic surface via Adrián).
    """

    WALK_IN = "walk_in"
    """Paciente walk-in — sin agendamiento previo, llega al consultorio."""

    TELEFONO = "telefono"
    """Reserva telefónica — staff creó manualmente desde llamada entrante."""

    PROACTIVO_ADRIAN = "proactivo_adrian"
    """Auto-creada por el flujo embudo Adrián (agente ventas vitalia).

    Indica que el turno surgió de una conversación proactiva del chatbot
    de ventas (sub-tab Adrián → Embudo). Badge especial en el slot.
    """

    PORTAL = "portal"
    """Paciente auto-agendó desde el portal público del consultorio."""
