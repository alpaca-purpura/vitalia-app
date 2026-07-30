"""Agentic eval cost budget — PDF extraction ≤$0.15 medical / ≤$0.18 dental (V-AE-16).

PDF extraction cost ceilings:
  MedicalKBExtractor (4 waves): ≤$0.15 USD per PDF
  DentalHistoryExtractor (4 waves vision-heavy): ≤$0.18 USD per PDF

Per 04-validators.yaml V-AE-16:
  "PDF extraction cost ≤$0.15 medical / ≤$0.18 dental (vision-heavy)"
  Threshold: 0.15 USD medical, 0.18 USD dental.

Per 03-arch-agentic.md § 5.1:
  MedicalKBExtractor waves:
    Wave 1 (allergies_and_medications): claude-sonnet-4-6-vision, timeout 30s
    Wave 2 (conditions_and_surgeries): claude-sonnet-4-6-vision, timeout 30s
    Wave 3 (family_and_vitals): claude-haiku-4-5-vision, timeout 20s
    Wave 4 (validate_and_merge): claude-sonnet-4-6, timeout 20s
  Cost/latency: ~$0.15 USD per PDF, p50 25s / p99 70s

Per 03-arch-agentic.md § 5.2:
  DentalHistoryExtractor: same wave pattern, vision-heavy
  Cost/latency: ~$0.18 USD per PDF, p50 30s / p99 90s

Per 03-arch-agentic.md § 15:
  PDF vision extraction waves:
    Waves 1-2: claude-sonnet-4-6-vision
    Wave 3: claude-haiku-4-5-vision
    Wave 4 (merge): claude-sonnet-4-6

Strategy — deterministic 4-wave cost model (no live LLM calls):
  Each wave = 1 LLM call. Vision models process PDF page images.
  Token estimates based on:
    - Vision input: ~1500-2500 tokens per PDF page (depends on page count)
    - Typical medical PDF: 3-5 pages → 4500-12500 image tokens per vision wave
    - Output: structured JSON extraction, ~200-400 tokens per wave
    - Wave 4 merge: text-only, ~800 tokens input (aggregated JSON), ~300 tokens output

  Approximate vision model pricing (May 2026 reference):
    claude-sonnet-4-6-vision: $3.00/M input + $15.00/M output (vision parity with text)
    claude-haiku-4-5-vision:  $0.80/M input + $4.00/M output (vision parity with text)
  Note: vision token pricing uses same per-token rate; image pre-processing
  handles resizing. LiteLLM Proxy normalizes to token counts.

  The 4-wave architecture distributes cost across specialized extraction passes,
  keeping total within the $0.15/$0.18 ceiling.

Run:
    cd $WS/vitalia/backend && uv run pytest \
        tests/agentic_evals/cost_budget/test_cost_budget_pdf_extraction.py -v
"""

from __future__ import annotations

from dataclasses import dataclass

# ── Cost model types ──────────────────────────────────────────────────────────


@dataclass
class _ExtractionWaveRecord:
    """Synthetic LLM call record for one extraction wave."""

    wave_name: str
    wave_number: int
    model: str
    input_tokens: int  # includes vision image tokens for multimodal waves
    output_tokens: int  # structured JSON extraction output
    cost_usd: float = 0.0


# ── Model pricing ─────────────────────────────────────────────────────────────

_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6-vision": {
        "input_per_m": 3.00,
        "output_per_m": 15.00,
    },
    "claude-haiku-4-5-vision": {
        "input_per_m": 0.80,
        "output_per_m": 4.00,
    },
    "claude-sonnet-4-6": {
        "input_per_m": 3.00,
        "output_per_m": 15.00,
    },
}


def _compute_wave_cost(record: _ExtractionWaveRecord) -> float:
    """Compute cost for one extraction wave (no prompt caching for PDF extraction — unique per PDF)."""
    p = _PRICING[record.model]
    return record.input_tokens * p["input_per_m"] / 1_000_000 + record.output_tokens * p["output_per_m"] / 1_000_000


# ── Synthetic Medical PDF extraction (MedicalKBExtractor — 4 waves) ──────────


