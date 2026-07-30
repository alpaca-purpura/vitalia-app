# cap: adrian.inbox
"""Pydantic v2 DTOs for the Telegram inbound webhook — T-BE-1.

Per pii-sanitisation.md: response_model= whitelist enforced on every route.
TelegramWebhookAck is the sole response DTO — contains no PHI.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TelegramWebhookAck(BaseModel):
    """Acknowledgement response for Telegram webhook receiver.

    Telegram convention: always return 200 with ok=True to prevent retry storms.
    Internal discard (invalid secret / dedup) is handled before dispatch; the
    response is always the same to avoid leaking auth signals to Telegram servers.

    Per V-NF-4: response_model= mandatory on every route (PII gate).
    """

    model_config = ConfigDict(from_attributes=True)

    ok: bool
