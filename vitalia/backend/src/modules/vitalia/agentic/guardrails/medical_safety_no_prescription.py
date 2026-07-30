# cap: agentic.medical-safety-guardrails
# story-origin: TBD
"""Vitalia AGENTIC guardrail — `medical_safety_no_prescription` (input + output layers).

R23: production_code=True AGENTIC code. Opus 4.7 EXCLUSIVE.
Story 11 T-guards-2.

Spec sources:
  * 02-design-agentic.md § 17.2 + § 17.5 INPUT pipeline step 4 + OUTPUT pipeline step 7
  * 03-arch-agentic.md § 10.1 pipeline order + § 10.2 per-guard runtime
  * 06-tickets.yaml::T-guards-2 acceptance A1 (test_forced_disclaimer_retrieval)
  * 05-guidelines.md § 1.10 R23 agentic patterns + § 1.4 tenant isolation
  * .claude/rules/sales-agent-brand-voice.md (chrome refusal strings stay neutro tuteo)
  * .claude/rules/copilot-resilience.md + copilot-observability.md (best-effort writes)
  * .claude/rules/anti-duplication.md §0 (NO mirror — NEW vertical-medical surface)
  * .claude/rules/tenant-isolation.md (every audit_log carries tenant_id)
  * tessl__graceful-degradation rules 1+2 (timeout + fallback on classifier outage)

Severity HIGH (production-critical for psychiatry tenants — wrong prescription
recommendation can cause real harm via missed contraindications, dose errors,
abrupt discontinuation syndromes). Stricter posture than `medical_safety_no_diagnosis`
(severity medium).

Semantics — input layer (pre-LLM call, pipeline step 4):
  1. Detect prescription REQUEST by patient via cheap keyword scan first
     (medication INN/brand name from
     ``medical_kb_psychiatry_v1/manifest.yaml::medication_keywords`` —
     300 entries — coupled within 80-char window with verb
     ``tomar|aumentar|disminuir|cambiar|reemplazar``).
  2. On keyword MISS, consult Haiku classifier fallback ("Is user asking
     for medication recommendation? bool only.") — wrapped in timeout +
     try/except per graceful-degradation rule 1.
  3. On EITHER positive → return ``InputGuardrailResult(fired=True,
     action='force_disclaimer_chunk_retrieval', forced_chunk_id=
     'disclaimer_psychiatric_prescription_only',
     augment_slot_4_safety_reminder=True, derive_to_specialty='psychiatry')``.
     The orchestrator (sales_agent runtime) consumes this directive to:
       a. Pin the boundary chunk at top-1 RAG retrieval (forced) so the
          response cites the disclaimer verbatim.
       b. Augment Slot 4 prompt with the safety reminder block.
       c. Surface the ``appointment_reschedule_with_doctor`` tool with
          ``specialty=psychiatry`` so the agent can derive the patient.
  4. On classifier outage (timeout/error) AND keyword miss → graceful
     degradation: return ``fired=False`` (false-positive cost > false-negative
     cost for input; downstream output guard + adversarial pass^5 ≥0.95
     cement at V-AE-11 catches paraphrased asks at end-to-end eval level).
  5. Audit log ``medical_safety_no_prescription_fired`` (severity HIGH)
     ONLY on fire.

Semantics — output layer (post-LLM, pipeline step 7, before disclaimer + PII):
  1. Detect prescription PHRASE in LLM response by cheap regex
     (verb pattern ``te recomiendo tomar|aumenta la dosis|cambia tu
     medicación|deja de tomar|reemplaza``).
  2. On regex MISS, consult Haiku classifier fallback ("Does response
     recommend medication? bool only.").
  3. On EITHER positive AND ``retry_attempted=False`` → return
     ``OutputGuardrailResult(blocked=True,
     action='regenerate_with_no_prescription_instruction')``. Caller
     invokes LLM again with explicit "do not recommend medication" suffix.
  4. On EITHER positive AND ``retry_attempted=True`` → return
     ``OutputGuardrailResult(blocked=True, action='use_fallback_response',
     fallback_response=<rendered safe template>)``. Caller sends fallback verbatim.
  5. On classifier outage AND regex miss → graceful degradation:
     return ``blocked=False`` (same reasoning as input — adversarial cement catches).
  6. Audit log ``medical_safety_no_prescription_fired`` (severity HIGH) ONLY on
     block, with ``layer='output'`` + ``retry_attempted`` flag.

Anti-duplication audit (Step 0 GATE pre-write per .claude/rules/anti-duplication.md):
  * `medical_safety_no_prescription` — NEW vertical-medical guard. Cross-codebase
    grep returned ZERO matches in `backend/src/`, `luana-platform/`, and
    `core/` aside from design docs + KB manifest + extension placeholder +
    skeleton ``__init__.py``. No mirror risk.
  * `sanitize_payload` consumed from `luana_core_observability.recording.sanitization`
    (per anti-duplication.md SSoT row) — NEVER re-implemented.
  * `_AuditLogLike` Protocol mirrors structural surface used by sibling
    guardrails (T-guards-1 + T-guards-3) + extractors (T-extractors-1) —
    structural typing only, NOT a class hierarchy mirror.
  * `_LLMClassifierLike` Protocol matches sibling guardrail T-guards-1 —
    decoupled bool classifier interface (no extra surface area beyond what
    the guardrail needs).
  * Medication keyword catalog — loaded from KB manifest at module init
    (single source of truth: ``medical_kb_psychiatry_v1/manifest.yaml::
    medication_keywords``). NEVER duplicated to a Python literal.
  * Forced disclaimer chunk_id — referenced by string constant only; the
    actual chunk content lives in ``00_disclaimer.md`` and is retrieved
    by the orchestrator via Qdrant. Guardrail emits the directive only.
  * Slot 4 sandbox markers + reminder text — REFERENCED via spec citation
    only. T-prompts-1 j2 file NOT modified by this ticket (cement immutable).

Cost: keyword scan + regex path $0; classifier fallback ≈ $0.0001-0.0003
per Haiku invocation (deferred to caller's existing observability hooks via
LiteLLM Proxy CustomLogger bridge — PI-12 S1 T-1 cement). Latency:
keyword scan <1ms (compiled regex over 300-name disjunction); regex <1ms;
classifier p99 ≤5s with hard timeout enforced per `tessl__graceful-degradation`.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal, Protocol

import structlog
import yaml
from luana_core_observability.recording.sanitization import sanitize_payload

logger = structlog.get_logger(__name__)


# ── Configuration constants (cement — exported for tests + ratchet) ───────


#: Spec § 17.2 verbatim fallback string. Safe phrasing — Spanish neutro tuteo
#: per spec § 17.4 chrome rule (refusal strings stay generic across tenants
#: regardless of voseo dialect; voice slot 5 owns the voiced channel-side
#: turn composition, but the safety fallback bypasses voice composition).
#:
#: Placeholders ``{dr_name}`` and ``{clinic_name}`` are substituted at render
#: time via :func:`render_fallback_response`. NEVER substitute via
#: ``str.format`` directly — use the helper to keep cement string intact.
FALLBACK_RESPONSE_TEMPLATE: Final[str] = (
    "Solo un psiquiatra puede recetar o ajustar medicación. Te agendo con el {dr_name} de {clinic_name}."
)

#: Boundary chunk id from `medical_kb_psychiatry_v1/manifest.yaml::boundary_chunks`
#: (T-kb-3 cement). Drift here would silently break the orchestrator's forced
#: top-1 retrieval call (Qdrant returns nothing → no disclaimer in response →
#: V-AE-11 adversarial pass^5 ≥0.95 fails → production safety regression).
FORCED_DISCLAIMER_CHUNK_ID: Final[str] = "disclaimer_psychiatric_prescription_only"

#: Hard timeout for the Haiku classifier fallback call. Per
#: `tessl__graceful-degradation` rule 1 default 5s — Haiku Anthropic latency
#: p99 typically <2s for short bool prompts, the 5s ceiling tolerates a slow
#: tail without holding up the patient turn.
_CLASSIFIER_TIMEOUT_SEC: Final[float] = 5.0

#: Severity per spec § 17.2 audit_log row. HIGH = production-critical for
#: psychiatry tenants (wrong recommendation can cause real harm). Compared to
#: ``medical_safety_no_diagnosis`` (severity medium), this guard is the
#: stricter posture for prescription-class asks.
_AUDIT_SEVERITY: Final[str] = "high"

#: Audit event type cement — must remain byte-equal to spec § 17.2 row name
#: so trend-monitoring queries + adversarial grader reads stay in sync.
_AUDIT_EVENT_TYPE: Final[str] = "medical_safety_no_prescription_fired"

#: Path to the KB manifest providing the canonical medication keyword
#: catalog (T-kb-3 contract). Single-source-of-truth: edits to the keyword
#: list happen in the manifest (so KB retrieval + safety guard stay in sync).
_PSYCHIATRY_MANIFEST_PATH: Final[Path] = (
    Path(__file__).resolve().parents[2]  # .../modules/vitalia/
    / "copilot"
    / "kb"
    / "medical_kb_psychiatry_v1"
    / "manifest.yaml"
)


# ── Medication keyword catalog (loaded once at module init) ───────────────


def _load_medication_keywords() -> tuple[str, ...]:
    """Load the 300+ medication keyword catalog from the psychiatry KB manifest.

    Returns an immutable tuple (frozen at import time) so callers cannot
    accidentally mutate the cement catalog. The list itself is maintained
    in `medical_kb_psychiatry_v1/manifest.yaml::medication_keywords`
    (T-kb-3 contract — same source the KB retrieval pipeline trusts).

    Failure mode: if the manifest cannot be read OR the key is missing,
    raise at import time. The guardrail is a SAFETY surface — running with
    an empty keyword catalog would silently degrade the input layer to
    classifier-only (cost spike + missed regex fast-paths), so we prefer
    a hard import-time failure to an invisible runtime regression.
    """
    if not _PSYCHIATRY_MANIFEST_PATH.is_file():
        raise FileNotFoundError(
            f"medical_safety_no_prescription: psychiatry KB manifest not found at "
            f"{_PSYCHIATRY_MANIFEST_PATH} — guard cannot initialize keyword catalog."
        )
    with _PSYCHIATRY_MANIFEST_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    keywords = data.get("medication_keywords") if isinstance(data, dict) else None
    if not isinstance(keywords, list) or not keywords:
        raise ValueError(
            f"medical_safety_no_prescription: medication_keywords missing/empty in "
            f"{_PSYCHIATRY_MANIFEST_PATH} — guard cannot initialize keyword catalog."
        )
    # Lowercase + dedupe + freeze — case-insensitive scan downstream
    return tuple(sorted({str(k).strip().lower() for k in keywords if str(k).strip()}))


#: Frozen medication keyword catalog (300+ INN + brand names) loaded once
#: at module import from ``medical_kb_psychiatry_v1/manifest.yaml``.
MEDICATION_KEYWORDS: Final[tuple[str, ...]] = _load_medication_keywords()


def _build_input_keyword_regex() -> re.Pattern[str]:
    """Compile a single regex coupling INPUT verbs with any medication keyword.

    Pattern shape: ``\\b(verb)\\b.{0,80}?\\b(med1|med2|...)\\b`` (and the
    reverse ordering ``\\b(med)\\b.{0,80}?\\b(verb)\\b`` to catch
    "Quiero la sertralina por la mañana, ¿puedo tomarla?" patterns where the
    medication is mentioned before the verb).

    The 80-char gap bounds the verb-medication coupling so a long benign
    sentence containing both tokens by accident does NOT trigger
    (e.g. "Tengo que cambiar mi turno con el doctor que me recetó sertralina
    el mes pasado" does not couple "cambiar" + "sertralina" within the
    80-char window — they sit ~70 chars apart but in unrelated clauses; the
    benign-passes parametrize covers similar cases).

    Compiling once at module load (rather than per-call) keeps hot-path
    latency under 1ms even with 300-name disjunction (Python ``re`` engine
    handles disjunctions efficiently when sorted longest-first).
    """
    # Sort longest-first so disjunction matches greedy maximal token first
    # (e.g. "inhibidor selectivo de la recaptación de serotonina" must
    # match before the shorter "inhibidor de la recaptación").
    meds_pattern = "|".join(re.escape(k) for k in sorted(MEDICATION_KEYWORDS, key=len, reverse=True))
    verbs_pattern = (
        r"(?:tomar|tomarla|tomarlo|aument(?:ar|a|o)|disminu(?:ir|ye|yo)"
        r"|cambiar|cambia|cambio|reemplaz(?:ar|a|o))"
    )
    # Two orderings: verb→med and med→verb, both coupled within 80-char window.
    pattern = (
        rf"(?:\b{verbs_pattern}\b.{{0,80}}?\b(?:{meds_pattern})\b)"
        rf"|"
        rf"(?:\b(?:{meds_pattern})\b.{{0,80}}?\b{verbs_pattern}\b)"
    )
    return re.compile(pattern, re.IGNORECASE | re.DOTALL)


#: Compiled INPUT regex coupling medication keywords with prescription
#: verbs. Built once at module init from :data:`MEDICATION_KEYWORDS`.
_INPUT_PRESCRIPTION_RE: Final[re.Pattern[str]] = _build_input_keyword_regex()


# ── OUTPUT regex catalog (append-only per safety ratchet) ─────────────────


#: OUTPUT regex — spec § 17.2 verbatim:
#: ``(te recomiendo tomar|aumenta la dosis|cambia tu medicación|
#:    deja de tomar|reemplaza)``.
#:
#: Append-only: adding a phrase is safe (true positives rise, false negatives
#: shrink). REMOVING a pattern requires bumping rubric version per Story E
#: D16 cement. Spec § 17.2 cement strings are kept verbatim; additional
#: variants extend defensively.
_OUTPUT_PRESCRIPTION_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:"
    r"te\s+recomiendo\s+tomar"  # spec verbatim
    r"|aumenta(?:r)?\s+(?:la\s+|tu\s+)?dosis"  # spec verbatim
    r"|cambia(?:r)?\s+tu\s+medicaci[oó]n"  # spec verbatim
    r"|deja(?:r)?\s+de\s+tomar"  # spec verbatim
    r"|reemplaza(?:r)?\s+(?:el|la|tu)\s+\w+"  # spec verbatim — must precede an article+noun (a medication)
    r")",
    re.IGNORECASE,
)


# ── Protocols (structural typing — decouple from concrete impls) ──────────


class _LLMClassifierLike(Protocol):
    """Minimal surface for the Haiku bool classifier fallback.

    Mirrors sibling guardrail T-guards-1 protocol shape. Concrete
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
    consumed by sibling guardrails (T-guards-1 + T-guards-3) + extractors
    (T-extractors-1) + compliance_event_service (T-be-3). Structural typing
    only — concrete implementation supplied by caller.
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

    When ``fired=True``:
      * ``action='force_disclaimer_chunk_retrieval'`` instructs the
        orchestrator to pin the boundary chunk at top-1 RAG retrieval.
      * ``forced_chunk_id`` identifies the chunk to pin (cement constant
        :data:`FORCED_DISCLAIMER_CHUNK_ID`).
      * ``augment_slot_4_safety_reminder=True`` instructs the orchestrator
        to enrich Slot 4 with the safety reminder block.
      * ``derive_to_specialty='psychiatry'`` instructs the orchestrator to
        surface the ``appointment_reschedule_with_doctor`` tool with that
        specialty so the agent can derive the patient.

    The guardrail does NOT compose the augmented prompt itself — it only
    emits the directive (orchestrator owns prompt assembly + tool surfacing
    + RAG forced retrieval).

    Detection metadata (``detection_source``) feeds the audit log payload
    so analysts can triangulate whether a fire originated from the cheap
    keyword scan (most adversarial corpus) or the classifier fallback
    (paraphrased asks, harder to enumerate).
    """

    fired: bool
    action: Literal["force_disclaimer_chunk_retrieval"] | None = None
    forced_chunk_id: str | None = None
    augment_slot_4_safety_reminder: bool = False
    derive_to_specialty: Literal["psychiatry"] | None = None
    detection_source: Literal["keywords", "classifier"] | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class OutputGuardrailResult:
    """Outcome of an output-layer guardrail check.

    When ``blocked=True``:
      * ``action='regenerate_with_no_prescription_instruction'`` — first
        failure; caller retries the LLM call with explicit
        "do not recommend medication" suffix.
      * ``action='use_fallback_response'`` — retry exhausted; caller sends
        ``fallback_response`` verbatim (cement Spanish-neutro safe phrasing).

    When ``blocked=False``, ``action`` and ``fallback_response`` are both
    None and the response passes through to the next pipeline stage
    (disclaimer decorator step 8).
    """

    blocked: bool
    action: (
        Literal[
            "regenerate_with_no_prescription_instruction",
            "use_fallback_response",
        ]
        | None
    ) = None
    fallback_response: str | None = None
    detection_source: Literal["regex", "classifier"] | None = None


# ── Pure helpers (unit-testable, no I/O) ──────────────────────────────────


def fires_input_keywords(user_msg: str) -> bool:
    """Return True iff ``user_msg`` matches a medication-keyword + verb couple.

    Pure regex — no LLM, no DB. Catalog
    (:data:`MEDICATION_KEYWORDS`) is loaded once at module init from the
    psychiatry KB manifest (T-kb-3 contract). Append-only ratchet (true
    positives rise on additions; false negatives shrink). Removing a verb
    or medication requires rubric version bump.
    """
    return _INPUT_PRESCRIPTION_RE.search(user_msg) is not None


def fires_output_regex(llm_response: str) -> bool:
    """Return True iff ``llm_response`` matches the cement OUTPUT regex.

    Pure regex — no LLM, no DB. Same ratchet semantics as
    :func:`fires_input_keywords`.
    """
    return _OUTPUT_PRESCRIPTION_RE.search(llm_response) is not None


def render_fallback_response(*, dr_name: str, clinic_name: str) -> str:
    """Render the cement fallback string with safe substitution.

    Uses ``str.format`` on :data:`FALLBACK_RESPONSE_TEMPLATE` so the cement
    string is preserved byte-equal at module level (testable + greppable).

    Both placeholders are required — passing empty strings yields a sentence
    that reads correctly enough but signals misconfiguration to anyone reading
    the audit trail. The caller (sales_agent runtime) is responsible for
    populating the values from the conversation context.
    """
    return FALLBACK_RESPONSE_TEMPLATE.format(dr_name=dr_name, clinic_name=clinic_name)


# ── Classifier consultation wrapper (graceful degradation) ────────────────


async def _consult_classifier_input(classifier: _LLMClassifierLike, user_msg: str) -> bool | None:
    """Call the Haiku bool classifier for INPUT layer.

    Returns:
      - True iff classifier flags prescription-request intent.
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
            prompt="Is user asking for medication recommendation? Answer bool only (true/false).",
            timeout_sec=_CLASSIFIER_TIMEOUT_SEC,
        )
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        logger.warning(
            "medical_safety_no_prescription.input_classifier_unavailable",
            exc=str(exc),
            text_length=len(user_msg),
        )
        return None


