# cap: fiscal.fiscal-emission-pe
# story-origin: TBD
"""Vitalia Fiscal — Standalone Emit API Router.

POST /api/v1/fiscal/emit — standalone fiscal emission retry endpoint.

Per 03-arch § 5.4 + T-7 deliverables:
  Saga compensation pattern (A6):
    When charge succeeds but fiscal emit fails, FiscalDocument.status='failed' is persisted.
    FE shows "Reintentar emisión" button that calls POST /api/v1/fiscal/emit.
    This endpoint retries the emit standalone (NOT re-charging the payment).

Idempotency:
  - If FiscalDocument already in 'emitted' state → return prior result (idempotency_replay=True).
  - X-Idempotency-Key header prevents duplicate emissions on network retry (future: persist key).

HIPAA-lite obligations (vitalia/.claude/rules/hipaa-lite.md):
  - Dual filter: tenant_id + clinic_id MANDATORY.
  - Audit log sync write BEFORE returning response (mandatory PHI write log).
  - response_model= MANDATORY (PII allowlist enforcement; arch test enforces).
  - PHI NEVER in URL params — POST body always.
  - X-Clinic-ID header MANDATORY.
  - RBAC: only doctor/nurse/admin_clinic/valeria_assistant access.
  - Cross-clinic returns 404 (don't confirm existence).

Architecture:
  - Thin router: validate DTO → fetch fiscal doc → call port → update doc → audit → respond.
  - No business logic in api/ (backend-ddd.md).
  - DI factory _get_emit_deps exported for test override.

downstream-regression-na: brand-local fiscal API router for vitalia brand
"""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter
from src.modules.vitalia.fiscal.api.dtos.emit_dtos import (
    FiscalDocResponseDTO,
    FiscalEmit503DTO,
    FiscalEmitRequestDTO,
)
from src.modules.vitalia.fiscal.application.fiscal_emit_port_impl import FiscalEmitPortImpl
from src.modules.vitalia.fiscal.infrastructure.repositories.fiscal_document_repository import (
    FiscalDocumentRepository,
)
from src.modules.vitalia.scheduling.application.ports.fiscal_emit_port import (
    FiscalAdapterUnavailableError,
    FiscalEmitPort,
)

logger = structlog.get_logger()

router = APIRouter(tags=["fiscal"])

#: PHI roles allowed to access fiscal endpoints (hipaa-lite.md § RBAC).
ALLOWED_PHI_ROLES: frozenset[str] = frozenset(["valeria_assistant", "doctor", "nurse", "admin_clinic"])


# ---------------------------------------------------------------------------
# Dependency factories (exported for test override)
# ---------------------------------------------------------------------------


async def _get_db() -> AsyncSession:
    """Async DB session dependency — delegates to brand-local src.db factory."""
    from src.db import get_async_session  # noqa: PLC0415

    async for session in get_async_session():
        yield session


async def _get_emit_deps(
    db: AsyncSession = Depends(_get_db),
) -> tuple[FiscalDocumentRepository, FiscalEmitPort]:
    """DI factory for emit dependencies — returns (repo, port) tuple.

    Exported so tests can override via:
        app.dependency_overrides[_get_emit_deps] = lambda: (mock_repo, mock_port)

    Per 03-arch service-blocker Option A:
      FiscalEmitPortImpl raises FiscalAdapterUnavailableError on all paths until
      vitalia-fiscal-emission-pe story is developed.
    """
    return (
        FiscalDocumentRepository(session=db),
        FiscalEmitPortImpl(),
    )


# ---------------------------------------------------------------------------
# POST /api/v1/fiscal/emit
# ---------------------------------------------------------------------------


