# cap: compliance.compliance-hipaa-lite-audit
# story-origin: TBD
"""Vitalia compliance guardrail — ``medical_safety_no_diagnosis`` (EP-13 wire).

Story T-ag-tools-2 — R23 production_code=true.

Per .claude/rules/anti-duplication.md § Regla cardinal:
  Canonical impl lives at
  ``vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_safety_no_diagnosis.py``
  (Story 11 T-guards-1 cement). This module is a thin RE-EXPORT shim so the
  EP-13 wire in ``vitalia/backend/src/modules/vitalia/extensions.py`` can
  reference a ``compliance.``-scoped path per the architecture target
  layout (``03-arch-be.md § 10``).

NO logic duplication — all detection regex, classifier consultation,
result types, and audit log emission live in the canonical module.

The single new symbol declared here is :func:`guardrail_check_no_diagnosis`,
a sync callable adapter matching the SDK ``GuardrailDef.pre_send_check`` /
``pre_receive_check`` signature ``(msg: str, ctx: BrandContext) -> GuardrailResult``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from luana_core_extension_sdk import GuardrailResult

# Re-export canonical impl symbols for downstream sales_agent runtime consumers.
from src.modules.vitalia.agentic.guardrails.medical_safety_no_diagnosis import (
    FALLBACK_RESPONSE_TEMPLATE,
    InputGuardrailResult,
    OutputGuardrailResult,
    fires_input_regex,
    fires_output_regex,
    medical_safety_no_diagnosis_input_check,
    medical_safety_no_diagnosis_output_check,
    render_fallback_response,
)

if TYPE_CHECKING:
    from luana_core_extension_sdk import BrandContext

logger = structlog.get_logger(__name__)


def guardrail_check_no_diagnosis(msg: str, ctx: BrandContext) -> GuardrailResult:
    """Sync SDK-compatible guardrail check — detects diagnosis claims.

    Lightweight regex pass (no LLM, no DB). Used as the EP-13 ``pre_send_check``
    / ``pre_receive_check`` callable. Async + classifier fallback paths live
    in :func:`medical_safety_no_diagnosis_output_check` (canonical agentic
    module) — sales_agent runtime invokes those via the orchestrator pipeline,
    NOT through this EP-13 dispatch (different surface).

    Args:
        msg: Message text to check.
        ctx: Brand context (unused — kept for SDK contract).

    Returns:
        GuardrailResult(blocked=True, reason=...) if regex fires.
        GuardrailResult(blocked=False) otherwise.
    """
    del ctx  # SDK contract — context unused for regex pass
    fired = fires_output_regex(msg) or fires_input_regex(msg)
    if fired:
        logger.info(
            "vitalia.compliance.guardrail_check_no_diagnosis.regex_fired",
            msg_length=len(msg),
        )
        return GuardrailResult(
            blocked=True,
            reason="medical_safety_no_diagnosis regex fired — diagnosis claim detected",
        )
    return GuardrailResult(blocked=False)


__all__ = [
    "FALLBACK_RESPONSE_TEMPLATE",
    "InputGuardrailResult",
    "OutputGuardrailResult",
    "fires_input_regex",
    "fires_output_regex",
    "guardrail_check_no_diagnosis",
    "medical_safety_no_diagnosis_input_check",
    "medical_safety_no_diagnosis_output_check",
    "render_fallback_response",
]


def _silence_any() -> Any:  # noqa: ANN401
    """No-op suppress unused-import lint."""
    return None
