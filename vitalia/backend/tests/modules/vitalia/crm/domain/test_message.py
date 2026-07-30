"""Tests for Message domain entity.

TDD RED phase — tests written before implementation.

SC-01 coverage: sender_type enum, retraction state.
SC-02 coverage: transcription_confidence field present.
PHI dual-filter: tenant_id + clinic_id mandatory.

downstream-regression-na: brand-local vitalia CRM domain entity tests
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from src.modules.vitalia.crm.domain.message import (
    VALID_MEDIA_KINDS,
    VALID_SENDER_TYPES,
    Message,
)


class TestMessageFields:
    """Message entity carries required PHI dual-filter fields."""

    def _make_message(self, **overrides: object) -> Message:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "conversation_id": uuid4(),
            "channel": "whatsapp",
            "external_message_id": None,
            "sender_type": "agent_ai",
            "sender_user_id": None,
            "body_text": "Hola, ¿en qué puedo ayudarte?",
            "media_kind": None,
            "media_url": None,
            "media_duration_s": None,
            "media_phi_flagged": False,
            "transcription_text": None,
            "transcription_confidence": None,
            "retracted_at": None,
            "retracted_by_user_id": None,
            "retracted_reason": None,
            "retract_succeeded": None,
            "handler_mode": "ai",
            "cache_hit_rate": None,
            "llm_cost_usd": None,
            "sent_at": datetime.now(UTC),
            "delivered_at": None,
            "read_at": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted_at": None,
        }
        defaults.update(overrides)
        return Message(**defaults)

    def test_message_has_tenant_id(self) -> None:
        """PHI dual-filter: tenant_id present."""
        tenant = uuid4()
        msg = self._make_message(tenant_id=tenant)
        assert msg.tenant_id == tenant

    def test_message_has_clinic_id(self) -> None:
        """PHI dual-filter: clinic_id present."""
        clinic = uuid4()
        msg = self._make_message(clinic_id=clinic)
        assert msg.clinic_id == clinic

    def test_message_has_conversation_id(self) -> None:
        conv = uuid4()
        msg = self._make_message(conversation_id=conv)
        assert msg.conversation_id == conv

    def test_message_soft_delete_field(self) -> None:
        """Soft delete only — deleted_at field present."""
        msg = self._make_message(deleted_at=None)
        assert msg.deleted_at is None


class TestMessageSenderType:
    """SC-01: sender_type enum validates correctly."""

    def _make_message(self, **overrides: object) -> Message:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "conversation_id": uuid4(),
            "channel": "whatsapp",
            "external_message_id": None,
            "sender_type": "agent_ai",
            "sender_user_id": None,
            "body_text": "Mensaje de prueba",
            "media_kind": None,
            "media_url": None,
            "media_duration_s": None,
            "media_phi_flagged": False,
            "transcription_text": None,
            "transcription_confidence": None,
            "retracted_at": None,
            "retracted_by_user_id": None,
            "retracted_reason": None,
            "retract_succeeded": None,
            "handler_mode": "ai",
            "cache_hit_rate": None,
            "llm_cost_usd": None,
            "sent_at": datetime.now(UTC),
            "delivered_at": None,
            "read_at": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted_at": None,
        }
        defaults.update(overrides)
        return Message(**defaults)

    def test_valid_sender_types(self) -> None:
        assert "patient" in VALID_SENDER_TYPES
        assert "agent_ai" in VALID_SENDER_TYPES
        assert "agent_human" in VALID_SENDER_TYPES
        assert "system" in VALID_SENDER_TYPES

    def test_sender_type_patient(self) -> None:
        msg = self._make_message(sender_type="patient")
        assert msg.sender_type == "patient"

    def test_sender_type_agent_ai(self) -> None:
        """SC-01: Adrián sends messages as agent_ai."""
        msg = self._make_message(sender_type="agent_ai")
        assert msg.sender_type == "agent_ai"

    def test_sender_type_agent_human(self) -> None:
        user = uuid4()
        msg = self._make_message(sender_type="agent_human", sender_user_id=user)
        assert msg.sender_type == "agent_human"
        assert msg.sender_user_id == user

    def test_sender_type_system(self) -> None:
        msg = self._make_message(sender_type="system")
        assert msg.sender_type == "system"


class TestMessageRetraction:
    """SC-01: Action receipts undo — retraction state machine."""

    def _make_message(self, **overrides: object) -> Message:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "conversation_id": uuid4(),
            "channel": "whatsapp",
            "external_message_id": "wamid.1234",
            "sender_type": "agent_ai",
            "sender_user_id": None,
            "body_text": "Mensaje para revertir",
            "media_kind": None,
            "media_url": None,
            "media_duration_s": None,
            "media_phi_flagged": False,
            "transcription_text": None,
            "transcription_confidence": None,
            "retracted_at": None,
            "retracted_by_user_id": None,
            "retracted_reason": None,
            "retract_succeeded": None,
            "handler_mode": "ai",
            "cache_hit_rate": None,
            "llm_cost_usd": None,
            "sent_at": datetime.now(UTC),
            "delivered_at": None,
            "read_at": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted_at": None,
        }
        defaults.update(overrides)
        return Message(**defaults)

    def test_initial_retraction_state_is_none(self) -> None:
        """Before retract: all retraction fields are None."""
        msg = self._make_message()
        assert msg.retracted_at is None
        assert msg.retracted_by_user_id is None
        assert msg.retracted_reason is None
        assert msg.retract_succeeded is None

    def test_retracted_at_can_be_set(self) -> None:
        retracted = datetime.now(UTC)
        user = uuid4()
        msg = self._make_message(
            retracted_at=retracted,
            retracted_by_user_id=user,
            retracted_reason="user_undo",
            retract_succeeded=True,
        )
        assert msg.retracted_at == retracted
        assert msg.retracted_by_user_id == user
        assert msg.retracted_reason == "user_undo"
        assert msg.retract_succeeded is True

    def test_retract_fallback_marcar_erroneo(self) -> None:
        """Email channel: retract not supported, fallback marcar_erroneo = retract_succeeded=False."""
        msg = self._make_message(
            channel="email",
            retracted_at=datetime.now(UTC),
            retract_succeeded=False,
        )
        assert msg.retract_succeeded is False


class TestMessageMedia:
    """SC-02: Audio IN fields."""

    def _make_message(self, **overrides: object) -> Message:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "conversation_id": uuid4(),
            "channel": "whatsapp",
            "external_message_id": None,
            "sender_type": "patient",
            "sender_user_id": None,
            "body_text": None,
            "media_kind": "audio",
            "media_url": "https://cdn.example.com/voice.ogg",
            "media_duration_s": 18,
            "media_phi_flagged": False,
            "transcription_text": None,
            "transcription_confidence": None,
            "retracted_at": None,
            "retracted_by_user_id": None,
            "retracted_reason": None,
            "retract_succeeded": None,
            "handler_mode": "ai",
            "cache_hit_rate": None,
            "llm_cost_usd": None,
            "sent_at": datetime.now(UTC),
            "delivered_at": None,
            "read_at": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted_at": None,
        }
        defaults.update(overrides)
        return Message(**defaults)

    def test_valid_media_kinds(self) -> None:
        assert "audio" in VALID_MEDIA_KINDS
        assert "image" in VALID_MEDIA_KINDS
        assert "video" in VALID_MEDIA_KINDS
        assert "document" in VALID_MEDIA_KINDS
        assert "sticker" in VALID_MEDIA_KINDS

    def test_audio_message_fields(self) -> None:
        """SC-02: Audio message carries duration and empty transcription."""
        msg = self._make_message(
            media_kind="audio",
            media_duration_s=18,
            transcription_text=None,
            transcription_confidence=None,
        )
        assert msg.media_kind == "audio"
        assert msg.media_duration_s == 18
        assert msg.transcription_text is None

    def test_audio_with_low_confidence_transcription(self) -> None:
        """SC-02: low confidence triggers fallback path in service."""
        msg = self._make_message(
            media_kind="audio",
            transcription_text="ininteligible",
            transcription_confidence=0.3,  # < 0.5 threshold
        )
        assert msg.transcription_confidence is not None
        assert msg.transcription_confidence < 0.5

    def test_audio_with_successful_transcription(self) -> None:
        msg = self._make_message(
            media_kind="audio",
            transcription_text="Hola, quería sacar turno para limpieza profunda",
            transcription_confidence=0.92,
        )
        assert msg.transcription_text is not None
        assert msg.transcription_confidence is not None
        assert msg.transcription_confidence >= 0.5

    def test_media_phi_flagged_default_false(self) -> None:
        msg = self._make_message(media_phi_flagged=False)
        assert msg.media_phi_flagged is False

    def test_media_phi_flagged_can_be_true(self) -> None:
        msg = self._make_message(media_phi_flagged=True)
        assert msg.media_phi_flagged is True
