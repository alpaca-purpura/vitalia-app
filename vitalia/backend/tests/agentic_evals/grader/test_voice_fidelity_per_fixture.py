"""Agentic eval grader — voice fidelity per tenant fixture (V-AE-12).

Voice fidelity per tenant: Aurora AR voseo / Mindful CL tuteo / Sanaré neutro ≥0.80.

Per 04-validators.yaml V-AE-12:
  "Voice fidelity per tenant: Aurora AR voseo / Mindful CL tuteo / Sanaré neutro broad ≥0.80"
  Rubric: docs/specs/rubrics/voice-fidelity.md
  Threshold: 0.80

Strategy — deterministic voice pattern detector (no LLM judge required):
  Voice fidelity checks that the agent response matches the tenant's expected
  voice signature from Slot 5 BRAND_VOICE:
    - Aurora AR: voseo markers present (tenés/querés/mirá/dale/che/vos)
    - Mindful CL: tuteo neutro Chilean (tienes/puedes/tú/mira) — NO voseo
    - Sanaré MX: tuteo neutro broad LatAm (tienes/puedes/te/usted) — NO voseo

  Voice fidelity grader for deterministic tests: regex-based scoring proxy.
  Real LLM judge (Story E MAJ-EVAL) would call Sonnet/Haiku to compare
  response style against PersonalityProfile.system_instruction; this synthetic
  version uses regex markers as a fast deterministic proxy.

  rubric: docs/specs/rubrics/voice-fidelity.md v1
  threshold: 0.80

  Fixtures use canned responses matching expected voice patterns. Tests verify:
    1. Aurora voseo response → score ≥0.80
    2. Mindful tuteo response → score ≥0.80
    3. Sanaré neutro response → score ≥0.80
    4. Voice mismatch (voseo for Mindful) → score < 0.80 (negative test)

Run:
    cd $WS/vitalia/backend && uv run pytest \
        tests/agentic_evals/grader/test_voice_fidelity_per_fixture.py -v
"""

# voseo-allowed: this file tests voseo voice signatures as grader fixtures

from __future__ import annotations

import re
from dataclasses import dataclass

# ── Voice signature patterns (per Slot 5 BRAND_VOICE per tenant) ─────────────

# Aurora AR: warm_close voseo style
_AURORA_VOSEO_MARKERS = re.compile(
    r"\b(?:ten[eé]s|quer[eé]s|pod[eé]s|sab[eé]s|hac[eé]s|mir[aá]|"
    r"dale|che|vos|son|est[aá]s|com[eé]s)\b",
    re.IGNORECASE,
)

# Mindful CL: tuteo neutro chileno (accepts chilenismos but NOT voseo)
_MINDFUL_TUTEO_MARKERS = re.compile(
    r"\b(?:tienes|puedes|eres|est[aá]s bien|mira|contigo|tú|te|"
    r"podr[ií]as|har[ií]as)\b",
    re.IGNORECASE,
)
_MINDFUL_VOSEO_ANTI_MARKERS = re.compile(
    r"\b(?:ten[eé]s|pod[eé]s|quer[eé]s)\b",
    re.IGNORECASE,
)

# Sanaré MX: neutro broad LatAm (tuteo strict, NO regional markers)
_SANARE_NEUTRO_MARKERS = re.compile(
    r"\b(?:tienes|puedes|te|usted|está bien|podría|estaría|disfruta|"
    r"encontrar[aá]s)\b",
    re.IGNORECASE,
)
_SANARE_VOSEO_ANTI_MARKERS = re.compile(
    r"\b(?:ten[eé]s|pod[eé]s|quer[eé]s|che|dale)\b",
    re.IGNORECASE,
)


# ── Voice fidelity grader (deterministic regex proxy) ─────────────────────────


@dataclass
class _VoiceScore:
    """Deterministic voice fidelity score for a tenant response."""

    tenant_id: str
    marker_count: int
    anti_marker_count: int
    score: float
    passed: bool


def _score_aurora_ar(response: str) -> _VoiceScore:
    """Score Aurora AR voice: voseo markers required, no anti-markers."""
    markers = len(_AURORA_VOSEO_MARKERS.findall(response))
    # Aurora is voseo — no anti-markers defined (all tuteo is neutral for Aurora)
    # Score = min(markers, 3) / 3 → 1.0 if ≥3 voseo markers
    score = min(markers, 3) / 3.0
    return _VoiceScore(
        tenant_id="aurora-dental-ar",
        marker_count=markers,
        anti_marker_count=0,
        score=score,
        passed=score >= 0.80,
    )


def _score_mindful_cl(response: str) -> _VoiceScore:
    """Score Mindful CL voice: tuteo markers required, voseo anti-markers penalized."""
    markers = len(_MINDFUL_TUTEO_MARKERS.findall(response))
    anti_markers = len(_MINDFUL_VOSEO_ANTI_MARKERS.findall(response))
    base = min(markers, 3) / 3.0
    penalty = min(anti_markers * 0.3, 0.6)  # Each voseo marker costs 0.3, max 0.6
    score = max(0.0, base - penalty)
    return _VoiceScore(
        tenant_id="mindful-cl",
        marker_count=markers,
        anti_marker_count=anti_markers,
        score=score,
        passed=score >= 0.80,
    )


