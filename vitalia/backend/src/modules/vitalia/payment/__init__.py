# cap: payment.payment-gateways-latam-recurring
# story-origin: TBD
"""Vitalia payment channel adapters — EXTEND `@luana/core/channels.payment`.

Per Story 11 03-arch-be.md § 11.2 (D4 ratified) — vitalia subclasses base
adapters from `luana_core_channels.payment` injecting medical-vertical
metadata (compliance_level=hipaa_lite, brand_slug=vitalia, contains_phi).

NEVER mirror — `.claude/rules/anti-duplication.md` enforces lift-shared.

# [VITALIA-D4-EXTENDS-CORE-MERCADOPAGO]
"""

from src.modules.vitalia.payment.mercadopago_adapter import (
    VitaliaMercadoPagoAdapter,
)

__all__ = ("VitaliaMercadoPagoAdapter",)
