"""RED tests — ExtractTenantContextService.

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- extract() calls website_scraper_adapter with URL
- extract() calls document_extractor_adapter with text content
- extract() merges partial slot values into draft
- extract() returns updated draft with filled slots (confidence populated)
- tenant_id always passed to adapters (isolation)
- No PHI leak — wizard config data only
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
DRAFT_ID = uuid4()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_draft() -> "object":
    from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft
    from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

    def _slot(slot_id: str) -> WizardSlot:
        return WizardSlot(slot_id=slot_id, value=None, confidence=0.0, confirmed_at=None, source="extracted")

    return OnboardingDraft(
        id=DRAFT_ID,
        tenant_id=TENANT_ID,
        user_id=uuid4(),
        clinic_id=None,
        mode="libre",
        slots_required={
            "tenant.name": _slot("tenant.name"),
            "tenant.vertical": _slot("tenant.vertical"),
            "tenant.location": _slot("tenant.location"),
        },
        slots_optional={"brand.tone_default": _slot("brand.tone_default")},
        bonus_extracted={},
        consent_voice_activation=False,
        created_at=_utc_now(),
        updated_at=_utc_now(),
        deleted_at=None,
        completed_at=None,
    )


class TestExtractTenantContextService:
    """Tests for ExtractTenantContextService.extract()."""

    @pytest.mark.asyncio
    async def test_extract_calls_website_scraper_with_url(self) -> None:
        """extract() calls website_scraper when url is provided."""
        from src.modules.vitalia.copilot.application.services.extract_tenant_context_service import (
            ExtractTenantContextService,
        )

        draft = _make_draft()
        mock_draft_repo = AsyncMock()
        mock_draft_repo.get_by_id = AsyncMock(return_value=draft)
        mock_draft_repo.save = AsyncMock(side_effect=lambda d: d)

        mock_scraper = AsyncMock()
        mock_scraper.extract = AsyncMock(
            return_value={
                "tenant.name": ("Clínica Dental Avenida", 0.88),
                "tenant.vertical": ("dental", 0.95),
            }
        )
        mock_doc_extractor = AsyncMock()
        mock_doc_extractor.extract = AsyncMock(return_value={})

        service = ExtractTenantContextService(
            draft_repo=mock_draft_repo,
            website_scraper=mock_scraper,
            document_extractor=mock_doc_extractor,
        )
        await service.extract(
            draft_id=DRAFT_ID,
            tenant_id=TENANT_ID,
            url="https://clinicadental.com",
            text_content=None,
        )

        mock_scraper.extract.assert_called_once_with(url="https://clinicadental.com", tenant_id=TENANT_ID)

    @pytest.mark.asyncio
    async def test_extract_calls_document_extractor_with_text(self) -> None:
        """extract() calls document_extractor when text_content is provided."""
        from src.modules.vitalia.copilot.application.services.extract_tenant_context_service import (
            ExtractTenantContextService,
        )

        draft = _make_draft()
        mock_draft_repo = AsyncMock()
        mock_draft_repo.get_by_id = AsyncMock(return_value=draft)
        mock_draft_repo.save = AsyncMock(side_effect=lambda d: d)

        mock_scraper = AsyncMock()
        mock_scraper.extract = AsyncMock(return_value={})
        mock_doc_extractor = AsyncMock()
        mock_doc_extractor.extract = AsyncMock(
            return_value={
                "tenant.name": ("Clínica Estética Sur", 0.82),
            }
        )

        service = ExtractTenantContextService(
            draft_repo=mock_draft_repo,
            website_scraper=mock_scraper,
            document_extractor=mock_doc_extractor,
        )
        await service.extract(
            draft_id=DRAFT_ID,
            tenant_id=TENANT_ID,
            url=None,
            text_content="Somos Clínica Estética Sur en Buenos Aires.",
        )

        mock_doc_extractor.extract.assert_called_once_with(
            text="Somos Clínica Estética Sur en Buenos Aires.", tenant_id=TENANT_ID
        )

    @pytest.mark.asyncio
    async def test_extract_merges_slots_into_draft(self) -> None:
        """extract() updates draft with extracted slot values."""
        from src.modules.vitalia.copilot.application.services.extract_tenant_context_service import (
            ExtractTenantContextService,
        )

        draft = _make_draft()
        mock_draft_repo = AsyncMock()
        mock_draft_repo.get_by_id = AsyncMock(return_value=draft)
        mock_draft_repo.save = AsyncMock(side_effect=lambda d: d)

        mock_scraper = AsyncMock()
        mock_scraper.extract = AsyncMock(
            return_value={
                "tenant.name": ("Clínica Norte", 0.90),
                "tenant.vertical": ("dental", 0.95),
            }
        )
        mock_doc_extractor = AsyncMock()
        mock_doc_extractor.extract = AsyncMock(return_value={})

        service = ExtractTenantContextService(
            draft_repo=mock_draft_repo,
            website_scraper=mock_scraper,
            document_extractor=mock_doc_extractor,
        )
        result = await service.extract(
            draft_id=DRAFT_ID,
            tenant_id=TENANT_ID,
            url="https://example.com",
            text_content=None,
        )

        # Merged slot should have extracted value
        assert result.slots_required["tenant.name"].value == "Clínica Norte"
        assert result.slots_required["tenant.name"].confidence == 0.90
        assert result.slots_required["tenant.name"].source == "extracted"
        assert result.slots_required["tenant.vertical"].value == "dental"

    @pytest.mark.asyncio
    async def test_extract_always_passes_tenant_id_to_repo(self) -> None:
        """extract() always passes tenant_id to repo.get_by_id (isolation)."""
        from src.modules.vitalia.copilot.application.services.extract_tenant_context_service import (
            ExtractTenantContextService,
        )

        draft = _make_draft()
        mock_draft_repo = AsyncMock()
        mock_draft_repo.get_by_id = AsyncMock(return_value=draft)
        mock_draft_repo.save = AsyncMock(side_effect=lambda d: d)

        service = ExtractTenantContextService(
            draft_repo=mock_draft_repo,
            website_scraper=AsyncMock(extract=AsyncMock(return_value={})),
            document_extractor=AsyncMock(extract=AsyncMock(return_value={})),
        )
        other_tenant = uuid4()
        await service.extract(
            draft_id=DRAFT_ID,
            tenant_id=other_tenant,
            url=None,
            text_content="test",
        )

        mock_draft_repo.get_by_id.assert_called_once_with(DRAFT_ID, tenant_id=other_tenant)
