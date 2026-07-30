# cap: adrian.inbox
"""Vitalia brand-local Telegram adapter — T-BE-1.

Thin wrapper around the engine's TelegramChannel (luana_core_connections).
Implements the BaseChannel ABC contract for use within the vitalia brand module.

The engine's ChatOrchestrator.handle_telegram_webhook already creates its own
adapter via create_telegram_adapter(). This brand-local adapter is used for
structural contract testing and direct normalize_payload calls when needed.

Per anti-duplication.md: this is a THIN shim — does NOT reimplement TelegramChannel
logic; delegates to luana_core_connections.infrastructure.channels.telegram.TelegramChannel.

Per hipaa-lite.md: Telegram update payloads are NOT PHI (no clinical data).
"""

from __future__ import annotations

from typing import Any

import structlog
from luana_core_platform.domain.messages import IncomingMessage, OutgoingMessage
from luana_core_platform.infrastructure.channels.base import BaseChannel

# downstream-regression-na: brand-local vitalia connections telegram adapter

logger = structlog.get_logger()


class TelegramAdapter(BaseChannel):
    """Vitalia brand-local Telegram adapter implementing BaseChannel.

    Delegates normalize_payload and send_message to the engine's TelegramChannel
    to avoid cross-brand mirror (anti-duplication.md). Used for:
    - Structural contract testing (arch tests verify BaseChannel compliance)
    - Direct normalize_payload calls in the webhook route

    The engine's handle_telegram_webhook creates its own adapter via
    create_telegram_adapter(); this adapter mirrors the same contract.
    """

    def __init__(self, token: str | None = None) -> None:
        """Initialize TelegramAdapter.

        Args:
            token: Per-tenant Telegram bot token. Falls back to engine settings
                   (TELEGRAM_BOT_TOKEN env) if not provided (legacy/global mode).
        """
        # Lazy import to avoid loading luana_core_connections at module level
        # (graceful degradation if the package is not installed in test env)
        try:
            from luana_core_connections.infrastructure.channels.telegram import TelegramChannel  # noqa: PLC0415

            self._delegate = TelegramChannel(token=token)
        except ImportError:
            logger.warning(
                "luana_core_connections not available — TelegramAdapter in stub mode",
                token_provided=token is not None,
            )
            self._delegate = None
        self._token = token

    def normalize_payload(self, payload: dict[str, Any]) -> IncomingMessage | None:
        """Convert raw Telegram webhook update to unified IncomingMessage.

        Returns None if the payload should be ignored (non-text messages,
        channel posts, edited messages, etc.).

        Per TelegramChannel engine implementation:
          - Only text messages from `.message` key are processed.
          - Extracts user_id from `message.from.id` (str).
          - Metadata: first_name, last_name, username, language_code, source='telegram'.
        """
        if self._delegate is not None:
            return self._delegate.normalize_payload(payload)

        # Fallback (stub mode — test env without luana_core_connections)
        message = payload.get("message")
        if not message or "text" not in message:
            return None

        user_data = message.get("from", {})
        user_id = str(user_data.get("id", ""))
        text = message.get("text", "")

        metadata: dict[str, Any] = {
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "username": user_data.get("username", ""),
            "language_code": user_data.get("language_code", ""),
            "source": "telegram",
        }

        return IncomingMessage(
            user_id=user_id,
            text=text,
            channel_type="telegram",
            metadata=metadata,
        )

    async def send_message(self, message: OutgoingMessage) -> dict[str, Any]:
        """Send outgoing message via Telegram Bot API.

        Delegates to engine's TelegramChannel.send_message.
        Graceful degradation: returns error dict if delegate unavailable.
        """
        if self._delegate is not None:
            return await self._delegate.send_message(message)

        logger.error(
            "telegram_send_message_unavailable",
            user_id=message.user_id,
        )
        return {"error": "telegram_adapter_not_available"}

    async def set_typing_status(self, user_id: str) -> None:
        """Send 'typing...' action to Telegram chat.

        Graceful degradation: logs warning if delegate unavailable.
        """
        if self._delegate is not None:
            await self._delegate.set_typing_status(user_id)
            return

        logger.warning(
            "telegram_typing_status_unavailable",
            user_id=user_id,
        )
