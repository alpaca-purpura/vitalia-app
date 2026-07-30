# cap: payment.payment-gateways-latam-recurring
# story-origin: vitalia-fase2-s1-TBD
"""Vitalia Payments — Charge API Router.

POST /api/v1/payments/charge — CobrarSaldo endpoint.

Per 03-arch § 5.3 + T-7 deliverables:
  - Consumes ChargeOrchestrator saga (T-5).
  - Idempotency: X-Idempotency-Key header prevents duplicate charges.
  - Conflict: ChargeConflictError → HTTP 409 ChargeConflict409DTO.
  - Payment 503: PaymentAdapterError → HTTP 503 PaymentAdapter503DTO.
  - Fiscal saga compensation (A6): charge OK + fiscal fail → 200 + fiscal_emission_status='failed'.
  - Currency: REQUIRED, never hardcoded (currency-handling.md).

HIPAA-lite obligations (vitalia/.claude/rules/hipaa-lite.md):
  - Dual filter: tenant_id + clinic_id MANDATORY.
  - Audit log sync write BEFORE returning response (mandatory PHI write log).
  - response_model= MANDATORY (PII allowlist enforcement; arch test enforces).
  - PHI NEVER in URL params — POST body always.
  - X-Clinic-ID header MANDATORY.
  - RBAC: only doctor/nurse/admin_clinic/valeria_assistant access.
  - Cross-clinic returns 404 (don't confirm existence).

Architecture:
  - Thin router: validate DTO → map to ChargeRequest → call ChargeOrchestrator → map exceptions.
  - No business logic in api/ (backend-ddd.md).
  - FastAPI(redirect_slashes=False) enforced at main.py level.
  - AsyncSession injected via Depends(_get_db).
  - DI factory _get_charge_orchestrator exported for test override.

downstream-regression-na: brand-local payments API router for vitalia brand
"""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.telemetry.growth_studio_emitter import GrowthStudioEmitter
from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter
from src.modules.vitalia.fiscal.application.fiscal_emit_port_impl import FiscalEmitPortImpl
from src.modules.vitalia.fiscal.infrastructure.repositories.fiscal_document_repository import (
    FiscalDocumentRepository,
)
from src.modules.vitalia.payments.api.dtos.charge_dtos import (
    ChargeConflict409DTO,
    ChargeRequestDTO,
    ChargeResponseDTO,
    PaymentAdapter503DTO,
)
from src.modules.vitalia.payments.application.payment_charge_port_impl import (
    PaymentChargePortImpl,
)
from src.modules.vitalia.scheduling.application.ports.payment_charge_port import (
    PaymentAdapterUnavailableError,
)
from src.modules.vitalia.scheduling.application.services.charge_orchestrator import (
    ChargeConflictError,
    ChargeOrchestrator,
    ChargeRequest,
    PaymentAdapterError,
)
from src.modules.vitalia.scheduling.infrastructure.repositories.appointment_payment_repository import (
    AppointmentPaymentRepository,
)

logger = structlog.get_logger()

router = APIRouter(tags=["payments"])

#: PHI roles allowed to access payment endpoints (hipaa-lite.md § RBAC).
ALLOWED_PHI_ROLES: frozenset[str] = frozenset(["valeria_assistant", "doctor", "nurse", "admin_clinic"])


# ---------------------------------------------------------------------------
# Dependency factories (exported for test override)
# ---------------------------------------------------------------------------


async def _get_db() -> AsyncSession:
    """Async DB session dependency — delegates to brand-local src.db factory."""
    from src.db import get_async_session  # noqa: PLC0415

    async for session in get_async_session():
        yield session


async def _get_charge_orchestrator(
    db: AsyncSession = Depends(_get_db),
) -> ChargeOrchestrator:
    """DI factory for ChargeOrchestrator — creates saga with all dependencies.

    Exported so tests can override via:
        app.dependency_overrides[_get_charge_orchestrator] = lambda: mock_orchestrator

    Per 03-arch § 7.2 service-blocker Option A:
      PaymentChargePortImpl routes efectivo/transferencia/otro as direct charges.
      FiscalEmitPortImpl raises FiscalAdapterUnavailableError (all routes blocked until
      vitalia-fiscal-emission-pe story is developed — T-10/T-11 in DAG).
    """
    return ChargeOrchestrator(
        payment_port=PaymentChargePortImpl(),
        fiscal_port=FiscalEmitPortImpl(),
        payment_repo=AppointmentPaymentRepository(session=db),
        audit_writer=AsyncAuditWriter(session=db),
        fiscal_doc_repo=FiscalDocumentRepository(session=db),
        growth_emitter=GrowthStudioEmitter(session=db),
    )


