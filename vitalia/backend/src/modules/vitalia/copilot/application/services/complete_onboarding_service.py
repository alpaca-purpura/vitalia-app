# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""CompleteOnboardingService — finalize Valeria wizard onboarding.

Orchestrates the onboarding completion flow:
1. Retrieve and validate the OnboardingDraft
2. Compile full personality profile from confirmed slots
3. Commit brand profile via brand_studio_port
4. Mark tenant as onboarded via tenant_port
5. Write audit log SYNC (HIPAA-lite compliance)
6. Publish TenantOnboardedEvent via outbox

HIPAA-lite: writes audit_log sync before response (per hipaa-lite.md § Audit log).
Events: USE_OUTBOX_PATTERN_COPILOT=True — TenantOnboardedEvent via outbox bus.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger()


class DraftNotFoundError(Exception):
    """Raised when the OnboardingDraft is not found for the given tenant."""

    def __init__(self, draft_id: UUID, tenant_id: UUID) -> None:
        """Initialize with identifiers."""
        super().__init__(f"OnboardingDraft {draft_id} not found for tenant {tenant_id}")
        self.draft_id = draft_id
        self.tenant_id = tenant_id


@dataclass
class CompleteResponse:
    """Response from completing onboarding.

    Attributes:
        tenant_activated: True when onboarding successfully completed.
        redirect_url: URL to redirect the user to post-onboarding.
    """

    tenant_activated: bool
    redirect_url: str


class TenantOnboardedEvent:
    """Domain event emitted when a tenant completes onboarding.

    Used by downstream systems (sales_agent activation, analytics, etc.)
    to react to new tenant onboarding.
    """

    def __init__(self, *, tenant_id: UUID, profile_id: Any) -> None:
        """Initialize event with tenant and profile identifiers."""
        self.tenant_id = tenant_id
        self.profile_id = profile_id
        self.occurred_at = datetime.now(tz=timezone.utc)


class CompleteOnboardingService:
    """Application service for completing the Valeria wizard onboarding.

    Coordinates personality compilation, brand commit, tenant activation,
    audit logging, and event emission in a single transactional flow.

    Dependencies injected — no direct DB/HTTP imports.
    """

    def __init__(
        self,
        draft_repo: "object",
        personality_adapter: "object",
        brand_studio_port: "object",
        tenant_port: "object",
        audit_log_repo: "object",
        event_bus: "object",
    ) -> None:
        """Initialize with all required ports and adapters."""
        self._draft_repo = draft_repo
        self._personality_adapter = personality_adapter
        self._brand_studio_port = brand_studio_port
        self._tenant_port = tenant_port
        self._audit_log_repo = audit_log_repo
        self._event_bus = event_bus

    async def complete(
        self,
        *,
        draft_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
    ) -> CompleteResponse:
        """Complete the onboarding for the given draft.

        Steps:
        1. Get draft (raises DraftNotFoundError if missing — tenant_id filter)
        2. Compile personality profile from confirmed slots
        3. Commit brand profile to brand studio
        4. Mark tenant as onboarded
        5. Save draft with completed_at timestamp
        6. Write audit log SYNC (HIPAA-lite requirement)
        7. Publish TenantOnboardedEvent via event_bus

        Args:
            draft_id: OnboardingDraft to complete.
            tenant_id: Tenant isolation identifier.
            user_id: User completing the onboarding.

        Returns:
            CompleteResponse with tenant_activated=True and redirect_url.

        Raises:
            DraftNotFoundError: When draft not found for tenant.
        """
        # 1. Get draft — tenant_id filter enforced by repo
        draft = await self._draft_repo.get_by_id(draft_id, tenant_id=tenant_id)
        if draft is None:
            raise DraftNotFoundError(draft_id, tenant_id)

        confirmed_slots = draft.all_confirmed_slots()

        # 2. Compile full personality profile
        profile = await self._personality_adapter.compile_full(
            tenant_id=tenant_id,
            slots_confirmed=confirmed_slots,
        )

        # 3. Commit brand profile to brand studio
        await self._brand_studio_port.commit_brand(
            tenant_id=tenant_id,
            profile=profile,
            slots=confirmed_slots,
        )

        # 4. Mark tenant as onboarded
        await self._tenant_port.mark_onboarded(tenant_id=tenant_id)

        # 5. Soft-complete the draft (set completed_at)
        draft.completed_at = datetime.now(tz=timezone.utc)
        draft.updated_at = draft.completed_at
        await self._draft_repo.save(draft)

        # 6. Write audit log SYNC — HIPAA-lite: must complete before response
        await self._audit_log_repo.write(
            tenant_id=tenant_id,
            action="onboarding_completed",
            resource_type="onboarding_draft",
            resource_id=str(draft_id),
            user_id=user_id,
        )

        # 7. Publish domain event via outbox (USE_OUTBOX_PATTERN_COPILOT=True)
        event = TenantOnboardedEvent(
            tenant_id=tenant_id,
            profile_id=getattr(profile, "id", None),
        )
        await self._event_bus.publish(event)

        logger.info(
            "onboarding_completed",
            draft_id=str(draft_id),
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            profile_id=str(getattr(profile, "id", "")),
        )

        return CompleteResponse(
            tenant_activated=True,
            redirect_url="/inbox",
        )
