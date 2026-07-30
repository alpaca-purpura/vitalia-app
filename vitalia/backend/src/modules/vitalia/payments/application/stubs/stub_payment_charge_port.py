# cap: payment.payment-gateways-latam-recurring
# story-origin: vitalia-fase2-s1-TBD
"""StubPaymentChargePort — service-blocker Option A stub.

# DEPRECATED: replace when vitalia-payment-adapter-mvp state=done.
# Architecture test test_no_stub_in_prod_path.py (post-story-merge ratchet)
# will enforce stub-free production before merge. Until then, this stub
# satisfies the interface contract and allows F2-S1 build + tests to proceed.

Usage (DI factory in charge router T-7):
    from src.modules.vitalia.payments.application.stubs.stub_payment_charge_port import (
        StubPaymentChargePort,
    )
    payment_port = StubPaymentChargePort(mode="happy")  # or "unavailable"

Modes:
  "happy"       — Returns ExternalPaymentResult with stub external_payment_id.
  "unavailable" — Raises PaymentAdapterUnavailableError (simulates adapter down).

Replacement path (when vitalia-payment-adapter-mvp is developed):
  Replace with PaymentChargePortImpl (payments/application/payment_charge_port_impl.py)
  which selects Stripe/MercadoPago adapter based on tenant.config.payment_gateway.
"""

from __future__ import annotations

import structlog

from src.modules.vitalia.scheduling.application.ports.payment_charge_port import (
    ExternalPaymentResult,
    PaymentAdapterUnavailableError,
    PaymentChargePort,
)

logger = structlog.get_logger()


# DEPRECATED: replace when vitalia-payment-adapter-mvp state=done
class StubPaymentChargePort(PaymentChargePort):
    """Stub payment charge port for F2-S1 service-blocker pattern (Option A).

    This stub satisfies the PaymentChargePort ABC contract.
    Mode "happy" returns a fake ExternalPaymentResult.
    Mode "unavailable" raises PaymentAdapterUnavailableError (for testing saga compensation).

    # DEPRECATED: replace when vitalia-payment-adapter-mvp state=done.
    """

    def __init__(self, *, mode: str = "happy") -> None:
        """Initialize stub payment port.

        Args:
            mode: "happy" (returns ExternalPaymentResult) or
                  "unavailable" (raises PaymentAdapterUnavailableError).
        """
        if mode not in ("happy", "unavailable"):
            raise ValueError(f"StubPaymentChargePort: mode must be 'happy' or 'unavailable', got '{mode}'")
        self._mode = mode

    async def charge(
        self,
        *,
        tenant_id,
        clinic_id,
        appointment_id,
        amount_cents: int,
        currency: str,
        method: str,
        idempotency_key: str,
    ) -> ExternalPaymentResult:
        """Stub charge — logs request, returns fake result or raises 503.

        # DEPRECATED: replace when vitalia-payment-adapter-mvp state=done.
        """
        logger.info(
            "stub_payment_charge_port.charge",
            mode=self._mode,
            amount_cents=amount_cents,
            currency=currency,
            method=method,
            idempotency_key=idempotency_key,
            # NOTE: No PHI logged here (appointment_id is UUID, no patient data)
        )

        if self._mode == "unavailable":
            raise PaymentAdapterUnavailableError(
                "StubPaymentChargePort: vitalia-payment-adapter-mvp not yet developed "
                "(service-blocker Option A). Replace this stub when state=done."
            )

        # Happy path: return stub external result
        return ExternalPaymentResult(
            external_payment_id=f"stub-{idempotency_key}",
            gateway="stub_gateway",
            raw_response={
                "stub": True,
                "mode": "happy",
                "amount_cents": amount_cents,
                "currency": currency,
            },
        )
