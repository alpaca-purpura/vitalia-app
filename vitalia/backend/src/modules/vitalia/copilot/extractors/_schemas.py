# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Pydantic schemas for vitalia copilot extractors (T-extractors-1, T-extractors-2).

Spec sources:
  * 02-design-agentic.md § 7.1 / § 7.2 — MedicalHistoryV1 + DentalHistoryV1 spec
  * 03-arch-agentic.md § 5.1 / § 5.2 — wave composition + output schemas
  * 06-tickets.yaml::T-extractors-1, T-extractors-2 acceptance criteria

Schema versioning:
  ``MedicalHistoryV1.schema_version: Literal[1]`` cement (frozen). Subsequent
  schema migrations land in ``MedicalHistoryV2`` (NEW class) — never mutate
  V1, per Story D goldens schema-cement playbook.

  ``DentalHistoryV1.schema_version: Literal[1]`` cement (frozen). Same
  immutability invariant — V2 is a NEW class, never an in-place mutation.

Anti-duplication audit (Step 0 GATE pre-write, 2026-05-14):
  * grep cross codebase for ``class MedicalHistoryV1`` / ``class MedicalKBExtractor``
    → zero collisions confirmed. All NEW symbols.
  * ``Allergy`` / ``Condition`` / ``Medication`` / ``Surgery`` /
    ``FamilyHistorySummary`` / ``VitalSigns`` are vertical-medical-specific
    domain primitives; no shared abstraction in luana-core to extend.
  * grep cross codebase for ``class DentalHistoryV1`` / ``class ToothPosition``
    / ``class Restoration`` → zero collisions confirmed (T-extractors-2). FDI tooth
    numbering is vertical-medical-specific; no shared luana-core entity.
  * Dental primitives appended to this file (M8 parallel-safety pattern —
    sibling T-extractors-1 owns medical primitives above; both extractors
    share ``ExtractionWave`` dataclass + same prompt slot architecture).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ─── Wave configuration dataclass ──────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ExtractionWave:
    """Configuration for a single LLM extraction wave.

    Frozen so wave configurations declared at class scope are immutable.
    """

    name: str
    """Human-readable slug for trace + structlog event naming."""

    model_role: str
    """Logical role consumed by `LiteLLMService.get_chat_model(role)` —
    e.g. ``"vision"`` for Sonnet vision, ``"nano"`` for Haiku vision when
    using the LiteLLM router. Never a wire model name (LLM_ROLE_BY_SITE SSoT).
    Production caller maps roles at the LiteLLM proxy boundary."""

    prompt_template: str
    """Filename of the Jinja2 prompt template under ``_prompts/`` (e.g.
    ``medical_extract_allergies_meds.j2``). Templates are cache-prefix
    invariant — variable inputs go AFTER the cache_control marker."""

    timeout_sec: float
    """Per-wave wall-clock timeout. Wave that exceeds this is treated as
    degraded (`extraction_warnings` records the timeout, confidence
    decremented, partial output kept)."""


# ─── Medical history primitive entities ────────────────────────────────────


class Allergy(BaseModel):
    """Allergy entry in patient medical history."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    substance: str = Field(..., max_length=200, description="Allergen name as cited in source.")
    severity: Literal["mild", "moderate", "severe", "unknown"] = "unknown"
    reaction: str | None = Field(None, max_length=500)


class Condition(BaseModel):
    """Chronic medical condition / diagnosis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., max_length=200)
    icd10_code: str | None = Field(None, max_length=10, pattern=r"^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$|^$")
    diagnosed_year: int | None = Field(None, ge=1900, le=2100)
    status: Literal["active", "controlled", "in_remission", "resolved", "unknown"] = "unknown"


class Medication(BaseModel):
    """Current medication entry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., max_length=200)
    dose: str | None = Field(None, max_length=100, description="e.g. '10 mg'.")
    frequency: str | None = Field(None, max_length=100, description="e.g. 'cada 8 hs'.")
    indication: str | None = Field(None, max_length=200)


class Surgery(BaseModel):
    """Past surgery entry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    procedure: str = Field(..., max_length=200)
    year: int | None = Field(None, ge=1900, le=2100)
    notes: str | None = Field(None, max_length=500)


class FamilyHistorySummary(BaseModel):
    """Summary of relevant family history."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    relevant_conditions: list[str] = Field(default_factory=list)
    notes: str | None = Field(None, max_length=1000)


class VitalSigns(BaseModel):
    """Most recent vital sign observation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    blood_pressure: str | None = Field(None, max_length=20, description="e.g. '120/80'.")
    heart_rate_bpm: int | None = Field(None, ge=20, le=300)
    weight_kg: float | None = Field(None, ge=0, le=500)
    height_cm: float | None = Field(None, ge=0, le=300)
    bmi: float | None = Field(None, ge=0, le=100)
    observed_at: str | None = Field(None, max_length=30, description="ISO date as cited.")


# ─── Output schema (top-level extractor product) ───────────────────────────


