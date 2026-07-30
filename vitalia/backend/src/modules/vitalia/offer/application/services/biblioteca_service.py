# cap: lisa.servicios
"""BibliotecaService — typeahead over the EP-2 medical preset library (T-2 § 6).

Reads the brand-local :data:`MEDICAL_SERVICES_V1_PRESETS` seed (NOT engine
catalog). Matches on name + synonyms, scoped to the tenant clinic_type, so
"fundas" surfaces "Carillas de porcelana" / "Diseño de sonrisa". "Usar plantilla"
returns an editable :class:`PresetSuggestion` carrying the canonical_ref; the
catalog service then drafts an Offer + OfferExt pre-filled from it.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.modules.vitalia.offer.biblioteca_seed import MEDICAL_SERVICES_V1_PRESETS


@dataclass(frozen=True)
class PresetSuggestion:
    """A library entry projected for the typeahead / "usar plantilla" flow."""

    canonical_ref: str
    name: str
    clinic_type: str
    category: str | None
    modality: str
    synonyms: list[str]
    keywords: list[str]


class BibliotecaService:
    """Name+synonym typeahead over the curated medical preset library."""

    def __init__(self, presets: tuple[dict[str, object], ...] = MEDICAL_SERVICES_V1_PRESETS) -> None:
        self._presets = presets

    def search(self, *, query: str, clinic_type: str) -> list[PresetSuggestion]:
        needle = query.strip().lower()
        out: list[PresetSuggestion] = []
        for p in self._presets:
            if p.get("clinic_type") != clinic_type:
                continue
            if needle and not _matches(p, needle):
                continue
            out.append(_to_suggestion(p))
        return out

    def get_template(self, *, canonical_ref: str) -> PresetSuggestion | None:
        for p in self._presets:
            if p.get("canonical_ref") == canonical_ref:
                return _to_suggestion(p)
        return None


def _matches(preset: dict[str, object], needle: str) -> bool:
    name = str(preset.get("name", "")).lower()
    if needle in name:
        return True
    synonyms = preset.get("synonyms", []) or []
    return any(needle in str(s).lower() for s in synonyms)  # type: ignore[union-attr]


def _to_suggestion(preset: dict[str, object]) -> PresetSuggestion:
    return PresetSuggestion(
        canonical_ref=str(preset["canonical_ref"]),
        name=str(preset["name"]),
        clinic_type=str(preset["clinic_type"]),
        category=preset.get("category") and str(preset["category"]) or None,
        modality=str(preset["modality"]),
        synonyms=[str(s) for s in (preset.get("synonyms") or [])],  # type: ignore[union-attr]
        keywords=[str(k) for k in (preset.get("keywords") or [])],  # type: ignore[union-attr]
    )
