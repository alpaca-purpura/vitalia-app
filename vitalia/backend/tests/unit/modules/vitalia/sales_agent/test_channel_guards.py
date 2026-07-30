"""RED tests — Channel guards (MedicalResultsChannelGuard + WhatsAppFreePhiGuard).

TDD per .claude/rules/tdd-mandatory.md + hipaa-lite.md § Voice patterns.

Tests verify:
- MedicalResultsChannelGuard raises BlockedChannelError for unencrypted channels
- WhatsAppFreePhiGuard blocks PHI field names in WhatsApp free messages
- Both guards are importable from compliance/guardrails
- Guards use VitaliaComplianceAdapter (no mirror of ComplianceService)
"""

from __future__ import annotations

from uuid import uuid4

import pytest

TENANT_ID = uuid4()


class TestMedicalResultsChannelGuard:
    """Tests for MedicalResultsChannelGuard — per hipaa-lite voice patterns."""

    def test_import_guard(self) -> None:
        """Guard importable from compliance guardrails."""
        from src.modules.vitalia.compliance.guardrails.medical_results_guard import (
            MedicalResultsChannelGuard,
        )

        assert MedicalResultsChannelGuard is not None

    def test_blocks_whatsapp_free_channel(self) -> None:
        """whatsapp_free channel raises BlockedChannelError — unencrypted."""
        from src.modules.vitalia.compliance.application.compliance_service_adapter import (
            BlockedChannelError,
        )
        from src.modules.vitalia.compliance.guardrails.medical_results_guard import (
            MedicalResultsChannelGuard,
        )

        guard = MedicalResultsChannelGuard()
        with pytest.raises(BlockedChannelError) as exc_info:
            guard.validate(message="Tu resultado es positivo", channel="whatsapp_free")
        assert "whatsapp_free" in str(exc_info.value)

    def test_blocks_sms_channel(self) -> None:
        """SMS channel raises BlockedChannelError — unencrypted."""
        from src.modules.vitalia.compliance.application.compliance_service_adapter import (
            BlockedChannelError,
        )
        from src.modules.vitalia.compliance.guardrails.medical_results_guard import (
            MedicalResultsChannelGuard,
        )

        guard = MedicalResultsChannelGuard()
        with pytest.raises(BlockedChannelError):
            guard.validate(message="Resultados listos", channel="sms")

    def test_blocks_email_plaintext_channel(self) -> None:
        """email_plaintext channel raises BlockedChannelError — unencrypted."""
        from src.modules.vitalia.compliance.application.compliance_service_adapter import (
            BlockedChannelError,
        )
        from src.modules.vitalia.compliance.guardrails.medical_results_guard import (
            MedicalResultsChannelGuard,
        )

        guard = MedicalResultsChannelGuard()
        with pytest.raises(BlockedChannelError):
            guard.validate(message="Resultados clínicos", channel="email_plaintext")

    def test_allows_portal_secure_channel(self) -> None:
        """portal_secure channel passes validation — encrypted."""
        from src.modules.vitalia.compliance.guardrails.medical_results_guard import (
            MedicalResultsChannelGuard,
        )

        guard = MedicalResultsChannelGuard()
        # Should not raise
        result = guard.validate(message="Puedes ver tus resultados", channel="portal_secure")
        assert result is True

    def test_allows_whatsapp_business_encrypted(self) -> None:
        """whatsapp_business_encrypted channel passes — end-to-end encrypted."""
        from src.modules.vitalia.compliance.guardrails.medical_results_guard import (
            MedicalResultsChannelGuard,
        )

        guard = MedicalResultsChannelGuard()
        result = guard.validate(message="Tu cita fue confirmada", channel="whatsapp_business_encrypted")
        assert result is True

    def test_portal_redirect_message_hint(self) -> None:
        """BlockedChannelError message includes portal redirect text (Spanish neutro)."""
        from src.modules.vitalia.compliance.application.compliance_service_adapter import (
            BlockedChannelError,
        )
        from src.modules.vitalia.compliance.guardrails.medical_results_guard import (
            MedicalResultsChannelGuard,
        )

        guard = MedicalResultsChannelGuard()
        with pytest.raises(BlockedChannelError) as exc_info:
            guard.validate(message="diagnóstico", channel="whatsapp_free")
        # Error message should contain portal guidance
        assert "portal" in str(exc_info.value).lower() or "seguro" in str(exc_info.value).lower()


