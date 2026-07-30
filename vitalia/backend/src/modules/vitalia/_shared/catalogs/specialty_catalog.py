# cap: configuracion.cuenta
"""Specialty catalog for Vitalia LatAm — pure Python, no framework imports.

Provides per-country specialty lists for the clinic account configuration
(primary_specialties selector). Each entry has:
  - id: URL-safe slug used in config_json
  - name: Display name in Spanish neutro LatAm (no voseo)
  - tier: 1=MVP vertical, 2=Tier 2 (6-12m), 3=Tier 3 (12-24m)

Tier 1 (MVP): dental cosmético, medicina estética, oftalmología refractiva
Tier 2: psicología, psiquiatría, dermatología, nutrición clínica
Tier 3: fisioterapia, capilar, fertilidad

Fallback: unsupported countries use DEFAULT catalog (pan-LatAm neutral).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpecialtyEntry:
    """A single specialty catalog entry.

    Attributes:
        id: URL-safe slug identifier.
        name: Display name in Spanish neutro LatAm.
        tier: Vitalia tier (1=MVP, 2=6-12m, 3=12-24m).
    """

    id: str
    name: str
    tier: int


# ---------------------------------------------------------------------------
# Base Tier 1-3 entries (shared across LatAm countries)
# ---------------------------------------------------------------------------

_TIER1: list[SpecialtyEntry] = [
    SpecialtyEntry("odontologia-estetica", "Odontología estética", 1),
    SpecialtyEntry("medicina-estetica", "Medicina estética", 1),
    SpecialtyEntry("oftalmologia-refractiva", "Oftalmología refractiva", 1),
]

_TIER2: list[SpecialtyEntry] = [
    SpecialtyEntry("psicologia", "Psicología", 2),
    SpecialtyEntry("psiquiatria", "Psiquiatría", 2),
    SpecialtyEntry("dermatologia", "Dermatología", 2),
    SpecialtyEntry("nutricion-clinica", "Nutrición clínica", 2),
]

_TIER3: list[SpecialtyEntry] = [
    SpecialtyEntry("fisioterapia", "Fisioterapia", 3),
    SpecialtyEntry("medicina-capilar", "Medicina capilar", 3),
    SpecialtyEntry("fertilidad", "Fertilidad", 3),
]

_BASE_CATALOG = _TIER1 + _TIER2 + _TIER3


# ---------------------------------------------------------------------------
# Per-country extensions (locale-specific specialties)
# ---------------------------------------------------------------------------

_AR_EXTRAS: list[SpecialtyEntry] = [
    SpecialtyEntry("odontologia-general", "Odontología general", 1),
    SpecialtyEntry("cardiologia-preventiva", "Cardiología preventiva", 2),
    SpecialtyEntry("ginecologia-estetica", "Ginecología estética", 2),
]

_MX_EXTRAS: list[SpecialtyEntry] = [
    SpecialtyEntry("odontologia-general", "Odontología general", 1),
    SpecialtyEntry("medicina-anti-envejecimiento", "Medicina antienvejecimiento", 2),
    SpecialtyEntry("cirugia-plastica", "Cirugía plástica", 2),
]

_CO_EXTRAS: list[SpecialtyEntry] = [
    SpecialtyEntry("odontologia-general", "Odontología general", 1),
    SpecialtyEntry("cirugia-estetica", "Cirugía estética", 2),
]

_PE_EXTRAS: list[SpecialtyEntry] = [
    SpecialtyEntry("odontologia-general", "Odontología general", 1),
    SpecialtyEntry("traumatologia-deportiva", "Traumatología deportiva", 2),
]

_CL_EXTRAS: list[SpecialtyEntry] = [
    SpecialtyEntry("odontologia-general", "Odontología general", 1),
    SpecialtyEntry("kinesiologia", "Kinesiología", 2),
]

_UY_EXTRAS: list[SpecialtyEntry] = [
    SpecialtyEntry("odontologia-general", "Odontología general", 1),
    SpecialtyEntry("psicomotricidad", "Psicomotricidad", 3),
]


# ---------------------------------------------------------------------------
# SPECIALTY_CATALOG — public SSoT dict
# ---------------------------------------------------------------------------

SPECIALTY_CATALOG: dict[str, list[SpecialtyEntry]] = {
    "AR": _BASE_CATALOG + _AR_EXTRAS,
    "MX": _BASE_CATALOG + _MX_EXTRAS,
    "CO": _BASE_CATALOG + _CO_EXTRAS,
    "PE": _BASE_CATALOG + _PE_EXTRAS,
    "CL": _BASE_CATALOG + _CL_EXTRAS,
    "UY": _BASE_CATALOG + _UY_EXTRAS,
    "DEFAULT": _BASE_CATALOG,
}


def get_specialties_for_country(country: str) -> list[SpecialtyEntry]:
    """Return specialty list for a country code.

    Falls back to DEFAULT for unknown/unsupported countries.

    Args:
        country: ISO 3166-1 alpha-2 country code (case-insensitive).

    Returns:
        List of SpecialtyEntry for the country, or DEFAULT if unknown.
    """
    return SPECIALTY_CATALOG.get(country.upper(), SPECIALTY_CATALOG["DEFAULT"])


class SpecialtyValidationError(ValueError):
    """A submitted specialty id is not in the country's catalog (RN-3/AC-4b)."""

    def __init__(self, invalid_ids: list[str], country: str) -> None:
        self.field = "primary_specialties"
        self.invalid_ids = invalid_ids
        self.message = f"Especialidades fuera del catálogo de {country.upper()}: {', '.join(invalid_ids)}"
        super().__init__(self.message)


def validate_specialties(specialty_ids: list[str], country: str) -> None:
    """Validate that every submitted specialty id exists in the country catalog.

    Persisted strings are the catalog entry *ids* (URL-safe slugs in
    config_json.clinic_config.primary_specialties).

    Raises:
        SpecialtyValidationError: any id not in the country's catalog (→ 422).
    """
    valid_ids = {entry.id for entry in get_specialties_for_country(country)}
    invalid = [s for s in specialty_ids if s not in valid_ids]
    if invalid:
        raise SpecialtyValidationError(invalid, country)
