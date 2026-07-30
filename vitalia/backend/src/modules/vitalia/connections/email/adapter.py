# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Email adapter — vitalia connections module.

Email channel does NOT support real message retraction.
RetractMessageService (T-inbox-be-3) catches ChannelRetractUnsupportedError
and applies 'marcar como erróneo' fallback:
- Sets message.retract_succeeded = False
- UI renders the message with strike-through

Per `.claude/rules/tdd-mandatory.md`: tests written FIRST (RED).
"""

from __future__ import annotations

import structlog

# downstream-regression-na: brand-local vitalia connections email adapter

logger = structlog.get_logger()


class ChannelRetractUnsupportedError(Exception):
    """Raised when a channel does not support message retraction.

    Caught by RetractMessageService to apply channel-specific fallback
    (e.g., 'marcar como erróneo' for email channel).

    Attributes:
        message_id: The message ID that retraction was attempted for.
        channel: The channel name that does not support retraction.
    """

    def __init__(self, message_id: str, channel: str) -> None:
        """Initialize ChannelRetractUnsupportedError.

        Args:
            message_id: The message ID that retraction was attempted for.
            channel: The channel name (e.g., 'email').
        """
        self.message_id = message_id
        self.channel = channel
        super().__init__(
            f"Channel '{channel}' does not support message retraction "
            f"(message_id={message_id}). "
            f"Caller should apply channel-specific fallback."
        )


class EmailAdapter:
    """Email channel adapter.

    Email does NOT support real-time message retraction (emails cannot be
    recalled once delivered). RetractMessageService catches the raised
    ChannelRetractUnsupportedError and applies the 'marcar como erróneo'
    fallback: flag the message + UI shows strike-through.

    Usage:
        adapter = EmailAdapter()
        try:
            await adapter.retract_message_id(message_id="email_msg_abc")
        except ChannelRetractUnsupportedError:
            # apply fallback (RetractMessageService handles this)
            ...
    """

    async def retract_message_id(self, message_id: str) -> None:
        """Attempt to retract an email message — raises ChannelRetractUnsupportedError.

        Email channel has no retract API. This method ALWAYS raises.
        RetractMessageService (T-inbox-be-3) catches and applies fallback.

        Args:
            message_id: The email message ID.

        Raises:
            ChannelRetractUnsupportedError: Always raised for email channel.
        """
        logger.info(
            "email_retract_unsupported",
            message_id=message_id,
            channel="email",
            fallback="marcar_como_erroneo",
        )
        raise ChannelRetractUnsupportedError(message_id=message_id, channel="email")
