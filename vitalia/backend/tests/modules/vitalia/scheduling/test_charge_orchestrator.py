"""Unit tests — ChargeOrchestrator saga (T-5 acceptance criteria).

TDD RED first, then GREEN via implementation in charge_orchestrator.py.

Coverage:
  A1: Saga happy path (charge + fiscal emit + 2 audit log rows)
  A2: Payment 503 → charge_failed audit + no fiscal emit + no payment row persisted
  A3: Fiscal 503 post-charge → charge persisted + warning + retry-emit standalone
  A4: Concurrent charge (race) → BalanceAlreadyChargedError → 409 (via exception)
  A5: Idempotency key → return prior response (no double charge)

HIPAA-lite: tests use stub UUIDs. No PHI values in assertions.
All mocks inject via constructor (DI — no monkeypatch).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.modules.vitalia.scheduling.application.ports.fiscal_emit_port import (
    FiscalAdapterUnavailableError,
    FiscalDocResult,
    FiscalEmitError,
)
from src.modules.vitalia.scheduling.application.ports.payment_charge_port import (
    ExternalPaymentResult,
    PaymentAdapterUnavailableError,
)
from src.modules.vitalia.scheduling.application.services.charge_orchestrator import (
    ChargeOrchestrator,
    ChargeRequest,
    ChargeResponse,
)
from src.modules.vitalia.scheduling.domain.exceptions import BalanceAlreadyChargedError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
USER_ID = uuid4()
APPOINTMENT_ID = uuid4()
PAYMENT_ID = uuid4()
IDEMPOTENCY_KEY = "f7a3c2d8-0001-4000-a000-111122223333"


def _make_charge_request(
    *,
    idempotency_key: str = IDEMPOTENCY_KEY,
    emit_invoice: bool = True,
    fiscal_doc_type: str = "boleta",
    amount_cents: int = 15000,
    currency: str = "PEN",
    method: str = "efectivo",
) -> ChargeRequest:
    """Build a standard ChargeRequest for tests."""
    return ChargeRequest(
        appointment_id=APPOINTMENT_ID,
        amount_cents=amount_cents,
        currency=currency,
        method=method,
        emit_invoice=emit_invoice,
        fiscal_doc_type=fiscal_doc_type,
        idempotency_key=idempotency_key,
    )


def _make_payment_model_stub(
    *,
    payment_id: UUID = PAYMENT_ID,
    amount: int = 15000,
    currency: str = "PEN",
    method: str = "efectivo",
    external_payment_id: str = IDEMPOTENCY_KEY,
    fiscal_doc_id: UUID | None = None,
) -> MagicMock:
    """Minimal AppointmentPaymentModel mock (struct-like)."""
    m = MagicMock()
    m.id = payment_id
    m.amount = amount
    m.currency = currency
    m.method = method
    m.external_payment_id = external_payment_id
    m.fiscal_doc_id = fiscal_doc_id
    return m


def _make_fiscal_doc_stub(
    *,
    doc_id: UUID | None = None,
    doc_number: str = "STUB-00001",
    doc_url: str | None = "https://cdn.example.com/stub-doc.pdf",
    status: str = "emitted",
) -> MagicMock:
    """Minimal FiscalDocumentModel mock."""
    m = MagicMock()
    m.id = doc_id or uuid4()
    m.doc_number = doc_number
    m.doc_url = doc_url
    m.status = status
    return m


@pytest.fixture
def payment_port() -> AsyncMock:
    """Default payment port — succeeds with stub external result."""
    port = AsyncMock()
    port.charge.return_value = ExternalPaymentResult(
        external_payment_id="ext-tx-001",
        gateway="stub",
        raw_response={"stub": True},
    )
    return port


@pytest.fixture
def fiscal_port() -> AsyncMock:
    """Default fiscal port — succeeds with stub doc result."""
    port = AsyncMock()
    port.emit.return_value = FiscalDocResult(
        doc_number="STUB-00001",
        doc_url="https://cdn.example.com/doc.pdf",
        provider="nubefact_stub",
    )
    return port


@pytest.fixture
def payment_repo() -> AsyncMock:
    """Default payment repo stub — no prior idempotency match."""
    repo = AsyncMock()
    repo.find_by_idempotency_key.return_value = None  # no prior match
    repo.lock_for_charge.return_value = None  # lock succeeds
    repo.create.return_value = _make_payment_model_stub()
    return repo


@pytest.fixture
def audit_writer() -> AsyncMock:
    """Async audit writer stub."""
    return AsyncMock()


@pytest.fixture
def fiscal_repo() -> AsyncMock:
    """Default fiscal document repo stub."""
    repo = AsyncMock()
    repo.create.return_value = _make_fiscal_doc_stub()
    repo.update_status.return_value = True
    return repo


@pytest.fixture
def growth_emitter() -> AsyncMock:
    """Growth Studio emitter stub."""
    return AsyncMock()


def _make_orchestrator(
    *,
    payment_port: AsyncMock,
    fiscal_port: AsyncMock,
    payment_repo: AsyncMock,
    audit_writer: AsyncMock,
    fiscal_repo: AsyncMock,
    growth_emitter: AsyncMock,
) -> ChargeOrchestrator:
    """Construct ChargeOrchestrator with injected stubs."""
    return ChargeOrchestrator(
        payment_port=payment_port,
        fiscal_port=fiscal_port,
        payment_repo=payment_repo,
        audit_writer=audit_writer,
        fiscal_doc_repo=fiscal_repo,
        growth_emitter=growth_emitter,
    )


# ---------------------------------------------------------------------------
# A1 — Happy path: charge + fiscal emit + 2 audit rows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_pe_boleta(
    payment_port: AsyncMock,
    fiscal_port: AsyncMock,
    payment_repo: AsyncMock,
    audit_writer: AsyncMock,
    fiscal_repo: AsyncMock,
    growth_emitter: AsyncMock,
) -> None:
    """A1: Saga happy path — charge succeeds + boleta emitted + 2 audit rows."""
    orchestrator = _make_orchestrator(
        payment_port=payment_port,
        fiscal_port=fiscal_port,
        payment_repo=payment_repo,
        audit_writer=audit_writer,
        fiscal_repo=fiscal_repo,
        growth_emitter=growth_emitter,
    )
    request = _make_charge_request(emit_invoice=True, fiscal_doc_type="boleta")

    response: ChargeResponse = await orchestrator.execute(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        user_id=USER_ID,
        request=request,
    )

    # Payment charged
    payment_port.charge.assert_awaited_once()
    charge_call = payment_port.charge.call_args
    assert charge_call.kwargs["amount_cents"] == 15000
    assert charge_call.kwargs["currency"] == "PEN"
    assert charge_call.kwargs["idempotency_key"] == IDEMPOTENCY_KEY

    # Payment row persisted
    payment_repo.create.assert_awaited_once()

    # Fiscal emit called
    fiscal_port.emit.assert_awaited_once()
    emit_call = fiscal_port.emit.call_args
    assert emit_call.kwargs["doc_type"] == "boleta"
    assert emit_call.kwargs["country"] == "PE"

    # Fiscal doc persisted
    fiscal_repo.create.assert_awaited_once()

    # Audit: 2 rows (charge + invoice_emitted)
    assert audit_writer.write.await_count == 2
    actions = [c.kwargs["action"] for c in audit_writer.write.call_args_list]
    assert "charge" in actions
    assert "invoice_emitted" in actions

    # Response
    assert response.fiscal_emission_status == "emitted"
    assert response.fiscal_doc_url == "https://cdn.example.com/doc.pdf"
    assert response.amount_cents == 15000
    assert response.currency == "PEN"

    # Growth event emitted (charge_completed)
    growth_emitter.emit_event.assert_awaited()


# ---------------------------------------------------------------------------
# A2 — Payment 503 → charge_failed audit + no fiscal emit + no payment row
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_payment_adapter_503(
    fiscal_port: AsyncMock,
    payment_repo: AsyncMock,
    audit_writer: AsyncMock,
    fiscal_repo: AsyncMock,
    growth_emitter: AsyncMock,
) -> None:
    """A2: Payment port raises 503 → charge_failed audit + fiscal skipped + no payment row."""
    failing_payment_port = AsyncMock()
    failing_payment_port.charge.side_effect = PaymentAdapterUnavailableError("stub payment adapter unavailable")

    orchestrator = _make_orchestrator(
        payment_port=failing_payment_port,
        fiscal_port=fiscal_port,
        payment_repo=payment_repo,
        audit_writer=audit_writer,
        fiscal_repo=fiscal_repo,
        growth_emitter=growth_emitter,
    )
    request = _make_charge_request()

    from src.modules.vitalia.scheduling.application.services.charge_orchestrator import (
        PaymentAdapterError,
    )

    with pytest.raises(PaymentAdapterError) as exc_info:
        await orchestrator.execute(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            request=request,
        )

    assert exc_info.value.error_code == "PAYMENT_ADAPTER_503"

    # Fiscal emit NOT called
    fiscal_port.emit.assert_not_awaited()

    # Payment row NOT persisted
    payment_repo.create.assert_not_awaited()

    # Audit: only charge_failed
    assert audit_writer.write.await_count == 1
    action = audit_writer.write.call_args.kwargs["action"]
    assert action == "charge_failed"


# ---------------------------------------------------------------------------
# A3 — Fiscal 503 post-charge → charge persisted + warning + retry emit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fiscal_503_post_charge(
    payment_port: AsyncMock,
    payment_repo: AsyncMock,
    audit_writer: AsyncMock,
    fiscal_repo: AsyncMock,
    growth_emitter: AsyncMock,
) -> None:
    """A3: Fiscal port fails after charge OK → payment persisted, fiscal_emission_status='failed'."""
    failing_fiscal_port = AsyncMock()
    failing_fiscal_port.emit.side_effect = FiscalAdapterUnavailableError("stub fiscal adapter unavailable")

    orchestrator = _make_orchestrator(
        payment_port=payment_port,
        fiscal_port=failing_fiscal_port,
        payment_repo=payment_repo,
        audit_writer=audit_writer,
        fiscal_repo=fiscal_repo,
        growth_emitter=growth_emitter,
    )
    request = _make_charge_request(emit_invoice=True, fiscal_doc_type="boleta")

    response: ChargeResponse = await orchestrator.execute(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        user_id=USER_ID,
        request=request,
    )

    # Saga compensation: charge succeeded
    payment_port.charge.assert_awaited_once()
    payment_repo.create.assert_awaited_once()

    # Fiscal emit attempted but failed
    failing_fiscal_port.emit.assert_awaited_once()

    # Audit: charge (success) + fiscal_emit_failed_post_charge
    assert audit_writer.write.await_count == 2
    actions = [c.kwargs["action"] for c in audit_writer.write.call_args_list]
    assert "charge" in actions
    assert "fiscal_emit_failed_post_charge" in actions

    # Response: charge OK, fiscal failed
    assert response.fiscal_emission_status == "failed"
    assert response.fiscal_doc_url is None
    assert response.fiscal_error_message is not None

    # Fiscal doc created with status='failed' for retry endpoint
    fiscal_repo.create.assert_awaited_once()
    create_call = fiscal_repo.create.call_args.kwargs
    assert create_call.get("status") == "failed"


# ---------------------------------------------------------------------------
# A4 — Concurrent charge (race) → BalanceAlreadyChargedError → exception
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_charge_optimistic_lock(
    payment_port: AsyncMock,
    fiscal_port: AsyncMock,
    audit_writer: AsyncMock,
    fiscal_repo: AsyncMock,
    growth_emitter: AsyncMock,
) -> None:
    """A4: lock_for_charge raises BalanceAlreadyChargedError → caller gets 409 signal."""
    locking_payment_repo = AsyncMock()
    locking_payment_repo.find_by_idempotency_key.return_value = None  # not idempotent hit
    locking_payment_repo.lock_for_charge.side_effect = BalanceAlreadyChargedError(
        payment_id=PAYMENT_ID,
        expected_version=1,
    )

    orchestrator = _make_orchestrator(
        payment_port=payment_port,
        fiscal_port=fiscal_port,
        payment_repo=locking_payment_repo,
        audit_writer=audit_writer,
        fiscal_repo=fiscal_repo,
        growth_emitter=growth_emitter,
    )
    request = _make_charge_request()

    from src.modules.vitalia.scheduling.application.services.charge_orchestrator import (
        ChargeConflictError,
    )

    with pytest.raises(ChargeConflictError) as exc_info:
        await orchestrator.execute(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=USER_ID,
            request=request,
        )

    assert exc_info.value.error_code == "BALANCE_ALREADY_CHARGED"

    # Payment port NOT called (lock failed first)
    payment_port.charge.assert_not_awaited()

    # Fiscal NOT called
    fiscal_port.emit.assert_not_awaited()


# ---------------------------------------------------------------------------
# A5 — Idempotency key match → return prior response (no double charge)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_idempotency_key_returns_prior_response(
    payment_port: AsyncMock,
    fiscal_port: AsyncMock,
    audit_writer: AsyncMock,
    fiscal_repo: AsyncMock,
    growth_emitter: AsyncMock,
) -> None:
    """A5: Prior payment found by idempotency_key → return prior response, no double charge."""
    prior_payment = _make_payment_model_stub(
        payment_id=PAYMENT_ID,
        amount=15000,
        currency="PEN",
        method="efectivo",
        external_payment_id=IDEMPOTENCY_KEY,
    )
    idempotent_payment_repo = AsyncMock()
    idempotent_payment_repo.find_by_idempotency_key.return_value = prior_payment

    # Prior fiscal doc already emitted
    prior_fiscal = _make_fiscal_doc_stub(
        doc_id=uuid4(),
        doc_number="STUB-00001",
        doc_url="https://cdn.example.com/prior-doc.pdf",
        status="emitted",
    )
    fiscal_repo.get_by_payment_id.return_value = prior_fiscal

    orchestrator = _make_orchestrator(
        payment_port=payment_port,
        fiscal_port=fiscal_port,
        payment_repo=idempotent_payment_repo,
        audit_writer=audit_writer,
        fiscal_repo=fiscal_repo,
        growth_emitter=growth_emitter,
    )
    request = _make_charge_request()

    response: ChargeResponse = await orchestrator.execute(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        user_id=USER_ID,
        request=request,
    )

    # Payment port NOT called (duplicate detected)
    payment_port.charge.assert_not_awaited()

    # Fiscal port NOT called
    fiscal_port.emit.assert_not_awaited()

    # Lock NOT acquired (idempotency check is before lock)
    idempotent_payment_repo.lock_for_charge.assert_not_awaited()

    # Response mirrors prior payment
    assert response.amount_cents == 15000
    assert response.currency == "PEN"
    # Idempotency response should indicate prior result
    assert response.idempotency_replay is True


# ---------------------------------------------------------------------------
# Bonus: fiscal emit error (provider rejects) — same saga as FiscalAdapterUnavailableError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fiscal_emit_error_post_charge_uses_compensation(
    payment_port: AsyncMock,
    payment_repo: AsyncMock,
    audit_writer: AsyncMock,
    fiscal_repo: AsyncMock,
    growth_emitter: AsyncMock,
) -> None:
    """FiscalEmitError (provider rejects doc) uses same compensation: charge stays, fiscal failed."""
    rejecting_fiscal_port = AsyncMock()
    rejecting_fiscal_port.emit.side_effect = FiscalEmitError("Nubefact: RUC inválido")

    orchestrator = _make_orchestrator(
        payment_port=payment_port,
        fiscal_port=rejecting_fiscal_port,
        payment_repo=payment_repo,
        audit_writer=audit_writer,
        fiscal_repo=fiscal_repo,
        growth_emitter=growth_emitter,
    )
    request = _make_charge_request(emit_invoice=True, fiscal_doc_type="factura")

    response: ChargeResponse = await orchestrator.execute(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        user_id=USER_ID,
        request=request,
    )

    # Charge succeeded
    payment_port.charge.assert_awaited_once()
    payment_repo.create.assert_awaited_once()

    # Fiscal failed
    assert response.fiscal_emission_status == "failed"
    assert "RUC inválido" in (response.fiscal_error_message or "")

    # Audit: charge + fiscal_emit_failed_post_charge
    actions = [c.kwargs["action"] for c in audit_writer.write.call_args_list]
    assert "charge" in actions
    assert "fiscal_emit_failed_post_charge" in actions


# ---------------------------------------------------------------------------
# Bonus: emit_invoice=False → fiscal emit skipped
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_invoice_requested_skips_fiscal_emit(
    payment_port: AsyncMock,
    fiscal_port: AsyncMock,
    payment_repo: AsyncMock,
    audit_writer: AsyncMock,
    fiscal_repo: AsyncMock,
    growth_emitter: AsyncMock,
) -> None:
    """emit_invoice=False → fiscal emit skipped entirely, status='skipped'."""
    orchestrator = _make_orchestrator(
        payment_port=payment_port,
        fiscal_port=fiscal_port,
        payment_repo=payment_repo,
        audit_writer=audit_writer,
        fiscal_repo=fiscal_repo,
        growth_emitter=growth_emitter,
    )
    request = _make_charge_request(emit_invoice=False, fiscal_doc_type=None)

    response: ChargeResponse = await orchestrator.execute(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        user_id=USER_ID,
        request=request,
    )

    fiscal_port.emit.assert_not_awaited()
    assert response.fiscal_emission_status == "skipped"

    # Only 1 audit row (charge), not invoice_emitted
    actions = [c.kwargs["action"] for c in audit_writer.write.call_args_list]
    assert "invoice_emitted" not in actions
    assert "charge" in actions
