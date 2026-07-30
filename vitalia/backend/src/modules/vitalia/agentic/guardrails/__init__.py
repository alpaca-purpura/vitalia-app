# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Vitalia agentic guardrails — registered via EP-13 in extensions.py.

Skeleton package created Story 11 T-extensions-1. Guardrail implementations land in:
  T-guards-1 → medical_safety_no_diagnosis  ← LANDED
  T-guards-2 → medical_safety_no_prescription  ← LANDED
  T-guards-3 → medical_disclaimer_required + prompt_injection_block_reuse  ← LANDED

Note on dataclass name reuse: ``InputGuardrailResult`` /
``OutputGuardrailResult`` / ``FALLBACK_RESPONSE_TEMPLATE`` /
``render_fallback_response`` exist as DISTINCT frozen dataclasses (and helper
template/function) in BOTH ``medical_safety_no_diagnosis`` and
``medical_safety_no_prescription`` modules — each with its own action /
directive vocabulary per spec § 17.1 vs § 17.2. To avoid silent name
collision at the package surface, those types are NOT re-exported from
``__init__.py``. Callers MUST import them by fully qualified module path:

    from src.modules.vitalia.agentic.guardrails.medical_safety_no_diagnosis import (
        InputGuardrailResult as DiagnosisInputResult,
    )
    from src.modules.vitalia.agentic.guardrails.medical_safety_no_prescription import (
        InputGuardrailResult as PrescriptionInputResult,
    )
"""

from src.modules.vitalia.agentic.guardrails.medical_disclaimer_required import (
    DISCLAIMER_TEXT,
    MEDICAL_TRIGGER_PATTERNS,
    apply_medical_disclaimer,
    medical_disclaimer_required_check,
    response_already_has_disclaimer,
    response_mentions_medical_topic,
)
from src.modules.vitalia.agentic.guardrails.medical_safety_no_diagnosis import (
    fires_input_regex,
    fires_output_regex,
    medical_safety_no_diagnosis_input_check,
    medical_safety_no_diagnosis_output_check,
)
from src.modules.vitalia.agentic.guardrails.medical_safety_no_prescription import (
    FORCED_DISCLAIMER_CHUNK_ID,
    MEDICATION_KEYWORDS,
    fires_input_keywords,
    medical_safety_no_prescription_input_check,
    medical_safety_no_prescription_output_check,
)
from src.modules.vitalia.agentic.guardrails.prompt_injection_block_reuse import (
    REFUSAL_RESPONSE,
    SANDBOX_MARKER_BEGIN,
    SANDBOX_MARKER_END,
    PromptInjectionResult,
    detect_prompt_injection,
    prompt_injection_block_check,
)

__all__ = [
    # medical_disclaimer_required (T-guards-3)
    "DISCLAIMER_TEXT",
    "MEDICAL_TRIGGER_PATTERNS",
    "apply_medical_disclaimer",
    "medical_disclaimer_required_check",
    "response_already_has_disclaimer",
    "response_mentions_medical_topic",
    # medical_safety_no_diagnosis (T-guards-1) — types omitted to avoid
    # collision with medical_safety_no_prescription duplicates (see docstring).
    "fires_input_regex",
    "fires_output_regex",
    "medical_safety_no_diagnosis_input_check",
    "medical_safety_no_diagnosis_output_check",
    # medical_safety_no_prescription (T-guards-2) — types omitted to avoid
    # collision with medical_safety_no_diagnosis duplicates (see docstring).
    "FORCED_DISCLAIMER_CHUNK_ID",
    "MEDICATION_KEYWORDS",
    "fires_input_keywords",
    "medical_safety_no_prescription_input_check",
    "medical_safety_no_prescription_output_check",
    # prompt_injection_block_reuse (T-guards-3)
    "PromptInjectionResult",
    "REFUSAL_RESPONSE",
    "SANDBOX_MARKER_BEGIN",
    "SANDBOX_MARKER_END",
    "detect_prompt_injection",
    "prompt_injection_block_check",
]