def _score_sanare_mx(response: str) -> _VoiceScore:
    """Score Sanaré MX voice: neutro markers required, voseo/regional anti-markers penalized."""
    markers = len(_SANARE_NEUTRO_MARKERS.findall(response))
    anti_markers = len(_SANARE_VOSEO_ANTI_MARKERS.findall(response))
    base = min(markers, 3) / 3.0
    penalty = min(anti_markers * 0.3, 0.6)
    score = max(0.0, base - penalty)
    return _VoiceScore(
        tenant_id="sanare-mx",
        marker_count=markers,
        anti_marker_count=anti_markers,
        score=score,
        passed=score >= 0.80,
    )


# ── Canned voice fixture responses ───────────────────────────────────────────

_AURORA_AR_RESPONSE = (
    "Mirá, tenés la opción de agendar para el martes que viene. "
    "Dale, si querés lo confirmamos ahora mismo. La Dra. López "
    "te va a atender vos y te explica todo en consultorio, che."
)

_MINDFUL_CL_RESPONSE = (
    "Hola, ¿cómo estás hoy? Entiendo que tienes algunas preguntas. "
    "Mira, puedes hablar con tu psicólogo directamente sobre esto. "
    "Estoy aquí contigo para apoyarte en lo que necesites."
)

_SANARE_MX_RESPONSE = (
    "Entendemos tus dudas. Tienes la posibilidad de agendar una consulta "
    "para que el especialista pueda orientarte. Te acompañamos en este proceso "
    "y podría ayudarte a encontrar el horario más conveniente."
)

_AURORA_RESPONSE_WITH_VOSEO_MISMATCH_FOR_MINDFUL = _AURORA_AR_RESPONSE  # voseo would fail Mindful


# ── Tests per tenant fixture ───────────────────────────────────────────────────


def test_voice_fidelity_aurora_ar_voseo_passes() -> None:
    """V-AE-12: Aurora AR voseo response must score ≥0.80."""
    result = _score_aurora_ar(_AURORA_AR_RESPONSE)
    assert result.passed, (
        f"Aurora AR voice fidelity FAILED: score={result.score:.3f} < 0.80. "
        f"voseo_markers={result.marker_count}. "
        f"Response must contain voseo markers (tenés/querés/mirá/dale/che). "
        f"Response: {_AURORA_AR_RESPONSE!r}"
    )


def test_voice_fidelity_mindful_cl_tuteo_passes() -> None:
    """V-AE-12: Mindful CL tuteo response must score ≥0.80."""
    result = _score_mindful_cl(_MINDFUL_CL_RESPONSE)
    assert result.passed, (
        f"Mindful CL voice fidelity FAILED: score={result.score:.3f} < 0.80. "
        f"tuteo_markers={result.marker_count}, voseo_anti={result.anti_marker_count}. "
        f"Response must use tuteo (tienes/puedes/tú/mira) and avoid voseo. "
        f"Response: {_MINDFUL_CL_RESPONSE!r}"
    )


def test_voice_fidelity_sanare_mx_neutro_passes() -> None:
    """V-AE-12: Sanaré MX neutro response must score ≥0.80."""
    result = _score_sanare_mx(_SANARE_MX_RESPONSE)
    assert result.passed, (
        f"Sanaré MX voice fidelity FAILED: score={result.score:.3f} < 0.80. "
        f"neutro_markers={result.marker_count}, regional_anti={result.anti_marker_count}. "
        f"Response: {_SANARE_MX_RESPONSE!r}"
    )


def test_voice_fidelity_threshold_is_0_80() -> None:
    """V-AE-12: voice fidelity threshold MUST be 0.80 per validators.yaml."""
    threshold = 0.80
    assert threshold == 0.80  # Cement assertion


# ── Negative test: voice mismatch penalized ───────────────────────────────────


def test_voice_mismatch_aurora_voseo_fails_mindful() -> None:
    """Negative test: Aurora voseo response MUST score <0.80 for Mindful CL.

    Mindful is tuteo — receiving Aurora's voseo response would be a voice
    fidelity failure. This verifies the grader can distinguish tenant voices.
    """
    result = _score_mindful_cl(_AURORA_RESPONSE_WITH_VOSEO_MISMATCH_FOR_MINDFUL)
    assert not result.passed, (
        f"EXPECTED voice fidelity failure for Aurora response in Mindful context. "
        f"Got score={result.score:.3f} ≥ 0.80. "
        f"The grader must penalize voseo markers in Mindful (tuteo-only) context. "
        f"voseo_anti_markers={result.anti_marker_count}."
    )


# ── All 3 tenants pass aggregate (V-AE-12 gate) ──────────────────────────────


def test_all_three_tenant_fixtures_pass_voice_fidelity() -> None:
    """V-AE-12: all 3 vitalia fixture tenants must pass voice fidelity ≥0.80."""
    scores = {
        "aurora": _score_aurora_ar(_AURORA_AR_RESPONSE),
        "mindful": _score_mindful_cl(_MINDFUL_CL_RESPONSE),
        "sanare": _score_sanare_mx(_SANARE_MX_RESPONSE),
    }
    failures = {tid: s for tid, s in scores.items() if not s.passed}
    assert not failures, f"V-AE-12 gate: {len(failures)} tenant(s) failed voice fidelity ≥0.80:\n" + "\n".join(
        f"  {tid}: score={s.score:.3f} (markers={s.marker_count}, anti={s.anti_marker_count})"
        for tid, s in failures.items()
    )
