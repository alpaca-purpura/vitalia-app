# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Vitalia print method registry (receipt/document output methods)."""

from .registry import (
    PRINT_METHOD_REGISTRY,
    PrintMethodDef,
    get_print_method,
    list_print_methods,
)

__all__ = (
    "PRINT_METHOD_REGISTRY",
    "PrintMethodDef",
    "get_print_method",
    "list_print_methods",
)
