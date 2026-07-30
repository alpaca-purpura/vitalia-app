"""Tests for Conversation domain entity.

TDD RED phase — tests written before implementation per .claude/rules/tdd-mandatory.md.

SC-01 coverage: handler_mode + proposal_required defaults, status enum values.
SC-03 coverage: updated_at present for OCC conflict resolution.
PHI dual-filter: tenant_id + clinic_id mandatory fields present on entity.

downstream-regression-na: brand-local vitalia CRM domain entity tests
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.modules.vitalia.crm.domain.conversation import (
    VALID_CHANNELS,
    VALID_HANDLER_MODES,
    VALID_STATUSES,
    Conversation,
)


class TestConversationFields:
    """Conversation entity carries required PHI dual-filter fields."""

    def _make_conversation(self, **overrides: object) -> Conversation:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "lead_id": uuid4(),
            "patient_id": None,
            "channel": "whatsapp",
            "channel_external_id": None,
            "status": "active",
            "handler_mode": "ai",
            "proposal_required": False,
            "pause_until": None,
            "help_needed": False,
            "help_needed_reason": None,
            "unread_media_count": 0,
            "last_message_at": None,
            "last_message_preview": None,
            "messages_count": 0,
            "stage_decision": None,
            "linked_offer_id": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted_at": None,
        }
        defaults.update(overrides)
        return Conversation(**defaults)

    def test_conversation_has_tenant_id(self) -> None:
        """PHI dual-filter: tenant_id present (mandatory)."""
        tenant = uuid4()
        conv = self._make_conversation(tenant_id=tenant)
        assert conv.tenant_id == tenant

    def test_conversation_has_clinic_id(self) -> None:
        """PHI dual-filter: clinic_id present (mandatory)."""
        clinic = uuid4()
        conv = self._make_conversation(clinic_id=clinic)
        assert conv.clinic_id == clinic

    def test_conversation_has_lead_id(self) -> None:
        lead = uuid4()
        conv = self._make_conversation(lead_id=lead)
        assert conv.lead_id == lead

    def test_conversation_patient_id_optional(self) -> None:
        conv = self._make_conversation(patient_id=None)
        assert conv.patient_id is None

        patient = uuid4()
        conv2 = self._make_conversation(patient_id=patient)
        assert conv2.patient_id == patient

    def test_conversation_has_updated_at_for_occ(self) -> None:
        """SC-03: updated_at present for OCC conflict check (If-Match header)."""
        now = datetime.now(UTC)
        conv = self._make_conversation(updated_at=now)
        assert conv.updated_at == now

    def test_conversation_soft_delete_field(self) -> None:
        """Soft delete only — deleted_at field present."""
        conv = self._make_conversation(deleted_at=None)
        assert conv.deleted_at is None

        deleted = datetime.now(UTC)
        conv2 = self._make_conversation(deleted_at=deleted)
        assert conv2.deleted_at == deleted


class TestConversationDefaults:
    """SC-01: Adrián mode defaults align with spec."""

    def _make_conversation(self, **overrides: object) -> Conversation:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "lead_id": uuid4(),
            "patient_id": None,
            "channel": "whatsapp",
            "channel_external_id": None,
            "status": "active",
            "handler_mode": "ai",
            "proposal_required": False,
            "pause_until": None,
            "help_needed": False,
            "help_needed_reason": None,
            "unread_media_count": 0,
            "last_message_at": None,
            "last_message_preview": None,
            "messages_count": 0,
            "stage_decision": None,
            "linked_offer_id": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted_at": None,
        }
        defaults.update(overrides)
        return Conversation(**defaults)

    def test_default_handler_mode_is_ai(self) -> None:
        """SC-01: default mode is 'ai' (Adrián decide)."""
        conv = self._make_conversation(handler_mode="ai")
        assert conv.handler_mode == "ai"

    def test_default_status_is_active(self) -> None:
        conv = self._make_conversation(status="active")
        assert conv.status == "active"

    def test_default_help_needed_is_false(self) -> None:
        conv = self._make_conversation(help_needed=False)
        assert conv.help_needed is False

    def test_default_unread_media_count_is_zero(self) -> None:
        conv = self._make_conversation(unread_media_count=0)
        assert conv.unread_media_count == 0

    def test_default_proposal_required_is_false(self) -> None:
        """handler_mode='ai' + proposal_required=False => 'Adrián decide' mode."""
        conv = self._make_conversation(handler_mode="ai", proposal_required=False)
        assert conv.proposal_required is False

    def test_adrián_consulta_mode_flags(self) -> None:
        """handler_mode='ai' + proposal_required=True => 'Adrián consulta' mode."""
        conv = self._make_conversation(handler_mode="ai", proposal_required=True)
        assert conv.handler_mode == "ai"
        assert conv.proposal_required is True

    def test_yo_escribo_mode_flags(self) -> None:
        """handler_mode='human' => 'Yo escribo' mode."""
        conv = self._make_conversation(handler_mode="human", proposal_required=False)
        assert conv.handler_mode == "human"


class TestConversationEnumValues:
    """Enum literals match expected spec values."""

    def test_valid_channels_includes_whatsapp(self) -> None:
        assert "whatsapp" in VALID_CHANNELS

    def test_valid_channels_includes_instagram(self) -> None:
        assert "instagram" in VALID_CHANNELS

    def test_valid_channels_includes_web(self) -> None:
        assert "web" in VALID_CHANNELS

    def test_valid_statuses_includes_active(self) -> None:
        assert "active" in VALID_STATUSES

    def test_valid_statuses_includes_closed(self) -> None:
        assert "closed" in VALID_STATUSES

    def test_valid_handler_modes(self) -> None:
        assert "ai" in VALID_HANDLER_MODES
        assert "human" in VALID_HANDLER_MODES


class TestConversationPause:
    """Pause-Adrián: pause_until field reflects 60min window."""

    def _make_conversation(self, **overrides: object) -> Conversation:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "lead_id": uuid4(),
            "patient_id": None,
            "channel": "whatsapp",
            "channel_external_id": None,
            "status": "active",
            "handler_mode": "ai",
            "proposal_required": False,
            "pause_until": None,
            "help_needed": False,
            "help_needed_reason": None,
            "unread_media_count": 0,
            "last_message_at": None,
            "last_message_preview": None,
            "messages_count": 0,
            "stage_decision": None,
            "linked_offer_id": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted_at": None,
        }
        defaults.update(overrides)
        return Conversation(**defaults)

    def test_pause_until_is_optional(self) -> None:
        conv = self._make_conversation(pause_until=None)
        assert conv.pause_until is None

    def test_pause_until_datetime_stored(self) -> None:
        future = datetime.now(UTC) + timedelta(minutes=60)
        conv = self._make_conversation(pause_until=future)
        assert conv.pause_until == future


class TestConversationStageDecision:
    """Stage decision field tracks consultive-selling pipeline stage."""

    def _make_conversation(self, **overrides: object) -> Conversation:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "lead_id": uuid4(),
            "patient_id": None,
            "channel": "whatsapp",
            "channel_external_id": None,
            "status": "active",
            "handler_mode": "ai",
            "proposal_required": False,
            "pause_until": None,
            "help_needed": False,
            "help_needed_reason": None,
            "unread_media_count": 0,
            "last_message_at": None,
            "last_message_preview": None,
            "messages_count": 0,
            "stage_decision": None,
            "linked_offer_id": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "deleted_at": None,
        }
        defaults.update(overrides)
        return Conversation(**defaults)

    def test_stage_decision_none_by_default(self) -> None:
        conv = self._make_conversation(stage_decision=None)
        assert conv.stage_decision is None

    def test_stage_decision_interesado(self) -> None:
        conv = self._make_conversation(stage_decision="interesado")
        assert conv.stage_decision == "interesado"

    def test_stage_decision_considerando(self) -> None:
        conv = self._make_conversation(stage_decision="considerando")
        assert conv.stage_decision == "considerando"

    def test_stage_decision_listo(self) -> None:
        conv = self._make_conversation(stage_decision="listo")
        assert conv.stage_decision == "listo"

    def test_stage_decision_decidio_no(self) -> None:
        conv = self._make_conversation(stage_decision="decidio_no")
        assert conv.stage_decision == "decidio_no"
