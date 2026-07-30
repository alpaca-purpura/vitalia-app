# cap: clinics.lisa.doctores
"""Tests for Doctor domain entity — TDD RED-first.

Domain layer: pure Python, no framework imports.
Tests domain invariants: display_name, BioPublic, AvailabilityBlock validation.
"""

from __future__ import annotations

from datetime import date, time
from uuid import uuid4

import pytest

from src.modules.vitalia.clinics.domain.bio import BioPublic
from src.modules.vitalia.clinics.domain.doctor import Doctor

# ── Doctor entity basics ──────────────────────────────────────────────────────


def _make_doctor(**kwargs: object) -> Doctor:
    defaults = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "clinic_id": uuid4(),
        "first_name": "Ana",
        "last_name": "García",
        "dni": "12345678",
        "email": "ana@clinica.com",
        "phone": "+51987654321",
        "specialty": "Odontología cosmética",
        "credential": "12345",
        "credential_country": "PE",
        "years_experience": 10,
        "languages": ["es", "en"],
        "bio_inputs_notes": None,
        "bio_links": [],
        "bio_public": None,
        "avatar_key": None,
        "visible_en_landing": False,
        "active": True,
    }
    defaults.update(kwargs)
    return Doctor(**defaults)  # type: ignore[arg-type]


def test_doctor_display_name_with_specialty() -> None:
    """display_name returns 'Dr(a). Nombre Apellido'."""
    doctor = _make_doctor(first_name="Ana", last_name="García")
    assert doctor.display_name == "Dra. Ana García"


def test_doctor_display_name_male_specialty() -> None:
    """display_name for male-name returns 'Dr. Nombre Apellido'."""
    doctor = _make_doctor(first_name="Carlos", last_name="Pérez")
    # display_name must be a string starting with 'Dr'
    assert doctor.display_name.startswith("Dr")
    assert "Carlos" in doctor.display_name
    assert "Pérez" in doctor.display_name


def test_doctor_active_by_default() -> None:
    """Doctor is active by default."""
    doctor = _make_doctor()
    assert doctor.active is True


def test_doctor_not_visible_by_default() -> None:
    """Doctor visible_en_landing is False by default."""
    doctor = _make_doctor()
    assert doctor.visible_en_landing is False


def test_doctor_languages_list() -> None:
    """Languages is a list of strings."""
    doctor = _make_doctor(languages=["es", "en", "pt"])
    assert len(doctor.languages) == 3
    assert "es" in doctor.languages


def test_doctor_bio_public_nullable() -> None:
    """bio_public can be None."""
    doctor = _make_doctor(bio_public=None)
    assert doctor.bio_public is None


def test_doctor_bio_public_set() -> None:
    """bio_public can be a BioPublic instance."""
    bio = BioPublic(resumen="Especialista en estética.", formacion="UPCH", enfoque="Blanqueamiento dental.")
    doctor = _make_doctor(bio_public=bio)
    assert doctor.bio_public is not None
    assert doctor.bio_public.resumen == "Especialista en estética."


# ── AvailabilityBlock domain validation ──────────────────────────────────────


def test_availability_block_recurrent_requires_end_condition() -> None:
    """Recurrent block without end condition raises ValueError."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    with pytest.raises(ValueError, match="condicion de fin"):
        AvailabilityBlock(
            id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            doctor_id=uuid4(),
            kind="recurrent",
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(17, 0),
            freq="weekly",
            end_condition_kind=None,  # invalid — must have one
            end_date=None,
            occurrences=None,
            specific_date=None,
        )


def test_availability_block_one_off_requires_specific_date() -> None:
    """One-off block without specific_date raises ValueError."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    with pytest.raises(ValueError, match="one_off"):
        AvailabilityBlock(
            id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            doctor_id=uuid4(),
            kind="one_off",
            day_of_week=None,
            start_time=time(9, 0),
            end_time=time(17, 0),
            freq=None,
            end_condition_kind=None,
            end_date=None,
            occurrences=None,
            specific_date=None,  # invalid
        )


def test_availability_block_start_before_end() -> None:
    """Block where start_time >= end_time raises ValueError."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    with pytest.raises(ValueError, match="start_time"):
        AvailabilityBlock(
            id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            doctor_id=uuid4(),
            kind="one_off",
            day_of_week=None,
            start_time=time(17, 0),
            end_time=time(9, 0),  # before start
            freq=None,
            end_condition_kind=None,
            end_date=None,
            occurrences=None,
            specific_date=date(2026, 6, 15),
        )


def test_availability_block_valid_recurrent_with_end_date() -> None:
    """Valid recurrent block with end_date passes validation."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(17, 0),
        freq="weekly",
        end_condition_kind="end_date",
        end_date=date(2026, 12, 31),
        occurrences=None,
        specific_date=None,
    )
    assert block.kind == "recurrent"
    assert block.end_date == date(2026, 12, 31)


def test_availability_block_valid_recurrent_with_occurrences() -> None:
    """Valid recurrent block with occurrences passes validation."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(17, 0),
        freq="weekly",
        end_condition_kind="occurrences",
        end_date=None,
        occurrences=10,
        specific_date=None,
    )
    assert block.occurrences == 10


def test_availability_block_valid_recurrent_open_ended() -> None:
    """Valid recurrent block with open_ended passes validation."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="recurrent",
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(17, 0),
        freq="weekly",
        end_condition_kind="open_ended",
        end_date=None,
        occurrences=None,
        specific_date=None,
    )
    assert block.end_condition_kind == "open_ended"


def test_availability_block_valid_one_off() -> None:
    """Valid one-off block passes validation."""
    from src.modules.vitalia.clinics.domain.availability_block import AvailabilityBlock

    block = AvailabilityBlock(
        id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        doctor_id=uuid4(),
        kind="one_off",
        day_of_week=None,
        start_time=time(10, 0),
        end_time=time(12, 0),
        freq=None,
        end_condition_kind=None,
        end_date=None,
        occurrences=None,
        specific_date=date(2026, 7, 1),
    )
    assert block.specific_date == date(2026, 7, 1)
