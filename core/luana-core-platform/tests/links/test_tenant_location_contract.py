"""Contract tests for ``TenantLocationContract`` Protocol.

Added 2026-05-17 via promotion proposal
``docs/promotion-protocol/proposals/2026-05-17-platform-tenants-location-columns.md``.

Validates:
  - Protocol shape (runtime_checkable)
  - Conforming implementations pass isinstance check
  - Non-conforming implementations fail isinstance check
  - Optional fields accept None
"""

from __future__ import annotations

import pytest
from luana_core_platform.links.ports.tenant_profile import TenantLocationContract


class _ConformingTenant:
    """Minimal class that conforms to TenantLocationContract."""

    def __init__(
        self,
        is_onboarded: bool = False,
        location_country: str | None = None,
        location_city: str | None = None,
        timezone: str | None = None,
    ) -> None:
        self.is_onboarded = is_onboarded
        self.location_country = location_country
        self.location_city = location_city
        self.timezone = timezone


class _MissingTimezoneTenant:
    """Missing ``timezone`` field — should fail Protocol check."""

    def __init__(self) -> None:
        self.is_onboarded = True
        self.location_country = "AR"
        self.location_city = "Buenos Aires"


def test_conforming_tenant_passes_isinstance_check() -> None:
    """Tenant with all 4 fields satisfies the Protocol."""
    tenant = _ConformingTenant(
        is_onboarded=True,
        location_country="AR",
        location_city="Buenos Aires",
        timezone="America/Argentina/Buenos_Aires",
    )
    assert isinstance(tenant, TenantLocationContract)


def test_conforming_tenant_with_optional_nulls_passes() -> None:
    """Optional fields (country/city/timezone) accept ``None``."""
    tenant = _ConformingTenant(is_onboarded=False)
    assert isinstance(tenant, TenantLocationContract)
    assert tenant.location_country is None
    assert tenant.location_city is None
    assert tenant.timezone is None


def test_non_conforming_tenant_fails_isinstance_check() -> None:
    """Tenant missing ``timezone`` field is not recognized as protocol member."""
    tenant = _MissingTimezoneTenant()
    assert not isinstance(tenant, TenantLocationContract)


@pytest.mark.parametrize(
    "country_code,timezone",
    [
        ("AR", "America/Argentina/Buenos_Aires"),
        ("PE", "America/Lima"),
        ("MX", "America/Mexico_City"),
        ("CO", "America/Bogota"),
        ("CL", "America/Santiago"),
        ("BR", "America/Sao_Paulo"),
        ("US", "America/New_York"),
        ("ES", "Europe/Madrid"),
    ],
)
def test_iso_3166_country_codes_accepted(country_code: str, timezone: str) -> None:
    """ISO 3166-1 alpha-2 country codes + IANA timezones are accepted shape-wise."""
    tenant = _ConformingTenant(
        is_onboarded=True,
        location_country=country_code,
        location_city="any-city",
        timezone=timezone,
    )
    assert isinstance(tenant, TenantLocationContract)
    assert len(tenant.location_country) == 2
