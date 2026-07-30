"""Tests for LivePreviewService — TDD RED first (T-onboarding-2).

Tests cover:
1. generate_whatsapp_preview — happy: draft found, simulate returns sample
2. generate_whatsapp_preview — cached: simulate_service returns cached flag
3. generate_whatsapp_preview — missing draft raises ValueError
4. generate_landing_snippet — happy: draft with payload returns HTML + sections_included
5. test_extract_tenant_context_integration_url_only — URL + text_content flow smoke
6. test_audio_deferred_skip — confirms audio path is deferred to Slice 2

downstream-regression-na: brand-local vitalia copilot live preview service (no engine pattern, no cross-brand mirror)
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

_TENANT_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_DRAFT_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(tz=timezone.utc)


def _make_draft(
    draft_id: UUID = _DRAFT_ID,
    tenant_id: UUID = _TENANT_A,
    voice_profile_partial_json: dict | None = None,
    draft_payload: dict | None = None,
) -> MagicMock:
    """Build a mock BrandStudioDraft with realistic field values."""
    draft = MagicMock()
    draft.id = draft_id
    draft.tenant_id = tenant_id
    draft.draft_kind = "onboarding_extraction"
    draft.voice_profile_partial_json = voice_profile_partial_json or {"tone": "warm"}
    draft.draft_payload = draft_payload or {}
    draft.committed_at = None
    draft.expires_at = None
    draft.created_at = _utc_now()
    draft.updated_at = _utc_now()
    return draft


def _make_simulate_response(sample_text: str, cache_hit: bool = False) -> MagicMock:
    """Build a mock SimulateResponse."""
    resp = MagicMock()
    resp.sample_text = sample_text
    resp.cache_hit = cache_hit
    resp.generated_at = _utc_now().isoformat()
    return resp


class TestLivePreviewServiceWhatsApp:
    """Test suite for generate_whatsapp_preview."""

    @pytest.mark.asyncio
    async def test_generate_whatsapp_preview_happy(self) -> None:
        """Happy path: draft exists + simulate returns sample → returns dict with sample_text."""
        from src.modules.vitalia.copilot.application.services.live_preview_service import (
            LivePreviewService,
        )

        draft = _make_draft(voice_profile_partial_json={"tone": "warm", "name": "Clínica Salud"})
        simulate_response = _make_simulate_response("Hola, ¿en qué te puedo ayudar hoy?")

        draft_repo = AsyncMock()
        draft_repo.get_by_id_tenant.return_value = draft

        simulate_service = AsyncMock()
        simulate_service.simulate.return_value = simulate_response

        svc = LivePreviewService(simulate_service=simulate_service, draft_repo=draft_repo)

        result = await svc.generate_whatsapp_preview(
            tenant_id=_TENANT_A,
            draft_id=_DRAFT_ID,
            scenario="appointment_inquiry",
        )

        assert isinstance(result, dict)
        assert "sample_text" in result
        assert result["sample_text"] == "Hola, ¿en qué te puedo ayudar hoy?"
        assert "cached" in result
        assert "throttled" in result
        assert result["throttled"] is False

        # Verify tenant isolation: simulate called with correct tenant_id
        simulate_service.simulate.assert_called_once()
        call_kwargs = simulate_service.simulate.call_args.kwargs
        assert call_kwargs["tenant_id"] == _TENANT_A

    @pytest.mark.asyncio
    async def test_generate_whatsapp_preview_cached(self) -> None:
        """Second call with cached simulate response sets cached=True in result."""
        from src.modules.vitalia.copilot.application.services.live_preview_service import (
            LivePreviewService,
        )

        draft = _make_draft(voice_profile_partial_json={"tone": "professional"})
        simulate_response = _make_simulate_response(
            "Bienvenido, estamos para ayudarle.",
            cache_hit=True,
        )

        draft_repo = AsyncMock()
        draft_repo.get_by_id_tenant.return_value = draft

        simulate_service = AsyncMock()
        simulate_service.simulate.return_value = simulate_response

        svc = LivePreviewService(simulate_service=simulate_service, draft_repo=draft_repo)

        result = await svc.generate_whatsapp_preview(
            tenant_id=_TENANT_A,
            draft_id=_DRAFT_ID,
            scenario="appointment_inquiry",
        )

        # cached flag reflects simulate_service.simulate cache_hit
        assert result["cached"] is True

    @pytest.mark.asyncio
    async def test_generate_whatsapp_preview_no_draft_raises_value_error(self) -> None:
        """Missing draft raises ValueError (not HTTP exception — service layer)."""
        from src.modules.vitalia.copilot.application.services.live_preview_service import (
            LivePreviewService,
        )

        draft_repo = AsyncMock()
        draft_repo.get_by_id_tenant.return_value = None  # draft not found

        simulate_service = AsyncMock()

        svc = LivePreviewService(simulate_service=simulate_service, draft_repo=draft_repo)

        with pytest.raises(ValueError, match=str(_DRAFT_ID)):
            await svc.generate_whatsapp_preview(
                tenant_id=_TENANT_A,
                draft_id=_DRAFT_ID,
                scenario="appointment_inquiry",
            )

        # simulate must not be called when draft is missing
        simulate_service.simulate.assert_not_called()


class TestLivePreviewServiceLanding:
    """Test suite for generate_landing_snippet."""

    @pytest.mark.asyncio
    async def test_generate_landing_snippet_happy(self) -> None:
        """Happy path: draft with brand identity returns HTML snippet + sections_included."""
        from src.modules.vitalia.copilot.application.services.live_preview_service import (
            LivePreviewService,
        )

        brand_payload = {
            "brand_name": "Clínica Bienestar",
            "tagline": "Tu salud, nuestra prioridad",
            "vertical": "salud_estetica",
        }
        draft = _make_draft(draft_payload=brand_payload)

        draft_repo = AsyncMock()
        draft_repo.get_by_id_tenant.return_value = draft

        simulate_service = AsyncMock()

        svc = LivePreviewService(simulate_service=simulate_service, draft_repo=draft_repo)

        result = await svc.generate_landing_snippet(
            tenant_id=_TENANT_A,
            draft_id=_DRAFT_ID,
        )

        assert isinstance(result, dict)
        assert "html" in result
        assert "sections_included" in result
        # HTML must contain at least some brand content
        assert isinstance(result["html"], str)
        assert len(result["html"]) > 0
        # Sections included matches draft_payload keys
        assert set(result["sections_included"]) == set(brand_payload.keys())

    @pytest.mark.asyncio
    async def test_generate_landing_snippet_empty_payload(self) -> None:
        """Draft with empty payload returns HTML (minimal skeleton) + empty sections_included."""
        from src.modules.vitalia.copilot.application.services.live_preview_service import (
            LivePreviewService,
        )

        draft = _make_draft(draft_payload={})

        draft_repo = AsyncMock()
        draft_repo.get_by_id_tenant.return_value = draft

        simulate_service = AsyncMock()

        svc = LivePreviewService(simulate_service=simulate_service, draft_repo=draft_repo)

        result = await svc.generate_landing_snippet(
            tenant_id=_TENANT_A,
            draft_id=_DRAFT_ID,
        )

        assert isinstance(result, dict)
        assert "html" in result
        assert isinstance(result["html"], str)
        assert result["sections_included"] == []

    @pytest.mark.asyncio
    async def test_generate_landing_snippet_no_draft_raises_value_error(self) -> None:
        """Missing draft raises ValueError."""
        from src.modules.vitalia.copilot.application.services.live_preview_service import (
            LivePreviewService,
        )

        draft_repo = AsyncMock()
        draft_repo.get_by_id_tenant.return_value = None

        simulate_service = AsyncMock()

        svc = LivePreviewService(simulate_service=simulate_service, draft_repo=draft_repo)

        with pytest.raises(ValueError, match=str(_DRAFT_ID)):
            await svc.generate_landing_snippet(
                tenant_id=_TENANT_A,
                draft_id=_DRAFT_ID,
            )


class TestExtractTenantContextIntegration:
    """Integration tests for ExtractTenantContextService URL + text_content flow.

    Audio path deferred to Slice 2 per OQ-3 ratification (Chris 2026-05-18).
    Uses OnboardingDraft (the entity extract_tenant_context_service returns)
    via mock to test adapter dispatch without real DB access.
    """

    @pytest.mark.asyncio
    async def test_extract_url_only_flow(self) -> None:
        """URL-only extraction: scraper called, draft slots updated with extracted values."""
        from src.modules.vitalia.copilot.application.services.extract_tenant_context_service import (
            ExtractTenantContextService,
        )
        from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft

        scraper_result = {
            "brand_name": ("Clínica Salud Total", 0.92),
            "vertical": ("salud_dental", 0.85),
        }

        # Build a real OnboardingDraft entity for slot merging to work correctly
        draft = OnboardingDraft(
            id=_DRAFT_ID,
            tenant_id=_TENANT_A,
            user_id=uuid4(),
            clinic_id=None,
            mode="guiado",
            slots_required={},
            slots_optional={},
            bonus_extracted={},
            consent_voice_activation=False,
            created_at=_utc_now(),
            updated_at=_utc_now(),
            deleted_at=None,
            completed_at=None,
        )

        draft_repo = AsyncMock()
        draft_repo.get_by_id.return_value = draft
        draft_repo.save.return_value = draft

        website_scraper = AsyncMock()
        website_scraper.extract.return_value = scraper_result

        document_extractor = AsyncMock()

        svc = ExtractTenantContextService(
            draft_repo=draft_repo,
            website_scraper=website_scraper,
            document_extractor=document_extractor,
        )

        result = await svc.extract(
            draft_id=_DRAFT_ID,
            tenant_id=_TENANT_A,
            url="https://clinicasaludtotal.example.com",
            text_content=None,
        )

        # Website scraper called with correct url + tenant_id
        website_scraper.extract.assert_called_once_with(
            url="https://clinicasaludtotal.example.com",
            tenant_id=_TENANT_A,
        )
        # Document extractor NOT called when text_content is None
        document_extractor.extract.assert_not_called()

        # Draft repo save called with updated draft
        draft_repo.save.assert_called_once()
        assert result is draft

        # Extracted slots stored in bonus_extracted (not in required/optional)
        assert "brand_name" in draft.bonus_extracted
        assert "vertical" in draft.bonus_extracted

    @pytest.mark.asyncio
    async def test_extract_text_content_only_flow(self) -> None:
        """text_content-only extraction: document extractor called, scraper not called."""
        from src.modules.vitalia.copilot.application.services.extract_tenant_context_service import (
            ExtractTenantContextService,
        )
        from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft

        doc_result = {
            "location": ("Buenos Aires, Argentina", 0.88),
        }

        draft = OnboardingDraft(
            id=_DRAFT_ID,
            tenant_id=_TENANT_A,
            user_id=uuid4(),
            clinic_id=None,
            mode="guiado",
            slots_required={},
            slots_optional={},
            bonus_extracted={},
            consent_voice_activation=False,
            created_at=_utc_now(),
            updated_at=_utc_now(),
            deleted_at=None,
            completed_at=None,
        )

        draft_repo = AsyncMock()
        draft_repo.get_by_id.return_value = draft
        draft_repo.save.return_value = draft

        website_scraper = AsyncMock()
        document_extractor = AsyncMock()
        document_extractor.extract.return_value = doc_result

        svc = ExtractTenantContextService(
            draft_repo=draft_repo,
            website_scraper=website_scraper,
            document_extractor=document_extractor,
        )

        await svc.extract(
            draft_id=_DRAFT_ID,
            tenant_id=_TENANT_A,
            url=None,
            text_content="Somos una clínica ubicada en Buenos Aires.",
        )

        # Scraper NOT called when url is None
        website_scraper.extract.assert_not_called()
        # Document extractor called with correct args
        document_extractor.extract.assert_called_once_with(
            text="Somos una clínica ubicada en Buenos Aires.",
            tenant_id=_TENANT_A,
        )
        # Extracted slot stored in bonus_extracted
        assert "location" in draft.bonus_extracted

    @pytest.mark.skip(reason="Audio Whisper STT deferred Slice 2 per Chris 2026-05-18 (OQ-3 ratified)")
    @pytest.mark.asyncio
    async def test_audio_path_deferred(self) -> None:
        """Placeholder: audio_uploads path will be implemented in Slice 2 via Whisper STT."""
        # This test is intentionally skipped.
        # When Slice 2 implements audio_transcriber.py, remove the skip marker
        # and implement the audio extraction flow here.
        pass
