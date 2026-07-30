"""Tests unitarios — voice_warning_override escribe audit_log con action correcto.

Verifica el contrato de VoiceBlocklistService.log_warning_override:
  - Llama await self._audit.write(...) con action="voice_warning_overridden"
  - El write es sync (awaited) — no fire-and-forget
  - payload NO contiene PHI verbatim (sanitizado)
  - resource_type = "brand_personality"

No requiere Postgres — usa AsyncMock para audit_writer y repo.

T-3 — F2-S7 vitalia-fase2-lisa-marca (A4: voice_warning audit row).
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import VoiceWarningOverrideRequestDTO
from src.modules.vitalia.brand_studio.application.services.voice_blocklist_service import VoiceBlocklistService
from src.modules.vitalia.brand_studio.domain.prohibited_phrase import ProhibitedPhrase, ProhibitedPhraseSeverity

# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def tenant_id() -> UUID:
    return UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def user_id() -> UUID:
    return UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def phrase_id() -> UUID:
    return UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


@pytest.fixture
def mock_phrase(phrase_id: UUID, tenant_id: UUID) -> ProhibitedPhrase:
    """Prohibited phrase domain entity simulada."""
    return ProhibitedPhrase(
        id=phrase_id,
        tenant_id=None,  # seed
        phrase="curamos",
        suggested_alternative="acompañamos tu tratamiento",
        severity=ProhibitedPhraseSeverity.HIGH.value,
        country_scope="PE",
    )


@pytest.fixture
def mock_repo(mock_phrase: ProhibitedPhrase) -> AsyncMock:
    """Mock ProhibitedPhraseRepository."""
    repo = AsyncMock()
    repo.get_by_id.return_value = mock_phrase
    return repo


@pytest.fixture
def mock_audit() -> AsyncMock:
    """Mock AsyncAuditWriter — captura llamadas a write()."""
    audit = AsyncMock()
    audit.write = AsyncMock(return_value=None)
    return audit


@pytest.fixture
def svc(mock_repo: AsyncMock, mock_audit: AsyncMock) -> VoiceBlocklistService:
    return VoiceBlocklistService(repo=mock_repo, audit=mock_audit)


@pytest.fixture
def override_request(phrase_id: UUID) -> VoiceWarningOverrideRequestDTO:
    return VoiceWarningOverrideRequestDTO(
        phrase_id=phrase_id,
        section="so_i_speak",
        user_text_excerpt="Queremos garantizar resultados",
    )


# ─── Tests ───────────────────────────────────────────────────────────────────


class TestVoiceWarningAuditLogAction:
    """log_warning_override debe escribir audit row con action correcto."""

    @pytest.mark.asyncio
    async def test_audit_write_called_once(
        self,
        svc: VoiceBlocklistService,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
        override_request: VoiceWarningOverrideRequestDTO,
    ) -> None:
        """audit.write() debe llamarse exactamente 1 vez por override."""
        await svc.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=override_request,
        )
        mock_audit.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_audit_action_is_voice_warning_overridden(
        self,
        svc: VoiceBlocklistService,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
        override_request: VoiceWarningOverrideRequestDTO,
    ) -> None:
        """El action debe ser exactamente 'voice_warning_overridden'."""
        await svc.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=override_request,
        )
        call_kwargs = mock_audit.write.call_args.kwargs
        assert call_kwargs["action"] == "voice_warning_overridden", (
            f"action esperado: 'voice_warning_overridden', recibido: '{call_kwargs['action']}'"
        )

    @pytest.mark.asyncio
    async def test_audit_resource_type_is_brand_personality(
        self,
        svc: VoiceBlocklistService,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
        override_request: VoiceWarningOverrideRequestDTO,
    ) -> None:
        """resource_type debe ser 'brand_personality'."""
        await svc.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=override_request,
        )
        call_kwargs = mock_audit.write.call_args.kwargs
        assert call_kwargs["resource_type"] == "brand_personality"

    @pytest.mark.asyncio
    async def test_audit_tenant_id_passed(
        self,
        svc: VoiceBlocklistService,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
        override_request: VoiceWarningOverrideRequestDTO,
    ) -> None:
        """tenant_id correcto debe pasarse al audit writer."""
        await svc.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=override_request,
        )
        call_kwargs = mock_audit.write.call_args.kwargs
        assert call_kwargs["tenant_id"] == tenant_id

    @pytest.mark.asyncio
    async def test_audit_user_id_passed(
        self,
        svc: VoiceBlocklistService,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
        override_request: VoiceWarningOverrideRequestDTO,
    ) -> None:
        """user_id correcto debe pasarse al audit writer."""
        await svc.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=override_request,
        )
        call_kwargs = mock_audit.write.call_args.kwargs
        assert call_kwargs["user_id"] == user_id


class TestVoiceWarningAuditNoRawPHI:
    """Payload en audit row NO debe contener texto verbatim del usuario (PHI)."""

    @pytest.mark.asyncio
    async def test_payload_has_no_user_text_raw(
        self,
        svc: VoiceBlocklistService,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
        phrase_id: UUID,
    ) -> None:
        """user_text_excerpt NO debe aparecer en el payload del audit row.

        Razón: user_text_excerpt puede contener diagnósticos o información
        sensible. El audit row solo registra phrase_id + section + severity.
        """
        sensitive_excerpt = "El paciente fue diagnosticado con diabetes"
        request = VoiceWarningOverrideRequestDTO(
            phrase_id=phrase_id,
            section="so_i_speak",
            user_text_excerpt=sensitive_excerpt,
        )
        await svc.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=request,
        )
        call_kwargs = mock_audit.write.call_args.kwargs
        payload = call_kwargs.get("payload", {})
        # El excerpt raw NO debe estar en el payload
        payload_str = str(payload)
        assert sensitive_excerpt not in payload_str, (
            "HIPAA-lite VIOLATION: user_text_excerpt raw en audit payload. "
            "El audit payload debe contener solo phrase_id + section + severity."
        )

    @pytest.mark.asyncio
    async def test_payload_contains_phrase_id(
        self,
        svc: VoiceBlocklistService,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
        override_request: VoiceWarningOverrideRequestDTO,
        phrase_id: UUID,
    ) -> None:
        """El payload del audit debe contener phrase_id para trazabilidad."""
        await svc.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=override_request,
        )
        call_kwargs = mock_audit.write.call_args.kwargs
        payload = call_kwargs.get("payload", {})
        assert "phrase_id" in payload, "Payload debe incluir phrase_id para trazabilidad"
        assert str(phrase_id) == payload["phrase_id"]

    @pytest.mark.asyncio
    async def test_payload_contains_section(
        self,
        svc: VoiceBlocklistService,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
        override_request: VoiceWarningOverrideRequestDTO,
    ) -> None:
        """El payload del audit debe contener section (sección de brand_studio)."""
        await svc.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=override_request,
        )
        call_kwargs = mock_audit.write.call_args.kwargs
        payload = call_kwargs.get("payload", {})
        assert "section" in payload
        assert payload["section"] == "so_i_speak"

    @pytest.mark.asyncio
    async def test_payload_contains_phrase_severity(
        self,
        svc: VoiceBlocklistService,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
        override_request: VoiceWarningOverrideRequestDTO,
    ) -> None:
        """El payload del audit debe contener phrase_severity (de la frase lookup)."""
        await svc.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=override_request,
        )
        call_kwargs = mock_audit.write.call_args.kwargs
        payload = call_kwargs.get("payload", {})
        assert "phrase_severity" in payload
        # La frase mock tiene severity=HIGH
        assert payload["phrase_severity"] == "high"


class TestVoiceWarningAuditWriteSyncBehavior:
    """audit.write() debe awaitearse (no fire-and-forget)."""

    @pytest.mark.asyncio
    async def test_audit_write_is_awaited(
        self,
        svc: VoiceBlocklistService,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
        override_request: VoiceWarningOverrideRequestDTO,
    ) -> None:
        """mock_audit.write debe ser AsyncMock — verifica que fue awaited."""
        await svc.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=override_request,
        )
        # AsyncMock.assert_awaited_once verifica que fue awaited (no schedulado)
        mock_audit.write.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_uuid(
        self,
        svc: VoiceBlocklistService,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
        override_request: VoiceWarningOverrideRequestDTO,
    ) -> None:
        """log_warning_override retorna UUID (audit_id sentinel)."""
        result = await svc.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=override_request,
        )
        assert isinstance(result, UUID)

    @pytest.mark.asyncio
    async def test_unknown_phrase_uses_severity_unknown(
        self,
        mock_audit: AsyncMock,
        tenant_id: UUID,
        user_id: UUID,
    ) -> None:
        """Si phrase no existe (None de repo), severity en payload = 'unknown'."""
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None  # phrase no encontrada

        svc_local = VoiceBlocklistService(repo=mock_repo, audit=mock_audit)
        request = VoiceWarningOverrideRequestDTO(
            phrase_id=uuid4(),
            section="so_i_dont_speak",
            user_text_excerpt="texto",
        )
        await svc_local.log_warning_override(
            tenant_id=tenant_id,
            user_id=user_id,
            request=request,
        )
        call_kwargs = mock_audit.write.call_args.kwargs
        payload = call_kwargs.get("payload", {})
        assert payload.get("phrase_severity") == "unknown"
