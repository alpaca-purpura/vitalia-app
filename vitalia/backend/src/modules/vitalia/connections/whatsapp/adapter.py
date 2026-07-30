# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""WhatsApp Cloud API adapter — vitalia connections module.

Provides retract_message_id via Meta Graph API with:
- DELETE /messages/{id} on Meta Graph API
- Bearer token auth
- 5s timeout per 03-arch-be.md § 6.3 RetractMessageService
- Idempotent: 404 = already deleted = treat as success
- Graceful degradation: timeout/5xx → RetractResult(succeeded=False), no raise

Per `.claude/rules/tdd-mandatory.md`: tests written FIRST (RED).
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import structlog

# downstream-regression-na: brand-local vitalia connections whatsapp adapter

logger = structlog.get_logger()

_META_GRAPH_API_VERSION = "v19.0"
_META_GRAPH_BASE = f"https://graph.facebook.com/{_META_GRAPH_API_VERSION}"
_RETRACT_TIMEOUT_SECONDS = 5.0


@dataclass
class RetractResult:
    """Result from adapter.retract_message_id().

    succeeded: True if retract succeeded or was already done (404).
    message_id: The message ID that was retracted.
    """

    succeeded: bool
    message_id: str


class WhatsAppAdapter:
    """WhatsApp Cloud API adapter with retract_message_id support.

    Implements retract via Meta Graph API DELETE /messages/{id}.
    Idempotent: 404 (already deleted) → RetractResult(succeeded=True).
    Graceful degradation: timeout/5xx → RetractResult(succeeded=False), no raise.

    Usage:
        adapter = WhatsAppAdapter(phone_number_id="123456789", access_token="EAA...")
        result = await adapter.retract_message_id(message_id="wamid.abc123")
    """

    def __init__(self, phone_number_id: str, access_token: str) -> None:
        """Initialize WhatsAppAdapter.

        Args:
            phone_number_id: WhatsApp Business phone number ID.
            access_token: Meta Graph API access token (Bearer).
        """
        self._phone_number_id = phone_number_id
        self._access_token = access_token

    async def retract_message_id(self, message_id: str) -> RetractResult:
        """Retract a WhatsApp message via Meta Graph API DELETE.

        Per 03-arch-be.md § 6.3: timeout 5s. Idempotent (404 = success).
        On timeout or server error: returns RetractResult(succeeded=False).

        Args:
            message_id: The WhatsApp message ID (wamid.*).

        Returns:
            RetractResult with succeeded flag and message_id.
        """
        url = f"{_META_GRAPH_BASE}/{message_id}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    url,
                    headers=headers,
                    timeout=_RETRACT_TIMEOUT_SECONDS,
                )
                response.raise_for_status()

        except httpx.TimeoutException:
            logger.warning(
                "whatsapp_retract_timeout",
                message_id=message_id,
                timeout_seconds=_RETRACT_TIMEOUT_SECONDS,
            )
            return RetractResult(succeeded=False, message_id=message_id)

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code == 404:
                # Already deleted — idempotent success
                logger.info(
                    "whatsapp_retract_already_deleted",
                    message_id=message_id,
                    status_code=status_code,
                )
                return RetractResult(succeeded=True, message_id=message_id)

            logger.error(
                "whatsapp_retract_http_error",
                message_id=message_id,
                status_code=status_code,
            )
            return RetractResult(succeeded=False, message_id=message_id)

        except Exception:
            logger.error(
                "whatsapp_retract_unexpected_error",
                message_id=message_id,
            )
            return RetractResult(succeeded=False, message_id=message_id)

        logger.info(
            "whatsapp_retract_success",
            message_id=message_id,
        )
        return RetractResult(succeeded=True, message_id=message_id)
