# cap: scheduling.mateo-agenda
# story-origin: vitalia-fase2-s1-TBD
"""Notify Service — template-only WhatsApp notification with ComplianceService guard.

Rule (hipaa-lite.md + 03-arch § 5):
  - Template-only: only pre-approved template_id values allowed (no free text).
    Free text risks PHI leakage in channel body.
  - ComplianceService.validate_outbound_message guard runs BEFORE dispatch.
    BlockedChannelError → NotificationBlockedError (audit log still written).
  - Audit log sync write with template_id + channel (NO message body in payload).
  - Cross-clinic: repo returns None → AppointmentNotFoundError (404).
  - Even on block/404, audit log is written (suspicious access pattern).

Usage:
    service = NotifyService(
        repo=repo,
        audit_writer=audit_writer,
        compliance_service=compliance_service,
    )
    result = await service.send_notification(
        appointment_id=appt_id,
        tenant_id=tenant_id,
        clinic_id=clinic_id,
        user_id=user_id,
        template_id="recordatorio_cita_1d",
        channel="whatsapp",
    )
"""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

import structlog

from src.modules.vitalia.scheduling.domain.exceptions import (
    AppointmentNotFoundError,
    FreeTextNotificationError,
    NotificationBlockedError,
)

logger = structlog.get_logger()


class NotifyService:
    """Application service: send template-only WhatsApp notification.

    Thin orchestration:
    1. Validate template_id non-empty (template-only gate).
    2. Load appointment (dual filter tenant_id + clinic_id).
    3. ComplianceService.validate_outbound_message (PHI channel guard).
    4. Audit log sync write (template_id + channel, NO body).
    5. Dispatch to channel adapter (stub in F2-S1 — no real WhatsApp connection).
    6. Return {status: "sent"}.

    PHI obligations (hipaa-lite.md):
    - Dual filter via repo.get_by_id (tenant_id + clinic_id WHERE clause).
    - Audit log written sync on every call — including on block/404.
    - No PHI in audit payload (only template_id reference, not the rendered body).
    - ComplianceService guard on every call (no bypass).
    """

    def __init__(
        self,
        *,
        repo: Any,
        audit_writer: Any,
        compliance_service: Any,
    ) -> None:
        """Initialize NotifyService.

        Args:
            repo: Implements get_by_id(appt_id, tenant_id, clinic_id) -> dict | None.
            audit_writer: AsyncAuditWriter — sync write before response.
            compliance_service: VitaliaComplianceAdapter (or mock). Calls
                validate_outbound_message(template_content, channel). May be
                sync or async — service handles both via _call_compliance().
        """
        self._repo = repo
        self._audit = audit_writer
        self._compliance = compliance_service

    async def send_notification(
        self,
        *,
        appointment_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        template_id: str,
        channel: str,
    ) -> dict[str, Any]:
        """Send a template-only notification for an appointment.

        Args:
            appointment_id: Target appointment UUID.
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID for dual filter.
            user_id: Actor user UUID.
            template_id: Pre-approved template identifier (non-empty, max 64 chars).
                Must NOT be empty — free-text prohibition.
            channel: Channel identifier (e.g. 'whatsapp', 'portal_secure').

        Returns:
            Dict with {"status": "sent"}.

        Raises:
            FreeTextNotificationError: If template_id is empty.
            AppointmentNotFoundError: If appointment not found for this tenant+clinic.
            NotificationBlockedError: If compliance guard blocks the channel.
        """
        # Gate 1: template-only enforcement (before any async ops)
        if not template_id or not template_id.strip():
            raise FreeTextNotificationError(
                "template_id is required. Free-text notifications are prohibited per HIPAA-lite."
            )

        # Load appointment via dual filter (raises on cross-clinic)
        appointment = await self._repo.get_by_id(
            appointment_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        if appointment is None:
            # Audit the 404 (suspicious cross-clinic access attempt)
            await self._audit.write(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="appointment.notify_cross_clinic_attempt",
                resource_type="appointment",
                resource_id=appointment_id,
                payload={
                    "template_id": template_id,
                    "channel": channel,
                    "found": False,
                },
            )
            raise AppointmentNotFoundError(
                appointment_id=appointment_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
            )

        # Gate 2: ComplianceService PHI channel guard
        # The template content is a placeholder here (F2-S1 stub — no template catalog yet)
        # In production, resolve template_id → content then validate_outbound_message(content, channel)
        template_content_placeholder = f"[template:{template_id}]"
        blocked = False
        block_reason = ""

        try:
            result = self._compliance.validate_outbound_message(template_content_placeholder, channel)
            # Handle both sync (bool) and async (awaitable) implementations
            if asyncio.iscoroutine(result):
                await result

        except Exception as exc:
            # Compliance blocked (BlockedChannelError or similar)
            blocked = True
            block_reason = str(exc)

        # Audit log sync write (HIPAA mandate — every notification attempt is logged)
        await self._audit.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="appointment.send_notification",
            resource_type="appointment",
            resource_id=appointment_id,
            payload={
                "template_id": template_id,  # safe to log (key reference, not PHI body)
                "channel": channel,
                "blocked": blocked,
                "block_reason": block_reason if blocked else None,
            },
        )

        if blocked:
            raise NotificationBlockedError(
                appointment_id=appointment_id,
                reason=block_reason or "compliance guard blocked outbound channel",
            )

        # F2-S1 stub: actual WhatsApp dispatch lives in vitalia-channels-integration story
        # When that story ships, this is where we call the channel adapter.
        logger.info(
            "appointment_notification_sent",
            appointment_id=str(appointment_id),
            tenant_id=str(tenant_id),
            template_id=template_id,
            channel=channel,
        )

        return {"status": "sent", "template_id": template_id, "channel": channel}
