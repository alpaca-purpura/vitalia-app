# voseo-allowed: regex detection patterns cite voseo markers as probe input — not user-facing strings.
"""Wizard goldens smoke regression — post FE wire-up (T-onboarding-7).

Story vitalia-slice-1-onboarding-wizard T-onboarding-7 (production_code=false).

Purpose:
    Verify that the 4 shipped wizard goldens (happy, negative, edge_browser_close, adversarial)
    still pass post T-onboarding-6 FE wire-up. The FE wizard now calls the same BE endpoints
    that the goldens exercise — this file confirms no import drift or contract breakage.

Scope (per 06-tickets-refresh.yaml T-onboarding-7 refresh_scope):
    1. Filesystem check: 4 golden YAML paths exist at exact canonical locations.
    2. Import check: runner module (test_wizard_pass_k_evaluation) importable without errors.
    3. Happy golden smoke: single trial, pass threshold ≥0.5.
    4. Voice fidelity grader smoke: engine grader (READ-ONLY consume from luana_core_brand_studio)
       processes a Valeria sample drawn from happy golden — result shape valid.

ANTI-DUPLICATION §0:
    Voice fidelity grader VIVE en engine:
        core/luana-core-brand-studio/src/luana_core_brand_studio/application/voice_fidelity/grader.py
    Este test CONSUME el engine grader vía import — NUNCA mirror.
    El grader retorna judge_skipped=True cuando LLM API key no disponible (CI).
    Honramos ese path — smoke verifica que el scaffolding + wizard golden son consumibles.

R23 OPT-OUT ratificado Chris 2026-05-18:
    production_code=false — esta es smoke regression post-FE-wire, no nuevo código agentic.
    Sonnet owner_eligibility OK.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

# Anti-duplication §0: import engine voice fidelity grader (READ-ONLY consume)
from luana_core_brand_studio.application.voice_fidelity.grader import (
    GraderResult,
    GraderRubric,
    grade_response,
)


def _import_runner() -> object:
    """Import test_wizard_pass_k_evaluation by path (pytest rootdir=vitalia/backend).

    Registers module in sys.modules before exec so @dataclass decorators resolve
    cls.__module__ correctly (required for frozen=True dataclasses in Python 3.12).
    """
    import sys

    module_name = "test_wizard_pass_k_evaluation"
    if module_name in sys.modules:
        return sys.modules[module_name]

    runner_path = Path(__file__).resolve().parent / "test_wizard_pass_k_evaluation.py"
    spec = importlib.util.spec_from_file_location(module_name, runner_path)
    assert spec is not None, f"Cannot load spec from {runner_path}"
    module = importlib.util.module_from_spec(spec)
    # Register BEFORE exec so __module__ lookup works for @dataclass(frozen=True)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# Runner imported for import-resolution smoke (not re-executed as a test)
_runner = _import_runner()

pytestmark = pytest.mark.no_eval


# ──────────────────────────────────────────────────────────────────────────
# Path resolution
# ──────────────────────────────────────────────────────────────────────────

_WORKSPACE_ROOT: Path = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())

_GOLDENS_DIR: Path = _WORKSPACE_ROOT / "vitalia" / "backend" / "tests" / "agentic_evals" / "copilot" / "wizard_goldens"

_PERSONAS_DIR: Path = (
    _WORKSPACE_ROOT / "vitalia" / "backend" / "tests" / "agentic_evals" / "copilot" / "wizard_personas"
)

_SALES_PERSONAS_DIR: Path = (
    _WORKSPACE_ROOT / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "sales_agent" / "personas"
)

# Canonical 4 golden paths (must exist verbatim)
_EXPECTED_GOLDEN_PATHS: tuple[str, ...] = (
    "happy.yaml",
    "negative.yaml",
    "edge_browser_close.yaml",
    "adversarial.yaml",
)


def _load_yaml(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict), f"{path.name}: yaml.safe_load returned non-dict"
    return raw


# ──────────────────────────────────────────────────────────────────────────
# Test 1: filesystem check — 4 golden YAML paths exist at exact locations
# ──────────────────────────────────────────────────────────────────────────


def test_4_goldens_exist() -> None:
    """Canonical wizard golden files MUST exist at exact paths post FE wire-up.

    Verifies that no migration, rename, or cleanup during T-onboarding-6 FE
    development displaced the 4 shipped golden files.
    """
    missing: list[str] = []
    for name in _EXPECTED_GOLDEN_PATHS:
        path = _GOLDENS_DIR / name
        if not path.is_file():
            missing.append(str(path))
    assert not missing, "Wizard golden files displaced post FE wire-up.\nMissing:\n" + "\n".join(
        f"  {p}" for p in missing
    )


# ──────────────────────────────────────────────────────────────────────────
# Test 2: import resolution — runner importable without errors post T-1..T-6
# ──────────────────────────────────────────────────────────────────────────


def test_runner_imports_resolve() -> None:
    """test_wizard_pass_k_evaluation module MUST be importable after T-1..T-6 merges.

    Confirms that no circular imports, missing dependencies, or path drift
    from the earlier tickets broke the runner module (which references golden
    paths, persona paths, and the LangGraph wizard state at import time).
    """
    # Module already imported at top level — if import failed the whole test file
    # would fail to collect. Assert the critical runner symbols are accessible.
    assert hasattr(_runner, "_GOLDENS_DIR"), "runner._GOLDENS_DIR missing"
    assert hasattr(_runner, "_PERSONAS_DIR"), "runner._PERSONAS_DIR missing"
    assert hasattr(_runner, "_discover_goldens"), "runner._discover_goldens missing"
    assert hasattr(_runner, "TRIALS_PER_SCENARIO"), "runner.TRIALS_PER_SCENARIO missing"
    assert hasattr(_runner, "PASS_K_THRESHOLD"), "runner.PASS_K_THRESHOLD missing"
    assert hasattr(_runner, "VOICE_FIDELITY_MIN"), "runner.VOICE_FIDELITY_MIN missing"

    # Policy constants not drifted from cement values
    assert _runner.TRIALS_PER_SCENARIO == 3, f"TRIALS_PER_SCENARIO drifted: {_runner.TRIALS_PER_SCENARIO}"
    assert _runner.PASS_K_THRESHOLD == 0.5, f"PASS_K_THRESHOLD drifted: {_runner.PASS_K_THRESHOLD}"
    assert _runner.VOICE_FIDELITY_MIN == 0.85, f"VOICE_FIDELITY_MIN drifted: {_runner.VOICE_FIDELITY_MIN}"

    # Goldens dir still resolves to existing directory
    assert _runner._GOLDENS_DIR.is_dir(), f"runner._GOLDENS_DIR not found: {_runner._GOLDENS_DIR}"

    # All 4 goldens discovered (count check)
    goldens = _runner._discover_goldens()
    assert len(goldens) == 4, f"runner discovered {len(goldens)} goldens, expected 4: {[p.name for p, _ in goldens]}"


# ──────────────────────────────────────────────────────────────────────────
# Test 3: happy golden smoke — single trial, pass rate ≥ PASS_K_THRESHOLD
# ──────────────────────────────────────────────────────────────────────────


def test_run_happy_golden_smoke() -> None:
    """Happy golden MUST pass a single trial with ≥0.5 pass rate post FE wire-up.

    Exercises the full grader pipeline on happy.yaml (the primary success-path
    golden) to confirm that:
      - The golden YAML is loadable and schema-valid
      - Persona cross-reference resolves
      - All 5 rubric grades return valid floats
      - Trial passes at ≥50% of 5 dimensions (i.e. ≥3/5 dimensions pass)

    This is the minimum smoke: if happy.yaml fails, the wizard contract is broken.
    """
    golden_path = _GOLDENS_DIR / "happy.yaml"
    assert golden_path.is_file(), f"happy.yaml missing: {golden_path}"

    golden = _load_yaml(golden_path)

    # Required top-level fields
    assert "scenario" in golden, "happy.yaml missing 'scenario'"
    assert "persona" in golden, "happy.yaml missing 'persona'"
    assert "input_conversation" in golden, "happy.yaml missing 'input_conversation'"
    assert golden["scenario"] == "happy", f"expected scenario='happy', got '{golden['scenario']}'"

    # Persona cross-reference resolves
    persona_path = _PERSONAS_DIR / golden["persona"]
    assert persona_path.is_file(), f"happy.yaml persona '{golden['persona']}' not found at: {persona_path}"
    persona = _load_yaml(persona_path)

    # Grade single trial via runner graders
    result = _runner._grade_trial(golden, persona)

    # All 5 rubric scores present
    for rubric in _runner.RUBRICS:
        assert rubric in result.rubric_scores, f"happy golden missing rubric score: {rubric}"
        score = result.rubric_scores[rubric]
        assert 0.0 <= score <= 1.0, f"happy golden rubric '{rubric}' score out of [0,1]: {score}"

    # Single trial passes at PASS_K_THRESHOLD (≥50% goldens = at minimum happy passes)
    pass_rate = 1.0 if result.trial_passed else 0.0
    assert pass_rate >= _runner.PASS_K_THRESHOLD, (
        f"Happy golden smoke FAILED: trial_passed={result.trial_passed}, "
        f"dimensions_passed={result.dimensions_passed}/{result.total_dimensions}, "
        f"rubric_scores={result.rubric_scores}"
    )


# ──────────────────────────────────────────────────────────────────────────
# Test 4: voice fidelity grader smoke — engine grader on Valeria sample
# ──────────────────────────────────────────────────────────────────────────


def test_voice_fidelity_grader_smoke() -> None:
    """Engine voice fidelity grader MUST process a Valeria wizard sample without crash.

    Consumes the engine grader (luana_core_brand_studio.application.voice_fidelity.grader)
    READ-ONLY with a representative Adrián/Valeria sample drawn from the happy golden
    assistant turns to verify:
      - GraderRubric is constructible with wizard-style content
      - grade_response() returns a valid GraderResult shape
      - In CI (no API key): judge_skipped=True + lex + banned fields populated
      - In live env (RUN_LLM_JUDGE=1): result.tone_match ≥0 (non-negative)

    Anchored to sales_agent warm_close_dental persona voice constraints
    (12 goldens scenario corpus, 3 pass^k trials per scenario — see
    vitalia/backend/tests/agentic_evals/sales_agent/).

    ANTI-DUPLICATION §0: grader VIVE en engine, NOT mirrored here.
    """
    # Use dental warm_close persona (ships with vitalia sales_agent — 5 persona files)
    dental_persona_path = _SALES_PERSONAS_DIR / "warm_close_dental.yaml"
    assert dental_persona_path.is_file(), (
        f"warm_close_dental.yaml not found at: {dental_persona_path}. "
        "Run T-ag-evals-1 or verify sales_agent personas shipped."
    )
    dental_persona = _load_yaml(dental_persona_path)

    # Extract a real Valeria assistant turn from happy golden as the "response under test"
    happy_golden = _load_yaml(_GOLDENS_DIR / "happy.yaml")
    valeria_turns = [t["content"] for t in happy_golden.get("input_conversation", []) if t.get("role") == "assistant"]
    assert valeria_turns, "happy.yaml has no assistant turns — golden malformed"

    # Use the slot confirmation turn (natural, warm, tuteo neutro)
    sample_response = valeria_turns[1] if len(valeria_turns) > 1 else valeria_turns[0]

    # Build GraderRubric from dental persona voice constraints
    voice = dental_persona.get("voice_constraints", {})
    forbidden = tuple(voice.get("forbidden_phrases", []) or [])
    allowed = tuple(voice.get("allowed_phrases", []) or [])

    rubric = GraderRubric(
        preset_key=dental_persona.get("persona_id", "warm_close_dental"),
        prompt="Configura la cuenta de la clínica",
        response=sample_response,
        target_dimensions={
            "warmth": 0.8,
            "professional": 0.9,
            "clarity": 0.8,
            "no_diagnosis": 1.0,
        },
        target_vocabulary=allowed,
        banned_phrases=forbidden,
        sample_exchanges=(),
    )

    # Consume engine grader
    result = grade_response(rubric)

    # GraderResult shape MUST be valid (regardless of judge_skipped)
    assert isinstance(result, GraderResult), f"grade_response returned unexpected type: {type(result)}"
    assert isinstance(result.tone_match, int), f"GraderResult.tone_match expected int, got {type(result.tone_match)}"
    assert 0.0 <= result.lexical_alignment <= 1.0, (
        f"GraderResult.lexical_alignment out of [0,1]: {result.lexical_alignment}"
    )
    assert isinstance(result.banned_vocab_absence, bool), (
        f"GraderResult.banned_vocab_absence expected bool, got {type(result.banned_vocab_absence)}"
    )
    assert 0.0 <= result.example_pair_similarity <= 1.0, (
        f"GraderResult.example_pair_similarity out of [0,1]: {result.example_pair_similarity}"
    )
    assert isinstance(result.judge_skipped, bool), (
        f"GraderResult.judge_skipped expected bool, got {type(result.judge_skipped)}"
    )

    # A clean Valeria turn (tuteo, no forbidden medical phrases) MUST pass banned check
    assert result.banned_vocab_absence is True, (
        f"Engine grader flagged banned phrase in clean Valeria wizard turn. "
        f"Response: '{sample_response[:120]}'. forbidden_phrases: {forbidden}"
    )