class MedicalHistoryV1(BaseModel):
    """Structured medical history extracted from a patient PDF.

    Schema-cemented per Story D goldens playbook. Bumping the schema → NEW
    class ``MedicalHistoryV2`` (NEVER mutate V1).
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    schema_version: Literal[1] = 1

    allergies: list[Allergy] = Field(default_factory=list)
    chronic_conditions: list[Condition] = Field(default_factory=list)
    current_medications: list[Medication] = Field(default_factory=list)
    past_surgeries: list[Surgery] = Field(default_factory=list)
    family_history: FamilyHistorySummary | None = None
    vital_signs_recent: VitalSigns | None = None

    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    """Aggregate confidence across the 4 waves. Each wave contributes a
    sub-score; merge wave averages and decrements per recorded warning."""

    missing_required_fields: list[str] = Field(default_factory=list)
    """Names of required fields the extractor could not populate (e.g.
    ``"allergies"`` when allergy section was illegible)."""

    extraction_warnings: list[str] = Field(default_factory=list)
    """Free-form messages from waves: timeouts, parse failures, low-quality
    pages, etc. Surfaced to clinic_owner for manual review trigger when
    ``confidence_score < 0.7``."""


# ─── Dental history primitive entities (T-extractors-2) ───────────────────


def _validate_fdi_code(value: int) -> int:
    """Reject FDI codes outside the 4 adult quadrants (11-18, 21-28, 31-38, 41-48).

    FDI World Dental Federation universal numbering for adult permanent dentition:
      Quadrant 1 (upper right):    11..18
      Quadrant 2 (upper left):     21..28
      Quadrant 3 (lower left):     31..38
      Quadrant 4 (lower right):    41..48
    Codes 19-20, 29-30, 39-40, 49+, 0, negatives are invalid.
    Pediatric dentition (51-85) deferred to Story 11.bis if needed.
    """
    quadrant, position = divmod(value, 10)
    if quadrant not in {1, 2, 3, 4} or position not in {1, 2, 3, 4, 5, 6, 7, 8}:
        raise ValueError(
            f"Invalid FDI tooth code {value!r}: quadrant must be 1-4 and "
            f"position 1-8 (adult permanent dentition). Got quadrant={quadrant}, "
            f"position={position}."
        )
    return value


# Pydantic v2 field validator — used by ToothPosition + Restoration
from pydantic import field_validator  # noqa: E402


class ToothPosition(BaseModel):
    """Single tooth position in FDI World Dental Federation notation. See § 7.2."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fdi_code: int = Field(
        ...,
        description="FDI tooth code (11-18 / 21-28 / 31-38 / 41-48). "
        "quadrant_digit * 10 + position_from_midline (1-8).",
    )
    notes: str | None = Field(None, max_length=200)

    @field_validator("fdi_code", mode="after")
    @classmethod
    def _check_fdi(cls, v: int) -> int:
        return _validate_fdi_code(v)


class Restoration(BaseModel):
    """Existing restoration entry (crown, implant, filling, bridge)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tooth_fdi: int = Field(..., description="FDI code of restored tooth.")
    type: Literal[
        "corona",
        "crown",
        "implante",
        "implant",
        "obturacion",
        "filling",
        "puente",
        "bridge",
        "endodoncia",
        "root_canal",
        "carilla",
        "veneer",
        "other",
    ] = "other"
    material: str | None = Field(None, max_length=100, description="e.g. 'porcelana', 'amalgama'.")
    placed_year: int | None = Field(None, ge=1900, le=2100)
    notes: str | None = Field(None, max_length=300)

    @field_validator("tooth_fdi", mode="after")
    @classmethod
    def _validate_tooth_fdi(cls, v: int) -> int:
        return _validate_fdi_code(v)


class PeriodontalSummary(BaseModel):
    """Periodontal status summary across the dentition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    general_status: Literal["sano", "leve", "moderado", "severo", "unknown"] = "unknown"
    bleeding_index: float | None = Field(None, ge=0.0, le=1.0, description="BoP index 0-1.")
    pocket_depth_max_mm: float | None = Field(None, ge=0.0, le=20.0)
    notes: str | None = Field(None, max_length=500)


class BiteAlignmentNotes(BaseModel):
    """Bite alignment notes (occlusion / malocclusion summary)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    alignment: Literal["normal", "clase_I", "clase_II", "clase_III", "open_bite", "cross_bite", "unknown"] = "unknown"
    notes: str | None = Field(None, max_length=500)


class RadiographRef(BaseModel):
    """Reference to a radiograph cited in the source document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal[
        "panoramica",
        "panoramic",
        "periapical",
        "bite_wing",
        "lateral_cefalometrica",
        "cone_beam",
        "cbct",
        "other",
    ] = "other"
    date_iso: str | None = Field(None, max_length=30, description="ISO date as cited.")
    finding_summary: str | None = Field(None, max_length=500)


# ─── Dental history output schema ───────────────────────────────────────────


class DentalHistoryV1(BaseModel):
    """Structured dental history extracted from a patient PDF + chart image.

    Schema-cemented per Story D goldens playbook — bumping the schema → NEW
    class ``DentalHistoryV2`` (NEVER mutate V1 in place).
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    schema_version: Literal[1] = 1

    missing_pieces: list[ToothPosition] = Field(
        default_factory=list,
        description="Teeth detected as missing from the dental chart (FDI notation).",
    )
    existing_restorations: list[Restoration] = Field(default_factory=list)
    periodontal_status: PeriodontalSummary | None = None
    bite_alignment: BiteAlignmentNotes | None = None
    radiographs_referenced: list[RadiographRef] = Field(default_factory=list)

    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    """Aggregate confidence across the 4 vision-heavy waves. Wave timeouts /
    chart rotation issues / garbled images decrement this score."""

    missing_required_fields: list[str] = Field(default_factory=list)
    """Names of required fields the extractor could not populate
    (e.g. ``"missing_pieces"`` when chart image was unreadable)."""

    extraction_warnings: list[str] = Field(default_factory=list)
    """Free-form messages from waves: timeouts, parse failures, low-quality
    chart images, rotation auto-retry attempts, etc."""


__all__ = [
    "Allergy",
    "BiteAlignmentNotes",
    "Condition",
    "DentalHistoryV1",
    "ExtractionWave",
    "FamilyHistorySummary",
    "Medication",
    "MedicalHistoryV1",
    "PeriodontalSummary",
    "RadiographRef",
    "Restoration",
    "Surgery",
    "ToothPosition",
    "VitalSigns",
]
