"""Tests for ProactiveOutboundService — TDD RED (T-inbox-be-3).

Coverage:
- 5 HSM templates: utility (no opt-in required) + marketing (opt-in required)
- ComplianceService gate blocks PHI on unencrypted channels
- marketing_opt_in enforcement for MARKETING category templates
- 7d throttle via OutboundRateLimiter
- ProactiveOutboundSent event emitted
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
LEAD_ID = uuid4()
CONV_ID = uuid4()
USER_ID = uuid4()


def _make_lead_model(marketing_opt_in: bool = True) -> MagicMock:
    lead = MagicMock()
    lead.id = LEAD_ID
    lead.tenant_id = TENANT_ID
    lead.clinic_id = CLINIC_ID
    lead.marketing_opt_in = marketing_opt_in
    lead.whatsapp_phone = "+521234567890"
    lead.channel = "whatsapp"
    return lead


def _make_compliance_result(allowed: bool = True) -> MagicMock:
    result = MagicMock()
    result.allowed = allowed
    result.failed_policy = None if allowed else "opt_in"
    result.reason = None if allowed else "lead has not opted in"
    return result


# ---------------------------------------------------------------------------
# Utility template tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proactive_outbound_utility_template_no_opt_in_required() -> None:
    """recordatorio_proxima_sesion (UTILITY) → no marketing_opt_in required."""
    from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
        ProactiveOutboundService,
    )

    lead_repo = AsyncMock()
    conv_repo = AsyncMock()
    msg_repo = AsyncMock()
    audit_writer = AsyncMock()
    event_bus = AsyncMock()
    compliance_service = AsyncMock()
    rate_limiter = AsyncMock()
    channel_adapter = AsyncMock()

    lead_model = _make_lead_model(marketing_opt_in=False)  # no opt-in
    lead_repo.get_by_id = AsyncMock(return_value=lead_model)

    compliance_result = _make_compliance_result(allowed=True)
    compliance_service.check = AsyncMock(return_value=compliance_result)

    rate_limiter.check = AsyncMock(return_value=True)

    sent_msg = MagicMock()
    sent_msg.id = uuid4()
    sent_msg.conversation_id = CONV_ID
    sent_msg.sent_at = datetime.now(UTC)
    msg_repo.create = AsyncMock(return_value=sent_msg)

    conv_model = MagicMock()
    conv_model.id = CONV_ID
    conv_repo.get_or_create_for_lead = AsyncMock(return_value=conv_model)

    svc = ProactiveOutboundService(
        lead_repo=lead_repo,
        conv_repo=conv_repo,
        msg_repo=msg_repo,
        audit_writer=audit_writer,
        event_bus=event_bus,
        compliance_service=compliance_service,
        rate_limiter=rate_limiter,
        channel_adapters={"whatsapp": channel_adapter},
    )

    result = await svc.send_proactive(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        lead_id=LEAD_ID,
        template_id="recordatorio_proxima_sesion",
        variables={"fecha": "miércoles 21 de mayo"},
        channel="whatsapp",
        sent_by_user_id=USER_ID,
    )

    assert result is not None
    assert result.template_id == "recordatorio_proxima_sesion"
    event_bus.publish.assert_called()


@pytest.mark.asyncio
async def test_proactive_outbound_marketing_requires_opt_in() -> None:
    """re_engagement_ausencia (MARKETING) → requires marketing_opt_in=True."""
    from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
        MarketingOptInRequiredError,
        ProactiveOutboundService,
    )

    lead_repo = AsyncMock()

    lead_model = _make_lead_model(marketing_opt_in=False)  # no opt-in
    lead_repo.get_by_id = AsyncMock(return_value=lead_model)

    svc = ProactiveOutboundService(
        lead_repo=lead_repo,
        conv_repo=AsyncMock(),
        msg_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        compliance_service=AsyncMock(),
        rate_limiter=AsyncMock(),
        channel_adapters={},
    )

    with pytest.raises(MarketingOptInRequiredError):
        await svc.send_proactive(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            lead_id=LEAD_ID,
            template_id="re_engagement_ausencia",  # MARKETING template
            variables={},
            channel="whatsapp",
            sent_by_user_id=USER_ID,
        )


@pytest.mark.asyncio
async def test_proactive_outbound_unknown_template_raises_error() -> None:
    """Unknown template_id → TemplateNotFoundError."""
    from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
        ProactiveOutboundService,
        TemplateNotFoundError,
    )

    lead_repo = AsyncMock()
    lead_repo.get_by_id = AsyncMock(return_value=_make_lead_model())

    svc = ProactiveOutboundService(
        lead_repo=lead_repo,
        conv_repo=AsyncMock(),
        msg_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        compliance_service=AsyncMock(),
        rate_limiter=AsyncMock(),
        channel_adapters={},
    )

    with pytest.raises(TemplateNotFoundError):
        await svc.send_proactive(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            lead_id=LEAD_ID,
            template_id="template_inexistente",
            variables={},
            channel="whatsapp",
            sent_by_user_id=USER_ID,
        )


@pytest.mark.asyncio
async def test_proactive_outbound_compliance_block_raises_error() -> None:
    """ComplianceService block → ComplianceBlockedError."""
    from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
        ComplianceBlockedError,
        ProactiveOutboundService,
    )

    lead_repo = AsyncMock()
    lead_model = _make_lead_model(marketing_opt_in=True)
    lead_repo.get_by_id = AsyncMock(return_value=lead_model)

    compliance_service = AsyncMock()
    blocked_result = _make_compliance_result(allowed=False)
    compliance_service.check = AsyncMock(return_value=blocked_result)

    svc = ProactiveOutboundService(
        lead_repo=lead_repo,
        conv_repo=AsyncMock(),
        msg_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        compliance_service=compliance_service,
        rate_limiter=AsyncMock(),
        channel_adapters={},
    )

    with pytest.raises(ComplianceBlockedError):
        await svc.send_proactive(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            lead_id=LEAD_ID,
            template_id="recordatorio_proxima_sesion",
            variables={"fecha": "mañana"},
            channel="whatsapp",
            sent_by_user_id=USER_ID,
        )


@pytest.mark.asyncio
async def test_proactive_outbound_rate_limit_exceeded_raises_error() -> None:
    """OutboundRateLimiter exceeded → RateLimitExceededError."""
    from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
        ProactiveOutboundService,
        RateLimitExceededError,
    )

    lead_repo = AsyncMock()
    lead_model = _make_lead_model(marketing_opt_in=True)
    lead_repo.get_by_id = AsyncMock(return_value=lead_model)

    compliance_service = AsyncMock()
    compliance_service.check = AsyncMock(return_value=_make_compliance_result(allowed=True))

    rate_limiter = AsyncMock()
    rate_limiter.check = AsyncMock(return_value=False)  # exceeded

    svc = ProactiveOutboundService(
        lead_repo=lead_repo,
        conv_repo=AsyncMock(),
        msg_repo=AsyncMock(),
        audit_writer=AsyncMock(),
        event_bus=AsyncMock(),
        compliance_service=compliance_service,
        rate_limiter=rate_limiter,
        channel_adapters={},
    )

    with pytest.raises(RateLimitExceededError):
        await svc.send_proactive(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            lead_id=LEAD_ID,
            template_id="recordatorio_proxima_sesion",
            variables={"fecha": "mañana"},
            channel="whatsapp",
            sent_by_user_id=USER_ID,
        )
