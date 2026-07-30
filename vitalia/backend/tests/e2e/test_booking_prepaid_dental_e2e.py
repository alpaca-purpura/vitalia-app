"""E2E test — booking prepaid dental happy path (T-be-7 A+ + V-F-6).

V-F-6 validator: spec § 3.4.A happy booking prepaid.

Per spec § 3.4.A:
  - POST /bookings → 201, status=pending_payment (requires_prepay=True)
  - GET /bookings/available-slots → 200 with slots list
  - POST /bookings/{id}/confirm-payment → 200, payment confirmed
  - POST /bookings/{id}/consent-sign → 200, signed
  - POST /bookings/{id}/cancel → 200, soft-cancelled
  - POST /bookings/{id}/reschedule → 200, new slot

Tests run WITHOUT live Postgres — httpx.AsyncClient + ASGITransport.
DB integration tests are in tests/integration/test_booking_repository.py.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app

TENANT_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
HEADERS = {"X-Tenant-ID": TENANT_ID}

DOCTOR_ID = str(uuid4())
OFFER_ID = str(uuid4())
PATIENT_ID = str(uuid4())
SLOT_ISO = "2026-12-15T10:00:00Z"
SLOT_ISO_NEW = "2026-12-16T14:00:00Z"


@pytest.fixture
async def client():
    """httpx.AsyncClient targeting vitalia FastAPI app via ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestBookingPrepaidHappyPath:
    """Spec § 3.4.A — prepaid booking flow."""

    async def test_create_booking_prepaid_returns_201(self, client: AsyncClient) -> None:
        """POST /bookings with requires_prepay=True → 201, status=pending_payment."""
        response = await client.post(
            "/api/v1/vitalia/bookings",
            json={
                "offer_id": OFFER_ID,
                "doctor_id": DOCTOR_ID,
                "patient_id": PATIENT_ID,
                "slot_iso": SLOT_ISO,
                "delivery_channel": "whatsapp",
                "requires_prepay": True,
                "deposit_only": True,
            },
            headers=HEADERS,
        )
        assert response.status_code == 201, f"Expected 201: {response.text}"
        body = response.json()
        assert "booking_id" in body
        assert body["status"] == "pending_payment"
        assert isinstance(body["is_idempotent_hit"], bool)

    async def test_create_booking_awaiting_consent(self, client: AsyncClient) -> None:
        """POST /bookings with requires_informed_consent=True → status=awaiting_consent."""
        response = await client.post(
            "/api/v1/vitalia/bookings",
            json={
                "offer_id": OFFER_ID,
                "doctor_id": DOCTOR_ID,
                "patient_id": PATIENT_ID,
                "slot_iso": SLOT_ISO,
                "delivery_channel": "email",
                "requires_informed_consent": True,
                "requires_prepay": True,
                "deposit_only": True,
            },
            headers=HEADERS,
        )
        assert response.status_code == 201
        body = response.json()
        # consent takes priority over prepay per spec
        assert body["status"] == "awaiting_consent"

    async def test_create_booking_confirmed_deposit_no_flags(self, client: AsyncClient) -> None:
        """POST /bookings with no special flags → status=confirmed_deposit."""
        response = await client.post(
            "/api/v1/vitalia/bookings",
            json={
                "offer_id": OFFER_ID,
                "doctor_id": DOCTOR_ID,
                "patient_id": PATIENT_ID,
                "slot_iso": SLOT_ISO,
                "delivery_channel": "both",
                "requires_prepay": False,
                "deposit_only": False,
            },
            headers=HEADERS,
        )
        assert response.status_code == 201
        assert response.json()["status"] == "confirmed_deposit"

    async def test_available_slots_returns_200(self, client: AsyncClient) -> None:
        """GET /bookings/available-slots → 200 with expected structure."""
        response = await client.get(
            "/api/v1/vitalia/bookings/available-slots",
            params={
                "doctor_id": DOCTOR_ID,
                "offer_id": OFFER_ID,
                "window_start": SLOT_ISO,
                "window_days": 7,
            },
            headers=HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert "slots" in body
        assert isinstance(body["slots"], list)
        assert "doctor_id" in body
        assert "offer_id" in body
        assert body["window_days"] == 7

    async def test_list_bookings_returns_200(self, client: AsyncClient) -> None:
        """GET /bookings → 200 with bookings list + total."""
        response = await client.get(
            "/api/v1/vitalia/bookings",
            headers=HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert "bookings" in body
        assert isinstance(body["bookings"], list)
        assert "total" in body

    async def test_confirm_payment_succeeded(self, client: AsyncClient) -> None:
        """POST /bookings/{id}/confirm-payment with succeeded → booking_status=confirmed_deposit."""
        booking_id = str(uuid4())
        response = await client.post(
            f"/api/v1/vitalia/bookings/{booking_id}/confirm-payment",
            json={
                "gateway_payment_id": "pi_test_123456",
                "gateway": "stripe_connect",
                "amount": "199.00",
                "currency": "USD",
                "status": "succeeded",
            },
            headers=HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["payment_status"] == "succeeded"
        assert body["booking_status"] == "confirmed_deposit"

    async def test_confirm_payment_failed(self, client: AsyncClient) -> None:
        """POST /bookings/{id}/confirm-payment with failed → payment_status=failed."""
        booking_id = str(uuid4())
        response = await client.post(
            f"/api/v1/vitalia/bookings/{booking_id}/confirm-payment",
            json={
                "gateway_payment_id": "pi_test_fail_789",
                "gateway": "mercadopago",
                "amount": "150.00",
                "currency": "ARS",
                "status": "failed",
            },
            headers=HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["payment_status"] == "failed"
        assert body["booking_status"] == "pending_payment"

    async def test_consent_sign_returns_200(self, client: AsyncClient) -> None:
        """POST /bookings/{id}/consent-sign → 200 with consent_record_id + signed_at."""
        booking_id = str(uuid4())
        response = await client.post(
            f"/api/v1/vitalia/bookings/{booking_id}/consent-sign",
            json={
                "signed_name": "Juan García",
                "signature_method": "typed_name",
                "consent_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.stub",
            },
            headers=HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert "consent_record_id" in body
        assert body["status"] == "signed"
        assert "signed_at" in body

    async def test_cancel_booking_returns_200(self, client: AsyncClient) -> None:
        """POST /bookings/{id}/cancel → 200, status=cancelled (soft delete)."""
        booking_id = str(uuid4())
        response = await client.post(
            f"/api/v1/vitalia/bookings/{booking_id}/cancel",
            json={"reason": "Paciente reprogramó por viaje"},
            headers=HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "cancelled"
        assert "cancelled_at" in body

    async def test_reschedule_booking_returns_200(self, client: AsyncClient) -> None:
        """POST /bookings/{id}/reschedule → 200 with old + new slot."""
        booking_id = str(uuid4())
        response = await client.post(
            f"/api/v1/vitalia/bookings/{booking_id}/reschedule",
            json={
                "new_slot_iso": SLOT_ISO_NEW,
                "reason": "Cambio de agenda del médico",
            },
            headers=HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert "booking_id" in body
        assert "old_slot_iso" in body
        assert "new_slot_iso" in body
        # new_slot_iso in response should match requested
        assert "2026-12-16" in body["new_slot_iso"]

    async def test_create_booking_invalid_delivery_channel(self, client: AsyncClient) -> None:
        """POST /bookings with invalid delivery_channel → 422."""
        response = await client.post(
            "/api/v1/vitalia/bookings",
            json={
                "offer_id": OFFER_ID,
                "doctor_id": DOCTOR_ID,
                "patient_id": PATIENT_ID,
                "slot_iso": SLOT_ISO,
                "delivery_channel": "telegram",  # invalid
            },
            headers=HEADERS,
        )
        assert response.status_code == 422

    async def test_create_booking_missing_required_fields(self, client: AsyncClient) -> None:
        """POST /bookings with missing required fields → 422."""
        response = await client.post(
            "/api/v1/vitalia/bookings",
            json={"offer_id": OFFER_ID},  # missing doctor_id, patient_id, slot_iso, delivery_channel
            headers=HEADERS,
        )
        assert response.status_code == 422

    async def test_available_slots_window_days_validation(self, client: AsyncClient) -> None:
        """GET /bookings/available-slots with window_days=0 → 422 (ge=1)."""
        response = await client.get(
            "/api/v1/vitalia/bookings/available-slots",
            params={
                "doctor_id": DOCTOR_ID,
                "offer_id": OFFER_ID,
                "window_start": SLOT_ISO,
                "window_days": 0,  # invalid: ge=1
            },
            headers=HEADERS,
        )
        assert response.status_code == 422
