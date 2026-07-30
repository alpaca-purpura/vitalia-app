"""Unit tests — Patient DTOs PII masking (T-be-7 A4).

A4 acceptance criterion: Patient PII masked in response (phone/email).

Per 03-arch-be.md § 7.2:
  - name_last_initial: last name 1 char only "G." per HIPAA-lite.
  - phone_masked: "+54***5555".
  - email_masked: "j***@***.com".
  - Full name/phone/email NOT in DTO field allowlist.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.modules.vitalia.api.dtos.treatment_dtos import (
    PatientDetailResponse,
    PatientSummary,
)


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class TestPatientSummaryPiiMask:
    """PatientSummary — PII allowlist verification."""

    def test_pii_masked_phone_field_name(self) -> None:
        """phone_masked field exposed (not full phone)."""
        model_fields = PatientSummary.model_fields
        assert "phone_masked" in model_fields, "phone_masked field must exist in PatientSummary"
        assert "phone" not in model_fields, "raw 'phone' field must NOT exist in PatientSummary (PII)"

    def test_pii_masked_email_field_name(self) -> None:
        """email_masked field exposed (not full email)."""
        model_fields = PatientSummary.model_fields
        assert "email_masked" in model_fields, "email_masked field must exist in PatientSummary"
        assert "email" not in model_fields, "raw 'email' field must NOT exist in PatientSummary (PII)"

    def test_name_last_initial_field_exists(self) -> None:
        """name_last_initial (not full last name) in PatientSummary."""
        model_fields = PatientSummary.model_fields
        assert "name_last_initial" in model_fields, "name_last_initial must exist"
        assert "name_last" not in model_fields, "raw 'name_last' must NOT exist (PII)"
        assert "last_name" not in model_fields, "raw 'last_name' must NOT exist (PII)"

    def test_patient_summary_instantiation_with_masked_pii(self) -> None:
        """PatientSummary can be instantiated with masked PII values."""
        patient = PatientSummary(
            id=uuid4(),
            name_first="Juan",
            name_last_initial="G.",
            phone_masked="+54***5555",
            email_masked="j***@***.com",
            clinic_type="dental",
            created_at=_utc_now(),
        )
        assert patient.name_last_initial == "G."
        assert patient.phone_masked == "+54***5555"
        assert patient.email_masked == "j***@***.com"

    def test_patient_summary_serialization_excludes_raw_pii(self) -> None:
        """JSON serialization of PatientSummary does not contain raw PII field names."""
        patient = PatientSummary(
            id=uuid4(),
            name_first="María",
            name_last_initial="R.",
            phone_masked="+56***1234",
            email_masked="m***@***.com",
            clinic_type="psychology",
            created_at=_utc_now(),
        )
        serialized = patient.model_dump()
        assert "phone" not in serialized, "raw 'phone' must NOT appear in serialized output"
        assert "email" not in serialized, "raw 'email' must NOT appear in serialized output"
        assert "name_last" not in serialized, "raw 'name_last' must NOT appear in serialized output"
        assert "phone_masked" in serialized
        assert "email_masked" in serialized
        assert "name_last_initial" in serialized


class TestPatientDetailResponsePiiMask:
    """PatientDetailResponse — deeper PII allowlist verification."""

    def test_pii_masked_fields_exist(self) -> None:
        """PatientDetailResponse exposes masked PII fields only."""
        model_fields = PatientDetailResponse.model_fields
        assert "phone_masked" in model_fields
        assert "email_masked" in model_fields
        assert "name_last_initial" in model_fields

    def test_raw_pii_fields_absent(self) -> None:
        """Raw PII fields must NOT exist in PatientDetailResponse."""
        model_fields = PatientDetailResponse.model_fields
        forbidden = ["phone", "email", "name_last", "last_name", "full_name", "ssn", "dni", "rut"]
        for field in forbidden:
            assert field not in model_fields, (
                f"Field '{field}' must NOT be in PatientDetailResponse — PII rule "
                "(Tessl pii-sanitisation.md + 03-arch-be.md § 7.2)"
            )

    def test_medical_history_summary_field_exists(self) -> None:
        """medical_history_summary is clinically relevant — allowed verbatim."""
        model_fields = PatientDetailResponse.model_fields
        assert "medical_history_summary" in model_fields, (
            "medical_history_summary must be present (clinically relevant per 05-guidelines § 1.6)"
        )

    def test_patient_detail_instantiation(self) -> None:
        """PatientDetailResponse can be instantiated with valid masked data."""
        now = _utc_now()
        detail = PatientDetailResponse(
            id=uuid4(),
            name_first="Ana",
            name_last_initial="C.",
            phone_masked="+52***9999",
            email_masked="a***@***.com",
            medical_history_summary="Paciente con ansiedad leve. Sin alergias conocidas.",
            clinic_type="psychology",
            created_at=now,
            updated_at=now,
        )
        assert detail.name_last_initial == "C."
        assert detail.medical_history_summary is not None


class TestBookingDtosPiiAllowlist:
    """Booking DTOs — patient PII not in responses."""

    def test_create_booking_response_no_patient_pii(self) -> None:
        """CreateBookingResponse exposes only patient_id UUID (no name/phone/email)."""
        from src.modules.vitalia.api.dtos.booking_dtos import CreateBookingResponse

        model_fields = CreateBookingResponse.model_fields
        forbidden = ["patient_name", "patient_phone", "patient_email", "phone", "email"]
        for field in forbidden:
            assert field not in model_fields, f"Field '{field}' must NOT be in CreateBookingResponse (PII rule)"
        # booking_id is allowed (UUID, not PII)
        assert "booking_id" in model_fields

    def test_booking_response_currency_field_not_hardcoded(self) -> None:
        """CreateBookingResponse.currency is Optional (not hardcoded 'USD')."""
        from src.modules.vitalia.api.dtos.booking_dtos import CreateBookingResponse

        # currency field must exist as Optional (str | None)
        field = CreateBookingResponse.model_fields.get("currency")
        assert field is not None, "currency field must exist"
        # Default must be None (not 'USD')
        assert field.default is None, "currency default must be None — NEVER hardcode 'USD' (currency-handling.md)"


class TestComplianceDtosPiiAllowlist:
    """Compliance DTOs — payload_redacted only (pre-sanitized)."""

    def test_compliance_event_item_payload_is_redacted(self) -> None:
        """ComplianceEventItem only exposes payload_redacted (no raw payload)."""
        from src.modules.vitalia.api.dtos.compliance_dtos import ComplianceEventItem

        model_fields = ComplianceEventItem.model_fields
        assert "payload_redacted" in model_fields, "payload_redacted must be present"
        assert "payload" not in model_fields, "raw 'payload' must NOT exist (PII)"
        assert "raw_payload" not in model_fields, "raw_payload must NOT exist (PII)"