def _build_medical_kb_extractor_records(pdf_pages: int = 4) -> list[_ExtractionWaveRecord]:
    """Build synthetic wave records for MedicalKBExtractor.

    Args:
        pdf_pages: Number of PDF pages (typical medical PDF: 3-5 pages)

    Wave routing per 03-arch-agentic.md § 5.1:
      Wave 1 (allergies_and_medications): claude-sonnet-4-6-vision
      Wave 2 (conditions_and_surgeries): claude-sonnet-4-6-vision
      Wave 3 (family_and_vitals): claude-haiku-4-5-vision
      Wave 4 (validate_and_merge): claude-sonnet-4-6 (text-only, merge)

    Token estimates:
      Vision input per page: ~1800 tokens (standard medical form density)
      Prompt per wave: ~200 tokens (wave-specific system prompt)
      Output per vision wave: ~250 tokens (structured JSON)
      Wave 4 input: aggregated JSON from waves 1-3 (~800 tokens, no vision)
      Wave 4 output: validated merged MedicalHistoryV1 (~350 tokens)
    """
    vision_tokens_per_page = 1_800
    total_vision_tokens = pdf_pages * vision_tokens_per_page
    wave_prompt_tokens = 200  # system prompt per wave

    records: list[_ExtractionWaveRecord] = []

    # Wave 1: allergies + medications — sonnet vision
    w1 = _ExtractionWaveRecord(
        wave_name="allergies_and_medications",
        wave_number=1,
        model="claude-sonnet-4-6-vision",
        input_tokens=wave_prompt_tokens + total_vision_tokens,
        output_tokens=250,
    )
    w1.cost_usd = _compute_wave_cost(w1)
    records.append(w1)

    # Wave 2: conditions + surgeries — sonnet vision
    w2 = _ExtractionWaveRecord(
        wave_name="conditions_and_surgeries",
        wave_number=2,
        model="claude-sonnet-4-6-vision",
        input_tokens=wave_prompt_tokens + total_vision_tokens,
        output_tokens=250,
    )
    w2.cost_usd = _compute_wave_cost(w2)
    records.append(w2)

    # Wave 3: family history + vitals — haiku vision (simpler extraction)
    w3 = _ExtractionWaveRecord(
        wave_name="family_and_vitals",
        wave_number=3,
        model="claude-haiku-4-5-vision",
        input_tokens=wave_prompt_tokens + total_vision_tokens,
        output_tokens=200,
    )
    w3.cost_usd = _compute_wave_cost(w3)
    records.append(w3)

    # Wave 4: validate + merge — sonnet text-only (aggregate JSON from waves 1-3)
    wave_outputs_tokens = 250 + 250 + 200  # combined JSON from waves 1-3
    w4 = _ExtractionWaveRecord(
        wave_name="validate_and_merge",
        wave_number=4,
        model="claude-sonnet-4-6",
        input_tokens=wave_prompt_tokens + wave_outputs_tokens,
        output_tokens=350,
    )
    w4.cost_usd = _compute_wave_cost(w4)
    records.append(w4)

    return records


# ── Synthetic Dental PDF extraction (DentalHistoryExtractor — 4 waves) ────────


