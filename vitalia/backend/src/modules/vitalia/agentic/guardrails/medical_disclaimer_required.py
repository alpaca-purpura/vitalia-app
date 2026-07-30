# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Vitalia AGENTIC guardrail — `medical_disclaimer_required`.

R23: production_code=True AGENTIC code. Opus 4.7 EXCLUSIVE.
Story 11 T-guards-3.

Spec sources:
  * 02-design-agentic.md § 17.3 + § 17.5 OUTPUT pipeline step 8
  * 03-arch-agentic.md § 10.1 pipeline order + § 10.2 per-guard runtime
  * 06-tickets.yaml::T-guards-3 acceptance A1 (test_inserted_idempotent)
  * 05-guidelines.md § 1.10 R23 agentic patterns

Semantics — output decorator (post-LLM, pre-channel-send):
  1. Detect medical topic in response (procedure / medication / condition /
     dose / surgery / therapy).
  2. If detected AND disclaimer not already present → append canonical
     disclaimer suffix verbatim (Spanish neutro):
         "Esto no reemplaza consulta médica profesional"
  3. If disclaimer already present (verbatim or canonical phrase substring) →
     NO duplicate insertion (idempotent). Returns response unchanged.
  4. If no medical topic detected → no-op (returns response unchanged).
  5. Audit log `disclaimer_inserted` (severity info) ON insertion only.

Idempotency contract (production-critical for A1):
  * Second invocation on same already-decorated response MUST return identity
    (string equality), MUST NOT duplicate the canonical phrase, MUST NOT
    write a new audit_log entry.
  * Detection of "already present" uses substring match on canonical phrase
    "Esto no reemplaza consulta médica profesional" so LLM-composed responses
    that include the phrase mid-text also satisfy the idempotency check.

Best-effort observability (R23 + tessl__graceful-degradation):
  * `audit_log` is optional — guard works when omitted.
  * audit_log raising MUST NOT break the decorator. Insertion is the
    production-critical action; logging is observability.
  * try/except + structlog warning per `.claude/rules/copilot-observability.md`.

Anti-duplication audit (Step 0 GATE pre-write per .claude/rules/anti-duplication.md):
  * `medical_disclaimer_required` — NEW vertical-medical guard. Cross-codebase
    grep returned zero matches in `backend/src/` and `luana-platform/` aside
    from design docs + Slot 4 j2 + extension placeholder. No mirror risk.
  * `sanitize_payload` consumed from `luana_core_observability.recording.sanitization`
    — NEVER re-implemented.
  * `_AuditLogLike` Protocol mirrors the medical_audit_log surface used by
    `MedicalKBExtractor` (T-extractors-1) and `compliance_event_service`
    (T-be-3) — no duplication of repository class, only structural typing
    for decoupling.

Cost: $0 LLM (pure regex + string ops). Latency budget <1ms.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Protocol

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload

logger = structlog.get_logger(__name__)


# ── Configuration constants (cement — exported for tests + ratchet) ───────


#: Canonical disclaimer text per spec § 17.3 — verbatim Spanish neutro.
#: Must remain byte-equal to the phrase the grader rubric A5 looks up
#: (vertical-medical-fidelity rubric, Story 11 grader cement).
DISCLAIMER_TEXT: str = "Esto no reemplaza consulta médica profesional."

#: Canonical phrase for idempotency check — substring match against this
#: catches both ``DISCLAIMER_TEXT`` verbatim AND LLM-composed responses that
#: included the phrase inline mid-text. Both should NOT trigger re-insertion.
_CANONICAL_PHRASE: str = "Esto no reemplaza consulta médica profesional"

#: Suffix separator inserted between original response and disclaimer.
_DISCLAIMER_SEPARATOR: str = " "


#: Compiled regex catalog of medical-topic triggers per 02-design § 17.3.
#: Each pattern is case-insensitive. Append-only for ratchet — DO NOT remove
#: a pattern without bumping rubric version (spec § 17.3 cement).
MEDICAL_TRIGGER_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Procedures (dental, surgical, generic)
    re.compile(r"\bimplante\b", re.IGNORECASE),
    re.compile(r"\bcirug[ií]a\b", re.IGNORECASE),
    re.compile(r"\bprocedimiento\b", re.IGNORECASE),
    re.compile(r"\bextracci[oó]n\b", re.IGNORECASE),
    re.compile(r"\bendodoncia\b", re.IGNORECASE),
    # Therapy (psychology, psychiatry, physio)
    re.compile(r"\bterap[ií]a\b", re.IGNORECASE),
    re.compile(r"\btratamiento\b", re.IGNORECASE),
    re.compile(r"\bsesi[oó]n\s+(?:cl[ií]nica|terap[ée]utica|psicol[oó]gica)\b", re.IGNORECASE),
    # Medication
    re.compile(r"\bmedicaci[oó]n\b", re.IGNORECASE),
    re.compile(r"\bmedicamento\b", re.IGNORECASE),
    re.compile(r"\b(?:dosis|dosificaci[oó]n)\b", re.IGNORECASE),
    re.compile(r"\breceta\b", re.IGNORECASE),
    # Conditions
    re.compile(r"\bdiagn[oó]stico\b", re.IGNORECASE),
    re.compile(r"\bs[ií]ntoma(?:s)?\b", re.IGNORECASE),
)


# ── Audit log protocol (decouple from concrete repository) ────────────────


