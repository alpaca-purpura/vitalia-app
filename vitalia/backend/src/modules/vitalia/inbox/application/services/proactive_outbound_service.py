# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""ProactiveOutboundService — vitalia inbox application layer.

HSM template picker with ComplianceService gate + marketing opt-in enforcement.

PHI obligations (hipaa-lite.md § Regla cardinal):
1. tenant_id + clinic_id dual filter on all repos
2. ComplianceService gate mandatory before send
3. Audit log written sync pre-response
4. ProactiveOutboundSent + MessageSent events via outbox bus

downstream-regression-na: brand-local vitalia inbox service
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.crm.domain.events import MessageSent, ProactiveOutboundSent
from src.modules.vitalia.inbox.application.services._templates import (
    get_template,
    is_marketing_template,
)

if TYPE_CHECKING:
    from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
        ConversationRepository,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
        MessageRepository,
    )

logger = structlog.get_logger()


class TemplateNotFoundError(Exception):
    """Raised when template_id is not in the approved registry."""

    def __init__(self, template_id: str) -> None:
        """Initialize."""
        super().__init__(f"Template '{template_id}' not found. Use one of the 5 Meta-approved HSM templates.")
        self.template_id = template_id


class MarketingOptInRequiredError(Exception):
    """Raised when a MARKETING template is used without marketing_opt_in."""

    def __init__(self, template_id: str, lead_id: UUID) -> None:
        """Initialize."""
        super().__init__(
            f"Template '{template_id}' is MARKETING category "
            f"but lead {lead_id} has not opted in to marketing communications."
        )
        self.template_id = template_id
        self.lead_id = lead_id


class ComplianceBlockedError(Exception):
    """Raised when ComplianceService gate blocks the outbound."""

    def __init__(self, failed_policy: str, reason: str | None) -> None:
        """Initialize."""
        super().__init__(f"Compliance check failed (policy: {failed_policy}): {reason}")
        self.failed_policy = failed_policy
        self.reason = reason


class RateLimitExceededError(Exception):
    """Raised when OutboundRateLimiter daily cap is exceeded."""

    def __init__(self, tenant_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"Outbound rate limit exceeded for tenant {tenant_id}. Try again tomorrow.")
        self.tenant_id = tenant_id


class LeadNotFoundError(Exception):
    """Raised when lead does not exist for tenant+clinic."""

    def __init__(self, lead_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"Lead {lead_id} not found or access denied")
        self.lead_id = lead_id


@dataclass
class ProactiveOutboundResult:
    """Result from ProactiveOutboundService.send_proactive()."""

    conversation_id: UUID
    message_id: UUID
    template_id: str
    channel: str
    sent_at: datetime
    compliance_checked: bool = True


