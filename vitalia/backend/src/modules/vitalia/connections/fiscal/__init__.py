# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Vitalia fiscal provider registry (LATAM e-invoicing dispatch)."""

from .registry import (
    FISCAL_PROVIDER_REGISTRY,
    FiscalProviderDef,
    get_fiscal_provider,
    list_fiscal_providers,
)

__all__ = (
    "FISCAL_PROVIDER_REGISTRY",
    "FiscalProviderDef",
    "get_fiscal_provider",
    "list_fiscal_providers",
)
