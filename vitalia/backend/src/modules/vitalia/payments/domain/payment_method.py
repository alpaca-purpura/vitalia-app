# cap: payment.payment-gateways-latam-recurring
# story-origin: vitalia-fase2-s1-TBD
"""PaymentMethod enum — vitalia-brand-local payment methods.

Used in:
  - CobrarSaldoSubform FE: method selector (5 options)
  - AppointmentPayment domain: method field validation
  - ChargeOrchestrator: gateway routing (tarjeta/mercado_pago → adapter; efectivo → direct)

Per 03-arch § 2.1 + UI mockup cobrar-saldo-subform.html (Chris ratified 2026-05-26).
"""

from __future__ import annotations

from enum import StrEnum


class PaymentMethod(StrEnum):
    """Accepted payment methods for clinic appointment charges.

    Values are lowercase Spanish for FE parity (select option labels).
    ChargeOrchestrator routes to payment adapter based on this value:
      efectivo      → direct record (no external adapter)
      tarjeta       → Stripe Connect or local gateway
      transferencia → manual confirmation flow
      mercado_pago  → MercadoPago adapter (vitalia-payment-adapter-mvp)
      otro          → manual record with notes
    """

    EFECTIVO = "efectivo"
    """Pago en efectivo — directo, sin adaptador externo."""

    TARJETA = "tarjeta"
    """Pago con tarjeta de débito/crédito — via gateway externo."""

    TRANSFERENCIA = "transferencia"
    """Transferencia bancaria — confirmación manual por staff."""

    MERCADO_PAGO = "mercado_pago"
    """Pago via MercadoPago — adapter vitalia-payment-adapter-mvp (service-blocker)."""

    OTRO = "otro"
    """Otro método — registro manual con campo de notas."""