# ---------------------------------------------------------------------------
# POST /api/v1/payments/charge
# ---------------------------------------------------------------------------


@router.post(
    "/charge",
    response_model=ChargeResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Cobrar saldo — charge appointment balance",
    description=(
        "Executes the charge saga: payment charge + optional fiscal document emission. "
        "Idempotent: X-Idempotency-Key prevents duplicate charges on network retry. "
        "Saga compensation: if charge succeeds but fiscal emit fails, "
        "returns fiscal_emission_status='failed' (FE shows retry button). "
        "Dual filter: tenant_id + clinic_id enforced (HIPAA-lite). "
        "PHI NEVER in URL params."
    ),
    responses={
        409: {"model": ChargeConflict409DTO, "description": "Concurrent charge conflict"},
        503: {"model": PaymentAdapter503DTO, "description": "Payment adapter unavailable"},
    },
)
async def charge_appointment(
    request: ChargeRequestDTO,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID"),
    user_role: str = Header(alias="X-User-Role", default=""),
    idempotency_key: str = Header(alias="X-Idempotency-Key", default=""),
    orchestrator: ChargeOrchestrator = Depends(_get_charge_orchestrator),
) -> ChargeResponseDTO:
    """POST /api/v1/payments/charge — execute appointment charge saga.

    Args:
        request: ChargeRequestDTO with appointment_id, amount_cents, currency, method.
        tenant_id: Root tenant UUID from X-Tenant-ID header.
        clinic_id: Clinic UUID from X-Clinic-ID header (HIPAA-lite dual filter).
        user_id: User performing the charge (for audit log).
        user_role: User role for RBAC check.
        idempotency_key: Client-generated idempotency key (X-Idempotency-Key header).
        orchestrator: ChargeOrchestrator DI (injected — override in tests).

    Returns:
        ChargeResponseDTO on success (200) or saga compensation (200 + fiscal_emission_status='failed').

    Raises:
        HTTPException(403): When role not in ALLOWED_PHI_ROLES.
        HTTPException(409): On concurrent charge conflict (optimistic lock failure).
        HTTPException(503): When payment adapter is unavailable.
        HTTPException(422): FastAPI validation (missing headers, invalid body).
    """
    # ── RBAC check (inline per agenda_router pattern) ──────────────────────
    if user_role not in ALLOWED_PHI_ROLES:
        logger.warning(
            "charge_phi_access_denied",
            user_role=user_role,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a información de pagos.",
        )

    # ── Map DTO → application-layer ChargeRequest ───────────────────────────
    charge_request = ChargeRequest(
        appointment_id=UUID(str(request.appointment_id)),
        amount_cents=request.amount_cents,
        currency=request.currency,
        method=request.method,
        emit_invoice=request.emit_invoice,
        idempotency_key=idempotency_key or str(request.appointment_id),
        fiscal_doc_type=request.fiscal_doc_type,
    )

    logger.info(
        "charge_request_received",
        appointment_id=str(request.appointment_id),
        amount_cents=request.amount_cents,
        currency=request.currency,
        method=request.method,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        emit_invoice=request.emit_invoice,
    )

    try:
        charge_response = await orchestrator.execute(
            tenant_id=UUID(tenant_id),
            clinic_id=UUID(clinic_id),
            user_id=UUID(user_id),
            request=charge_request,
        )
    except ChargeConflictError as exc:
        logger.warning(
            "charge_conflict",
            payment_id=str(exc.payment_id) if exc.payment_id else None,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ChargeConflict409DTO(
                retry_with_idempotency_key=idempotency_key or None,
            ).model_dump(),
        )
    except PaymentAdapterError as exc:
        logger.error(
            "charge_payment_adapter_unavailable",
            detail=str(exc),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=PaymentAdapter503DTO().model_dump(),
        )
    except PaymentAdapterUnavailableError as exc:
        # Direct raise from PaymentChargePort (not wrapped by orchestrator in edge cases)
        logger.error(
            "charge_payment_adapter_unavailable_direct",
            detail=str(exc),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=PaymentAdapter503DTO().model_dump(),
        )

    # ── Map application response → API DTO ─────────────────────────────────
    return ChargeResponseDTO(
        payment_id=charge_response.payment_id,
        appointment_id=charge_response.appointment_id,
        amount_cents=charge_response.amount_cents,
        currency=charge_response.currency,
        method=charge_response.method,
        external_payment_id=charge_response.external_payment_id,
        fiscal_doc_id=charge_response.fiscal_doc_id,
        fiscal_doc_url=charge_response.fiscal_doc_url,
        fiscal_emission_status=charge_response.fiscal_emission_status,
        fiscal_error_message=charge_response.fiscal_error_message,
        idempotency_replay=charge_response.idempotency_replay,
    )
