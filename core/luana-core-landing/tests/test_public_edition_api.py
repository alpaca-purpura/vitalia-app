"""Smoke tests for the per-edition public landing routes (Phase 8)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from luana_core_iam.infrastructure.models.tenant_model import TenantModel
from luana_core_landing.api.public_edition import router as public_edition_router
from luana_core_platform.core.database import get_db

# Skip tests that depend on luana_core_offer until it is lifted (Story 5 deferred).
_skip_if_no_offer = pytest.mark.skipif(
    True,
    reason="luana_core_offer not yet installed (Story 5 deferred)",
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


_TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_TENANT_SLUG = "acme"


@pytest.fixture
def client(db: "Session") -> TestClient:
    app = FastAPI()
    app.include_router(public_edition_router, prefix="/api/v1/public")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def tenant_row(db: "Session") -> TenantModel:
    tenant = TenantModel(
        id=_TENANT_ID,
        slug=_TENANT_SLUG,
        name="Acme",
    )
    db.add(tenant)
    db.flush()
    return tenant


class TestRedirect:
    def test_unknown_tenant_returns_404(self, client: TestClient) -> None:
        response = client.get(f"/api/v1/public/tenants/ghost/offers/{uuid.uuid4()}")
        assert response.status_code == 404

    @_skip_if_no_offer
    def test_redirects_to_edition(
        self,
        client: TestClient,
    ) -> None:
        """Requires luana_core_offer — deferred to Story 5."""

    @_skip_if_no_offer
    def test_no_public_edition_returns_404(
        self,
        client: TestClient,
        tenant_row: TenantModel,
        db: "Session",
    ) -> None:
        """Requires luana_core_offer — deferred to Story 5."""


class TestEditionLanding:
    @_skip_if_no_offer
    def test_serves_edition_landing(
        self,
        client: TestClient,
    ) -> None:
        """Requires luana_core_offer — deferred to Story 5."""

    @_skip_if_no_offer
    def test_bogus_edition_number_returns_404(
        self,
        client: TestClient,
    ) -> None:
        """Requires luana_core_offer — deferred to Story 5."""
