# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""PaymentChargePort — abstract interface for payment adapter (service-blocker pattern).

Rule (03-arch § 7 + service-blocker decoupling):
  CreateAppointmentService and ChargeOrchestrator depend on this ABC,
  not on the concrete payment adapter (Stripe/MercadoPago/efectivo).

  vitalia-payment-adapter-mvp story (state: refined, NOT developed) is the
  concrete implementation. Until it ships, ChargeOrchestrator uses a stub
  that raises PaymentAdapterUnavailableError → 503 → MSW mock in FE (§ 8.6).

  This port lives here (scheduling/application/ports/) because it is consumed
  by ChargeOrchestrator (scheduling/application/). The concrete impl lives in
  vitalia/backend/src/modules/vitalia/payments/application/payment_charge_port_impl.py.

Usage:
    class MyConcreteAdapter(PaymentChargePort):
        async def charge(self, ...) -> ExternalPaymentResult: ...

    # Stub for F2-S1 (service-blocker):
    class StubPaymentChargePort(PaymentChargePort):
        async def charge(self, ...) -> ExternalPaymentResult:
            raise PaymentAdapterUnavailableError("stub: vitalia-payment-adapter-mvp not developed")
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

__all__ = ["PaymentChargePort", "ExternalPaymentResult", "PaymentAdapterUnavailableError"]


@dataclass(frozen=True)
class ExternalPaymentResult:
    """Result from external payment gateway.

    Returned by PaymentChargePort.charge() on success.

    Attributes:
        external_payment_id: Gateway-assigned transaction ID (stored for idempotency).
        gateway: Gateway name ('stripe', 'mercadopago', 'efectivo_manual').
        raw_response: Original gateway response dict (used for fiscal emit if needed).
    """

    external_payment_id: str
    gateway: str
    raw_response: dict


class PaymentAdapterUnavailableError(Exception):
    """Raised when the payment adapter cannot process the request.

    Callers (ChargeOrchestrator) catch this and return HTTP 503 to FE.
    FE shows "Servicio de pago temporalmente no disponible" + retry button.

    In F2-S1 service-blocker pattern: StubPaymentChargePort always raises this.
    """


class PaymentChargePort(ABC):
    """Abstract payment charge port.

    Concrete implementations:
    - vitalia/backend/src/modules/vitalia/payments/application/payment_charge_port_impl.py
      (targets: vitalia-payment-adapter-mvp story, state: refined)
    - StubPaymentChargePort (inline in ChargeOrchestrator DI factory for F2-S1)

    All implementations MUST raise PaymentAdapterUnavailableError (not generic Exception)
    on adapter failure — this allows ChargeOrchestrator to map to HTTP 503 consistently.
    """

    @abstractmethod
    async def charge(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        appointment_id: UUID,
        amount_cents: int,
        currency: str,
        method: str,
        idempotency_key: str,
    ) -> ExternalPaymentResult:
        """Charge the given amount via the tenant's configured payment gateway.

        Args:
            tenant_id: Root tenant UUID (selects gateway from tenant.config).
            clinic_id: Clinic UUID (for audit/reporting scope).
            appointment_id: Appointment this charge is for.
            amount_cents: Amount in smallest currency unit (centavos/cents).
                Must be positive non-zero.
            currency: ISO 4217 currency code (e.g. 'PEN', 'ARS', 'MXN', 'USD').
                NOT hardcoded — comes from ChargeRequestDTO.currency.
            method: PaymentMethod string (efectivo/tarjeta/transferencia/mercado_pago/otro).
            idempotency_key: Caller-provided key (UUID v4 string) for dedup.
                Gateway MUST NOT double-charge if same key arrives twice.

        Returns:
            ExternalPaymentResult with external_payment_id + gateway name.

        Raises:
            PaymentAdapterUnavailableError: On gateway timeout, auth failure,
                or stub (service-blocker) pattern. Caller maps to HTTP 503.
        """