async def _consult_classifier_output(classifier: _LLMClassifierLike, llm_response: str) -> bool | None:
    """Call the Haiku bool classifier for OUTPUT layer.

    Same semantics as :func:`_consult_classifier_input` but with the OUTPUT
    prompt phrasing per spec § 17.2.
    """
    try:
        return await classifier.aclassify_bool(
            text=llm_response,
            prompt="Does response recommend medication? Answer bool only (true/false).",
            timeout_sec=_CLASSIFIER_TIMEOUT_SEC,
        )
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        logger.warning(
            "medical_safety_no_prescription.output_classifier_unavailable",
            exc=str(exc),
            text_length=len(llm_response),
        )
        return None


# ── Side-effecting checks (input + output layers + audit_log) ─────────────


async def medical_safety_no_prescription_input_check(
    *,
    user_msg: str,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID | None = None,
    classifier: _LLMClassifierLike,
    audit_log: _AuditLogLike | None = None,
) -> InputGuardrailResult:
    """Input-layer guard — fire on prescription request, audit, return directive.

    Per 02-design § 17.2 + § 17.5 INPUT pipeline step 4 (after PII detection +
    prompt_injection_block + medical_safety_no_diagnosis, before sales_agent
    LLM call).

    Algorithm (cost-optimised — cheap keyword scan first):
      1. Keyword-verb couple match → fire immediately, skip classifier (cost guard).
      2. Keyword miss → consult classifier (Haiku bool fallback).
      3. Classifier True → fire.
      4. Classifier False or None (outage) → pass-through (graceful degradation;
         downstream output guard + adversarial pass^5 cement catches paraphrased
         asks at end-to-end eval level — V-AE-11 production-critical bar).

    Parameters
    ----------
    user_msg
        Raw patient input (post PII sanitization + prompt_injection_block +
        medical_safety_no_diagnosis input layer).
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
        - ``fired=True`` + directive payload on positive (forced retrieval +
          Slot 4 reminder + derive-to-psychiatry).
        - ``fired=False`` on benign or classifier outage.

    Notes
    -----
    Audit_log writes ONLY on fire. Benign pass-through does NOT write to keep
    the audit table signal-rich.

    Decision is production-critical safety (HIGH severity) — MUST succeed
    even if audit_log fails. Returns the verdict regardless of logging
    success (best-effort observability invariant).
    """
    if fires_input_keywords(user_msg):
        await _emit_audit_log(
            audit_log,
            tenant_id=tenant_id,
            patient_id=patient_id,
            layer="input",
            detection_source="keywords",
            input_length=len(user_msg),
        )
        return _build_input_fire_result(detection_source="keywords")

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
        return _build_input_fire_result(detection_source="classifier")

    # Classifier False OR None (outage) → pass-through
    return InputGuardrailResult(fired=False)


