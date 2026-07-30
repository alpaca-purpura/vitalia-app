"""RED tests — Lucas domain entities (StageRecommendation, AttributionMatrixSnapshot, ReferralsLeaderboardSnapshot).

TDD per .claude/rules/tdd-mandatory.md. Domain layer is pure Python — no framework imports.
Tests verify entity construction, field types, and invariants.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from uuid import UUID, uuid4

TENANT_ID = uuid4()
CLINIC_ID = uuid4()


def _utc_now() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)


class TestStageRecommendation:
    """Tests for StageRecommendation domain entity."""

    def test_create_with_required_fields(self) -> None:
        """StageRecommendation can be created with required fields."""
        from src.modules.vitalia.agentic.lucas.domain.entities.stage_recommendation import (
            StageRecommendation,
        )

        rec = StageRecommendation(
            id=uuid4(),
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            stage="attraction",
            recommendation_kind="growth",
            title="Aumenta tus nuevos pacientes",
            body="Activa campaña de referidos en tu área.",
            rationale_json={"source": "analytics"},
            priority=50,
            status="open",
            expires_at=_utc_now() + dt.timedelta(days=30),
            created_at=_utc_now(),
            updated_at=_utc_now(),
            deleted_at=None,
            approved_by_user_id=None,
            approved_at=None,
            undo_until=None,
        )
        assert rec.tenant_id == TENANT_ID
        assert rec.clinic_id == CLINIC_ID
        assert rec.stage == "attraction"
        assert rec.status == "open"

    def test_stage_recommendation_has_clinic_id(self) -> None:
        """StageRecommendation carries clinic_id for HIPAA-lite dual filter."""
        from src.modules.vitalia.agentic.lucas.domain.entities.stage_recommendation import (
            StageRecommendation,
        )

        rec = StageRecommendation(
            id=uuid4(),
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            stage="capture",
            recommendation_kind="conversion",
            title="Test",
            body="Test body",
            rationale_json={},
            priority=50,
            status="open",
            expires_at=_utc_now() + dt.timedelta(days=7),
            created_at=_utc_now(),
            updated_at=_utc_now(),
            deleted_at=None,
            approved_by_user_id=None,
            approved_at=None,
            undo_until=None,
        )
        assert isinstance(rec.clinic_id, UUID)

    def test_stage_recommendation_deleted_at_default_none(self) -> None:
        """StageRecommendation deleted_at defaults to None (soft-delete only)."""
        from src.modules.vitalia.agentic.lucas.domain.entities.stage_recommendation import (
            StageRecommendation,
        )

        rec = StageRecommendation(
            id=uuid4(),
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            stage="retention",
            recommendation_kind="loyalty",
            title="Seguimiento",
            body="Crea programa de seguimiento post-tratamiento.",
            rationale_json={},
            priority=40,
            status="open",
            expires_at=_utc_now() + dt.timedelta(days=14),
            created_at=_utc_now(),
            updated_at=_utc_now(),
            deleted_at=None,
            approved_by_user_id=None,
            approved_at=None,
            undo_until=None,
        )
        assert rec.deleted_at is None


class TestAttributionMatrixSnapshot:
    """Tests for AttributionMatrixSnapshot domain entity."""

    def test_create_attribution_snapshot(self) -> None:
        """AttributionMatrixSnapshot can be created with required fields."""
        from src.modules.vitalia.agentic.lucas.domain.entities.attribution_matrix_snapshot import (
            AttributionMatrixSnapshot,
        )

        snap = AttributionMatrixSnapshot(
            id=uuid4(),
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=dt.date(2026, 1, 1),
            period_end=dt.date(2026, 1, 31),
            channel_breakdown={"google_ads": 15000.0, "organic": 8000.0},
            total_attributed_revenue=Decimal("23000.00"),
            currency="ARS",
            computed_at=_utc_now(),
            deleted_at=None,
        )
        assert snap.tenant_id == TENANT_ID
        assert snap.clinic_id == CLINIC_ID
        assert snap.currency == "ARS"

    def test_attribution_snapshot_currency_not_hardcoded(self) -> None:
        """AttributionMatrixSnapshot currency field is flexible, not hardcoded USD."""
        from src.modules.vitalia.agentic.lucas.domain.entities.attribution_matrix_snapshot import (
            AttributionMatrixSnapshot,
        )

        for curr in ("USD", "ARS", "COP", "MXN", "PEN", None):
            snap = AttributionMatrixSnapshot(
                id=uuid4(),
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_ID,
                period_start=dt.date(2026, 1, 1),
                period_end=dt.date(2026, 1, 31),
                channel_breakdown={},
                total_attributed_revenue=Decimal("0.00"),
                currency=curr,
                computed_at=_utc_now(),
                deleted_at=None,
            )
            assert snap.currency == curr


class TestReferralsLeaderboardSnapshot:
    """Tests for ReferralsLeaderboardSnapshot domain entity."""

    def test_create_referrals_snapshot(self) -> None:
        """ReferralsLeaderboardSnapshot can be created with required fields."""
        from src.modules.vitalia.agentic.lucas.domain.entities.referrals_leaderboard_snapshot import (
            ReferralsLeaderboardSnapshot,
        )

        snap = ReferralsLeaderboardSnapshot(
            id=uuid4(),
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=dt.date(2026, 1, 1),
            period_end=dt.date(2026, 1, 31),
            top_referrers=[{"referrer_id": str(uuid4()), "referral_count": 5, "rank": 1}],
            total_referrals=12,
            total_converted=8,
            computed_at=_utc_now(),
            deleted_at=None,
        )
        assert snap.tenant_id == TENANT_ID
        assert snap.clinic_id == CLINIC_ID
        assert snap.total_referrals == 12
        assert snap.total_converted == 8

    def test_referrals_snapshot_has_dual_filter_fields(self) -> None:
        """ReferralsLeaderboardSnapshot carries both tenant_id and clinic_id."""
        from src.modules.vitalia.agentic.lucas.domain.entities.referrals_leaderboard_snapshot import (
            ReferralsLeaderboardSnapshot,
        )

        snap = ReferralsLeaderboardSnapshot(
            id=uuid4(),
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=dt.date(2026, 2, 1),
            period_end=dt.date(2026, 2, 28),
            top_referrers=[],
            total_referrals=0,
            total_converted=0,
            computed_at=_utc_now(),
            deleted_at=None,
        )
        assert isinstance(snap.tenant_id, UUID)
        assert isinstance(snap.clinic_id, UUID)


class TestStageEnum:
    """Tests for StageEnum domain enum."""

    def test_stage_enum_values(self) -> None:
        """StageEnum covers all funnel stages."""
        from src.modules.vitalia.agentic.lucas.domain.enums.stage import StageEnum

        assert StageEnum.ATTRACTION.value == "attraction"
        assert StageEnum.CAPTURE.value == "capture"
        assert StageEnum.NURTURE.value == "nurture"
        assert StageEnum.OPPORTUNITY.value == "opportunity"
        assert StageEnum.RETENTION.value == "retention"

    def test_stage_enum_all_stages_present(self) -> None:
        """All 5 funnel stages are present in StageEnum."""
        from src.modules.vitalia.agentic.lucas.domain.enums.stage import StageEnum

        values = {e.value for e in StageEnum}
        expected = {"attraction", "capture", "nurture", "opportunity", "retention"}
        assert values == expected
