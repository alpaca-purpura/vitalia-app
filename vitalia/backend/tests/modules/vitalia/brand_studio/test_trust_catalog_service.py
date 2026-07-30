"""Tests unitarios para TrustCatalogService — catalog híbrido por país.

OQ-D resolution (CONTEXT-BRIEF.md 2026-05-27): TrustCatalogService retorna
set cerrado de autoridades conocidas por país + opción free-text.
PE: 8 entradas fijas. AR/CL/CO/MX/BR: empty (futuros stories).

Verifica:
  - PE seed tiene exactamente 8 entradas con códigos correctos
  - Lookup case-insensitive (pe, Pe, PE → mismo resultado)
  - País desconocido → lista vacía (no error)
  - Retorna TrustSignalsCatalogDTO con campo country correcto

T-3 — F2-S7 vitalia-fase2-lisa-marca.
"""

from __future__ import annotations

import pytest

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import TrustSignalsCatalogDTO
from src.modules.vitalia.brand_studio.application.services.trust_catalog_service import TrustCatalogService

# Códigos canónicos PE por 03-arch § OQ-D
EXPECTED_PE_CODES: set[str] = {
    "DIGESA",
    "MINSA",
    "SUSALUD",
    "COP_ODONTO",
    "CMP",
    "SUNAT",
    "ISO_9001",
    "ESSALUD",
}


@pytest.fixture
def svc() -> TrustCatalogService:
    return TrustCatalogService()


class TestTrustCatalogPE:
    """Catálogo PE tiene 8 entradas con códigos correctos (OQ-D resolution)."""

    @pytest.mark.asyncio
    async def test_pe_catalog_has_8_items(self, svc: TrustCatalogService) -> None:
        """GET /trust-catalog?country=PE → 8 entradas (DIGESA + 7 más)."""
        result = await svc.get_catalog(country="PE")
        assert isinstance(result, TrustSignalsCatalogDTO)
        assert len(result.items) == 8, (
            f"PE catalog debe tener exactamente 8 entradas per OQ-D. Encontradas: {len(result.items)}"
        )

    @pytest.mark.asyncio
    async def test_pe_catalog_has_correct_codes(self, svc: TrustCatalogService) -> None:
        """PE catalog contiene exactamente los 8 códigos canónicos."""
        result = await svc.get_catalog(country="PE")
        found_codes = {item["code"] for item in result.items}
        assert found_codes == EXPECTED_PE_CODES, (
            f"PE catalog codes mismatch.\nEsperados: {sorted(EXPECTED_PE_CODES)}\nEncontrados: {sorted(found_codes)}"
        )

    @pytest.mark.asyncio
    async def test_pe_catalog_has_digesa(self, svc: TrustCatalogService) -> None:
        """PE catalog debe incluir DIGESA (autoridad sanitaria peruana)."""
        result = await svc.get_catalog(country="PE")
        codes = [item["code"] for item in result.items]
        assert "DIGESA" in codes

    @pytest.mark.asyncio
    async def test_pe_catalog_has_cmp(self, svc: TrustCatalogService) -> None:
        """PE catalog debe incluir CMP (Colegio Médico del Perú)."""
        result = await svc.get_catalog(country="PE")
        codes = [item["code"] for item in result.items]
        assert "CMP" in codes

    @pytest.mark.asyncio
    async def test_pe_catalog_has_essalud(self, svc: TrustCatalogService) -> None:
        """PE catalog debe incluir ESSALUD (convenio seguro social)."""
        result = await svc.get_catalog(country="PE")
        codes = [item["code"] for item in result.items]
        assert "ESSALUD" in codes

    @pytest.mark.asyncio
    async def test_pe_catalog_items_have_label_and_hint(self, svc: TrustCatalogService) -> None:
        """Cada entrada del catalog PE tiene code, label y hint no vacíos."""
        result = await svc.get_catalog(country="PE")
        for item in result.items:
            assert item.get("code"), f"Entrada sin code: {item}"
            assert item.get("label"), f"Entrada sin label: {item}"
            assert item.get("hint"), f"Entrada sin hint: {item}"

    @pytest.mark.asyncio
    async def test_pe_catalog_country_field_is_uppercase(self, svc: TrustCatalogService) -> None:
        """DTO retornado tiene country='PE' (uppercase)."""
        result = await svc.get_catalog(country="PE")
        assert result.country == "PE"


