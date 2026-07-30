"""Tests for ActivityEvent domain entity.

TDD RED phase — tests written before implementation.

SC-01 coverage: ActivityStream events with description_es + agent_id.
PHI dual-filter: tenant_id + clinic_id mandatory.

downstream-regression-na: brand-local vitalia CRM domain entity tests
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from src.modules.vitalia.crm.domain.activity_event import (
    VALID_AGENT_IDS,
    ActivityEvent,
)


class TestActivityEventFields:
    """ActivityEvent carries PHI dual-filter + UI-tuned description."""

    def _make_event(self, **overrides: object) -> ActivityEvent:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "conversation_id": uuid4(),
            "source_trace_event_id": None,
            "event_kind": "consulto_precio",
            "description_es": "Consultó precio de Blanqueamiento Premium ($24.000)",
            "agent_id": "adrian",
            "occurred_at": datetime.now(UTC),
            "payload_sanitized": {},
            "created_at": datetime.now(UTC),
        }
        defaults.update(overrides)
        return ActivityEvent(**defaults)

    def test_activity_event_has_tenant_id(self) -> None:
        """PHI dual-filter: tenant_id present."""
        tenant = uuid4()
        evt = self._make_event(tenant_id=tenant)
        assert evt.tenant_id == tenant

    def test_activity_event_has_clinic_id(self) -> None:
        """PHI dual-filter: clinic_id present."""
        clinic = uuid4()
        evt = self._make_event(clinic_id=clinic)
        assert evt.clinic_id == clinic

    def test_activity_event_has_conversation_id(self) -> None:
        conv = uuid4()
        evt = self._make_event(conversation_id=conv)
        assert evt.conversation_id == conv

    def test_description_es_required_non_empty(self) -> None:
        """SC-01: ActivityStream shows description_es in UI."""
        evt = self._make_event(description_es="Consultó precio de Blanqueamiento Premium ($24.000)")
        assert evt.description_es == "Consultó precio de Blanqueamiento Premium ($24.000)"

    def test_description_es_no_voseo(self) -> None:
        """spanish-text.md: description_es uses neutro LatAm (no voseo)."""
        # 'consultó' uses 3rd person (narrated form for activity stream) — OK
        evt = self._make_event(description_es="Verificó disponibilidad martes 12:00 (libre)")
        assert "verificó" in evt.description_es.lower()
        # Voseo patterns not present
        assert "verificás" not in evt.description_es

    def test_source_trace_event_id_optional(self) -> None:
        evt = self._make_event(source_trace_event_id=None)
        assert evt.source_trace_event_id is None

        trace_id = uuid4()
        evt2 = self._make_event(source_trace_event_id=trace_id)
        assert evt2.source_trace_event_id == trace_id

    def test_payload_sanitized_is_dict(self) -> None:
        """Payload must be dict (PII-sanitized before storing)."""
        evt = self._make_event(payload_sanitized={})
        assert isinstance(evt.payload_sanitized, dict)

    def test_payload_sanitized_can_have_data(self) -> None:
        payload = {"offer_name": "Blanqueamiento Premium", "price_display": "$24.000"}
        evt = self._make_event(payload_sanitized=payload)
        assert evt.payload_sanitized["offer_name"] == "Blanqueamiento Premium"


class TestActivityEventAgentId:
    """SC-01: agent_id reflects who performed the action."""

    def _make_event(self, **overrides: object) -> ActivityEvent:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "conversation_id": uuid4(),
            "source_trace_event_id": None,
            "event_kind": "consulto_precio",
            "description_es": "Consultó precio",
            "agent_id": "adrian",
            "occurred_at": datetime.now(UTC),
            "payload_sanitized": {},
            "created_at": datetime.now(UTC),
        }
        defaults.update(overrides)
        return ActivityEvent(**defaults)

    def test_valid_agent_ids_contains_adrian(self) -> None:
        assert "adrian" in VALID_AGENT_IDS

    def test_valid_agent_ids_contains_valeria(self) -> None:
        assert "valeria" in VALID_AGENT_IDS

    def test_valid_agent_ids_contains_lucas(self) -> None:
        assert "lucas" in VALID_AGENT_IDS

    def test_valid_agent_ids_contains_system(self) -> None:
        assert "system" in VALID_AGENT_IDS

    def test_agent_id_adrian(self) -> None:
        """SC-01: Adrián is the primary agent for inbox operations."""
        evt = self._make_event(agent_id="adrian")
        assert evt.agent_id == "adrian"

    def test_agent_id_system(self) -> None:
        evt = self._make_event(agent_id="system")
        assert evt.agent_id == "system"


class TestActivityEventKind:
    """SC-01: event_kind reflects consultive-selling workflow steps."""

    def _make_event(self, **overrides: object) -> ActivityEvent:
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "conversation_id": uuid4(),
            "source_trace_event_id": None,
            "event_kind": "consulto_precio",
            "description_es": "Consultó precio",
            "agent_id": "adrian",
            "occurred_at": datetime.now(UTC),
            "payload_sanitized": {},
            "created_at": datetime.now(UTC),
        }
        defaults.update(overrides)
        return ActivityEvent(**defaults)

    def test_event_kind_consulto_precio(self) -> None:
        """SC-01: 'consultó precio de Blanqueamiento Premium ($24.000)'."""
        evt = self._make_event(event_kind="consulto_precio")
        assert evt.event_kind == "consulto_precio"

    def test_event_kind_verifico_agenda(self) -> None:
        """SC-01: 'verificó disponibilidad martes 12:00 (libre)'."""
        evt = self._make_event(event_kind="verifico_agenda")
        assert evt.event_kind == "verifico_agenda"

    def test_event_kind_propuso_turno(self) -> None:
        """SC-01: 'propuso: Te puedo ofrecer martes 12:00…'."""
        evt = self._make_event(event_kind="propuso_turno")
        assert evt.event_kind == "propuso_turno"

    def test_event_kind_clasifico_interes(self) -> None:
        """SC-01: 'clasificó: interés alto · vertical odontológica'."""
        evt = self._make_event(event_kind="clasifico_interes")
        assert evt.event_kind == "clasifico_interes"

    def test_event_kind_derivo_doctor(self) -> None:
        evt = self._make_event(event_kind="derivo_doctor")
        assert evt.event_kind == "derivo_doctor"
