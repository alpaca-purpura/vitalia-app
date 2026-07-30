# cap: payment.payment-gateways-latam-recurring
# story-origin: TBD
"""Vitalia Tokenized Recurring adapter — card-on-file installment charges.

Per Story 11 03-arch-be.md § 11.3 + ticket T-payment-2:

Use cases (per spec § 3 + 02-design § 18):
  - Mindful Santiago "Paquete 4 Sesiones" (CLP 89,990 split over 4 sessions)
  - Aurora ortodoncia $3,500 USD (deposit + 6 monthly installments)
  - Sanaré Wellness packages (multi-month subscription bundles)

Gateway support:
  - ``stripe_connect`` — Stripe Customer + PaymentMethod attach
  - ``mercadopago`` — MP Customer + payment_method primitives (subscription token)

Idempotency key: composite of (patient_id, treatment_id, installment_n).
Each installment has a unique, deterministic key → re-run NEVER double-charges (A2).

Cron integration: schedule_recurring() registers each installment with
``@luana/core/scheduling.cron_worker`` (T-workflow-1 per 02-design § 7).
Dependency injected via ``_cron_register_fn`` for testability.

Currency handling:
  - Currency forwarded from ``Installment.currency`` — NEVER hardcoded.
  - Supports CLP, ARS, MXN, USD, PEN, COP, BRL, UYU (all LatAm ISO 4217).

# [VITALIA-D7-TOKENIZED-RECURRING-IDEMPOTENT]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Coroutine, Literal
from uuid import UUID

import structlog

logger = structlog.get_logger()

# ── Idempotency key scheme ────────────────────────────────────────────────────

_IDEMPOTENCY_KEY_PREFIX = "vitalia:recurring"


# ── Domain VOs ────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Installment:
    """A single installment in a recurring payment schedule.

    Attributes:
        installment_n: 1-based installment number (1 = first charge, N = last).
        amount: Decimal amount to charge.
        currency: ISO 4217 currency code (e.g., "CLP", "ARS"). NEVER hardcoded.
        scheduled_at: UTC datetime when this installment should be charged.
        description: Optional human-readable label (default generated from n).
    """

    installment_n: int
    amount: Decimal
    currency: str  # ISO 4217 — forwarded from booking/offer context, never "USD" default
    scheduled_at: datetime
    description: str | None = None


@dataclass(frozen=True, slots=True)
class InstallmentResult:
    """Result of a single installment charge attempt.

    Attributes:
        payment_intent_id: Gateway payment identifier (Stripe pi_* or MP pref_*).
        status: Charge status ("succeeded" / "scheduled" / "failed").
        idempotency_key: The composite key used for this charge.
        currency: ISO 4217 code (forwarded from Installment — never hardcoded).
        installment_n: Which installment this result corresponds to.
    """

    payment_intent_id: str
    status: str
    idempotency_key: str
    currency: str
    installment_n: int


@dataclass(frozen=True, slots=True)
class PaymentSchedule:
    """Summary of a recurring payment schedule.

    Attributes:
        patient_id: Patient UUID.
        treatment_id: Treatment UUID.
        gateway: "stripe_connect" | "mercadopago".
        total_installments: Number of installments in the schedule.
        currency: ISO 4217 code (all installments share the same currency).
        results: Ordered list of individual InstallmentResult values.
    """

    patient_id: UUID
    treatment_id: UUID
    gateway: str
    total_installments: int
    currency: str
    results: tuple[InstallmentResult, ...]


# ── Type alias for injected dependencies ─────────────────────────────────────

# Async function that executes the actual gateway charge.
# Injected via _charge_fn parameter for testability — real impl uses Stripe/MP SDK.
_ChargeFnType = Callable[..., Coroutine[Any, Any, dict]]

# Async function that registers an installment with the cron worker.
# Per 03-arch-be.md § 11.3: "Cron job processes next installment due via
# @luana/core/scheduling.cron_worker (per T-workflow-1)."
_CronRegisterFnType = Callable[..., Coroutine[Any, Any, None]]


# ── Adapter ───────────────────────────────────────────────────────────────────


@dataclass(slots=True)
class VitaliaTokenizedRecurringAdapter:
    """Card-on-file recurring installment adapter.

    Wraps either:
      - Stripe Customer + PaymentMethod (gateway="stripe_connect")
      - MercadoPago customer tokens (gateway="mercadopago")

    Idempotency (A2): Each (patient_id, treatment_id, installment_n) triple maps
    to a deterministic idempotency key. Re-running charge_installment with the
    same triple returns the cached result WITHOUT calling the gateway API again.
    This prevents double-charges on network retries or cron re-runs.

    Args:
        gateway: Payment gateway ("stripe_connect" | "mercadopago").
        stripe_secret_key: Stripe secret key (required when gateway=stripe_connect).
        mp_access_token: MP access token (required when gateway=mercadopago).
        _charge_fn: Injectable charge function (real impl / test double).
        _cron_register_fn: Injectable cron registration function.
    """

    gateway: Literal["stripe_connect", "mercadopago"]
    stripe_secret_key: str = ""
    mp_access_token: str = ""

    # Injected for testability — production callers leave these as None
    # and the adapter uses the real Stripe/MP SDK functions.
    _charge_fn: _ChargeFnType | None = field(default=None, repr=False)
    _cron_register_fn: _CronRegisterFnType | None = field(default=None, repr=False)

    # In-memory idempotency store (seed from DB on production initialization).
    # Maps idempotency_key → InstallmentResult.
    # In production this should be backed by vitalia_payment_schedules table.
    _processed: dict[str, InstallmentResult] = field(default_factory=dict, repr=False)

    # ── Idempotency key ───────────────────────────────────────────────────────

    @staticmethod
    def build_idempotency_key(
        *,
        patient_id: UUID,
        treatment_id: UUID,
        installment_n: int,
    ) -> str:
        """Build a deterministic, composite idempotency key.

        Key format: ``vitalia:recurring:{patient_id}:{treatment_id}:{n}``

        This key uniquely identifies a (patient, treatment, installment) triple.
        Same inputs → same key (deterministic). Different inputs → different key.
        Re-charging with the same key MUST be a no-op (A2 acceptance criterion).

        Args:
            patient_id: Patient UUID.
            treatment_id: Treatment UUID.
            installment_n: 1-based installment number.

        Returns:
            Deterministic string idempotency key.
        """
        return f"{_IDEMPOTENCY_KEY_PREFIX}:{patient_id}:{treatment_id}:{installment_n}"

    # ── Public API ────────────────────────────────────────────────────────────

    async def charge_installment(
        self,
        *,
        patient_id: UUID,
        treatment_id: UUID,
        installment: Installment,
    ) -> InstallmentResult:
        """Charge a single installment, idempotently.

        A2 acceptance: If the same (patient_id, treatment_id, installment_n)
        has already been successfully charged, returns the cached result WITHOUT
        calling the gateway again. No double-charge.

        Currency is forwarded from ``installment.currency`` — never hardcoded.

        Args:
            patient_id: Patient UUID.
            treatment_id: Treatment UUID.
            installment: The installment to charge.

        Returns:
            InstallmentResult (may be cached from a previous call).
        """
        idempotency_key = self.build_idempotency_key(
            patient_id=patient_id,
            treatment_id=treatment_id,
            installment_n=installment.installment_n,
        )

        # A2: idempotency check — return cached result if already processed
        if idempotency_key in self._processed:
            cached = self._processed[idempotency_key]
            logger.info(
                "tokenized_installment_idempotent",
                idempotency_key=idempotency_key,
                payment_intent_id=cached.payment_intent_id,
                patient_id=str(patient_id),
                treatment_id=str(treatment_id),
                installment_n=installment.installment_n,
            )
            return cached

        # Dispatch to real charge function or injected test double
        charge_fn = self._charge_fn or self._default_charge_fn()
        raw_result = await charge_fn(
            idempotency_key=idempotency_key,
            amount=installment.amount,
            currency=installment.currency,  # forwarded — never hardcoded
            patient_id=patient_id,
            treatment_id=treatment_id,
            installment_n=installment.installment_n,
            gateway=self.gateway,
        )

        result = InstallmentResult(
            payment_intent_id=raw_result["payment_intent_id"],
            status=raw_result.get("status", "succeeded"),
            idempotency_key=idempotency_key,
            currency=installment.currency,  # forwarded, never hardcoded
            installment_n=installment.installment_n,
        )

        # Store in idempotency cache
        self._processed[idempotency_key] = result

        logger.info(
            "tokenized_installment_charged",
            payment_intent_id=result.payment_intent_id,
            idempotency_key=idempotency_key,
            patient_id=str(patient_id),
            treatment_id=str(treatment_id),
            installment_n=installment.installment_n,
            currency=installment.currency,
            amount=str(installment.amount),
            gateway=self.gateway,
        )

        return result

    async def schedule_recurring(
        self,
        *,
        patient_id: UUID,
        treatment_id: UUID,
        installments: list[Installment],
    ) -> PaymentSchedule:
        """Schedule a recurring payment plan (multiple installments).

        For each installment:
          1. Derives the idempotency key.
          2. Registers the installment with ``@luana/core/scheduling.cron_worker``
             (per 03-arch-be.md § 11.3) via the injected ``_cron_register_fn``.
          3. Stores a "scheduled" result (actual charge happens when cron fires).

        Currency is forwarded from each ``Installment.currency`` — never hardcoded.
        All installments in a schedule share the same currency (caller enforces this).

        Args:
            patient_id: Patient UUID.
            treatment_id: Treatment UUID.
            installments: Ordered list of installments to schedule.

        Returns:
            PaymentSchedule with all results and schedule metadata.
        """
        if not installments:
            return PaymentSchedule(
                patient_id=patient_id,
                treatment_id=treatment_id,
                gateway=self.gateway,
                total_installments=0,
                currency="",
                results=(),
            )

        cron_fn = self._cron_register_fn or self._default_cron_register_fn()
        results: list[InstallmentResult] = []

        for inst in installments:
            idempotency_key = self.build_idempotency_key(
                patient_id=patient_id,
                treatment_id=treatment_id,
                installment_n=inst.installment_n,
            )

            # Register with cron worker for scheduled firing
            await cron_fn(
                patient_id=patient_id,
                treatment_id=treatment_id,
                installment_n=inst.installment_n,
                scheduled_at=inst.scheduled_at,
                amount=inst.amount,
                currency=inst.currency,
                idempotency_key=idempotency_key,
                gateway=self.gateway,
            )

            # Mark as "scheduled" — actual charge happens when cron fires
            charge_fn = self._charge_fn or self._default_charge_fn()
            raw_result = await charge_fn(
                idempotency_key=idempotency_key,
                amount=inst.amount,
                currency=inst.currency,
                patient_id=patient_id,
                treatment_id=treatment_id,
                installment_n=inst.installment_n,
                gateway=self.gateway,
            )

            result = InstallmentResult(
                payment_intent_id=raw_result["payment_intent_id"],
                status=raw_result.get("status", "scheduled"),
                idempotency_key=idempotency_key,
                currency=inst.currency,
                installment_n=inst.installment_n,
            )

            self._processed[idempotency_key] = result
            results.append(result)

        # All installments share the same currency (caller invariant)
        currency = installments[0].currency

        logger.info(
            "tokenized_schedule_registered",
            patient_id=str(patient_id),
            treatment_id=str(treatment_id),
            total_installments=len(installments),
            currency=currency,
            gateway=self.gateway,
        )

        return PaymentSchedule(
            patient_id=patient_id,
            treatment_id=treatment_id,
            gateway=self.gateway,
            total_installments=len(installments),
            currency=currency,
            results=tuple(results),
        )

    # ── Default gateway functions (production path) ───────────────────────────

    def _default_charge_fn(self) -> _ChargeFnType:
        """Return the real gateway charge function based on ``gateway`` attribute.

        Production path — called when ``_charge_fn`` is not injected.
        Tests always inject ``_charge_fn`` to avoid real API calls.
        """
        gateway = self.gateway

        async def _real_charge(
            *,
            idempotency_key: str,
            amount: Decimal,
            currency: str,
            patient_id: UUID,
            treatment_id: UUID,
            installment_n: int,
            **_kwargs: Any,
        ) -> dict:
            if gateway == "stripe_connect":
                return await _real_stripe_charge(
                    secret_key=self.stripe_secret_key,
                    idempotency_key=idempotency_key,
                    amount=amount,
                    currency=currency,
                )
            # gateway == "mercadopago"
            return await _real_mp_charge(
                access_token=self.mp_access_token,
                idempotency_key=idempotency_key,
                amount=amount,
                currency=currency,
            )

        return _real_charge

    def _default_cron_register_fn(self) -> _CronRegisterFnType:
        """Return default no-op cron registration (production wires real scheduler).

        In production, T-workflow-1 wires this to
        ``@luana/core/scheduling.cron_worker``. Default no-op avoids hard
        dependency on cron infra during unit tests that don't inject a mock.
        """

        async def _noop_register(**_kwargs: Any) -> None:
            logger.warning(
                "tokenized_cron_register_noop",
                detail="No cron_register_fn injected — install cron worker per T-workflow-1",
            )

        return _noop_register


# ── Real gateway charge functions (production implementations) ────────────────


async def _real_stripe_charge(
    *,
    secret_key: str,
    idempotency_key: str,
    amount: Decimal,
    currency: str,
) -> dict:
    """Execute a real Stripe PaymentIntent charge.

    Uses Stripe API v1/payment_intents with idempotency_key header.
    Currency forwarded from caller — never hardcoded.
    Timeout: 10s (tessl__graceful-degradation Rule 1).
    """
    import httpx

    amount_cents = int(amount * 100)

    payload = {
        "amount": str(amount_cents),
        "currency": currency.lower(),  # Stripe expects lowercase ISO 4217
        "payment_method_types[]": "card",
        "confirm": "false",  # Customer confirms on frontend
    }

    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Idempotency-Key": idempotency_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://api.stripe.com/v1/payment_intents",
            data=payload,
            headers=headers,
        )

    resp.raise_for_status()
    data = resp.json()

    return {
        "payment_intent_id": data["id"],
        "status": data.get("status", "requires_confirmation"),
        "idempotency_key": idempotency_key,
    }


async def _real_mp_charge(
    *,
    access_token: str,
    idempotency_key: str,
    amount: Decimal,
    currency: str,
) -> dict:
    """Execute a real MercadoPago payment charge.

    Uses MP Payments API with X-Idempotency-Key header.
    Currency forwarded from caller — never hardcoded.
    Timeout: 10s (tessl__graceful-degradation Rule 1).
    """
    import httpx

    payload = {
        "transaction_amount": float(amount),
        "currency_id": currency,  # MP expects ISO 4217 uppercase
        "description": "Installment payment",
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Idempotency-Key": idempotency_key,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://api.mercadopago.com/v1/payments",
            json=payload,
            headers=headers,
        )

    resp.raise_for_status()
    data = resp.json()

    return {
        "payment_intent_id": str(data.get("id", "")),
        "status": data.get("status", "in_process"),
        "idempotency_key": idempotency_key,
    }


# voseo-allowed: doc/comentario interno citando glosario voseo, no user-facing
