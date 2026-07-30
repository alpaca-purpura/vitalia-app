"""Tests for Email adapter retract_message_id — T-inbox-be-4 (RED first, TDD).

SC-03 edge: Email channel does NOT support real message retraction.
Raises ChannelRetractUnsupportedError (caught by RetractMessageService which
applies "marcar como erróneo" fallback via flag + UI strike-through).

Per `.claude/rules/tdd-mandatory.md`: tests written BEFORE implementation.
"""

from __future__ import annotations

import pytest

# downstream-regression-na: brand-local vitalia connections unit test


class TestEmailAdapterContract:
    """Structural contract — EmailAdapter must expose retract_message_id raising unsupported."""

    def test_adapter_importable(self) -> None:
        """EmailAdapter must be importable."""
        from src.modules.vitalia.connections.email.adapter import (  # noqa: F401
            EmailAdapter,
        )

    def test_adapter_has_retract_method(self) -> None:
        """EmailAdapter must expose async retract_message_id method."""
        from src.modules.vitalia.connections.email.adapter import EmailAdapter

        assert hasattr(EmailAdapter, "retract_message_id"), "EmailAdapter missing retract_message_id"

    def test_channel_retract_unsupported_error_importable(self) -> None:
        """ChannelRetractUnsupportedError must be importable from email adapter."""
        from src.modules.vitalia.connections.email.adapter import (  # noqa: F401
            ChannelRetractUnsupportedError,
        )

    def test_channel_retract_unsupported_error_is_exception(self) -> None:
        """ChannelRetractUnsupportedError must be a subclass of Exception."""
        from src.modules.vitalia.connections.email.adapter import ChannelRetractUnsupportedError

        assert issubclass(ChannelRetractUnsupportedError, Exception)

    def test_unsupported_error_has_message_id(self) -> None:
        """ChannelRetractUnsupportedError should carry message_id for logging."""
        from src.modules.vitalia.connections.email.adapter import ChannelRetractUnsupportedError

        err = ChannelRetractUnsupportedError(message_id="email_msg_001", channel="email")
        assert err.message_id == "email_msg_001"
        assert err.channel == "email"


class TestEmailRetractUnsupported:
    """SC-03 edge case: email retract raises ChannelRetractUnsupportedError."""

    @pytest.mark.asyncio
    async def test_retract_raises_unsupported_error(self) -> None:
        """Email adapter retract_message_id MUST raise ChannelRetractUnsupportedError.

        Per 03-arch-be.md § 6.3: Email channel has no retract API.
        RetractMessageService catches this and applies 'marcar como erróneo' fallback.
        """
        from src.modules.vitalia.connections.email.adapter import (
            ChannelRetractUnsupportedError,
            EmailAdapter,
        )

        adapter = EmailAdapter()
        with pytest.raises(ChannelRetractUnsupportedError) as exc_info:
            await adapter.retract_message_id(message_id="email_msg_abc123")

        assert exc_info.value.message_id == "email_msg_abc123"

    @pytest.mark.asyncio
    async def test_retract_error_carries_channel_name(self) -> None:
        """ChannelRetractUnsupportedError must identify channel='email' for service logging."""
        from src.modules.vitalia.connections.email.adapter import (
            ChannelRetractUnsupportedError,
            EmailAdapter,
        )

        adapter = EmailAdapter()
        with pytest.raises(ChannelRetractUnsupportedError) as exc_info:
            await adapter.retract_message_id(message_id="email_msg_xyz789")

        assert exc_info.value.channel == "email"

    @pytest.mark.asyncio
    async def test_retract_does_not_call_any_external_api(self) -> None:
        """Email retract must NOT make any HTTP calls — it's a pure raise.

        Verifies no httpx or external client is invoked on retract attempt.
        """
        from unittest.mock import patch

        import httpx

        from src.modules.vitalia.connections.email.adapter import (
            ChannelRetractUnsupportedError,
            EmailAdapter,
        )

        with patch.object(httpx, "AsyncClient") as mock_client:
            adapter = EmailAdapter()
            with pytest.raises(ChannelRetractUnsupportedError):
                await adapter.retract_message_id(message_id="email_msg_no_http")

        assert not mock_client.called, "Email retract must NOT instantiate httpx.AsyncClient"

    @pytest.mark.asyncio
    async def test_retract_any_message_id_raises(self) -> None:
        """Any message_id triggers unsupported — it's unconditional for email channel."""
        from src.modules.vitalia.connections.email.adapter import (
            ChannelRetractUnsupportedError,
            EmailAdapter,
        )

        adapter = EmailAdapter()

        for msg_id in ["email_001", "email_uuid-abc", "SOME-EMAIL-MSG-ID"]:
            with pytest.raises(ChannelRetractUnsupportedError):
                await adapter.retract_message_id(message_id=msg_id)
