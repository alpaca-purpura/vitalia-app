"""Regression: get_visuals/patch_visuals deben tolerar un BrandIdentity sin `visuals`.

Origen: estabilizar-harness-e2e-lisa-marca. El de-mock e2e reveló que GET
/api/v1/lisa/marca/visuals devolvía **500** con
`AttributeError: 'BrandIdentity' object has no attribute 'visuals'`.

Causa raíz: el modelo de dominio del engine `BrandIdentity`
(`luana_core_brand_studio.domain.identity`) **NO declara** el campo `visuals`.
El servicio accedía `settings.identity.visuals` directo, lo cual:
  - funciona mientras un `setattr(identity, "visuals", BrandVisuals())` previo
    (de patch_visuals) sobreviva en memoria/serialización, PERO
  - revienta tras un `patch_identity` que guarda+recarga un identity sin ese
    atributo dinámico → AttributeError → 500.

El test de unidad viejo lo enmascaraba usando `MagicMock()` para
`settings.identity` (auto-crea cualquier atributo). Acá usamos el `BrandIdentity`
REAL del engine para reproducir el contrato verdadero.

Engine OFF-LIMITS (promotion gate) → el fix correcto es defensivo en el servicio
brand_studio (`getattr(identity, "visuals", None)`).

downstream-regression-na: brand-local vitalia BE service regression; no cross-brand consumers
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from luana_core_brand_studio.domain.identity import BrandIdentity

from src.modules.vitalia.brand_studio.application.services.marca_service import (
    MarcaService,
)


def _make_service() -> MarcaService:
    return MarcaService(
        session=AsyncMock(),
        audit=AsyncMock(),
        telemetry=MagicMock(),
        voice_preview_service=AsyncMock(),
        voice_blocklist_service=AsyncMock(),
        trust_signal_repo=AsyncMock(),
        trust_catalog_service=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_get_visuals_tolerates_identity_without_visuals_attr() -> None:
    """GET visuals con un BrandIdentity real (sin `visuals`) → DTO vacío, NO 500."""
    service = _make_service()
    settings = MagicMock()
    settings.identity = BrandIdentity()  # engine real: NO tiene atributo `visuals`
    service._get_brand_settings = AsyncMock(return_value=settings)  # type: ignore[method-assign]

    dto = await service.get_visuals(tenant_id=uuid4())

    assert dto.primary_color is None
    assert dto.accent_color is None
    assert dto.logo_url is None


@pytest.mark.asyncio
async def test_get_visuals_when_identity_is_none() -> None:
    """GET visuals sin identity → DTO vacío, NO 500."""
    service = _make_service()
    settings = MagicMock()
    settings.identity = None
    service._get_brand_settings = AsyncMock(return_value=settings)  # type: ignore[method-assign]

    dto = await service.get_visuals(tenant_id=uuid4())

    assert dto.primary_color is None


@pytest.mark.asyncio
async def test_patch_visuals_initializes_visuals_on_identity_without_attr() -> None:
    """PATCH visuals con un BrandIdentity real (sin `visuals`) inicializa y guarda, NO 500."""
    service = _make_service()
    settings = MagicMock()
    settings.identity = BrandIdentity()  # sin `visuals`
    service._get_brand_settings = AsyncMock(return_value=settings)  # type: ignore[method-assign]
    service._save_brand_settings = AsyncMock(return_value=settings)  # type: ignore[method-assign]

    from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import (
        BrandVisualsPatchDTO,
    )

    dto = await service.patch_visuals(
        tenant_id=uuid4(),
        user_id=uuid4(),
        patch=BrandVisualsPatchDTO(primary_color="#01B2F8"),
    )

    assert dto.primary_color == "#01B2F8"


@pytest.mark.asyncio
async def test_get_visuals_when_visuals_is_dict_after_reload() -> None:
    """GET visuals cuando el brand repo recargó visuals como dict (JSON) → coacciona, NO 500.

    Origen: el fix del PATCH visuals (whitelist 6 campos) destapó que el brand repo
    PERSISTE+RECARGA visuals como dict → `visuals.primary_color` daba AttributeError.
    """
    service = _make_service()
    settings = MagicMock()
    settings.identity = MagicMock()
    settings.identity.visuals = {
        "primary_color": "#01B2F8",
        "accent_color": "#7B2D91",
        "font_heading": "Inter",
    }
    service._get_brand_settings = AsyncMock(return_value=settings)  # type: ignore[method-assign]

    dto = await service.get_visuals(tenant_id=uuid4())

    assert dto.primary_color == "#01B2F8"
    assert dto.accent_color == "#7B2D91"
    assert dto.font_heading == "Inter"


@pytest.mark.asyncio
async def test_patch_visuals_when_visuals_is_dict_after_reload() -> None:
    """PATCH visuals sobre un visuals recargado como dict → coacciona + actualiza, NO 500."""
    service = _make_service()
    settings = MagicMock()
    settings.identity = MagicMock()
    settings.identity.visuals = {"primary_color": "#000000"}  # dict del reload
    service._get_brand_settings = AsyncMock(return_value=settings)  # type: ignore[method-assign]
    service._save_brand_settings = AsyncMock(return_value=settings)  # type: ignore[method-assign]

    from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import (
        BrandVisualsPatchDTO,
    )

    dto = await service.patch_visuals(
        tenant_id=uuid4(),
        user_id=uuid4(),
        patch=BrandVisualsPatchDTO(primary_color="#01B2F8"),
    )

    assert dto.primary_color == "#01B2F8"
