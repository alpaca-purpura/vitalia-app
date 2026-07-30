# cap: fiscal.fiscal-emission-pe
# story-origin: TBD
"""FiscalEmitPortImpl — tenant country selector for fiscal document emission.

Rule (03-arch § 7 + service-blocker pattern):
  Selects the appropriate fiscal provider based on tenant country code.
  Provider routing:
    PE (Peru)    → Nubefact (vitalia-fiscal-emission-pe service-blocker)
    AR (Argentina) → AFIP (future service-blocker)
    MX (Mexico)  → SAT (future service-blocker)
    default      → raises FiscalAdapterUnavailableError

Service-blocker (Option A):
  vitalia-fiscal-emission-pe story (state: refining, NOT developed).
  All provider paths currently raise FiscalAdapterUnavailableError.
  ChargeOrchestrator catches this and applies saga compensation (charge stays, fiscal fails).

When vitalia-fiscal-emission-pe is developed:
  Update _emit_nubefact() to call the real Nubefact client.
  Keep FiscalEmitPortImpl as the selector; only the _emit_*() methods change.

Per 03-arch § 7 + 05-guidelines T-5 deliverables.
"""

from __future__ import annotations

from uuid import UUID

import structlog

from src.modules.vitalia.scheduling.application.ports.fiscal_emit_port import (
    FiscalAdapterUnavailableError,
    FiscalDocResult,
    FiscalEmitPort,
)

logger = structlog.get_logger()

# Country → provider routing table
_COUNTRY_PROVIDER_MAP: dict[str, str] = {
    "PE": "nubefact",
    "AR": "afip",
    "MX": "sat",
    "CO": "dian",
    "CL": "sii",
    "US": "generic",  # No fiscal emit in US context
}


class FiscalEmitPortImpl(FiscalEmitPort):
    """Real fiscal emit port — country selector for LatAm fiscal providers.

    Routes to the appropriate fiscal provider based on tenant country:
      PE → Nubefact (boleta/factura electronica)
      AR → AFIP (factura_a/b/recibo)
      MX → SAT (CFDI)
      CO → DIAN (factura electronica)
      CL → SII (boleta/factura)

    Current state (service-blocker):
      All provider paths raise FiscalAdapterUnavailableError.
      vitalia-fiscal-emission-pe (state: refining) will implement Nubefact first.

    When service-blockers ship, update _emit_nubefact() / _emit_afip() etc.
    """

    def __init__(self, *, country: str = "PE") -> None:
        """Initialize port with tenant's country code.

        Args:
            country: ISO 3166-1 alpha-2 country code (injected by DI factory).
                     Used to select the fiscal provider.
        """
        self._country = country.upper()
        self._provider = _COUNTRY_PROVIDER_MAP.get(self._country, "unknown")

    async def emit(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        payment_id: UUID,
        doc_type: str,
        country: str,
        idempotency_key: str,
        amount_cents: int | None = None,
        currency: str | None = None,
    ) -> FiscalDocResult:
        """Emit fiscal document for the tenant's country.

        Routes to the appropriate provider based on country code.
        All routes currently raise FiscalAdapterUnavailableError (service-blocker).

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (audit scope).
            payment_id: AppointmentPayment UUID this document covers.
            doc_type: FiscalDocType string (boleta/factura/cfdi/ticket).
            country: ISO 3166-1 alpha-2 country code.
            idempotency_key: Prevents double-emission on retry.
            amount_cents: Optional amount for provider validation.
            currency: Optional ISO 4217 code for provider display.

        Returns:
            FiscalDocResult with doc_number + doc_url.

        Raises:
            FiscalAdapterUnavailableError: Provider unreachable or service-blocker.
            FiscalEmitError: Provider reachable but rejected the document.
        """
        effective_country = country.upper() if country else self._country
        provider = _COUNTRY_PROVIDER_MAP.get(effective_country, "unknown")

        logger.info(
            "fiscal_emit_port_impl.emit",
            country=effective_country,
            provider=provider,
            doc_type=doc_type,
            idempotency_key=idempotency_key,
            # No PHI: payment_id is UUID only
        )

        if effective_country == "PE":
            return await self._emit_nubefact(
                tenant_id=tenant_id,
                payment_id=payment_id,
                doc_type=doc_type,
                idempotency_key=idempotency_key,
                amount_cents=amount_cents,
                currency=currency,
            )

        if effective_country == "AR":
            return await self._emit_afip(
                tenant_id=tenant_id,
                payment_id=payment_id,
                doc_type=doc_type,
                idempotency_key=idempotency_key,
                amount_cents=amount_cents,
                currency=currency,
            )

        if effective_country == "MX":
            return await self._emit_sat(
                tenant_id=tenant_id,
                payment_id=payment_id,
                doc_type=doc_type,
                idempotency_key=idempotency_key,
                amount_cents=amount_cents,
                currency=currency,
            )

        # Unknown/unsupported country — fiscal emit unavailable
        raise FiscalAdapterUnavailableError(
            f"FiscalEmitPortImpl: no fiscal provider configured for country '{effective_country}'. "
            "Supported countries: PE (Nubefact), AR (AFIP), MX (SAT). "
            "Use StubFiscalEmitPort for dev/test."
        )

    async def _emit_nubefact(
        self,
        *,
        tenant_id: UUID,
        payment_id: UUID,
        doc_type: str,
        idempotency_key: str,
        amount_cents: int | None,
        currency: str | None,
    ) -> FiscalDocResult:
        """Emit via Nubefact (PE — boleta/factura electronica).

        # DEPRECATED path: vitalia-fiscal-emission-pe not yet developed.
        # When developed, instantiate NubefactClient and call .emit_document().

        Raises:
            FiscalAdapterUnavailableError: Always raised until service-blocker developed.
        """
        raise FiscalAdapterUnavailableError(
            "FiscalEmitPortImpl: Nubefact adapter not yet configured. "
            "Waiting for vitalia-fiscal-emission-pe (state: refining → developed). "
            "Use StubFiscalEmitPort for local development."
        )

    async def _emit_afip(
        self,
        *,
        tenant_id: UUID,
        payment_id: UUID,
        doc_type: str,
        idempotency_key: str,
        amount_cents: int | None,
        currency: str | None,
    ) -> FiscalDocResult:
        """Emit via AFIP (AR — factura_a/b/recibo).

        # DEPRECATED path: AFIP adapter future service-blocker.

        Raises:
            FiscalAdapterUnavailableError: Always raised until service-blocker developed.
        """
        raise FiscalAdapterUnavailableError(
            "FiscalEmitPortImpl: AFIP adapter not yet configured. "
            "Future service-blocker: vitalia-fiscal-emission-ar. "
            "Use StubFiscalEmitPort for local development."
        )

    async def _emit_sat(
        self,
        *,
        tenant_id: UUID,
        payment_id: UUID,
        doc_type: str,
        idempotency_key: str,
        amount_cents: int | None,
        currency: str | None,
    ) -> FiscalDocResult:
        """Emit via SAT (MX — CFDI).

        # DEPRECATED path: SAT adapter future service-blocker.

        Raises:
            FiscalAdapterUnavailableError: Always raised until service-blocker developed.
        """
        raise FiscalAdapterUnavailableError(
            "FiscalEmitPortImpl: SAT/CFDI adapter not yet configured. "
            "Future service-blocker: vitalia-fiscal-emission-mx. "
            "Use StubFiscalEmitPort for local development."
        )
