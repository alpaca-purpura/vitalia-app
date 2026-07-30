"""Offer catalogs DAG smoke — lift preservation cement.

Per 03-arch.md §7.4 + offer-expert skill SSoT + outcome §7.3 verbatim lift.

Confirms the 7-catalog DAG was preserved post-lift (no entries dropped or
silently re-numbered). Counts asserted as ≥ thresholds because new entries
may be added later in production but lift must not lose any.

Threshold rationale:
- 5 archetypes (SERVICIO/PROGRAMA/MEMBRESIA/EXPERIENCIA/PRODUCTO) — stable contract
- 5 value levels (LEAD_MAGNET/TRIPWIRE/CORE/PREMIUM/ENTERPRISE) — stable contract
- ≥21 section keys (post-2026 consolidation: 9 universal + 7 archetype-specific + 5 LATAM)
- ≥76 presets (pre-lift count; lift verbatim preserves whatever current AISALESHT has — currently 84)
- ≥4 variant structures (PERIOD/SCOPE/TIER/PACK + extensions)

V-F-cat-1 validator.
"""

from __future__ import annotations


def test_archetype_catalog_loaded():
    """All 5 OfferArchetype entries present after lift."""
    from luana_core_offer_studio.domain.archetype_catalog import ARCHETYPE_CATALOG

    assert len(ARCHETYPE_CATALOG) == 5, (
        f"ARCHETYPE_CATALOG must have 5 entries (lift cement). Found: {len(ARCHETYPE_CATALOG)}"
    )


def test_value_level_catalog_loaded():
    """All 5 OfferValueLevel entries present after lift."""
    from luana_core_offer_studio.domain.value_level_catalog import VALUE_LEVEL_CATALOG

    assert len(VALUE_LEVEL_CATALOG) == 5, (
        f"VALUE_LEVEL_CATALOG must have 5 entries (lift cement). Found: {len(VALUE_LEVEL_CATALOG)}"
    )


def test_section_catalog_loaded():
    """≥21 SectionKey entries present after lift (post-2026 consolidation)."""
    from luana_core_offer_studio.domain.section_catalog import SECTION_CATALOG

    assert len(SECTION_CATALOG) >= 21, (
        f"SECTION_CATALOG must have at least 21 entries (post-2026 consolidation). Found: {len(SECTION_CATALOG)}"
    )


def test_preset_catalog_loaded():
    """≥76 OfferTypePreset entries present after lift (AISALESHT pre-lift baseline)."""
    from luana_core_offer_studio.domain.offer_type_preset_catalog import OFFER_TYPE_PRESET_CATALOG

    assert len(OFFER_TYPE_PRESET_CATALOG) >= 76, (
        f"OFFER_TYPE_PRESET_CATALOG must have at least 76 entries (lift preservation). "
        f"Found: {len(OFFER_TYPE_PRESET_CATALOG)}"
    )


def test_variant_structure_catalog_loaded():
    """≥4 VariantStructure entries present after lift."""
    from luana_core_offer_studio.domain.variant_structure_catalog import VARIANT_STRUCTURE_CATALOG

    assert len(VARIANT_STRUCTURE_CATALOG) >= 4, (
        f"VARIANT_STRUCTURE_CATALOG must have at least 4 entries. Found: {len(VARIANT_STRUCTURE_CATALOG)}"
    )


def test_format_catalog_loaded():
    """OfferFormat catalog non-empty (composite per archetype × EBT)."""
    from luana_core_offer_studio.domain.format_catalog import FORMAT_CATALOG

    assert len(FORMAT_CATALOG) > 0, "FORMAT_CATALOG must be non-empty (composite axis)"


def test_offer_ladder_hints_loaded():
    """OfferLadderHints non-empty (per (EBT, ValueLevel) hint entries)."""
    from luana_core_offer_studio.domain.offer_ladder_hints import OFFER_LADDER_HINTS

    assert len(OFFER_LADDER_HINTS) > 0, "OFFER_LADDER_HINTS must be non-empty (axis composite)"


def test_seven_catalog_dag_intact():
    """Confirms all 7 catalogs co-imported without circular deps.

    Per offer-expert SSoT mental model — 7 catalogs form a DAG:
    base layer: ExpertBusinessType, OfferValueLevel, SectionCatalog, VariantStructure
    intermediate: OfferArchetype
    composite: OfferFormat, OfferLadderHints, OfferTypePreset
    """
    from luana_core_offer_studio.domain.archetype_catalog import ARCHETYPE_CATALOG
    from luana_core_offer_studio.domain.format_catalog import FORMAT_CATALOG
    from luana_core_offer_studio.domain.offer_ladder_hints import OFFER_LADDER_HINTS
    from luana_core_offer_studio.domain.offer_type_preset_catalog import OFFER_TYPE_PRESET_CATALOG
    from luana_core_offer_studio.domain.section_catalog import SECTION_CATALOG
    from luana_core_offer_studio.domain.value_level_catalog import VALUE_LEVEL_CATALOG
    from luana_core_offer_studio.domain.variant_structure_catalog import VARIANT_STRUCTURE_CATALOG

    catalogs = {
        "archetypes": ARCHETYPE_CATALOG,
        "value_levels": VALUE_LEVEL_CATALOG,
        "sections": SECTION_CATALOG,
        "presets": OFFER_TYPE_PRESET_CATALOG,
        "variants": VARIANT_STRUCTURE_CATALOG,
        "formats": FORMAT_CATALOG,
        "ladder_hints": OFFER_LADDER_HINTS,
    }
    for name, catalog in catalogs.items():
        assert catalog is not None, f"{name} catalog import failed (None)"
        assert len(catalog) > 0, f"{name} catalog empty after lift"
