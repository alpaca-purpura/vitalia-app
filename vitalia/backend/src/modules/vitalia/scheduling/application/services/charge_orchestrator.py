# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""ChargeOrchestrator — saga payment + fiscal emit + audit log + compensation.

Rule (03-arch § 7.2 — service-blocker pattern Option A):
  This orchestrator is the single authoritative service for the "cobrar saldo" flow.
  It is consumed by the POST /api/v1/payments/charge endpoint (T-7 wire-up).

Saga pattern (03-arch § 7.2):
  1. Idempotency check — find_by_idempotency_key() → if prior result, return it (A5)
  2. Optimistic lock — lock_for_charge() → BalanceAlreadyChargedError → 409 (A4)
  3. Payment port charge — PaymentChargePort.charge() → PaymentAdapterUnavailableError → 503 (A2)
  4. Persist payment row (A1 happy)
  5. Optional fiscal emit — FiscalEmitPort.emit() → saga compensation on failure (A3)
  6. Persist fiscal document row (emitted or failed)
  7. Audit log rows (charge + invoice_emitted | fiscal_emit_failed_post_charge)
  8. Emit growth_studio_event charge_completed (fire-and-forget, NOT part of PHI audit)
  9. Return ChargeResponse

Compensation rule (A3 — architect A6):
  Charge OK + fiscal emit FAIL → DO NOT rollback charge.
  Record fiscal_document with status='failed'.
  Return response with fiscal_emission_status='failed' + fiscal_error_message.
  FE shows warning banner + "Reintentar emisión" button (standalone POST /fiscal/emit).

Currency rule (03-arch § 8.5 + .claude/rules/currency-handling.md):
  currency field is REQUIRED in ChargeRequestDTO and stored verbatim in payment row.
  NEVER defaults to 'USD'. Comes from FE CobrarSaldoSubform (tenant locale or override).

HIPAA-lite (vitalia/.claude/rules/hipaa-lite.md):
  Audit log sync write WITHIN same AsyncSession (transactional atomicity).
  No PHI values in audit payload (only UUIDs + amounts + statuses).
  Dual filter (tenant_id + clinic_id) applied by repository layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

import structlog

from src.modules.vitalia.scheduling.application.ports.fiscal_emit_port import (
    FiscalAdapterUnavailableError,
    FiscalEmitError,
    FiscalEmitPort,
)
from src.modules.vitalia.scheduling.application.ports.payment_charge_port import (
    PaymentAdapterUnavailableError,
    PaymentChargePort,
)
from src.modules.vitalia.scheduling.domain.exceptions import BalanceAlreadyChargedError

logger = structlog.get_logger()

__all__ = [
    "ChargeOrchestrator",
    "ChargeRequest",
    "ChargeResponse",
    "ChargeConflictError",
    "PaymentAdapterError",
]


# ---------------------------------------------------------------------------
# DTOs (application layer — no FastAPI dependency)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChargeRequest:
    """Input to ChargeOrchestrator.execute().

    Mirrors ChargeRequestDTO from api/dtos but lives in application layer
    (no Pydantic dependency — pure Python dataclass for testability).

    Currency is REQUIRED — never default to 'USD' (currency-handling.md).
    """

    appointment_id: UUID
    amount_cents: int
    currency: str  # ISO 4217 (PEN/ARS/MXN/USD/...) — required
    method: str  # PaymentMethod value
    emit_invoice: bool
    idempotency_key: str  # client-generated UUID string
    fiscal_doc_type: str | None = None  # required when emit_invoice=True


@dataclass
class ChargeResponse:
    """Output of ChargeOrchestrator.execute().

    Mirrors ChargeResponseDTO from api/dtos but lives in application layer.
    fiscal_emission_status: "emitted" | "pending" | "failed" | "skipped"
    idempotency_replay: True when response is a replay of prior successful charge.
    """

    payment_id: UUID
    appointment_id: UUID
    amount_cents: int
    currency: str
    method: str
    external_payment_id: str | None
    fiscal_doc_id: UUID | None
    fiscal_doc_url: str | None
    fiscal_emission_status: Literal["emitted", "pending", "failed", "skipped"]
    fiscal_error_message: str | None = None
    idempotency_replay: bool = False


# ---------------------------------------------------------------------------
# Domain exceptions (raised by orchestrator — router maps to HTTP status)
# ---------------------------------------------------------------------------


