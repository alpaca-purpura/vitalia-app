# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""TrustCatalogService — hybrid catalog per country (OQ-D resolution 2026-05-27).

Seed catalog read-only. Closed entries per country + free-text "Otra".
PE shipped; AR/CL/CO/MX/BR populated in future stories.

Anti-creep: NO LLM validator, NO PHI.
downstream-regression-na: brand-local service vitalia
"""

from __future__ import annotations

import structlog

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import TrustSignalsCatalogDTO

logger = structlog.get_logger()


class TrustCatalogService:
    """Hybrid catalog per country (OQ-D) — seed catalog read-only.

    Returns closed set of known authorities per country + free-text option.
    """

    HYBRID_CATALOG: dict[str, list[dict[str, str]]] = {
        "PE": [
            {
                "code": "DIGESA",
                "label": "DIGESA (Dirección General de Salud Ambiental)",
                "hint": "Autoridad sanitaria PE",
            },
            {
                "code": "MINSA",
                "label": "MINSA (Ministerio de Salud)",
                "hint": "Autoridad nacional salud",
            },
            {
                "code": "SUSALUD",
                "label": "SUSALUD (Superintendencia Nacional de Salud)",
                "hint": "Regulador salud",
            },
            {
                "code": "COP_ODONTO",
                "label": "Colegio Odontológico del Perú",
                "hint": "Para clínicas dentales",
            },
            {
                "code": "CMP",
                "label": "Colegio Médico del Perú",
                "hint": "Para clínicas médicas",
            },
            {
                "code": "SUNAT",
                "label": "SUNAT (vigente)",
                "hint": "Contribuyente activo",
            },
            {
                "code": "ISO_9001",
                "label": "ISO 9001 Calidad",
                "hint": "Certificación gestión calidad",
            },
            {
                "code": "ESSALUD",
                "label": "EsSalud (convenio)",
                "hint": "Convenio seguro social",
            },
        ],
        "AR": [],  # populate in future story vitalia-fase2-lisa-marca-seed-countries
        "CL": [],
        "CO": [],
        "MX": [],
        "BR": [],
    }

    async def get_catalog(self, *, country: str) -> TrustSignalsCatalogDTO:
        """Return hybrid catalog for a country.

        Args:
            country: ISO 3166-1 alpha-2 country code (case-insensitive).

        Returns:
            TrustSignalsCatalogDTO with items for the country.
            Empty items list for unknown countries.
        """
        upper_country = country.upper()
        items = self.HYBRID_CATALOG.get(upper_country, [])
        logger.debug(
            "trust_catalog_fetched",
            country=upper_country,
            item_count=len(items),
        )
        return TrustSignalsCatalogDTO(country=upper_country, items=items)
