"""Tests for Vitalia CRM domain events.

TDD RED phase — tests written before implementation.

SC-01 coverage: ConversationStarted, MessageSent, MessageRetracted, ModeChanged,
                AdrianPaused, ProactiveOutboundSent
SC-03 coverage: ModeChanged carries OCC context (previous_updated_at).
PHI dual-filter: tenant_id + clinic_id mandatory.

downstream-regression-na: brand-local vitalia CRM domain events tests
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.modules.vitalia.crm.domain.events import (
    AdrianPaused,
    ConversationStarted,
    MessageRetracted,
    MessageSent,
    ModeChanged,
    ProactiveOutboundSent,
)


class TestConversationStarted:
    """SC-01: ConversationStarted event fields and event_name."""

    def _make_event(self, **overrides: object) -> ConversationStarted:
        now = datetime.now(UTC)
        tenant_id = uuid4()
        defaults: dict[str, object] = {
            "event_name": "conversation_started",
            "tenant_id": tenant_id,
            "occurred_at": now,
            "payload": {},
            "conversation_id": uuid4(),
            "clinic_id": uuid4(),
            "lead_id": uuid4(),
            "channel": "whatsapp",
        }
        defaults.update(overrides)
        return ConversationStarted(**defaults)

    def test_event_name_is_conversation_started(self) -> None:
        event = self._make_event()
        assert event.event_name == "conversation_started"

    def test_carries_tenant_id(self) -> None:
        tenant = uuid4()
        event = self._make_event(tenant_id=tenant)
        assert event.tenant_id == tenant

    def test_carries_clinic_id_phi_dual_filter(self) -> None:
        """PHI dual-filter: clinic_id present in event."""
        clinic = uuid4()
        event = self._make_event(clinic_id=clinic)
        assert event.clinic_id == clinic

    def test_carries_conversation_id(self) -> None:
        conv = uuid4()
        event = self._make_event(conversation_id=conv)
        assert event.conversation_id == conv

    def test_carries_channel(self) -> None:
        event = self._make_event(channel="instagram")
        assert event.channel == "instagram"


class TestMessageSent:
    """SC-01: MessageSent event + ActionReceipt created for AI messages."""

    def _make_event(self, **overrides: object) -> MessageSent:
        now = datetime.now(UTC)
        defaults: dict[str, object] = {
            "event_name": "message_sent",
            "tenant_id": uuid4(),
            "occurred_at": now,
            "payload": {},
            "message_id": uuid4(),
            "conversation_id": uuid4(),
            "clinic_id": uuid4(),
            "sender_type": "agent_ai",
            "channel": "whatsapp",
        }
        defaults.update(overrides)
        return MessageSent(**defaults)

    def test_event_name_is_message_sent(self) -> None:
        event = self._make_event()
        assert event.event_name == "message_sent"

    def test_carries_message_id(self) -> None:
        msg = uuid4()
        event = self._make_event(message_id=msg)
        assert event.message_id == msg

    def test_carries_clinic_id_phi_dual_filter(self) -> None:
        clinic = uuid4()
        event = self._make_event(clinic_id=clinic)
        assert event.clinic_id == clinic

    def test_sender_type_agent_ai(self) -> None:
        event = self._make_event(sender_type="agent_ai")
        assert event.sender_type == "agent_ai"

    def test_sender_type_patient(self) -> None:
        event = self._make_event(sender_type="patient")
        assert event.sender_type == "patient"


class TestMessageRetracted:
    """SC-01: MessageRetracted — user_undo, expired, patient_replied; fallback 'marcar erróneo'."""

    def _make_event(self, **overrides: object) -> MessageRetracted:
        now = datetime.now(UTC)
        defaults: dict[str, object] = {
            "event_name": "message_retracted",
            "tenant_id": uuid4(),
            "occurred_at": now,
            "payload": {},
            "message_id": uuid4(),
            "conversation_id": uuid4(),
            "clinic_id": uuid4(),
            "retract_succeeded": True,
            "retract_reason": "user_undo",
        }
        defaults.update(overrides)
        return MessageRetracted(**defaults)

    def test_event_name_is_message_retracted(self) -> None:
        event = self._make_event()
        assert event.event_name == "message_retracted"

    def test_retract_succeeded_true_user_undo(self) -> None:
        event = self._make_event(retract_succeeded=True, retract_reason="user_undo")
        assert event.retract_succeeded is True
        assert event.retract_reason == "user_undo"

    def test_retract_succeeded_false_marcar_erroneo_email(self) -> None:
        """Email channel: retraction not supported → fallback 'marcar erróneo'."""
        event = self._make_event(retract_succeeded=False, retract_reason="user_undo")
        assert event.retract_succeeded is False

    def test_reason_expired(self) -> None:
        event = self._make_event(retract_reason="expired")
        assert event.retract_reason == "expired"

    def test_reason_patient_replied(self) -> None:
        event = self._make_event(retract_reason="patient_replied")
        assert event.retract_reason == "patient_replied"

    def test_carries_clinic_id_phi_dual_filter(self) -> None:
        clinic = uuid4()
        event = self._make_event(clinic_id=clinic)
        assert event.clinic_id == clinic


class TestModeChanged:
    """SC-03: ModeChanged event carries OCC context (previous_updated_at)."""

    def _make_event(self, **overrides: object) -> ModeChanged:
        now = datetime.now(UTC)
        defaults: dict[str, object] = {
            "event_name": "mode_changed",
            "tenant_id": uuid4(),
            "occurred_at": now,
            "payload": {},
            "conversation_id": uuid4(),
            "clinic_id": uuid4(),
            "previous_handler_mode": "ai",
            "new_handler_mode": "human",
            "previous_updated_at": now - timedelta(seconds=30),
        }
        defaults.update(overrides)
        return ModeChanged(**defaults)

    def test_event_name_is_mode_changed(self) -> None:
        event = self._make_event()
        assert event.event_name == "mode_changed"

    def test_occ_previous_updated_at_present(self) -> None:
        """SC-03: OCC token (previous_updated_at) carried for conflict detection."""
        now = datetime.now(UTC)
        token = now - timedelta(seconds=30)
        event = self._make_event(previous_updated_at=token)
        assert event.previous_updated_at == token

    def test_mode_transition_ai_to_human(self) -> None:
        event = self._make_event(previous_handler_mode="ai", new_handler_mode="human")
        assert event.previous_handler_mode == "ai"
        assert event.new_handler_mode == "human"

    def test_mode_transition_human_to_ai(self) -> None:
        event = self._make_event(previous_handler_mode="human", new_handler_mode="ai")
        assert event.previous_handler_mode == "human"
        assert event.new_handler_mode == "ai"

    def test_carries_clinic_id_phi_dual_filter(self) -> None:
        clinic = uuid4()
        event = self._make_event(clinic_id=clinic)
        assert event.clinic_id == clinic


class TestAdrianPaused:
    """SC-01: AdrianPaused — 60min pause window, auto-resumes."""

    def _make_event(self, **overrides: object) -> AdrianPaused:
        now = datetime.now(UTC)
        defaults: dict[str, object] = {
            "event_name": "adrian_paused",
            "tenant_id": uuid4(),
            "occurred_at": now,
            "payload": {},
            "conversation_id": uuid4(),
            "clinic_id": uuid4(),
            "pause_until": now + timedelta(minutes=60),
            "paused_by_user_id": None,
        }
        defaults.update(overrides)
        return AdrianPaused(**defaults)

    def test_event_name_is_adrian_paused(self) -> None:
        event = self._make_event()
        assert event.event_name == "adrian_paused"

    def test_pause_until_60_minutes_from_now(self) -> None:
        now = datetime.now(UTC)
        pause_until = now + timedelta(minutes=60)
        event = self._make_event(pause_until=pause_until)
        delta = event.pause_until - now
        # 60 minutes window
        assert abs(delta.total_seconds() - 3600) < 5

    def test_paused_by_user_id_optional(self) -> None:
        event = self._make_event(paused_by_user_id=None)
        assert event.paused_by_user_id is None

    def test_paused_by_user_id_set(self) -> None:
        user = uuid4()
        event = self._make_event(paused_by_user_id=user)
        assert event.paused_by_user_id == user

    def test_carries_clinic_id_phi_dual_filter(self) -> None:
        clinic = uuid4()
        event = self._make_event(clinic_id=clinic)
        assert event.clinic_id == clinic


class TestProactiveOutboundSent:
    """SC-01: ProactiveOutboundSent — Adrián proactive contact (follow-up, reminder)."""

    def _make_event(self, **overrides: object) -> ProactiveOutboundSent:
        now = datetime.now(UTC)
        defaults: dict[str, object] = {
            "event_name": "proactive_outbound_sent",
            "tenant_id": uuid4(),
            "occurred_at": now,
            "payload": {},
            "message_id": uuid4(),
            "conversation_id": uuid4(),
            "clinic_id": uuid4(),
            "channel": "whatsapp",
            "outbound_kind": "follow_up",
        }
        defaults.update(overrides)
        return ProactiveOutboundSent(**defaults)

    def test_event_name_is_proactive_outbound_sent(self) -> None:
        event = self._make_event()
        assert event.event_name == "proactive_outbound_sent"

    def test_outbound_kind_follow_up(self) -> None:
        event = self._make_event(outbound_kind="follow_up")
        assert event.outbound_kind == "follow_up"

    def test_outbound_kind_appointment_reminder(self) -> None:
        event = self._make_event(outbound_kind="appointment_reminder")
        assert event.outbound_kind == "appointment_reminder"

    def test_outbound_kind_reactivation(self) -> None:
        event = self._make_event(outbound_kind="reactivation")
        assert event.outbound_kind == "reactivation"

    def test_carries_clinic_id_phi_dual_filter(self) -> None:
        clinic = uuid4()
        event = self._make_event(clinic_id=clinic)
        assert event.clinic_id == clinic

    def test_carries_message_id(self) -> None:
        msg = uuid4()
        event = self._make_event(message_id=msg)
        assert event.message_id == msg


class TestDomainEventInheritance:
    """All 6 events inherit from DomainEvent (engine base)."""

    def test_conversation_started_inherits_domain_event(self) -> None:
        from luana_core_platform.domain.events import DomainEvent

        event = ConversationStarted(
            event_name="conversation_started",
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            clinic_id=uuid4(),
            lead_id=uuid4(),
            channel="whatsapp",
        )
        assert isinstance(event, DomainEvent)

    def test_message_sent_inherits_domain_event(self) -> None:
        from luana_core_platform.domain.events import DomainEvent

        event = MessageSent(
            event_name="message_sent",
            tenant_id=uuid4(),
            message_id=uuid4(),
            conversation_id=uuid4(),
            clinic_id=uuid4(),
            sender_type="agent_ai",
            channel="whatsapp",
        )
        assert isinstance(event, DomainEvent)

    def test_mode_changed_inherits_domain_event(self) -> None:
        from luana_core_platform.domain.events import DomainEvent

        event = ModeChanged(
            event_name="mode_changed",
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            clinic_id=uuid4(),
            previous_handler_mode="ai",
            new_handler_mode="human",
        )
        assert isinstance(event, DomainEvent)
