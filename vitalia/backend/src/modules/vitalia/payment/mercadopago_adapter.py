# cap: payment.payment-gateways-latam-recurring
# story-origin: TBD
"""Vitalia MercadoPago adapter — EXTENDS `luana_core_channels.payment.MercadoPagoAdapter`.

Per Story 11 03-arch-be.md § 11.2 (D4 ratified):
- Injects medical-vertical metadata: ``compliance_level=hipaa_lite``,
  ``contains_phi=False``, ``brand_slug=vitalia`` per Q6=B ratification.
- Reuses ALL HTTP plumbing + idempotency + HMAC + canonical status mapping
  from core base — vitalia never re-implements.

Anti-duplication.md enforcement: this module subclasses (composition over
mirror). Future Comunify / Lupulo brands ALSO extend the same core base.

# [VITALIA-D4-EXTENDS-CORE-MERCADOPAGO]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luana_core_channels.payment import MercadoPagoAdapter

if TYPE_CHECKING:
    from uuid import UUID


class VitaliaMercadoPagoAdapter(MercadoPagoAdapter):
    """Vitalia (medical-vertical) MercadoPago booking-deposit adapter.

    Extension contract per `.claude/rules/anti-duplication.md`:
    - Override `_extra_metadata` ONLY (vertical metadata injection).
    - Inherit ALL HTTP / idempotency / HMAC / status-mapping behavior unchanged.
    - NO override of `create_preference` / `verify_payment` / HTTP client lifecycle.
    """

    # Vertical-medical compliance constants (Q6=B ratified — HIPAA-lite, NOT HIPAA-full).
    COMPLIANCE_LEVEL: str = "hipaa_lite"
    BRAND_SLUG: str = "vitalia"
    # PHI never sent to MP — payer block keeps masked initials only (J. P.).
    CONTAINS_PHI: bool = False

    def _extra_metadata(
        self,
        *,
        tenant_id: UUID,  # noqa: ARG002 — kept for hook signature stability
        booking_id: UUID | None,  # noqa: ARG002
        deposit_or_full: str,
    ) -> dict[str, Any]:
        """Inject vertical-medical metadata into MP preference."""
        return {
            "compliance_level": self.COMPLIANCE_LEVEL,
            "contains_phi": self.CONTAINS_PHI,
            "brand_slug": self.BRAND_SLUG,
            "deposit_or_full": deposit_or_full,
            # Audit-log breadcrumb (vitalia_medical_audit_log surface — per arch-be § 6).
            "audit_category": "payment_intent_created",
        }
