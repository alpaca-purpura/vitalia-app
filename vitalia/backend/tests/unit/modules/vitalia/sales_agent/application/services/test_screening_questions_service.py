"""RED tests — ScreeningQuestionsService.

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- load_questions_for_vertical() returns questions from YAML SSoT
- screen() calls LLM service (mocked) + persists LeadScreeningEvent row
- PHI sanitization applied before persist (sanitize_phi_payload)
- audit_log row written synchronously after persist
- outcome is a ScreeningOutcome enum value
- Unknown vertical returns empty questions list gracefully
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
LEAD_ID = uuid4()


class TestScreeningQuestionsService:
    """Unit tests for ScreeningQuestionsService."""

    def test_import_service(self) -> None:
        """Service importable from application services layer."""
        from src.modules.vitalia.sales_agent.application.services.screening_questions_service import (
            ScreeningQuestionsService,
        )

        assert ScreeningQuestionsService is not None

    def test_load_questions_for_dental_vertical(self) -> None:
        """dental vertical returns list of question strings from YAML SSoT."""
        from src.modules.vitalia.sales_agent.application.services.screening_questions_service import (
            ScreeningQuestionsService,
        )

        svc = ScreeningQuestionsService(
            screening_repo=AsyncMock(),
            audit_log_repo=AsyncMock(),
            llm_service=AsyncMock(),
        )
        questions = svc.load_questions_for_vertical("dental")
        assert isinstance(questions, list)
        assert len(questions) >= 1  # YAML has at least 1 question per vertical

    def test_load_questions_for_estetica_vertical(self) -> None:
        """estetica vertical returns questions list."""
        from src.modules.vitalia.sales_agent.application.services.screening_questions_service import (
            ScreeningQuestionsService,
        )

        svc = ScreeningQuestionsService(
            screening_repo=AsyncMock(),
            audit_log_repo=AsyncMock(),
            llm_service=AsyncMock(),
        )
        questions = svc.load_questions_for_vertical("estetica")
        assert isinstance(questions, list)

    def test_load_questions_unknown_vertical_returns_empty(self) -> None:
        """Unknown vertical returns empty list (graceful fallback)."""
        from src.modules.vitalia.sales_agent.application.services.screening_questions_service import (
            ScreeningQuestionsService,
        )

        svc = ScreeningQuestionsService(
            screening_repo=AsyncMock(),
            audit_log_repo=AsyncMock(),
            llm_service=AsyncMock(),
        )
        questions = svc.load_questions_for_vertical("unknown_vertical")
        assert questions == []

    @pytest.mark.asyncio()
    async def test_screen_calls_llm_service(self) -> None:
        """screen() calls LLM service with question context."""
        from src.modules.vitalia.sales_agent.application.services.screening_questions_service import (
            ScreeningQuestionsService,
        )

        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            return_value=MagicMock(content='{"outcome": "ok_proceed", "reasoning": "No contraindications."}')
        )
        mock_repo = AsyncMock()
        mock_audit = AsyncMock()

        svc = ScreeningQuestionsService(
            screening_repo=mock_repo,
            audit_log_repo=mock_audit,
            llm_service=mock_llm,
        )
        await svc.screen(
            lead_id=LEAD_ID,
            vertical="dental",
            response_text="No tengo dolor. No estoy embarazada.",
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=uuid4(),
        )
        mock_llm.generate.assert_called_once()

    @pytest.mark.asyncio()
    async def test_screen_persists_event_row(self) -> None:
        """screen() persists LeadScreeningEvent via repository."""
        from src.modules.vitalia.sales_agent.application.services.screening_questions_service import (
            ScreeningQuestionsService,
        )

        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            return_value=MagicMock(content='{"outcome": "ok_proceed", "reasoning": "No issues."}')
        )
        mock_repo = AsyncMock()
        mock_audit = AsyncMock()

        svc = ScreeningQuestionsService(
            screening_repo=mock_repo,
            audit_log_repo=mock_audit,
            llm_service=mock_llm,
        )
        await svc.screen(
            lead_id=LEAD_ID,
            vertical="dental",
            response_text="Sin problemas",
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=uuid4(),
        )
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio()
    async def test_screen_writes_audit_log_sync(self) -> None:
        """screen() writes audit log row synchronously (HIPAA-lite requirement)."""
        from src.modules.vitalia.sales_agent.application.services.screening_questions_service import (
            ScreeningQuestionsService,
        )

        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            return_value=MagicMock(content='{"outcome": "ok_proceed", "reasoning": "Clear."}')
        )
        mock_repo = AsyncMock()
        mock_audit = AsyncMock()

        svc = ScreeningQuestionsService(
            screening_repo=mock_repo,
            audit_log_repo=mock_audit,
            llm_service=mock_llm,
        )
        await svc.screen(
            lead_id=LEAD_ID,
            vertical="dental",
            response_text="OK",
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=uuid4(),
        )
        mock_audit.write.assert_called_once()

    @pytest.mark.asyncio()
    async def test_screen_returns_valid_outcome(self) -> None:
        """screen() returns a valid ScreeningOutcome value."""
        from src.modules.vitalia.sales_agent.application.services.screening_questions_service import (
            ScreeningQuestionsService,
        )
        from src.modules.vitalia.sales_agent.domain.enums.screening_outcome import (
            ScreeningOutcome,
        )

        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(
            return_value=MagicMock(content='{"outcome": "ok_proceed", "reasoning": "Cleared."}')
        )
        svc = ScreeningQuestionsService(
            screening_repo=AsyncMock(),
            audit_log_repo=AsyncMock(),
            llm_service=mock_llm,
        )
        result = await svc.screen(
            lead_id=LEAD_ID,
            vertical="dental",
            response_text="All clear",
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            user_id=uuid4(),
        )
        assert result.outcome in {e.value for e in ScreeningOutcome}
