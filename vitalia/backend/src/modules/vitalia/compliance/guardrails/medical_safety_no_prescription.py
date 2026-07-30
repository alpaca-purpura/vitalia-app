# cap: compliance.compliance-hipaa-lite-audit
# story-origin: TBD
"""Vitalia compliance guardrail — ``medical_safety_no_prescription`` (EP-13 wire).

Story T-ag-tools-2 — R23 production_code=true.

Per .claude/rules/anti-duplication.md § Regla cardinal:
  Canonical impl lives at
  ``vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_safety_no_prescription.py``
  (Story 11 T-guards-1 cement). This module is a thin RE-EXPORT shim so the
  EP-13 wire in ``vitalia/backend/src/modules/vitalia/extensions.py`` can
  reference a ``compliance.``-scoped path per the architecture target
  layout (``03-arch-be.md § 10``).

NO logic duplication.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from luana_core_extension_sdk import GuardrailResult

# Re-export canonical impl symbols.
from src.modules.vitalia.agentic.guardrails.medical_safety_no_prescription import (
    FALLBACK_RESPONSE_TEMPLATE,
    InputGuardrailResult,
    OutputGuardrailResult,
    fires_input_keywords,
    fires_output_regex,
    medical_safety_no_prescription_input_check,
    medical_safety_no_prescription_output_check,
    render_fallback_response,
)

if TYPE_CHECKING:
    from luana_core_extension_sdk import BrandContext

logger = structlog.get_logger(__name__)


def guardrail_check_no_prescription(msg: str, ctx: BrandContext) -> GuardrailResult:
    """Sync SDK-compatible guardrail check — detects prescription claims.

    Lightweight keyword + regex pass (no LLM). Used as EP-13 ``pre_send_check``
    / ``pre_receive_check``. Async classifier paths live in canonical agentic
    module.

    Args:
        msg: Message text to check.
        ctx: Brand context (unused — kept for SDK contract).

    Returns:
        GuardrailResult(blocked=True, reason=...) if keyword or regex fires.
        GuardrailResult(blocked=False) otherwise.
    """
    del ctx
    fired = fires_input_keywords(msg) or fires_output_regex(msg)
    if fired:
        logger.info(
            "vitalia.compliance.guardrail_check_no_prescription.regex_fired",
            msg_length=len(msg),
        )
        return GuardrailResult(
            blocked=True,
            reason="medical_safety_no_prescription fired — prescription/medication claim detected",
        )
    return GuardrailResult(blocked=False)


__all__ = [
    "FALLBACK_RESPONSE_TEMPLATE",
    "InputGuardrailResult",
    "OutputGuardrailResult",
    "fires_input_keywords",
    "fires_output_regex",
    "guardrail_check_no_prescription",
    "medical_safety_no_prescription_input_check",
    "medical_safety_no_prescription_output_check",
    "render_fallback_response",
]
