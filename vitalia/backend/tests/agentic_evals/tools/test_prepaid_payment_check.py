"""Tool tests — `prepaid_payment_check` (vitalia AGENTIC tool, R23 Opus 4.7).

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Acceptance per 06-tickets.yaml::T-tools-1 + 02-design § 6.1:
  A1: test_paid_true — succeeded payment_intent → paid=True + amount + currency populated
  A2: test_processing_retry — processing payment_intent → paid=False + retry_after_seconds
  A3: test_tenant_id_not_in_schema — assert tenant_id NOT in input Pydantic schema
       (security boundary: ctx-injected, NEVER client-provided)
  A4: test_latency_p99 — 100 invocations, p99 <250ms

Covers (02-design § 5.3 flow + § 6.1 spec):
  - Happy path: payment_intents.status='succeeded' → paid=True + amount/currency/method
  - Processing: payment_intents.status='processing' → paid=False + retry_after_seconds=30
  - Failed: payment_intents.status='failed' → paid=False + failure_reason
  - No payment intent: zero rows → paid=False + no_payment_initiated=True
  - Tenant isolation: tenant_A handler cannot see tenant_B payment_intents (cross-tenant)
  - Booking not found: paid=False + no_payment_initiated=True
  - Observability: trace_event recorded with sanitized payload (best-effort)
  - Observability failure: trace_event repo raising does NOT break tool turn

These are UNIT tests — repositories are mocked via in-memory fakes. Integration
tests with real Postgres land in tests/integration/ (separate test marker).
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# A3 — Tenant ID NOT in input schema (security boundary; sync test, no fixtures)
# ---------------------------------------------------------------------------


def test_tenant_id_not_in_schema() -> None:
    """A3 acceptance: tenant_id MUST NEVER appear in client-provided input.

    Security boundary per `.claude/rules/tenant-isolation.md` + 02-design § 6.1:
    > tenant_id NOT in schema — injected via tool dispatcher from ctx
    """
    from src.modules.vitalia.agentic.tools.prepaid_payment_check import (
        PrepaidPaymentCheckInput,
    )

    fields = PrepaidPaymentCheckInput.model_fields
    assert "tenant_id" not in fields, (
        "tenant_id MUST NOT be in PrepaidPaymentCheckInput — "
        "security boundary per tenant-isolation.md + 02-design § 6.1"
    )
    # booking_id is the only required field
    assert "booking_id" in fields


# ---------------------------------------------------------------------------
# Fixtures — in-memory fake repositories
# ---------------------------------------------------------------------------


class _FakeBooking:
    """In-memory stand-in for VitaliaBookingModel (minimal surface)."""

    def __init__(
        self,
        *,
        booking_id: uuid.UUID,
        tenant_id: uuid.UUID,
        deleted_at: datetime | None = None,
    ) -> None:
        self.id = booking_id
        self.tenant_id = tenant_id
        self.deleted_at = deleted_at


class _FakePaymentIntent:
    """In-memory stand-in for VitaliaPaymentIntentModel."""

    def __init__(
        self,
        *,
        intent_id: uuid.UUID,
        tenant_id: uuid.UUID,
        booking_id: uuid.UUID,
        status: str,
        amount: Decimal,
        currency: str,
        gateway: str = "mercadopago",
        failure_reason: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = intent_id
        self.tenant_id = tenant_id
        self.booking_id = booking_id
        self.status = status
        self.amount = amount
        self.currency = currency
        self.gateway = gateway
        self.failure_reason = failure_reason
        self.created_at = created_at or datetime.now(timezone.utc)


class _FakeBookingRepo:
    """Tenant-scoped fake — mirrors BookingRepository.get_by_id surface."""

    def __init__(self, tenant_id: uuid.UUID, bookings: list[_FakeBooking]) -> None:
        self._tenant_id = tenant_id
        self._rows = bookings

    async def get_by_id(self, booking_id: uuid.UUID) -> _FakeBooking | None:
        for b in self._rows:
            if (
                b.id == booking_id
                and b.tenant_id == self._tenant_id  # tenant isolation
                and b.deleted_at is None
            ):
                return b
        return None


class _FakePaymentIntentRepo:
    """Tenant-scoped fake — mirrors PaymentIntentRepository.list_by_booking."""

    def __init__(self, tenant_id: uuid.UUID, intents: list[_FakePaymentIntent]) -> None:
        self._tenant_id = tenant_id
        self._rows = intents

    async def list_by_booking(self, booking_id: uuid.UUID) -> list[_FakePaymentIntent]:
        # Order by created_at DESC to mirror real repo
        return sorted(
            [pi for pi in self._rows if pi.booking_id == booking_id and pi.tenant_id == self._tenant_id],
            key=lambda pi: pi.created_at,
            reverse=True,
        )


class _CapturingTraceRepo:
    """Captures trace_event.add() calls for observability assertions."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def add(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


