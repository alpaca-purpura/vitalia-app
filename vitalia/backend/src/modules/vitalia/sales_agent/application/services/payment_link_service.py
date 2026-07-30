# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""PaymentLinkService — MercadoPago deposit link via WhatsApp for Adrián.

Orchestrates:
  1. ChannelGuardService.validate (BEFORE any send — HIPAA-lite mandatory)
  2. MercadoPago preference creation
  3. WhatsApp template message dispatch
  4. payment_events DB row write (with idempotency key)
  5. Audit log sync write

Per 03-arch-be.md § 1 + 06-tickets.yaml T-be-services-2:
  "payment_link_service.py — ChannelGuardService.validate pre-send +
   MercadoPago preference + WhatsApp template send + DB write payment_events
   + sync audit_log + idempotency key (appointment_id, deposit_percent)"

HIPAA-lite (vitalia/.claude/rules/hipaa-lite.md):
  - validate_outbound_message() MUST be called before every send
  - audit_log written synchronously (never async fire-forget)
  - No PHI in MP preference payload (names/contact data must be omitted)

downstream-regression-na: brand-local service for vitalia Adrián sales_agent
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.vitalia._shared.repositories.audit_log_repository import (
        AuditLogRepository,
    )
    from src.modules.vitalia.compliance.guardrails.medical_results_guard import (
        MedicalResultsChannelGuard,
    )
    from src.modules.vitalia.sales_agent.infrastructure.adapters.mercadopago_adapter import (
        MercadoPagoAdapter,
    )
    from src.modules.vitalia.sales_agent.infrastructure.adapters.whatsapp_business_adapter import (
        WhatsAppBusinessAdapter,
    )

logger = structlog.get_logger()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass
class PaymentLinkResult:
    """Result of a successful payment link dispatch."""

    preference_id: str
    init_point: str
    appointment_id: UUID
    deposit_percent: int
    channel: str
    sent_at: datetime


