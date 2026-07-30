"""Tests for Instagram adapter retract_message_id extension — T-inbox-be-4 (RED first).

SC-01 happy: retract via Instagram Graph API.
HMAC-validated adapter. Idempotent.

All HTTP calls mocked — no real Meta API calls in unit tests.
Per `.claude/rules/tdd-mandatory.md`: tests written BEFORE implementation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# downstream-regression-na: brand-local vitalia connections unit test


class TestInstagramAdapterContract:
    """Structural contract — Instagram adapter must have retract_message_id."""

    def test_adapter_importable(self) -> None:
        """InstagramAdapter must be importable."""
        from src.modules.vitalia.connections.instagram.adapter import (  # noqa: F401
            InstagramAdapter,
        )

    def test_adapter_has_retract_method(self) -> None:
        """InstagramAdapter must expose async retract_message_id(message_id)."""
        from src.modules.vitalia.connections.instagram.adapter import InstagramAdapter

        assert hasattr(InstagramAdapter, "retract_message_id"), "InstagramAdapter missing retract_message_id"

    def test_retract_result_importable(self) -> None:
        """RetractResult must be importable from instagram adapter."""
        from src.modules.vitalia.connections.instagram.adapter import (  # noqa: F401
            RetractResult,
        )


class TestInstagramRetractSuccess:
    """Instagram retract_message_id tests."""

    @pytest.mark.asyncio
    async def test_retract_succeeds(self) -> None:
        """IG Graph API retract success → RetractResult(succeeded=True)."""
        from src.modules.vitalia.connections.instagram.adapter import (
            InstagramAdapter,
            RetractResult,
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

            adapter = InstagramAdapter(
                page_id="page123",
                access_token="test-token",
            )
            result = await adapter.retract_message_id(message_id="ig_msg_abc123")

        assert isinstance(result, RetractResult)
        assert result.succeeded is True
        assert result.message_id == "ig_msg_abc123"

    @pytest.mark.asyncio
    async def test_retract_calls_ig_graph_api(self) -> None:
        """retract_message_id MUST call IG Graph API endpoint."""
        from src.modules.vitalia.connections.instagram.adapter import InstagramAdapter

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"success": True}
            mock_client.delete.return_value = mock_response

            adapter = InstagramAdapter(
                page_id="page123",
                access_token="test-token",
            )
            await adapter.retract_message_id(message_id="ig_msg_XYZ789")

        assert mock_client.delete.called, "retract_message_id must call httpx DELETE"
        call_url = mock_client.delete.call_args[0][0] if mock_client.delete.call_args[0] else ""
        assert "ig_msg_XYZ789" in str(call_url), f"Message ID not in DELETE URL: {call_url}"

    @pytest.mark.asyncio
    async def test_retract_timeout_returns_failed(self) -> None:
        """IG retract timeout → RetractResult(succeeded=False), no raise."""
        from src.modules.vitalia.connections.instagram.adapter import (
            InstagramAdapter,
            RetractResult,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.delete.side_effect = httpx.TimeoutException("timeout", request=MagicMock())

            adapter = InstagramAdapter(
                page_id="page123",
                access_token="test-token",
            )
            result = await adapter.retract_message_id(message_id="ig_msg_abc123")

        assert isinstance(result, RetractResult)
        assert result.succeeded is False

    @pytest.mark.asyncio
    async def test_retract_idempotent_on_404(self) -> None:
        """IG 404 (already deleted) → RetractResult(succeeded=True, idempotent)."""
        from src.modules.vitalia.connections.instagram.adapter import (
            InstagramAdapter,
            RetractResult,
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

            adapter = InstagramAdapter(
                page_id="page123",
                access_token="test-token",
            )
            result = await adapter.retract_message_id(message_id="ig_msg_abc123")

        assert isinstance(result, RetractResult)
        assert result.succeeded is True  # idempotent

    @pytest.mark.asyncio
    async def test_retract_http_500_returns_failed(self) -> None:
        """IG server error → RetractResult(succeeded=False), no raise."""
        from src.modules.vitalia.connections.instagram.adapter import (
            InstagramAdapter,
            RetractResult,
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

            adapter = InstagramAdapter(
                page_id="page123",
                access_token="test-token",
            )
            result = await adapter.retract_message_id(message_id="ig_msg_abc123")

        assert isinstance(result, RetractResult)
        assert result.succeeded is False
