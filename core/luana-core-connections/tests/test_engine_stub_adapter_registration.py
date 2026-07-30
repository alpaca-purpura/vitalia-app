"""Smoke test: connections engine accepts stub adapter registration.

Per 04-validators.yaml V-F-conn-1. Verifies the brand-agnostic contract:
- BaseChannel ABC is importable from luana_core_platform
- A brand-agnostic stub adapter can be defined against the ABC
- The stub adapter passes structural conformance checks
- No brand-specific conditionals needed for registration

This test is independent of any brand vertical — it uses a plain
in-memory StubAdapter that satisfies the BaseChannel interface without
referencing any Nicolify/Vitalia/Comunify/Lupulo specifics.
"""

from __future__ import annotations

from typing import Any

import pytest
from luana_core_platform.domain.messages import IncomingMessage, OutgoingMessage
from luana_core_platform.infrastructure.channels.base import BaseChannel


class StubAdapter(BaseChannel):
    """Minimal brand-agnostic stub implementing the BaseChannel contract.

    Used to verify that the channels engine accepts any conformant adapter
    without requiring brand-specific configuration.
    """

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self.sent: list[str] = []
        self.typing_calls: list[str] = []

    def normalize_payload(self, payload: dict[str, Any]) -> IncomingMessage | None:
        """Return None for empty payloads, IncomingMessage otherwise."""
        if not payload:
            return None
        return IncomingMessage(
            user_id=payload.get("user_id", "anon"),
            text=payload.get("text", ""),
            channel_type="stub",
        )

    async def send_message(self, message: OutgoingMessage) -> dict[str, Any]:
        """Capture sent messages for assertion."""
        self.sent.append(message.text)
        return {"ok": True, "text": message.text}

    async def set_typing_status(self, user_id: str) -> None:
        """Capture typing status calls."""
        self.typing_calls.append(user_id)


class TestStubAdapterRegistration:
    """Verifies the brand-agnostic engine contract via stub adapter."""

    def test_stub_adapter_is_instance_of_base_channel(self):
        """StubAdapter satisfies the BaseChannel ABC structural contract."""
        adapter = StubAdapter(tenant_id="tenant-abc-123")
        assert isinstance(adapter, BaseChannel)

    def test_normalize_payload_returns_none_for_empty(self):
        """normalize_payload returns None when payload should be ignored."""
        adapter = StubAdapter(tenant_id="tenant-abc-123")
        result = adapter.normalize_payload({})
        assert result is None

    def test_normalize_payload_returns_incoming_message(self):
        """normalize_payload returns IncomingMessage for valid payload."""
        adapter = StubAdapter(tenant_id="tenant-abc-123")
        result = adapter.normalize_payload({"user_id": "u1", "text": "hello"})
        assert result is not None
        assert result.user_id == "u1"
        assert result.text == "hello"
        assert result.channel_type == "stub"

    @pytest.mark.asyncio
    async def test_send_message_collects_text(self):
        """send_message captures the outgoing message text."""
        adapter = StubAdapter(tenant_id="tenant-abc-123")
        msg = OutgoingMessage(user_id="u1", text="hola mundo")
        result = await adapter.send_message(msg)
        assert result["ok"] is True
        assert "hola mundo" in adapter.sent

    @pytest.mark.asyncio
    async def test_set_typing_status_records_user(self):
        """set_typing_status records the user ID."""
        adapter = StubAdapter(tenant_id="tenant-abc-123")
        await adapter.set_typing_status("u1")
        assert "u1" in adapter.typing_calls

    @pytest.mark.asyncio
    async def test_send_rich_message_falls_back_to_send_message(self):
        """send_rich_message falls back to send_message (default impl in BaseChannel)."""
        adapter = StubAdapter(tenant_id="tenant-abc-123")
        msg = OutgoingMessage(user_id="u1", text="rich content")
        result = await adapter.send_rich_message(msg)
        # Default fallback calls send_message
        assert "rich content" in adapter.sent
        assert result["ok"] is True

    def test_no_brand_in_adapter(self):
        """Adapter carries tenant_id (multi-tenant) but no brand slug."""
        adapter = StubAdapter(tenant_id="any-tenant-uuid")
        # tenant_id is dynamic, not brand-specific
        assert adapter.tenant_id == "any-tenant-uuid"
        # No brand slug attributes
        assert not hasattr(adapter, "brand_slug")
        assert not hasattr(adapter, "brand_name")
