"""E2E test — onboarding dental clinic happy path (T-be-7 A3 + V-F-5).

A3 acceptance criterion: Spec § 3.1.A happy onboarding dental passes E2E.

Per spec § 3.1.A (Scenario — Happy path dental clinic Argentina):
  - POST /onboarding/clinic-profile → 201 with tenant_id + clinic_type=dental
  - GET /onboarding/plans → 200 with plan list
  - GET /onboarding/status → 200 with onboarding_complete field

Tests run WITHOUT a live Postgres instance — uses httpx.AsyncClient + ASGITransport
targeting the FastAPI app directly.

If Postgres unavailable: tests pass (API layer tested independently).
Mark integration tests separately if DB-backed assertions needed.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app

TENANT_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
HEADERS = {"X-Tenant-ID": TENANT_ID, "X-Clerk-User-ID": "clerk_dental_aurora_01"}


@pytest.fixture
async def client():
    """httpx.AsyncClient targeting vitalia FastAPI app via ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHappyPathOnboardingDental:
    """Scenario 3.1.A — dental clinic Argentina onboarding."""

    async def test_happy_path(self, client: AsyncClient) -> None:
        """A3: Full onboarding sequence passes — clinic_profile → plans → status."""
        # Step 1: Create clinic profile
        response = await client.post(
            "/api/v1/vitalia/onboarding/clinic-profile",
            json={
                "clinic_name": "Clínica Dental Aurora",
                "clinic_type": "dental",
                "country": "AR",
                "city": "Buenos Aires",
                "plan_tier": "clinic",
            },
            headers=HEADERS,
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        body = response.json()

        # Verify response fields (per A3 + spec § 3.1.A)
        assert "tenant_id" in body
        assert body["clinic_name"] == "Clínica Dental Aurora"
        assert body["clinic_type"] == "dental"
        assert body["country"] == "AR"
        assert body["city"] == "Buenos Aires"
        assert body["plan_tier"] == "clinic"
        assert isinstance(body["is_new"], bool)
        assert "created_at" in body

        # Step 2: List plans
        plans_response = await client.get(
            "/api/v1/vitalia/onboarding/plans",
            headers=HEADERS,
        )
        assert plans_response.status_code == 200
        plans_body = plans_response.json()
        assert "plans" in plans_body
        assert isinstance(plans_body["plans"], list)
        assert len(plans_body["plans"]) > 0

        plan_slugs = [p["slug"] for p in plans_body["plans"]]
        assert "clinic" in plan_slugs, "clinic plan must be available"
        assert "starter" in plan_slugs

        # Each plan has required fields
        for plan in plans_body["plans"]:
            assert "slug" in plan
            assert "label_es" in plan
            assert "price_usd_monthly" in plan
            assert "features_enabled" in plan

        # Step 3: Check onboarding status
        status_response = await client.get(
            "/api/v1/vitalia/onboarding/status",
            headers=HEADERS,
        )
        assert status_response.status_code == 200
        status_body = status_response.json()
        assert "tenant_id" in status_body
        assert "onboarding_complete" in status_body
        assert isinstance(status_body["onboarding_complete"], bool)

    async def test_create_clinic_profile_returns_201(self, client: AsyncClient) -> None:
        """POST /onboarding/clinic-profile returns 201 with valid payload."""
        response = await client.post(
            "/api/v1/vitalia/onboarding/clinic-profile",
            json={
                "clinic_name": "Mindful Psicología",
                "clinic_type": "psychology",
                "country": "CL",
                "city": "Santiago",
                "plan_tier": "multi_site",
            },
            headers={"X-Tenant-ID": TENANT_ID, "X-Clerk-User-ID": "clerk_mindful_01"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["clinic_type"] == "psychology"
        assert body["country"] == "CL"

    async def test_create_clinic_profile_invalid_clinic_type(self, client: AsyncClient) -> None:
        """POST /onboarding/clinic-profile with invalid clinic_type → 422."""
        response = await client.post(
            "/api/v1/vitalia/onboarding/clinic-profile",
            json={
                "clinic_name": "Test Clinic",
                "clinic_type": "veterinary",  # invalid
                "country": "AR",
                "city": "Córdoba",
                "plan_tier": "starter",
            },
            headers=HEADERS,
        )
        assert response.status_code == 422
        body = response.json()
        assert "detail" in body

    async def test_create_clinic_profile_missing_required_fields(self, client: AsyncClient) -> None:
        """POST /onboarding/clinic-profile with missing fields → 422."""
        response = await client.post(
            "/api/v1/vitalia/onboarding/clinic-profile",
            json={"clinic_name": "Incomplete"},  # missing clinic_type, country, city, plan_tier
            headers=HEADERS,
        )
        assert response.status_code == 422

    async def test_create_clinic_profile_invalid_country(self, client: AsyncClient) -> None:
        """POST /onboarding/clinic-profile with 3-char country → 422 (ISO 3166-1 alpha-2 required)."""
        response = await client.post(
            "/api/v1/vitalia/onboarding/clinic-profile",
            json={
                "clinic_name": "Test",
                "clinic_type": "dental",
                "country": "ARG",  # 3-char, invalid (must be 2)
                "city": "Buenos Aires",
                "plan_tier": "starter",
            },
            headers=HEADERS,
        )
        assert response.status_code == 422

    async def test_subscribe_returns_201(self, client: AsyncClient) -> None:
        """POST /onboarding/subscribe returns 201 with checkout_url."""
        response = await client.post(
            "/api/v1/vitalia/onboarding/subscribe",
            json={
                "plan_tier": "clinic",
                "success_url": "https://app.vitalia.health/onboarding/success",
                "cancel_url": "https://app.vitalia.health/onboarding/plans",
            },
            headers=HEADERS,
        )
        assert response.status_code == 201
        body = response.json()
        assert "checkout_url" in body
        assert body["plan_tier"] == "clinic"

    async def test_missing_tenant_id_header(self, client: AsyncClient) -> None:
        """Request without X-Tenant-ID header → 422 (missing required header)."""
        response = await client.post(
            "/api/v1/vitalia/onboarding/clinic-profile",
            json={
                "clinic_name": "Test",
                "clinic_type": "dental",
                "country": "AR",
                "city": "Buenos Aires",
                "plan_tier": "starter",
            },
        )
        assert response.status_code == 422

    async def test_offer_presets_endpoint(self, client: AsyncClient) -> None:
        """GET /offer/presets returns medical_services_v1 preset."""
        response = await client.get(
            "/api/v1/vitalia/offer/presets",
            headers=HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["preset_id"] == "medical_services_v1"
        assert "label_es" in body
        assert "base_sections" in body
        assert isinstance(body["base_sections"], list)
        assert "default_flags" in body
        assert isinstance(body["examples_es"], list)
        assert len(body["examples_es"]) >= 2  # arch test: ≥2 examples
