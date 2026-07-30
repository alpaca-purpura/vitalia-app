# cap: adrian.inbox
"""Tests for Telegram inbound webhook security — T-BE-1 (RED first).

Covers V-NF-1 (secret validation + update_id dedup) + V-FN-5 (SC-5) + V-FN-6 (SC-6 tenant isolation).

Test order (TDD RED-first per tdd-mandatory.md):
  1. Invalid secret → ack but no dispatch (V-NF-1)
  2. Valid secret + first update_id → dispatch exactly once (V-FN-5)
  3. Duplicate update_id → no second dispatch (V-FN-5)
  4. Tenant isolation — bot token resolves correct tenant_id (V-FN-6)

All heavy deps (DB, orchestrator, connections lookup) are mocked — pure unit tests.
Integration marker tests use @pytest.mark.integration and require live DB.

Per hipaa-lite.md: Telegram update payloads are NOT PHI (no clinical data);
audit log not required at route layer. sanitize_payload is engine-layer (chat.py).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

# downstream-regression-na: brand-local vitalia connections telegram webhook security

_VALID_SECRET = "test-secret-abc123"
_TENANT_ID = str(uuid4())

_SAMPLE_UPDATE: dict[str, Any] = {
    "update_id": 999001,
    "message": {
        "message_id": 42,
        "from": {
            "id": 123456789,
            "first_name": "Ana",
            "last_name": "García",
            "username": "ana_garcia",
            "language_code": "es",
        },
        "chat": {"id": 123456789, "type": "private"},
        "text": "Hola, quiero información sobre blanqueamiento dental",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Section 1 — Adapter contract (brand-local shim)
# ─────────────────────────────────────────────────────────────────────────────


class TestTelegramAdapterContract:
    """Brand-local TelegramAdapter must be importable and implement BaseChannel."""

    def test_adapter_importable(self) -> None:
        """TelegramAdapter must be importable from connections.telegram.adapter."""
        from src.modules.vitalia.connections.telegram.adapter import (  # noqa: F401
            TelegramAdapter,
        )

    def test_adapter_has_normalize_payload(self) -> None:
        """TelegramAdapter must expose normalize_payload matching BaseChannel ABC."""
        from src.modules.vitalia.connections.telegram.adapter import TelegramAdapter

        assert hasattr(TelegramAdapter, "normalize_payload"), "TelegramAdapter missing normalize_payload"

    def test_adapter_has_send_message(self) -> None:
        """TelegramAdapter must expose async send_message matching BaseChannel ABC."""
        from src.modules.vitalia.connections.telegram.adapter import TelegramAdapter

        assert hasattr(TelegramAdapter, "send_message"), "TelegramAdapter missing send_message"

    def test_adapter_normalize_returns_none_for_non_text(self) -> None:
        """normalize_payload returns None for non-text updates (photos, status)."""
        from src.modules.vitalia.connections.telegram.adapter import TelegramAdapter

        adapter = TelegramAdapter(token="test-token")
        # Update without message
        result = adapter.normalize_payload({"update_id": 1})
        assert result is None

    def test_adapter_normalize_extracts_text_message(self) -> None:
        """normalize_payload extracts user_id and text from a Telegram message update."""
        from src.modules.vitalia.connections.telegram.adapter import TelegramAdapter

        adapter = TelegramAdapter(token="test-token")
        result = adapter.normalize_payload(_SAMPLE_UPDATE)
        assert result is not None
        assert result.user_id == "123456789"
        assert "blanqueamiento dental" in result.text


# ─────────────────────────────────────────────────────────────────────────────
# Section 2 — DTO contract
# ─────────────────────────────────────────────────────────────────────────────


class TestTelegramWebhookDtoContract:
    """TelegramWebhookAck DTO must be importable and have required fields."""

    def test_ack_dto_importable(self) -> None:
        """TelegramWebhookAck must be importable."""
        from src.modules.vitalia.connections.telegram.api.dtos import (  # noqa: F401
            TelegramWebhookAck,
        )

    def test_ack_dto_has_ok_field(self) -> None:
        """TelegramWebhookAck must have ok: bool field."""
        from src.modules.vitalia.connections.telegram.api.dtos import TelegramWebhookAck

        ack = TelegramWebhookAck(ok=True)
        assert ack.ok is True

    def test_ack_dto_pydantic_v2(self) -> None:
        """TelegramWebhookAck must use Pydantic v2 ConfigDict (no inner class Config)."""
        from src.modules.vitalia.connections.telegram.api.dtos import TelegramWebhookAck

        # Pydantic v2: model_config is a class attribute (ConfigDict), not inner class
        assert hasattr(TelegramWebhookAck, "model_config"), (
            "TelegramWebhookAck must use Pydantic v2 model_config = ConfigDict(...)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — Secret validation (V-NF-1 / SC-5)
# ─────────────────────────────────────────────────────────────────────────────


class TestTelegramWebhookSecretValidation:
    """V-NF-1: Secret inválido → descarta SIN dispatch; secret válido → dispatch."""

    def test_router_importable(self) -> None:
        """Telegram webhook router must be importable."""
        from src.modules.vitalia.connections.telegram.api.router import (  # noqa: F401
            router as telegram_router,
        )

    def test_router_has_webhook_endpoint(self) -> None:
        """Router must expose POST /webhook endpoint."""
        from src.modules.vitalia.connections.telegram.api.router import router as telegram_router

        routes = [(r.path, list(r.methods)) for r in telegram_router.routes]  # type: ignore[attr-defined]
        # /webhook with POST
        webhook_paths = [p for p, m in routes if "POST" in m and "webhook" in p]
        assert len(webhook_paths) >= 1, f"No POST webhook route found. Routes: {routes}"

    @pytest.mark.asyncio
    async def test_invalid_secret_returns_ack_no_dispatch(self) -> None:
        """V-NF-1 / SC-5: Invalid X-Telegram-Bot-Api-Secret-Token → 200 ack, orchestrator NOT called.

        Telegram convention: never return 4xx (retry storm). Discard internally + log.
        """
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from src.modules.vitalia.connections.telegram.api.router import router as telegram_router

        app = FastAPI()
        app.include_router(telegram_router, prefix="/api/v1/connections/telegram")

        with (
            patch(
                "src.modules.vitalia.connections.telegram.api.router.TELEGRAM_WEBHOOK_SECRET",
                _VALID_SECRET,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._is_update_seen",
                return_value=False,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._orchestrator_dispatch",
            ) as mock_dispatch,
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/connections/telegram/webhook",
                    json=_SAMPLE_UPDATE,
                    headers={"X-Telegram-Bot-Api-Secret-Token": "WRONG_SECRET"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True  # still ack (Telegram convention)
        mock_dispatch.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_secret_dispatches_once(self) -> None:
        """V-NF-1 / SC-5: Valid secret + first update_id → dispatch called once."""
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from src.modules.vitalia.connections.telegram.api.router import router as telegram_router

        app = FastAPI()
        app.include_router(telegram_router, prefix="/api/v1/connections/telegram")

        with (
            patch(
                "src.modules.vitalia.connections.telegram.api.router.TELEGRAM_WEBHOOK_SECRET",
                _VALID_SECRET,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._is_update_seen",
                return_value=False,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._mark_update_seen",
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._resolve_tenant_id",
                return_value=_TENANT_ID,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._orchestrator_dispatch",
                new_callable=AsyncMock,
            ) as mock_dispatch,
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/connections/telegram/webhook",
                    json=_SAMPLE_UPDATE,
                    headers={"X-Telegram-Bot-Api-Secret-Token": _VALID_SECRET},
                )

        assert response.status_code == 200
        assert response.json()["ok"] is True
        mock_dispatch.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_update_id_no_second_dispatch(self) -> None:
        """V-FN-5 (SC-5): Duplicate update_id → idempotent (no second dispatch)."""
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from src.modules.vitalia.connections.telegram.api.router import router as telegram_router

        app = FastAPI()
        app.include_router(telegram_router, prefix="/api/v1/connections/telegram")

        with (
            patch(
                "src.modules.vitalia.connections.telegram.api.router.TELEGRAM_WEBHOOK_SECRET",
                _VALID_SECRET,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._is_update_seen",
                return_value=True,  # already seen
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._orchestrator_dispatch",
                new_callable=AsyncMock,
            ) as mock_dispatch,
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/connections/telegram/webhook",
                    json=_SAMPLE_UPDATE,
                    headers={"X-Telegram-Bot-Api-Secret-Token": _VALID_SECRET},
                )

        assert response.status_code == 200
        assert response.json()["ok"] is True
        mock_dispatch.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Section 4 — Tenant isolation (V-FN-6 / SC-6)
# ─────────────────────────────────────────────────────────────────────────────


class TestTelegramTenantIsolation:
    """V-FN-6 / SC-6: Bot token resolves correct tenant_id (dual-filter)."""

    @pytest.mark.asyncio
    async def test_dispatch_receives_correct_tenant_id(self) -> None:
        """Dispatch must be called with the tenant_id resolved from bot token.

        SC-6: Bot A → data A only (tenant isolation at dispatch level).
        The engine handle_telegram_webhook uses tenant_id to scope the conversation.
        """
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        tenant_a = str(uuid4())

        from src.modules.vitalia.connections.telegram.api.router import router as telegram_router

        app = FastAPI()
        app.include_router(telegram_router, prefix="/api/v1/connections/telegram")

        dispatched_with: dict[str, Any] = {}

        async def capture_dispatch(
            payload: dict,
            background_tasks: Any,
            tenant_id: str | None,
            db: Any,
        ) -> None:
            dispatched_with["tenant_id"] = tenant_id

        with (
            patch(
                "src.modules.vitalia.connections.telegram.api.router.TELEGRAM_WEBHOOK_SECRET",
                _VALID_SECRET,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._is_update_seen",
                return_value=False,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._mark_update_seen",
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._resolve_tenant_id",
                return_value=tenant_a,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._orchestrator_dispatch",
                side_effect=capture_dispatch,
            ),
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                await ac.post(
                    "/api/v1/connections/telegram/webhook",
                    json=_SAMPLE_UPDATE,
                    headers={"X-Telegram-Bot-Api-Secret-Token": _VALID_SECRET},
                )

        assert dispatched_with.get("tenant_id") == tenant_a, (
            f"Expected tenant_id={tenant_a}, got {dispatched_with.get('tenant_id')}"
        )

    @pytest.mark.asyncio
    async def test_missing_message_field_skipped(self) -> None:
        """Non-message updates (edit, channel_post) → ack with no dispatch (normalize returns None)."""
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from src.modules.vitalia.connections.telegram.api.router import router as telegram_router

        app = FastAPI()
        app.include_router(telegram_router, prefix="/api/v1/connections/telegram")

        non_message_update = {"update_id": 999002, "edited_message": {"message_id": 1}}

        with (
            patch(
                "src.modules.vitalia.connections.telegram.api.router.TELEGRAM_WEBHOOK_SECRET",
                _VALID_SECRET,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._is_update_seen",
                return_value=False,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._mark_update_seen",
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._resolve_tenant_id",
                return_value=_TENANT_ID,
            ),
            patch(
                "src.modules.vitalia.connections.telegram.api.router._orchestrator_dispatch",
                new_callable=AsyncMock,
            ) as mock_dispatch,
        ):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/connections/telegram/webhook",
                    json=non_message_update,
                    headers={"X-Telegram-Bot-Api-Secret-Token": _VALID_SECRET},
                )

        assert response.status_code == 200
        assert response.json()["ok"] is True
        # Non-message update → normalize_payload returns None → no dispatch
        mock_dispatch.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Section 5 — response_model present (V-NF-4)
# ─────────────────────────────────────────────────────────────────────────────


class TestTelegramWebhookResponseModel:
    """V-NF-4: Every route must declare response_model= (PII gate)."""

    def test_webhook_route_has_response_model(self) -> None:
        """POST /webhook route must declare response_model=TelegramWebhookAck."""
        from src.modules.vitalia.connections.telegram.api.dtos import TelegramWebhookAck
        from src.modules.vitalia.connections.telegram.api.router import router as telegram_router

        for route in telegram_router.routes:  # type: ignore[attr-defined]
            if hasattr(route, "path") and "webhook" in route.path:
                assert route.response_model is TelegramWebhookAck, (  # type: ignore[attr-defined]
                    f"Route {route.path} must have response_model=TelegramWebhookAck"
                )
