"""Contract tests for ``OfferAdherenceContract`` Protocol + ``MaintenanceScheduleEnum``.

Added 2026-05-17 via promotion proposal
``docs/promotion-protocol/proposals/2026-05-17-offer-studio-multi-session-maintenance.md``.

Validates:
  - Protocol shape (runtime_checkable)
  - MaintenanceScheduleEnum values stable
  - Conforming offers pass isinstance check
  - Non-conforming offers fail isinstance check
"""

from __future__ import annotations

import pytest

from luana_core_offer_studio.domain.enums import MaintenanceScheduleEnum
from luana_core_offer_studio.domain.offer import OfferAdherenceContract


class _ConformingOffer:
    """Minimal class that conforms to OfferAdherenceContract."""

    def __init__(
        self,
        requires_multi_session: bool = False,
        sessions_expected: int | None = None,
        gap_alert_days: int | None = None,
        maintenance_schedule: MaintenanceScheduleEnum = MaintenanceScheduleEnum.NONE,
        maintenance_custom_days: int | None = None,
    ) -> None:
        self.requires_multi_session = requires_multi_session
        self.sessions_expected = sessions_expected
        self.gap_alert_days = gap_alert_days
        self.maintenance_schedule = maintenance_schedule
        self.maintenance_custom_days = maintenance_custom_days


class _MissingMaintenanceOffer:
    """Missing ``maintenance_schedule`` field — should fail Protocol check."""

    def __init__(self) -> None:
        self.requires_multi_session = True
        self.sessions_expected = 4
        self.gap_alert_days = 21
        self.maintenance_custom_days = None


def test_maintenance_schedule_enum_values_stable() -> None:
    """Enum values are stable + match proposal contract."""
    expected = {"NONE", "MONTHLY", "QUARTERLY", "BIANNUAL", "ANNUAL", "CUSTOM"}
    actual = {e.value for e in MaintenanceScheduleEnum}
    assert actual == expected


def test_maintenance_schedule_default_none() -> None:
    """Default value semantically = NONE (one-shot offer)."""
    assert MaintenanceScheduleEnum.NONE.value == "NONE"


def test_one_shot_offer_conforms() -> None:
    """Offer with defaults (no multi-session, no maintenance) is valid."""
    offer = _ConformingOffer()
    assert isinstance(offer, OfferAdherenceContract)
    assert offer.requires_multi_session is False
    assert offer.maintenance_schedule == MaintenanceScheduleEnum.NONE


def test_multi_session_offer_conforms() -> None:
    """Offer with multi-session columns set is valid (e.g. orthodontics)."""
    offer = _ConformingOffer(
        requires_multi_session=True,
        sessions_expected=12,
        gap_alert_days=60,
    )
    assert isinstance(offer, OfferAdherenceContract)


def test_maintenance_offer_conforms() -> None:
    """Offer with maintenance schedule is valid (e.g. dental cleaning BIANNUAL)."""
    offer = _ConformingOffer(maintenance_schedule=MaintenanceScheduleEnum.BIANNUAL)
    assert isinstance(offer, OfferAdherenceContract)


def test_custom_maintenance_with_days_conforms() -> None:
    """CUSTOM maintenance with custom_days is valid (e.g. 45-day cadence)."""
    offer = _ConformingOffer(
        maintenance_schedule=MaintenanceScheduleEnum.CUSTOM,
        maintenance_custom_days=45,
    )
    assert isinstance(offer, OfferAdherenceContract)


def test_missing_required_field_fails() -> None:
    """Offer missing ``maintenance_schedule`` is not recognized as protocol member."""
    offer = _MissingMaintenanceOffer()
    assert not isinstance(offer, OfferAdherenceContract)


@pytest.mark.parametrize(
    "schedule",
    [
        MaintenanceScheduleEnum.NONE,
        MaintenanceScheduleEnum.MONTHLY,
        MaintenanceScheduleEnum.QUARTERLY,
        MaintenanceScheduleEnum.BIANNUAL,
        MaintenanceScheduleEnum.ANNUAL,
        MaintenanceScheduleEnum.CUSTOM,
    ],
)
def test_all_schedule_values_accepted_shape_wise(schedule: MaintenanceScheduleEnum) -> None:
    """All 6 enum values are valid for the Protocol field."""
    offer = _ConformingOffer(
        maintenance_schedule=schedule,
        maintenance_custom_days=30 if schedule == MaintenanceScheduleEnum.CUSTOM else None,
    )
    assert isinstance(offer, OfferAdherenceContract)