class _RaisingTraceRepo:
    """Always raises — used to confirm observability failures do NOT break tool turn."""

    def add(self, **kwargs: Any) -> None:
        raise RuntimeError("trace repo down — must NOT break turn")


# ---------------------------------------------------------------------------
# A1 — Happy path: paid=True + amount + currency populated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_paid_true_succeeded_payment() -> None:
    """A1 acceptance: succeeded payment_intent → paid=True + populated fields."""
    from src.modules.vitalia.agentic.tools.prepaid_payment_check import (
        PrepaidPaymentCheckInput,
        prepaid_payment_check,
    )

    tenant_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    booking_repo = _FakeBookingRepo(tenant_id, [_FakeBooking(booking_id=booking_id, tenant_id=tenant_id)])
    payment_repo = _FakePaymentIntentRepo(
        tenant_id,
        [
            _FakePaymentIntent(
                intent_id=uuid.uuid4(),
                tenant_id=tenant_id,
                booking_id=booking_id,
                status="succeeded",
                amount=Decimal("150.00"),
                currency="USD",
                gateway="mercadopago",
            )
        ],
    )

    result = await prepaid_payment_check(
        PrepaidPaymentCheckInput(booking_id=booking_id),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        payment_intent_repo=payment_repo,
    )

    assert result.paid is True
    assert result.amount == Decimal("150.00")
    assert result.currency == "USD"
    assert result.payment_method == "mercadopago"
    assert result.failure_reason is None
    assert result.retry_after_seconds is None
    assert result.no_payment_initiated is False


# ---------------------------------------------------------------------------
# A2 — Processing: paid=False + retry_after_seconds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_processing_retry_returns_retry_after() -> None:
    """A2 acceptance: processing payment_intent → paid=False + retry_after_seconds."""
    from src.modules.vitalia.agentic.tools.prepaid_payment_check import (
        PrepaidPaymentCheckInput,
        prepaid_payment_check,
    )

    tenant_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    booking_repo = _FakeBookingRepo(tenant_id, [_FakeBooking(booking_id=booking_id, tenant_id=tenant_id)])
    payment_repo = _FakePaymentIntentRepo(
        tenant_id,
        [
            _FakePaymentIntent(
                intent_id=uuid.uuid4(),
                tenant_id=tenant_id,
                booking_id=booking_id,
                status="processing",
                amount=Decimal("200.00"),
                currency="ARS",
                gateway="mercadopago",
            )
        ],
    )

    result = await prepaid_payment_check(
        PrepaidPaymentCheckInput(booking_id=booking_id),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        payment_intent_repo=payment_repo,
    )

    assert result.paid is False
    assert result.retry_after_seconds is not None
    assert result.retry_after_seconds > 0
    # Currency from data source — NEVER hardcoded
    assert result.currency == "ARS"
    assert result.no_payment_initiated is False


