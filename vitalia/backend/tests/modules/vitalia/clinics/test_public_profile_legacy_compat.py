# cap: clinics.lisa.doctores
"""Regression RED-first (audit DELTA-BE 2026-06-12): legacy bio_public blob compat.

La migración 041 backfillea ``public_profile = bio_public`` VERBATIM — el JSONB
backfilleado tiene la forma legacy 3-blob ``{resumen, formacion: str, enfoque}``,
NO la estructurada ``{sobre_mi, formacion: list[dict], ...}``.

Contrato ratificado (03-arch-delta § 6.1):
  - ``public_profile.sobre_mi ← bio_public.resumen``
  - ``formacion ← [{titulo: bio_public.formacion, institucion: '', anio: null}]``

Bugs cazados por esta batería (antes del fix en DoctorPublicProfile.from_dict):
  1. ``from_dict`` leía ``data['formacion']`` (str legacy) y lo tipaba list[dict]
     → doctors_router._to_public_profile_dto iteraba el STRING char por char →
     N FormacionItemDTO vacíos basura en DoctorDetailDTO.
  2. El contenido legacy (resumen) quedaba INVISIBLE en la página pública
     (sobre_mi=None) pese al backfill ratificado por el arch.
"""

from __future__ import annotations

from src.modules.vitalia.clinics.domain.public_profile import DoctorPublicProfile

# ── Legacy 3-blob shape (post-041 backfill) ──────────────────────────────────


def test_from_dict_legacy_blob_maps_resumen_to_sobre_mi() -> None:
    """Legacy {resumen, formacion str, enfoque} → sobre_mi ← resumen (arch § 6.1)."""
    legacy = {
        "resumen": "Dra. con 10 años de experiencia en implantes.",
        "formacion": "Odontóloga UPCH 2008",
        "enfoque": "Trato cálido",
    }
    profile = DoctorPublicProfile.from_dict(legacy)

    assert profile is not None
    assert profile.sobre_mi == "Dra. con 10 años de experiencia en implantes."


def test_from_dict_legacy_blob_wraps_formacion_string_as_single_item() -> None:
    """Legacy formacion str → [{titulo: blob, institucion: '', anio: None}] (arch § 6.1).

    institucion '' (no None): FormacionItemDTO.institucion tipa str requerido —
    un None rompería la validación Pydantic en el GET.
    """
    legacy = {"resumen": None, "formacion": "Odontóloga UPCH 2008", "enfoque": None}
    profile = DoctorPublicProfile.from_dict(legacy)

    assert profile is not None
    assert profile.formacion == [{"titulo": "Odontóloga UPCH 2008", "institucion": "", "anio": None}]
    assert all(isinstance(item, dict) for item in profile.formacion)


def test_from_dict_legacy_blob_never_iterates_string_as_items() -> None:
    """El blob legacy JAMÁS produce un item por carácter (bug router _to_public_profile_dto)."""
    legacy = {"resumen": "R", "formacion": "Texto largo de formación académica", "enfoque": "E"}
    profile = DoctorPublicProfile.from_dict(legacy)

    assert profile is not None
    assert len(profile.formacion) <= 1, (
        f"formacion legacy debe colapsar a ≤1 item estructurado, got {len(profile.formacion)}"
    )


def test_from_dict_legacy_blob_empty_formacion_string_gives_empty_list() -> None:
    """Legacy con formacion vacía/None → formacion = [] (sin items fantasma)."""
    assert DoctorPublicProfile.from_dict({"resumen": "R", "formacion": None, "enfoque": None}).formacion == []  # type: ignore[union-attr]
    assert DoctorPublicProfile.from_dict({"resumen": "R", "formacion": "  ", "enfoque": None}).formacion == []  # type: ignore[union-attr]


# ── Type-hardening del shape estructurado ────────────────────────────────────


def test_from_dict_structured_hardens_non_list_sections() -> None:
    """Secciones con tipo inesperado → lista vacía (nunca str/int crudo tipado como list)."""
    malformed = {
        "sobre_mi": "Texto válido",
        "formacion": "esto-no-es-lista",
        "experiencia": 42,
        "tratamientos": {"k": "v"},
        "certificaciones": None,
        "idiomas": "es",
    }
    profile = DoctorPublicProfile.from_dict(malformed)

    assert profile is not None
    assert profile.sobre_mi == "Texto válido"
    assert profile.formacion == []
    assert profile.experiencia == []
    assert profile.tratamientos == []
    assert profile.certificaciones == []
    assert profile.idiomas == []


def test_from_dict_structured_shape_roundtrips_unchanged() -> None:
    """El shape estructurado canónico pasa intacto (no regresión del path normal)."""
    structured = {
        "sobre_mi": "Especialista en cirugía oral.",
        "formacion": [{"titulo": "Cirujano", "institucion": "UPCH", "anio": 2005}],
        "experiencia": [{"puesto": "Jefe", "lugar": "Aurora", "anios": 4}],
        "tratamientos": ["Cirugía oral"],
        "certificaciones": ["Colegiatura 12345 (PE)"],
        "idiomas": ["Español", "Inglés"],
    }
    profile = DoctorPublicProfile.from_dict(structured)

    assert profile is not None
    assert profile.sobre_mi == "Especialista en cirugía oral."
    assert profile.formacion == structured["formacion"]
    assert profile.experiencia == structured["experiencia"]
    assert profile.tratamientos == ["Cirugía oral"]
    assert profile.certificaciones == ["Colegiatura 12345 (PE)"]
    assert profile.idiomas == ["Español", "Inglés"]


def test_from_dict_none_and_empty_still_return_none() -> None:
    """Contrato existente: None / {} → None (no regresión)."""
    assert DoctorPublicProfile.from_dict(None) is None
    assert DoctorPublicProfile.from_dict({}) is None
