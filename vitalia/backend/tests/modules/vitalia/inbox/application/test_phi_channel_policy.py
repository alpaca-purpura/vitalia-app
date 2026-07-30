# cap: inbox.adrian-inbox
"""Tests for PhiChannelPolicy — TDD RED-first (T-1 vitalia-fase2-adrian-inbox).

SC-3 coverage:
- PHI clinical keywords on unencrypted channel (whatsapp/sms) → allowed=False
- Non-PHI message on whatsapp → allowed=True
- PHI keywords on encrypted channel (web/email) → allowed=True
- Empty message on whatsapp → allowed=True (no keywords)
- failed_policy value when blocked
- Protocol compliance check
"""

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_phi_keywords_on_whatsapp_blocked() -> None:
    """SC-3: PHI clinical result keywords on WhatsApp free tier → allowed=False."""
    from src.modules.vitalia.inbox.application.policies.phi_channel_policy import (
        PhiChannelPolicy,
    )

    policy = PhiChannelPolicy()
    result = await policy.evaluate(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        channel="whatsapp",
        identifier="Tu diagnóstico confirmó displasia cervical, resultados adjuntos.",
        campaign_id=None,
    )

    assert result.allowed is False
    assert result.failed_policy == "phi_unencrypted_channel"


@pytest.mark.asyncio
async def test_phi_resultado_keyword_on_sms_blocked() -> None:
    """SC-3: 'resultado' keyword on SMS channel → allowed=False."""
    from src.modules.vitalia.inbox.application.policies.phi_channel_policy import (
        PhiChannelPolicy,
    )

    policy = PhiChannelPolicy()
    result = await policy.evaluate(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        channel="sms",
        identifier="Su resultado del estudio de laboratorio llegó.",
        campaign_id=None,
    )

    assert result.allowed is False
    assert result.failed_policy == "phi_unencrypted_channel"


@pytest.mark.asyncio
async def test_non_phi_message_on_whatsapp_allowed() -> None:
    """Non-PHI marketing message on WhatsApp → allowed=True."""
    from src.modules.vitalia.inbox.application.policies.phi_channel_policy import (
        PhiChannelPolicy,
    )

    policy = PhiChannelPolicy()
    result = await policy.evaluate(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        channel="whatsapp",
        identifier="Hola, te recordamos tu cita mañana a las 10am.",
        campaign_id=None,
    )

    assert result.allowed is True
    assert result.failed_policy is None


@pytest.mark.asyncio
async def test_phi_keywords_on_web_channel_allowed() -> None:
    """PHI keywords on web (encrypted) channel → allowed=True (no restriction)."""
    from src.modules.vitalia.inbox.application.policies.phi_channel_policy import (
        PhiChannelPolicy,
    )

    policy = PhiChannelPolicy()
    result = await policy.evaluate(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        channel="web",
        identifier="Tu diagnóstico es positivo, aquí tienes los resultados clínicos.",
        campaign_id=None,
    )

    assert result.allowed is True


@pytest.mark.asyncio
async def test_phi_keywords_on_email_channel_allowed() -> None:
    """PHI keywords on email (encrypted) channel → allowed=True."""
    from src.modules.vitalia.inbox.application.policies.phi_channel_policy import (
        PhiChannelPolicy,
    )

    policy = PhiChannelPolicy()
    result = await policy.evaluate(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        channel="email",
        identifier="Adjunto el informe de laboratorio con tu diagnóstico.",
        campaign_id=None,
    )

    assert result.allowed is True


@pytest.mark.asyncio
async def test_empty_message_on_whatsapp_allowed() -> None:
    """Empty message (no content) on WhatsApp → allowed=True (no PHI keywords)."""
    from src.modules.vitalia.inbox.application.policies.phi_channel_policy import (
        PhiChannelPolicy,
    )

    policy = PhiChannelPolicy()
    result = await policy.evaluate(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        channel="whatsapp",
        identifier="",
        campaign_id=None,
    )

    assert result.allowed is True


@pytest.mark.asyncio
async def test_instagram_not_in_unencrypted_set() -> None:
    """Instagram is not in _UNENCRYPTED_CHANNELS → PHI keywords allowed by this policy."""
    from src.modules.vitalia.inbox.application.policies.phi_channel_policy import (
        PhiChannelPolicy,
    )

    policy = PhiChannelPolicy()
    result = await policy.evaluate(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        channel="instagram",
        identifier="Tu diagnóstico está listo, te compartimos los resultados.",
        campaign_id=None,
    )

    # Instagram is NOT in _UNENCRYPTED_CHANNELS (only whatsapp free tier + sms)
    assert result.allowed is True


@pytest.mark.asyncio
async def test_policy_has_name_attribute() -> None:
    """PhiChannelPolicy.name is set (satisfies CompliancePolicy Protocol)."""
    from src.modules.vitalia.inbox.application.policies.phi_channel_policy import (
        PhiChannelPolicy,
    )

    policy = PhiChannelPolicy()
    assert hasattr(policy, "name")
    assert isinstance(policy.name, str)
    assert len(policy.name) > 0


def test_phi_channel_policy_implements_compliance_policy_protocol() -> None:
    """PhiChannelPolicy satisfies the CompliancePolicy Protocol (runtime_checkable)."""
    from luana_core_compliance.application.compliance_service import CompliancePolicy

    from src.modules.vitalia.inbox.application.policies.phi_channel_policy import (
        PhiChannelPolicy,
    )

    assert isinstance(PhiChannelPolicy(), CompliancePolicy)