class ChargeConflictError(Exception):
    """Raised on optimistic lock failure (concurrent charge detected).

    Router maps to HTTP 409 with ChargeConflict409DTO.
    Per 03-arch § 7.2 — A4 (SC-5 race condition prevention).
    """

    error_code: str = "BALANCE_ALREADY_CHARGED"

    def __init__(self, *, payment_id: UUID | None = None) -> None:
        """Initialize ChargeConflictError.

        Args:
            payment_id: Payment UUID that triggered the conflict (for logging).
        """
        self.payment_id = payment_id
        super().__init__(
            "Concurrent charge detected — balance_version has already changed. "
            "Reload payment state before retrying. "
            "Use idempotency key to check if prior charge already succeeded."
        )


class PaymentAdapterError(Exception):
    """Raised when payment adapter is unavailable (503).

    Router maps to HTTP 503 with error_code='PAYMENT_ADAPTER_503'.
    Per 03-arch § 7.2 — A2 (payment port 503 compensation).
    """

    error_code: str = "PAYMENT_ADAPTER_503"

    def __init__(self, *, detail: str = "Payment adapter temporarily unavailable") -> None:
        """Initialize PaymentAdapterError.

        Args:
            detail: Human-readable error detail (NO PHI).
        """
        self.detail = detail
        super().__init__(detail)


# ---------------------------------------------------------------------------
# ChargeOrchestrator
# ---------------------------------------------------------------------------


