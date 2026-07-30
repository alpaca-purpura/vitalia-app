# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""WhatsApp Business API adapter for Vitalia Adrián sales_agent.

Sends approved template messages via WhatsApp Cloud API.
Retract API is a Slice 2 placeholder (raises NotImplementedError).

Per 03-arch-be.md § 1 + 06-tickets.yaml T-be-services-2:
  - send_template_message(phone, template_name, params) → bool
  - retract_last_message() → NotImplementedError (Slice 2)

HIPAA-lite: NEVER send PHI via WhatsApp free tier.
Channel guard (VitaliaComplianceAdapter) MUST be called BEFORE this adapter.

Per tessl__graceful-degradation: 10s timeout + fallback log on 4xx template error.

downstream-regression-na: brand-local WhatsApp adapter for vitalia
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

logger = structlog.get_logger()

_TIMEOUT_SECONDS = 10


class WhatsAppBusinessAdapter:
    """Async adapter for WhatsApp Business Cloud API.

    Sends pre-approved template messages (HSM) to leads.
    Templates must be approved in the Meta Business Manager before use.

    CRITICAL: This adapter ASSUMES the caller (PaymentLinkService) has
    already validated the channel via VitaliaComplianceAdapter. Never
    call this directly without the channel guard check.
    """

    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        api_version: str = "v18.0",
    ) -> None:
        """Initialize with WhatsApp Business credentials.

        Args:
            phone_number_id: Meta WhatsApp Phone Number ID.
            access_token: Meta System User token with whatsapp_business_messages permission.
            api_version: Meta Graph API version.
        """
        self._phone_number_id = phone_number_id
        self._access_token = access_token
        self._base_url = f"https://graph.facebook.com/{api_version}"

    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        template_params: list[str] | None = None,
        language_code: str = "es_AR",
    ) -> bool:
        """Send an approved WhatsApp template message.

        Args:
            to_phone: Recipient phone number in E.164 format (+54...).
            template_name: Name of the approved Meta HSM template.
            template_params: List of parameter values to fill template slots.
            language_code: BCP-47 language code matching the template.

        Returns:
            True if the message was accepted by the WhatsApp API.

        Raises:
            RuntimeError: On API failure after timeout.
        """
        components: list[dict[str, Any]] = []
        if template_params:
            components.append(
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in template_params],
                }
            )

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components,
            },
        }

        logger.info(
            "whatsapp.send_template_message.start",
            to=to_phone[-4:] + "****",  # Last 4 digits only — no PHI in logs
            template=template_name,
        )

        try:
            async with asyncio.timeout(_TIMEOUT_SECONDS):
                result = await self._post_message(payload)
            logger.info(
                "whatsapp.send_template_message.ok",
                template=template_name,
                message_id=result.get("messages", [{}])[0].get("id"),
            )
            return True
        except asyncio.TimeoutError:
            logger.error(
                "whatsapp.send_template_message.timeout",
                template=template_name,
            )
            raise RuntimeError(f"WhatsApp API timeout sending template '{template_name}'")
        except Exception as exc:
            logger.error(
                "whatsapp.send_template_message.error",
                template=template_name,
                error=str(exc),
            )
            raise

    async def retract_last_message(self, message_id: str) -> None:
        """Retract (delete) a sent WhatsApp message. Slice 2 — NOT YET IMPLEMENTED.

        Args:
            message_id: The wamid of the message to retract.

        Raises:
            NotImplementedError: Always raised — retract is Slice 2 scope.
        """
        raise NotImplementedError(
            "WhatsApp message retraction is a Slice 2 feature. "
            "Per 06-tickets.yaml T-be-services-2: "
            "'retract API placeholder for Slice 2'. "
            "Escalate to /pm-vitalia if retraction is urgently needed."
        )

    async def _post_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send authenticated POST to WhatsApp Cloud API."""
        import httpx  # noqa: PLC0415

        url = f"{self._base_url}/{self._phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
