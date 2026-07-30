# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Instagram Graph API adapter — vitalia connections module.

Provides retract_message_id via Instagram Graph API with:
- DELETE /messages/{id} on Instagram Graph API
- Page access token auth (Bearer)
- 5s timeout per 03-arch-be.md § 6.3 RetractMessageService
- Idempotent: 404 = already deleted = treat as success
- Graceful degradation: timeout/5xx → RetractResult(succeeded=False), no raise

Per `.claude/rules/tdd-mandatory.md`: tests written FIRST (RED).
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import structlog

# downstream-regression-na: brand-local vitalia connections instagram adapter

logger = structlog.get_logger()

_IG_GRAPH_API_VERSION = "v19.0"
_IG_GRAPH_BASE = f"https://graph.facebook.com/{_IG_GRAPH_API_VERSION}"
_RETRACT_TIMEOUT_SECONDS = 5.0


@dataclass
class RetractResult:
    """Result from adapter.retract_message_id().

    succeeded: True if retract succeeded or was already done (404).
    message_id: The message ID that was retracted.
    """

    succeeded: bool
    message_id: str


class InstagramAdapter:
    """Instagram Graph API adapter with retract_message_id support.

    Implements retract via Instagram Graph API DELETE /messages/{id}.
    Idempotent: 404 (already deleted) → RetractResult(succeeded=True).
    Graceful degradation: timeout/5xx → RetractResult(succeeded=False), no raise.

    Usage:
        adapter = InstagramAdapter(page_id="page123", access_token="EAA...")
        result = await adapter.retract_message_id(message_id="ig_msg_abc123")
    """

    def __init__(self, page_id: str, access_token: str) -> None:
        """Initialize InstagramAdapter.

        Args:
            page_id: Instagram/Facebook Page ID.
            access_token: Page access token (Bearer).
        """
        self._page_id = page_id
        self._access_token = access_token

    async def retract_message_id(self, message_id: str) -> RetractResult:
        """Retract an Instagram message via Graph API DELETE.

        Per 03-arch-be.md § 6.3: timeout 5s. Idempotent (404 = success).
        On timeout or server error: returns RetractResult(succeeded=False).

        Args:
            message_id: The Instagram message ID.

        Returns:
            RetractResult with succeeded flag and message_id.
        """
        url = f"{_IG_GRAPH_BASE}/{message_id}"
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
                "instagram_retract_timeout",
                message_id=message_id,
                timeout_seconds=_RETRACT_TIMEOUT_SECONDS,
            )
            return RetractResult(succeeded=False, message_id=message_id)

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code == 404:
                # Already deleted — idempotent success
                logger.info(
                    "instagram_retract_already_deleted",
                    message_id=message_id,
                    status_code=status_code,
                )
                return RetractResult(succeeded=True, message_id=message_id)

            logger.error(
                "instagram_retract_http_error",
                message_id=message_id,
                status_code=status_code,
            )
            return RetractResult(succeeded=False, message_id=message_id)

        except Exception:
            logger.error(
                "instagram_retract_unexpected_error",
                message_id=message_id,
            )
            return RetractResult(succeeded=False, message_id=message_id)

        logger.info(
            "instagram_retract_success",
            message_id=message_id,
        )
        return RetractResult(succeeded=True, message_id=message_id)
