"""Tests for fidelización domain value objects (TDD RED phase).

Verifica: ReEngagementPattern, ReEngagementOutcome, UrgencyLevel, NPSBand + from_score helper.
"""

import pytest

from src.modules.vitalia.fidelizacion.domain.value_objects.nps_band import (
    NPSBand,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_outcome import (
    ReEngagementOutcome,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.urgency_level import (
    UrgencyLevel,
)


class TestReEngagementPattern:
    """ReEngagementPattern StrEnum — 5 valores."""

    def test_values_exist(self) -> None:
        assert ReEngagementPattern.MULTI_SESSION == "multi_session"
        assert ReEngagementPattern.FOLLOW_UP == "follow_up"
        assert ReEngagementPattern.MAINTENANCE == "maintenance"
        assert ReEngagementPattern.ABSENCE == "absence"
        assert ReEngagementPattern.NPS == "nps"

    def test_is_str(self) -> None:
        assert isinstance(ReEngagementPattern.MULTI_SESSION, str)

    def test_from_string(self) -> None:
        assert ReEngagementPattern("multi_session") == ReEngagementPattern.MULTI_SESSION

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            ReEngagementPattern("invalid_pattern")

    def test_all_values(self) -> None:
        patterns = list(ReEngagementPattern)
        assert len(patterns) == 5


class TestReEngagementOutcome:
    """ReEngagementOutcome StrEnum — 7 valores."""

    def test_values_exist(self) -> None:
        assert ReEngagementOutcome.SENT == "sent"
        assert ReEngagementOutcome.RESPONDED == "responded"
        assert ReEngagementOutcome.RESCHEDULED == "rescheduled"
        assert ReEngagementOutcome.DECLINED == "declined"
        assert ReEngagementOutcome.NOT_RESPONSIVE == "not_responsive"
        assert ReEngagementOutcome.OPTED_OUT == "opted_out"
        assert ReEngagementOutcome.FAILED_SENDING == "failed_sending"

    def test_is_str(self) -> None:
        assert isinstance(ReEngagementOutcome.SENT, str)

    def test_all_values(self) -> None:
        outcomes = list(ReEngagementOutcome)
        assert len(outcomes) == 7

    def test_from_string(self) -> None:
        assert ReEngagementOutcome("opted_out") == ReEngagementOutcome.OPTED_OUT


class TestUrgencyLevel:
    """UrgencyLevel StrEnum — niveles de urgencia cron/seguimiento."""

    def test_values_exist(self) -> None:
        assert UrgencyLevel.UP_TO_DATE == "up_to_date"
        assert UrgencyLevel.WAITING == "waiting"
        assert UrgencyLevel.NEAR == "near"
        assert UrgencyLevel.ALERT == "alert"
        assert UrgencyLevel.CRITICAL == "critical"

    def test_is_str(self) -> None:
        assert isinstance(UrgencyLevel.ALERT, str)

    def test_ordering_intent(self) -> None:
        """Los 5 niveles deben existir y ser comparables como strings."""
        all_levels = list(UrgencyLevel)
        assert len(all_levels) == 5

    def test_from_string(self) -> None:
        assert UrgencyLevel("critical") == UrgencyLevel.CRITICAL


class TestNPSBand:
    """NPSBand StrEnum con factory from_score."""

    def test_values_exist(self) -> None:
        assert NPSBand.PROMOTER == "promoter"
        assert NPSBand.PASSIVE == "passive"
        assert NPSBand.DETRACTOR == "detractor"

    def test_is_str(self) -> None:
        assert isinstance(NPSBand.PROMOTER, str)

    def test_from_score_promoter(self) -> None:
        for score in range(9, 11):
            assert NPSBand.from_score(score) == NPSBand.PROMOTER

    def test_from_score_passive(self) -> None:
        for score in range(7, 9):
            assert NPSBand.from_score(score) == NPSBand.PASSIVE

    def test_from_score_detractor(self) -> None:
        for score in range(0, 7):
            assert NPSBand.from_score(score) == NPSBand.DETRACTOR

    def test_from_score_boundaries(self) -> None:
        assert NPSBand.from_score(0) == NPSBand.DETRACTOR
        assert NPSBand.from_score(6) == NPSBand.DETRACTOR
        assert NPSBand.from_score(7) == NPSBand.PASSIVE
        assert NPSBand.from_score(8) == NPSBand.PASSIVE
        assert NPSBand.from_score(9) == NPSBand.PROMOTER
        assert NPSBand.from_score(10) == NPSBand.PROMOTER

    def test_from_score_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="score"):
            NPSBand.from_score(-1)
        with pytest.raises(ValueError, match="score"):
            NPSBand.from_score(11)
