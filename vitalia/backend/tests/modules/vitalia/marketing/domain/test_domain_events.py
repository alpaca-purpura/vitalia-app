"""Tests for marketing domain events — all 9 events must be defined with correct payloads."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.modules.vitalia.marketing.domain.enums import BowtieStage, ProviderSlug, RejectReason
from src.modules.vitalia.marketing.domain.events import (
    ChannelSyncFailed,
    ChannelSyncSucceeded,
    LucasRecommendationApproved,
    LucasRecommendationExpired,
    LucasRecommendationGenerated,
    LucasRecommendationRejected,
    LucasRecommendationUndone,
    ReferralCodeGenerated,
    ReferralConverted,
)


class TestLucasRecommendationGenerated:
    """LucasRecommendationGenerated event has correct structure."""

    def test_event_name(self) -> None:
        tenant_id = uuid.uuid4()
        rec_id = uuid.uuid4()
        event = LucasRecommendationGenerated(
            tenant_id=tenant_id,
            recommendation_id=rec_id,
            stage=BowtieStage.ATTRACTION,
            recommendation_kind="increase_budget",
            priority=1,
        )
        assert event.event_name == "lucas_recommendation_generated"

    def test_payload_contains_recommendation_id(self) -> None:
        tenant_id = uuid.uuid4()
        rec_id = uuid.uuid4()
        event = LucasRecommendationGenerated(
            tenant_id=tenant_id,
            recommendation_id=rec_id,
            stage=BowtieStage.ATTRACTION,
            recommendation_kind="increase_budget",
            priority=1,
        )
        assert str(rec_id) in str(event.payload)

    def test_tenant_id_set(self) -> None:
        tenant_id = uuid.uuid4()
        event = LucasRecommendationGenerated(
            tenant_id=tenant_id,
            recommendation_id=uuid.uuid4(),
            stage=BowtieStage.QUALIFICATION,
            recommendation_kind="add_promo",
            priority=2,
        )
        assert event.tenant_id == tenant_id


class TestLucasRecommendationApproved:
    """LucasRecommendationApproved event is defined."""

    def test_event_name(self) -> None:
        event = LucasRecommendationApproved(
            tenant_id=uuid.uuid4(),
            recommendation_id=uuid.uuid4(),
            approved_by_user_id=uuid.uuid4(),
        )
        assert event.event_name == "lucas_recommendation_approved"


class TestLucasRecommendationRejected:
    """LucasRecommendationRejected event is defined."""

    def test_event_name(self) -> None:
        event = LucasRecommendationRejected(
            tenant_id=uuid.uuid4(),
            recommendation_id=uuid.uuid4(),
            rejected_by_user_id=uuid.uuid4(),
            reason=RejectReason.NOT_PRIORITY,
        )
        assert event.event_name == "lucas_recommendation_rejected"


class TestLucasRecommendationUndone:
    """LucasRecommendationUndone event is defined."""

    def test_event_name(self) -> None:
        event = LucasRecommendationUndone(
            tenant_id=uuid.uuid4(),
            recommendation_id=uuid.uuid4(),
        )
        assert event.event_name == "lucas_recommendation_undone"


class TestLucasRecommendationExpired:
    """LucasRecommendationExpired event is defined."""

    def test_event_name(self) -> None:
        event = LucasRecommendationExpired(
            tenant_id=uuid.uuid4(),
            recommendation_id=uuid.uuid4(),
        )
        assert event.event_name == "lucas_recommendation_expired"


class TestChannelSyncSucceeded:
    """ChannelSyncSucceeded event is defined."""

    def test_event_name(self) -> None:
        event = ChannelSyncSucceeded(
            tenant_id=uuid.uuid4(),
            clinic_id=uuid.uuid4(),
            provider=ProviderSlug.GOOGLE_ADS,
            synced_at=datetime.now(UTC),
        )
        assert event.event_name == "channel_sync_succeeded"


class TestChannelSyncFailed:
    """ChannelSyncFailed event is defined."""

    def test_event_name(self) -> None:
        event = ChannelSyncFailed(
            tenant_id=uuid.uuid4(),
            clinic_id=uuid.uuid4(),
            provider=ProviderSlug.META_ADS,
            error_message="Token expirado",
        )
        assert event.event_name == "channel_sync_failed"


class TestReferralCodeGenerated:
    """ReferralCodeGenerated event is defined."""

    def test_event_name(self) -> None:
        event = ReferralCodeGenerated(
            tenant_id=uuid.uuid4(),
            referral_id=uuid.uuid4(),
            patient_id=uuid.uuid4(),
            code="REF-ABC123",
        )
        assert event.event_name == "referral_code_generated"


class TestReferralConverted:
    """ReferralConverted event is defined."""

    def test_event_name(self) -> None:
        event = ReferralConverted(
            tenant_id=uuid.uuid4(),
            referral_id=uuid.uuid4(),
            referred_patient_id=uuid.uuid4(),
        )
        assert event.event_name == "referral_converted"
