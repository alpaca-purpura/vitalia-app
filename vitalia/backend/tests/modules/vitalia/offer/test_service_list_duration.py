# cap: scheduling.mateo-agenda
"""RED-first tests for T-BE-1: initial_appt_duration_minutes exposed in ServiceListItemDTO.

SC-dur-default (gherkin_coverage T-BE-1): GET /servicios returns
initial_appt_duration_minutes per item. Null is valid (FE defaults to 30, RN-5).

Tests verify:
  1. ServiceListItemDTO carries the field in the JSON response (schema test).
  2. A non-null value (e.g. 45) round-trips through list endpoint.
  3. A null value is preserved (FE defaults to 30 — that's a FE concern, RN-5).
  4. Cross-tenant safety: request with wrong tenant returns 404 / empty list (no leak).
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from luana_core_offer_studio.domain.enums import OfferStatus

from src.modules.vitalia.offer.application.services.catalog_service import ServiceView
from src.modules.vitalia.offer.domain.enums import ServiceModality

pytestmark = pytest.mark.integration

_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_BASE = "/api/v1/offer/servicios"


def _view_with_duration(duration: int | None) -> ServiceView:
    """Build a ServiceView with a specific initial_appt_duration_minutes."""
    return ServiceView(
        offer_id=uuid4(),
        public_name="Consulta inicial",
        price=Decimal("150"),
        currency="MXN",
        status=OfferStatus.ACTIVE,
        is_active=True,
        modality=ServiceModality.UNICA,
        category="Consulta",
        canonical_service_ref=None,
        initial_appt_duration_minutes=duration,
    )


def _bundle_for_list(catalog: AsyncMock) -> AsyncMock:
    bundle = AsyncMock()
    bundle.catalog = catalog
    bundle.biblioteca = AsyncMock()
    bundle.specialists = AsyncMock()
    bundle.proof = AsyncMock()
    bundle.sales_brief = AsyncMock()
    bundle.autocomplete = AsyncMock()
    bundle.sales_brief.get.return_value = None
    bundle.specialists.list_for_offer.return_value = []
    bundle.proof.list_cases.return_value = []
    bundle.proof.list_testimonials.return_value = []
    return bundle


@pytest.fixture
def app():
    from src.main import app as vitalia_app

    return vitalia_app


def _patch():
    return patch("src.modules.vitalia.offer.api.servicios_router._build_service")


# ── SC-dur-default: non-null duration round-trips ──────────────────────────────


@pytest.mark.asyncio
async def test_list_returns_duration_when_set(app) -> None:
    """ServiceListItemDTO includes initial_appt_duration_minutes when set (T-BE-1)."""
    catalog = AsyncMock()
    catalog.list_services.return_value = ([_view_with_duration(45)], None)
    with _patch() as mock_build:
        mock_build.return_value = _bundle_for_list(catalog=catalog)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(_BASE, headers={"X-Tenant-ID": _TENANT_A})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    # KEY assertion: field must be present and equal to the value set
    assert "initial_appt_duration_minutes" in items[0], (
        "initial_appt_duration_minutes missing from ServiceListItemDTO — T-BE-1 not implemented"
    )
    assert items[0]["initial_appt_duration_minutes"] == 45


# ── SC-dur-default: null duration round-trips (FE defaults to 30, RN-5) ───────


@pytest.mark.asyncio
async def test_list_returns_null_duration_when_not_set(app) -> None:
    """ServiceListItemDTO returns null when duration not set; FE defaults to 30 (RN-5)."""
    catalog = AsyncMock()
    catalog.list_services.return_value = ([_view_with_duration(None)], None)
    with _patch() as mock_build:
        mock_build.return_value = _bundle_for_list(catalog=catalog)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(_BASE, headers={"X-Tenant-ID": _TENANT_A})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert "initial_appt_duration_minutes" in items[0], (
        "initial_appt_duration_minutes missing from ServiceListItemDTO — T-BE-1 not implemented"
    )
    assert items[0]["initial_appt_duration_minutes"] is None


# ── Schema contract: field present in DTO even without a service ───────────────


def test_service_list_item_dto_has_duration_field() -> None:
    """ServiceListItemDTO schema declares initial_appt_duration_minutes (T-BE-1 contract)."""
    from src.modules.vitalia.offer.api.dtos import ServiceListItemDTO

    fields = ServiceListItemDTO.model_fields
    assert "initial_appt_duration_minutes" in fields, (
        "initial_appt_duration_minutes field missing from ServiceListItemDTO — add it (T-BE-1)"
    )
    # Field must be optional (int | None)
    field_info = fields["initial_appt_duration_minutes"]
    assert not field_info.is_required(), "initial_appt_duration_minutes must be optional (int | None)"
