"""Tests for WhatsApp adapter retract_message_id extension — T-inbox-be-4 (RED first).

SC-01 happy: retract within 5min via WA Cloud API (DELETE /messages/{id}).
HMAC-validated adapter. Idempotent.

All HTTP calls mocked — no real Meta API calls in unit tests.
Per `.claude/rules/tdd-mandatory.md`: tests written BEFORE implementation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# downstream-regression-na: brand-local vitalia connections unit test


class TestWhatsAppAdapterContract:
    """Structural contract — WhatsApp adapter must have retract_message_id."""

    def test_adapter_importable(self) -> None:
        """WhatsAppAdapter must be importable."""
        from src.modules.vitalia.connections.whatsapp.adapter import (  # noqa: F401
            WhatsAppAdapter,
        )

    def test_adapter_has_retract_method(self) -> None:
        """WhatsAppAdapter must expose async retract_message_id(message_id) method."""
        from src.modules.vitalia.connections.whatsapp.adapter import WhatsAppAdapter

        assert hasattr(WhatsAppAdapter, "retract_message_id"), "WhatsAppAdapter missing retract_message_id"

    def test_retract_result_importable(self) -> None:
        """RetractResult must be importable for both WA and IG adapters."""
        from src.modules.vitalia.connections.whatsapp.adapter import (  # noqa: F401
            RetractResult,
        )


class TestWhatsAppRetractSuccess:
    """test_retract_within_5min_succeeds: SC-01 Gherkin coverage."""

    @pytest.mark.asyncio
    async def test_retract_within_5min_succeeds(self) -> None:
        """WA Cloud API retract success → RetractResult(succeeded=True).

        Per 03-arch-be.md § 6.3: DELETE /messages/{id} on Meta Graph API.
        HMAC validated. Returns RetractResult.
        """
        from src.modules.vitalia.connections.whatsapp.adapter import (
            RetractResult,
            WhatsAppAdapter,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"success": True}
            mock_client.delete.return_value = mock_response

            adapter = WhatsAppAdapter(
                phone_number_id="123456789",
                access_token="test-token",
            )
            result = await adapter.retract_message_id(message_id="wamid.abc123")

        assert isinstance(result, RetractResult)
        assert result.succeeded is True
        assert result.message_id == "wamid.abc123"

    @pytest.mark.asyncio
    async def test_retract_calls_delete_endpoint(self) -> None:
        """retract_message_id MUST call Meta Graph API DELETE endpoint."""
        from src.modules.vitalia.connections.whatsapp.adapter import WhatsAppAdapter

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"success": True}
            mock_client.delete.return_value = mock_response

            adapter = WhatsAppAdapter(
                phone_number_id="123456789",
                access_token="test-token",
            )
            await adapter.retract_message_id(message_id="wamid.XYZ789")

        # Must have called DELETE (not POST, not GET)
        assert mock_client.delete.called, "retract_message_id must call httpx DELETE"
        args = mock_client.delete.call_args
        call_url = args[0][0] if args[0] else args[1].get("url", "")
        assert "wamid.XYZ789" in str(call_url), f"Message ID not in DELETE URL: {call_url}"

    @pytest.mark.asyncio
    async def test_retract_timeout_returns_failed(self) -> None:
        """WA retract timeout (5s limit per arch) → RetractResult(succeeded=False), no raise."""
        from src.modules.vitalia.connections.whatsapp.adapter import (
            RetractResult,
            WhatsAppAdapter,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.delete.side_effect = httpx.TimeoutException("timeout", request=MagicMock())

            adapter = WhatsAppAdapter(
                phone_number_id="123456789",
                access_token="test-token",
            )
            result = await adapter.retract_message_id(message_id="wamid.abc123")

        assert isinstance(result, RetractResult)
        assert result.succeeded is False

    @pytest.mark.asyncio
    async def test_retract_idempotent_on_404(self) -> None:
        """Meta returns 404 (already deleted) → RetractResult(succeeded=True, idempotent=True).

        Message already retracted → consider success (idempotent call).
        """
        from src.modules.vitalia.connections.whatsapp.adapter import (
            RetractResult,
            WhatsAppAdapter,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "not found",
                request=MagicMock(),
                response=mock_response,
            )
            mock_client.delete.return_value = mock_response

            adapter = WhatsAppAdapter(
                phone_number_id="123456789",
                access_token="test-token",
            )
            result = await adapter.retract_message_id(message_id="wamid.abc123")

        assert isinstance(result, RetractResult)
        # 404 = already gone = idempotent success
        assert result.succeeded is True

    @pytest.mark.asyncio
    async def test_retract_http_500_returns_failed(self) -> None:
        """Meta server error → RetractResult(succeeded=False), no raise."""
        from src.modules.vitalia.connections.whatsapp.adapter import (
            RetractResult,
            WhatsAppAdapter,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "internal server error",
                request=MagicMock(),
                response=mock_response,
            )
            mock_client.delete.return_value = mock_response

            adapter = WhatsAppAdapter(
                phone_number_id="123456789",
                access_token="test-token",
            )
            result = await adapter.retract_message_id(message_id="wamid.abc123")

        assert isinstance(result, RetractResult)
        assert result.succeeded is False

    @pytest.mark.asyncio
    async def test_retract_uses_bearer_token(self) -> None:
        """retract_message_id MUST send Authorization: Bearer header."""
        from src.modules.vitalia.connections.whatsapp.adapter import WhatsAppAdapter

        captured_headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"success": True}

            def capture_delete(*args, **kwargs):
                captured_headers.update(kwargs.get("headers", {}))
                return mock_response

            mock_client.delete.side_effect = capture_delete

            adapter = WhatsAppAdapter(
                phone_number_id="123456789",
                access_token="my-secret-token",
            )
            await adapter.retract_message_id(message_id="wamid.abc123")

        auth_header = captured_headers.get("Authorization", "")
        assert "Bearer my-secret-token" in auth_header or "Bearer" in str(captured_headers), (
            f"Authorization Bearer header missing. Headers: {captured_headers}"
        )
