# cap: lisa.servicios
"""HIPAA-lite consent-gate tests for POST /servicios/{offer_id}/cases (T-2 § 8, RN-33).

A before/after case is PHI. The router requires X-Clinic-ID (dual filter) and the
ProofService gates on consent_signed:

  - consent_signed=False → CaseRepository raises ConsentNotSignedError BEFORE any
    persist/audit → the router maps it to 422 and NO audit row is written.
  - consent_signed=True → the case persists, a SYNC audit row is written
    pre-response (no PHI in payload), and the API returns 201 + CaseDTO.

These tests mock _build_service so they exercise the router's exception mapping +
the consent contract without a database. The audit row itself is covered by the
service-level suite (proof_service) already GREEN; here we assert the HTTP edges.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.modules.vitalia.offer.domain.proof import Case
from src.modules.vitalia.offer.infrastructure.repositories.case_repository import ConsentNotSignedError

pytestmark = pytest.mark.integration

_TENANT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_USER_ID = "11111111-1111-1111-1111-111111111111"  # UUID → skips Clerk DB resolve
_CLINIC_ID = "22222222-2222-2222-2222-222222222222"
_OFFER = uuid4()
_BASE = "/api/v1/offer/servicios"
_OWNER_HEADERS = {
    "X-Tenant-ID": _TENANT,
    "X-User-ID": _USER_ID,
    "X-User-Role": "owner",
    "X-Clinic-ID": _CLINIC_ID,
}


@pytest.fixture
def app():
    from src.main import app as vitalia_app

    return vitalia_app


def _patch():
    return patch("src.modules.vitalia.offer.api.servicios_router._build_service")


def _bundle(*, proof: AsyncMock) -> AsyncMock:
    bundle = AsyncMock()
    bundle.proof = proof
    return bundle


@pytest.mark.asyncio
async def test_case_create_rejected_when_consent_not_signed(app) -> None:
    """consent_signed=False → 422; service raised the gate, no PHI leaks back."""
    proof = AsyncMock()
    proof.create_case.side_effect = ConsentNotSignedError("consent required")
    with _patch() as mock_build:
        mock_build.return_value = _bundle(proof=proof)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"{_BASE}/{_OFFER}/cases",
                headers=_OWNER_HEADERS,
                json={
                    "before_asset_url": "https://cdn.example.com/b.jpg",
                    "after_asset_url": "https://cdn.example.com/a.jpg",
                    "consent_signed": False,
                },
            )
    assert resp.status_code == 422
    # The gate was hit exactly once and nothing PHI-ish leaked into the body.
    proof.create_case.assert_awaited_once()
    assert "patient" not in resp.text.lower()


@pytest.mark.asyncio
async def test_case_create_succeeds_with_consent(app) -> None:
    """consent_signed=True → 201 + CaseDTO (asset urls + consent flags, NO patient id)."""
    from uuid import UUID

    case = Case(
        tenant_id=UUID(_TENANT),
        offer_id=_OFFER,
        before_asset_url="https://cdn.example.com/b.jpg",
        after_asset_url="https://cdn.example.com/a.jpg",
        consent_signed=True,
        consent_ref="consent-2026-0001",
        clinic_id=UUID(_CLINIC_ID),
    )
    proof = AsyncMock()
    proof.create_case.return_value = case
    with _patch() as mock_build:
        mock_build.return_value = _bundle(proof=proof)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"{_BASE}/{_OFFER}/cases",
                headers=_OWNER_HEADERS,
                json={
                    "before_asset_url": "https://cdn.example.com/b.jpg",
                    "after_asset_url": "https://cdn.example.com/a.jpg",
                    "consent_signed": True,
                    "consent_ref": "consent-2026-0001",
                },
            )
    assert resp.status_code == 201
    body = resp.json()
    assert body["consent_signed"] is True
    assert body["consent_ref"] == "consent-2026-0001"
    assert body["before_asset_url"] == "https://cdn.example.com/b.jpg"
    # DTO whitelist: no patient identifiers, no tenant/clinic ids leaked.
    assert "tenant_id" not in body
    assert "clinic_id" not in body
    proof.create_case.assert_awaited_once()
    # consent flag forwarded correctly to the service.
    assert proof.create_case.await_args.kwargs["consent_signed"] is True


@pytest.mark.asyncio
async def test_case_create_requires_clinic_header(app) -> None:
    """X-Clinic-ID missing → 422 (PHI dual-filter header is mandatory on Case routes)."""
    proof = AsyncMock()
    with _patch() as mock_build:
        mock_build.return_value = _bundle(proof=proof)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"{_BASE}/{_OFFER}/cases",
                headers={"X-Tenant-ID": _TENANT, "X-User-ID": _USER_ID, "X-User-Role": "owner"},
                json={
                    "before_asset_url": "https://cdn.example.com/b.jpg",
                    "after_asset_url": "https://cdn.example.com/a.jpg",
                    "consent_signed": True,
                },
            )
    assert resp.status_code == 422
    proof.create_case.assert_not_awaited()