class ChargeOrchestrator:
    """Saga orchestrator for appointment balance charges.

    Dependencies injected via constructor (no global state — testable).
    All dependencies are async-compatible.

    DI factory (in T-7 router):
        orchestrator = ChargeOrchestrator(
            payment_port=PaymentChargePortImpl(payment_gateway=tenant.config.payment_gateway),
            fiscal_port=FiscalEmitPortImpl(country=tenant.country),
            payment_repo=AppointmentPaymentRepository(session=db),
            audit_writer=AsyncAuditWriter(session=db),
            fiscal_doc_repo=FiscalDocumentRepository(session=db),
            growth_emitter=GrowthStudioEmitter(session=db),
        )
    """

    def __init__(
        self,
        *,
        payment_port: PaymentChargePort,
        fiscal_port: FiscalEmitPort,
        payment_repo: object,  # AppointmentPaymentRepository (typed via duck-typing)
        audit_writer: object,  # AsyncAuditWriter
        fiscal_doc_repo: object,  # FiscalDocumentRepository
        growth_emitter: object,  # GrowthStudioEmitter
    ) -> None:
        """Initialize ChargeOrchestrator with injected dependencies.

        Args:
            payment_port: Concrete PaymentChargePort (real or stub).
            fiscal_port: Concrete FiscalEmitPort (real or stub).
            payment_repo: AppointmentPaymentRepository for persistence.
            audit_writer: AsyncAuditWriter for HIPAA-lite audit log.
            fiscal_doc_repo: FiscalDocumentRepository for fiscal records.
            growth_emitter: GrowthStudioEmitter for UX funnel telemetry.
        """
        self._payment_port = payment_port
        self._fiscal_port = fiscal_port
        self._payment_repo = payment_repo
        self._audit = audit_writer
        self._fiscal_doc_repo = fiscal_doc_repo
        self._growth = growth_emitter

    async def execute(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        request: ChargeRequest,
    ) -> ChargeResponse:
        """Execute the charge saga.

        Steps:
          1. Idempotency check (A5)
          2. Optimistic lock (A4)
          3. Payment charge (A2 — PaymentAdapterUnavailableError → raises PaymentAdapterError)
          4. Persist payment row
          5. Optional fiscal emit + persist fiscal doc (A3 compensation if fail)
          6. Audit log rows (sync within session)
          7. Growth Studio event (fire-and-forget)
          8. Return ChargeResponse

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite dual filter).
            user_id: User performing the action (for audit log).
            request: ChargeRequest dataclass.

        Returns:
            ChargeResponse with payment + fiscal emission status.

        Raises:
            ChargeConflictError: On optimistic lock failure (→ HTTP 409).
            PaymentAdapterError: When payment port is unavailable (→ HTTP 503).
        """
        # ── Step 1: Idempotency check (A5) ─────────────────────────────────
        existing_payment = await self._payment_repo.find_by_idempotency_key(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            idempotency_key=request.idempotency_key,
        )

        if existing_payment is not None:
            logger.info(
                "charge_orchestrator.idempotency_replay",
                idempotency_key=request.idempotency_key,
                payment_id=str(existing_payment.id),
                tenant_id=str(tenant_id),
            )
            # Lookup existing fiscal document if any
            prior_fiscal = await self._fiscal_doc_repo.get_by_payment_id(
                existing_payment.id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
            )
            return self._project_response(
                payment=existing_payment,
                fiscal_doc=prior_fiscal,
                idempotency_replay=True,
            )

        # ── Step 2: Optimistic lock (A4) ────────────────────────────────────
        try:
            await self._payment_repo.lock_for_charge(
                payment_id=request.appointment_id,  # lock on appointment-level payment record
                expected_version=1,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
            )
        except BalanceAlreadyChargedError as exc:
            logger.warning(
                "charge_orchestrator.balance_already_charged",
                payment_id=str(exc.payment_id),
                expected_version=exc.expected_version,
                tenant_id=str(tenant_id),
            )
            raise ChargeConflictError(payment_id=exc.payment_id) from exc

        # ── Step 3: Payment port charge (A2) ────────────────────────────────
        try:
            external_result = await self._payment_port.charge(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                appointment_id=request.appointment_id,
                amount_cents=request.amount_cents,
                currency=request.currency,
                method=request.method,
                idempotency_key=request.idempotency_key,
            )
        except PaymentAdapterUnavailableError as exc:
            logger.error(
                "charge_orchestrator.payment_adapter_unavailable",
                method=request.method,
                error=str(exc),
                tenant_id=str(tenant_id),
            )
            # Audit log: charge_failed (NO PHI in payload)
            await self._audit.write(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="charge_failed",
                resource_type="appointment_payment",
                resource_id=request.appointment_id,
                payload={
                    "method": request.method,
                    "error": "payment_adapter_unavailable",
                    "idempotency_key": request.idempotency_key,
                    # No amount here — it never processed, avoid confusion
                },
            )
            raise PaymentAdapterError(detail=str(exc)) from exc

        # ── Step 4: Persist payment row ─────────────────────────────────────
        payment_model = await self._payment_repo.create(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            appointment_id=request.appointment_id,
            amount=request.amount_cents,
            currency=request.currency,
            method=request.method,
            external_payment_id=request.idempotency_key,
            notes=None,
        )

        # Audit: charge (success) — sync within session
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="charge",
            resource_type="appointment_payment",
            resource_id=payment_model.id,
            payload={
                "amount_cents": request.amount_cents,
                "currency": request.currency,
                "method": request.method,
                "gateway": external_result.gateway,
                # No PHI: appointment_id is UUID, no patient data
            },
        )

        # ── Step 5: Optional fiscal emit (A3 compensation) ──────────────────
        fiscal_status: Literal["emitted", "pending", "failed", "skipped"] = "skipped"
        fiscal_doc_url: str | None = None
        fiscal_error: str | None = None
        fiscal_doc_model = None

        if request.emit_invoice and request.fiscal_doc_type:
            # Derive country from doc_type (PE default if boleta/factura)
            country = _infer_country_from_doc_type(request.fiscal_doc_type)

            try:
                fiscal_result = await self._fiscal_port.emit(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    payment_id=payment_model.id,
                    doc_type=request.fiscal_doc_type,
                    country=country,
                    idempotency_key=f"fiscal-{request.idempotency_key}",
                    amount_cents=request.amount_cents,
                    currency=request.currency,
                )
                fiscal_status = "emitted"
                fiscal_doc_url = fiscal_result.doc_url

                # Persist fiscal document (success)
                fiscal_doc_model = await self._fiscal_doc_repo.create(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    appointment_payment_id=payment_model.id,
                    doc_type=request.fiscal_doc_type,
                    provider=fiscal_result.provider,
                    doc_number=fiscal_result.doc_number,
                    doc_url=fiscal_result.doc_url,
                    status="emitted",
                )

                # Audit: invoice_emitted
                await self._audit.write(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    user_id=user_id,
                    action="invoice_emitted",
                    resource_type="fiscal_document",
                    resource_id=fiscal_doc_model.id,
                    payload={
                        "doc_type": request.fiscal_doc_type,
                        "provider": fiscal_result.provider,
                        "doc_number": fiscal_result.doc_number,
                    },
                )

            except (FiscalAdapterUnavailableError, FiscalEmitError) as exc:
                # Saga compensation: charge stays, fiscal fails
                fiscal_status = "failed"
                fiscal_error = str(exc)

                logger.warning(
                    "charge_orchestrator.fiscal_emit_failed_post_charge",
                    doc_type=request.fiscal_doc_type,
                    error=str(exc),
                    payment_id=str(payment_model.id),
                    tenant_id=str(tenant_id),
                )

                # Persist fiscal document (failed — for retry endpoint)
                fiscal_doc_model = await self._fiscal_doc_repo.create(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    appointment_payment_id=payment_model.id,
                    doc_type=request.fiscal_doc_type,
                    provider="pending",
                    doc_number=None,
                    doc_url=None,
                    status="failed",
                )

                # Audit: fiscal_emit_failed_post_charge
                await self._audit.write(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    user_id=user_id,
                    action="fiscal_emit_failed_post_charge",
                    resource_type="fiscal_document",
                    resource_id=fiscal_doc_model.id,
                    payload={
                        "doc_type": request.fiscal_doc_type,
                        "error": "fiscal_adapter_unavailable",
                        # No PHI: doc_id is UUID, no patient data
                    },
                )

        # ── Step 7: Growth Studio event (fire-and-forget, A1) ───────────────
        try:
            await self._growth.emit_event(
                event_type="charge_completed",
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                entity_id=payment_model.id,
                props={
                    "method": request.method,
                    "currency": request.currency,
                    # Bucketed amount (no exact figure in telemetry — privacy)
                    "amount_bucket": _bucket_amount(request.amount_cents),
                    "fiscal_status": fiscal_status,
                },
            )
        except Exception as exc:
            # Growth event is fire-and-forget — never fail charge for telemetry
            logger.warning(
                "charge_orchestrator.growth_event_failed",
                error=str(exc),
                event_type="charge_completed",
            )

        return self._project_response(
            payment=payment_model,
            fiscal_doc=fiscal_doc_model,
            fiscal_status=fiscal_status,
            fiscal_doc_url=fiscal_doc_url,
            fiscal_error=fiscal_error,
            idempotency_replay=False,
        )

    def _project_response(
        self,
        *,
        payment: object,
        fiscal_doc: object | None = None,
        fiscal_status: Literal["emitted", "pending", "failed", "skipped"] = "skipped",
        fiscal_doc_url: str | None = None,
        fiscal_error: str | None = None,
        idempotency_replay: bool = False,
    ) -> ChargeResponse:
        """Build ChargeResponse from payment + fiscal doc models.

        Called for both new charges and idempotency replays.
        """
        # Derive fiscal_status from fiscal doc model if replay
        if idempotency_replay and fiscal_doc is not None:
            fiscal_status = getattr(fiscal_doc, "status", "pending")  # type: ignore[arg-type]
            fiscal_doc_url = getattr(fiscal_doc, "doc_url", None)

        return ChargeResponse(
            payment_id=getattr(payment, "id"),
            appointment_id=getattr(payment, "appointment_id"),
            amount_cents=getattr(payment, "amount"),
            currency=getattr(payment, "currency"),
            method=getattr(payment, "method"),
            external_payment_id=getattr(payment, "external_payment_id", None),
            fiscal_doc_id=getattr(fiscal_doc, "id", None) if fiscal_doc is not None else None,
            fiscal_doc_url=fiscal_doc_url,
            fiscal_emission_status=fiscal_status,
            fiscal_error_message=fiscal_error,
            idempotency_replay=idempotency_replay,
        )


