# cap: payment.payment-gateways-latam-recurring
# story-origin: vitalia-fase2-s1-TBD
"""DTOs for POST /api/v1/payments/charge — CobrarSaldo endpoint.

Per 03-arch § 5.3 + T-7 deliverables:
  ChargeRequestDTO  — discriminated union by method (effectivo/tarjeta/transferencia/etc.)
  ChargeResponseDTO — payment_id + fiscal_doc_url + status + balance_after_cents
  ChargeConflict409DTO — optimistic lock conflict response (SC-5 race condition)

Currency rule (.claude/rules/currency-handling.md):
  currency is REQUIRED in ChargeRequestDTO — never hardcoded, comes from FE tenant locale
  or per-transaction override (Q14: appointment may override tenant default currency).

HIPAA-lite: no PHI fields in DTOs (appointment_id is UUID, no patient data).
response_model= mandatory (arch test test_vitalia_response_models_required.py enforces).

downstream-regression-na: brand-local payments API DTOs for vitalia (no cross-brand mirror)
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChargeRequestDTO(BaseModel):
    """Request body for POST /api/v1/payments/charge.

    Attributes:
        appointment_id: UUID of the appointment being charged.
        amount_cents: Amount in smallest currency unit (centavos/cents). Must be > 0.
        currency: ISO 4217 currency code (PEN/ARS/MXN/USD). REQUIRED — no default.
            Per Q14: appointment can override tenant default currency.
        method: Payment method (efectivo/tarjeta/transferencia/mercado_pago/otro).
        emit_invoice: Whether to emit a fiscal document after charge.
        fiscal_doc_type: Required when emit_invoice=True. FiscalDocType enum value.
        clinic_id: Clinic UUID for dual filter (HIPAA-lite). Required.
        notes: Optional staff notes for payment record.
        currency_override: Optional per-transaction currency override (Q14 spec).
            When set, overrides tenant default currency for this transaction.
    """

    model_config = ConfigDict(extra="forbid")

    appointment_id: UUID = Field(..., description="UUID of the appointment to charge")
    amount_cents: int = Field(..., gt=0, description="Amount in smallest currency unit (must be > 0)")
    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code (PEN/ARS/MXN/USD). REQUIRED — no default.",
    )
    method: Literal["efectivo", "tarjeta", "transferencia", "mercado_pago", "otro"] = Field(
        ...,
        description="Payment method for this charge",
    )
    emit_invoice: bool = Field(
        default=False,
        description="Whether to emit a fiscal document (boleta/factura) after charge",
    )
    fiscal_doc_type: str | None = Field(
        default=None,
        description=(
            "Fiscal document type (boleta/factura/factura_a/factura_b/recibo/cfdi/ticket). "
            "Required when emit_invoice=True."
        ),
    )
    clinic_id: UUID = Field(..., description="Clinic UUID for HIPAA-lite dual filter")
    notes: str | None = Field(
        default=None,
        max_length=500,
        description="Optional staff notes for payment record",
    )

    @field_validator("currency")
    @classmethod
    def currency_must_be_uppercase(cls, v: str) -> str:
        """Normalize currency to uppercase ISO 4217."""
        return v.upper()

    @field_validator("fiscal_doc_type")
    @classmethod
    def validate_fiscal_doc_type(cls, v: str | None) -> str | None:
        """Validate fiscal_doc_type against known values."""
        if v is None:
            return None
        valid_types = {"boleta", "factura", "factura_a", "factura_b", "recibo", "cfdi", "ticket"}
        if v.lower() not in valid_types:
            raise ValueError(f"fiscal_doc_type '{v}' is not valid. Valid types: {', '.join(sorted(valid_types))}.")
        return v.lower()


class ChargeResponseDTO(BaseModel):
    """Response from POST /api/v1/payments/charge.

    Returned on HTTP 200 (success — including fiscal emit failure, saga compensation).

    Attributes:
        payment_id: Newly created AppointmentPayment UUID.
        appointment_id: Appointment that was charged.
        amount_cents: Charged amount in smallest currency unit.
        currency: ISO 4217 currency code (from request — never hardcoded).
        method: Payment method used.
        external_payment_id: Gateway-assigned transaction ID (None for efectivo/direct).
        fiscal_doc_id: FiscalDocument UUID (None if no invoice requested or failed).
        fiscal_doc_url: PDF/XML URL (None if stub or not yet available).
        fiscal_emission_status: One of 'emitted'|'pending'|'failed'|'skipped'.
        fiscal_error_message: Human-readable error if fiscal_emission_status='failed'.
        idempotency_replay: True when this is a replay of a prior successful charge.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    payment_id: UUID
    appointment_id: UUID
    amount_cents: int
    currency: str
    method: str
    external_payment_id: str | None = None
    fiscal_doc_id: UUID | None = None
    fiscal_doc_url: str | None = None
    fiscal_emission_status: Literal["emitted", "pending", "failed", "skipped"]
    fiscal_error_message: str | None = None
    idempotency_replay: bool = False


class ChargeConflict409DTO(BaseModel):
    """Response body for HTTP 409 Conflict (concurrent charge / optimistic lock failure).

    Per 03-arch A7 (SC-5 race condition prevention):
      Returned when balance_version has already been incremented by a concurrent request.
      FE should reload payment state and check idempotency key before retrying.

    Attributes:
        error_code: Machine-readable error code ('BALANCE_ALREADY_CHARGED').
        message: Human-readable error message in Spanish neutro LatAm.
        retry_with_idempotency_key: Idempotency key to check for prior result.
    """

    model_config = ConfigDict(extra="forbid")

    error_code: str = Field(default="BALANCE_ALREADY_CHARGED")
    message: str = Field(
        default=("El cobro ya fue procesado concurrentemente. Verifica el estado del pago antes de reintentar.")
    )
    retry_with_idempotency_key: str | None = None


class PaymentAdapter503DTO(BaseModel):
    """Response body for HTTP 503 (payment adapter temporarily unavailable).

    Per 03-arch A2 (payment port 503 compensation):
      Returned when PaymentChargePort raises PaymentAdapterUnavailableError.
      No fiscal document is created (charge never processed).

    Attributes:
        error_code: Machine-readable error code ('PAYMENT_ADAPTER_503').
        message: Human-readable error message in Spanish neutro LatAm.
    """

    model_config = ConfigDict(extra="forbid")

    error_code: str = Field(default="PAYMENT_ADAPTER_503")
    message: str = Field(
        default=("El servicio de pago no está disponible temporalmente. Por favor, intenta de nuevo en unos minutos.")
    )
