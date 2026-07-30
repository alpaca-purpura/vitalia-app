# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Fiscal provider registry (Vitalia LATAM e-invoicing dispatch).

Per `03-arch-be.md` § 6.2 — Slice 1 ships only `nubefact_pe`. Real adapter
lands in side story `vitalia-fiscal-emission-pe`; the slot here is a
placeholder.

Slice 2 candidates: tefacturo_pe, facturak_pe.
Slice 3 candidates: facturama_mx, dian_co, afip_ar, sii_cl.

Promotion to engine EP-20 candidate documented in
`vitalia/docs/product/stories/vitalia-ux-discovery/delta-arch-notes.md`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


def _fiscal_not_implemented(provider_id: str, side_story: str):
    """Build placeholder callable for fiscal providers (side story gated)."""

    def _placeholder(*args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            f"vitalia.connections.fiscal provider={provider_id!r} handler is a "
            f"placeholder — real implementation lands in side story {side_story!r}. "
            f"T-infra-2 scope mounts the slot only."
        )

    return _placeholder


@dataclass(frozen=True)
class FiscalProviderDef:
    """Metadata + dispatch callable for a Vitalia fiscal-emission provider slot.

    Attributes:
        provider_id: canonical slug (snake_case)
        country: ISO-3166 alpha-2 (PE, MX, CO, AR, CL, BR, US)
        emits: tuple of receipt kinds the adapter can emit
               (e.g. boleta / factura / nota_credito / nota_debito)
        handler: callable bound at dispatch time. Slice 1 raises NotImplementedError.
        handler_ref: dotted path under `vitalia.connections.fiscal.*` for documentation.
        retry_queue: whether the adapter requires a retry queue for transient
                     failures (Nubefact rate-limited 100req/h free tier — MANDATORY).
        cdr_archive: whether the adapter archives the CDR (Constancia de Recepción)
                     XML / acknowledgment payload from the fiscal authority.
    """

    provider_id: str
    country: str
    emits: tuple[str, ...]
    handler: Any
    handler_ref: str = ""
    retry_queue: bool = True
    cdr_archive: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


FISCAL_PROVIDER_REGISTRY: dict[str, FiscalProviderDef] = {
    "nubefact_pe": FiscalProviderDef(
        provider_id="nubefact_pe",
        country="PE",
        emits=("boleta", "factura", "nota_credito"),
        handler=_fiscal_not_implemented("nubefact_pe", "vitalia-fiscal-emission-pe"),
        handler_ref="vitalia.connections.fiscal.nubefact_pe.adapter:submit_receipt",
        retry_queue=True,
        cdr_archive=True,
        metadata={"side_story": "vitalia-fiscal-emission-pe"},
    ),
}


def get_fiscal_provider(provider_id: str) -> FiscalProviderDef | None:
    """Return the registered fiscal provider def or None if unknown."""
    return FISCAL_PROVIDER_REGISTRY.get(provider_id)


def list_fiscal_providers() -> tuple[str, ...]:
    """Return the tuple of registered provider slugs (deterministic order)."""
    return tuple(FISCAL_PROVIDER_REGISTRY.keys())


__all__: Iterable[str] = (
    "FISCAL_PROVIDER_REGISTRY",
    "FiscalProviderDef",
    "get_fiscal_provider",
    "list_fiscal_providers",
)
