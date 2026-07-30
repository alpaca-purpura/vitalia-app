"""Unit tests — TDD A1: All 8 repositories importable + correct constructor signatures.

Per T-be-3 acceptance:
  A1: All repos importable
  A2: Repo constructor signature (session, tenant_id) enforced
  A3: Arch fitness test extends to repos (covered by test_vitalia_no_query_without_tenant_filter.py)

These are pure-import + attribute tests — no Postgres required.
"""

from __future__ import annotations

import inspect
import uuid

import pytest

# ---------------------------------------------------------------------------
# A1 — All 8 repos importable from their individual files
# ---------------------------------------------------------------------------


def test_booking_repository_importable() -> None:
    """BookingRepository importable."""
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    assert BookingRepository.__name__ == "BookingRepository"


def test_treatment_followup_repository_importable() -> None:
    """TreatmentFollowupRepository importable."""
    from src.modules.vitalia.infrastructure.repositories.treatment_followup_repository import (
        TreatmentFollowupRepository,
    )

    assert TreatmentFollowupRepository.__name__ == "TreatmentFollowupRepository"


def test_consent_repository_importable() -> None:
    """ConsentRepository importable."""
    from src.modules.vitalia.infrastructure.repositories.consent_repository import (
        ConsentRepository,
    )

    assert ConsentRepository.__name__ == "ConsentRepository"


def test_payment_intent_repository_importable() -> None:
    """PaymentIntentRepository importable."""
    from src.modules.vitalia.infrastructure.repositories.payment_intent_repository import (
        PaymentIntentRepository,
    )

    assert PaymentIntentRepository.__name__ == "PaymentIntentRepository"


def test_medical_audit_log_repository_importable() -> None:
    """MedicalAuditLogRepository importable."""
    from src.modules.vitalia.infrastructure.repositories.medical_audit_log_repository import (
        MedicalAuditLogRepository,
    )

    assert MedicalAuditLogRepository.__name__ == "MedicalAuditLogRepository"


def test_doctor_extension_repository_importable() -> None:
    """DoctorExtensionRepository importable."""
    from src.modules.vitalia.infrastructure.repositories.doctor_extension_repository import (
        DoctorExtensionRepository,
    )

    assert DoctorExtensionRepository.__name__ == "DoctorExtensionRepository"


def test_patient_medical_history_repository_importable() -> None:
    """PatientMedicalHistoryRepository importable."""
    from src.modules.vitalia.infrastructure.repositories.patient_medical_history_repository import (
        PatientMedicalHistoryRepository,
    )

    assert PatientMedicalHistoryRepository.__name__ == "PatientMedicalHistoryRepository"


def test_plan_tier_config_repository_importable() -> None:
    """PlanTierConfigRepository importable."""
    from src.modules.vitalia.infrastructure.repositories.plan_tier_repository import (
        PlanTierConfigRepository,
    )

    assert PlanTierConfigRepository.__name__ == "PlanTierConfigRepository"


def test_repositories_package_importable() -> None:
    """All repos importable via the repositories package __init__."""
    from src.modules.vitalia.infrastructure.repositories import (
        BookingRepository,
        ConsentRepository,
        DoctorExtensionRepository,
        MedicalAuditLogRepository,
        PatientMedicalHistoryRepository,
        PaymentIntentRepository,
        PlanTierConfigRepository,
        TreatmentFollowupRepository,
    )

    assert BookingRepository is not None
    assert TreatmentFollowupRepository is not None
    assert ConsentRepository is not None
    assert PaymentIntentRepository is not None
    assert MedicalAuditLogRepository is not None
    assert DoctorExtensionRepository is not None
    assert PatientMedicalHistoryRepository is not None
    assert PlanTierConfigRepository is not None


# ---------------------------------------------------------------------------
# A2 — Constructor signature: (session, tenant_id) for tenant-scoped repos
# ---------------------------------------------------------------------------

_TENANT_SCOPED_REPOS = [
    "src.modules.vitalia.infrastructure.repositories.booking_repository.BookingRepository",
    "src.modules.vitalia.infrastructure.repositories.treatment_followup_repository.TreatmentFollowupRepository",
    "src.modules.vitalia.infrastructure.repositories.consent_repository.ConsentRepository",
    "src.modules.vitalia.infrastructure.repositories.payment_intent_repository.PaymentIntentRepository",
    "src.modules.vitalia.infrastructure.repositories.medical_audit_log_repository.MedicalAuditLogRepository",
    "src.modules.vitalia.infrastructure.repositories.doctor_extension_repository.DoctorExtensionRepository",
]

# PatientMedicalHistoryRepository has get_medical_by_id / get_dental_by_id (dual-model repo)
_DUAL_MODEL_REPOS = [
    "src.modules.vitalia.infrastructure.repositories.patient_medical_history_repository.PatientMedicalHistoryRepository",
]


@pytest.mark.parametrize("repo_path", _TENANT_SCOPED_REPOS)
def test_tenant_scoped_repo_constructor_has_tenant_id(repo_path: str) -> None:
    """Each tenant-scoped repo must accept (session, tenant_id) at construction."""
    module_path, class_name = repo_path.rsplit(".", 1)
    import importlib

    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)

    sig = inspect.signature(cls.__init__)
    params = list(sig.parameters.keys())

    assert "session" in params, f"{class_name}.__init__ must have 'session' parameter"
    assert "tenant_id" in params, f"{class_name}.__init__ must have 'tenant_id' parameter (A2 tenant isolation)"


