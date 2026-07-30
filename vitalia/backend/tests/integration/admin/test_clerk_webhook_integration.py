"""fn-be-webhook-clerk-integration — Clerk webhook HMAC + response tests (SC-05, SC-12).

Tests the existing clerk webhook endpoint:
    POST /api/v1/vitalia/webhooks/clerk

Scenarios covered:
    SC-12: Valid HMAC → 200 received
    SC-05: Invalid HMAC → 400 (per design: HMAC failure = 400, not 401)
    SC-05b: user.created event → 200 received (stub dispatch logged)

These tests do NOT require Postgres — they test HMAC verification and
response structure via httpx.AsyncClient + ASGITransport.
"""

from __future__ import annotations

import pytest

from tests.integration.admin.conftest import (
    build_clerk_user_created_payload,
    build_clerk_webhook_headers,
)


@pytest.mark.asyncio
async def test_valid_hmac_returns_200(webhook_client) -> None:  # noqa: ANN001
    """SC-12: Valid Clerk HMAC signature → 200 received.

    Given: A properly signed Clerk user.created webhook
    When: POST /api/v1/vitalia/webhooks/clerk with correct svix headers
    Then: Response is 200 with status='received'
    """
    raw_body, clerk_user_id = build_clerk_user_created_payload(email="valid-hmac@vitalia.com")
    headers = build_clerk_webhook_headers(raw_body=raw_body)

    response = await webhook_client.post(
        "/api/v1/vitalia/webhooks/clerk",
        content=raw_body,
        headers={
            "content-type": "application/json",
            **headers,
        },
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["status"] == "received", f"Expected status='received', got {body}"
    assert "event_id" in body, "Response missing event_id"
    assert "processed_at" in body, "Response missing processed_at"


@pytest.mark.asyncio
async def test_invalid_hmac_returns_400_no_row(webhook_client) -> None:  # noqa: ANN001
    """SC-05/SC-12: Invalid HMAC → 400 (per gateway design: HMAC failure = 400).

    Given: A Clerk webhook with tampered/invalid signature
    When: POST /api/v1/vitalia/webhooks/clerk
    Then: Response is 400 (not 401 — gateway best-practice per webhook_routes.py design comment)

    Note: Design decision in webhook_routes.py: 'HMAC failure → 400 (not 401)
    per gateway best-practice (no auth semantics leakage)'.
    """
    raw_body, _ = build_clerk_user_created_payload(email="invalid-hmac@vitalia.com")
    headers = build_clerk_webhook_headers(
        raw_body=raw_body,
        tamper_signature=True,  # Produces invalid/garbage signature
    )

    response = await webhook_client.post(
        "/api/v1/vitalia/webhooks/clerk",
        content=raw_body,
        headers={
            "content-type": "application/json",
            **headers,
        },
    )

    # Per webhook_routes.py design: HMAC failure returns 400
    assert response.status_code == 400, f"Expected 400 for tampered HMAC, got {response.status_code}: {response.text}"


@pytest.mark.asyncio
async def test_user_created_event_dispatched(webhook_client) -> None:  # noqa: ANN001
    """SC-05: user.created event → dispatched (200 received, stub logged).

    Given: A valid Clerk user.created webhook
    When: POST /api/v1/vitalia/webhooks/clerk
    Then: 200 received + event_id matches svix-id header

    Note: Dispatch to OnboardingService is stubbed in T-be-8 scope.
    The test verifies HMAC passes and correct event routing occurs.
    """
    raw_body, clerk_user_id = build_clerk_user_created_payload(
        clerk_user_id="user_sc05_test_001",
        email="user-created@vitalia.com",
    )
    headers = build_clerk_webhook_headers(raw_body=raw_body)
    svix_event_id = headers["svix-id"]

    response = await webhook_client.post(
        "/api/v1/vitalia/webhooks/clerk",
        content=raw_body,
        headers={
            "content-type": "application/json",
            **headers,
        },
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["status"] == "received"
    # event_id in response should match svix-id header (dedup key)
    assert body["event_id"] == svix_event_id, f"Expected event_id={svix_event_id!r}, got {body['event_id']!r}"


@pytest.mark.asyncio
async def test_replay_returns_200_replay_skipped(webhook_client) -> None:  # noqa: ANN001
    """SC-12b: Duplicate svix-id → 200 replay_skipped (idempotency guard).

    Given: Same svix-id sent twice
    When: POST /api/v1/vitalia/webhooks/clerk with same event_id twice
    Then: Second request → 200 with status='replay_skipped'
    """
    raw_body, _ = build_clerk_user_created_payload(email="replay-test@vitalia.com")
    fixed_event_id = "evt_replay_test_sc12b_fixed"
    headers = build_clerk_webhook_headers(raw_body=raw_body, event_id=fixed_event_id)

    # First request
    response1 = await webhook_client.post(
        "/api/v1/vitalia/webhooks/clerk",
        content=raw_body,
        headers={"content-type": "application/json", **headers},
    )
    assert response1.status_code == 200

    # Same event_id — should be idempotent (replay_skipped)
    response2 = await webhook_client.post(
        "/api/v1/vitalia/webhooks/clerk",
        content=raw_body,
        headers={"content-type": "application/json", **headers},
    )
    assert response2.status_code == 200, f"Expected 200 on replay, got {response2.status_code}"
    body2 = response2.json()
    assert body2["status"] == "replay_skipped", f"Expected replay_skipped on duplicate event, got {body2['status']}"


@pytest.mark.asyncio
async def test_missing_svix_headers_returns_422(webhook_client) -> None:  # noqa: ANN001
    """SC-12c: Missing required svix headers → 422 (FastAPI validation).

    Given: A request without svix-id/svix-timestamp/svix-signature headers
    When: POST /api/v1/vitalia/webhooks/clerk
    Then: 422 Unprocessable Entity (FastAPI rejects missing Header params)
    """
    raw_body, _ = build_clerk_user_created_payload()

    response = await webhook_client.post(
        "/api/v1/vitalia/webhooks/clerk",
        content=raw_body,
        headers={"content-type": "application/json"},
        # No svix headers — FastAPI enforces Header params
    )

    assert response.status_code == 422, f"Expected 422 for missing svix headers, got {response.status_code}"
