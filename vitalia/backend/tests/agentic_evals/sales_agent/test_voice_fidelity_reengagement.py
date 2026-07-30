# voseo-allowed: test fixtures + assertions reference voseo markers as detection / tenant-voice
# signals — NOT user-facing strings. sales_agent OUTPUT respects tenant voice per slot 5.
"""Voice fidelity grader smoke — Adrián 4 reengagement golden scenarios.

Story vitalia-slice-1-fidelizacion T-15 (R23 production_code=false — tests/goldens Sonnet OK).

Per 04-validators.yaml::adrian_voice_fidelity_reengagement + 03-arch-agentic.md § 9.5:
  Threshold ≥0.85 per golden.
  Engine grader consumed (anti-duplication §0 — NEVER mirror).

Anchors:
  Adrián OUTPUT respects tenant voice per slot 5 BRAND_VOICE per
  ``personality_profiles.system_instruction`` consumed via warm_close_*.yaml SSoT in
  ``vitalia/backend/src/modules/vitalia/sales_agent/personas/``.

  Reengagement goldens test the NEW send_proactive_reengagement tool (T-9) scenarios:
  - happy_multi_session: active treatment gap → template sent (es-AR voseo)
  - happy_follow_up: post-treatment control due → template sent (es-AR voseo)
  - happy_maintenance: periodic maintenance → template sent (es-MX tuteo)
  - absence_optin_guard: opt-out patient → NO tool invoked (Adrián neutral response)

ANTI-DUPLICATION §0 cardinal:
    Voice fidelity grader VIVE en engine:
        ``core/luana-core-brand-studio/src/luana_core_brand_studio/
           application/voice_fidelity/grader.py``
    Este test CONSUME el engine grader vía import — NUNCA mirror.

    Engine grader returns ``judge_skipped=True`` cuando LLM unavailable (CI context).
    Honramos ese path — smoke verifica rubric scaffolding + warm_close_*.yaml SSoT
    son consumibles end-to-end. Real LLM-as-judge via RUN_LLM_JUDGE=1 opt-in (Slice 2+).

HIPAA-lite invariant:
    Goldens use [PATIENT_ID] / [PATIENT_PHONE] placeholders for PHI fields.
    Actual PHI NEVER committed to golden YAML files.
    This test additionally validates that NO real PHI patterns appear in
    golden assistant responses.
"""

from __future__ import annotations

import re
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


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

VOICE_FIDELITY_MIN = 0.85

# Reengagement-specific: Adrián uses cálido/proactivo tone in reminders.
# Golden Adrián responses should reflect operational language (confirmations, reports).
# For absence_optin_guard: Adrián explains NON-send clearly.
_OPTIN_GUARD_EXPECTED_KEYWORDS = re.compile(
    r"optó|baja|mensajes\s+proactivos|no\s+se\s+enviará|respetamos|comunicaciones",
    re.IGNORECASE,
)