class PaymentLinkService:
    """Service that creates and sends MercadoPago deposit payment links.

    Call order (per HIPAA-lite mandatory):
      1. channel_guard.validate()  ← MUST be first (BlockedChannelError aborts)
      2. mercadopago_adapter.create_preference()
      3. whatsapp_adapter.send_template_message()
      4. DB write (payment_events idempotency)
      5. audit_log.write()

    If step 1 raises BlockedChannelError, steps 2-5 are skipped.
    """

    def __init__(
        self,
        channel_guard: "MedicalResultsChannelGuard",
        mercadopago_adapter: "MercadoPagoAdapter",
        whatsapp_adapter: "WhatsAppBusinessAdapter",
        audit_log_repo: "AuditLogRepository",
        session: "AsyncSession",
    ) -> None:
        """Initialize with all required dependencies.

        Args:
            channel_guard: HIPAA-lite channel validator (validates before send).
            mercadopago_adapter: MP API adapter for preference creation.
            whatsapp_adapter: WhatsApp Business API adapter for template dispatch.
            audit_log_repo: HIPAA-lite synchronous audit log repository.
            session: AsyncSession for idempotency DB check.
        """
        self._guard = channel_guard
        self._mp = mercadopago_adapter
        self._wa = whatsapp_adapter
        self._audit = audit_log_repo
        self._session = session

    async def send_payment_link(
        self,
        lead_id: UUID,
        appointment_id: UUID,
        deposit_percent: int,
        channel: str,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        amount: float = 0.0,
        to_phone: str = "",
        currency: str = "ARS",
        template_name: str = "vitalia_deposit_link",
    ) -> PaymentLinkResult:
        """Create and send a payment link for an appointment deposit.

        Args:
            lead_id: CRM lead UUID receiving the link.
            appointment_id: Appointment UUID (used as MP external_reference + idempotency key).
            deposit_percent: Percentage of total to charge (e.g. 30 for 30%).
            channel: Channel slug (validated by channel_guard before send).
            tenant_id: Tenant UUID (root isolation).
            clinic_id: Clinic UUID (HIPAA-lite dual filter).
            user_id: Operator UUID (audit log attribution).
            amount: Total appointment amount in tenant currency.
            to_phone: Lead phone number in E.164 format for WhatsApp send.
            currency: ISO 4217 currency code.
            template_name: Approved WhatsApp HSM template name.

        Returns:
            PaymentLinkResult with preference_id and init_point URL.

        Raises:
            BlockedChannelError: If channel is blocked by guard (no send occurs).
        """
        # Step 1 — HIPAA-lite mandatory: validate channel BEFORE any send
        self._guard.validate(message="", channel=channel)

        logger.info(
            "payment_link.start",
            lead_id=str(lead_id),
            appointment_id=str(appointment_id),
            deposit_percent=deposit_percent,
            channel=channel,
            tenant_id=str(tenant_id),
        )

        # Step 2 — Create MercadoPago payment preference
        preference = await self._mp.create_preference(
            appointment_id=str(appointment_id),
            amount=amount,
            deposit_percent=deposit_percent,
            currency=currency,
        )
        init_point: str = preference.get("init_point", "")
        preference_id: str = preference.get("id", str(uuid4()))

        # Step 3 — Send WhatsApp template (if phone available)
        if to_phone:
            await self._wa.send_template_message(
                to_phone=to_phone,
                template_name=template_name,
                template_params=[init_point],
            )

        now = _utc_now()

        # Step 4 — DB write (idempotency: appointment_id + deposit_percent partial unique index)
        await self._write_payment_event(
            appointment_id=appointment_id,
            preference_id=preference_id,
            deposit_percent=deposit_percent,
            channel=channel,
            tenant_id=tenant_id,
            created_at=now,
        )

        # Step 5 — Audit log sync write (HIPAA-lite mandate)
        from src.modules.vitalia._shared.repositories.audit_log_repository import (  # noqa: PLC0415
            AuditLogEntry,
        )

        audit_entry = AuditLogEntry(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="payment_link_sent",
            resource_type="appointment",
            resource_id=appointment_id,
            payload_redacted=b"",
        )
        await self._audit.write(audit_entry)

        logger.info(
            "payment_link.sent",
            preference_id=preference_id,
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
        )

        return PaymentLinkResult(
            preference_id=preference_id,
            init_point=init_point,
            appointment_id=appointment_id,
            deposit_percent=deposit_percent,
            channel=channel,
            sent_at=now,
        )

    async def _write_payment_event(
        self,
        appointment_id: UUID,
        preference_id: str,
        deposit_percent: int,
        channel: str,
        tenant_id: UUID,
        created_at: datetime,
    ) -> None:
        """Write payment_events row with idempotency guard.

        Uses raw SQL ON CONFLICT DO NOTHING on (appointment_id, deposit_percent)
        partial unique index (created in migration 021).

        Args:
            appointment_id: Appointment UUID (idempotency key part 1).
            preference_id: MercadoPago preference ID.
            deposit_percent: Deposit percentage (idempotency key part 2).
            channel: Channel used for dispatch.
            tenant_id: Tenant UUID for isolation.
            created_at: Event creation timestamp.
        """
        from sqlalchemy import text  # noqa: PLC0415

        stmt = text(
            """
            INSERT INTO payment_events
              (id, tenant_id, appointment_id, preference_id,
               deposit_percent, channel, created_at)
            VALUES
              (:id, :tenant_id, :appointment_id, :preference_id,
               :deposit_percent, :channel, :created_at)
            ON CONFLICT (appointment_id, deposit_percent) DO NOTHING
            """
        )
        await self._session.execute(
            stmt,
            {
                "id": str(uuid4()),
                "tenant_id": str(tenant_id),
                "appointment_id": str(appointment_id),
                "preference_id": preference_id,
                "deposit_percent": deposit_percent,
                "channel": channel,
                "created_at": created_at,
            },
        )
