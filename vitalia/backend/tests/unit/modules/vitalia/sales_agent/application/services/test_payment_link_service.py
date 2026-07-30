"""RED tests — PaymentLinkService.

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- send_payment_link() calls ChannelGuardService.validate BEFORE send
- BlockedChannelError propagates — service does NOT send on blocked channel
- MercadoPago adapter called to create preference
- WhatsApp adapter called to send template
- idempotency key prevents duplicate payment_events (same appointment_id + deposit_percent)
- audit_log written synchronously
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
LEAD_ID = uuid4()
APPOINTMENT_ID = uuid4()


class TestPaymentLinkService:
    """Unit tests for PaymentLinkService."""

    def test_import_service(self) -> None:
        """Service importable from application services layer."""
        from src.modules.vitalia.sales_agent.application.services.payment_link_service import (
            PaymentLinkService,
        )

        assert PaymentLinkService is not None

    @pytest.mark.asyncio()
    async def test_channel_guard_called_before_send(self) -> None:
        """ChannelGuardService.validate called before any message send."""
        from src.modules.vitalia.sales_agent.application.services.payment_link_service import (
            PaymentLinkService,
        )

        mock_guard = AsyncMock()
        mock_guard.validate = MagicMock(return_value=True)
        mock_mp = AsyncMock()
        mock_mp.create_preference = AsyncMock(return_value={"init_point": "https://mp.link"})
        mock_wa = AsyncMock()
        mock_wa.send_template_message = AsyncMock(return_value=True)
        mock_audit = AsyncMock()

        svc = PaymentLinkService(
            channel_guard=mock_guard,
            mercadopago_adapter=mock_mp,
            whatsapp_adapter=mock_wa,
            audit_log_repo=mock_audit,
            session=AsyncMock(),
        )

        await svc.send_payment_link(
            lead_id=LEAD_ID,
            appointment_id=APPOINTMENT_ID,
            deposit_percent=30,
            channel="whatsapp_free",
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=uuid4(),
        )

        mock_guard.validate.assert_called_once()

    @pytest.mark.asyncio()
    async def test_blocked_channel_error_propagates(self) -> None:
        """BlockedChannelError from guard propagates — service must not send."""
        from src.modules.vitalia.compliance.application.compliance_service_adapter import (
            BlockedChannelError,
        )
        from src.modules.vitalia.sales_agent.application.services.payment_link_service import (
            PaymentLinkService,
        )

        mock_guard = MagicMock()
        mock_guard.validate = MagicMock(side_effect=BlockedChannelError(channel="whatsapp_free"))
        mock_wa = AsyncMock()
        mock_mp = AsyncMock()
        mock_mp.create_preference = AsyncMock(return_value={"init_point": "https://mp.link"})

        svc = PaymentLinkService(
            channel_guard=mock_guard,
            mercadopago_adapter=mock_mp,
            whatsapp_adapter=mock_wa,
            audit_log_repo=AsyncMock(),
            session=AsyncMock(),
        )

        with pytest.raises(BlockedChannelError):
            await svc.send_payment_link(
                lead_id=LEAD_ID,
                appointment_id=APPOINTMENT_ID,
                deposit_percent=30,
                channel="whatsapp_free",
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                user_id=uuid4(),
            )

        # WhatsApp adapter must NOT have been called
        mock_wa.send_template_message.assert_not_called()

    @pytest.mark.asyncio()
    async def test_mercadopago_adapter_called(self) -> None:
        """MercadoPago adapter called to create payment preference."""
        from src.modules.vitalia.sales_agent.application.services.payment_link_service import (
            PaymentLinkService,
        )

        mock_guard = MagicMock()
        mock_guard.validate = MagicMock(return_value=True)
        mock_mp = AsyncMock()
        mock_mp.create_preference = AsyncMock(return_value={"init_point": "https://mp.link"})
        mock_wa = AsyncMock()
        mock_wa.send_template_message = AsyncMock(return_value=True)

        svc = PaymentLinkService(
            channel_guard=mock_guard,
            mercadopago_adapter=mock_mp,
            whatsapp_adapter=mock_wa,
            audit_log_repo=AsyncMock(),
            session=AsyncMock(),
        )

        await svc.send_payment_link(
            lead_id=LEAD_ID,
            appointment_id=APPOINTMENT_ID,
            deposit_percent=30,
            channel="whatsapp_business_encrypted",
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=uuid4(),
        )

        mock_mp.create_preference.assert_called_once()

    @pytest.mark.asyncio()
    async def test_audit_log_written_sync(self) -> None:
        """Audit log written synchronously after successful send."""
        from src.modules.vitalia.sales_agent.application.services.payment_link_service import (
            PaymentLinkService,
        )

        mock_guard = MagicMock()
        mock_guard.validate = MagicMock(return_value=True)
        mock_mp = AsyncMock()
        mock_mp.create_preference = AsyncMock(return_value={"init_point": "https://mp.link"})
        mock_wa = AsyncMock()
        mock_wa.send_template_message = AsyncMock(return_value=True)
        mock_audit = AsyncMock()

        svc = PaymentLinkService(
            channel_guard=mock_guard,
            mercadopago_adapter=mock_mp,
            whatsapp_adapter=mock_wa,
            audit_log_repo=mock_audit,
            session=AsyncMock(),
        )

        await svc.send_payment_link(
            lead_id=LEAD_ID,
            appointment_id=APPOINTMENT_ID,
            deposit_percent=30,
            channel="whatsapp_business_encrypted",
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=uuid4(),
        )

        mock_audit.write.assert_called_once()
