# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""FiscalEmitPort — abstract interface for fiscal document emission (service-blocker pattern).

Rule (03-arch § 7 + service-blocker decoupling):
  ChargeOrchestrator depends on this ABC, not on the concrete fiscal provider
  (Nubefact PE, AFIP AR, SAT MX, etc.).

  vitalia-fiscal-emission-pe story (state: refining, NOT developed) is the
  concrete implementation. Until it ships, ChargeOrchestrator uses a stub
  that raises FiscalAdapterUnavailableError → FE shows fiscal warning banner
  + "retry emit" button.

  Saga compensation (03-arch § 7.3):
    - Charge OK + fiscal emit FAIL → DO NOT rollback charge.
    - Return fiscal_emission_status='failed' + audit log.
    - FE CobrarSaldoSubform shows warning + offers retry-emit standalone.

  Port lives in scheduling/application/ports/ because consumed by ChargeOrchestrator.
  Concrete impl lives in vitalia/backend/src/modules/vitalia/fiscal/application/ports/
  fiscal_emit_port_impl.py.

Usage:
    class NubefactFiscalPort(FiscalEmitPort):
        async def emit(self, ...) -> FiscalDocResult: ...

    # Stub for F2-S1 (service-blocker):
    class StubFiscalEmitPort(FiscalEmitPort):
        async def emit(self, ...) -> FiscalDocResult:
            raise FiscalAdapterUnavailableError("stub: vitalia-fiscal-emission-pe not developed")
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

__all__ = ["FiscalEmitPort", "FiscalDocResult", "FiscalAdapterUnavailableError", "FiscalEmitError"]


@dataclass(frozen=True)
class FiscalDocResult:
    """Result from fiscal document emission.

    Returned by FiscalEmitPort.emit() on success.

    Attributes:
        doc_number: Issued fiscal document number (e.g. 'B001-00001234').
        doc_url: Signed URL to download the PDF fiscal document.
        provider: Provider name ('nubefact', 'afip', 'sat', 'manual').
    """

    doc_number: str
    doc_url: str
    provider: str


class FiscalAdapterUnavailableError(Exception):
    """Raised when the fiscal provider is unreachable or stub.

    ChargeOrchestrator catches this and proceeds without fiscal
    (saga compensation: charge stays, fiscal status = 'failed').
    FE shows fiscal warning banner + "retry emit" button.
    """


class FiscalEmitError(Exception):
    """Raised when fiscal emission fails with a known provider error.

    Distinct from FiscalAdapterUnavailableError:
    - FiscalAdapterUnavailableError: Provider unreachable (network/auth).
    - FiscalEmitError: Provider reachable but rejected the document
      (invalid data, tax validation failure, duplicate series, etc.).

    ChargeOrchestrator handles both the same way (saga: charge stays, warn FE).
    """


class FiscalEmitPort(ABC):
    """Abstract fiscal document emission port.

    Concrete implementations:
    - vitalia/backend/src/modules/vitalia/fiscal/application/ports/fiscal_emit_port_impl.py
      (targets: vitalia-fiscal-emission-pe story, state: refining)
    - StubFiscalEmitPort (inline in ChargeOrchestrator DI factory for F2-S1)

    All implementations MUST raise FiscalAdapterUnavailableError or FiscalEmitError
    on failure — this allows ChargeOrchestrator to apply saga compensation consistently.
    """

    @abstractmethod
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
        """Emit a fiscal document for a completed payment.

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (for audit/reporting scope).
            payment_id: AppointmentPayment UUID this document covers.
            doc_type: FiscalDocType string (boleta/factura/factura_a/recibo/cfdi/ticket).
            country: ISO 3166-1 alpha-2 country code ('PE', 'AR', 'MX', 'CO', 'CL').
                Selects the appropriate provider and tax rules.
            idempotency_key: Caller-provided key (f"fiscal-{payment_idempotency_key}")
                prevents double-emission on retry.
            amount_cents: Optional amount validation (provider may verify).
            currency: Optional ISO 4217 currency code (provider may use for display).

        Returns:
            FiscalDocResult with doc_number + doc_url.

        Raises:
            FiscalAdapterUnavailableError: Provider unreachable or stub.
            FiscalEmitError: Provider rejected the document request.
        """