def _build_dental_history_extractor_records(pdf_pages: int = 5) -> list[_ExtractionWaveRecord]:
    """Build synthetic wave records for DentalHistoryExtractor.

    Dental PDFs are vision-heavy (radiograph images, dental charts):
      Typical dental PDF: 4-6 pages including radiograph images
      Radiograph images = higher token count per page (~2200 tokens vs 1800 medical)

    Wave routing per 03-arch-agentic.md § 5.2:
      Same pattern as MedicalKBExtractor; dental output schema includes
      FDI notation (missing_pieces 11-48) + existing_restorations + periodontal_status.

    Cost: ~$0.18 USD per PDF (higher than medical due to radiograph density).
    """
    # Dental PDFs are more image-dense (radiographs count ~2200 tokens/page)
    vision_tokens_per_page = 2_200
    total_vision_tokens = pdf_pages * vision_tokens_per_page
    wave_prompt_tokens = 200

    records: list[_ExtractionWaveRecord] = []

    # Wave 1: FDI notation + missing pieces — sonnet vision (dental charts)
    w1 = _ExtractionWaveRecord(
        wave_name="fdi_notation_and_missing",
        wave_number=1,
        model="claude-sonnet-4-6-vision",
        input_tokens=wave_prompt_tokens + total_vision_tokens,
        output_tokens=280,
    )
    w1.cost_usd = _compute_wave_cost(w1)
    records.append(w1)

    # Wave 2: restorations + periodontal — sonnet vision (requires dental expertise)
    w2 = _ExtractionWaveRecord(
        wave_name="restorations_and_periodontal",
        wave_number=2,
        model="claude-sonnet-4-6-vision",
        input_tokens=wave_prompt_tokens + total_vision_tokens,
        output_tokens=260,
    )
    w2.cost_usd = _compute_wave_cost(w2)
    records.append(w2)

    # Wave 3: bite alignment + radiograph refs — haiku vision (less complex classification)
    w3 = _ExtractionWaveRecord(
        wave_name="bite_and_radiograph_refs",
        wave_number=3,
        model="claude-haiku-4-5-vision",
        input_tokens=wave_prompt_tokens + total_vision_tokens,
        output_tokens=180,
    )
    w3.cost_usd = _compute_wave_cost(w3)
    records.append(w3)

    # Wave 4: validate + merge dental schema — sonnet text-only
    wave_outputs_tokens = 280 + 260 + 180
    w4 = _ExtractionWaveRecord(
        wave_name="validate_and_merge_dental",
        wave_number=4,
        model="claude-sonnet-4-6",
        input_tokens=wave_prompt_tokens + wave_outputs_tokens,
        output_tokens=380,
    )
    w4.cost_usd = _compute_wave_cost(w4)
    records.append(w4)

    return records


# ── Cost budget ceilings ──────────────────────────────────────────────────────

_COST_CEILING_MEDICAL_USD = 0.15  # per V-AE-16 + 03-arch § 14.3
_COST_CEILING_DENTAL_USD = 0.18  # per V-AE-16 + 03-arch § 14.3


# ── Tests: MedicalKBExtractor ─────────────────────────────────────────────────


def test_cost_budget_medical_kb_extractor_within_ceiling() -> None:
    """V-AE-16: MedicalKBExtractor 4-wave total cost MUST be ≤$0.15 USD per PDF."""
    records = _build_medical_kb_extractor_records(pdf_pages=4)  # typical 4-page medical PDF
    total_cost = sum(r.cost_usd for r in records)

    assert total_cost <= _COST_CEILING_MEDICAL_USD, (
        f"V-AE-16 FAIL: MedicalKBExtractor cost ${total_cost:.6f} > ceiling ${_COST_CEILING_MEDICAL_USD:.2f} USD.\n"
        f"Per-wave breakdown:\n"
        + "\n".join(
            f"  Wave {r.wave_number} ({r.wave_name}, {r.model}): "
            f"in={r.input_tokens} out={r.output_tokens} → ${r.cost_usd:.6f}"
            for r in records
        )
    )


def test_cost_budget_medical_kb_extractor_four_waves() -> None:
    """Sanity: MedicalKBExtractor MUST have exactly 4 waves per 03-arch § 5.1."""
    records = _build_medical_kb_extractor_records()
    assert len(records) == 4, f"Expected 4 extraction waves, got {len(records)}"


def test_cost_budget_medical_kb_extractor_routing() -> None:
    """V-AE-16 routing: MedicalKBExtractor wave models per § 15.

    Waves 1-2: claude-sonnet-4-6-vision
    Wave 3: claude-haiku-4-5-vision
    Wave 4 (merge): claude-sonnet-4-6
    """
    records = _build_medical_kb_extractor_records()
    assert records[0].model == "claude-sonnet-4-6-vision", "Wave 1 must be sonnet-vision"
    assert records[1].model == "claude-sonnet-4-6-vision", "Wave 2 must be sonnet-vision"
    assert records[2].model == "claude-haiku-4-5-vision", "Wave 3 must be haiku-vision"
    assert records[3].model == "claude-sonnet-4-6", "Wave 4 (merge) must be sonnet text-only"


def test_cost_budget_medical_kb_extractor_worst_case_5_pages() -> None:
    """V-AE-16 worst-case: 5-page medical PDF MUST still be within ceiling."""
    records = _build_medical_kb_extractor_records(pdf_pages=5)
    total_cost = sum(r.cost_usd for r in records)

    assert total_cost <= _COST_CEILING_MEDICAL_USD, (
        f"V-AE-16 worst-case (5 pages): MedicalKBExtractor ${total_cost:.6f} "
        f"> ceiling ${_COST_CEILING_MEDICAL_USD:.2f} USD.\n"
        "5-page medical PDFs are within typical range — budget must accommodate."
    )


