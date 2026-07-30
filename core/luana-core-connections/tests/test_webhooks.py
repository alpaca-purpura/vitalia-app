"""Tests for connections webhook endpoints.

Lifted from AISALESHT. Adapted from src.main app to local mini-app
per luana-platform lift pattern (Story 4 T-5).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from luana_core_connections.api.dependencies import get_message_handler
from luana_core_connections.api.marketing_webhooks import router as marketing_webhooks_router
from luana_core_connections.api.meta import router as meta_router
from luana_core_connections.api.shopify_compliance import router as shopify_compliance_router
from luana_core_platform.core.database import get_db  # composition root — used for DI override


def _create_test_app() -> FastAPI:
    """Create a minimal FastAPI app with connections webhook routes."""
    app = FastAPI(redirect_slashes=False)
    app.include_router(
        marketing_webhooks_router,
        prefix="/api/v1/connections/marketing-webhooks",
        tags=["connections-webhooks"],
    )
    app.include_router(
        shopify_compliance_router,
        prefix="/api/v1/connections/shopify/compliance",
        tags=["connections-shopify-compliance"],
    )
    app.include_router(
        meta_router,
        prefix="/api/v1/connections/meta",
        tags=["connections-meta"],
    )
    return app


@pytest.fixture(scope="module")
def app():
    return _create_test_app()


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


# Helper functions to generate signatures
def generate_shopify_signature(secret, body):
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def generate_meta_signature(secret, body):
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.fixture
def mock_settings():
    with patch(
        "luana_core_connections.api.dependencies.webhook_security.settings",
    ) as mock:
        mock.SHOPIFY_API_SECRET = "test_shopify_secret"
        mock.META_APP_SECRET = "test_meta_secret"
        yield mock


@pytest.fixture
def mock_db(app):
    mock_session = MagicMock()
    mock_handler = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_session
    # Override get_message_handler stub (deferred Story 7 composition root)
    app.dependency_overrides[get_message_handler] = lambda: mock_handler
    yield mock_session
    app.dependency_overrides = {}


# --- Shopify Tests ---


def test_shopify_signature_valid(client, mock_settings, mock_db):
    payload = {"test": "shopify_data"}
    body = json.dumps(payload).encode("utf-8")
    signature = generate_shopify_signature(mock_settings.SHOPIFY_API_SECRET, body)

    headers = {"X-Shopify-Hmac-Sha256": signature, "Content-Type": "application/json"}

    response = client.post(
        "/api/v1/connections/marketing-webhooks/shopify",
        content=body,
        headers=headers,
    )

    # Valid signature must not return 401 (signature error)
    assert response.status_code == 200
    assert response.json().get("status") != "invalid_signature"


def test_shopify_signature_invalid(client, mock_settings, mock_db):
    payload = {"test": "shopify_data"}
    body = json.dumps(payload).encode("utf-8")

    headers = {
        "X-Shopify-Hmac-Sha256": "invalid_signature",
        "Content-Type": "application/json",
    }

    response = client.post(
        "/api/v1/connections/marketing-webhooks/shopify",
        content=body,
        headers=headers,
    )

    # Expect 401 per implementation in webhook_security.py
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Shopify signature"


def test_shopify_compliance_data_request_valid(client, mock_settings, mock_db):
    payload = {
        "shop_id": 954889,
        "shop_domain": "johns-apparel.myshopify.com",
        "orders_requested": [299938, 280263, 220458],
        "customer": {
            "id": 191167,
            "email": "john@example.com",
            "phone": "+1-234-567-8910",
        },
    }
    body = json.dumps(payload).encode("utf-8")
    signature = generate_shopify_signature(mock_settings.SHOPIFY_API_SECRET, body)

    headers = {"X-Shopify-Hmac-Sha256": signature, "Content-Type": "application/json"}

    response = client.post(
        "/api/v1/connections/shopify/compliance/customers/data_request",
        content=body,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "received"


def test_shopify_compliance_customers_redact_valid(client, mock_settings, mock_db):
    payload = {
        "shop_id": 954889,
        "shop_domain": "johns-apparel.myshopify.com",
        "customer": {
            "id": 191167,
            "email": "john@example.com",
            "phone": "+1-234-567-8910",
        },
        "orders_to_redact": [299938, 280263, 220458],
    }
    body = json.dumps(payload).encode("utf-8")
    signature = generate_shopify_signature(mock_settings.SHOPIFY_API_SECRET, body)

    headers = {"X-Shopify-Hmac-Sha256": signature, "Content-Type": "application/json"}

    response = client.post(
        "/api/v1/connections/shopify/compliance/customers/redact",
        content=body,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "received"


def test_shopify_compliance_shop_redact_valid(client, mock_settings, mock_db):
    payload = {"shop_id": 954889, "shop_domain": "johns-apparel.myshopify.com"}
    body = json.dumps(payload).encode("utf-8")
    signature = generate_shopify_signature(mock_settings.SHOPIFY_API_SECRET, body)

    headers = {"X-Shopify-Hmac-Sha256": signature, "Content-Type": "application/json"}

    response = client.post(
        "/api/v1/connections/shopify/compliance/shop/redact",
        content=body,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "received"


def test_shopify_compliance_invalid_hmac_returns_401(client, mock_settings, mock_db):
    payload = {"shop_id": 954889, "shop_domain": "johns-apparel.myshopify.com"}
    body = json.dumps(payload).encode("utf-8")

    headers = {
        "X-Shopify-Hmac-Sha256": "invalid_signature",
        "Content-Type": "application/json",
    }

    response = client.post(
        "/api/v1/connections/shopify/compliance/shop/redact",
        content=body,
        headers=headers,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Shopify signature"


# --- Meta Tests ---


def test_meta_signature_valid(client, mock_settings, mock_db):
    # Mock DB query result
    mock_db.query.return_value.filter.return_value.all.return_value = []

    payload = {
        "object": "instagram",
        "entry": [{"id": "123456789", "time": 12345678, "changes": []}],
    }
    body = json.dumps(payload).encode("utf-8")
    signature = generate_meta_signature(mock_settings.META_APP_SECRET, body)

    headers = {"X-Hub-Signature-256": signature, "Content-Type": "application/json"}

    response = client.post(
        "/api/v1/connections/meta/webhook",
        content=body,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ignored", "reason": "unknown_account"}


def test_meta_signature_invalid(client, mock_settings, mock_db):
    payload = {"object": "instagram"}
    body = json.dumps(payload).encode("utf-8")

    headers = {
        "X-Hub-Signature-256": "sha256=invalid_signature",
        "Content-Type": "application/json",
    }

    response = client.post(
        "/api/v1/connections/meta/webhook",
        content=body,
        headers=headers,
    )

    # Expect 401 per implementation in webhook_security.py
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Meta signature"
