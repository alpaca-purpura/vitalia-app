"""RED tests — ComplianceServiceAdapter: channel guard + PHI sanitization.

TDD: RED first per T-infra-3.
Verifies:
  1. WhatsApp free channel blocked for PHI (BlockedChannelError raised).
  2. sanitize_phi_payload omits all 22 canonical PHI fields.
"""

from __future__ import annotations

from uuid import uuid4

import pytest


def _import_adapter():
    from src.modules.vitalia.compliance.application.compliance_service_adapter import (  # noqa: PLC0415
        BlockedChannelError,
        VitaliaComplianceAdapter,
    )

    return VitaliaComplianceAdapter, BlockedChannelError


def _import_sanitize():
    from src.modules.vitalia.compliance.application.compliance_service_adapter import (  # noqa: PLC0415
        sanitize_phi_payload,
    )

    return sanitize_phi_payload


class TestVitaliaComplianceAdapterChannelGuard:
    """validate_outbound_message must block PHI on unencrypted channels."""

    def test_adapter_importable(self) -> None:
        """VitaliaComplianceAdapter must be importable."""
        VitaliaComplianceAdapter, _ = _import_adapter()
        assert VitaliaComplianceAdapter is not None

    def test_blocked_channel_error_importable(self) -> None:
        """BlockedChannelError must be importable from adapter module."""
        _, BlockedChannelError = _import_adapter()
        assert BlockedChannelError is not None

    def test_whatsapp_free_blocked_for_phi(self) -> None:
        """validate_outbound_message must raise BlockedChannelError for whatsapp_free channel."""
        VitaliaComplianceAdapter, BlockedChannelError = _import_adapter()

        adapter = VitaliaComplianceAdapter()
        with pytest.raises(BlockedChannelError):
            adapter.validate_outbound_message(
                message="Diagnóstico: hipertensión grado II",
                channel="whatsapp_free",
                tenant_id=uuid4(),
            )

    def test_sms_blocked_for_phi(self) -> None:
        """validate_outbound_message must raise BlockedChannelError for sms channel."""
        VitaliaComplianceAdapter, BlockedChannelError = _import_adapter()

        adapter = VitaliaComplianceAdapter()
        with pytest.raises(BlockedChannelError):
            adapter.validate_outbound_message(
                message="Resultado de laboratorio: glucosa 126 mg/dL",
                channel="sms",
                tenant_id=uuid4(),
            )

    def test_secure_portal_channel_not_blocked(self) -> None:
        """validate_outbound_message must NOT raise for portal_secure channel."""
        VitaliaComplianceAdapter, BlockedChannelError = _import_adapter()

        adapter = VitaliaComplianceAdapter()
        # Must not raise
        result = adapter.validate_outbound_message(
            message="Diagnóstico: hipertensión grado II",
            channel="portal_secure",
            tenant_id=uuid4(),
        )
        assert result is True or result is None  # allowed — any truthy/None return OK

    def test_blocked_channel_error_contains_channel_info(self) -> None:
        """BlockedChannelError must include the blocked channel name in its message."""
        VitaliaComplianceAdapter, BlockedChannelError = _import_adapter()

        adapter = VitaliaComplianceAdapter()
        with pytest.raises(BlockedChannelError) as exc_info:
            adapter.validate_outbound_message(
                message="Tratamiento: metformina 850mg",
                channel="whatsapp_free",
                tenant_id=uuid4(),
            )
        assert "whatsapp_free" in str(exc_info.value).lower() or "whatsapp" in str(exc_info.value).lower()


class TestSanitizePhiPayload:
    """sanitize_phi_payload must strip all 22 canonical PHI fields."""

    def test_sanitize_phi_payload_importable(self) -> None:
        """sanitize_phi_payload must be importable."""
        sanitize_phi_payload = _import_sanitize()
        assert sanitize_phi_payload is not None

    def test_patient_name_redacted(self) -> None:
        """patient.name must be redacted from payload."""
        sanitize_phi_payload = _import_sanitize()
        payload = {"patient": {"name": "María García", "age": 45}}
        result = sanitize_phi_payload(payload)
        # patient.name must be redacted
        if "patient" in result and isinstance(result["patient"], dict):
            assert result["patient"].get("name") != "María García"

    def test_diagnosis_redacted(self) -> None:
        """diagnosis field must be redacted."""
        sanitize_phi_payload = _import_sanitize()
        payload = {"diagnosis": "Diabetes mellitus tipo 2", "appointment_id": "abc-123"}
        result = sanitize_phi_payload(payload)
        assert result.get("diagnosis") != "Diabetes mellitus tipo 2"

    def test_non_phi_fields_preserved(self) -> None:
        """Non-PHI fields must be preserved."""
        sanitize_phi_payload = _import_sanitize()
        payload = {
            "appointment_id": "abc-123",
            "tenant_id": "tenant-x",
            "diagnosis": "Hipertensión",
        }
        result = sanitize_phi_payload(payload)
        assert result.get("appointment_id") == "abc-123"
        assert result.get("tenant_id") == "tenant-x"

    def test_all_22_phi_fields_redacted(self) -> None:
        """All 22 canonical PHI fields must be absent or redacted after sanitization."""
        sanitize_phi_payload = _import_sanitize()

        # Build a payload with all top-level PHI fields from hipaa-lite.md
        phi_fields = [
            "diagnosis",
            "treatment_plan",
            "medication",
            "dosage",
            "allergies",
            "symptoms",
            "medical_notes",
            "lab_results",
            "vital_signs",
            "imaging_url",
            "xray_filename",
            "ultrasound_report",
            "previous_treatments",
            "family_history",
            "surgical_history",
        ]
        payload: dict = {field: f"sensitive-value-{field}" for field in phi_fields}
        payload["appointment_id"] = "keep-this"

        result = sanitize_phi_payload(payload)

        for field in phi_fields:
            assert result.get(field) != f"sensitive-value-{field}", (
                f"PHI field '{field}' was not redacted by sanitize_phi_payload"
            )
        # Non-PHI must remain
        assert result.get("appointment_id") == "keep-this"

    def test_nested_patient_phi_fields_redacted(self) -> None:
        """Nested patient.* PHI fields must be redacted."""
        sanitize_phi_payload = _import_sanitize()
        payload = {
            "patient": {
                "name": "Juan López",
                "dni": "12345678",
                "cuit": "20-12345678-3",
                "date_of_birth": "1980-05-20",
                "phone": "+54 11 5555-1234",
                "email": "juan.lopez@email.com",
                "address": "Av. Corrientes 1234",
            },
            "clinic_id": "clinic-abc",
        }
        result = sanitize_phi_payload(payload)

        # clinic_id must remain
        assert result.get("clinic_id") == "clinic-abc"

        # patient PHI fields must be redacted
        patient = result.get("patient", {})
        for phi_field in ["name", "dni", "cuit", "date_of_birth", "phone", "email", "address"]:
            assert patient.get(phi_field) != payload["patient"][phi_field], f"patient.{phi_field} was not redacted"