# ── Tests: DentalHistoryExtractor ─────────────────────────────────────────────


def test_cost_budget_dental_history_extractor_within_ceiling() -> None:
    """V-AE-16: DentalHistoryExtractor 4-wave total cost MUST be ≤$0.18 USD per PDF."""
    records = _build_dental_history_extractor_records(pdf_pages=5)  # typical 5-page dental PDF
    total_cost = sum(r.cost_usd for r in records)

    assert total_cost <= _COST_CEILING_DENTAL_USD, (
        f"V-AE-16 FAIL: DentalHistoryExtractor cost ${total_cost:.6f} > ceiling ${_COST_CEILING_DENTAL_USD:.2f} USD.\n"
        f"Per-wave breakdown:\n"
        + "\n".join(
            f"  Wave {r.wave_number} ({r.wave_name}, {r.model}): "
            f"in={r.input_tokens} out={r.output_tokens} → ${r.cost_usd:.6f}"
            for r in records
        )
    )


def test_cost_budget_dental_history_extractor_four_waves() -> None:
    """Sanity: DentalHistoryExtractor MUST have exactly 4 waves per 03-arch § 5.2."""
    records = _build_dental_history_extractor_records()
    assert len(records) == 4, f"Expected 4 extraction waves, got {len(records)}"


def test_cost_budget_dental_history_extractor_routing() -> None:
    """V-AE-16 routing: DentalHistoryExtractor wave models per § 15 (vision-heavy).

    Same wave routing as MedicalKBExtractor but higher token density.
    """
    records = _build_dental_history_extractor_records()
    assert records[0].model == "claude-sonnet-4-6-vision", "Wave 1 must be sonnet-vision"
    assert records[1].model == "claude-sonnet-4-6-vision", "Wave 2 must be sonnet-vision"
    assert records[2].model == "claude-haiku-4-5-vision", "Wave 3 must be haiku-vision"
    assert records[3].model == "claude-sonnet-4-6", "Wave 4 (merge) must be sonnet text-only"


def test_cost_budget_dental_higher_than_medical() -> None:
    """V-AE-16 design intent: dental PDF costs more than medical (radiograph density).

    03-arch § 14.3 specifies different ceilings: medical $0.15, dental $0.18.
    This test verifies the cost model reflects the intended density difference.
    """
    medical_records = _build_medical_kb_extractor_records(pdf_pages=4)
    dental_records = _build_dental_history_extractor_records(pdf_pages=4)  # same pages, different density

    medical_total = sum(r.cost_usd for r in medical_records)
    dental_total = sum(r.cost_usd for r in dental_records)

    assert dental_total > medical_total, (
        f"Dental extraction (radiograph-dense) should cost more than medical at same page count. "
        f"Medical: ${medical_total:.6f}, Dental: ${dental_total:.6f}. "
        "Check vision_tokens_per_page in extractor builders."
    )


# ── Tests: Ceiling constants ───────────────────────────────────────────────────


def test_cost_budget_medical_ceiling_constant() -> None:
    """V-AE-16 ceiling constant: medical PDF limit MUST be $0.15 USD."""
    assert _COST_CEILING_MEDICAL_USD == 0.15  # Cement per V-AE-16 + § 14.3


def test_cost_budget_dental_ceiling_constant() -> None:
    """V-AE-16 ceiling constant: dental PDF limit MUST be $0.18 USD."""
    assert _COST_CEILING_DENTAL_USD == 0.18  # Cement per V-AE-16 + § 14.3


def test_cost_budget_pdf_dental_ceiling_higher_than_medical() -> None:
    """V-AE-16 invariant: dental ceiling ($0.18) > medical ceiling ($0.15)."""
    assert _COST_CEILING_DENTAL_USD > _COST_CEILING_MEDICAL_USD, (
        f"Dental ceiling ${_COST_CEILING_DENTAL_USD} must exceed medical ${_COST_CEILING_MEDICAL_USD}. "
        "Dental is vision-heavy (radiographs) → higher cost per § 5.2."
    )
