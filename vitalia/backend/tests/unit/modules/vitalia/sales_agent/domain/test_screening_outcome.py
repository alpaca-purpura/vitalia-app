"""RED tests — ScreeningOutcome domain enum.

TDD per .claude/rules/tdd-mandatory.md.

Verifies:
- All enum values present matching migration CHECK constraint
- String values match expected slugs (used in DB CHECK constraint)
- Enum is importable from domain enums layer (no framework deps)
"""

from __future__ import annotations


class TestScreeningOutcomeEnum:
    """Tests for ScreeningOutcome StrEnum."""

    def test_import_from_domain(self) -> None:
        """Enum lives in domain/enums — pure Python, no framework deps."""
        from src.modules.vitalia.sales_agent.domain.enums.screening_outcome import (
            ScreeningOutcome,
        )

        assert ScreeningOutcome is not None

    def test_all_four_values_present(self) -> None:
        """Must have exactly 4 values matching migration 021 CHECK constraint."""
        from src.modules.vitalia.sales_agent.domain.enums.screening_outcome import (
            ScreeningOutcome,
        )

        values = {e.value for e in ScreeningOutcome}
        assert values == {
            "ok_proceed",
            "derivar_doctor",
            "derivar_emergencia",
            "awaiting_response",
        }

    def test_ok_proceed_value(self) -> None:
        """ok_proceed — lead is cleared to receive payment link."""
        from src.modules.vitalia.sales_agent.domain.enums.screening_outcome import (
            ScreeningOutcome,
        )

        assert ScreeningOutcome.OK_PROCEED.value == "ok_proceed"

    def test_derivar_doctor_value(self) -> None:
        """derivar_doctor — refer to medical professional for consultation."""
        from src.modules.vitalia.sales_agent.domain.enums.screening_outcome import (
            ScreeningOutcome,
        )

        assert ScreeningOutcome.DERIVAR_DOCTOR.value == "derivar_doctor"

    def test_derivar_emergencia_value(self) -> None:
        """derivar_emergencia — urgent: route to emergency care."""
        from src.modules.vitalia.sales_agent.domain.enums.screening_outcome import (
            ScreeningOutcome,
        )

        assert ScreeningOutcome.DERIVAR_EMERGENCIA.value == "derivar_emergencia"

    def test_awaiting_response_value(self) -> None:
        """awaiting_response — lead hasn't answered yet."""
        from src.modules.vitalia.sales_agent.domain.enums.screening_outcome import (
            ScreeningOutcome,
        )

        assert ScreeningOutcome.AWAITING_RESPONSE.value == "awaiting_response"

    def test_is_str_enum(self) -> None:
        """Must be StrEnum for direct string comparison in Pydantic / SA."""
        from enum import StrEnum

        from src.modules.vitalia.sales_agent.domain.enums.screening_outcome import (
            ScreeningOutcome,
        )

        assert issubclass(ScreeningOutcome, StrEnum)

    def test_string_equality(self) -> None:
        """StrEnum allows == comparison with raw string (used in service logic)."""
        from src.modules.vitalia.sales_agent.domain.enums.screening_outcome import (
            ScreeningOutcome,
        )

        assert ScreeningOutcome.OK_PROCEED == "ok_proceed"
        assert ScreeningOutcome.DERIVAR_EMERGENCIA == "derivar_emergencia"