class TestTrustCatalogCaseInsensitive:
    """Lookup case-insensitive: pe, Pe, PE → mismo resultado."""

    @pytest.mark.asyncio
    async def test_lowercase_pe_returns_8_items(self, svc: TrustCatalogService) -> None:
        """country='pe' (lowercase) debe retornar mismas 8 entradas."""
        result = await svc.get_catalog(country="pe")
        assert len(result.items) == 8

    @pytest.mark.asyncio
    async def test_mixed_case_pe_returns_8_items(self, svc: TrustCatalogService) -> None:
        """country='Pe' (mixed) debe retornar mismas 8 entradas."""
        result = await svc.get_catalog(country="Pe")
        assert len(result.items) == 8

    @pytest.mark.asyncio
    async def test_normalized_country_in_response(self, svc: TrustCatalogService) -> None:
        """DTO retornado normaliza country a uppercase independientemente del input."""
        result = await svc.get_catalog(country="pe")
        assert result.country == "PE"


class TestTrustCatalogUnknownCountry:
    """País desconocido → lista vacía (sin error)."""

    @pytest.mark.asyncio
    async def test_unknown_country_returns_empty_list(self, svc: TrustCatalogService) -> None:
        """País no registrado (ej. 'XX') → items=[] (no excepción)."""
        result = await svc.get_catalog(country="XX")
        assert isinstance(result, TrustSignalsCatalogDTO)
        assert result.items == [] or len(result.items) == 0

    @pytest.mark.asyncio
    async def test_future_countries_return_empty(self, svc: TrustCatalogService) -> None:
        """Países futuros (AR, CL, CO, MX, BR) retornan lista vacía actualmente."""
        for country in ("AR", "CL", "CO", "MX", "BR"):
            result = await svc.get_catalog(country=country)
            assert len(result.items) == 0, (
                f"País {country} debe tener lista vacía hasta que se cargue su catalog. "
                f"Encontrados: {len(result.items)} items."
            )


class TestTrustCatalogReturnType:
    """get_catalog retorna TrustSignalsCatalogDTO correctamente tipado."""

    @pytest.mark.asyncio
    async def test_returns_catalog_dto(self, svc: TrustCatalogService) -> None:
        """Retorno es instancia de TrustSignalsCatalogDTO."""
        result = await svc.get_catalog(country="PE")
        assert isinstance(result, TrustSignalsCatalogDTO)

    @pytest.mark.asyncio
    async def test_items_are_dicts_with_string_values(self, svc: TrustCatalogService) -> None:
        """Cada item del catálogo es dict con valores string."""
        result = await svc.get_catalog(country="PE")
        for item in result.items:
            assert isinstance(item, dict), f"item debe ser dict, got: {type(item)}"
            for key, val in item.items():
                assert isinstance(key, str), f"key debe ser str, got: {type(key)}"
                assert isinstance(val, str), f"value de '{key}' debe ser str, got: {type(val)}"

    @pytest.mark.asyncio
    async def test_class_variable_unchanged(self, svc: TrustCatalogService) -> None:
        """HYBRID_CATALOG es class variable inmutable — get_catalog no debe mutarla."""
        original_pe_count = len(TrustCatalogService.HYBRID_CATALOG["PE"])
        await svc.get_catalog(country="PE")
        assert len(TrustCatalogService.HYBRID_CATALOG["PE"]) == original_pe_count