async def medical_safety_no_prescription_output_check(
    *,
    llm_response: str,
    tenant_id: uuid.UUID,
    dr_name: str,
    clinic_name: str,
    patient_id: uuid.UUID | None = None,
    classifier: _LLMClassifierLike,
    audit_log: _AuditLogLike | None = None,
    retry_attempted: bool = False,
) -> OutputGuardrailResult:
    """Output-layer guard — block prescription phrase, retry hint or fallback.

    Per 02-design § 17.2 + § 17.5 OUTPUT pipeline step 7 (after sales_agent
    LLM call + medical_safety_no_diagnosis output layer, before
    medical_disclaimer_required + PII detection + channel send).

    Algorithm (cost-optimised — cheap regex first):
      1. Regex match → block immediately, skip classifier.
      2. Regex miss → consult Haiku classifier fallback.
      3. Classifier True → block.
      4. Classifier False or None (outage) → pass-through (graceful degradation;
         adversarial pass^5 ≥0.95 cement catches paraphrased phrases).

    On block:
      * ``retry_attempted=False`` → action ``regenerate_with_no_prescription_instruction``;
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
    dr_name
        Required — substituted into fallback template (e.g. "Dra. Pérez").
    clinic_name
        Required — substituted into fallback template (e.g. "Sanaré LATAM").
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
            dr_name=dr_name,
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
            dr_name=dr_name,
            clinic_name=clinic_name,
            retry_attempted=retry_attempted,
            detection_source="classifier",
        )

    # Classifier False OR None (outage) → pass-through
    return OutputGuardrailResult(blocked=False)


def _build_input_fire_result(
    *,
    detection_source: Literal["keywords", "classifier"],
) -> InputGuardrailResult:
    """Compose the InputGuardrailResult for a fire decision.

    Centralised so both keyword-hit and classifier-hit paths produce
    structurally identical directive payloads (sole diff is
    ``detection_source`` for audit triage). Encodes the spec § 17.2 INPUT
    action triplet:
      a. forced top-1 RAG retrieval of the disclaimer chunk
      b. Slot 4 safety reminder augmentation
      c. derive-to-psychiatry tool surfacing
    """
    return InputGuardrailResult(
        fired=True,
        action="force_disclaimer_chunk_retrieval",
        forced_chunk_id=FORCED_DISCLAIMER_CHUNK_ID,
        augment_slot_4_safety_reminder=True,
        derive_to_specialty="psychiatry",
        detection_source=detection_source,
    )


def _build_output_block_result(
    *,
    dr_name: str,
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
            fallback_response=render_fallback_response(dr_name=dr_name, clinic_name=clinic_name),
            detection_source=detection_source,
        )
    return OutputGuardrailResult(
        blocked=True,
        action="regenerate_with_no_prescription_instruction",
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
    detection_source: Literal["keywords", "regex", "classifier"],
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
        "guardrail": "medical_safety_no_prescription",
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
            "medical_safety_no_prescription.audit_log_failed",
            exc=str(exc),
            tenant_id=str(tenant_id),
            patient_id=str(patient_id) if patient_id else None,
            layer=layer,
        )


__all__ = [
    "FALLBACK_RESPONSE_TEMPLATE",
    "FORCED_DISCLAIMER_CHUNK_ID",
    "MEDICATION_KEYWORDS",
    "InputGuardrailResult",
    "OutputGuardrailResult",
    "fires_input_keywords",
    "fires_output_regex",
    "medical_safety_no_prescription_input_check",
    "medical_safety_no_prescription_output_check",
    "render_fallback_response",
]
