# cap: compliance.compliance-hipaa-lite-audit
# story-origin: TBD
"""Vitalia compliance guardrail — ``prompt_injection_block_reuse`` (NEW Slice 1).

Story T-ag-tools-2 — R23 production_code=true. Opus 4.7 EXCLUSIVE.

Per 03-arch-agentic.md § 10 + 03-arch.md § 3.7 + 02-design-agentic.md § 2.7
(error recovery — user prompt injection):
  Detects classic prompt-injection patterns ("ignora tus instrucciones",
  "forget previous", "system prompt", "reveal your tools", "act as
  developer", etc.) and signals the orchestrator to BLOCK the request.

Reuse strategy: regex catalog derived from the canonical Story E grader
adversarial patterns + extended with Spanish neutro variants commonly seen
in WhatsApp lead injection attempts.

Per .claude/rules/anti-duplication.md:
  - Engine has NO sales_agent-side prompt_injection callable (Story E grader
    operates on goldens, not runtime). This guardrail is NEW Slice 1.
  - Detection regex append-only — adding patterns broadens coverage, removing
    requires explicit safety review.
  - Future Slice 2 lift candidate to ``core/luana-core-compliance/`` once 2+
    brands consume same patterns.

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


# ── Injection pattern catalog (append-only) ─────────────────────────────


#: Regex catalog covering Spanish + English injection patterns.
#: Append-only ratchet — new patterns increase coverage, removal requires
#: explicit safety review with rubric version bump.
_INJECTION_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    # Spanish — "ignora/olvida tus instrucciones"
    re.compile(r"\b(?:ignora|olvida)\s+(?:tus|las?)\s+(?:instrucciones|reglas|sistema)\b", re.IGNORECASE),
    # English — "ignore/forget previous instructions"
    re.compile(r"\b(?:ignore|forget|disregard)\s+(?:previous|all|prior)\s+(?:instructions?|rules?)\b", re.IGNORECASE),
    # System prompt extraction
    re.compile(r"\b(?:reveal|show|print|display|repeat|dump)\s+(?:your|the)?\s*system\s+prompt\b", re.IGNORECASE),
    re.compile(
        r"\b(?:mostr[aá]|imprim[ií]|repet[ií]|revel[aá])\s+(?:el|tu)\s+(?:system|prompt|instrucciones)\b",
        re.IGNORECASE,
    ),
    # Role hijack — "act as developer / mode admin"
    re.compile(r"\bact\s+as\s+(?:a\s+)?(?:developer|admin|root|jailbreak)\b", re.IGNORECASE),
    re.compile(r"\b(?:actuá|actua|comportate)\s+como\s+(?:dev|administrador|jailbreak)\b", re.IGNORECASE),
    # DAN-style jailbreak
    re.compile(r"\bDAN\s+mode\b", re.IGNORECASE),
    re.compile(r"\bdo\s+anything\s+now\b", re.IGNORECASE),
    # Tool exfiltration (accepts "list all your tools", "list your tools", "list all tools", "show tools", etc.)
    re.compile(
        r"\b(?:list|show|reveal|enumerate|dump)\s+(?:all\s+)?(?:your\s+|the\s+)?tools?\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:list[aá]|most[rá])\s+(?:tus|las)\s+(?:tools?|herramientas)\b", re.IGNORECASE),
    # Cross-tenant attempts
    re.compile(r"\b(?:list|show|dump|enumerate)\s+(?:all|every)\s+(?:tenant|patient|user|paciente)s?\b", re.IGNORECASE),
    re.compile(r"\bdame\s+(?:todos\s+los\s+)?(?:pacientes|usuarios|tenants)\b", re.IGNORECASE),
    # Encoded payloads
    re.compile(r"\b(?:base64|hex|rot13)\s*[:=]", re.IGNORECASE),
)


def fires_injection_pattern(message: str) -> bool:
    """Return True iff message matches any injection pattern in the catalog.

    Pure regex — no LLM, no DB. Append-only catalog (safety ratchet).
    """
    return any(pattern.search(message) for pattern in _INJECTION_PATTERNS)


def matching_patterns(message: str) -> list[str]:
    """Return list of pattern source strings that matched (for audit log)."""
    matched: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(message):
            matched.append(pattern.pattern)
    return matched


# ── SDK-compatible callable ─────────────────────────────────────────────


def guardrail_check_prompt_injection(msg: str, ctx: BrandContext) -> GuardrailResult:
    """Sync SDK-compatible guardrail — block mode.

    Used as EP-13 ``pre_send_check`` (mode='block'):
      - If pattern fires → ``blocked=True``, orchestrator drops + emits
        safe Spanish refusal ("No entendí, ¿en qué te puedo ayudar con tu
        consulta?").

    Args:
        msg: Inbound or outbound message text.
        ctx: Brand context (unused — kept for SDK contract).

    Returns:
        GuardrailResult(blocked=True, reason=...) on pattern match.
        GuardrailResult(blocked=False) on clean message.
    """
    del ctx

    if fires_injection_pattern(msg):
        matched = matching_patterns(msg)
        logger.warning(
            "vitalia.compliance.guardrail_check_prompt_injection.fired",
            msg_length=len(msg),
            patterns=matched[:3],  # truncate for log brevity
        )
        return GuardrailResult(
            blocked=True,
            reason=f"prompt_injection_block_reuse fired — matched patterns: {matched[:3]!r}",
        )

    return GuardrailResult(blocked=False)


__all__ = [
    "fires_injection_pattern",
    "guardrail_check_prompt_injection",
    "matching_patterns",
]