# PHI leak guard (from hipaa-lite.md SSoT — vitalia/.claude/rules/hipaa-lite.md)
_PHI_LEAK_PATTERNS = re.compile(
    r"\b(?:"
    r"dni\s*\d{6,}|"
    r"cuit\s*\d{2}-?\d{6,8}-?\d|"
    r"resultados?\s+de\s+(?:tu|sus)\s+(?:laboratorio|an[aá]lisis)|"
    r"diagn[oó]stico\s+(?:confirmado|definitivo)"
    r")\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Path resolution (workspace-anchored, multibrand-safe)
# ─────────────────────────────────────────────────────────────────────────────

_WORKSPACE_ROOT: Path = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
_REENGAGEMENT_GOLDENS_DIR: Path = (
    _WORKSPACE_ROOT / "vitalia" / "backend" / "tests" / "agentic_evals" / "sales_agent" / "goldens" / "reengagement"
)
_PERSONAS_VOICE_DIR: Path = (
    _WORKSPACE_ROOT / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "sales_agent" / "personas"
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _load_yaml(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict), f"{path.name}: yaml.safe_load returned non-dict"
    return raw


def _build_rubric_from_persona(
    persona_yaml: dict,
    prompt: str,
    response: str,
) -> GraderRubric:
    """Map vitalia warm_close persona YAML → engine GraderRubric.

    Same pattern as test_voice_fidelity_vitalia.py (anti-duplication: reuse,
    don't mirror logic).
    """
    voice = persona_yaml.get("voice_constraints", {})
    forbidden = tuple(voice.get("forbidden_phrases", []) or [])
    allowed = tuple(voice.get("allowed_phrases", []) or [])

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


def _collect_assistant_text(golden: dict) -> str:
    """Collect all assistant turns into a single string for grading."""
    return " ".join(turn["content"] for turn in golden.get("input_conversation", []) if turn.get("role") == "assistant")


# ─────────────────────────────────────────────────────────────────────────────
# Structural tests (goldens presence + schema)
# ─────────────────────────────────────────────────────────────────────────────


def test_reengagement_goldens_dir_exists() -> None:
    """Reengagement goldens directory MUST exist (T-15 created it)."""
    assert _REENGAGEMENT_GOLDENS_DIR.is_dir(), f"reengagement goldens directory missing: {_REENGAGEMENT_GOLDENS_DIR}"


def test_reengagement_goldens_count_is_4() -> None:
    """Exactly 4 reengagement golden YAMLs MUST exist (T-15 scope)."""
    goldens = sorted(_REENGAGEMENT_GOLDENS_DIR.glob("*.yaml"))
    assert len(goldens) == 4, f"expected 4 reengagement goldens, found {len(goldens)}: {[g.name for g in goldens]}"


def test_reengagement_goldens_required_fields() -> None:
    """Every reengagement golden MUST declare required schema fields."""
    required = {
        "golden_id",
        "vertical",
        "scenario",
        "persona",
        "input_conversation",
        "expected_tools_trajectory",
        "expected_voice_fidelity_score",
        "expected_medical_guardrails",
        "expected_channel_guards",
        "expected_outcome",
    }
    errors: list[str] = []
    for path in sorted(_REENGAGEMENT_GOLDENS_DIR.glob("*.yaml")):
        golden = _load_yaml(path)
        missing = required - set(golden.keys())
        if missing:
            errors.append(f"{path.name}: missing keys {sorted(missing)}")
    assert not errors, "schema violations:\n" + "\n".join(f"  {e}" for e in errors)


def test_reengagement_goldens_persona_references_exist() -> None:
    """Every reengagement golden.persona MUST point to existing personas file."""
    errors: list[str] = []
    for path in sorted(_REENGAGEMENT_GOLDENS_DIR.glob("*.yaml")):
        golden = _load_yaml(path)
        persona_filename = golden.get("persona")
        if not persona_filename:
            errors.append(f"{path.name}: missing 'persona' field")
            continue
        # Check in eval personas dir
        eval_personas_dir = _REENGAGEMENT_GOLDENS_DIR.parent.parent / "personas"
        persona_path = eval_personas_dir / persona_filename
        if not persona_path.is_file():
            errors.append(f"{path.name}: persona '{persona_filename}' not found at {persona_path}")
    assert not errors, "persona references broken:\n" + "\n".join(f"  {e}" for e in errors)


def test_reengagement_voice_fidelity_threshold_cement() -> None:
    """Cement: voice_fidelity_min = 0.85 per design § 2.8 + 04-validators.yaml."""
    assert VOICE_FIDELITY_MIN == 0.85


# ─────────────────────────────────────────────────────────────────────────────
# Engine grader importable
# ─────────────────────────────────────────────────────────────────────────────


def test_engine_grader_importable_for_reengagement() -> None:
    """ANTI-DUPLICATION §0: engine grader is the only voice fidelity grader."""
    assert grade_response is not None
    assert GraderRubric is not None
    assert GraderResult is not None


# ─────────────────────────────────────────────────────────────────────────────
# PHI invariant — NO real PHI in golden files
# ─────────────────────────────────────────────────────────────────────────────


def test_reengagement_goldens_no_phi_in_assistant_responses() -> None:
    """HIPAA-lite: NO real PHI patterns in golden assistant responses.

    Goldens use [PATIENT_ID] / [PATIENT_PHONE] placeholders, never real values.
    """
    errors: list[str] = []
    for path in sorted(_REENGAGEMENT_GOLDENS_DIR.glob("*.yaml")):
        golden = _load_yaml(path)
        assistant_text = _collect_assistant_text(golden)
        leaks = _PHI_LEAK_PATTERNS.findall(assistant_text)
        if leaks:
            errors.append(f"{path.name}: PHI leak detected in assistant response: {leaks}")
    assert not errors, "PHI leak violations:\n" + "\n".join(f"  {e}" for e in errors)


# ─────────────────────────────────────────────────────────────────────────────
# Tool trajectory invariants
# ─────────────────────────────────────────────────────────────────────────────


def test_happy_goldens_have_send_proactive_tool() -> None:
    """3 happy reengagement goldens MUST include send_proactive_reengagement in trajectory."""
    happy_goldens = [name for name in ["happy_multi_session.yaml", "happy_follow_up.yaml", "happy_maintenance.yaml"]]
    errors: list[str] = []
    for golden_name in happy_goldens:
        path = _REENGAGEMENT_GOLDENS_DIR / golden_name
        assert path.is_file(), f"golden file missing: {golden_name}"
        golden = _load_yaml(path)
        trajectory = golden.get("expected_tools_trajectory", [])
        tool_names = [t.get("tool") for t in trajectory]
        if "send_proactive_reengagement" not in tool_names:
            errors.append(f"{golden_name}: expected 'send_proactive_reengagement' in trajectory, got {tool_names}")
    assert not errors, "tool trajectory violations:\n" + "\n".join(f"  {e}" for e in errors)


def test_absence_optin_guard_has_empty_tool_trajectory() -> None:
    """absence_optin_guard golden MUST have EMPTY tools trajectory (NO send attempted)."""
    path = _REENGAGEMENT_GOLDENS_DIR / "absence_optin_guard.yaml"
    assert path.is_file(), "absence_optin_guard.yaml golden missing"
    golden = _load_yaml(path)
    trajectory = golden.get("expected_tools_trajectory", [])
    assert trajectory == [], f"absence_optin_guard MUST have empty tools trajectory, got: {trajectory}"


# ─────────────────────────────────────────────────────────────────────────────
# Voice fidelity grader smoke — engine grader consume
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "golden_name,persona_yaml_name",
    [
        ("happy_multi_session.yaml", "warm_close_dental.yaml"),
        ("happy_follow_up.yaml", "warm_close_dental.yaml"),
        ("happy_maintenance.yaml", "warm_close_dental.yaml"),
        ("absence_optin_guard.yaml", "warm_close_dental.yaml"),
    ],
    ids=["multi_session", "follow_up", "maintenance", "optin_guard"],
)
def test_reengagement_voice_fidelity_grader_smoke(
    golden_name: str,
    persona_yaml_name: str,
) -> None:
    """Engine grader smoke for each reengagement golden.

    Validates:
    1. GraderResult is the correct type (no crash — engine available).
    2. banned_vocab_absence=True (Adrián reengagement response has no forbidden phrases).
    3. lexical_alignment ≥ 0 (non-negative, engine accepted the rubric).
    4. All GraderResult fields present and within valid ranges.

    Note: judge_skipped=True expected in CI (no API key). judge_skipped=False
    only in environments with Anthropic API key + RUN_LLM_JUDGE=1.
    Either way, result shape MUST be valid.
    """
    golden_path = _REENGAGEMENT_GOLDENS_DIR / golden_name
    persona_voice_path = _PERSONAS_VOICE_DIR / persona_yaml_name
    assert golden_path.is_file(), f"golden file missing: {golden_name}"
    assert persona_voice_path.is_file(), f"persona voice file missing: {persona_yaml_name}"

    golden = _load_yaml(golden_path)
    persona = _load_yaml(persona_voice_path)
    assistant_text = _collect_assistant_text(golden)

    # Reengagement prompt context (Adrián receiving system trigger)
    system_turn = next(
        (t["content"] for t in golden.get("input_conversation", []) if t.get("role") == "system"),
        "Adrián recibe aviso de re-engagement y actúa.",
    )

    rubric = _build_rubric_from_persona(persona, prompt=system_turn, response=assistant_text)
    result = grade_response(rubric)

    # Shape invariants (always — regardless of judge_skipped)
    assert isinstance(result, GraderResult), f"{golden_name}: grade_response returned non-GraderResult type"
    assert isinstance(result.tone_match, int), f"{golden_name}: tone_match must be int, got {type(result.tone_match)}"
    assert 0.0 <= result.lexical_alignment <= 1.0, (
        f"{golden_name}: lexical_alignment={result.lexical_alignment:.3f} out of [0, 1]"
    )
    assert isinstance(result.banned_vocab_absence, bool), f"{golden_name}: banned_vocab_absence must be bool"
    assert 0.0 <= result.example_pair_similarity <= 1.0, f"{golden_name}: example_pair_similarity out of [0, 1]"
    assert isinstance(result.judge_skipped, bool), f"{golden_name}: judge_skipped must be bool"

    # Banned vocab invariant — Adrián reengagement responses MUST NOT trigger forbidden phrases
    # (warm_close_dental forbidden: "te diagnostico", "tenés gingivitis", etc.)
    # Reengagement confirmations are operational — no clinical content → banned_vocab MUST be absent.
    assert result.banned_vocab_absence is True, (
        f"{golden_name}: BANNED PHRASE DETECTED in Adrián response. "
        f"forbidden phrases in persona: {rubric.banned_phrases}. "
        f"assistant text: '{assistant_text[:200]}'"
    )


def test_absence_optin_guard_response_mentions_optin_compliance() -> None:
    """absence_optin_guard: Adrián response MUST mention opt-out / compliance decision.

    Critical: when NO tool is invoked, Adrián's textual response MUST
    communicate the opt-out compliance decision clearly.
    """
    path = _REENGAGEMENT_GOLDENS_DIR / "absence_optin_guard.yaml"
    golden = _load_yaml(path)
    assistant_text = _collect_assistant_text(golden)

    assert _OPTIN_GUARD_EXPECTED_KEYWORDS.search(assistant_text), (
        f"absence_optin_guard: Adrián response MUST mention opt-out/compliance decision. "
        f"Expected one of: optó|baja|mensajes proactivos|no se enviará|respetamos|comunicaciones. "
        f"Got: '{assistant_text[:200]}'"
    )


def test_engine_grader_smoke_handles_missing_llm_gracefully_reengagement() -> None:
    """Engine grader returns valid GraderResult shape even without LLM (CI guard)."""
    persona = _load_yaml(_PERSONAS_VOICE_DIR / "warm_close_dental.yaml")
    response = (
        "Recordatorio proactivo enviado (patrón=multi_session, "
        "template=recordatorio_proxima_sesion, event_id=abc-123, sent_at=2026-05-20T14:30:00Z)."
    )
    rubric = _build_rubric_from_persona(persona, prompt="Adrián envía recordatorio re-engagement", response=response)
    result = grade_response(rubric)

    assert isinstance(result, GraderResult)
    assert isinstance(result.tone_match, int)
    assert 0.0 <= result.lexical_alignment <= 1.0
    assert isinstance(result.banned_vocab_absence, bool)
    assert 0.0 <= result.example_pair_similarity <= 1.0
    assert isinstance(result.judge_skipped, bool)
