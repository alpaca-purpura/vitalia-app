# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Vitalia AGENTIC tool — `prepaid_payment_check`.

R23: production_code=True AGENTIC tool. Opus 4.7 EXCLUSIVE.
Story 11 T-tools-1.

Spec sources:
  * 02-design-agentic.md § 5.3 flow + § 6.1 verbose spec
  * 03-arch-agentic.md § 4.1 tool architecture
  * 06-tickets.yaml::T-tools-1 acceptance criteria A1-A4
  * 05-guidelines.md § 1.10 R23 agentic patterns

Semantics — deterministic SQL read-only two-table query:
  bookings WHERE id=booking_id AND tenant_id=ctx.tenant_id (R2 tenant-isolation)
  payment_intents WHERE booking_id=... ORDER BY created_at DESC (latest wins)

Returns paid/processing/failed/no_payment_initiated per latest payment intent
state. Currency NEVER hardcoded — read from payment_intents.currency
(per `.claude/rules/currency-handling.md`).

Tenant isolation (security boundary):
  * tenant_id MUST NEVER appear in input schema — injected from ctx via
    sales_agent tool dispatcher. Repos enforce tenant_id filter natively
    (BookingRepository + PaymentIntentRepository accept tenant_id at
    construction; queries always include `.where(tenant_id == self._tenant_id)`).

Observability (best-effort per R23):
  * trace_event_repo optional — when supplied, tool records one event
    with sanitized payload via `sanitize_payload`.
  * Repository failure during trace MUST NOT break tool turn (try/except
    + structlog warning). Anti-pattern: naked recorder call.

Idempotency: natural (read-only, no side-effects).

Cost: $0 LLM (deterministic SQL). Latency budget p50 80ms / p99 250ms
(indexed queries on booking_id + tenant_id).

