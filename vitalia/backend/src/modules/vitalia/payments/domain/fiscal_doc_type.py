# cap: payment.payment-gateways-latam-recurring
# story-origin: vitalia-fase2-s1-TBD
"""FiscalDocType enum — fiscal document types per LatAm territory.

Covers PE/AR/MX territories confirmed in CONTEXT-BRIEF § 11
(validator gap: "Verify FiscalDocType covers PE/AR/MX territories").

Used in:
  - CobrarSaldoSubform FE: invoice toggle (show doc_type selector)
  - FiscalDocument domain: doc_type field
  - FiscalEmitPort stub: route by doc_type to provider

Provider mapping:
  PE boleta/factura → Nubefact (vitalia-fiscal-emission-pe service-blocker)
  AR factura_a/b/recibo → AFIP (future service-blocker)
  MX cfdi → SAT (future service-blocker)
  ticket → generic receipt (no fiscal provider required)

Per 03-arch § 2.1 + vitalia fiscal service-blockers scope.
"""

from __future__ import annotations

from enum import StrEnum


class FiscalDocType(StrEnum):
    """Fiscal document types for LatAm territories.

    Values are lowercase Spanish matching provider terminology.
    ticket is the generic fallback for non-regulated transactions.
    """

    # Peru (PE) — Nubefact provider
    BOLETA = "boleta"
    """Boleta de venta electrónica (PE) — consumidor final, sin RUC."""

    FACTURA = "factura"
    """Factura electrónica (PE/genérica) — persona jurídica con RUC."""

    # Argentina (AR) — AFIP provider (future)
    FACTURA_A = "factura_a"
    """Factura A (AR) — responsable inscripto a responsable inscripto."""

    FACTURA_B = "factura_b"
    """Factura B (AR) — responsable inscripto a consumidor final."""

    RECIBO = "recibo"
    """Recibo (AR) — para pagos en efectivo o parciales."""

    # Mexico (MX) — SAT provider (future)
    CFDI = "cfdi"
    """CFDI (MX) — Comprobante Fiscal Digital por Internet via SAT."""

    # Generic
    TICKET = "ticket"
    """Ticket genérico — sin emisión fiscal, solo registro interno."""