# ---------------------------------------------------------------------------
# Helpers (module-private)
# ---------------------------------------------------------------------------


def _infer_country_from_doc_type(doc_type: str) -> str:
    """Infer country code from fiscal document type.

    Used when explicit country is not provided to fiscal emit.
    Follows the provider mapping in 03-arch § 7.
    """
    _DOC_TYPE_COUNTRY_MAP = {
        "boleta": "PE",
        "factura": "PE",
        "factura_a": "AR",
        "factura_b": "AR",
        "recibo": "AR",
        "cfdi": "MX",
        "ticket": "PE",  # Generic ticket — default to PE context
    }
    return _DOC_TYPE_COUNTRY_MAP.get(doc_type.lower(), "PE")


def _bucket_amount(amount_cents: int) -> str:
    """Bucket amount_cents into privacy-safe ranges for telemetry.

    Per vitalia/_shared/telemetry/amount_bucket.py pattern.
    Avoids exact transaction amounts in growth_studio_event.props.
    """
    if amount_cents <= 0:
        return "zero"
    if amount_cents < 2_000:  # < S/20 / AR$20 / MX$20
        return "micro"
    if amount_cents < 20_000:  # < S/200 / AR$200 / MX$200
        return "small"
    if amount_cents < 100_000:  # < S/1000 / AR$1000 / MX$1000
        return "medium"
    if amount_cents < 500_000:  # < S/5000
        return "large"
    return "premium"
