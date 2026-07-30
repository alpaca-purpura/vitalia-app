"""Tests for MarcaService — core orchestrator Lisa > Marca.

Verifies:
  - GET methods return correct DTO types (tenant_id only, no user_id)
  - PATCH methods write audit log sync pre-return (user_id required)
  - Telemetry is fire-forget (exception swallowed)
  - Trust signals CRUD delegation to trust_signal_repo
  - Voice preview delegates to VoicePreviewService
  - All service methods pass tenant_id to engine repos

Uses AsyncMock for all engine repos (no Postgres required).

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import (
    BrandIdentityDTO,
    BrandIdentityPatchDTO,
    BrandVisualsDTO,
    BrandVisualsPatchDTO,
    TrustSignalCreateRequestDTO,
)
from src.modules.vitalia.brand_studio.application.services.marca_service import MarcaService
from src.modules.vitalia.brand_studio.application.services.trust_catalog_service import TrustCatalogService
from src.modules.vitalia.brand_studio.application.services.voice_blocklist_service import VoiceBlocklistService
from src.modules.vitalia.brand_studio.application.services.voice_preview_service import VoicePreviewService
from src.modules.vitalia.brand_studio.domain.trust_signal import TrustSignal

pytestmark = pytest.mark.integration

_TENANT_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_USER_A = UUID("11111111-1111-1111-1111-111111111111")


def _make_mock_brand_settings() -> MagicMock:
    """Build a fake BrandSettings-like object for engine bridging."""
    settings = MagicMock()
    settings.identity = MagicMock()
    settings.identity.brand_name = "Clínica Bienestar"
    settings.identity.tagline = "Tu salud es nuestra prioridad"
    settings.identity.visuals = MagicMock()
    settings.identity.visuals.primary_color = "#01B2F8"
    settings.identity.visuals.accent_color = "#7B2D91"
    settings.identity.visuals.background_color = None
    settings.identity.visuals.text_primary_color = None
    settings.identity.visuals.font_heading = "Inter"
    settings.identity.visuals.font_body = "Inter"
    settings.identity.visuals.logo_url = None
    settings.personality = None
    settings.contact = None
    return settings


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)

    async def _run_sync(fn: object) -> MagicMock:
        return _make_mock_brand_settings()

    session.run_sync.side_effect = _run_sync
    return session


@pytest.fixture
def mock_audit() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_telemetry() -> MagicMock:
    t = MagicMock()
    t.emit_event = MagicMock(return_value=None)
    return t


@pytest.fixture
def mock_voice_preview() -> AsyncMock:
    return AsyncMock(spec=VoicePreviewService)


@pytest.fixture
def mock_voice_blocklist() -> AsyncMock:
    return AsyncMock(spec=VoiceBlocklistService)


@pytest.fixture
def mock_trust_signal_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.list_for_tenant.return_value = []
    return repo


@pytest.fixture
def mock_trust_catalog() -> AsyncMock:
    return AsyncMock(spec=TrustCatalogService)


@pytest.fixture
def service(
    mock_session: AsyncMock,
    mock_audit: AsyncMock,
    mock_telemetry: MagicMock,
    mock_voice_preview: AsyncMock,
    mock_voice_blocklist: AsyncMock,
    mock_trust_signal_repo: AsyncMock,
    mock_trust_catalog: AsyncMock,
) -> MarcaService:
    return MarcaService(
        session=mock_session,
        audit=mock_audit,
        telemetry=mock_telemetry,
        voice_preview_service=mock_voice_preview,
        voice_blocklist_service=mock_voice_blocklist,
        trust_signal_repo=mock_trust_signal_repo,
        trust_catalog_service=mock_trust_catalog,
    )


class TestMarcaServiceGetMethods:
    """GET methods — sólo requieren tenant_id, no user_id."""

    @pytest.mark.asyncio
    async def test_get_identity_returns_dto(self, service: MarcaService) -> None:
        result = await service.get_identity(tenant_id=_TENANT_A)
        assert isinstance(result, BrandIdentityDTO)
        assert result.tenant_id == _TENANT_A

    @pytest.mark.asyncio
    async def test_get_visuals_returns_dto(self, service: MarcaService) -> None:
        result = await service.get_visuals(tenant_id=_TENANT_A)
        assert isinstance(result, BrandVisualsDTO)
        assert result.tenant_id == _TENANT_A

    @pytest.mark.asyncio
    async def test_get_identity_does_not_write_audit_log(
        self,
        service: MarcaService,
        mock_audit: AsyncMock,
    ) -> None:
        """GET methods non-mutating: no audit log write."""
        await service.get_identity(tenant_id=_TENANT_A)
        mock_audit.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_visuals_does_not_write_audit_log(
        self,
        service: MarcaService,
        mock_audit: AsyncMock,
    ) -> None:
        await service.get_visuals(tenant_id=_TENANT_A)
        mock_audit.write.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_trust_signals_returns_list(
        self,
        service: MarcaService,
        mock_trust_signal_repo: AsyncMock,
    ) -> None:
        mock_trust_signal_repo.list_for_tenant.return_value = []

        result = await service.get_trust_signals(tenant_id=_TENANT_A, user_id=_USER_A)
        assert isinstance(result, list)


class TestMarcaServicePatchMethods:
    """PATCH methods — requieren user_id, escriben audit log sync pre-return."""

    @pytest.mark.asyncio
    async def test_patch_identity_writes_audit_log(
        self,
        service: MarcaService,
        mock_audit: AsyncMock,
    ) -> None:
        """patch_identity debe escribir audit row action=brand_identity_updated."""
        patch_dto = BrandIdentityPatchDTO(name="Clínica Bienestar Actualizada")
        await service.patch_identity(
            tenant_id=_TENANT_A,
            user_id=_USER_A,
            patch=patch_dto,
        )
        mock_audit.write.assert_called_once()
        call_kwargs = mock_audit.write.call_args.kwargs
        assert call_kwargs["action"] == "brand_identity_updated"
        assert call_kwargs["tenant_id"] == _TENANT_A
        assert call_kwargs["user_id"] == _USER_A

    @pytest.mark.asyncio
    async def test_patch_visuals_writes_audit_log(
        self,
        service: MarcaService,
        mock_audit: AsyncMock,
        mock_session: AsyncMock,
    ) -> None:
        """patch_visuals escribe audit row action=brand_visuals_updated."""
        patch_dto = BrandVisualsPatchDTO(primary_color="#FF0000")
        await service.patch_visuals(
            tenant_id=_TENANT_A,
            user_id=_USER_A,
            patch=patch_dto,
        )
        mock_audit.write.assert_called_once()
        call_kwargs = mock_audit.write.call_args.kwargs
        assert call_kwargs["action"] == "brand_visuals_updated"
        assert call_kwargs["tenant_id"] == _TENANT_A

    @pytest.mark.asyncio
    async def test_patch_identity_returns_dto(
        self,
        service: MarcaService,
    ) -> None:
        patch_dto = BrandIdentityPatchDTO(tagline="Cuidamos tu salud con evidencia")
        result = await service.patch_identity(
            tenant_id=_TENANT_A,
            user_id=_USER_A,
            patch=patch_dto,
        )
        assert isinstance(result, BrandIdentityDTO)
        assert result.tenant_id == _TENANT_A


class TestMarcaServiceTrustSignals:
    """CRUD de trust signals a través de MarcaService."""

    @pytest.mark.asyncio
    async def test_create_trust_signal_delegates_to_repo(
        self,
        service: MarcaService,
        mock_trust_signal_repo: AsyncMock,
    ) -> None:
        new_signal = TrustSignal(
            tenant_id=_TENANT_A,
            label="DIGESA",
            catalog_code="DIGESA",
        )
        mock_trust_signal_repo.create.return_value = new_signal

        request = TrustSignalCreateRequestDTO(
            label="DIGESA",
            catalog_code="DIGESA",
        )
        await service.create_trust_signal(
            tenant_id=_TENANT_A,
            user_id=_USER_A,
            request=request,
        )
        mock_trust_signal_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_trust_signal_delegates_to_repo(
        self,
        service: MarcaService,
        mock_trust_signal_repo: AsyncMock,
        mock_audit: AsyncMock,
    ) -> None:
        signal_id = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
        signal = TrustSignal(id=signal_id, tenant_id=_TENANT_A, label="DIGESA")
        mock_trust_signal_repo.get_by_id.return_value = signal

        await service.delete_trust_signal(
            tenant_id=_TENANT_A,
            user_id=_USER_A,
            signal_id=signal_id,
        )
        mock_trust_signal_repo.soft_delete.assert_called_once()


class TestMarcaServiceTelemetry:
    """Telemetría fire-forget — nunca propaga excepciones."""

    @pytest.mark.asyncio
    async def test_telemetry_exception_swallowed(
        self,
        service: MarcaService,
        mock_telemetry: MagicMock,
    ) -> None:
        """Si telemetry.emit_event lanza excepción, NO se propaga."""
        mock_telemetry.emit_event.side_effect = RuntimeError("telemetry_down")

        patch_dto = BrandIdentityPatchDTO(name="Test Clinic")
        # Should not raise despite telemetry failure
        result = await service.patch_identity(
            tenant_id=_TENANT_A,
            user_id=_USER_A,
            patch=patch_dto,
        )
        assert isinstance(result, BrandIdentityDTO)


class TestMarcaServiceLogoUpload:
    """upload_logo / delete_logo — object storage real vía la StorageStrategy del engine.

    Origen: estabilizar-harness-e2e-lisa-marca T-5 (logo R2). El upload deja de descartar
    los bytes (`logo:{uuid}` stub) y consume la StorageStrategy del engine
    (`luana_core_assets.infrastructure.storage.get_storage_strategy`) **directamente** — NO
    `AssetsService.upload_asset` (su Asset DB entity tiene FK `assets.offer_id -> products.id`
    que vitalia NUNCA migra → `NoReferencedTableError` 500; cazado por el demo de Chris). La
    capa de storage no tiene dependencia de DB. El storage se mockea (ya testeado en core);
    acá verificamos el punto de integración: que se sube vía `storage.save` y la URL pública
    real se persiste en `visuals.logo_url` + se devuelve en el DTO.
    """

    @pytest.mark.asyncio
    async def test_upload_logo_persists_real_public_url(self, service: MarcaService) -> None:
        """upload_logo sube vía StorageStrategy y persiste la URL pública real (no 'logo:')."""
        public_url = "https://pub-test.r2.dev/aaaaaaaa/logo/abc123.png"
        with patch("luana_core_assets.infrastructure.storage.get_storage_strategy") as mock_gss:
            mock_gss.return_value.save.return_value = ("aaaaaaaa/logo/abc123.png", public_url)
            result = await service.upload_logo(
                tenant_id=_TENANT_A,
                user_id=_USER_A,
                content=b"\x89PNG fake bytes",
                ext="png",
                size_bytes=15,
            )

        # DTO devuelve la URL pública real, no el stub "logo:{uuid}"
        assert result.logo_url == public_url
        assert not result.logo_url.startswith("logo:")

        # storage.save(file_obj, filename, path_prefix) — path_prefix tenant-scoped + ext preservada
        call = mock_gss.return_value.save.call_args
        assert str(_TENANT_A) in call.args[2]
        assert call.args[1].endswith(".png")

    @pytest.mark.asyncio
    async def test_upload_logo_writes_audit(self, service: MarcaService, mock_audit: AsyncMock) -> None:
        """upload_logo sigue escribiendo audit log sync (HIPAA-lite) tras el storage real."""
        with patch("luana_core_assets.infrastructure.storage.get_storage_strategy") as mock_gss:
            mock_gss.return_value.save.return_value = ("x/logo/z.png", "https://pub-test.r2.dev/x/logo/z.png")
            await service.upload_logo(
                tenant_id=_TENANT_A,
                user_id=_USER_A,
                content=b"bytes",
                ext="png",
                size_bytes=5,
            )

        mock_audit.write.assert_called_once()
        assert mock_audit.write.call_args.kwargs["action"] == "brand_logo_uploaded"

    @pytest.mark.asyncio
    async def test_delete_logo_removes_from_storage(self, service: MarcaService) -> None:
        """delete_logo desreferencia el campo y borra el objeto del storage (key derivada de la URL).

        Sin logo_id en la firma: una marca tiene UN solo logo.
        """
        # visuals viven anidados bajo identity (mismo lugar que patch_visuals/get_visuals)
        fake_settings = MagicMock()
        fake_settings.identity.visuals.logo_url = "https://pub-test.r2.dev/aaaaaaaa/logo/abc123.png"

        with (
            patch.object(service, "_get_brand_settings", new=AsyncMock(return_value=fake_settings)),
            patch.object(service, "_save_brand_settings", new=AsyncMock(return_value=None)),
            patch("luana_core_assets.infrastructure.storage.get_storage_strategy") as mock_gss,
            patch("luana_core_platform.core.config.settings") as mock_cfg,
        ):
            mock_cfg.R2_PUBLIC_URL = "https://pub-test.r2.dev"
            await service.delete_logo(tenant_id=_TENANT_A, user_id=_USER_A)

        # campo desreferenciado en identity.visuals + objeto borrado con la key derivada
        assert fake_settings.identity.visuals.logo_url is None
        mock_gss.return_value.delete.assert_called_once_with("aaaaaaaa/logo/abc123.png")