@router.post(
    "/emit",
    response_model=FiscalDocResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Reintentar emisión fiscal — standalone retry",
    description=(
        "Retries fiscal document emission for a payment whose charge already succeeded. "
        "Idempotent: if document already emitted, returns prior result (idempotency_replay=True). "
        "Dual filter: tenant_id + clinic_id enforced (HIPAA-lite). "
        "Audit log written synchronously. "
        "PHI NEVER in URL params."
    ),
    responses={
        503: {"model": FiscalEmit503DTO, "description": "Fiscal adapter temporarily unavailable"},
    },
)
async def emit_fiscal_document(
    request: FiscalEmitRequestDTO,
    tenant_id: str = Header(alias="X-Tenant-ID"),
    clinic_id: str = Header(alias="X-Clinic-ID"),
    user_id: str = Header(alias="X-User-ID"),
    user_role: str = Header(alias="X-User-Role", default=""),
    idempotency_key: str = Header(alias="X-Idempotency-Key", default=""),
    deps: tuple[FiscalDocumentRepository, FiscalEmitPort] = Depends(_get_emit_deps),
) -> FiscalDocResponseDTO:
    """POST /api/v1/fiscal/emit — standalone fiscal document emission retry.

    Args:
        request: FiscalEmitRequestDTO with payment_id + doc_type + clinic_id.
        tenant_id: Root tenant UUID from X-Tenant-ID header.
        clinic_id: Clinic UUID from X-Clinic-ID header (HIPAA-lite dual filter).
        user_id: User performing the retry (for audit log).
        user_role: User role for RBAC check.
        idempotency_key: Client-generated idempotency key (X-Idempotency-Key header).
        deps: (FiscalDocumentRepository, FiscalEmitPort) tuple from DI factory.

    Returns:
        FiscalDocResponseDTO on success (200).
        idempotency_replay=True if document already emitted.

    Raises:
        HTTPException(403): When role not in ALLOWED_PHI_ROLES.
        HTTPException(404): When payment_id has no associated fiscal document.
        HTTPException(503): When fiscal adapter is temporarily unavailable.
    """
    fiscal_doc_repo, fiscal_port = deps

    # ── RBAC check (inline per agenda_router pattern) ──────────────────────
    if user_role not in ALLOWED_PHI_ROLES:
        logger.warning(
            "fiscal_emit_phi_access_denied",
            user_role=user_role,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para emitir comprobantes fiscales.",
        )

    tenant_uuid = UUID(tenant_id)
    clinic_uuid = UUID(clinic_id)
    user_uuid = UUID(user_id)
    payment_uuid = request.payment_id

    logger.info(
        "fiscal_emit_request_received",
        payment_id=str(payment_uuid),
        doc_type=request.doc_type,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
    )

    # ── Fetch existing fiscal document (dual filter — HIPAA-lite) ──────────
    fiscal_doc = await fiscal_doc_repo.get_by_payment_id(
        payment_uuid,
        tenant_id=tenant_uuid,
        clinic_id=clinic_uuid,
    )

    if fiscal_doc is None:
        # 404 per hipaa-lite.md: don't confirm existence (cross-clinic reads 404)
        logger.info(
            "fiscal_emit_not_found",
            payment_id=str(payment_uuid),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "FISCAL_DOC_NOT_FOUND",
                "message": "No se encontró el comprobante fiscal para este pago.",
            },
        )

    # ── Idempotency: already emitted → replay ──────────────────────────────
    if fiscal_doc.status == "emitted":
        logger.info(
            "fiscal_emit_idempotency_replay",
            doc_id=str(fiscal_doc.id),
            payment_id=str(payment_uuid),
            doc_number=fiscal_doc.doc_number,
        )
        return FiscalDocResponseDTO(
            doc_id=fiscal_doc.id,
            payment_id=fiscal_doc.appointment_payment_id,
            doc_type=fiscal_doc.doc_type,
            doc_number=fiscal_doc.doc_number,
            doc_url=fiscal_doc.doc_url,
            provider=fiscal_doc.provider,
            status="emitted",
            idempotency_replay=True,
        )

    # ── Emit via fiscal port ────────────────────────────────────────────────
    try:
        result = await fiscal_port.emit(
            tenant_id=tenant_uuid,
            clinic_id=clinic_uuid,
            payment_id=payment_uuid,
            doc_type=request.doc_type,
            country="PE",  # TODO T-10: resolve from tenant config (fiscal-emission-pe story)
            idempotency_key=idempotency_key or str(payment_uuid),
        )
    except FiscalAdapterUnavailableError as exc:
        logger.error(
            "fiscal_emit_adapter_unavailable",
            doc_id=str(fiscal_doc.id),
            payment_id=str(payment_uuid),
            detail=str(exc),
            tenant_id=tenant_id,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=FiscalEmit503DTO().model_dump(),
        )

    # ── Persist updated status ──────────────────────────────────────────────
    await fiscal_doc_repo.update_status(
        fiscal_doc.id,
        tenant_id=tenant_uuid,
        clinic_id=clinic_uuid,
        status="emitted",
        doc_number=result.doc_number,
        doc_url=result.doc_url,
    )

    # Fetch updated doc to return accurate data
    updated_doc = await fiscal_doc_repo.get_by_id(
        fiscal_doc.id,
        tenant_id=tenant_uuid,
        clinic_id=clinic_uuid,
    )
    if updated_doc is None:
        # Should not happen — just emitted; log + fallback to pre-update doc
        logger.error(
            "fiscal_emit_updated_doc_not_found",
            doc_id=str(fiscal_doc.id),
            tenant_id=tenant_id,
        )
        updated_doc = fiscal_doc

    # ── Audit log (sync write BEFORE response — HIPAA-lite mandatory) ───────
    # Note: AsyncAuditWriter is constructed here since _get_emit_deps doesn't include it.
    # _get_db is resolved via the deps factory, so we access the session through repo.
    audit_session = fiscal_doc_repo._session  # noqa: SLF001 — private attr required for shared session
    audit = AsyncAuditWriter(session=audit_session)
    await audit.write(
        tenant_id=tenant_uuid,
        clinic_id=clinic_uuid,
        user_id=user_uuid,
        action="invoice_emitted",
        resource_type="fiscal_document",
        resource_id=fiscal_doc.id,
        payload={
            "doc_id": str(fiscal_doc.id),
            "payment_id": str(payment_uuid),
            "doc_type": request.doc_type,
            "provider": result.provider,
            "doc_number": result.doc_number,
            # No PHI values — only UUIDs + statuses
        },
    )

    logger.info(
        "fiscal_emit_success",
        doc_id=str(fiscal_doc.id),
        payment_id=str(payment_uuid),
        doc_number=result.doc_number,
        provider=result.provider,
        tenant_id=tenant_id,
    )

    return FiscalDocResponseDTO(
        doc_id=updated_doc.id,
        payment_id=updated_doc.appointment_payment_id,
        doc_type=updated_doc.doc_type,
        doc_number=updated_doc.doc_number,
        doc_url=updated_doc.doc_url,
        provider=result.provider,
        status="emitted",
        idempotency_replay=False,
    )