# ---------------------------------------------------------------------------
# Error mode: failed payment_intent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_failed_payment_returns_failure_reason() -> None:
    """failed payment_intent → paid=False + failure_reason."""
    from src.modules.vitalia.agentic.tools.prepaid_payment_check import (
        PrepaidPaymentCheckInput,
        prepaid_payment_check,
    )

    tenant_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    booking_repo = _FakeBookingRepo(tenant_id, [_FakeBooking(booking_id=booking_id, tenant_id=tenant_id)])
    payment_repo = _FakePaymentIntentRepo(
        tenant_id,
        [
            _FakePaymentIntent(
                intent_id=uuid.uuid4(),
                tenant_id=tenant_id,
                booking_id=booking_id,
                status="failed",
                amount=Decimal("100.00"),
                currency="USD",
                gateway="stripe_connect",
                failure_reason="card_declined",
            )
        ],
    )

    result = await prepaid_payment_check(
        PrepaidPaymentCheckInput(booking_id=booking_id),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        payment_intent_repo=payment_repo,
    )

    assert result.paid is False
    assert result.failure_reason == "card_declined"
    assert result.retry_after_seconds is None
    assert result.no_payment_initiated is False


# ---------------------------------------------------------------------------
# Error mode: no payment_intent rows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_payment_initiated_returns_flag() -> None:
    """No payment_intent rows for booking → paid=False + no_payment_initiated=True."""
    from src.modules.vitalia.agentic.tools.prepaid_payment_check import (
        PrepaidPaymentCheckInput,
        prepaid_payment_check,
    )

    tenant_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    booking_repo = _FakeBookingRepo(tenant_id, [_FakeBooking(booking_id=booking_id, tenant_id=tenant_id)])
    payment_repo = _FakePaymentIntentRepo(tenant_id, [])  # no intents

    result = await prepaid_payment_check(
        PrepaidPaymentCheckInput(booking_id=booking_id),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        payment_intent_repo=payment_repo,
    )

    assert result.paid is False
    assert result.no_payment_initiated is True
    assert result.failure_reason is None
    assert result.amount is None


# ---------------------------------------------------------------------------
# Error mode: booking not found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_booking_not_found_returns_flag() -> None:
    """Booking missing or deleted → paid=False + no_payment_initiated=True."""
    from src.modules.vitalia.agentic.tools.prepaid_payment_check import (
        PrepaidPaymentCheckInput,
        prepaid_payment_check,
    )

    tenant_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    booking_repo = _FakeBookingRepo(tenant_id, [])  # not found
    payment_repo = _FakePaymentIntentRepo(tenant_id, [])

    result = await prepaid_payment_check(
        PrepaidPaymentCheckInput(booking_id=booking_id),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        payment_intent_repo=payment_repo,
    )

    assert result.paid is False
    assert result.no_payment_initiated is True


# ---------------------------------------------------------------------------
# Tenant isolation — cross-tenant attempt
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_tenant_attempt_returns_no_payment() -> None:
    """Tenant_A handler cannot see tenant_B booking — repo enforces isolation,
    handler returns no_payment_initiated=True (booking invisible)."""
    from src.modules.vitalia.agentic.tools.prepaid_payment_check import (
        PrepaidPaymentCheckInput,
        prepaid_payment_check,
    )

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    booking_id = uuid.uuid4()

    # Booking belongs to tenant_B; tenant_A repo cannot see it
    booking_repo_a = _FakeBookingRepo(tenant_a, [_FakeBooking(booking_id=booking_id, tenant_id=tenant_b)])
    payment_repo_a = _FakePaymentIntentRepo(tenant_a, [])

    result = await prepaid_payment_check(
        PrepaidPaymentCheckInput(booking_id=booking_id),
        tenant_id=tenant_a,
        booking_repo=booking_repo_a,
        payment_intent_repo=payment_repo_a,
    )

    assert result.paid is False
    assert result.no_payment_initiated is True


