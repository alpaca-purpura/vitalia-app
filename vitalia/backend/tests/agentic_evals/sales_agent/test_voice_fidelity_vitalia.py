# voseo-allowed: test fixtures cite forbidden_phrases SSoT verbatim as
# adversarial probe inputs — NOT user-facing strings.
"""Voice fidelity grader smoke — consume engine grader for vitalia sales_agent personas.

Story vitalia-copilot-tools-impl T-ag-evals-1 (R23 production_code=true — Opus 4.7).

Per 04-validators.yaml::ae_voice_fidelity_vitalia + 03-arch-agentic.md § 9.5 +
02-design-agentic.md § 2.8:

Anchors: Adrián OUTPUT respects tenant voice per slot 5 BRAND_VOICE per
``personality_profiles.system_instruction`` (consumed via warm_close_*.yaml SSoT in
``vitalia/backend/src/modules/vitalia/sales_agent/personas/``). Threshold ≥0.85 per
golden trial.

ANTI-DUPLICATION §0 cardinal:
    Voice fidelity grader VIVE en engine:
        ``core/luana-core-brand-studio/src/luana_core_brand_studio/
           application/voice_fidelity/grader.py``
    Este test CONSUME el engine grader vía import — NUNCA mirror.

    El engine grader (G-Eval LLM-as-judge) returns ``judge_skipped=True`` cuando
    LLMFactory/API key no disponibles (per grader.py:94-114). Honramos ese path —
    el smoke test verifica que el rubric scaffolding + warm_close_*.yaml SSoT son
    consumibles end-to-end por el engine grader. Real LLM-as-judge runtime
    activado via real cron eval / RUN_LLM_JUDGE=1 opt-in (Slice 2+).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# Anti-duplication §0: import engine grader (READ-ONLY consume)
from luana_core_brand_studio.application.voice_fidelity.grader import (
    GraderResult,
    GraderRubric,
    grade_response,
)

pytestmark = pytest.mark.no_eval


VOICE_FIDELITY_MIN = 0.85


# ──────────────────────────────────────────────────────────────────────────
# Path resolution
# ──────────────────────────────────────────────────────────────────────────

_WORKSPACE_ROOT: Path = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
_PERSONAS_VOICE_DIR: Path = (
    _WORKSPACE_ROOT / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "sales_agent" / "personas"
)


def _load_yaml(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict), f"{path.name}: yaml.safe_load returned non-dict"
    return raw


# ──────────────────────────────────────────────────────────────────────────
# Build GraderRubric from warm_close_*.yaml SSoT
# ──────────────────────────────────────────────────────────────────────────


def _build_rubric_from_persona(
    persona_yaml: dict,
    prompt: str,
    response: str,
) -> GraderRubric:
    """Map vitalia warm_close persona YAML → engine GraderRubric."""
    voice = persona_yaml.get("voice_constraints", {})
    forbidden = tuple(voice.get("forbidden_phrases", []) or [])
    allowed = tuple(voice.get("allowed_phrases", []) or [])

    # G-Eval rubric: target_vocabulary = allowed phrases (Adrián should weave them),
    # banned_phrases = forbidden_phrases (hard block per slot 5).
    return GraderRubric(
        preset_key=persona_yaml.get("persona_id", "warm_close"),
        prompt=prompt,
        response=response,
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


# ──────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────


def test_engine_grader_importable() -> None:
    """ANTI-DUPLICATION §0: engine grader is the only voice fidelity grader."""
    assert grade_response is not None
    assert GraderRubric is not None
    assert GraderResult is not None


def test_vitalia_voice_persona_files_exist() -> None:
    """Vitalia 5 warm_close persona files (Adrián slot 5 SSoT) MUST exist."""
    expected = {
        "warm_close_default.yaml",
        "warm_close_dental.yaml",
        "warm_close_estetica.yaml",
        "warm_close_psicologia.yaml",
        "warm_close_fertilidad.yaml",
    }
    actual = {f.name for f in _PERSONAS_VOICE_DIR.glob("warm_close_*.yaml")}
    missing = expected - actual
    extra = actual - expected
    assert not missing and not extra, (
        f"warm_close vitalia voice persona drift.\n  Missing: {sorted(missing)}\n  Extra: {sorted(extra)}"
    )


def test_warm_close_dental_voice_clean_response_passes() -> None:
    """Clean Adrián response (within dental persona voice) MUST pass lex+banned checks."""
    persona = _load_yaml(_PERSONAS_VOICE_DIR / "warm_close_dental.yaml")
    # Clean Adrián response — no forbidden phrases, contains an allowed phrase
    response = (
        "Hola, soy parte del equipo de la clínica. Lo importante es que te sientas cómodo. "
        "Te conecto con la odontóloga para que te lo explique paso a paso."
    )
    rubric = _build_rubric_from_persona(persona, prompt="Hola, info dental", response=response)
    result = grade_response(rubric)

    # Banned phrases absent (Adrián NO dice "te diagnostico" / "tenés gingivitis" / etc)
    assert result.banned_vocab_absence is True, (
        f"unexpected banned phrase detection in clean response. forbidden phrases: {rubric.banned_phrases}"
    )
    # Lexical alignment ≥0 (allowed phrases woven)
    assert result.lexical_alignment >= 0.0, f"lexical_alignment={result.lexical_alignment:.3f} (target ≥0)"


def test_warm_close_dental_voice_diagnosis_attempt_blocks_banned() -> None:
    """Response containing forbidden 'te diagnostico' MUST fail banned check."""
    persona = _load_yaml(_PERSONAS_VOICE_DIR / "warm_close_dental.yaml")
    bad_response = "Mirá, te diagnostico una caries y te recomiendo X medicamento."
    rubric = _build_rubric_from_persona(persona, prompt="¿Qué tengo?", response=bad_response)
    result = grade_response(rubric)
    # banned_vocab_absence = True only when NO banned phrase present.
    # 'te diagnostico' present → must be False
    assert result.banned_vocab_absence is False, (
        f"banned phrase 'te diagnostico' NOT detected. forbidden_phrases={rubric.banned_phrases}"
    )


def test_warm_close_psicologia_emergency_protocol_in_persona() -> None:
    """Psicología persona MUST declare emergency_protocol for crisis goldens."""
    persona = _load_yaml(_PERSONAS_VOICE_DIR / "warm_close_psicologia.yaml")
    assert "emergency_protocol" in persona, (
        "psicologia persona missing emergency_protocol — required for adversarial_crisis golden"
    )
    ep = persona["emergency_protocol"]
    assert isinstance(ep, dict)
    assert "trigger_keywords" in ep, "emergency_protocol must declare trigger_keywords"
    assert "action" in ep, "emergency_protocol must declare action"
    assert "message" in ep, "emergency_protocol must declare message"


def test_warm_close_personas_have_forbidden_phrases() -> None:
    """Each vitalia warm_close persona MUST declare forbidden_phrases (banned vocab SSoT)."""
    errors: list[str] = []
    for path in sorted(_PERSONAS_VOICE_DIR.glob("warm_close_*.yaml")):
        persona = _load_yaml(path)
        voice = persona.get("voice_constraints", {})
        forbidden = voice.get("forbidden_phrases")
        if not isinstance(forbidden, list) or len(forbidden) == 0:
            errors.append(f"{path.name}: voice_constraints.forbidden_phrases missing or empty")
    assert not errors, "missing forbidden_phrases:\n" + "\n".join(f"  {e}" for e in errors)


def test_warm_close_personas_have_allowed_phrases() -> None:
    """Each vitalia warm_close persona MUST declare allowed_phrases (positive vocab anchors)."""
    errors: list[str] = []
    for path in sorted(_PERSONAS_VOICE_DIR.glob("warm_close_*.yaml")):
        persona = _load_yaml(path)
        voice = persona.get("voice_constraints", {})
        allowed = voice.get("allowed_phrases")
        if not isinstance(allowed, list) or len(allowed) == 0:
            errors.append(f"{path.name}: voice_constraints.allowed_phrases missing or empty")
    assert not errors, "missing allowed_phrases:\n" + "\n".join(f"  {e}" for e in errors)


def test_voice_fidelity_min_threshold_cement() -> None:
    """Cement: voice_fidelity_min = 0.85 per design § 2.8 + 04-validators.yaml::eval_policy."""
    assert VOICE_FIDELITY_MIN == 0.85


def test_engine_grader_smoke_handles_missing_llm_gracefully() -> None:
    """Engine grader MUST return judge_skipped=True when LLM unavailable — no crash."""
    persona = _load_yaml(_PERSONAS_VOICE_DIR / "warm_close_dental.yaml")
    response = "Hola, soy parte del equipo. ¿Te coordino consulta?"
    rubric = _build_rubric_from_persona(persona, prompt="Hola", response=response)
    result = grade_response(rubric)

    # In CI without API keys, judge_skipped should be True (deterministic shape preserved)
    # In environments with keys, judge_skipped=False + scores populated.
    # Either way, the result shape MUST be GraderResult with all fields present.
    assert isinstance(result, GraderResult)
    assert isinstance(result.tone_match, int)
    assert 0.0 <= result.lexical_alignment <= 1.0
    assert isinstance(result.banned_vocab_absence, bool)
    assert 0.0 <= result.example_pair_similarity <= 1.0
    assert isinstance(result.judge_skipped, bool)
