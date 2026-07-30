# cap: configuracion.cuenta
"""RED tests for specialty_catalog — written BEFORE implementation (TDD).

Covers:
  - SPECIALTY_CATALOG is a dict[str, list[SpecialtyEntry]]
  - Keys cover AR, MX, CO, PE, CL, UY + DEFAULT
  - Each entry has id (str), name (str), tier (int 1-3)
  - get_specialties_for_country() returns list for known country
  - get_specialties_for_country() falls back to DEFAULT for unknown country
  - Names are Spanish neutro (no voseo markers)
  - No duplicate ids within a country
"""

from __future__ import annotations

from src.modules.vitalia._shared.catalogs.specialty_catalog import (
    SPECIALTY_CATALOG,
    SpecialtyEntry,
    get_specialties_for_country,
)

SUPPORTED_COUNTRIES = ["AR", "MX", "CO", "PE", "CL", "UY"]


def test_catalog_has_all_supported_countries() -> None:
    """Catalog must include all 6 target LatAm countries + DEFAULT."""
    for country in SUPPORTED_COUNTRIES:
        assert country in SPECIALTY_CATALOG, f"Missing country: {country}"
    assert "DEFAULT" in SPECIALTY_CATALOG


def test_each_country_has_non_empty_list() -> None:
    for country in SUPPORTED_COUNTRIES + ["DEFAULT"]:
        entries = SPECIALTY_CATALOG[country]
        assert len(entries) > 0, f"Empty specialty list for {country}"


def test_entries_are_specialty_entry_instances() -> None:
    for country, entries in SPECIALTY_CATALOG.items():
        for e in entries:
            assert isinstance(e, SpecialtyEntry), f"{country}: not SpecialtyEntry: {e}"


def test_entries_have_required_fields() -> None:
    for country, entries in SPECIALTY_CATALOG.items():
        for e in entries:
            assert e.id, f"{country}: empty id"
            assert e.name, f"{country}: empty name"
            assert e.tier in (1, 2, 3), f"{country}: invalid tier {e.tier}"


def test_no_duplicate_ids_per_country() -> None:
    for country, entries in SPECIALTY_CATALOG.items():
        ids = [e.id for e in entries]
        assert len(ids) == len(set(ids)), f"{country}: duplicate specialty ids"


def test_get_specialties_for_known_country() -> None:
    for country in SUPPORTED_COUNTRIES:
        result = get_specialties_for_country(country)
        assert isinstance(result, list)
        assert len(result) > 0


def test_get_specialties_fallback_to_default() -> None:
    """Unknown country returns DEFAULT catalog."""
    result = get_specialties_for_country("ZZ")
    default = SPECIALTY_CATALOG["DEFAULT"]
    assert result == default


def test_get_specialties_case_insensitive() -> None:
    """Country code is normalized to uppercase."""
    upper = get_specialties_for_country("AR")
    lower = get_specialties_for_country("ar")
    assert upper == lower


def test_tier1_specialties_include_dental_aesthetic() -> None:
    """Tier 1 must include odontología cosmética / estética (vitalia's MVP verticals)."""
    for country in SUPPORTED_COUNTRIES:
        entries = get_specialties_for_country(country)
        tier1 = [e for e in entries if e.tier == 1]
        names_lower = [e.name.lower() for e in tier1]
        has_dental_or_estetica = any(
            "dental" in n or "estética" in n or "estetica" in n or "odontolog" in n for n in names_lower
        )
        assert has_dental_or_estetica, f"{country}: no Tier 1 dental/estética specialty"


def test_no_voseo_in_names() -> None:
    """Specialty names must use Spanish neutro (no voseo imperatives)."""
    voseo_markers = ["vos", "tenés", "podés", "hacé", "mirá"]
    for country, entries in SPECIALTY_CATALOG.items():
        for e in entries:
            name_lower = e.name.lower()
            for marker in voseo_markers:
                assert marker not in name_lower, f"{country}.{e.id}: voseo in name: {e.name}"
