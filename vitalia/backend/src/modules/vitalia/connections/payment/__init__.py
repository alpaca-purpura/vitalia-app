# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Vitalia payment provider registry (brand-internal dispatch table)."""

from .registry import (
    PAYMENT_PROVIDER_REGISTRY,
    PaymentProviderDef,
    get_payment_provider,
    list_payment_providers,
)

__all__ = (
    "PAYMENT_PROVIDER_REGISTRY",
    "PaymentProviderDef",
    "get_payment_provider",
    "list_payment_providers",
)
