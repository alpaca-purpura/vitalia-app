"""Tests for VoiceBlocklistService — CRUD + seed + override log.

Verifies:
  - list_for_tenant delegates to repo with tenant_id
  - log_warning_override returns UUID (not tenant_id sentinel)
  - audit write action=voice_warning_overridden
  - seed_defaults_pe() returns 10 PE phrases

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import (
    ProhibitedPhrasesListDTO,
    VoiceWarningOverrideRequestDTO,
)
from src.modules.vitalia.brand_studio.application.services.voice_blocklist_service import VoiceBlocklistService
from src.modules.vitalia.brand_studio.domain.prohibited_phrase import (
    ProhibitedPhrase,
    ProhibitedPhraseSeverity,
)

pytestmark = pytest.mark.integration

_TENANT_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_USER_A = UUID("11111111-1111-1111-1111-111111111111")
_PHRASE_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.list_for_tenant.return_value = []
    repo.get_by_id.return_value = ProhibitedPhrase(
        id=_PHRASE_ID,
        phrase="curamos",
        severity=ProhibitedPhraseSeverity.HIGH.value,
    )
    return repo


@pytest.fixture
def mock_audit() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(mock_repo: AsyncMock, mock_audit: AsyncMock) -> VoiceBlocklistService:
    return VoiceBlocklistService(repo=mock_repo, audit=mock_audit)


class TestVoiceBlocklistServiceListForTenant:
    """list_for_tenant delegates + returns DTO."""

    @pytest.mark.asyncio
    async def test_list_for_tenant_returns_dto(
        self,
        service: VoiceBlocklistService,
        mock_repo: AsyncMock,
    ) -> None:
        result = await service.list_for_tenant(tenant_id=_TENANT_A)
        assert isinstance(result, ProhibitedPhrasesListDTO)

    @pytest.mark.asyncio
    async def test_list_for_tenant_delegates_to_repo(
        self,
        service: VoiceBlocklistService,
        mock_repo: AsyncMock,
    ) -> None:
        await service.list_for_tenant(tenant_id=_TENANT_A)
        mock_repo.list_for_tenant.assert_called_once()
        call_kwargs = mock_repo.list_for_tenant.call_args.kwargs
        assert call_kwargs["tenant_id"] == _TENANT_A

    @pytest.mark.asyncio
    async def test_list_for_tenant_passes_country_filter(
        self,
        service: VoiceBlocklistService,
        mock_repo: AsyncMock,
    ) -> None:
        await service.list_for_tenant(tenant_id=_TENANT_A, country="PE")
        call_kwargs = mock_repo.list_for_tenant.call_args.kwargs
        assert call_kwargs["country"] == "PE"

    @pytest.mark.asyncio
    async def test_list_for_tenant_total_matches_items(
        self,
        service: VoiceBlocklistService,
        mock_repo: AsyncMock,
    ) -> None:
        phrases = [
            ProhibitedPhrase(phrase="curamos", country_scope="PE"),
            ProhibitedPhrase(phrase="garantizado", country_scope="PE"),
        ]
        mock_repo.list_for_tenant.return_value = phrases
        result = await service.list_for_tenant(tenant_id=_TENANT_A)
        assert result.total == 2
        assert len(result.items) == 2


class TestVoiceBlocklistServiceLogWarningOverride:
    """log_warning_override — returns UUID (F5 fix)."""

    @pytest.mark.asyncio
    async def test_log_warning_override_returns_uuid(
        self,
        service: VoiceBlocklistService,
        mock_audit: AsyncMock,
    ) -> None:
        """F5: return value debe ser UUID, no tenant_id sentinel."""
        request = VoiceWarningOverrideRequestDTO(
            phrase_id=_PHRASE_ID,
            section="so_i_speak",
            user_text_excerpt="texto de prueba",
        )
        result = await service.log_warning_override(
            tenant_id=_TENANT_A,
            user_id=_USER_A,
            request=request,
        )
        # Debe ser UUID
        assert isinstance(result, UUID)
        # NO debe ser el tenant_id (era el bug F5)
        assert result != _TENANT_A

    @pytest.mark.asyncio
    async def test_log_warning_override_writes_audit_log(
        self,
        service: VoiceBlocklistService,
        mock_audit: AsyncMock,
    ) -> None:
        request = VoiceWarningOverrideRequestDTO(
            phrase_id=_PHRASE_ID,
            section="so_i_speak",
            user_text_excerpt="texto de prueba",
        )
        await service.log_warning_override(
            tenant_id=_TENANT_A,
            user_id=_USER_A,
            request=request,
        )
        mock_audit.write.assert_called_once()
        call_kwargs = mock_audit.write.call_args.kwargs
        assert call_kwargs["action"] == "voice_warning_overridden"
        assert call_kwargs["tenant_id"] == _TENANT_A
        assert call_kwargs["user_id"] == _USER_A

    @pytest.mark.asyncio
    async def test_log_warning_override_audit_payload_has_phrase_id(
        self,
        service: VoiceBlocklistService,
        mock_audit: AsyncMock,
    ) -> None:
        request = VoiceWarningOverrideRequestDTO(
            phrase_id=_PHRASE_ID,
            section="so_i_speak",
            user_text_excerpt="texto",
        )
        await service.log_warning_override(
            tenant_id=_TENANT_A,
            user_id=_USER_A,
            request=request,
        )
        call_kwargs = mock_audit.write.call_args.kwargs
        payload = call_kwargs["payload"]
        assert "phrase_id" in payload
        assert payload["phrase_id"] == str(_PHRASE_ID)

    @pytest.mark.asyncio
    async def test_log_warning_override_each_call_returns_unique_id(
        self,
        service: VoiceBlocklistService,
        mock_audit: AsyncMock,
    ) -> None:
        """Cada llamada retorna UUID diferente (uuid4)."""
        request = VoiceWarningOverrideRequestDTO(
            phrase_id=_PHRASE_ID,
            section="so_i_speak",
            user_text_excerpt="texto",
        )
        result_1 = await service.log_warning_override(
            tenant_id=_TENANT_A,
            user_id=_USER_A,
            request=request,
        )
        result_2 = await service.log_warning_override(
            tenant_id=_TENANT_A,
            user_id=_USER_A,
            request=request,
        )
        assert result_1 != result_2


class TestVoiceBlocklistServiceSeedDefaults:
    """seed_defaults_pe() — 10 PE phrases."""

    def test_seed_defaults_pe_returns_10_phrases(self) -> None:
        seeds = VoiceBlocklistService.seed_defaults_pe()
        assert len(seeds) == 10

    def test_seed_defaults_pe_all_have_country_pe(self) -> None:
        seeds = VoiceBlocklistService.seed_defaults_pe()
        assert all(s.country_scope == "PE" for s in seeds)

    def test_seed_defaults_pe_includes_curamos(self) -> None:
        seeds = VoiceBlocklistService.seed_defaults_pe()
        phrases = [s.phrase for s in seeds]
        assert "curamos" in phrases

    def test_seed_defaults_pe_all_have_suggested_alternative(self) -> None:
        seeds = VoiceBlocklistService.seed_defaults_pe()
        assert all(s.suggested_alternative for s in seeds)

    def test_seed_defaults_pe_high_severity_count(self) -> None:
        """Al menos 5 frases deben ser HIGH severity (regulación)."""
        seeds = VoiceBlocklistService.seed_defaults_pe()
        high_count = sum(1 for s in seeds if s.severity == ProhibitedPhraseSeverity.HIGH.value)
        assert high_count >= 5
