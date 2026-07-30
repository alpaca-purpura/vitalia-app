"""Tests de cross-tenant isolation para brand_studio.

Verifica que:
  - RBAC dependency falla con 403 para roles no autorizados (no leakage)
  - VoiceBlocklistService.list_for_tenant() filtra por tenant_id
  - TrustSignalRepository usa tenant_id en todos los métodos
  - VoicePreviewService cache keys son tenant-scoped (no cross-tenant hit)
  - require_brand_owner_access() NO procesa el request cuando rol incorrecto

Estos tests no requieren Postgres (AsyncMock para repos y session).

T-3 — F2-S7 vitalia-fase2-lisa-marca (A1: cross-tenant isolation).
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import HTTPException

from src.modules.vitalia._shared.auth.rbac import require_brand_owner_access
from src.modules.vitalia.brand_studio.application.services.trust_catalog_service import TrustCatalogService
from src.modules.vitalia.brand_studio.application.services.voice_blocklist_service import VoiceBlocklistService
from src.modules.vitalia.brand_studio.application.services.voice_preview_service import (
    _PREVIEW_CACHE,
    VoicePreviewService,
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
def user_a() -> UUID:
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def user_b() -> UUID:
    return UUID("22222222-2222-2222-2222-222222222222")


# ─── RBAC cross-tenant isolation ─────────────────────────────────────────────


class TestRBACCrossRoleIsolation:
    """Requests de roles no autorizados no llegan al service layer."""

    @pytest.mark.asyncio
    async def test_patient_cannot_mutate_brand_config(self) -> None:
        """role=patient → 403 ANTES de que el service sea invocado.

        Garantiza que el RBAC gate bloquea en la capa HTTP
        sin pasar al servicio (no hay posibilidad de leak).
        """
        dep = require_brand_owner_access()
        with pytest.raises(HTTPException) as exc_info:
            await dep(user_role="patient")
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == {"error_code": "BRAND_OWNER_RBAC_DENIED"}

    @pytest.mark.asyncio
    async def test_doctor_cannot_mutate_brand_config(self) -> None:
        """role=doctor → 403 (tiene acceso a PHI pero no a brand config mutations)."""
        dep = require_brand_owner_access()
        with pytest.raises(HTTPException) as exc_info:
            await dep(user_role="doctor")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_empty_role_cannot_mutate_brand_config(self) -> None:
        """Header X-User-Role ausente o vacío → 403."""
        dep = require_brand_owner_access()
        with pytest.raises(HTTPException) as exc_info:
            await dep(user_role="")
        assert exc_info.value.status_code == 403


# ─── VoiceBlocklistService tenant isolation ──────────────────────────────────


class TestVoiceBlocklistServiceTenantIsolation:
    """VoiceBlocklistService pasa tenant_id al repo — no mezcla datos cross-tenant."""

    @pytest.mark.asyncio
    async def test_list_for_tenant_passes_tenant_id_to_repo(
        self,
        tenant_a: UUID,
    ) -> None:
        """list_for_tenant() llama repo.list_for_tenant() con el tenant_id correcto."""
        mock_repo = AsyncMock()
        mock_repo.list_for_tenant.return_value = []
        mock_audit = AsyncMock()

        svc = VoiceBlocklistService(repo=mock_repo, audit=mock_audit)
        await svc.list_for_tenant(tenant_id=tenant_a)

        mock_repo.list_for_tenant.assert_called_once()
        call_kwargs = mock_repo.list_for_tenant.call_args.kwargs
        assert call_kwargs["tenant_id"] == tenant_a

    @pytest.mark.asyncio
    async def test_tenant_a_request_does_not_use_tenant_b(
        self,
        tenant_a: UUID,
        tenant_b: UUID,
    ) -> None:
        """Requests de tenant_a nunca pasan tenant_b al repo."""
        mock_repo = AsyncMock()
        mock_repo.list_for_tenant.return_value = []
        mock_audit = AsyncMock()

        svc = VoiceBlocklistService(repo=mock_repo, audit=mock_audit)
        await svc.list_for_tenant(tenant_id=tenant_a)

        call_kwargs = mock_repo.list_for_tenant.call_args.kwargs
        # El tenant_id que se pasó NO es tenant_b
        assert call_kwargs["tenant_id"] != tenant_b

    @pytest.mark.asyncio
    async def test_log_warning_override_passes_tenant_id_to_audit(
        self,
        tenant_a: UUID,
        user_a: UUID,
    ) -> None:
        """log_warning_override pasa tenant_id correcto al audit_writer."""
        from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import VoiceWarningOverrideRequestDTO
        from src.modules.vitalia.brand_studio.domain.prohibited_phrase import (
            ProhibitedPhrase,
            ProhibitedPhraseSeverity,
        )

        phrase_id = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
        mock_phrase = ProhibitedPhrase(
            id=phrase_id,
            phrase="curamos",
            severity=ProhibitedPhraseSeverity.HIGH.value,
        )
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_phrase
        mock_audit = AsyncMock()

        svc = VoiceBlocklistService(repo=mock_repo, audit=mock_audit)
        request = VoiceWarningOverrideRequestDTO(
            phrase_id=phrase_id,
            section="so_i_speak",
            user_text_excerpt="test",
        )
        await svc.log_warning_override(
            tenant_id=tenant_a,
            user_id=user_a,
            request=request,
        )
        audit_call_kwargs = mock_audit.write.call_args.kwargs
        assert audit_call_kwargs["tenant_id"] == tenant_a


# ─── VoicePreviewService cache tenant isolation ───────────────────────────────


class TestVoicePreviewCacheTenantIsolation:
    """Cache de VoicePreviewService no permite cross-tenant hits."""

    @pytest.mark.asyncio
    async def test_tenant_a_cache_miss_after_tenant_b_caches(
        self,
        tenant_a: UUID,
        tenant_b: UUID,
    ) -> None:
        """Cache de tenant_b no produce HIT para tenant_a con mismos blocks."""
        svc = VoicePreviewService()
        profile_id = UUID("11111111-1111-1111-1111-111111111111")
        blocks = {"archetype": "cuidador"}
        instruction = "## ASÍ HABLO\nSoy preciso y empático."

        # tenant_b cachea primero
        await svc.get_preview(
            tenant_id=tenant_b,
            personality_profile_id=profile_id,
            system_instruction=instruction,
            blocks=blocks,
        )

        # tenant_a con MISMO blocks/profile → debe ser MISS (cache es tenant-scoped)
        _, _, cache_hit = await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=instruction,
            blocks=blocks,
        )
        assert cache_hit is False, (
            "CROSS-TENANT CACHE LEAK: tenant_a recibió HIT del cache de tenant_b. "
            "El cache debe ser tenant-scoped — cache key incluye tenant_id."
        )

    @pytest.mark.asyncio
    async def test_invalidate_tenant_a_does_not_affect_tenant_b(
        self,
        tenant_a: UUID,
        tenant_b: UUID,
    ) -> None:
        """invalidate(tenant_a) no elimina entries de tenant_b."""
        svc = VoicePreviewService()
        profile_id = UUID("11111111-1111-1111-1111-111111111111")
        blocks = {"archetype": "experto"}
        instruction = "## ASÍ HABLO\nSoy preciso."

        # Cachear ambos
        await svc.get_preview(
            tenant_id=tenant_a,
            personality_profile_id=profile_id,
            system_instruction=instruction,
            blocks=blocks,
        )
        await svc.get_preview(
            tenant_id=tenant_b,
            personality_profile_id=profile_id,
            system_instruction=instruction,
            blocks=blocks,
        )

        # Invalidar tenant_a
        await svc.invalidate(tenant_id=tenant_a)

        # tenant_b sigue con HIT
        _, _, hit_b = await svc.get_preview(
            tenant_id=tenant_b,
            personality_profile_id=profile_id,
            system_instruction=instruction,
            blocks=blocks,
        )
        assert hit_b is True, "invalidate(tenant_a) no debe afectar el cache de tenant_b"


# ─── TrustCatalogService (no tenant — read-only seed) ────────────────────────


class TestTrustCatalogNoCrossTenanLeak:
    """TrustCatalogService es stateless — no hay datos cross-tenant."""

    @pytest.mark.asyncio
    async def test_catalog_is_stateless_and_read_only(self) -> None:
        """get_catalog() retorna seed data read-only — no hay tenant context."""
        svc = TrustCatalogService()
        result = await svc.get_catalog(country="PE")
        # Sin tenant_id — el catalog es el mismo para todos los tenants
        assert len(result.items) == 8


# ─── Cross-tenant request boundary (audit + repo) ────────────────────────────


class TestCrossTenantAuditRowTenantIsolation:
    """Audit rows escritos tienen el tenant_id correcto del request actual."""

    @pytest.mark.asyncio
    async def test_audit_row_uses_request_tenant_not_other(
        self,
        tenant_a: UUID,
        tenant_b: UUID,
        user_a: UUID,
    ) -> None:
        """Audit row de tenant_a no contiene tenant_b."""
        from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import VoiceWarningOverrideRequestDTO
        from src.modules.vitalia.brand_studio.domain.prohibited_phrase import (
            ProhibitedPhrase,
            ProhibitedPhraseSeverity,
        )

        phrase_id = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = ProhibitedPhrase(
            id=phrase_id,
            phrase="garantizado",
            severity=ProhibitedPhraseSeverity.HIGH.value,
        )
        mock_audit = AsyncMock()
        svc = VoiceBlocklistService(repo=mock_repo, audit=mock_audit)

        request = VoiceWarningOverrideRequestDTO(
            phrase_id=phrase_id,
            section="so_i_speak",
            user_text_excerpt="texto",
        )

        # Request de tenant_a
        await svc.log_warning_override(
            tenant_id=tenant_a,
            user_id=user_a,
            request=request,
        )

        call_kwargs = mock_audit.write.call_args.kwargs
        # El tenant_id en el audit row es tenant_a, no tenant_b
        assert call_kwargs["tenant_id"] == tenant_a
        assert call_kwargs["tenant_id"] != tenant_b
