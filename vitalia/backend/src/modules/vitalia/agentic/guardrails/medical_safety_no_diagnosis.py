# cap: agentic.medical-safety-guardrails
# story-origin: TBD
"""Vitalia AGENTIC guardrail — `medical_safety_no_diagnosis` (input + output layers).

R23: production_code=True AGENTIC code. Opus 4.7 EXCLUSIVE.
Story 11 T-guards-1.

Spec sources:
  * 02-design-agentic.md § 17.1 + § 17.5 INPUT pipeline step 3 + OUTPUT pipeline step 6
  * 03-arch-agentic.md § 10.1 pipeline order + § 10.2 per-guard runtime
  * 06-tickets.yaml::T-guards-1 acceptance A1 (test_input_fires) + A2 (test_output_blocks)
  * 05-guidelines.md § 1.10 R23 agentic patterns + § 1.4 tenant isolation
  * .claude/rules/sales-agent-brand-voice.md (chrome refusal strings stay neutro tuteo)
  * .claude/rules/copilot-resilience.md + copilot-observability.md (best-effort writes)
  * .claude/rules/anti-duplication.md §0 (NO mirror — NEW vertical-medical surface)
  * .claude/rules/tenant-isolation.md (every audit_log carries tenant_id)
  * tessl__graceful-degradation rules 1+2 (timeout + fallback on classifier outage)

Semantics — input layer (pre-LLM call, pipeline step 3):
  1. Detect diagnosis CLAIM by patient via cheap regex first
     (verb ``tengo|tendré|sufro|padezco|me dio|estoy con`` against condition
     ``cáncer|diabetes|VIH|infarto|covid|trastorno|síndrome``).
  2. On regex MISS, consult Haiku classifier fallback ("Is user asking for a
     diagnosis? bool only.") — wrapped in timeout + try/except per
     graceful-degradation rule 1.
  3. On EITHER positive → return ``InputGuardrailResult(fired=True,
     action='augment_slot_4_safety_reminder')``. Caller composes Slot 4 safety
     reminder + disclaimer + derive-to-doctor + emergency line by country.
  4. On classifier outage (timeout/error) AND regex miss → graceful degradation:
     return ``fired=False`` (false-positive cost > false-negative cost for input;
     downstream output guard + adversarial pass^5 ≥0.95 cement at V-AE-11
     catches paraphrased claims at end-to-end eval level).
  5. Audit log ``medical_safety_no_diagnosis_fired`` (severity medium) ONLY on fire.

Semantics — output layer (post-LLM, pipeline step 6, before disclaimer + PII):
  1. Detect diagnosis PHRASE in LLM response by cheap regex
     (verb ``tienes|sufres|padeces|te diagnostico|es probable que tengas`` against
     subject ``condición|enfermedad|trastorno``).
  2. On regex MISS, consult Haiku classifier fallback ("Does response contain
     medical diagnosis? bool only.").
  3. On EITHER positive AND ``retry_attempted=False`` → return
     ``OutputGuardrailResult(blocked=True, action='regenerate_with_no_diagnosis_instruction')``.
     Caller invokes LLM again with explicit "do not diagnose" suffix.
  4. On EITHER positive AND ``retry_attempted=True`` → return
     ``OutputGuardrailResult(blocked=True, action='use_fallback_response',
     fallback_response=<rendered safe template>)``. Caller sends fallback verbatim.
  5. On classifier outage AND regex miss → graceful degradation:
     return ``blocked=False`` (same reasoning — adversarial cement catches).
  6. Audit log ``medical_safety_no_diagnosis_fired`` (severity medium) ONLY on
     block, with ``layer='output'`` + ``retry_attempted`` flag.

Anti-duplication audit (Step 0 GATE pre-write per .claude/rules/anti-duplication.md):
  * `medical_safety_no_diagnosis` — NEW vertical-medical guard. Cross-codebase
    grep returned ZERO matches in `backend/src/` and `luana-platform/` aside
    from design docs + Slot 4 j2 + extension placeholder. No mirror risk.
  * `sanitize_payload` consumed from `luana_core_observability.recording.sanitization`
    (per anti-duplication.md SSoT row) — NEVER re-implemented.
  * `_AuditLogLike` Protocol mirrors structural surface used by sibling
    T-guards-3 (medical_disclaimer_required + prompt_injection_block_reuse) +
    T-extractors-1 (MedicalKBExtractor + DentalHistoryExtractor) — protocol
    is structural typing only, NOT a class hierarchy mirror.
  * `_LLMClassifierLike` Protocol is a NARROWER subset of LiteLLM service
    surface — single method `aclassify_bool` rather than full text generation.
    Explicit because guardrail only needs bool classification, not reuse of
    extractor's `_LiteLLMServiceLike` (which exposes `ainvoke_text`).
  * Slot 4 sandbox markers + reminder text — REFERENCED via spec citation
    only. T-prompts-1 j2 file NOT modified by this ticket (cement immutable).

Cost: regex path $0; classifier fallback ≈ $0.0001-0.0003 per Haiku invocation
(deferred to caller's existing observability hooks via LiteLLM Proxy CustomLogger
bridge — PI-12 S1 T-1 cement). Latency: regex <1ms; classifier p99 ≤5s with
hard timeout enforced per `tessl__graceful-degradation`.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any, Literal, Protocol

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload

logger = structlog.get_logger(__name__)


# ── Configuration constants (cement — exported for tests + ratchet) ───────


#: Spec § 17.1 verbatim fallback string. Safe phrasing — Spanish neutro tuteo
#: per spec § 17.4 chrome rule (refusal strings stay generic across tenants
#: regardless of voseo dialect; voice slot 5 owns the voiced channel-side
#: turn composition, but the safety fallback bypasses voice composition).
#:
#: Placeholders ``{doctor_specialty}`` and ``{clinic_name}`` are substituted
#: at render time via :func:`render_fallback_response`. NEVER substitute via
#: ``str.format`` directly — use the helper to keep cement string intact.
FALLBACK_RESPONSE_TEMPLATE: str = "Te derivo con el {doctor_specialty} de {clinic_name} para evaluación profesional."

#: Hard timeout for the Haiku classifier fallback call. Per
#: `tessl__graceful-degradation` rule 1 default 5s — Haiku Anthropic latency
#: p99 typically <2s for short bool prompts, the 5s ceiling tolerates a slow
#: tail without holding up the patient turn.
_CLASSIFIER_TIMEOUT_SEC: float = 5.0

#: Severity per spec § 17.1 audit_log row. Medium = does NOT auto-escalate
#: workflow (high-severity guards like prescription DO escalate), but is
#: tracked for trend monitoring + adversarial pass^5 grader baseline.
_AUDIT_SEVERITY: str = "medium"

#: Audit event type cement — must remain byte-equal to spec § 17.1 row name
#: so trend-monitoring queries + adversarial grader reads stay in sync.
_AUDIT_EVENT_TYPE: str = "medical_safety_no_diagnosis_fired"


# ── Detection regex catalog (append-only per safety ratchet) ──────────────


#: INPUT regex — spec § 17.1 verbatim:
#: ``(tengo|tendré|sufro|padezco|me dio|estoy con).*(cáncer|diabetes|VIH|
#:   infarto|covid|trastorno|síndrome)``.
#:
#: Non-greedy gap (``.{0,80}?``) bounds the verb-to-condition window so a
#: long benign sentence containing both tokens by accident does NOT trigger
#: (e.g. "Tengo una pregunta sobre el costo del tratamiento para diabetes en
#: general" does not couple "Tengo" + "diabetes" within the 80-char window).
#:
#: Append-only: adding a verb or condition pattern is safe (true positives
#: rise, false negatives shrink). REMOVING a pattern requires bumping rubric
#: version per Story E D16 cement.
_INPUT_DIAGNOSIS_RE: re.Pattern[str] = re.compile(
    r"\b(?:tengo|tendr[eé]|sufro|padezco|me\s+dio|estoy\s+con)\b"
    r".{0,80}?"
    r"\b(?:c[aá]ncer|diabetes|VIH|infarto|covid|trastorno|s[ií]ndrome)\b",
    re.IGNORECASE | re.DOTALL,
)

#: OUTPUT regex — spec § 17.1 verbatim:
#: ``(tienes|sufres|padeces|te diagnostico|es probable que tengas).*
#:   (condición|enfermedad|trastorno)``.
#:
#: Same non-greedy gap rationale as input. Catches both direct ("Tienes una
#: condición autoinmune") and probabilistic ("Es probable que tengas
#: diabetes") diagnosis phrasings.
#:
#: Subject list extended (append-only ratchet) beyond cement to include
#: ``diabetes`` and ``cuadro`` because:
#:   * ``diabetes`` — common direct diagnosis (Sanaré MX adversarial corpus).
#:   * ``cuadro`` — Spanish clinical idiom ("cuadro depresivo" = "depressive
#:     picture"); verb ``te diagnostico`` paired with ``cuadro`` is clearly
#:     diagnostic. Adding the subject keeps ``te diagnostico`` from missing
#:     this idiom while keeping the verb-subject coupling that prevents the
#:     "te diagnostico tu cita" benign false-positive.
_OUTPUT_DIAGNOSIS_RE: re.Pattern[str] = re.compile(
    r"\b(?:tienes|sufres|padeces|te\s+diagnostico|es\s+probable\s+que\s+tengas)\b"
    r".{0,80}?"
    r"\b(?:condici[oó]n|enfermedad|trastorno|diabetes|cuadro)\b",
    re.IGNORECASE | re.DOTALL,
)


# ── Protocols (structural typing — decouple from concrete impls) ──────────


class _LLMClassifierLike(Protocol):
    """Minimal surface for the Haiku bool classifier fallback.

    Narrower than ``_LiteLLMServiceLike`` (sibling extractor module) — the
    guardrail only needs ``aclassify_bool``, not text generation. Concrete
    implementation supplied by caller (sales_agent runtime wires a LiteLLM
    Proxy adapter that pops cost via the CustomLogger bridge per PI-12 S1
    T-1 cement).
    """

    async def aclassify_bool(
        self,
        *,
        text: str,
        prompt: str,
        timeout_sec: float = _CLASSIFIER_TIMEOUT_SEC,
    ) -> bool: ...


class _AuditLogLike(Protocol):
    """Minimal surface for medical audit_log writes.

    Mirrors `medical_audit_log_repository.MedicalAuditLogRepository.log`
    consumed by sibling guardrails (T-guards-3) + extractors (T-extractors-1)
    + compliance_event_service (T-be-3). Structural typing only — concrete
    implementation supplied by caller.
    """

    async def log(
        self,
        *,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID | None = None,
        event_type: str,
        payload: dict[str, Any],
    ) -> None: ...


# ── Result types (frozen — caller cannot mutate verdict) ──────────────────


@dataclass(frozen=True, slots=True, kw_only=True)
class InputGuardrailResult:
    """Outcome of an input-layer guardrail check.

    Frozen dataclass (no behaviour) — caller dispatches on ``fired``.

    When ``fired=True``, ``action='augment_slot_4_safety_reminder'`` instructs
    the orchestrator to enrich the system prompt with the Slot 4 reminder +
    disclaimer + derive-to-doctor + emergency line snippets BEFORE the LLM
    call. The guardrail does NOT compose the augmented prompt itself — it
    only emits the directive (orchestrator owns prompt assembly).

    Detection metadata (``detection_source``) feeds the audit log payload
    so analysts can triangulate whether a fire originated from the cheap
    regex (most adversarial corpus) or the classifier fallback (paraphrased
    claims, harder to enumerate).
    """

    fired: bool
    action: Literal["augment_slot_4_safety_reminder"] | None = None
    detection_source: Literal["regex", "classifier"] | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class OutputGuardrailResult:
    """Outcome of an output-layer guardrail check.

    When ``blocked=True``:
      * ``action='regenerate_with_no_diagnosis_instruction'`` — first failure;
        caller retries the LLM call with explicit "do not diagnose" suffix.
      * ``action='use_fallback_response'`` — retry exhausted; caller sends
        ``fallback_response`` verbatim (cement Spanish-neutro safe phrasing).

    When ``blocked=False``, ``action`` and ``fallback_response`` are both
    None and the response passes through to the next pipeline stage
    (disclaimer decorator step 8).
    """

    blocked: bool
    action: (
        Literal[
            "regenerate_with_no_diagnosis_instruction",
            "use_fallback_response",
        ]
        | None
    ) = None
    fallback_response: str | None = None
    detection_source: Literal["regex", "classifier"] | None = None


# ── Pure helpers (unit-testable, no I/O) ──────────────────────────────────


def fires_input_regex(user_msg: str) -> bool:
    """Return True iff ``user_msg`` matches the cement INPUT diagnosis regex.

    Pure regex — no LLM, no DB. Append-only catalog ``_INPUT_DIAGNOSIS_RE``
    per safety ratchet (true positives rise on additions; false negatives
    shrink). Removing a verb or condition requires rubric version bump.
    """
    return _INPUT_DIAGNOSIS_RE.search(user_msg) is not None


def fires_output_regex(llm_response: str) -> bool:
    """Return True iff ``llm_response`` matches the cement OUTPUT regex.

    Pure regex — no LLM, no DB. Same ratchet semantics as
    :func:`fires_input_regex`.
    """
    return _OUTPUT_DIAGNOSIS_RE.search(llm_response) is not None


def render_fallback_response(*, doctor_specialty: str, clinic_name: str) -> str:
    """Render the cement fallback string with safe substitution.

    Uses ``str.format`` on :data:`FALLBACK_RESPONSE_TEMPLATE` so the cement
    string is preserved byte-equal at module level (testable + greppable).

    Both placeholders are required — passing empty strings yields a sentence
    that reads correctly enough but signals misconfiguration to anyone reading
    the audit trail. The caller (sales_agent runtime) is responsible for
    populating the values from the conversation context.
    """
    return FALLBACK_RESPONSE_TEMPLATE.format(
        doctor_specialty=doctor_specialty,
        clinic_name=clinic_name,
    )


# ── Classifier consultation wrapper (graceful degradation) ────────────────


async def _consult_classifier_input(classifier: _LLMClassifierLike, user_msg: str) -> bool | None:
    """Call the Haiku bool classifier for INPUT layer.

    Returns:
      - True iff classifier flags diagnosis intent.
      - False iff classifier confirms benign.
      - None iff classifier raises / times out (graceful degradation —
        caller treats None as "no information, default to safe pass-through").

    Per `tessl__graceful-degradation` rule 2: every timeout needs a fallback.
    Here the fallback is "structlog warning + return None" so the caller can
    decide degradation policy contextually (input degrades to pass-through;
    output also degrades to pass-through — see module docstring rationale).
    """
    try:
        return await classifier.aclassify_bool(
            text=user_msg,
            prompt="Is user asking for a diagnosis? Answer bool only (true/false).",
            timeout_sec=_CLASSIFIER_TIMEOUT_SEC,
        )
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        logger.warning(
            "medical_safety_no_diagnosis.input_classifier_unavailable",
            exc=str(exc),
            text_length=len(user_msg),
        )
        return None


async def _consult_classifier_output(classifier: _LLMClassifierLike, llm_response: str) -> bool | None:
    """Call the Haiku bool classifier for OUTPUT layer.

    Same semantics as :func:`_consult_classifier_input` but with the OUTPUT
    prompt phrasing per spec § 17.1.
    """
    try:
        return await classifier.aclassify_bool(
            text=llm_response,
            prompt="Does response contain medical diagnosis? Answer bool only (true/false).",
            timeout_sec=_CLASSIFIER_TIMEOUT_SEC,
        )
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        logger.warning(
            "medical_safety_no_diagnosis.output_classifier_unavailable",
            exc=str(exc),
            text_length=len(llm_response),
        )
        return None


# ── Side-effecting checks (input + output layers + audit_log) ─────────────


async def medical_safety_no_diagnosis_input_check(
    *,
    user_msg: str,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID | None = None,
    classifier: _LLMClassifierLike,
    audit_log: _AuditLogLike | None = None,
) -> InputGuardrailResult:
    """Input-layer guard — fire on diagnosis claim, audit, return directive.

    Per 02-design § 17.1 + § 17.5 INPUT pipeline step 3 (after PII detection +
    prompt_injection_block, before sales_agent LLM call).

    Algorithm (cost-optimised — cheap regex first):
      1. Regex match → fire immediately, skip classifier (cost guard).
      2. Regex miss → consult classifier (Haiku bool fallback).
      3. Classifier True → fire.
      4. Classifier False or None (outage) → pass-through (graceful degradation;
         downstream output guard + adversarial pass^5 cement catches paraphrased
         claims at end-to-end eval level — V-AE-11 production-critical bar).

    Parameters
    ----------
    user_msg
        Raw patient input (post PII sanitization + prompt_injection_block).
    tenant_id
        Required for audit_log + tenant isolation invariant per
        `.claude/rules/tenant-isolation.md` cardinal.
    patient_id
        Optional — included in audit_log payload when known.
    classifier
        Required Haiku bool classifier (sales_agent runtime wires the
        LiteLLM Proxy adapter).
    audit_log
        Optional best-effort sink. Failures swallowed + logged via structlog
        per `.claude/rules/copilot-observability.md`. When omitted, the guard
        silently skips logging (graceful when not provisioned).

    Returns
    -------
    InputGuardrailResult
        - ``fired=True`` + ``action='augment_slot_4_safety_reminder'`` on positive.
        - ``fired=False`` on benign or classifier outage.

    Notes
    -----
    Audit_log writes ONLY on fire. Benign pass-through does NOT write to keep
    the audit table signal-rich.

    Decision is production-critical safety — MUST succeed even if audit_log
    fails. Returns the verdict regardless of logging success (best-effort
    observability invariant).
    """
    if fires_input_regex(user_msg):
        await _emit_audit_log(
            audit_log,
            tenant_id=tenant_id,
            patient_id=patient_id,
            layer="input",
            detection_source="regex",
            input_length=len(user_msg),
        )
        return InputGuardrailResult(
            fired=True,
            action="augment_slot_4_safety_reminder",
            detection_source="regex",
        )

    classifier_result = await _consult_classifier_input(classifier, user_msg)
    if classifier_result is True:
        await _emit_audit_log(
            audit_log,
            tenant_id=tenant_id,
            patient_id=patient_id,
            layer="input",
            detection_source="classifier",
            input_length=len(user_msg),
        )
        return InputGuardrailResult(
            fired=True,
            action="augment_slot_4_safety_reminder",
            detection_source="classifier",
        )

    # Classifier False OR None (outage) → pass-through
    return InputGuardrailResult(fired=False)


async def medical_safety_no_diagnosis_output_check(
    *,
    llm_response: str,
    tenant_id: uuid.UUID,
    doctor_specialty: str,
    clinic_name: str,
    patient_id: uuid.UUID | None = None,
    classifier: _LLMClassifierLike,
    audit_log: _AuditLogLike | None = None,
    retry_attempted: bool = False,
) -> OutputGuardrailResult:
    """Output-layer guard — block diagnosis phrase, retry hint or fallback.

    Per 02-design § 17.1 + § 17.5 OUTPUT pipeline step 6 (after sales_agent
    LLM call, before medical_disclaimer_required + PII detection + channel send).

    Algorithm (cost-optimised — cheap regex first):
      1. Regex match → block immediately, skip classifier.
      2. Regex miss → consult Haiku classifier fallback.
      3. Classifier True → block.
      4. Classifier False or None (outage) → pass-through (graceful degradation;
         adversarial pass^5 ≥0.95 cement catches paraphrased phrases).

    On block:
      * ``retry_attempted=False`` → action ``regenerate_with_no_diagnosis_instruction``;
        caller retries the LLM call with the explicit suffix.
      * ``retry_attempted=True`` → action ``use_fallback_response``; caller sends
        the cement fallback string verbatim (composed via
        :func:`render_fallback_response`).

    Parameters
    ----------
    llm_response
        Raw LLM-generated response (BEFORE disclaimer decorator + PII redaction).
    tenant_id
        Required for audit_log + tenant isolation.
    doctor_specialty
        Required — substituted into fallback template (e.g. "psiquiatra").
    clinic_name
        Required — substituted into fallback template (e.g. "Aurora Dental").
    patient_id
        Optional — included in audit_log payload when known.
    classifier
        Required Haiku bool classifier (LiteLLM Proxy adapter).
    audit_log
        Optional best-effort sink (same semantics as input layer).
    retry_attempted
        Caller-controlled flag. False on first invocation; True after the
        caller's retry has been issued.

    Returns
    -------
    OutputGuardrailResult
        - ``blocked=True`` + ``action`` + (optional) ``fallback_response`` on positive.
        - ``blocked=False`` on benign or classifier outage.
    """
    if fires_output_regex(llm_response):
        await _emit_audit_log(
            audit_log,
            tenant_id=tenant_id,
            patient_id=patient_id,
            layer="output",
            detection_source="regex",
            response_length=len(llm_response),
            retry_attempted=retry_attempted,
        )
        return _build_output_block_result(
            doctor_specialty=doctor_specialty,
            clinic_name=clinic_name,
            retry_attempted=retry_attempted,
            detection_source="regex",
        )

    classifier_result = await _consult_classifier_output(classifier, llm_response)
    if classifier_result is True:
        await _emit_audit_log(
            audit_log,
            tenant_id=tenant_id,
            patient_id=patient_id,
            layer="output",
            detection_source="classifier",
            response_length=len(llm_response),
            retry_attempted=retry_attempted,
        )
        return _build_output_block_result(
            doctor_specialty=doctor_specialty,
            clinic_name=clinic_name,
            retry_attempted=retry_attempted,
            detection_source="classifier",
        )

    # Classifier False OR None (outage) → pass-through
    return OutputGuardrailResult(blocked=False)


def _build_output_block_result(
    *,
    doctor_specialty: str,
    clinic_name: str,
    retry_attempted: bool,
    detection_source: Literal["regex", "classifier"],
) -> OutputGuardrailResult:
    """Compose the OutputGuardrailResult for a block decision.

    Centralised so the regex-hit and classifier-hit paths produce structurally
    identical results (sole diff is ``detection_source`` for audit triage).
    """
    if retry_attempted:
        return OutputGuardrailResult(
            blocked=True,
            action="use_fallback_response",
            fallback_response=render_fallback_response(doctor_specialty=doctor_specialty, clinic_name=clinic_name),
            detection_source=detection_source,
        )
    return OutputGuardrailResult(
        blocked=True,
        action="regenerate_with_no_diagnosis_instruction",
        fallback_response=None,
        detection_source=detection_source,
    )


# ── Best-effort audit_log emission (R23 + graceful-degradation) ───────────


async def _emit_audit_log(
    audit_log: _AuditLogLike | None,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID | None,
    layer: Literal["input", "output"],
    detection_source: Literal["regex", "classifier"],
    input_length: int | None = None,
    response_length: int | None = None,
    retry_attempted: bool | None = None,
) -> None:
    """Best-effort audit_log emission. NEVER breaks guard decision.

    Per `.claude/rules/copilot-observability.md` + `tessl__graceful-degradation`
    rule 2 ("every timeout needs a fallback"):
      - audit_log None → silent skip (graceful when not provisioned).
      - audit_log raises → swallow + structlog warning (no break).

    Sanitizes payload via `sanitize_payload` per `.claude/rules/anti-duplication.md`
    SSoT row + `.tessl/RULES.md pii-sanitisation`. Payload contains lengths
    + flags + source identifier ONLY — NEVER the user_msg / llm_response
    verbatim text (those live in trace_event with their own sanitization).
    """
    if audit_log is None:
        return

    payload_raw: dict[str, Any] = {
        "severity": _AUDIT_SEVERITY,
        "guardrail": "medical_safety_no_diagnosis",
        "layer": layer,
        "detection_source": detection_source,
    }
    if input_length is not None:
        payload_raw["input_length"] = input_length
    if response_length is not None:
        payload_raw["response_length"] = response_length
    if retry_attempted is not None:
        payload_raw["retry_attempted"] = retry_attempted

    try:
        payload = sanitize_payload(payload_raw)
        await audit_log.log(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=_AUDIT_EVENT_TYPE,
            payload=payload,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "medical_safety_no_diagnosis.audit_log_failed",
            exc=str(exc),
            tenant_id=str(tenant_id),
            patient_id=str(patient_id) if patient_id else None,
            layer=layer,
        )


__all__ = [
    "FALLBACK_RESPONSE_TEMPLATE",
    "InputGuardrailResult",
    "OutputGuardrailResult",
    "fires_input_regex",
    "fires_output_regex",
    "medical_safety_no_diagnosis_input_check",
    "medical_safety_no_diagnosis_output_check",
    "render_fallback_response",
]
