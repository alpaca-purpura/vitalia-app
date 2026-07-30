"""Integration tests for VitaliaTokenizedRecurringAdapter.

Acceptance criteria (03-arch-be.md § 11.3 + ticket T-payment-2):
  A2: Tokenized installment idempotent — re-run same installment_n no double-charge
  Additional: cron_handler receives next installment due correctly

All external calls are mocked — no real Stripe/MP API credentials required.

Per .claude/rules/tdd-mandatory.md: these tests must go RED before implementation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest

# ── Helpers ───────────────────────────────────────────────────────────────────


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestTokenizedRecurringAdapterIdempotency:
    """A2: Same installment_n MUST NOT trigger double-charge."""

    @pytest.mark.integration
    async def test_installment_idempotent(self) -> None:
        """A2: Charging same (patient_id, treatment_id, installment_n) twice → second call skipped.

        No duplicate Stripe/MP API call must be issued.
        The second call must return the SAME PaymentResult (not a new charge).
        """
        from src.modules.vitalia.payment.tokenized_recurring_adapter import (
            Installment,
            VitaliaTokenizedRecurringAdapter,
        )

        patient_id = uuid.uuid4()
        treatment_id = uuid.uuid4()

        # In-memory idempotency store (simulates the persisted payment_schedule table)
        processed: dict[str, dict] = {}

        async def _mock_charge_stripe(*, idempotency_key: str, **kwargs) -> dict:  # noqa: ANN003
            if idempotency_key in processed:
                return processed[idempotency_key]
            result = {
                "payment_intent_id": f"pi_{uuid.uuid4().hex[:8]}",
                "status": "succeeded",
                "idempotency_key": idempotency_key,
            }
            processed[idempotency_key] = result
            return result

        adapter = VitaliaTokenizedRecurringAdapter(
            gateway="stripe_connect",
            stripe_secret_key="sk_test_fake",
            _charge_fn=_mock_charge_stripe,  # inject for test
        )

        installment = Installment(
            installment_n=1,
            amount=Decimal("89990"),
            currency="CLP",
            scheduled_at=_utc_now(),
        )

        # First call — should charge
        result_1 = await adapter.charge_installment(
            patient_id=patient_id,
            treatment_id=treatment_id,
            installment=installment,
        )

        # Second call — identical params — MUST return same result, no new API call
        result_2 = await adapter.charge_installment(
            patient_id=patient_id,
            treatment_id=treatment_id,
            installment=installment,
        )

        assert result_1.payment_intent_id == result_2.payment_intent_id
        assert result_1.idempotency_key == result_2.idempotency_key
        # Only one real charge should have been issued
        assert len(processed) == 1

    @pytest.mark.integration
    async def test_different_installment_n_is_separate_charge(self) -> None:
        """Different installment_n → separate, independent charge (no contamination)."""
        from src.modules.vitalia.payment.tokenized_recurring_adapter import (
            Installment,
            VitaliaTokenizedRecurringAdapter,
        )

        patient_id = uuid.uuid4()
        treatment_id = uuid.uuid4()
        processed: dict[str, dict] = {}

        async def _mock_charge(*, idempotency_key: str, **kwargs) -> dict:  # noqa: ANN003
            if idempotency_key in processed:
                return processed[idempotency_key]
            result = {
                "payment_intent_id": f"pi_{uuid.uuid4().hex[:8]}",
                "status": "succeeded",
                "idempotency_key": idempotency_key,
            }
            processed[idempotency_key] = result
            return result

        adapter = VitaliaTokenizedRecurringAdapter(
            gateway="stripe_connect",
            stripe_secret_key="sk_test_fake",
            _charge_fn=_mock_charge,
        )

        installment_1 = Installment(
            installment_n=1,
            amount=Decimal("89990"),
            currency="CLP",
            scheduled_at=_utc_now(),
        )
        installment_2 = Installment(
            installment_n=2,
            amount=Decimal("89990"),
            currency="CLP",
            scheduled_at=_utc_now(),
        )

        result_1 = await adapter.charge_installment(
            patient_id=patient_id,
            treatment_id=treatment_id,
            installment=installment_1,
        )
        result_2 = await adapter.charge_installment(
            patient_id=patient_id,
            treatment_id=treatment_id,
            installment=installment_2,
        )

        # Two different installments → two separate payment intents
        assert result_1.payment_intent_id != result_2.payment_intent_id
        assert len(processed) == 2

    @pytest.mark.integration
    async def test_different_treatment_id_is_separate_charge(self) -> None:
        """Different treatment_id + same installment_n → separate charge."""
        from src.modules.vitalia.payment.tokenized_recurring_adapter import (
            Installment,
            VitaliaTokenizedRecurringAdapter,
        )

        patient_id = uuid.uuid4()
        treatment_a = uuid.uuid4()
        treatment_b = uuid.uuid4()
        processed: dict[str, dict] = {}

        async def _mock_charge(*, idempotency_key: str, **kwargs) -> dict:  # noqa: ANN003
            if idempotency_key in processed:
                return processed[idempotency_key]
            result = {
                "payment_intent_id": f"pi_{uuid.uuid4().hex[:8]}",
                "status": "succeeded",
                "idempotency_key": idempotency_key,
            }
            processed[idempotency_key] = result
            return result

        adapter = VitaliaTokenizedRecurringAdapter(
            gateway="stripe_connect",
            stripe_secret_key="sk_test_fake",
            _charge_fn=_mock_charge,
        )

        installment = Installment(
            installment_n=1,
            amount=Decimal("89990"),
            currency="CLP",
            scheduled_at=_utc_now(),
        )

        result_a = await adapter.charge_installment(
            patient_id=patient_id,
            treatment_id=treatment_a,
            installment=installment,
        )
        result_b = await adapter.charge_installment(
            patient_id=patient_id,
            treatment_id=treatment_b,
            installment=installment,
        )

        assert result_a.payment_intent_id != result_b.payment_intent_id
        assert len(processed) == 2


class TestTokenizedRecurringAdapterIdempotencyKey:
    """Verify idempotency key derivation scheme."""

    @pytest.mark.integration
    def test_idempotency_key_includes_all_three_components(self) -> None:
        """Key = (patient_id, treatment_id, installment_n) — all 3 must be present."""
        from src.modules.vitalia.payment.tokenized_recurring_adapter import (
            VitaliaTokenizedRecurringAdapter,
        )

        patient_id = uuid.uuid4()
        treatment_id = uuid.uuid4()
        installment_n = 3

        key = VitaliaTokenizedRecurringAdapter.build_idempotency_key(
            patient_id=patient_id,
            treatment_id=treatment_id,
            installment_n=installment_n,
        )

        assert str(patient_id) in key
        assert str(treatment_id) in key
        assert str(installment_n) in key

    @pytest.mark.integration
    def test_idempotency_key_deterministic(self) -> None:
        """Same inputs → same key (deterministic, not random)."""
        from src.modules.vitalia.payment.tokenized_recurring_adapter import (
            VitaliaTokenizedRecurringAdapter,
        )

        patient_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        treatment_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

        key_a = VitaliaTokenizedRecurringAdapter.build_idempotency_key(
            patient_id=patient_id,
            treatment_id=treatment_id,
            installment_n=1,
        )
        key_b = VitaliaTokenizedRecurringAdapter.build_idempotency_key(
            patient_id=patient_id,
            treatment_id=treatment_id,
            installment_n=1,
        )

        assert key_a == key_b


class TestTokenizedRecurringAdapterCronHandler:
    """Cron handler schedules next installment via @luana/core/scheduling.cron_worker."""

    @pytest.mark.integration
    async def test_schedule_recurring_registers_cron_jobs(self) -> None:
        """schedule_recurring() persists installment rows + registers cron for each."""
        from src.modules.vitalia.payment.tokenized_recurring_adapter import (
            Installment,
            VitaliaTokenizedRecurringAdapter,
        )

        patient_id = uuid.uuid4()
        treatment_id = uuid.uuid4()

        registered_jobs: list[dict] = []

        async def _mock_cron_register(**kwargs) -> None:  # noqa: ANN003
            registered_jobs.append(kwargs)

        async def _mock_charge(*, idempotency_key: str, **kwargs) -> dict:  # noqa: ANN003
            return {
                "payment_intent_id": f"pi_{uuid.uuid4().hex[:8]}",
                "status": "scheduled",
                "idempotency_key": idempotency_key,
            }

        adapter = VitaliaTokenizedRecurringAdapter(
            gateway="stripe_connect",
            stripe_secret_key="sk_test_fake",
            _charge_fn=_mock_charge,
            _cron_register_fn=_mock_cron_register,
        )

        installments = [
            Installment(installment_n=1, amount=Decimal("89990"), currency="CLP", scheduled_at=_utc_now()),
            Installment(installment_n=2, amount=Decimal("89990"), currency="CLP", scheduled_at=_utc_now()),
            Installment(installment_n=3, amount=Decimal("89990"), currency="CLP", scheduled_at=_utc_now()),
            Installment(installment_n=4, amount=Decimal("89990"), currency="CLP", scheduled_at=_utc_now()),
        ]

        schedule = await adapter.schedule_recurring(
            patient_id=patient_id,
            treatment_id=treatment_id,
            installments=installments,
        )

        # 4 installments → 4 cron registrations (one per installment)
        assert len(registered_jobs) == 4
        assert schedule.total_installments == 4
        assert schedule.currency == "CLP"

    @pytest.mark.integration
    async def test_schedule_recurring_mp_gateway(self) -> None:
        """MP gateway path: schedule_recurring works for MercadoPago too."""
        from src.modules.vitalia.payment.tokenized_recurring_adapter import (
            Installment,
            VitaliaTokenizedRecurringAdapter,
        )

        patient_id = uuid.uuid4()
        treatment_id = uuid.uuid4()
        registered_jobs: list[dict] = []

        async def _mock_cron_register(**kwargs) -> None:  # noqa: ANN003
            registered_jobs.append(kwargs)

        async def _mock_charge(*, idempotency_key: str, **kwargs) -> dict:  # noqa: ANN003
            return {
                "payment_intent_id": f"mp_pref_{uuid.uuid4().hex[:8]}",
                "status": "scheduled",
                "idempotency_key": idempotency_key,
            }

        adapter = VitaliaTokenizedRecurringAdapter(
            gateway="mercadopago",
            mp_access_token="TEST-fake-mp-token",
            _charge_fn=_mock_charge,
            _cron_register_fn=_mock_cron_register,
        )

        installments = [
            Installment(installment_n=1, amount=Decimal("10000"), currency="ARS", scheduled_at=_utc_now()),
            Installment(installment_n=2, amount=Decimal("10000"), currency="ARS", scheduled_at=_utc_now()),
        ]

        schedule = await adapter.schedule_recurring(
            patient_id=patient_id,
            treatment_id=treatment_id,
            installments=installments,
        )

        assert len(registered_jobs) == 2
        assert schedule.gateway == "mercadopago"
        assert schedule.currency == "ARS"


class TestTokenizedRecurringAdapterCurrencyHandling:
    """Currency must come from data, never hardcoded."""

    @pytest.mark.integration
    async def test_currency_forwarded_from_installment(self) -> None:
        """Currency in result must match installment currency (no hardcoded USD/ARS)."""
        from src.modules.vitalia.payment.tokenized_recurring_adapter import (
            Installment,
            VitaliaTokenizedRecurringAdapter,
        )

        async def _mock_charge(*, idempotency_key: str, currency: str, **kwargs) -> dict:  # noqa: ANN003
            return {
                "payment_intent_id": f"pi_{uuid.uuid4().hex[:8]}",
                "status": "succeeded",
                "idempotency_key": idempotency_key,
                "currency": currency,
            }

        adapter = VitaliaTokenizedRecurringAdapter(
            gateway="stripe_connect",
            stripe_secret_key="sk_test_fake",
            _charge_fn=_mock_charge,
        )

        for currency_code in ("CLP", "ARS", "MXN", "USD", "PEN", "COP"):
            installment = Installment(
                installment_n=1,
                amount=Decimal("100"),
                currency=currency_code,
                scheduled_at=_utc_now(),
            )
            # Use unique IDs per iteration to avoid idempotency collision
            result = await adapter.charge_installment(
                patient_id=uuid.uuid4(),
                treatment_id=uuid.uuid4(),
                installment=installment,
            )
            assert result.currency == currency_code, f"Expected {currency_code}, got {result.currency}"
