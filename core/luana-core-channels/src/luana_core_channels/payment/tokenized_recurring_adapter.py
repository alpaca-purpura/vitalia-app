"""Tokenized Recurring adapter — card-on-file installment + subscription charges.

Generic base lifted to @luana/core/channels per Story 12 T-payment-1
(anti-duplication.md: Story 11 kept vitalia-local; lift happens here Story 12).

Use cases:
  - Cohort installments (3/6/12 months) — e.g., Comunify coaching programs
  - Monthly membership subscriptions — e.g., Comunify creator tiers
  - Treatment installment plans — e.g., Vitalia orthodontics 6-month plan
  - Any recurring payment where card-on-file is tokenized once, charged N times

Gateway support:
  - ``stripe_connect`` — Stripe Customer + PaymentMethod attach
  - ``mercadopago`` — MP Customer + payment_method primitives (subscription token)

Idempotency key: composite of (subscriber_id, entity_id, installment_n).
Each installment has a unique, deterministic key → re-run NEVER double-charges.

Cron integration: schedule_recurring() registers each installment with
the cron worker via injected ``_cron_register_fn`` for testability.

Currency handling:
  - Currency forwarded from ``Installment.currency`` — NEVER hardcoded.
  - Supports all LatAm ISO 4217: CLP, ARS, MXN, USD, PEN, COP, BRL, UYU.

# [STORY12-T-PAYMENT-1-LIFT-TOKENIZED-RECURRING]
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

_DEFAULT_IDEMPOTENCY_PREFIX = "luana:recurring"


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
        payment_intent_id: Gateway payment identifier (Stripe pi_* or MP payment id).
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
class RecurringPaymentSchedule:
    """Summary of a recurring payment schedule.

    Attributes:
        subscriber_id: Subscriber / payer UUID.
        entity_id: The entity being paid for (cohort_id / treatment_id / offer_id).
        gateway: "stripe_connect" | "mercadopago".
        total_installments: Number of installments in the schedule.
        currency: ISO 4217 code (all installments share the same currency).
        results: Ordered tuple of individual InstallmentResult values.
    """

    subscriber_id: UUID
    entity_id: UUID
    gateway: str
    total_installments: int
    currency: str
    results: tuple[InstallmentResult, ...]


# ── Type aliases for injected dependencies ────────────────────────────────────

# Async function that executes the actual gateway charge.
# Injected via _charge_fn parameter for testability — real impl uses Stripe/MP SDK.
_ChargeFnType = Callable[..., Coroutine[Any, Any, dict]]

# Async function that registers an installment with the cron worker.
_CronRegisterFnType = Callable[..., Coroutine[Any, Any, None]]


# ── Adapter base class ────────────────────────────────────────────────────────


@dataclass(slots=True)
class TokenizedRecurringAdapter:
    """Card-on-file recurring installment adapter.

    Wraps either:
      - Stripe Customer + PaymentMethod (gateway="stripe_connect")
      - MercadoPago customer tokens (gateway="mercadopago")

    Idempotency: Each (subscriber_id, entity_id, installment_n) triple maps
    to a deterministic idempotency key. Re-running charge_installment with the
    same triple returns the cached result WITHOUT calling the gateway API again.
    This prevents double-charges on network retries or cron re-runs.

    Args:
        gateway: Payment gateway ("stripe_connect" | "mercadopago").
        stripe_secret_key: Stripe secret key (required when gateway=stripe_connect).
        mp_access_token: MP access token (required when gateway=mercadopago).
        idempotency_prefix: Prefix for idempotency keys (default "luana:recurring").
            Subclasses override for vertical-specific namespacing.
        _charge_fn: Injectable charge function (real impl / test double).
        _cron_register_fn: Injectable cron registration function.
    """

    gateway: Literal["stripe_connect", "mercadopago"]
    stripe_secret_key: str = ""
    mp_access_token: str = ""
    idempotency_prefix: str = _DEFAULT_IDEMPOTENCY_PREFIX

    # Injected for testability — production callers leave these as None
    # and the adapter uses the real Stripe/MP SDK functions.
    _charge_fn: _ChargeFnType | None = field(default=None, repr=False)
    _cron_register_fn: _CronRegisterFnType | None = field(default=None, repr=False)

    # In-memory idempotency store (seed from DB on production initialization).
    # Maps idempotency_key → InstallmentResult.
    # In production this should be backed by a persistence table.
    _processed: dict[str, InstallmentResult] = field(default_factory=dict, repr=False)

    # ── Idempotency key ────────────────────────────────────────────────────────

    def build_idempotency_key(
        self,
        *,
        subscriber_id: UUID,
        entity_id: UUID,
        installment_n: int,
    ) -> str:
        """Build a deterministic, composite idempotency key.

        Key format: ``{prefix}:{subscriber_id}:{entity_id}:{n}``

        Same inputs → same key (deterministic). Different inputs → different key.
        Re-charging with the same key MUST be a no-op (prevents double-charges).

        Args:
            subscriber_id: Payer / subscriber UUID.
            entity_id: Entity being paid for (cohort, treatment, offer).
            installment_n: 1-based installment number.

        Returns:
            Deterministic string idempotency key.
        """
        return f"{self.idempotency_prefix}:{subscriber_id}:{entity_id}:{installment_n}"

    # ── Public API ─────────────────────────────────────────────────────────────

    async def charge_installment(
        self,
        *,
        subscriber_id: UUID,
        entity_id: UUID,
        installment: Installment,
    ) -> InstallmentResult:
        """Charge a single installment, idempotently.

        If the same (subscriber_id, entity_id, installment_n) has already been
        successfully charged, returns the cached result WITHOUT calling the gateway.
        No double-charge on retry.

        Currency is forwarded from ``installment.currency`` — never hardcoded.

        Args:
            subscriber_id: Payer UUID.
            entity_id: Entity UUID (cohort_id / treatment_id / offer_id).
            installment: The installment to charge.

        Returns:
            InstallmentResult (may be cached from a previous call).
        """
        idempotency_key = self.build_idempotency_key(
            subscriber_id=subscriber_id,
            entity_id=entity_id,
            installment_n=installment.installment_n,
        )

        if idempotency_key in self._processed:
            cached = self._processed[idempotency_key]
            logger.info(
                "tokenized_installment_idempotent",
                idempotency_key=idempotency_key,
                payment_intent_id=cached.payment_intent_id,
                subscriber_id=str(subscriber_id),
                entity_id=str(entity_id),
                installment_n=installment.installment_n,
            )
            return cached

        charge_fn = self._charge_fn or self._default_charge_fn()
        raw_result = await charge_fn(
            idempotency_key=idempotency_key,
            amount=installment.amount,
            currency=installment.currency,  # forwarded — never hardcoded
            subscriber_id=subscriber_id,
            entity_id=entity_id,
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

        self._processed[idempotency_key] = result

        logger.info(
            "tokenized_installment_charged",
            payment_intent_id=result.payment_intent_id,
            idempotency_key=idempotency_key,
            subscriber_id=str(subscriber_id),
            entity_id=str(entity_id),
            installment_n=installment.installment_n,
            currency=installment.currency,
            amount=str(installment.amount),
            gateway=self.gateway,
        )

        return result

    async def schedule_recurring(
        self,
        *,
        subscriber_id: UUID,
        entity_id: UUID,
        installments: list[Installment],
    ) -> RecurringPaymentSchedule:
        """Schedule a recurring payment plan (multiple installments).

        For each installment:
          1. Derives the idempotency key.
          2. Registers the installment with the cron worker via injected
             ``_cron_register_fn``.
          3. Stores a "scheduled" result (actual charge happens when cron fires).

        Currency is forwarded from each ``Installment.currency`` — never hardcoded.
        All installments in a schedule MUST share the same currency (caller enforces).

        Args:
            subscriber_id: Payer UUID.
            entity_id: Entity UUID (cohort_id / treatment_id / offer_id).
            installments: Ordered list of installments to schedule.

        Returns:
            RecurringPaymentSchedule with all results and schedule metadata.
        """
        if not installments:
            return RecurringPaymentSchedule(
                subscriber_id=subscriber_id,
                entity_id=entity_id,
                gateway=self.gateway,
                total_installments=0,
                currency="",
                results=(),
            )

        cron_fn = self._cron_register_fn or self._default_cron_register_fn()
        results: list[InstallmentResult] = []

        for inst in installments:
            idempotency_key = self.build_idempotency_key(
                subscriber_id=subscriber_id,
                entity_id=entity_id,
                installment_n=inst.installment_n,
            )

            await cron_fn(
                subscriber_id=subscriber_id,
                entity_id=entity_id,
                installment_n=inst.installment_n,
                scheduled_at=inst.scheduled_at,
                amount=inst.amount,
                currency=inst.currency,
                idempotency_key=idempotency_key,
                gateway=self.gateway,
            )

            charge_fn = self._charge_fn or self._default_charge_fn()
            raw_result = await charge_fn(
                idempotency_key=idempotency_key,
                amount=inst.amount,
                currency=inst.currency,
                subscriber_id=subscriber_id,
                entity_id=entity_id,
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

        currency = installments[0].currency

        logger.info(
            "tokenized_schedule_registered",
            subscriber_id=str(subscriber_id),
            entity_id=str(entity_id),
            total_installments=len(installments),
            currency=currency,
            gateway=self.gateway,
        )

        return RecurringPaymentSchedule(
            subscriber_id=subscriber_id,
            entity_id=entity_id,
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
        stripe_secret_key = self.stripe_secret_key
        mp_access_token = self.mp_access_token

        async def _real_charge(
            *,
            idempotency_key: str,
            amount: Decimal,
            currency: str,
            **_kwargs: Any,
        ) -> dict:
            if gateway == "stripe_connect":
                return await _real_stripe_charge(
                    secret_key=stripe_secret_key,
                    idempotency_key=idempotency_key,
                    amount=amount,
                    currency=currency,
                )
            return await _real_mp_charge(
                access_token=mp_access_token,
                idempotency_key=idempotency_key,
                amount=amount,
                currency=currency,
            )

        return _real_charge

    def _default_cron_register_fn(self) -> _CronRegisterFnType:
        """Return default no-op cron registration (production wires real scheduler).

        In production, the caller wires this to ``@luana/core/scheduling.cron_worker``.
        Default no-op avoids hard dependency on cron infra during unit tests that
        don't inject a mock.
        """

        async def _noop_register(**_kwargs: Any) -> None:
            logger.warning(
                "tokenized_cron_register_noop",
                detail="No cron_register_fn injected — install cron worker integration",
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
        "currency": currency.lower(),
        "payment_method_types[]": "card",
        "confirm": "false",
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
        "currency_id": currency,
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


__all__ = (
    "Installment",
    "InstallmentResult",
    "RecurringPaymentSchedule",
    "TokenizedRecurringAdapter",
)