class TestWhatsAppFreePhiGuard:
    """Tests for WhatsAppFreePhiGuard — blocks PHI fields in WhatsApp Free messages."""

    def test_import_guard(self) -> None:
        """Guard importable from compliance guardrails."""
        from src.modules.vitalia.compliance.guardrails.whatsapp_free_phi_guard import (
            WhatsAppFreePhiGuard,
        )

        assert WhatsAppFreePhiGuard is not None

    def test_blocks_message_with_diagnosis_field(self) -> None:
        """Message payload containing 'diagnosis' key blocked on whatsapp_free."""
        from src.modules.vitalia.compliance.application.compliance_service_adapter import (
            BlockedChannelError,
        )
        from src.modules.vitalia.compliance.guardrails.whatsapp_free_phi_guard import (
            WhatsAppFreePhiGuard,
        )

        guard = WhatsAppFreePhiGuard()
        payload = {"text": "Hola", "diagnosis": "anemia leve"}
        with pytest.raises(BlockedChannelError):
            guard.scan_payload(payload=payload, channel="whatsapp_free")

    def test_blocks_message_with_treatment_plan(self) -> None:
        """Message payload containing 'treatment_plan' key blocked on whatsapp_free."""
        from src.modules.vitalia.compliance.application.compliance_service_adapter import (
            BlockedChannelError,
        )
        from src.modules.vitalia.compliance.guardrails.whatsapp_free_phi_guard import (
            WhatsAppFreePhiGuard,
        )

        guard = WhatsAppFreePhiGuard()
        payload = {"text": "Tu plan", "treatment_plan": "10 sesiones"}
        with pytest.raises(BlockedChannelError):
            guard.scan_payload(payload=payload, channel="whatsapp_free")

    def test_allows_non_phi_payload(self) -> None:
        """Non-PHI payload on whatsapp_free passes guard."""
        from src.modules.vitalia.compliance.guardrails.whatsapp_free_phi_guard import (
            WhatsAppFreePhiGuard,
        )

        guard = WhatsAppFreePhiGuard()
        payload = {"text": "Tu turno es el lunes a las 10 hs.", "appointment_date": "2026-06-01"}
        result = guard.scan_payload(payload=payload, channel="whatsapp_free")
        assert result is True

    def test_allows_any_payload_on_secure_channel(self) -> None:
        """PHI payload on portal_secure passes guard (encrypted channel)."""
        from src.modules.vitalia.compliance.guardrails.whatsapp_free_phi_guard import (
            WhatsAppFreePhiGuard,
        )

        guard = WhatsAppFreePhiGuard()
        payload = {"diagnosis": "anemia", "treatment_plan": "iron supplements"}
        result = guard.scan_payload(payload=payload, channel="portal_secure")
        assert result is True

    def test_blocks_nested_patient_phi(self) -> None:
        """Nested patient.name PHI field blocked on whatsapp_free."""
        from src.modules.vitalia.compliance.application.compliance_service_adapter import (
            BlockedChannelError,
        )
        from src.modules.vitalia.compliance.guardrails.whatsapp_free_phi_guard import (
            WhatsAppFreePhiGuard,
        )

        guard = WhatsAppFreePhiGuard()
        payload = {"patient": {"name": "Juan Perez", "id": str(uuid4())}}
        with pytest.raises(BlockedChannelError):
            guard.scan_payload(payload=payload, channel="whatsapp_free")
