"""TDD unit tests — A1: All 11 models importable + register to Base.metadata.

Per T-be-2 acceptance criterion A1.

These are pure-import tests — no Postgres required.
All 11 SQLAlchemy 2.0 ORM model classes must:
  1. Be importable from their individual module files
  2. Be importable via the package __init__.py
  3. Register their table in Base.metadata.tables
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# A1.1 — Individual model modules importable
# ---------------------------------------------------------------------------


def test_booking_model_importable() -> None:
    """VitaliaBookingModel importable from booking_model.py."""
    from src.modules.vitalia.infrastructure.models.booking_model import (
        VitaliaBookingModel,
    )

    assert VitaliaBookingModel.__tablename__ == "vitalia_bookings"


def test_treatment_followup_model_importable() -> None:
    """VitaliaTreatmentFollowupModel importable."""
    from src.modules.vitalia.infrastructure.models.treatment_followup_model import (
        VitaliaTreatmentFollowupModel,
    )

    assert VitaliaTreatmentFollowupModel.__tablename__ == "vitalia_treatment_followups"


def test_consent_record_model_importable() -> None:
    """VitaliaConsentRecordModel importable."""
    from src.modules.vitalia.infrastructure.models.consent_record_model import (
        VitaliaConsentRecordModel,
    )

    assert VitaliaConsentRecordModel.__tablename__ == "vitalia_consent_records"


def test_medical_audit_log_model_importable() -> None:
    """VitaliaMedicalAuditLogModel importable."""
    from src.modules.vitalia.infrastructure.models.medical_audit_log_model import (
        VitaliaMedicalAuditLogModel,
    )

    assert VitaliaMedicalAuditLogModel.__tablename__ == "vitalia_medical_audit_log"


def test_payment_intent_model_importable() -> None:
    """VitaliaPaymentIntentModel importable."""
    from src.modules.vitalia.infrastructure.models.payment_intent_model import (
        VitaliaPaymentIntentModel,
    )

    assert VitaliaPaymentIntentModel.__tablename__ == "vitalia_payment_intents"


def test_payment_schedule_model_importable() -> None:
    """VitaliaPaymentScheduleModel importable."""
    from src.modules.vitalia.infrastructure.models.payment_schedule_model import (
        VitaliaPaymentScheduleModel,
    )

    assert VitaliaPaymentScheduleModel.__tablename__ == "vitalia_payment_schedules"


def test_adherence_record_model_importable() -> None:
    """VitaliaAdherenceRecordModel importable."""
    from src.modules.vitalia.infrastructure.models.adherence_record_model import (
        VitaliaAdherenceRecordModel,
    )

    assert VitaliaAdherenceRecordModel.__tablename__ == "vitalia_adherence_records"


def test_doctor_extension_model_importable() -> None:
    """VitaliaDoctorExtensionModel importable."""
    from src.modules.vitalia.infrastructure.models.doctor_extension_model import (
        VitaliaDoctorExtensionModel,
    )

    assert VitaliaDoctorExtensionModel.__tablename__ == "vitalia_doctor_extensions"


def test_patient_medical_history_model_importable() -> None:
    """VitaliaPatientMedicalHistoryModel importable."""
    from src.modules.vitalia.infrastructure.models.medical_history_model import (
        VitaliaPatientMedicalHistoryModel,
    )

    assert VitaliaPatientMedicalHistoryModel.__tablename__ == "vitalia_patient_medical_histories"


def test_patient_dental_history_model_importable() -> None:
    """VitaliaPatientDentalHistoryModel importable."""
    from src.modules.vitalia.infrastructure.models.medical_history_model import (
        VitaliaPatientDentalHistoryModel,
    )

    assert VitaliaPatientDentalHistoryModel.__tablename__ == "vitalia_patient_dental_histories"


def test_plan_tier_config_model_importable() -> None:
    """VitaliaPlanTierConfigModel importable."""
    from src.modules.vitalia.infrastructure.models.plan_tier_config_model import (
        VitaliaPlanTierConfigModel,
    )

    assert VitaliaPlanTierConfigModel.__tablename__ == "vitalia_plan_tier_configs"


# ---------------------------------------------------------------------------
# A1.2 — All models importable via package __init__.py
# ---------------------------------------------------------------------------


def test_all_models_importable_via_package() -> None:
    """All 11 model classes importable via models package __init__.py."""
    from src.modules.vitalia.infrastructure.models import (
        VitaliaAdherenceRecordModel,
        VitaliaBookingModel,
        VitaliaConsentRecordModel,
        VitaliaDoctorExtensionModel,
        VitaliaMedicalAuditLogModel,
        VitaliaPatientDentalHistoryModel,
        VitaliaPatientMedicalHistoryModel,
        VitaliaPaymentIntentModel,
        VitaliaPaymentScheduleModel,
        VitaliaPlanTierConfigModel,
        VitaliaTreatmentFollowupModel,
    )

    expected_classes = [
        VitaliaBookingModel,
        VitaliaTreatmentFollowupModel,
        VitaliaConsentRecordModel,
        VitaliaMedicalAuditLogModel,
        VitaliaPaymentIntentModel,
        VitaliaPaymentScheduleModel,
        VitaliaAdherenceRecordModel,
        VitaliaDoctorExtensionModel,
        VitaliaPatientMedicalHistoryModel,
        VitaliaPatientDentalHistoryModel,
        VitaliaPlanTierConfigModel,
    ]
    for cls in expected_classes:
        assert cls is not None, f"{cls} must not be None"


# ---------------------------------------------------------------------------
# A1.3 — All models register their table in Base.metadata
# ---------------------------------------------------------------------------

EXPECTED_TABLES = [
    "vitalia_bookings",
    "vitalia_treatment_followups",
    "vitalia_consent_records",
    "vitalia_medical_audit_log",
    "vitalia_payment_intents",
    "vitalia_payment_schedules",
    "vitalia_adherence_records",
    "vitalia_doctor_extensions",
    "vitalia_patient_medical_histories",
    "vitalia_patient_dental_histories",
    "vitalia_plan_tier_configs",
]


def test_all_11_tables_in_base_metadata() -> None:
    """All 11 vitalia tables must appear in Base.metadata.tables after import."""
    # Force import of all models to register with Base
    from luana_core_platform.domain.base_entity import Base

    import src.modules.vitalia.infrastructure.models  # noqa: F401

    registered = set(Base.metadata.tables.keys())
    for table in EXPECTED_TABLES:
        assert table in registered, (
            f"Table '{table}' not registered in Base.metadata — check that the model class inherits from Base"
        )


def test_exactly_14_vitalia_tables_registered() -> None:
    """Exactly 14 vitalia_ prefixed tables must be registered in Base.metadata.

    T-be-migrations-1 added vitalia_lucas_recommendations (12th table).
    Ratchet updated T-be-services-3 (2026-05-18) to 12.
    Ratchet updated T-4 (2026-05-18) to 14: vitalia_brand_studio_drafts +
    vitalia_onboarding_progress added by prior tickets (brand studio + onboarding).
    """
    from luana_core_platform.domain.base_entity import Base

    import src.modules.vitalia.infrastructure.models  # noqa: F401

    vitalia_tables = {name for name in Base.metadata.tables if name.startswith("vitalia_")}
    assert len(vitalia_tables) == 14, (
        f"Expected 14 vitalia_ tables, got {len(vitalia_tables)}: {sorted(vitalia_tables)}"
    )


# ---------------------------------------------------------------------------
# A1.4 — Verify Base inheritance (not Pydantic BaseEntity)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "model_name,tablename",
    [
        ("VitaliaBookingModel", "vitalia_bookings"),
        ("VitaliaTreatmentFollowupModel", "vitalia_treatment_followups"),
        ("VitaliaConsentRecordModel", "vitalia_consent_records"),
        ("VitaliaMedicalAuditLogModel", "vitalia_medical_audit_log"),
        ("VitaliaPaymentIntentModel", "vitalia_payment_intents"),
        ("VitaliaPaymentScheduleModel", "vitalia_payment_schedules"),
        ("VitaliaAdherenceRecordModel", "vitalia_adherence_records"),
        ("VitaliaDoctorExtensionModel", "vitalia_doctor_extensions"),
        ("VitaliaPatientMedicalHistoryModel", "vitalia_patient_medical_histories"),
        ("VitaliaPatientDentalHistoryModel", "vitalia_patient_dental_histories"),
        ("VitaliaPlanTierConfigModel", "vitalia_plan_tier_configs"),
    ],
)
def test_model_inherits_sqla_base(model_name: str, tablename: str) -> None:
    """Each model must inherit from SQLA Base (not Pydantic BaseModel)."""
    from sqlalchemy.orm import DeclarativeMeta

    import src.modules.vitalia.infrastructure.models as models_pkg

    cls = getattr(models_pkg, model_name)
    # SQLAlchemy 2.0 legacy declarative_base() produces classes with DeclarativeMeta
    assert isinstance(cls, DeclarativeMeta), (
        f"{model_name} must be a SQLAlchemy ORM model class (DeclarativeMeta), not a Pydantic model"
    )
    assert cls.__tablename__ == tablename