class _AuditLogLike(Protocol):
    """Minimal surface for medical audit_log writes.

    Mirrors `medical_audit_log_repository.MedicalAuditLogRepository.log`
    consumed by `MedicalKBExtractor` (T-extractors-1) and
    `compliance_event_service` (T-be-3). Structural typing — concrete
    implementations supply their own dispatch.
    """

    async def log(
        self,
        *,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID | None = None,
        event_type: str,
        payload: dict[str, Any],
    ) -> None: ...


# ── Pure helpers (unit-testable, no I/O) ──────────────────────────────────


def response_mentions_medical_topic(response: str) -> bool:
    """Return True iff response touches procedure / medication / condition.

    Per 02-design § 17.3 trigger patterns. Pure regex — no LLM, no DB.

    Append-only catalog of patterns; safety bar is "at least one match
    triggers disclaimer". False negatives (regex misses an emerging medical
    term) → caught downstream by output guard `medical_safety_no_diagnosis`
    + adversarial grader pass^5 ≥0.95 (V-AE-11).
    """
    return any(pattern.search(response) for pattern in MEDICAL_TRIGGER_PATTERNS)


def response_already_has_disclaimer(response: str) -> bool:
    """Return True iff response already contains the canonical disclaimer phrase.

    Idempotency guarantee: substring match on `_CANONICAL_PHRASE` covers both
    `DISCLAIMER_TEXT` verbatim AND LLM-composed responses that already wove
    the phrase into prose (e.g. "Esto no reemplaza consulta médica profesional
    con tu odontólogo").

    Pure string op — no regex, no normalization. The canonical phrase is a
    fixed cement string by spec § 17.3.
    """
    return _CANONICAL_PHRASE in response


def apply_medical_disclaimer(response: str) -> str:
    """Append disclaimer to response (idempotent, pure).

    Returns:
      - ``response`` unchanged if no medical topic detected (no-op)
      - ``response`` unchanged if disclaimer already present (idempotent)
      - ``response + separator + DISCLAIMER_TEXT`` otherwise

    Pure function — does NOT log audit events. Use
    `medical_disclaimer_required_check` for the side-effecting wrapper.
    """
    if not response_mentions_medical_topic(response):
        return response
    if response_already_has_disclaimer(response):
        return response
    return f"{response}{_DISCLAIMER_SEPARATOR}{DISCLAIMER_TEXT}"


# ── Side-effecting check (decorator with audit_log) ───────────────────────


async def medical_disclaimer_required_check(
    *,
    response: str,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID | None = None,
    audit_log: _AuditLogLike | None = None,
) -> str:
    """Output decorator — append disclaimer + audit.

    Per 02-design § 17.3 + § 17.5 OUTPUT pipeline step 8 (post-LLM,
    pre-channel-send).

    Parameters
    ----------
    response
        Raw LLM-generated response (post all output safety guards 6-7).
    tenant_id
        Required for audit_log + future multi-tenant disclaimer
        customization (currently disclaimer is brand-uniform).
    patient_id
        Optional — included in audit_log payload when known.
    audit_log
        Optional best-effort sink. Failures are swallowed + logged via
        structlog (per .claude/rules/copilot-observability.md). When omitted,
        the decorator silently skips logging (graceful degradation).

    Returns
    -------
    str
        Response with disclaimer appended (or unchanged when no-op /
        idempotent skip).

    Notes
    -----
    Idempotent — second invocation returns identical string. No retry / no
    backoff / no circuit breaker needed — pure local operation.

    Audit_log writes ONLY on fresh insertion. Idempotent skips and benign
    no-ops do NOT write to keep the audit table signal-rich.
    """
    decorated = apply_medical_disclaimer(response)

    # Insertion happened iff the decorated string differs from the original.
    if decorated == response:
        return response

    await _emit_audit_log(
        audit_log,
        tenant_id=tenant_id,
        patient_id=patient_id,
        original_length=len(response),
        decorated_length=len(decorated),
    )
    return decorated


# ── Best-effort audit_log emission (R23 + graceful-degradation) ───────────


async def _emit_audit_log(
    audit_log: _AuditLogLike | None,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID | None,
    original_length: int,
    decorated_length: int,
) -> None:
    """Best-effort audit log emission. NEVER breaks decorator turn.

    Per .claude/rules/copilot-observability.md + tessl__graceful-degradation
    rule 2 ("every external call needs a fallback"):
      - audit_log None → silent skip (graceful when not provisioned)
      - audit_log raises → swallow + structlog warning (no break)

    Sanitizes payload via `sanitize_payload` per anti-duplication.md +
    .tessl/RULES.md pii-sanitisation. The payload contains lengths + counts
    only (never the response text itself — that lives in trace_event with
    its own sanitization layer).
    """
    if audit_log is None:
        return

    try:
        payload = sanitize_payload(
            {
                "severity": "info",
                "guardrail": "medical_disclaimer_required",
                "action": "disclaimer_inserted",
                "original_length": original_length,
                "decorated_length": decorated_length,
                "disclaimer_text_length": len(DISCLAIMER_TEXT),
            }
        )
        await audit_log.log(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type="disclaimer_inserted",
            payload=payload,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "medical_disclaimer_required.audit_log_failed",
            exc=str(exc),
            tenant_id=str(tenant_id),
            patient_id=str(patient_id) if patient_id else None,
        )


__all__ = [
    "DISCLAIMER_TEXT",
    "MEDICAL_TRIGGER_PATTERNS",
    "apply_medical_disclaimer",
    "medical_disclaimer_required_check",
    "response_already_has_disclaimer",
    "response_mentions_medical_topic",
]
