"""Architecture fitness — A1: Slot 4 MEDICAL_SAFETY_RAILS contains required markers.

Per Story 11 T-prompts-1 acceptance criterion A1:
  Slot 4 contains sandbox markers <<TRANSCRIPT_BEGIN>> + <<TRANSCRIPT_END>>
  + ASÍ HABLAS / ASÍ NO blocks (medical safety overlay).

Spec sources:
  * 02-design-agentic.md § 10.1 SLOT 4 layout + § 11.3 medical safety overlay
  * 03-arch-agentic.md § 8.1 SLOT 4 cacheable + § 9.2 sandbox markers DQ2
  * 06-tickets.yaml::T-prompts-1 acceptance A1

Pure file inspection — no LLM call, no Postgres, no Anthropic SDK required.
Validates the literal MEDICAL_SAFETY_RAILS template content for the markers
that subsequent rendering MUST preserve verbatim. If a future ticket overrides
or rewrites the slot, this test cements the contract.
"""

from __future__ import annotations

import pytest

from src.modules.vitalia.agentic.prompts.compose import (
    load_slot_4_medical_safety_rails,
)

# ─────────────────────────────────────────────────────────────────────────────
# A1 — sandbox markers DQ2 (defense vs prompt-injection)
# ─────────────────────────────────────────────────────────────────────────────


def test_slot_4_contains_transcript_begin_marker() -> None:
    """A1: Slot 4 contains literal `<<TRANSCRIPT_BEGIN>>` marker."""
    slot_4 = load_slot_4_medical_safety_rails()
    assert "<<TRANSCRIPT_BEGIN>>" in slot_4, (
        "Slot 4 MUST include literal <<TRANSCRIPT_BEGIN>> sandbox marker per "
        "03-arch-agentic § 9.2 prompt-injection defense (DQ2)."
    )


def test_slot_4_contains_transcript_end_marker() -> None:
    """A1: Slot 4 contains literal `<<TRANSCRIPT_END>>` marker."""
    slot_4 = load_slot_4_medical_safety_rails()
    assert "<<TRANSCRIPT_END>>" in slot_4, (
        "Slot 4 MUST include literal <<TRANSCRIPT_END>> sandbox marker per "
        "03-arch-agentic § 9.2 prompt-injection defense (DQ2)."
    )


def test_slot_4_sandbox_markers_in_correct_order() -> None:
    """A1: <<TRANSCRIPT_BEGIN>> precedes <<TRANSCRIPT_END>> (semantic order)."""
    slot_4 = load_slot_4_medical_safety_rails()
    begin_idx = slot_4.find("<<TRANSCRIPT_BEGIN>>")
    end_idx = slot_4.find("<<TRANSCRIPT_END>>")
    assert begin_idx >= 0 and end_idx >= 0, "both markers must be present"
    assert begin_idx < end_idx, (
        "<<TRANSCRIPT_BEGIN>> must precede <<TRANSCRIPT_END>> for sandbox "
        "semantics to be coherent (model treats anything outside as "
        "potentially adversarial)."
    )


def test_slot_4_sandbox_explanation_mentions_injection_defense() -> None:
    """A1: Slot 4 explains WHY markers exist (anti-injection rationale)."""
    slot_4 = load_slot_4_medical_safety_rails()
    text_lower = slot_4.lower()
    # Must mention either "injection" or "adversarial" so model understands
    # the markers' security purpose (per spec § 9.2 + DQ2 + § 8.4 creep guard).
    has_rationale = "injection" in text_lower or "adversarial" in text_lower
    assert has_rationale, (
        "Slot 4 MUST explicitly mention 'injection' or 'adversarial' so the "
        "model understands sandbox markers are a defense, not decoration."
    )


# ─────────────────────────────────────────────────────────────────────────────
# A1 — ASÍ HABLAS / ASÍ NO bullet sections present
# ─────────────────────────────────────────────────────────────────────────────


def test_slot_4_contains_asi_hablas_section() -> None:
    """A1: Slot 4 contains literal `ASÍ HABLAS` heading (medical safety bullets)."""
    slot_4 = load_slot_4_medical_safety_rails()
    assert "ASÍ HABLAS" in slot_4, (
        "Slot 4 MUST include 'ASÍ HABLAS' section header per 02-design § 11.3 "
        "medical safety overlay structure (anchored to PersonalityCompiler v2 "
        "pattern from sales-agent-brand-voice.md SSoT)."
    )


def test_slot_4_contains_asi_no_section() -> None:
    """A1: Slot 4 contains literal `ASÍ NO` heading (medical safety prohibitions)."""
    slot_4 = load_slot_4_medical_safety_rails()
    assert "ASÍ NO" in slot_4, (
        "Slot 4 MUST include 'ASÍ NO' section header per 02-design § 11.3 "
        "medical safety overlay structure (anchored to PersonalityCompiler v2 "
        "pattern from sales-agent-brand-voice.md SSoT)."
    )


def test_slot_4_asi_hablas_precedes_asi_no() -> None:
    """A1: ASÍ HABLAS (DOs) precedes ASÍ NO (DON'Ts) — pedagogical order."""
    slot_4 = load_slot_4_medical_safety_rails()
    hablas_idx = slot_4.find("ASÍ HABLAS")
    no_idx = slot_4.find("ASÍ NO")
    assert hablas_idx >= 0 and no_idx >= 0, "both sections must be present"
    assert hablas_idx < no_idx, (
        "ASÍ HABLAS must precede ASÍ NO — establishing the affirmative pattern "
        "BEFORE prohibitions is the PersonalityCompiler v2 cement convention."
    )


# ─────────────────────────────────────────────────────────────────────────────
# A1 — medical safety prohibitions verbatim (production-critical bar)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "prohibition_keyword",
    [
        "diagnóstico",  # NO diagnosis
        "recetar",  # NO prescription / "recetar" verb
        "medicación",  # NO medication recommendation
        "doctor",  # NO contradicting doctor
    ],
)
def test_slot_4_mentions_critical_prohibition(prohibition_keyword: str) -> None:
    """A1: Slot 4 explicitly mentions each safety prohibition keyword.

    Per 02-design § 11.3 + 03-arch § 9.2: the 4 production-critical safety
    rails (NO diagnosis / NO prescription / NO medication change / NO contradict
    doctor) MUST be lexically present in the cached overlay so the model has
    the literal Spanish words available without depending on Slot 5 voice.
    """
    slot_4 = load_slot_4_medical_safety_rails()
    text_lower = slot_4.lower()
    assert prohibition_keyword in text_lower, (
        f"Slot 4 missing critical safety keyword '{prohibition_keyword}' — "
        f"vertical-medical fidelity bar requires lexical presence per "
        f"03-arch § 9.2."
    )


def test_slot_4_mentions_disclaimer_obligation() -> None:
    """A1: Slot 4 instructs model to insert disclaimer on sensitive responses."""
    slot_4 = load_slot_4_medical_safety_rails()
    text_lower = slot_4.lower()
    assert "disclaimer" in text_lower or "no reemplaza consulta" in text_lower, (
        "Slot 4 MUST instruct disclaimer insertion on symptom/procedure/medication "
        "responses per 02-design § 11.3 ASÍ HABLAS bullet 4."
    )