class ProactiveOutboundService:
    """Service for sending HSM proactive outbound messages.

    Template registry: 5 Meta-approved templates (see _templates.py).
    - UTILITY: no marketing_opt_in required.
    - MARKETING: requires lead.marketing_opt_in = True.

    ComplianceService gate applied before any send (PHI channel guard + opt-in).
    OutboundRateLimiter gate applied (7d throttle per pattern per arch spec §6.6).
    """

    def __init__(
        self,
        *,
        lead_repo: object,
        conv_repo: ConversationRepository,
        msg_repo: MessageRepository,
        audit_writer: object,
        event_bus: object,
        compliance_service: object,
        rate_limiter: object,
        channel_adapters: dict[str, object],
        session: object | None = None,
    ) -> None:
        """Initialize ProactiveOutboundService.

        Args:
            lead_repo: LeadRepository (for lead fetch + marketing_opt_in check).
            conv_repo: ConversationRepository (dual-filter enforced).
            msg_repo: MessageRepository (dual-filter enforced).
            audit_writer: Async audit log writer.
            event_bus: Outbox event bus.
            compliance_service: ComplianceService instance (PHI + channel gate).
            rate_limiter: OutboundRateLimiter instance (daily cap).
            channel_adapters: Dict mapping channel name to adapter instance.
            session: Optional AsyncSession for event publish.
        """
        self._lead_repo = lead_repo
        self._conv_repo = conv_repo
        self._msg_repo = msg_repo
        self._audit_writer = audit_writer
        self._event_bus = event_bus
        self._compliance = compliance_service
        self._rate_limiter = rate_limiter
        self._channel_adapters = channel_adapters
        self._session = session

    async def send_proactive(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        lead_id: UUID,
        template_id: str,
        variables: dict[str, str],
        channel: str,
        sent_by_user_id: UUID,
    ) -> ProactiveOutboundResult:
        """Send a proactive HSM message via approved template.

        PHI dual-filter: all repo calls include tenant_id AND clinic_id.
        Audit log written sync before returning.

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            lead_id: Target lead UUID.
            template_id: One of the 5 Meta-approved template IDs.
            variables: Template variable substitutions.
            channel: Outbound channel ('whatsapp' | 'instagram').
            sent_by_user_id: User triggering the send.

        Returns:
            ProactiveOutboundResult with conversation and message IDs.

        Raises:
            TemplateNotFoundError: template_id not in approved registry.
            LeadNotFoundError: Lead does not exist for tenant+clinic.
            MarketingOptInRequiredError: MARKETING template without opt-in.
            ComplianceBlockedError: ComplianceService gate failed.
            RateLimitExceededError: Daily outbound cap exceeded.
        """
        # Validate template exists in registry
        template = get_template(template_id)
        if template is None:
            raise TemplateNotFoundError(template_id)

        # Fetch lead (dual-filter applied by repo)
        lead = await self._lead_repo.get_by_id(
            id=lead_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )
        if lead is None:
            raise LeadNotFoundError(lead_id)

        # Marketing opt-in enforcement for MARKETING templates
        if is_marketing_template(template_id) and not lead.marketing_opt_in:
            raise MarketingOptInRequiredError(template_id, lead_id)

        # ComplianceService gate (PHI channel guard + opt-in policy chain)
        compliance_result = await self._compliance.check(
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel=channel,
            identifier=str(lead_id),
            campaign_id=None,
        )
        if not compliance_result.allowed:
            raise ComplianceBlockedError(
                failed_policy=compliance_result.failed_policy or "unknown",
                reason=compliance_result.reason,
            )

        # Rate limiter check (daily outbound cap)
        allowed = await self._rate_limiter.check(tenant_id=tenant_id)
        if not allowed:
            raise RateLimitExceededError(tenant_id)

        # Get or create conversation for lead
        conv = await self._conv_repo.get_or_create_for_lead(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            lead_id=lead_id,
            channel=channel,
        )

        now = datetime.now(UTC)
        msg_id = uuid4()

        # Persist message
        msg = await self._msg_repo.create(
            id=msg_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conv.id,
            channel=channel,
            external_message_id=None,
            sender_type="system",
            sender_user_id=sent_by_user_id,
            body_text=f"[HSM:{template_id}]",
            media_kind=None,
            media_url=None,
            media_duration_s=None,
            media_phi_flagged=False,
            transcription_text=None,
            transcription_confidence=None,
            retracted_at=None,
            retracted_by_user_id=None,
            retracted_reason=None,
            retract_succeeded=None,
            handler_mode="ai",
            cache_hit_rate=None,
            llm_cost_usd=None,
            sent_at=now,
            delivered_at=None,
            read_at=None,
        )

        # Audit log sync write (HIPAA-lite: mandatory pre-response)
        await self._audit_writer.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=sent_by_user_id,
            action="inbox.proactive_outbound.sent",
            resource_type="inbox.proactive_outbound_sent",
            resource_id=msg.id,
            payload={
                "template_id": template_id,
                "channel": channel,
                "lead_id": str(lead_id),
                "conversation_id": str(conv.id),
            },
        )

        # Emit events via outbox bus
        msg_event = MessageSent(
            event_name="message_sent",
            tenant_id=tenant_id,
            message_id=msg.id,
            conversation_id=conv.id,
            clinic_id=clinic_id,
            sender_type="system",
            channel=channel,
            occurred_at=now,
        )
        await self._event_bus.publish(msg_event, session=self._session)

        outbound_event = ProactiveOutboundSent(
            event_name="proactive_outbound_sent",
            tenant_id=tenant_id,
            message_id=msg.id,
            conversation_id=conv.id,
            clinic_id=clinic_id,
            channel=channel,
            outbound_kind="hsm_template",
            occurred_at=now,
        )
        await self._event_bus.publish(outbound_event, session=self._session)

        logger.info(
            "proactive_outbound.sent",
            tenant_id=str(tenant_id),
            template_id=template_id,
            channel=channel,
            conversation_id=str(conv.id),
        )

        return ProactiveOutboundResult(
            conversation_id=conv.id,
            message_id=msg.id,
            template_id=template_id,
            channel=channel,
            sent_at=now,
            compliance_checked=True,
        )
