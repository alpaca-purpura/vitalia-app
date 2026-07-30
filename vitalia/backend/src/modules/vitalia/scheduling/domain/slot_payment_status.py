# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Slot payment status enum — visual color coding for the agenda cockpit.

Drives the 4-color matrix on each slot cell in the calendar grid:
  🟢 pagado    — paid in full
  🟡 deposito  — partial payment (deposit taken, balance remains)
  🔴 sin_pago  — no payment recorded yet
  ⚫ no_show   — patient did not attend

Derived server-side in AgendaSlotService from:
  - AppointmentStatus engine value (NO_SHOW → no_show)
  - AppointmentPayment records: balance_amount_cents vs amount paid

Per 03-arch § 2.2 (SlotPaymentStatus lives in scheduling/domain).
"""

from __future__ import annotations

from enum import StrEnum


class SlotPaymentStatus(StrEnum):
    """Payment status indicator for agenda slot cell color coding.

    4×3 matrix: 4 payment states × 3 origin badges (walk_in, telefono, Adrián).
    Rendered as colored left-border on each slot cell.
    """

    PAGADO = "pagado"
    """Balance es cero + hay al menos un pago registrado. Borde verde 🟢."""

    DEPOSITO = "deposito"
    """Balance > 0 + hay al menos un pago registrado (depósito parcial). Borde amarillo 🟡."""

    SIN_PAGO = "sin_pago"
    """Balance > 0 + sin ningún pago registrado. Borde rojo 🔴."""

    NO_SHOW = "no_show"
    """Paciente no se presentó (AppointmentStatus.NO_SHOW en engine). Borde gris ⚫."""
