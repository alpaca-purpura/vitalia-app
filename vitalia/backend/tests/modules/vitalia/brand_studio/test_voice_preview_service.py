"""Tests unitarios para VoicePreviewService — cache LRU in-process.

OQ-C resolution (CONTEXT-BRIEF.md 2026-05-27): VoicePreviewService compila
slot 5 BRAND_VOICE determinísticamente (sin LLM) con cache LRU in-process.

Verifica:
  - CACHE HIT: misma entrada (tenant_id + profile_id + blocks) → retorna cached=True
  - CACHE MISS: entrada nueva → cached=False + compila
  - Invalidación por tenant: eliminate las entries del tenant_id dado
  - Retorno 3-tuple: (sample_whatsapp, sample_email, cache_hit: bool)
  - Cache key segmenta por tenant (no cross-tenant leak)

T-3 — F2-S7 vitalia-fase2-lisa-marca.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.modules.vitalia.brand_studio.application.services.voice_preview_service import (
    _PREVIEW_CACHE,
    VoicePreviewService,
    _build_cache_key,
    _hash_blocks,
)

# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_preview_cache() -> None:
    """Limpia el cache in-process antes de cada test."""
    _PREVIEW_CACHE.clear()
    yield
    _PREVIEW_CACHE.clear()


@pytest.fixture
def tenant_a() -> UUID:
    return UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def tenant_b() -> UUID:
    return UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def profile_id() -> UUID:
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def sample_blocks() -> dict:
    return {
        "archetype": "cuidador",
        "tone": "cálido",
        "voice_adjectives": ["confiable", "cercano"],
    }


@pytest.fixture
def sample_instruction() -> str:
    return "## ASÍ HABLO\nAcompaño con calidez y precisión clínica.\nMe expreso con claridad y empatía genuina.\n"


@pytest.fixture
def svc() -> VoicePreviewService:
    return VoicePreviewService()


# ─── Tests ───────────────────────────────────────────────────────────────────


class TestVoicePreviewCacheHit:
    """Misma entrada debe retornar cache_hit=True en la segunda llamada."""

    @pytest.mark.asyncio
    async def test_first_call_is_cache_miss(
        self,
        svc: VoicePreviewService,
        tenant_a: UUID,
        profile_id: UUID,
        sample_blocks: dict,
        sample_instruction: str,
    ) -> None:
        """La primera llamada compila y retorna cache_hit=False."""
        wa, email, cache_hit = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        assert cache_hit is False
        assert len(wa) > 0
        assert len(email) > 0

    @pytest.mark.asyncio
    async def test_second_call_is_cache_hit(
        self,
        svc: VoicePreviewService,
        tenant_a: UUID,
        profile_id: UUID,
        sample_blocks: dict,
        sample_instruction: str,
    ) -> None:
        """La segunda llamada con los mismos datos retorna cache_hit=True."""
        # Primera llamada — MISS
        await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )

        # Segunda llamada con exactamente los mismos parámetros — HIT
        wa, email, cache_hit = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        assert cache_hit is True
        assert len(wa) > 0
        assert len(email) > 0

    @pytest.mark.asyncio
    async def test_cache_hit_returns_same_content(
        self,
        svc: VoicePreviewService,
        tenant_a: UUID,
        profile_id: UUID,
        sample_blocks: dict,
        sample_instruction: str,
    ) -> None:
        """Cache hit debe retornar exactamente el mismo contenido que el miss inicial."""
        wa_miss, email_miss, _ = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        wa_hit, email_hit, cache_hit = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        assert cache_hit is True
        assert wa_hit == wa_miss
        assert email_hit == email_miss


class TestVoicePreviewCacheMiss:
    """Bloques distintos → MISS + recompilación."""

    @pytest.mark.asyncio
    async def test_different_blocks_is_cache_miss(
        self,
        svc: VoicePreviewService,
        tenant_a: UUID,
        profile_id: UUID,
        sample_instruction: str,
    ) -> None:
        """Bloques distintos generan cache key distinta → MISS."""
        blocks_v1 = {"archetype": "cuidador", "tone": "cálido"}
        blocks_v2 = {"archetype": "experto", "tone": "profesional"}

        _, _, miss1 = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=blocks_v1,
        )
        _, _, miss2 = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=blocks_v2,
        )
        assert miss1 is False
        assert miss2 is False

    @pytest.mark.asyncio
    async def test_different_profile_is_cache_miss(
        self,
        svc: VoicePreviewService,
        tenant_a: UUID,
        sample_blocks: dict,
        sample_instruction: str,
    ) -> None:
        """Profile ID distinto → cache key distinta → MISS."""
        profile_1 = uuid4()
        profile_2 = uuid4()

        _, _, miss1 = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_1,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        _, _, miss2 = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_2,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        assert miss1 is False
        assert miss2 is False


class TestVoicePreviewCacheIsolation:
    """Cache aislado por tenant — sin cross-tenant leak."""

    @pytest.mark.asyncio
    async def test_different_tenants_no_cross_cache(
        self,
        svc: VoicePreviewService,
        tenant_a: UUID,
        tenant_b: UUID,
        profile_id: UUID,
        sample_blocks: dict,
        sample_instruction: str,
    ) -> None:
        """Mismos bloques para tenant_a y tenant_b → MISS ambos (keys distintas)."""
        _, _, miss_a = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        # tenant_b tiene su propia key aunque los datos sean iguales
        _, _, miss_b = await svc.get_preview(
            tenant_id=tenant_b,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        assert miss_a is False  # Primera llamada tenant_a = MISS
        assert miss_b is False  # Primera llamada tenant_b = MISS (keys distintas)

    @pytest.mark.asyncio
    async def test_invalidate_removes_only_target_tenant_entries(
        self,
        svc: VoicePreviewService,
        tenant_a: UUID,
        tenant_b: UUID,
        profile_id: UUID,
        sample_blocks: dict,
        sample_instruction: str,
    ) -> None:
        """invalidate(tenant_id=A) solo elimina entries de tenant_a."""
        # Primer: cachear ambos tenants
        await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        await svc.get_preview(
            tenant_id=tenant_b,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )

        # Invalidar solo tenant_a
        await svc.invalidate(tenant_id=tenant_a)

        # tenant_a: MISS tras invalidar
        _, _, hit_a = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        # tenant_b: HIT — no fue invalidado
        _, _, hit_b = await svc.get_preview(
            tenant_id=tenant_b,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        assert hit_a is False  # cache fue limpiado para tenant_a
        assert hit_b is True  # tenant_b intacto


class TestVoicePreviewReturnShape:
    """Verifica que el retorno es 3-tuple (str, str, bool)."""

    @pytest.mark.asyncio
    async def test_returns_three_tuple(
        self,
        svc: VoicePreviewService,
        tenant_a: UUID,
        profile_id: UUID,
        sample_blocks: dict,
        sample_instruction: str,
    ) -> None:
        """get_preview retorna (whatsapp_sample, email_sample, cache_hit: bool)."""
        result = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=sample_instruction,
            blocks=sample_blocks,
        )
        assert len(result) == 3
        wa, email, cache_hit = result
        assert isinstance(wa, str)
        assert isinstance(email, str)
        assert isinstance(cache_hit, bool)

    @pytest.mark.asyncio
    async def test_empty_instruction_returns_fallback(
        self,
        svc: VoicePreviewService,
        tenant_a: UUID,
        profile_id: UUID,
    ) -> None:
        """Instrucción vacía → retorna fallback genérico (no None)."""
        wa, email, cache_hit = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction="",
            blocks={},
        )
        assert isinstance(wa, str) and len(wa) > 0
        assert isinstance(email, str) and len(email) > 0
        assert cache_hit is False


class TestVoicePreviewHelperFunctions:
    """Verifica funciones auxiliares de cache key y hash."""

    def test_hash_blocks_deterministic(self) -> None:
        """_hash_blocks debe ser determinístico — mismo input → mismo hash."""
        blocks = {"a": 1, "b": "test"}
        assert _hash_blocks(blocks) == _hash_blocks(blocks)

    def test_hash_blocks_different_for_different_input(self) -> None:
        """_hash_blocks debe ser distinto para inputs distintos."""
        b1 = {"archetype": "cuidador"}
        b2 = {"archetype": "experto"}
        assert _hash_blocks(b1) != _hash_blocks(b2)

    def test_hash_blocks_length(self) -> None:
        """_hash_blocks retorna 16 caracteres (SHA256 truncado)."""
        assert len(_hash_blocks({"x": 1})) == 16

    def test_build_cache_key_format(self) -> None:
        """_build_cache_key retorna clave con prefijo 'voice_preview:'."""
        tid = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        pid = UUID("11111111-1111-1111-1111-111111111111")
        key = _build_cache_key(tid, pid, "v2", "abcdef1234567890")
        assert key.startswith("voice_preview:")
        assert str(tid) in key
        assert str(pid) in key
        assert "v2" in key
        assert "abcdef1234567890" in key
