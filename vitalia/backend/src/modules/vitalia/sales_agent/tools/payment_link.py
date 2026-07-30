# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""Vitalia Adrián sales_agent tool — ``send_payment_link``.

Story T-ag-tools-2 — R23 production_code=true. Opus 4.7 EXCLUSIVE.

Per 03-arch-agentic.md § 4.2 + 02-design-agentic.md § 2.3 + § 2.7.

Semantics:
  Fires the ``PaymentLinkService.send_payment_link`` async pipeline:
    1. ChannelGuard.validate (BlockedChannelError aborts pre-send)
    2. MercadoPago preference creation (timeout 10s + retry 1x backoff 2s)
    3. WhatsApp Business API template send (timeout 10s + queue on 429)
    4. DB write payment_events (idempotency key partial unique)
    5. Sync audit log row (HIPAA-lite mandate)

Tenant + clinic dual filter cardinal (HIPAA-lite overlay).
Channel guard runs BEFORE any external send (compliance gate).

Cost: $0 LLM (network only — adapters cost negligible).
Latency p95: ≤3s (MercadoPago + WhatsApp serial calls).

Anti-duplication audit (Step 0 GATE):
  - ``PaymentLinkService`` consumed via DI — NEVER instantiated in tool
  - ``MedicalResultsChannelGuard`` consumed via service injection — NEVER mirrored
  - Engine has ``send_payment_link`` function-style tool
    (``core/luana-core-sales-agent/.../application/agents/sales/tools.py``)
    BUT vitalia version is a brand-extension wrapping vertical-medical services
    (channel guard pre-check + clinic dual filter + audit log) — distinct
    contract surface, NOT a mirror.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from src.modules.vitalia.sales_agent.application.services.payment_link_service import (
        PaymentLinkService,
    )

logger = structlog.get_logger(__name__)


# ── Pydantic schemas (Pydantic v2) ──────────────────────────────────────


class SendPaymentLinkInput(BaseModel):
    """Input schema — tenant_id + clinic_id mandatory per HIPAA-lite cardinal."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lead_id: UUID = Field(
        ...,
        description="CRM lead UUID receiving the link.",
    )
    appointment_id: UUID = Field(
        ...,
        description="Appointment UUID (used as MP external_reference + idempotency key part 1).",
    )
    deposit_percent: int = Field(
        ...,
        ge=1,
        le=100,
        description="Percentage of total to charge as deposit (idempotency key part 2). Default 30 per offer.",
    )
    channel: str = Field(
        ...,
        description="Channel slug (validated by channel_guard before send). e.g. 'whatsapp_business_encrypted'.",
    )
    tenant_id: UUID = Field(
        ...,
        description="Tenant UUID (root isolation — dual filter).",
    )
    clinic_id: UUID = Field(
        ...,
        description="Clinic UUID (HIPAA-lite dual filter).",
    )
    amount: float = Field(
        0.0,
        ge=0.0,
        description="Total appointment amount in tenant currency (caller pre-computes).",
    )
    to_phone: str = Field(
        "",
        description="Lead phone in E.164 format for WhatsApp send. Empty string skips WA dispatch.",
    )
    currency: str = Field(
        "ARS",
        description="ISO 4217 currency code (read from offer config — NEVER hardcoded by tool).",
    )
    template_name: str = Field(
        "vitalia_deposit_link",
        description="Approved WhatsApp HSM template name.",
    )
    user_id: UUID | None = Field(
        None,
        description="Operator UUID for audit log attribution. Defaults to lead_id when None.",
    )


# ── Service resolver (DI hook) ──────────────────────────────────────────

_service_resolver: Any = None  # callable returning PaymentLinkService


def set_payment_link_service_resolver(resolver: Any) -> None:
    """Wire the service resolver at orchestrator init.

    Resolver signature: ``() -> PaymentLinkService``. Called at tool
    invocation time so the service is built within the active request scope.
    """
    global _service_resolver  # noqa: PLW0603 — DI bootstrap hook
    _service_resolver = resolver


def _get_service() -> PaymentLinkService:
    if _service_resolver is None:
        raise RuntimeError(
            "send_payment_link tool: service resolver not configured. "
            "Call set_payment_link_service_resolver(...) during orchestrator init."
        )
    return _service_resolver()


# ── Tool ────────────────────────────────────────────────────────────────


@tool("send_payment_link", args_schema=SendPaymentLinkInput)
async def send_payment_link(
    lead_id: UUID,
    appointment_id: UUID,
    deposit_percent: int,
    channel: str,
    tenant_id: UUID,
    clinic_id: UUID,
    amount: float = 0.0,
    to_phone: str = "",
    currency: str = "ARS",
    template_name: str = "vitalia_deposit_link",
    user_id: UUID | None = None,
) -> str:
    """Create and dispatch a MercadoPago deposit payment link.

    Channel guard runs BEFORE any send. If the channel is blocked (e.g.
    WhatsApp free + PHI), returns a portal-redirect message instead.

    Returns:
        Spanish summary suitable for LLM consumption with checkout URL +
        confirmation status. On graceful-degradation paths, returns the
        derive-to-portal message.
    """
    service = _get_service()
    effective_user_id = user_id or lead_id

    try:
        result = await service.send_payment_link(
            lead_id=lead_id,
            appointment_id=appointment_id,
            deposit_percent=deposit_percent,
            channel=channel,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=effective_user_id,
            amount=amount,
            to_phone=to_phone,
            currency=currency,
            template_name=template_name,
        )
    except Exception as exc:  # noqa: BLE001
        # Channel guard raises BlockedChannelError — message already includes
        # the portal-redirect Spanish neutral text.
        if exc.__class__.__name__ == "BlockedChannelError":
            return f"Canal '{channel}' bloqueado por seguridad. Te paso el link por un canal autorizado. {exc}"
        logger.warning(
            "vitalia.sales_agent.tools.send_payment_link.failed",
            error=str(exc),
            lead_id=str(lead_id),
            appointment_id=str(appointment_id),
        )
        return (
            "Hay un problema técnico con el sistema de pagos. El equipo te va a contactar en breve con el link manual."
        )

    return (
        f"Link de pago enviado para turno {appointment_id} "
        f"(deposit {deposit_percent}%, canal {result.channel}). "
        f"Checkout URL: {result.init_point}. Preference ID: {result.preference_id}."
    )


__all__ = [
    "SendPaymentLinkInput",
    "send_payment_link",
    "set_payment_link_service_resolver",
]