Anti-duplication audit (Step 0 GATE pre-write):
  * `sanitize_payload` consumed from `luana_core_observability.recording.sanitization`
    — NEVER re-implemented (`.claude/rules/anti-duplication.md`).
  * `BaseTraceEventRepoProtocol` from `luana_core_observability.persistence.base_trace_event_repo`
    — handler accepts any concrete implementing the protocol.
  * `BookingRepository` + `PaymentIntentRepository` (T-be-3) consumed —
    NEVER raw SQL bypass (R32 enforce via repository pattern).
  * No equivalent en luana-core (per 02-design § 6.1: "vertical-medical
    specific — couples bookings + payment_intents + tenant context").
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Literal, Protocol

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger(__name__)


# ─── Configuration constants ─────────────────────────────────────────────

# Retry interval hint for sales_agent when payment is mid-flight.
# 02-design § 5.3: "IF payment_intents.status='processing' THEN return paid=false + retry_after=30s"
_PROCESSING_RETRY_SECONDS: int = 30

# Allowed payment_method literals per 02-design § 6.1 PrepaidPaymentCheckOutput.
# Mirrors gateway slugs registered in extensions.py EP-8 channel adapters.
_KNOWN_GATEWAYS: frozenset[str] = frozenset({"mercadopago", "stripe_connect", "tokenized_recurring"})


# ─── Pydantic schemas (input/output contract) ────────────────────────────


class PrepaidPaymentCheckInput(BaseModel):
    """Input schema — tenant_id intentionally OMITTED (ctx injection).

    Per 02-design § 6.1 + .claude/rules/tenant-isolation.md:
    > tenant_id NOT in schema — injected via tool dispatcher from ctx
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    booking_id: uuid.UUID = Field(
        ...,
        description="Booking UUID for which to verify payment status.",
    )


class PrepaidPaymentCheckOutput(BaseModel):
    """Result of prepaid_payment_check tool invocation.

    Per 02-design § 6.1 verbose spec.
    """

    model_config = ConfigDict(frozen=True)

    paid: bool = Field(
        False,
        description="True iff a payment_intent exists with status='succeeded'.",
    )
    amount: Decimal | None = Field(
        None,
        description="Amount charged (only populated when paid=True or status='processing').",
    )
    currency: str | None = Field(
        None,
        description="ISO 4217 currency code FROM data source (NEVER hardcoded).",
    )
    payment_method: Literal["mercadopago", "stripe_connect", "tokenized_recurring", None] = Field(
        None,
        description="Payment gateway slug.",
    )
    failure_reason: str | None = Field(
        None,
        description="Populated when payment_intent.status='failed'.",
    )
    no_payment_initiated: bool = Field(
        False,
        description="True iff no payment_intent rows for this booking.",
    )
    retry_after_seconds: int | None = Field(
        None,
        description="Hint for caller — non-None when status='processing'.",
    )


# ─── Repository protocols (decouple from concrete SQLAlchemy types) ──────


class _BookingRepoLike(Protocol):
    """Minimal surface consumed from BookingRepository."""

    async def get_by_id(self, booking_id: uuid.UUID) -> Any: ...


class _PaymentIntentRepoLike(Protocol):
    """Minimal surface consumed from PaymentIntentRepository."""

    async def list_by_booking(self, booking_id: uuid.UUID) -> list[Any]: ...


class _TraceEventRepoLike(Protocol):
    """Mirror of BaseTraceEventRepoProtocol — see luana_core_observability."""

    def add(
        self,
        *,
        tenant_id: uuid.UUID,
        turn_id: uuid.UUID,
        span_id: uuid.UUID,
        event_type: str,
        name: str | None = ...,
        data: dict[str, Any] | None = ...,
        duration_ms: int | None = ...,
        status: str = ...,
        **agent_specific: Any,
    ) -> Any: ...


# ─── Handler ─────────────────────────────────────────────────────────────


async def prepaid_payment_check(
    input: PrepaidPaymentCheckInput,
    *,
    tenant_id: uuid.UUID,
    booking_repo: _BookingRepoLike,
    payment_intent_repo: _PaymentIntentRepoLike,
    trace_event_repo: _TraceEventRepoLike | None = None,
    turn_id: uuid.UUID | None = None,
    span_id: uuid.UUID | None = None,
) -> PrepaidPaymentCheckOutput:
    """Verify payment_status for a booking pre-confirmation.

    See module docstring for full semantics + spec references.

    Parameters
    ----------
    input
        Pydantic input with `booking_id` only — tenant_id NEVER here.
    tenant_id
        Injected from ctx by sales_agent tool dispatcher (NEVER from input).
    booking_repo
        Tenant-scoped BookingRepository (T-be-3). MUST already be bound to
        the same tenant_id passed here — caller's responsibility.
    payment_intent_repo
        Tenant-scoped PaymentIntentRepository (T-be-3). Same tenant binding.
    trace_event_repo
        Optional — when supplied, tool records one trace_event for the
        invocation. Best-effort (try/except + structlog warning).
    turn_id / span_id
        Required iff trace_event_repo supplied — caller's correlation IDs.

    Returns
    -------
    PrepaidPaymentCheckOutput — never raises tool-side errors; downstream
    errors (DB issues, etc.) bubble up via the repo layer.
    """
    # 1. Lookup booking — tenant_id enforcement is intrinsic to repo (tenant-scoped).
    booking = await booking_repo.get_by_id(input.booking_id)
    if booking is None:
        # 02-design § 5.3: "IF no payment_intent row THEN return paid=false + no_payment_initiated=true"
        # If booking is gone/deleted/foreign-tenant → SAME response (don't leak existence).
        result = PrepaidPaymentCheckOutput(no_payment_initiated=True)
        await _emit_trace_event(
            trace_event_repo,
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            booking_id=input.booking_id,
            result=result,
            duration_ms=None,
        )
        return result

    # 2. Lookup payment intents for this booking (latest-first).
    intents = await payment_intent_repo.list_by_booking(input.booking_id)
    if not intents:
        result = PrepaidPaymentCheckOutput(no_payment_initiated=True)
        await _emit_trace_event(
            trace_event_repo,
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            booking_id=input.booking_id,
            result=result,
            duration_ms=None,
        )
        return result

    # 3. Latest payment intent determines status. Repo returns ORDER BY created_at DESC.
    latest = intents[0]
    payment_method = _normalize_gateway(getattr(latest, "gateway", None))

    if latest.status == "succeeded":
        result = PrepaidPaymentCheckOutput(
            paid=True,
            amount=latest.amount,
            currency=latest.currency,
            payment_method=payment_method,
        )
    elif latest.status == "processing":
        result = PrepaidPaymentCheckOutput(
            paid=False,
            amount=latest.amount,
            currency=latest.currency,
            payment_method=payment_method,
            retry_after_seconds=_PROCESSING_RETRY_SECONDS,
        )
    elif latest.status == "failed":
        result = PrepaidPaymentCheckOutput(
            paid=False,
            currency=latest.currency,
            payment_method=payment_method,
            failure_reason=getattr(latest, "failure_reason", None) or "payment_failed",
        )
    else:
        # initiated / refunded / unknown → treat as no payment confirmed.
        # Note: refunded is rare in pre-confirm context; treated as not paid.
        result = PrepaidPaymentCheckOutput(
            paid=False,
            currency=latest.currency,
            payment_method=payment_method,
            no_payment_initiated=(latest.status == "initiated"),
        )

    await _emit_trace_event(
        trace_event_repo,
        tenant_id=tenant_id,
        turn_id=turn_id,
        span_id=span_id,
        booking_id=input.booking_id,
        result=result,
        duration_ms=None,
    )
    return result


# ─── Helpers ─────────────────────────────────────────────────────────────


def _normalize_gateway(
    gateway: str | None,
) -> Literal["mercadopago", "stripe_connect", "tokenized_recurring", None]:
    """Map gateway slug to typed literal. Unknown gateways → None (defensive)."""
    if gateway is None:
        return None
    if gateway in _KNOWN_GATEWAYS:
        # mypy/pyright narrow via the membership check
        return gateway  # type: ignore[return-value]
    logger.warning("prepaid_payment_check.unknown_gateway", gateway=gateway)
    return None


async def _emit_trace_event(
    trace_event_repo: _TraceEventRepoLike | None,
    *,
    tenant_id: uuid.UUID,
    turn_id: uuid.UUID | None,
    span_id: uuid.UUID | None,
    booking_id: uuid.UUID,
    result: PrepaidPaymentCheckOutput,
    duration_ms: int | None,
) -> None:
    """Best-effort trace_event emission. NEVER breaks tool turn (R23).

    Skips silently if repo not supplied or correlation IDs missing.
    Logs warning on persistence failure.
    """
    if trace_event_repo is None or turn_id is None or span_id is None:
        return

    try:
        # Sanitize payload before persist — PII never reaches trace store.
        payload = sanitize_payload(
            {
                "booking_id": str(booking_id),
                "paid": result.paid,
                "amount": str(result.amount) if result.amount is not None else None,
                "currency": result.currency,
                "payment_method": result.payment_method,
                "no_payment_initiated": result.no_payment_initiated,
                "failure_reason": result.failure_reason,
                "retry_after_seconds": result.retry_after_seconds,
            }
        )
        trace_event_repo.add(
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type="tool.prepaid_payment_check.completed",
            name="prepaid_payment_check",
            data=payload,
            duration_ms=duration_ms,
            status="ok",
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "prepaid_payment_check.trace_event_persist_failed",
            exc=str(exc),
            booking_id=str(booking_id),
            tenant_id=str(tenant_id),
        )


__all__ = [
    "PrepaidPaymentCheckInput",
    "PrepaidPaymentCheckOutput",
    "prepaid_payment_check",
]
