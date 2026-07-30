# cap: compliance.compliance-hipaa-lite-audit
# story-origin: TBD
"""Vitalia compliance guardrail — ``medical_disclaimer_required`` (NEW Slice 1).

Story T-ag-tools-2 — R23 production_code=true. Opus 4.7 EXCLUSIVE.

Per 03-arch-agentic.md § 10 + 03-arch.md § 3.7 + 02-design-agentic.md § 1.7 (slot 4
required footers):
  "If user mentions a medical condition → append:
   'Esta información es de referencia general. Consultá con tu doctor para
    diagnóstico personalizado.'"

This guardrail is a ``rewrite`` mode guard (mode='rewrite' in EP-13):
the LLM response is augmented (not blocked) with the disclaimer footer
when medical information terms are present and the footer is missing.

Detection:
  - Regex match on medical info trigger terms (symptoms / treatments /
    procedures / conditions / medications mentioned without explicit
    "consultá con tu doctor" already present).
  - If response already contains a disclaimer marker (regex on
    canonical footer phrase), guardrail no-ops (idempotent — never
    appends twice).

Anti-duplication audit (Step 0 GATE):
  - No engine equivalent — vertical-medical specific NEW Slice 1.
  - Uses ``GuardrailResult.replacement_text`` field (SDK contract) to
    deliver the augmented message back to the orchestrator.
  - Detection regex append-only ratchet — adding terms increases coverage,
    removing requires explicit safety review.

Cost: $0 (pure regex). Latency: <1ms.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

import structlog
from luana_core_extension_sdk import GuardrailResult

if TYPE_CHECKING:
    from luana_core_extension_sdk import BrandContext

logger = structlog.get_logger(__name__)


# ── Configuration cement (exported for tests + ratchet) ─────────────────

#: Canonical disclaimer footer (Spanish neutral; tenant voice respects this
#: as a literal append — voseo variants of "consultá" are intentionally
#: NOT exhaustive here, the regex below detects any equivalent).
DISCLAIMER_FOOTER: Final[str] = (
    "Esta información es de referencia general. Consulta con tu doctor para diagnóstico personalizado."
)

#: Medical info trigger regex — append-only catalog.
#: Detects sentences that mention conditions, symptoms, treatments,
#: procedures, or medication names without surrounding "consultá con tu
#: doctor" already present (idempotent guard below).
_MEDICAL_TRIGGER_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:"
    r"s[ií]ntomas?|dolor(?:es)?|fiebre|tos|n[aá]usea|v[oó]mito|mareo|"
    r"tratamiento(?:s)?|procedimiento(?:s)?|"
    r"diagn[oó]stico(?:s)?|"
    r"medicaci[oó]n|medicamento(?:s)?|"
    r"condici[oó]n(?:es)?|enfermedad(?:es)?|"
    r"presi[oó]n|colesterol|glucosa|diabetes|hipertensi[oó]n"
    r")\b",
    re.IGNORECASE,
)

#: Existing disclaimer regex — covers tuteo and voseo variants of "consulta/é".
_EXISTING_DISCLAIMER_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(?:consulta(?:r)?|consult[aá])(?:\s+con)?\s+(?:tu|el|al|un)?\s*(?:doctor|médic[oa]|profesional)\b",
    re.IGNORECASE,
)


# ── Pure helpers ────────────────────────────────────────────────────────


def has_medical_trigger(message: str) -> bool:
    """Return True iff the message mentions medical info trigger terms."""
    return _MEDICAL_TRIGGER_RE.search(message) is not None


def already_has_disclaimer(message: str) -> bool:
    """Return True iff the message already contains a disclaimer footer.

    Conservative match — accepts any "consultá con tu doctor" / "consulta con
    tu médico" variant. Tenant voice variations preserved (no normalization).
    """
    return _EXISTING_DISCLAIMER_RE.search(message) is not None


def append_disclaimer(message: str) -> str:
    """Return message with disclaimer footer appended (separated by blank line)."""
    if not message.endswith(("\n", " ")):
        return f"{message}\n\n{DISCLAIMER_FOOTER}"
    return f"{message}\n{DISCLAIMER_FOOTER}"


# ── SDK-compatible callable ─────────────────────────────────────────────


def guardrail_check_disclaimer_required(msg: str, ctx: BrandContext) -> GuardrailResult:
    """Sync SDK-compatible guardrail — rewrite mode (append disclaimer when needed).

    Per EP-13 contract with mode='rewrite':
      - If guardrail returns ``blocked=False`` AND ``rewritten`` is set,
        orchestrator uses ``rewritten`` instead of original ``msg``.
      - If ``blocked=True``, orchestrator drops the message (NOT this guard's case).
      - If ``rewritten=None``, orchestrator passes through original.

    Args:
        msg: Outbound message (typically LLM response).
        ctx: Brand context (unused — kept for SDK contract).

    Returns:
        GuardrailResult with:
          - ``blocked=False`` always (rewrite mode, never blocks)
          - ``rewritten=msg+disclaimer`` when trigger fires + no existing
            disclaimer
          - ``rewritten=None`` when no augmentation needed (idempotent)
    """
    del ctx

    if not has_medical_trigger(msg):
        return GuardrailResult(blocked=False)

    if already_has_disclaimer(msg):
        return GuardrailResult(blocked=False)

    augmented = append_disclaimer(msg)
    logger.info(
        "vitalia.compliance.guardrail_check_disclaimer_required.appended",
        original_length=len(msg),
        augmented_length=len(augmented),
    )
    return GuardrailResult(
        blocked=False,
        rewritten=augmented,
        reason="medical_disclaimer_required — appended generic disclaimer footer",
    )


__all__ = [
    "DISCLAIMER_FOOTER",
    "already_has_disclaimer",
    "append_disclaimer",
    "guardrail_check_disclaimer_required",
    "has_medical_trigger",
]
