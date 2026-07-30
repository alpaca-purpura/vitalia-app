# cap: fiscal.fiscal-emission-pe
# story-origin: TBD
"""StubFiscalEmitPort — service-blocker Option A stub.

# DEPRECATED: replace when vitalia-fiscal-emission-pe state=done.
# This stub unblocks F2-S1 build while the fiscal emission service is being developed.
# Architecture test test_no_stub_in_prod_path.py (post-story-merge ratchet) will
# enforce stub-free production before merge.

Usage (DI factory in fiscal router T-7):
    from src.modules.vitalia.fiscal.application.stubs.stub_fiscal_emit_port import (
        StubFiscalEmitPort,
    )
    fiscal_port = StubFiscalEmitPort(mode="happy")

Modes:
  "happy"       — Returns FiscalDocResult with stub doc_number.
  "unavailable" — Raises FiscalAdapterUnavailableError (tests saga compensation).
  "error"       — Raises FiscalEmitError (provider rejects — tests saga compensation).

Replacement path (when vitalia-fiscal-emission-pe is developed):
  Replace with FiscalEmitPortImpl (fiscal/application/fiscal_emit_port_impl.py)
  which selects Nubefact/AFIP/SAT provider based on tenant country.
"""

from __future__ import annotations

import structlog

from src.modules.vitalia.scheduling.application.ports.fiscal_emit_port import (
    FiscalAdapterUnavailableError,
    FiscalDocResult,
    FiscalEmitError,
    FiscalEmitPort,
)

logger = structlog.get_logger()

_STUB_SEQUENCE = 0


def _next_stub_doc_number(doc_type: str) -> str:
    """Generate incrementing stub doc number for traceability."""
    global _STUB_SEQUENCE  # noqa: PLW0603
    _STUB_SEQUENCE += 1
    return f"STUB-{doc_type.upper()[:3]}-{_STUB_SEQUENCE:06d}"


# DEPRECATED: replace when vitalia-fiscal-emission-pe state=done
class StubFiscalEmitPort(FiscalEmitPort):
    """Stub fiscal emit port for F2-S1 service-blocker pattern (Option A).

    Satisfies the FiscalEmitPort ABC contract.
    Used in dev/test until vitalia-fiscal-emission-pe ships.

    # DEPRECATED: replace when vitalia-fiscal-emission-pe state=done.
    """

    def __init__(self, *, mode: str = "happy") -> None:
        """Initialize stub fiscal port.

        Args:
            mode: "happy" | "unavailable" | "error"
        """
        valid_modes = ("happy", "unavailable", "error")
        if mode not in valid_modes:
            raise ValueError(f"StubFiscalEmitPort: mode must be one of {valid_modes}, got '{mode}'")
        self._mode = mode

    async def emit(
        self,
        *,
        tenant_id,
        clinic_id,
        payment_id,
        doc_type: str,
        country: str,
        idempotency_key: str,
        amount_cents: int | None = None,
        currency: str | None = None,
    ) -> FiscalDocResult:
        """Stub emit — logs request, returns fake result or raises error.

        # DEPRECATED: replace when vitalia-fiscal-emission-pe state=done.
        """
        logger.info(
            "stub_fiscal_emit_port.emit",
            mode=self._mode,
            doc_type=doc_type,
            country=country,
            idempotency_key=idempotency_key,
            # No PHI: payment_id is UUID, no patient data
        )

        if self._mode == "unavailable":
            raise FiscalAdapterUnavailableError(
                "StubFiscalEmitPort: vitalia-fiscal-emission-pe not yet developed "
                "(service-blocker Option A). Replace this stub when state=done."
            )

        if self._mode == "error":
            raise FiscalEmitError(f"StubFiscalEmitPort: simulated provider rejection for {doc_type}/{country}")

        # Happy path: return stub fiscal document result
        doc_number = _next_stub_doc_number(doc_type)
        return FiscalDocResult(
            doc_number=doc_number,
            doc_url=None,  # No real PDF in stub — FE shows pending indicator
            provider="nubefact_stub",
        )
