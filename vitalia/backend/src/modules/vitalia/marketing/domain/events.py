# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""Marketing domain events for vitalia brand — 9 events total.

All events subclass DomainEvent from luana_core_platform.domain.events.
Events are published via luana_core_events outbox adapter bus.

Events defined:
1. LucasRecommendationGenerated
2. LucasRecommendationApproved
3. LucasRecommendationRejected
4. LucasRecommendationUndone
5. LucasRecommendationExpired
6. ChannelSyncSucceeded
7. ChannelSyncFailed
8. ReferralCodeGenerated
9. ReferralConverted
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from luana_core_platform.domain.events import DomainEvent

from src.modules.vitalia.marketing.domain.enums import BowtieStage, ProviderSlug, RejectReason


@dataclass
class LucasRecommendationGenerated(DomainEvent):
    """Emitted when Lucas AI generates a new recommendation for a clinic."""

    event_name: str = field(default="lucas_recommendation_generated", init=False)
    recommendation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    stage: BowtieStage = BowtieStage.ATTRACTION
    recommendation_kind: str = ""
    priority: int = 1

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        recommendation_id: uuid.UUID,
        stage: BowtieStage,
        recommendation_kind: str,
        priority: int,
    ) -> None:
        payload: dict[str, Any] = {
            "recommendation_id": str(recommendation_id),
            "stage": stage.value,
            "recommendation_kind": recommendation_kind,
            "priority": priority,
        }
        super().__init__(
            event_name="lucas_recommendation_generated",
            tenant_id=tenant_id,
            occurred_at=datetime.now(UTC),
            payload=payload,
        )
        self.recommendation_id = recommendation_id
        self.stage = stage
        self.recommendation_kind = recommendation_kind
        self.priority = priority


@dataclass
class LucasRecommendationApproved(DomainEvent):
    """Emitted when a user approves a Lucas recommendation."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        recommendation_id: uuid.UUID,
        approved_by_user_id: uuid.UUID,
    ) -> None:
        payload: dict[str, Any] = {
            "recommendation_id": str(recommendation_id),
            "approved_by_user_id": str(approved_by_user_id),
        }
        super().__init__(
            event_name="lucas_recommendation_approved",
            tenant_id=tenant_id,
            occurred_at=datetime.now(UTC),
            payload=payload,
        )
        self.recommendation_id = recommendation_id
        self.approved_by_user_id = approved_by_user_id


@dataclass
class LucasRecommendationRejected(DomainEvent):
    """Emitted when a user rejects a Lucas recommendation."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        recommendation_id: uuid.UUID,
        rejected_by_user_id: uuid.UUID,
        reason: RejectReason,
    ) -> None:
        payload: dict[str, Any] = {
            "recommendation_id": str(recommendation_id),
            "rejected_by_user_id": str(rejected_by_user_id),
            "reason": reason.value,
        }
        super().__init__(
            event_name="lucas_recommendation_rejected",
            tenant_id=tenant_id,
            occurred_at=datetime.now(UTC),
            payload=payload,
        )
        self.recommendation_id = recommendation_id
        self.rejected_by_user_id = rejected_by_user_id
        self.reason = reason


@dataclass
class LucasRecommendationUndone(DomainEvent):
    """Emitted when a user undoes a recent approval within the 5-minute window."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        recommendation_id: uuid.UUID,
    ) -> None:
        payload: dict[str, Any] = {
            "recommendation_id": str(recommendation_id),
        }
        super().__init__(
            event_name="lucas_recommendation_undone",
            tenant_id=tenant_id,
            occurred_at=datetime.now(UTC),
            payload=payload,
        )
        self.recommendation_id = recommendation_id


@dataclass
class LucasRecommendationExpired(DomainEvent):
    """Emitted by the expiry cron when a recommendation reaches its expires_at."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        recommendation_id: uuid.UUID,
    ) -> None:
        payload: dict[str, Any] = {
            "recommendation_id": str(recommendation_id),
        }
        super().__init__(
            event_name="lucas_recommendation_expired",
            tenant_id=tenant_id,
            occurred_at=datetime.now(UTC),
            payload=payload,
        )
        self.recommendation_id = recommendation_id


@dataclass
class ChannelSyncSucceeded(DomainEvent):
    """Emitted when an OAuth token sync for an ad channel completes successfully."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        clinic_id: uuid.UUID,
        provider: ProviderSlug,
        synced_at: datetime,
    ) -> None:
        payload: dict[str, Any] = {
            "clinic_id": str(clinic_id),
            "provider": provider.value,
            "synced_at": synced_at.isoformat(),
        }
        super().__init__(
            event_name="channel_sync_succeeded",
            tenant_id=tenant_id,
            occurred_at=datetime.now(UTC),
            payload=payload,
        )
        self.clinic_id = clinic_id
        self.provider = provider
        self.synced_at = synced_at


@dataclass
class ChannelSyncFailed(DomainEvent):
    """Emitted when an OAuth token sync for an ad channel fails."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        clinic_id: uuid.UUID,
        provider: ProviderSlug,
        error_message: str,
    ) -> None:
        payload: dict[str, Any] = {
            "clinic_id": str(clinic_id),
            "provider": provider.value,
            "error_message": error_message,
        }
        super().__init__(
            event_name="channel_sync_failed",
            tenant_id=tenant_id,
            occurred_at=datetime.now(UTC),
            payload=payload,
        )
        self.clinic_id = clinic_id
        self.provider = provider
        self.error_message = error_message


@dataclass
class ReferralCodeGenerated(DomainEvent):
    """Emitted when a new referral code is created for a patient."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        referral_id: uuid.UUID,
        patient_id: uuid.UUID,
        code: str,
    ) -> None:
        payload: dict[str, Any] = {
            "referral_id": str(referral_id),
            "patient_id": str(patient_id),
            "code": code,
        }
        super().__init__(
            event_name="referral_code_generated",
            tenant_id=tenant_id,
            occurred_at=datetime.now(UTC),
            payload=payload,
        )
        self.referral_id = referral_id
        self.patient_id = patient_id
        self.code = code


@dataclass
class ReferralConverted(DomainEvent):
    """Emitted when a referred patient completes registration (referral converted)."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        referral_id: uuid.UUID,
        referred_patient_id: uuid.UUID,
    ) -> None:
        payload: dict[str, Any] = {
            "referral_id": str(referral_id),
            "referred_patient_id": str(referred_patient_id),
        }
        super().__init__(
            event_name="referral_converted",
            tenant_id=tenant_id,
            occurred_at=datetime.now(UTC),
            payload=payload,
        )
        self.referral_id = referral_id
        self.referred_patient_id = referred_patient_id


__all__ = [
    "LucasRecommendationGenerated",
    "LucasRecommendationApproved",
    "LucasRecommendationRejected",
    "LucasRecommendationUndone",
    "LucasRecommendationExpired",
    "ChannelSyncSucceeded",
    "ChannelSyncFailed",
    "ReferralCodeGenerated",
    "ReferralConverted",
]
