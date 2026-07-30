"""Tests for POST /api/v1/fiscal/emit — standalone fiscal emission retry.

TDD RED phase for T-7 vitalia-fase2-valeria-agenda.

Per 03-arch § 5.4 + hipaa-lite.md:
  - Standalone fiscal retry: charge already succeeded, only fiscal failed.
  - Dual filter: tenant_id + clinic_id MANDATORY.
  - Audit log sync write BEFORE response.
  - response_model= mandatory (enforced by arch test).
  - PHI roles allowed: doctor, nurse, admin_clinic, valeria_assistant.
  - Cross-clinic returns 404.
  - X-Idempotency-Key prevents duplicate emissions.

Architecture:
  - Uses minimal FastAPI app (no src.main import — avoids Settings env var validation).
  - All dependencies mocked via dependency_overrides.

downstream-regression-na: brand-local fiscal API router tests for vitalia
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.modules.vitalia.fiscal.api.emit_router import (
    _get_db,
    _get_emit_deps,
)
from src.modules.vitalia.fiscal.api.emit_router import (
    router as emit_router,
)
from src.modules.vitalia.fiscal.infrastructure.repositories.fiscal_document_repository import (
    FiscalDocumentRepository,
)
from src.modules.vitalia.scheduling.application.ports.fiscal_emit_port import (
    FiscalAdapterUnavailableError,
    FiscalDocResult,
)

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

_DOC_ID = uuid4()
_PAYMENT_ID = uuid4()
_TENANT_ID = uuid4()
_CLINIC_ID = uuid4()
_USER_ID = uuid4()

_VALID_HEADERS = {
    "X-Tenant-ID": str(_TENANT_ID),
    "X-Clinic-ID": str(_CLINIC_ID),
    "X-User-ID": str(_USER_ID),
    "X-User-Role": "admin_clinic",
    "X-Idempotency-Key": str(uuid4()),
}

_VALID_BODY = {
    "payment_id": str(_PAYMENT_ID),
    "doc_type": "boleta",
    "clinic_id": str(_CLINIC_ID),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fiscal_doc_mock(*, status: str = "failed", doc_number: str | None = None) -> MagicMock:
    """Build a FiscalDocumentModel mock for tests."""
    doc = MagicMock()
    doc.id = _DOC_ID
    doc.appointment_payment_id = _PAYMENT_ID
    doc.doc_type = "boleta"
    doc.doc_number = doc_number
    doc.doc_url = None
    doc.provider = "nubefact_stub"
    doc.status = status
    doc.tenant_id = _TENANT_ID
    doc.clinic_id = _CLINIC_ID
    return doc


def _build_test_app(
    *,
    mock_repo: AsyncMock | None = None,
    mock_port: AsyncMock | None = None,
) -> FastAPI:
    """Build a minimal FastAPI test app with the emit router mounted.

    Overrides _get_db and _get_emit_deps to avoid real DB connections.
    """
    test_app = FastAPI(redirect_slashes=False)
    test_app.include_router(emit_router, prefix="/api/v1/fiscal")

    # Mock session
    mock_session = AsyncMock()

    async def _fake_db():  # noqa: ANN202
        yield mock_session

    test_app.dependency_overrides[_get_db] = _fake_db

    if mock_repo is not None and mock_port is not None:
        _repo = mock_repo
        _port = mock_port

        async def _fake_emit_deps():  # noqa: ANN202
            return _repo, _port

        test_app.dependency_overrides[_get_emit_deps] = _fake_emit_deps

    return test_app


# ---------------------------------------------------------------------------
# Test: Happy path — standalone emit after charge succeeded
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_standalone_emit_after_charge_succeeded() -> None:
    """POST /emit returns 200 + FiscalDocResponseDTO when doc exists in 'failed' state.

    Scenario (03-arch A6 saga compensation):
      - Charge succeeded, fiscal failed (FiscalDocument.status='failed').
      - Frontend calls POST /fiscal/emit to retry.
      - Emit port returns success.
      - FiscalDocument updated to 'emitted'.
      - Response includes doc_number + provider.
    """
    existing_doc = _make_fiscal_doc_mock(status="failed")
    updated_doc = _make_fiscal_doc_mock(status="emitted", doc_number="STUB-BOL-000001")

    mock_repo = AsyncMock(spec=FiscalDocumentRepository)
    mock_repo.get_by_payment_id = AsyncMock(return_value=existing_doc)
    mock_repo.get_by_id = AsyncMock(return_value=updated_doc)
    mock_repo.update_status = AsyncMock(return_value=True)
    mock_repo._session = AsyncMock()

    mock_port = AsyncMock()
    mock_port.emit = AsyncMock(
        return_value=FiscalDocResult(
            doc_number="STUB-BOL-000001",
            doc_url=None,
            provider="nubefact_stub",
        )
    )

    app = _build_test_app(mock_repo=mock_repo, mock_port=mock_port)

    with patch("src.modules.vitalia.fiscal.api.emit_router.AsyncAuditWriter") as mock_audit_cls:
        mock_audit_instance = AsyncMock()
        mock_audit_instance.write = AsyncMock()
        mock_audit_cls.return_value = mock_audit_instance

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/fiscal/emit",
                json=_VALID_BODY,
                headers={**_VALID_HEADERS, "X-Idempotency-Key": str(uuid4())},
            )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["doc_type"] == "boleta"
    assert data["provider"] == "nubefact_stub"
    assert data["status"] == "emitted"
    assert data["doc_number"] == "STUB-BOL-000001"
    assert data["payment_id"] == str(_PAYMENT_ID)
    assert data["idempotency_replay"] is False


# ---------------------------------------------------------------------------
# Test: Audit log written synchronously on successful emit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_log_invoice_emitted() -> None:
    """POST /emit writes audit_log row synchronously before returning response.

    Per hipaa-lite.md: audit log sync write BEFORE response (NOT fire-and-forget).
    Action: 'invoice_emitted'
    Resource: fiscal_document
    No PHI in audit payload — only UUIDs + statuses.
    """
    existing_doc = _make_fiscal_doc_mock(status="failed")
    updated_doc = _make_fiscal_doc_mock(status="emitted", doc_number="STUB-BOL-000002")

    mock_repo = AsyncMock(spec=FiscalDocumentRepository)
    mock_repo.get_by_payment_id = AsyncMock(return_value=existing_doc)
    mock_repo.get_by_id = AsyncMock(return_value=updated_doc)
    mock_repo.update_status = AsyncMock(return_value=True)
    mock_repo._session = AsyncMock()

    mock_port = AsyncMock()
    mock_port.emit = AsyncMock(
        return_value=FiscalDocResult(
            doc_number="STUB-BOL-000002",
            doc_url=None,
            provider="nubefact_stub",
        )
    )

    app = _build_test_app(mock_repo=mock_repo, mock_port=mock_port)

    with patch("src.modules.vitalia.fiscal.api.emit_router.AsyncAuditWriter") as mock_audit_cls:
        mock_audit_instance = AsyncMock()
        mock_audit_instance.write = AsyncMock()
        mock_audit_cls.return_value = mock_audit_instance

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/fiscal/emit",
                json=_VALID_BODY,
                headers={**_VALID_HEADERS, "X-Idempotency-Key": str(uuid4())},
            )

        assert resp.status_code == 200
        # Audit log MUST have been called with action 'invoice_emitted'
        mock_audit_instance.write.assert_called_once()
        call_kwargs = mock_audit_instance.write.call_args.kwargs
        assert call_kwargs["action"] == "invoice_emitted"
        assert call_kwargs["resource_type"] == "fiscal_document"
        # No PHI in audit payload — only UUIDs + statuses
        payload = call_kwargs.get("payload", {})
        for phi_key in ("patient_name", "patient_dni", "diagnosis", "medication"):
            assert phi_key not in payload, f"PHI key '{phi_key}' found in audit payload"


# ---------------------------------------------------------------------------
# Test: 503 when fiscal adapter unavailable on retry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_emit_503_when_fiscal_adapter_unavailable() -> None:
    """POST /emit returns 503 when FiscalAdapterUnavailableError raised.

    Per 03-arch A3: standalone retry endpoint returns 503 (not 500) when
    fiscal provider is temporarily unavailable. FE shows retry hint.
    """
    existing_doc = _make_fiscal_doc_mock(status="failed")

    mock_repo = AsyncMock(spec=FiscalDocumentRepository)
    mock_repo.get_by_payment_id = AsyncMock(return_value=existing_doc)
    mock_repo._session = AsyncMock()

    mock_port = AsyncMock()
    mock_port.emit = AsyncMock(side_effect=FiscalAdapterUnavailableError("provider down"))

    app = _build_test_app(mock_repo=mock_repo, mock_port=mock_port)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/fiscal/emit",
            json=_VALID_BODY,
            headers={**_VALID_HEADERS, "X-Idempotency-Key": str(uuid4())},
        )

    assert resp.status_code == 503, f"Expected 503, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["error_code"] == "FISCAL_ADAPTER_503"
    assert "proveedor fiscal" in data["message"].lower()


# ---------------------------------------------------------------------------
# Test: 404 when payment not found or cross-clinic access attempt
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_emit_404_when_payment_not_found() -> None:
    """POST /emit returns 404 when fiscal doc not found for payment_id.

    Per hipaa-lite.md: cross-clinic returns 404 (NOT 403 — don't confirm existence).
    Also 404 when payment_id has no associated fiscal document.
    """
    mock_repo = AsyncMock(spec=FiscalDocumentRepository)
    mock_repo.get_by_payment_id = AsyncMock(return_value=None)
    mock_repo._session = AsyncMock()

    mock_port = AsyncMock()

    app = _build_test_app(mock_repo=mock_repo, mock_port=mock_port)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/fiscal/emit",
            json=_VALID_BODY,
            headers={**_VALID_HEADERS, "X-Idempotency-Key": str(uuid4())},
        )

    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Test: 403 when role is not allowed PHI access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_emit_403_for_unauthorized_role() -> None:
    """POST /emit returns 403 when role is not in ALLOWED_PHI_ROLES.

    Per hipaa-lite.md § RBAC: marketing, sales roles never see PHI.
    """
    app = _build_test_app()  # no deps override needed — RBAC check happens first

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/fiscal/emit",
            json=_VALID_BODY,
            headers={
                **_VALID_HEADERS,
                "X-User-Role": "marketing",  # Not in ALLOWED_PHI_ROLES
                "X-Idempotency-Key": str(uuid4()),
            },
        )

    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Test: Idempotency replay when doc already emitted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_emit_idempotency_already_emitted() -> None:
    """POST /emit returns 200 + idempotency_replay=True when doc already emitted.

    Idempotent behavior: if fiscal doc already in 'emitted' state,
    return prior result without calling emit port again.
    """
    already_emitted_doc = _make_fiscal_doc_mock(status="emitted", doc_number="BOL-PRIOR-001")
    already_emitted_doc.doc_url = "https://example.com/doc.pdf"

    mock_repo = AsyncMock(spec=FiscalDocumentRepository)
    mock_repo.get_by_payment_id = AsyncMock(return_value=already_emitted_doc)
    mock_repo._session = AsyncMock()

    # emit should NOT be called when doc already emitted
    mock_port = AsyncMock()
    mock_port.emit = AsyncMock()

    app = _build_test_app(mock_repo=mock_repo, mock_port=mock_port)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/fiscal/emit",
            json=_VALID_BODY,
            headers={**_VALID_HEADERS, "X-Idempotency-Key": str(uuid4())},
        )

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["idempotency_replay"] is True
    assert data["status"] == "emitted"
    assert data["doc_number"] == "BOL-PRIOR-001"
    # emit port must NOT have been called
    mock_port.emit.assert_not_called()


# ---------------------------------------------------------------------------
# Test: Missing mandatory headers → 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_emit_missing_clinic_id_header_rejected() -> None:
    """POST /emit returns 422 when X-Clinic-ID header is missing."""
    app = _build_test_app()

    headers_without_clinic = {k: v for k, v in _VALID_HEADERS.items() if k != "X-Clinic-ID"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/fiscal/emit",
            json=_VALID_BODY,
            headers=headers_without_clinic,
        )

    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
