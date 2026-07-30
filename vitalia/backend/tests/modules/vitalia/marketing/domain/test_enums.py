"""Tests for marketing domain enums — all enum values must be defined."""

from __future__ import annotations

from src.modules.vitalia.marketing.domain.enums import (
    BowtieStage,
    ProviderSlug,
    RecommendationStatus,
    ReferralStatus,
    RejectReason,
    SyncStatus,
)


class TestProviderSlug:
    """ProviderSlug enum covers all supported ad providers."""

    def test_google_ads_value(self) -> None:
        assert ProviderSlug.GOOGLE_ADS.value == "google_ads"

    def test_meta_ads_value(self) -> None:
        assert ProviderSlug.META_ADS.value == "meta_ads"

    def test_has_exactly_two_providers(self) -> None:
        assert len(ProviderSlug) == 2


class TestSyncStatus:
    """SyncStatus enum covers sync states."""

    def test_ok_value(self) -> None:
        assert SyncStatus.OK.value == "ok"

    def test_error_value(self) -> None:
        assert SyncStatus.ERROR.value == "error"

    def test_pending_value(self) -> None:
        assert SyncStatus.PENDING.value == "pending"

    def test_has_exactly_three_statuses(self) -> None:
        assert len(SyncStatus) == 3


class TestRecommendationStatus:
    """RecommendationStatus enum covers lifecycle states."""

    def test_open_value(self) -> None:
        assert RecommendationStatus.OPEN.value == "open"

    def test_approved_value(self) -> None:
        assert RecommendationStatus.APPROVED.value == "approved"

    def test_rejected_value(self) -> None:
        assert RecommendationStatus.REJECTED.value == "rejected"

    def test_expired_value(self) -> None:
        assert RecommendationStatus.EXPIRED.value == "expired"

    def test_has_exactly_four_statuses(self) -> None:
        assert len(RecommendationStatus) == 4


class TestReferralStatus:
    """ReferralStatus enum covers referral lifecycle (5 states per spec)."""

    def test_open_value(self) -> None:
        assert ReferralStatus.OPEN.value == "open"

    def test_shared_value(self) -> None:
        assert ReferralStatus.SHARED.value == "shared"

    def test_signed_up_value(self) -> None:
        assert ReferralStatus.SIGNED_UP.value == "signed_up"

    def test_converted_value(self) -> None:
        assert ReferralStatus.CONVERTED.value == "converted"

    def test_expired_value(self) -> None:
        assert ReferralStatus.EXPIRED.value == "expired"

    def test_has_exactly_five_statuses(self) -> None:
        assert len(ReferralStatus) == 5


class TestBowtieStage:
    """BowtieStage enum covers the 5-stage bowtie marketing funnel per spec."""

    def test_attraction_value(self) -> None:
        assert BowtieStage.ATTRACTION.value == "attraction"

    def test_qualification_value(self) -> None:
        assert BowtieStage.QUALIFICATION.value == "qualification"

    def test_reservation_value(self) -> None:
        assert BowtieStage.RESERVATION.value == "reservation"

    def test_adoption_value(self) -> None:
        assert BowtieStage.ADOPTION.value == "adoption"

    def test_expansion_value(self) -> None:
        assert BowtieStage.EXPANSION.value == "expansion"

    def test_has_exactly_five_stages(self) -> None:
        assert len(BowtieStage) == 5


class TestRejectReason:
    """RejectReason enum covers reasons a recommendation can be rejected (5 per spec)."""

    def test_not_priority_value(self) -> None:
        assert RejectReason.NOT_PRIORITY.value == "not_priority"

    def test_already_doing_value(self) -> None:
        assert RejectReason.ALREADY_DOING.value == "already_doing"

    def test_data_wrong_value(self) -> None:
        assert RejectReason.DATA_WRONG.value == "data_wrong"

    def test_too_risky_value(self) -> None:
        assert RejectReason.TOO_RISKY.value == "too_risky"

    def test_other_value(self) -> None:
        assert RejectReason.OTHER.value == "other"

    def test_has_exactly_five_reasons(self) -> None:
        assert len(RejectReason) == 5
