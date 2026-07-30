# cap: payment.payment-gateways-latam-recurring
# story-origin: vitalia-fase2-s1-TBD
"""PaymentChargePortImpl — tenant gateway selector wrapping existing scaffolds.

Rule (03-arch § 7 + service-blocker pattern):
  Selects the appropriate payment adapter based on tenant.config.payment_gateway.
  Wraps existing scaffolds in vitalia/backend/src/modules/vitalia/payment/:
    stripe_connect_adapter.py   → "stripe"
    mercadopago_adapter.py      → "mercadopago"
  efectivo/transferencia/otro  → no external adapter (direct record, handled here).

Service-blocker (Option A):
  vitalia-payment-adapter-mvp story (state: refined, NOT developed).
  If adapter methods are missing or not configured → raises PaymentAdapterUnavailableError.
  Callers (ChargeOrchestrator) catch this and return HTTP 503.

Do NOT modify existing scaffold files (vitalia/backend/src/modules/vitalia/payment/).
This module adapts the scaffold API to the PaymentChargePort ABC.

Per 03-arch § 7.2 + 05-guidelines "NO modify scaffolds, only adapt".

Replacement note: When vitalia-payment-adapter-mvp is developed, update this impl
to fully wire the mvp adapter instead of raising PaymentAdapterUnavailableError.
"""

from __future__ import annotations

from uuid import UUID

import structlog

from src.modules.vitalia.scheduling.application.ports.payment_charge_port import (
    ExternalPaymentResult,
    PaymentAdapterUnavailableError,
    PaymentChargePort,
)

logger = structlog.get_logger()

# Payment gateways requiring external adapter (not yet implemented)
_ADAPTER_REQUIRED_GATEWAYS = frozenset({"stripe", "mercadopago"})

# Payment methods that are direct records (no external gateway call)
_DIRECT_METHODS = frozenset({"efectivo", "transferencia", "otro"})


class PaymentChargePortImpl(PaymentChargePort):
    """Real payment charge port implementation — tenant gateway selector.

    Selects adapter based on tenant.config.payment_gateway at runtime.
    Wraps existing scaffolds (stripe_connect_adapter.py, mercadopago_adapter.py)
    WITHOUT modifying them.

    Current state:
      efectivo / transferencia / otro → direct record (no external adapter call).
      stripe / mercadopago           → raises PaymentAdapterUnavailableError
                                       (service-blocker: vitalia-payment-adapter-mvp
                                       not yet developed).

    When vitalia-payment-adapter-mvp ships:
      Update _charge_via_stripe() / _charge_via_mercadopago() to use the real adapter.
    """

    def __init__(self, *, payment_gateway: str = "efectivo") -> None:
        """Initialize port with tenant's configured payment gateway.

        Args:
            payment_gateway: Tenant configuration value ('efectivo', 'transferencia',
                'stripe', 'mercadopago', 'otro'). Injected by DI factory in router.
        """
        self._gateway = payment_gateway

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
        """Charge via the tenant's configured gateway.

        Routes based on method:
          efectivo / transferencia / otro → _charge_direct() (no external adapter)
          tarjeta (stripe)               → raises PaymentAdapterUnavailableError (service-blocker)
          mercado_pago                   → raises PaymentAdapterUnavailableError (service-blocker)

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (for audit scope — not sent to payment gateway).
            appointment_id: Appointment this charge is for.
            amount_cents: Amount in smallest currency unit.
            currency: ISO 4217 currency code (PEN/ARS/MXN/USD — never hardcoded).
            method: PaymentMethod value.
            idempotency_key: Client-supplied UUID to prevent duplicate charges.

        Returns:
            ExternalPaymentResult on success.

        Raises:
            PaymentAdapterUnavailableError: When external adapter is not yet configured
                (service-blocker) or unavailable (timeout/auth failure).
        """
        logger.info(
            "payment_charge_port_impl.charge",
            gateway=self._gateway,
            method=method,
            amount_cents=amount_cents,
            currency=currency,
            idempotency_key=idempotency_key,
            # No PHI: appointment_id is UUID, no patient data
        )

        if method in _DIRECT_METHODS:
            return await self._charge_direct(
                appointment_id=appointment_id,
                amount_cents=amount_cents,
                currency=currency,
                method=method,
                idempotency_key=idempotency_key,
            )

        if method == "tarjeta":
            return await self._charge_via_stripe(
                tenant_id=tenant_id,
                appointment_id=appointment_id,
                amount_cents=amount_cents,
                currency=currency,
                idempotency_key=idempotency_key,
            )

        if method == "mercado_pago":
            return await self._charge_via_mercadopago(
                tenant_id=tenant_id,
                appointment_id=appointment_id,
                amount_cents=amount_cents,
                currency=currency,
                idempotency_key=idempotency_key,
            )

        # Unknown method — treat as unavailable
        raise PaymentAdapterUnavailableError(
            f"PaymentChargePortImpl: unknown payment method '{method}'. "
            "Valid methods: efectivo, tarjeta, transferencia, mercado_pago, otro."
        )

    async def _charge_direct(
        self,
        *,
        appointment_id: UUID,
        amount_cents: int,
        currency: str,
        method: str,
        idempotency_key: str,
    ) -> ExternalPaymentResult:
        """Direct payment record — no external gateway call needed.

        efectivo / transferencia / otro are confirmed manually by staff.
        Returns a record ref using the idempotency_key as the external_payment_id.
        """
        logger.info(
            "payment_charge_port_impl.direct_record",
            method=method,
            amount_cents=amount_cents,
            currency=currency,
        )
        return ExternalPaymentResult(
            external_payment_id=f"direct-{method}-{idempotency_key}",
            gateway=method,
            raw_response={"method": method, "direct_record": True},
        )

    async def _charge_via_stripe(
        self,
        *,
        tenant_id: UUID,
        appointment_id: UUID,
        amount_cents: int,
        currency: str,
        idempotency_key: str,
    ) -> ExternalPaymentResult:
        """Charge via Stripe Connect adapter (scaffold wrapper).

        # DEPRECATED path: vitalia-payment-adapter-mvp not yet developed.
        # When developed, import and call StripeConnectAdapter.create_payment_intent().
        # Scaffolds in vitalia/backend/src/modules/vitalia/payment/stripe_connect_adapter.py
        # must NOT be modified — only adapted here.

        Raises:
            PaymentAdapterUnavailableError: Always raised until mvp adapter developed.
        """
        raise PaymentAdapterUnavailableError(
            "PaymentChargePortImpl: Stripe adapter not yet configured. "
            "Waiting for vitalia-payment-adapter-mvp (state: refined → developed). "
            "Use StubPaymentChargePort for local development."
        )

    async def _charge_via_mercadopago(
        self,
        *,
        tenant_id: UUID,
        appointment_id: UUID,
        amount_cents: int,
        currency: str,
        idempotency_key: str,
    ) -> ExternalPaymentResult:
        """Charge via MercadoPago adapter (scaffold wrapper).

        # DEPRECATED path: vitalia-payment-adapter-mvp not yet developed.
        # When developed, import and call MercadoPagoAdapter.create_preference().
        # Scaffolds in vitalia/backend/src/modules/vitalia/payment/mercadopago_adapter.py
        # must NOT be modified — only adapted here.

        Raises:
            PaymentAdapterUnavailableError: Always raised until mvp adapter developed.
        """
        raise PaymentAdapterUnavailableError(
            "PaymentChargePortImpl: MercadoPago adapter not yet configured. "
            "Waiting for vitalia-payment-adapter-mvp (state: refined → developed). "
            "Use StubPaymentChargePort for local development."
        )