# ---------------------------------------------------------------------------
# Observability — trace_event recorded with sanitized payload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trace_event_recorded_when_repo_supplied() -> None:
    """Best-effort observability: when trace_repo supplied, tool records event."""
    from src.modules.vitalia.agentic.tools.prepaid_payment_check import (
        PrepaidPaymentCheckInput,
        prepaid_payment_check,
    )

    tenant_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    turn_id = uuid.uuid4()
    span_id = uuid.uuid4()

    booking_repo = _FakeBookingRepo(tenant_id, [_FakeBooking(booking_id=booking_id, tenant_id=tenant_id)])
    payment_repo = _FakePaymentIntentRepo(
        tenant_id,
        [
            _FakePaymentIntent(
                intent_id=uuid.uuid4(),
                tenant_id=tenant_id,
                booking_id=booking_id,
                status="succeeded",
                amount=Decimal("150.00"),
                currency="USD",
            )
        ],
    )
    trace_repo = _CapturingTraceRepo()

    result = await prepaid_payment_check(
        PrepaidPaymentCheckInput(booking_id=booking_id),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        payment_intent_repo=payment_repo,
        trace_event_repo=trace_repo,
        turn_id=turn_id,
        span_id=span_id,
    )

    assert result.paid is True
    assert len(trace_repo.calls) == 1
    call = trace_repo.calls[0]
    assert call["tenant_id"] == tenant_id
    assert call["turn_id"] == turn_id
    assert call["span_id"] == span_id
    assert call["event_type"] == "tool.prepaid_payment_check.completed"
    assert call["status"] == "ok"
    # Payload must contain booking_id + result fields, sanitized
    data = call["data"]
    assert "booking_id" in data
    assert data["paid"] is True


@pytest.mark.asyncio
async def test_trace_event_failure_does_not_break_turn() -> None:
    """Best-effort: trace_event repo raising MUST NOT break the tool turn (R23)."""
    from src.modules.vitalia.agentic.tools.prepaid_payment_check import (
        PrepaidPaymentCheckInput,
        prepaid_payment_check,
    )

    tenant_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    booking_repo = _FakeBookingRepo(tenant_id, [_FakeBooking(booking_id=booking_id, tenant_id=tenant_id)])
    payment_repo = _FakePaymentIntentRepo(
        tenant_id,
        [
            _FakePaymentIntent(
                intent_id=uuid.uuid4(),
                tenant_id=tenant_id,
                booking_id=booking_id,
                status="succeeded",
                amount=Decimal("150.00"),
                currency="USD",
            )
        ],
    )

    # Tool must succeed even though trace_repo raises
    result = await prepaid_payment_check(
        PrepaidPaymentCheckInput(booking_id=booking_id),
        tenant_id=tenant_id,
        booking_repo=booking_repo,
        payment_intent_repo=payment_repo,
        trace_event_repo=_RaisingTraceRepo(),
        turn_id=uuid.uuid4(),
        span_id=uuid.uuid4(),
    )

    assert result.paid is True
    assert result.amount == Decimal("150.00")


# ---------------------------------------------------------------------------
# A4 — Latency p99 <250ms (deterministic SQL)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_latency_p99_under_250ms() -> None:
    """A4 acceptance: 100 invocations, p99 <250ms.

    Pure compute (mocked I/O) — measures handler overhead, NOT DB latency.
    Real DB perf measured in integration tests.
    """
    from src.modules.vitalia.agentic.tools.prepaid_payment_check import (
        PrepaidPaymentCheckInput,
        prepaid_payment_check,
    )

    tenant_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    booking_repo = _FakeBookingRepo(tenant_id, [_FakeBooking(booking_id=booking_id, tenant_id=tenant_id)])
    payment_repo = _FakePaymentIntentRepo(
        tenant_id,
        [
            _FakePaymentIntent(
                intent_id=uuid.uuid4(),
                tenant_id=tenant_id,
                booking_id=booking_id,
                status="succeeded",
                amount=Decimal("150.00"),
                currency="USD",
            )
        ],
    )

    timings_ms: list[float] = []
    for _ in range(100):
        start = time.perf_counter()
        await prepaid_payment_check(
            PrepaidPaymentCheckInput(booking_id=booking_id),
            tenant_id=tenant_id,
            booking_repo=booking_repo,
            payment_intent_repo=payment_repo,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        timings_ms.append(elapsed_ms)

    timings_ms.sort()
    p99_index = int(len(timings_ms) * 0.99)
    p99 = timings_ms[p99_index]
    assert p99 < 250.0, (
        f"p99 latency {p99:.2f}ms exceeds 250ms budget per 02-design § 6.1. "
        f"Timings sample: min={timings_ms[0]:.2f}ms median={timings_ms[50]:.2f}ms "
        f"p99={p99:.2f}ms max={timings_ms[-1]:.2f}ms"
    )
