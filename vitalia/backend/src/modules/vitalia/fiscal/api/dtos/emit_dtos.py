# cap: fiscal.fiscal-emission-pe
# story-origin: TBD
"""DTOs for POST /api/v1/fiscal/emit — standalone fiscal emission retry endpoint.

Per 03-arch § 5.4 + T-7 deliverables:
  FiscalEmitRequestDTO  — payment_id + doc_type for standalone retry
  FiscalDocResponseDTO  — doc_number + doc_url + status + audit confirmation

Saga compensation pattern (03-arch A6):
  When charge succeeds but fiscal emit fails, FiscalDocument.status='failed' is persisted.
  FE shows "Reintentar emisión" button that calls POST /api/v1/fiscal/emit.
  This endpoint retries the emit standalone (NOT re-charging the payment).

HIPAA-lite: no PHI fields in DTOs (payment_id is UUID, no patient data).
Idempotency: X-Idempotency-Key header prevents duplicate emissions on network retry.

downstream-regression-na: brand-local fiscal API DTOs for vitalia (no cross-brand mirror)
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FiscalEmitRequestDTO(BaseModel):
    """Request body for POST /api/v1/fiscal/emit.

    Used for standalone fiscal emission retry after saga compensation
    (charge succeeded + fiscal failed in ChargeOrchestrator).

    Attributes:
        payment_id: UUID of the AppointmentPayment to emit fiscal doc for.
        doc_type: Fiscal document type (boleta/factura/cfdi/ticket/etc.).
        clinic_id: Clinic UUID for HIPAA-lite dual filter.
    """

    model_config = ConfigDict(extra="forbid")

    payment_id: UUID = Field(
        ...,
        description="UUID of the AppointmentPayment to emit fiscal document for",
    )
    doc_type: str = Field(
        ...,
        description=(
            "Fiscal document type: boleta|factura|factura_a|factura_b|recibo|cfdi|ticket. "
            "Must match the doc_type from the original charge request."
        ),
    )
    clinic_id: UUID = Field(..., description="Clinic UUID for HIPAA-lite dual filter")


class FiscalDocResponseDTO(BaseModel):
    """Response from POST /api/v1/fiscal/emit.

    Returned on HTTP 200 (success) after standalone fiscal emission.

    Attributes:
        doc_id: FiscalDocument UUID (new or updated).
        payment_id: AppointmentPayment UUID this document covers.
        doc_type: Fiscal document type emitted.
        doc_number: Provider-issued serial number (None if still pending/stub).
        doc_url: PDF/XML download URL (None if not available yet).
        provider: Fiscal provider slug (nubefact/afip/sat/nubefact_stub).
        status: Emission status ('emitted'|'pending'|'failed').
        idempotency_replay: True if this is a replay of prior successful emission.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    doc_id: UUID
    payment_id: UUID
    doc_type: str
    doc_number: str | None = None
    doc_url: str | None = None
    provider: str
    status: Literal["emitted", "pending", "failed"]
    idempotency_replay: bool = False


class FiscalEmit503DTO(BaseModel):
    """Response for HTTP 503 when fiscal adapter is temporarily unavailable.

    Per 03-arch A3 (saga compensation):
      FiscalAdapterUnavailableError → HTTP 503 on standalone retry.
      FE shows "Proveedor fiscal no disponible" + retry hint.

    Attributes:
        error_code: Machine-readable error code.
        message: Human-readable error in Spanish neutro LatAm.
    """

    model_config = ConfigDict(extra="forbid")

    error_code: str = Field(default="FISCAL_ADAPTER_503")
    message: str = Field(
        default=(
            "El proveedor fiscal no está disponible temporalmente. "
            "Por favor, intenta emitir la factura en unos minutos."
        )
    )