def test_plan_tier_repo_has_no_tenant_id_in_constructor() -> None:
    """PlanTierConfigRepository must NOT have tenant_id — cross-tenant catalog."""
    from src.modules.vitalia.infrastructure.repositories.plan_tier_repository import (
        PlanTierConfigRepository,
    )

    sig = inspect.signature(PlanTierConfigRepository.__init__)
    params = list(sig.parameters.keys())

    assert "tenant_id" not in params, (
        "PlanTierConfigRepository is a cross-tenant catalog — must NOT have tenant_id param"
    )
    assert "session" in params


# ---------------------------------------------------------------------------
# A2 — get_by_id is present on all tenant-scoped repos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("repo_path", _TENANT_SCOPED_REPOS)
def test_tenant_scoped_repo_has_get_by_id(repo_path: str) -> None:
    """Each repo must expose get_by_id async method."""
    module_path, class_name = repo_path.rsplit(".", 1)
    import importlib

    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)

    assert hasattr(cls, "get_by_id"), f"{class_name} must have get_by_id method"
    assert inspect.iscoroutinefunction(cls.get_by_id), f"{class_name}.get_by_id must be async"


def test_patient_medical_history_repo_has_dual_get_methods() -> None:
    """PatientMedicalHistoryRepository exposes get_medical_by_id + get_dental_by_id.

    This repo manages two models (medical + dental history) hence uses
    prefixed method names instead of a single get_by_id.
    """
    from src.modules.vitalia.infrastructure.repositories.patient_medical_history_repository import (
        PatientMedicalHistoryRepository,
    )

    assert inspect.iscoroutinefunction(PatientMedicalHistoryRepository.get_medical_by_id)
    assert inspect.iscoroutinefunction(PatientMedicalHistoryRepository.get_dental_by_id)
    assert inspect.iscoroutinefunction(PatientMedicalHistoryRepository.save_medical)
    assert inspect.iscoroutinefunction(PatientMedicalHistoryRepository.save_dental)


# ---------------------------------------------------------------------------
# A2 — save is present on all repos
# ---------------------------------------------------------------------------


def test_booking_repo_has_async_save() -> None:
    """BookingRepository must expose async save() method."""
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    assert inspect.iscoroutinefunction(BookingRepository.save)


def test_booking_repo_has_async_soft_delete() -> None:
    """BookingRepository must expose async soft_delete() method."""
    from src.modules.vitalia.infrastructure.repositories.booking_repository import (
        BookingRepository,
    )

    assert inspect.iscoroutinefunction(BookingRepository.soft_delete)


def test_medical_audit_log_repo_has_no_soft_delete() -> None:
    """MedicalAuditLogRepository must NOT have soft_delete — audit log is immutable."""
    from src.modules.vitalia.infrastructure.repositories.medical_audit_log_repository import (
        MedicalAuditLogRepository,
    )

    assert not hasattr(MedicalAuditLogRepository, "soft_delete"), (
        "MedicalAuditLogRepository is append-only — must not expose soft_delete"
    )


def test_plan_tier_repo_has_no_save() -> None:
    """PlanTierConfigRepository must NOT have save — read-only catalog."""
    from src.modules.vitalia.infrastructure.repositories.plan_tier_repository import (
        PlanTierConfigRepository,
    )

    assert not hasattr(PlanTierConfigRepository, "save"), (
        "PlanTierConfigRepository is read-only — must not expose save()"
    )


# ---------------------------------------------------------------------------
# Advisory locks — importable (unit check, no DB needed)
# ---------------------------------------------------------------------------


def test_advisory_locks_module_importable() -> None:
    """advisory_locks module importable with required public functions."""
    from src.modules.vitalia.infrastructure.advisory_locks import (
        _slot_lock_key,
        acquire_slot_advisory_lock,
        release_slot_advisory_lock,
        try_acquire_slot_advisory_lock,
    )

    assert callable(_slot_lock_key)
    assert inspect.iscoroutinefunction(acquire_slot_advisory_lock)
    assert inspect.iscoroutinefunction(try_acquire_slot_advisory_lock)
    assert inspect.iscoroutinefunction(release_slot_advisory_lock)


def test_advisory_lock_key_deterministic_no_db() -> None:
    """_slot_lock_key returns same key for same inputs (no DB needed)."""
    from datetime import datetime, timezone

    from src.modules.vitalia.infrastructure.advisory_locks import _slot_lock_key

    doctor = uuid.uuid4()
    slot = datetime(2026, 10, 1, 9, 0, 0, tzinfo=timezone.utc)

    k1 = _slot_lock_key(doctor_id=doctor, slot_iso=slot)
    k2 = _slot_lock_key(doctor_id=doctor, slot_iso=slot)
    assert k1 == k2
    assert isinstance(k1, int)
    # Must be within signed int64 range
    assert -(2**63) <= k1 < 2**63
