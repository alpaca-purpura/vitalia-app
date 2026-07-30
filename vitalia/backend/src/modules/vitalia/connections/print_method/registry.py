# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Print method registry (Vitalia document/receipt output).

Per `03-arch-be.md` § 6.5 — Slice 1 ships only `browser_pdf` (FE-only
`window.print()` on a hidden iframe in the agenda payment receipt sheet). No
backend callable; the registry slot exists so:

  1. The asset_template renderer (EP-12) can validate `print_method` references.
  2. Slice 2 thermal printer support (`webusb_escpos` 58mm/80mm) lands as a
     drop-in new registry entry without changing any consumer code.
  3. Slice 3 network printing (`network_ipp`) lands similarly.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PrintMethodDef:
    """Metadata for a Vitalia print method slot.

    Attributes:
        method_id: canonical slug (snake_case)
        method: implementation kind. For Slice 1, `"window.print()"` denotes
                FE-only browser native print. Future kinds:
                `"webusb_escpos_58mm" | "webusb_escpos_80mm" | "network_ipp"`.
        formats: tuple of output formats supported (`"pdf" | "html" | "escpos"`).
        is_fe_only: True if no backend callable required (Slice 1 browser_pdf).
        label_es: Spanish-neutro user-facing label.
    """

    method_id: str
    method: str
    formats: tuple[str, ...]
    is_fe_only: bool = True
    label_es: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


PRINT_METHOD_REGISTRY: dict[str, PrintMethodDef] = {
    "browser_pdf": PrintMethodDef(
        method_id="browser_pdf",
        method="window.print()",
        formats=("pdf",),
        is_fe_only=True,
        label_es="Imprimir desde el navegador",
    ),
}


def get_print_method(method_id: str) -> PrintMethodDef | None:
    """Return the registered print method def or None if unknown."""
    return PRINT_METHOD_REGISTRY.get(method_id)


def list_print_methods() -> tuple[str, ...]:
    """Return the tuple of registered print-method slugs (deterministic order)."""
    return tuple(PRINT_METHOD_REGISTRY.keys())


__all__: Iterable[str] = (
    "PRINT_METHOD_REGISTRY",
    "PrintMethodDef",
    "get_print_method",
    "list_print_methods",
)
