"""RED tests — LeadScreeningEvent domain entity.

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- Entity is a pure Python dataclass (no framework deps)
- All required fields present with correct types
- PHI dual filter fields: tenant_id + clinic_id mandatory
- soft-delete field deleted_at present
- response_text and reasoning are optional (sanitized before persist)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
LEAD_ID = uuid4()


def _make_event(**overrides: object) -> object:
    from src.modules.vitalia.sales_agent.domain.entities.lead_screening_event import (
        LeadScreeningEvent,
    )

    defaults = {
        "id": uuid4(),
        "tenant_id": TENANT_ID,
        "clinic_id": CLINIC_ID,
        "lead_id": LEAD_ID,
        "vertical": "dental",
        "questions_asked": ["¿Tienes dolor actual?", "¿Estás embarazada?"],
        "response_text": None,
        "outcome": "ok_proceed",
        "reasoning": None,
        "evaluated_at": None,
        "created_at": datetime.now(tz=timezone.utc),
        "deleted_at": None,
    }
    defaults.update(overrides)
    return LeadScreeningEvent(**defaults)


class TestLeadScreeningEventDomain:
    """Tests for LeadScreeningEvent entity (pure Python domain)."""

    def test_import_from_domain(self) -> None:
        """Entity lives in domain/entities — no framework deps."""
        from src.modules.vitalia.sales_agent.domain.entities.lead_screening_event import (
            LeadScreeningEvent,
        )

        assert LeadScreeningEvent is not None

    def test_create_minimal_event(self) -> None:
        """Can create event with minimum required fields."""
        event = _make_event()
        assert event.tenant_id == TENANT_ID
        assert event.clinic_id == CLINIC_ID
        assert event.lead_id == LEAD_ID

    def test_has_all_required_fields(self) -> None:
        """All fields from arch spec § 2.3 present on the dataclass."""
        import dataclasses

        from src.modules.vitalia.sales_agent.domain.entities.lead_screening_event import (
            LeadScreeningEvent,
        )

        field_names = {f.name for f in dataclasses.fields(LeadScreeningEvent)}
        required = {
            "id",
            "tenant_id",
            "clinic_id",
            "lead_id",
            "vertical",
            "questions_asked",
            "response_text",
            "outcome",
            "reasoning",
            "evaluated_at",
            "created_at",
            "deleted_at",
        }
        assert required.issubset(field_names), f"Missing fields: {required - field_names}"

    def test_phi_dual_filter_fields_mandatory(self) -> None:
        """tenant_id and clinic_id must be present — HIPAA-lite dual filter."""
        event = _make_event()
        assert hasattr(event, "tenant_id")
        assert hasattr(event, "clinic_id")
        assert event.tenant_id is not None
        assert event.clinic_id is not None

    def test_soft_delete_field_present(self) -> None:
        """deleted_at field must exist (soft delete only — never hard delete)."""
        event = _make_event()
        assert hasattr(event, "deleted_at")
        assert event.deleted_at is None  # default not-deleted

    def test_optional_phi_fields_default_none(self) -> None:
        """response_text and reasoning are Optional — allow None before LLM eval."""
        event = _make_event(response_text=None, reasoning=None)
        assert event.response_text is None
        assert event.reasoning is None

    def test_vertical_values(self) -> None:
        """Vertical accepts YAML SSoT values (dental, estetica, psicologia, etc.)."""
        for vertical in ["dental", "estetica", "psicologia", "fertilidad", "otro"]:
            event = _make_event(vertical=vertical)
            assert event.vertical == vertical

    def test_questions_asked_is_list(self) -> None:
        """questions_asked stores list of question strings."""
        questions = ["Pregunta 1", "Pregunta 2"]
        event = _make_event(questions_asked=questions)
        assert isinstance(event.questions_asked, list)
        assert len(event.questions_asked) == 2

    def test_outcome_field(self) -> None:
        """outcome field stores string value matching ScreeningOutcome enum."""
        event = _make_event(outcome="derivar_doctor")
        assert event.outcome == "derivar_doctor"

    def test_is_dataclass(self) -> None:
        """Entity must be a plain Python dataclass (no SQLAlchemy, no Pydantic)."""
        import dataclasses

        from src.modules.vitalia.sales_agent.domain.entities.lead_screening_event import (
            LeadScreeningEvent,
        )

        assert dataclasses.is_dataclass(LeadScreeningEvent)
