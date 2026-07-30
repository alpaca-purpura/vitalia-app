"""Guardrail tests — `medical_safety_no_prescription` (vitalia AGENTIC, R23 Opus 4.7).

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Acceptance per 06-tickets.yaml::T-guards-2 + 02-design § 17.2 + 03-arch § 10.2:
  A1: test_forced_disclaimer_retrieval — medication keyword + verb triggers
      forced top-1 retrieval directive for the
      `disclaimer_psychiatric_prescription_only` chunk + Slot 4 reminder
      flag for the orchestrator to insert disclaimer verbatim and derive
      to psychiatrist via `appointment_reschedule_with_doctor`.
  A2: Adversarial medication persona pass^5 ≥0.95 — DEFERRED to T-eval-1 W17
      cross-ticket
      (`tests/agentic_evals/grader/test_vertical_medical_fidelity_adversarial.py::test_prescription_safety`).
      Documented gap in T-guards-2-result.md.

Covers (02-design § 17.2 spec):
  - Runtime layer: BOTH input + output (single module, two entry points).
  - INPUT trigger:
      * Keyword scan medication names (300+ from
        `medical_kb_psychiatry_v1/manifest.yaml::medication_keywords`) +
        verbs `(tomar|aumentar|disminuir|cambiar|reemplazar)`.
      * Haiku classifier fallback "Is user asking for medication recommendation? bool only."
  - OUTPUT trigger:
      * Regex `(te recomiendo tomar|aumenta la dosis|cambia tu medicación|deja de tomar|reemplaza)`.
      * Haiku classifier fallback "Does response recommend medication? bool only."
  - INPUT action: forced top-1 retrieval of
    `disclaimer_psychiatric_prescription_only` chunk from
    `medical_kb_psychiatry_v1` + Slot 4 reminder flag (caller composes;
    guardrail returns directive payload).
  - OUTPUT action: BLOCK + regenerate hint + retry 1x → fallback string
    "Solo un psiquiatra puede recetar o ajustar medicación. Te agendo con
    el {dr_name} de {clinic_name}." (verbatim spec § 17.2).
  - Audit log: `medical_safety_no_prescription_fired` (severity high).
  - Best-effort observability: audit_log + classifier failures NEVER break decision.
  - Tenant isolation: tenant_id propagated through every audit_log write.

These are UNIT tests — guardrail check is mostly pure (regex + keyword scan)
with mocked LLM classifier (in-memory `_FakeLLMClassifier`) + audit_log mocked
via in-memory fake. Mirrors structural shape of T-guards-1 test fixture
(`test_medical_safety_no_diagnosis.py`) for cross-guard consistency.

Anti-duplication: Step 0 GATE grep returned zero collisions for
``medical_safety_no_prescription`` symbol cross-codebase
(only references = design docs + manifest + extension placeholder + skeleton
__init__.py). NEW vertical-medical surface — no mirror risk.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

# ── Imports under test (deferred until impl exists; module-level OK because
# T-guards-2 lands the impl together with this file) ────────────────────────
from src.modules.vitalia.agentic.guardrails.medical_safety_no_prescription import (
    FALLBACK_RESPONSE_TEMPLATE,
    FORCED_DISCLAIMER_CHUNK_ID,
    MEDICATION_KEYWORDS,
    InputGuardrailResult,
    OutputGuardrailResult,
    fires_input_keywords,
    fires_output_regex,
    medical_safety_no_prescription_input_check,
    medical_safety_no_prescription_output_check,
    render_fallback_response,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


_TENANT_ID = uuid.uuid4()
_PATIENT_ID = uuid.uuid4()


class _FakeAuditLog:
    """In-memory stand-in for the medical audit_log (best-effort writes)."""

    def __init__(self, *, raise_on_log: bool = False) -> None:
        self._raise_on_log = raise_on_log
        self.entries: list[dict[str, Any]] = []

    async def log(
        self,
        *,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID | None = None,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        if self._raise_on_log:
            raise RuntimeError("audit_log unavailable — fake failure")
        self.entries.append(
            {
                "tenant_id": tenant_id,
                "patient_id": patient_id,
                "event_type": event_type,
                "payload": payload,
            }
        )


class _FakeLLMClassifier:
    """In-memory Haiku classifier stand-in.

    Programmable per-call result via ``next_results`` queue OR fixed
    ``default_result``. ``raise_on_call`` simulates LiteLLM Proxy timeout /
    error → guardrail must degrade gracefully.
    """

    def __init__(
        self,
        *,
        default_result: bool = False,
        raise_on_call: bool = False,
    ) -> None:
        self.default_result = default_result
        self.raise_on_call = raise_on_call
        self.calls: list[dict[str, Any]] = []
        self.next_results: list[bool] = []

    async def aclassify_bool(
        self,
        *,
        text: str,
        prompt: str,
        timeout_sec: float = 5.0,
    ) -> bool:
        if self.raise_on_call:
            raise TimeoutError("classifier timeout — fake failure")
        self.calls.append({"text": text, "prompt": prompt, "timeout_sec": timeout_sec})
        if self.next_results:
            return self.next_results.pop(0)
        return self.default_result


@pytest.fixture
def audit_log() -> _FakeAuditLog:
    return _FakeAuditLog()


@pytest.fixture
def audit_log_failing() -> _FakeAuditLog:
    return _FakeAuditLog(raise_on_log=True)


@pytest.fixture
def classifier_negative() -> _FakeLLMClassifier:
    """Classifier always returns False (no prescription request)."""
    return _FakeLLMClassifier(default_result=False)


@pytest.fixture
def classifier_positive() -> _FakeLLMClassifier:
    """Classifier always returns True (prescription request)."""
    return _FakeLLMClassifier(default_result=True)


@pytest.fixture
def classifier_failing() -> _FakeLLMClassifier:
    """Classifier always raises (LiteLLM timeout / error)."""
    return _FakeLLMClassifier(raise_on_call=True)


# ── Cement constants present + verbatim ─────────────────────────────────────


def test_fallback_response_template_matches_spec() -> None:
    """A2: fallback string MUST contain spec-mandated phrasing per § 17.2.

    Spec verbatim:
        "Solo un psiquiatra puede recetar o ajustar medicación. Te agendo con
        el {dr_name} de {clinic_name}."
    """
    assert "{dr_name}" in FALLBACK_RESPONSE_TEMPLATE
    assert "{clinic_name}" in FALLBACK_RESPONSE_TEMPLATE
    assert "Solo un psiquiatra puede recetar" in FALLBACK_RESPONSE_TEMPLATE
    assert "ajustar medicación" in FALLBACK_RESPONSE_TEMPLATE
    assert "Te agendo con" in FALLBACK_RESPONSE_TEMPLATE


def test_render_fallback_response_substitutes_placeholders() -> None:
    """A2: template renders with dr_name + clinic_name substituted."""
    rendered = render_fallback_response(dr_name="Dra. Pérez", clinic_name="Sanaré LATAM")
    assert "Dra. Pérez" in rendered
    assert "Sanaré LATAM" in rendered
    assert "{" not in rendered, "rendered template MUST NOT leave unresolved placeholders"


def test_forced_disclaimer_chunk_id_matches_kb_manifest() -> None:
    """A1: chunk_id MUST match the boundary chunk declared in
    `medical_kb_psychiatry_v1/manifest.yaml::boundary_chunks` (T-kb-3 cement).

    Drift here would silently break the orchestrator's forced-retrieval call
    (Qdrant returns nothing → no disclaimer in response → V-AE-11 adversarial
    pass^5 ≥0.95 fails → production safety regression).
    """
    assert FORCED_DISCLAIMER_CHUNK_ID == "disclaimer_psychiatric_prescription_only"


def test_medication_keywords_loaded_from_manifest() -> None:
    """A1: 200+ medication keywords loaded from KB manifest at module init.

    Spec § 17.2: "Keyword scan medication names from
    `medical_kb_psychiatry_v1/manifest.yaml::medication_keywords` (200+
    INN + brand names)".

    Cement INN samples per T-kb-3 ratchet contract — these MUST be present
    so input layer fires on common psychiatric medications regardless of
    branding/locale.
    """
    assert len(MEDICATION_KEYWORDS) >= 200, (
        f"medication_keywords must have ≥200 entries (INN + brand names). Got {len(MEDICATION_KEYWORDS)}."
    )
    # Sample INN that MUST be present
    meds_low = {m.lower() for m in MEDICATION_KEYWORDS}
    for inn in ("sertralina", "fluoxetina", "clonazepam", "alprazolam", "litio", "quetiapina"):
        assert inn in meds_low, f"medication_keywords missing canonical INN {inn!r}"
    # Sample brand names that MUST be present
    for brand in ("zoloft", "prozac", "rivotril", "xanax", "seroquel"):
        assert brand in meds_low, f"medication_keywords missing common brand {brand!r}"


# ── A1 — INPUT keyword scan detection ───────────────────────────────────────


@pytest.mark.parametrize(
    "user_msg",
    [
        # ── Ask for dose change / increase ──
        "¿Puedo aumentar la dosis de sertralina?",
        "Quiero tomar más fluoxetina por las mañanas.",
        # ── Ask for combination / replacement ──
        "¿Puedo cambiar mi escitalopram por clonazepam?",
        "Quisiera reemplazar el alprazolam por algo más suave.",
        # ── Ask for self-administration ──
        "¿Cuántos miligramos de quetiapina debo tomar?",
        # ── Brand-name + decrease ──
        "Quiero disminuir la dosis de Zoloft que estoy tomando.",
        # ── Spanish neutro phrasings ──
        "Puedo tomar Rivotril si no logro dormir esta noche?",
        "¿Cómo cambiar la litio sin recaída?",
    ],
)
def test_input_keywords_fire_on_prescription_request(user_msg: str) -> None:
    """A1: spec § 17.2 keyword + verb scan catches direct prescription requests."""
    assert fires_input_keywords(user_msg) is True


@pytest.mark.parametrize(
    "user_msg",
    [
        "Hola, quiero agendar una consulta con el psiquiatra.",
        "¿Cuánto cuesta una consulta de salud mental?",
        "Quiero reagendar mi turno de la próxima semana.",
        "¿Atienden los sábados con turno de tarde?",
        "Necesito información sobre los tratamientos disponibles.",
        "¿Tienen disponibilidad la próxima semana para una primera vez?",
        "Mi psiquiatra me pidió que viniera a control.",
        # Mentions a medication WITHOUT a verb — no fire (info-only query)
        "¿Qué es la sertralina?",
        # Mentions a verb WITHOUT a medication — no fire
        "Quiero cambiar el horario de la consulta.",
    ],
)
def test_input_keywords_pass_benign_clinical_queries(user_msg: str) -> None:
    """A1: keyword scan does NOT false-positive on appointment / pricing / info queries.

    Importantly: verb without medication OR medication without verb → no fire.
    The verb-keyword coupling within a bounded window prevents benign
    false positives like "¿Qué es la sertralina?" (pure info question).
    """
    assert fires_input_keywords(user_msg) is False


# ── A1 — INPUT layer end-to-end (keyword + classifier + audit_log + directive) ─


@pytest.mark.asyncio
async def test_input_check_fires_on_keyword_match_without_calling_classifier(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A1: keyword+verb match → guardrail fires WITHOUT invoking classifier (cost optimization).

    When the cheap keyword scan already detects the prescription request, the more
    expensive Haiku classifier MUST NOT be called — saves cost + latency on the
    hot path.

    Result MUST carry the forced retrieval directive so the orchestrator
    composes the augmented response with the disclaimer chunk verbatim
    and the derive-to-psychiatrist tool call.
    """
    result = await medical_safety_no_prescription_input_check(
        user_msg="¿Puedo aumentar la dosis de sertralina?",
        tenant_id=_TENANT_ID,
        patient_id=_PATIENT_ID,
        classifier=classifier_negative,
        audit_log=audit_log,
    )
    assert result.fired is True
    assert result.action == "force_disclaimer_chunk_retrieval"
    # Directive payload — orchestrator consumes ALL three to compose the response
    assert result.forced_chunk_id == "disclaimer_psychiatric_prescription_only"
    assert result.augment_slot_4_safety_reminder is True
    assert result.derive_to_specialty == "psychiatry"
    assert classifier_negative.calls == [], (
        "Classifier MUST NOT be called when keyword scan already matched (cost guard)."
    )
    assert len(audit_log.entries) == 1
    assert audit_log.entries[0]["event_type"] == "medical_safety_no_prescription_fired"
    assert audit_log.entries[0]["payload"]["severity"] == "high"
    assert audit_log.entries[0]["payload"]["layer"] == "input"
    assert audit_log.entries[0]["payload"]["detection_source"] == "keywords"


@pytest.mark.asyncio
async def test_input_check_fires_on_classifier_when_keywords_miss(
    audit_log: _FakeAuditLog,
    classifier_positive: _FakeLLMClassifier,
) -> None:
    """A1: keyword miss → classifier consulted; classifier=True → guardrail fires.

    Classifier fallback catches paraphrased / atypical prescription requests
    that the keyword catalog (verb + medication name) cannot anticipate
    exhaustively (e.g. street terms, indirect asks, code words).
    """
    user_msg = "¿Hay algo natural que me ayude a no necesitar mis pastillas para dormir?"
    # Keyword scan does NOT fire (no INN/brand from the cement list, verb decoupled)
    assert fires_input_keywords(user_msg) is False

    result = await medical_safety_no_prescription_input_check(
        user_msg=user_msg,
        tenant_id=_TENANT_ID,
        classifier=classifier_positive,
        audit_log=audit_log,
    )
    assert result.fired is True
    assert result.action == "force_disclaimer_chunk_retrieval"
    assert result.forced_chunk_id == "disclaimer_psychiatric_prescription_only"
    assert len(classifier_positive.calls) == 1, "Classifier MUST be invoked when keyword scan misses"
    assert len(audit_log.entries) == 1
    assert audit_log.entries[0]["payload"]["detection_source"] == "classifier"


@pytest.mark.asyncio
async def test_input_check_passes_when_both_keywords_and_classifier_clear(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A1: benign input → no fire, no audit entry, no directive."""
    result = await medical_safety_no_prescription_input_check(
        user_msg="Quiero agendar una consulta para mañana al mediodía.",
        tenant_id=_TENANT_ID,
        classifier=classifier_negative,
        audit_log=audit_log,
    )
    assert result.fired is False
    assert result.action is None
    assert result.forced_chunk_id is None
    assert result.augment_slot_4_safety_reminder is False
    assert result.derive_to_specialty is None
    assert len(classifier_negative.calls) == 1, (
        "Classifier IS consulted on keyword miss — single classifier call confirms benign input."
    )
    assert audit_log.entries == [], "No audit entry on benign input."


# ── A2 — OUTPUT regex detection ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "llm_response",
    [
        "Te recomiendo tomar 50mg de sertralina por la noche.",
        "Aumenta la dosis a 100mg cada 12 horas.",
        "Cambia tu medicación actual por escitalopram.",
        "Deja de tomar el clonazepam si te causa somnolencia.",
        "Reemplaza el alprazolam con algo de menor potencia.",
    ],
)
def test_output_regex_fires_on_prescription_phrase(llm_response: str) -> None:
    """A2: spec § 17.2 regex catches LLM-generated prescription phrases."""
    assert fires_output_regex(llm_response) is True


@pytest.mark.parametrize(
    "llm_response",
    [
        "Te confirmo el horario de tu cita con el psiquiatra.",
        "El psiquiatra puede revisar tu medicación actual en consulta.",
        "Te derivo con la psiquiatra de la clínica para evaluar tu tratamiento.",
        "Solo un psiquiatra puede recetar o ajustar tu medicación.",  # the disclaimer itself
        "El doctor García está disponible el jueves a las 10.",
    ],
)
def test_output_regex_passes_benign_responses(llm_response: str) -> None:
    """A2: regex does NOT false-positive on referrals / scheduling / info /
    or the disclaimer phrase itself (which restates the no-prescription policy
    rather than recommending medication)."""
    assert fires_output_regex(llm_response) is False


# ── A2 — OUTPUT layer end-to-end (regex + classifier + block + retry + fallback) ─


@pytest.mark.asyncio
async def test_output_check_blocks_on_regex_match_emits_regenerate_hint(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A2: regex match → blocked=True + action=regenerate (single retry hint).

    First failure path: caller retries the LLM call once with explicit
    "do not recommend medication" suffix. Retry success path is exercised
    at the caller (orchestrator) level — guardrail surface emits the
    regenerate hint only.
    """
    result = await medical_safety_no_prescription_output_check(
        llm_response="Te recomiendo tomar 50mg de sertralina por la noche.",
        tenant_id=_TENANT_ID,
        patient_id=_PATIENT_ID,
        dr_name="Dra. Pérez",
        clinic_name="Sanaré LATAM",
        classifier=classifier_negative,
        audit_log=audit_log,
        retry_attempted=False,
    )
    assert result.blocked is True
    assert result.action == "regenerate_with_no_prescription_instruction"
    assert result.fallback_response is None, "Fallback only used after retry has been attempted (retry_attempted=True)."
    assert classifier_negative.calls == [], "Cost guard — regex hit short-circuits classifier."
    assert len(audit_log.entries) == 1
    assert audit_log.entries[0]["payload"]["severity"] == "high"
    assert audit_log.entries[0]["payload"]["layer"] == "output"


@pytest.mark.asyncio
async def test_output_check_returns_fallback_after_retry_exhausted(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A2: regex match + retry_attempted=True → fallback string returned.

    Spec § 17.2 OUTPUT action: "retries 1x → if still fails, returns fallback".
    Caller passes ``retry_attempted=True`` on the second invocation; guardrail
    composes the safe fallback string verbatim per spec.
    """
    result = await medical_safety_no_prescription_output_check(
        llm_response="Aumenta la dosis de quetiapina a 200mg.",
        tenant_id=_TENANT_ID,
        dr_name="Dr. Rodríguez",
        clinic_name="Sanaré LATAM",
        classifier=classifier_negative,
        audit_log=audit_log,
        retry_attempted=True,
    )
    assert result.blocked is True
    assert result.action == "use_fallback_response"
    assert result.fallback_response is not None
    assert "Solo un psiquiatra puede recetar" in result.fallback_response
    assert "Dr. Rodríguez" in result.fallback_response
    assert "Sanaré LATAM" in result.fallback_response
    assert len(audit_log.entries) == 1
    assert audit_log.entries[0]["payload"]["retry_attempted"] is True


@pytest.mark.asyncio
async def test_output_check_classifier_fallback_when_regex_misses(
    audit_log: _FakeAuditLog,
    classifier_positive: _FakeLLMClassifier,
) -> None:
    """A2: regex miss → classifier consulted; classifier=True → blocked.

    Phrasing chosen avoids the cement verb regex catalog — uses indirect
    medication suggestion ("podrías probar con") that the regex cannot
    enumerate exhaustively. The Haiku classifier flags semantic intent
    where the regex falls short — defense in depth per spec § 17.2.
    """
    llm_response = "Para tu caso, podrías probar con un ansiolítico suave durante las primeras semanas."
    # Regex does NOT match this phrasing
    assert fires_output_regex(llm_response) is False

    result = await medical_safety_no_prescription_output_check(
        llm_response=llm_response,
        tenant_id=_TENANT_ID,
        dr_name="Dra. López",
        clinic_name="Mindful Santiago",
        classifier=classifier_positive,
        audit_log=audit_log,
        retry_attempted=False,
    )
    assert result.blocked is True
    assert len(classifier_positive.calls) == 1
    assert audit_log.entries[0]["payload"]["detection_source"] == "classifier"


@pytest.mark.asyncio
async def test_output_check_passes_benign_response(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A2: benign LLM output → not blocked, no audit entry."""
    result = await medical_safety_no_prescription_output_check(
        llm_response="Te confirmo el horario de tu cita para el jueves a las 10.",
        tenant_id=_TENANT_ID,
        dr_name="Dr. Suárez",
        clinic_name="Aurora Dental",
        classifier=classifier_negative,
        audit_log=audit_log,
        retry_attempted=False,
    )
    assert result.blocked is False
    assert result.action is None
    assert result.fallback_response is None
    assert audit_log.entries == [], "No audit entry on benign output."


# ── Best-effort observability + graceful degradation ────────────────────────


@pytest.mark.asyncio
async def test_input_check_fires_even_if_audit_log_raises(
    audit_log_failing: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A1: audit_log failure MUST NOT prevent guardrail decision (R23 best-effort).

    Per .claude/rules/copilot-observability.md + tessl__graceful-degradation:
    > Best-effort observability — NEVER break the production path on failure.

    Decision (fire/no-fire) is production-critical safety; logging is observability.
    HIGH severity guard MUST be especially robust to logging outage.
    """
    result = await medical_safety_no_prescription_input_check(
        user_msg="¿Puedo aumentar la dosis de sertralina?",
        tenant_id=_TENANT_ID,
        classifier=classifier_negative,
        audit_log=audit_log_failing,
    )
    assert result.fired is True, "Decision MUST succeed even if audit_log raises — block decision is safety-critical."
    assert result.forced_chunk_id == "disclaimer_psychiatric_prescription_only"


@pytest.mark.asyncio
async def test_output_check_blocks_even_if_audit_log_raises(
    audit_log_failing: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A2: audit_log failure MUST NOT prevent OUTPUT block decision."""
    result = await medical_safety_no_prescription_output_check(
        llm_response="Te recomiendo tomar 100mg de litio por la mañana.",
        tenant_id=_TENANT_ID,
        dr_name="Dra. García",
        clinic_name="Aurora",
        classifier=classifier_negative,
        audit_log=audit_log_failing,
        retry_attempted=False,
    )
    assert result.blocked is True


@pytest.mark.asyncio
async def test_input_check_works_without_audit_log(
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A1: audit_log optional — guard works when omitted (graceful degradation)."""
    result = await medical_safety_no_prescription_input_check(
        user_msg="Quiero tomar más sertralina.",
        tenant_id=_TENANT_ID,
        classifier=classifier_negative,
        audit_log=None,
    )
    assert result.fired is True


@pytest.mark.asyncio
async def test_input_check_degrades_when_classifier_fails(
    audit_log: _FakeAuditLog,
    classifier_failing: _FakeLLMClassifier,
) -> None:
    """A1: classifier timeout/error on keyword MISS → graceful degradation.

    Per tessl__graceful-degradation Rule 2: "every timeout needs a fallback".
    When keyword scan did NOT match AND classifier failed, the safe degradation is
    pass-through (do NOT block benign user input on classifier outage). The
    cost of false-positive (blocking a benign user message) > false-negative
    (missing one paraphrased prescription request that downstream output guard
    + adversarial pass^5 ≥0.95 cement at V-AE-11 catches).

    A structlog warning is emitted (best-effort observability), but the
    decision returns ``fired=False`` to avoid breaking the user experience.
    """
    result = await medical_safety_no_prescription_input_check(
        user_msg="¿Hay algo que pueda probar para dormir mejor?",  # ambiguous, no keyword
        tenant_id=_TENANT_ID,
        classifier=classifier_failing,
        audit_log=audit_log,
    )
    assert result.fired is False, (
        "Pass-through on classifier failure when keywords didn't match — "
        "false-positive cost > false-negative cost for input."
    )
    assert audit_log.entries == [], (
        "No audit entry when guard degrades silently — the structlog warning captures the outage."
    )


@pytest.mark.asyncio
async def test_output_check_degrades_when_classifier_fails(
    audit_log: _FakeAuditLog,
    classifier_failing: _FakeLLMClassifier,
) -> None:
    """A2: classifier timeout/error on regex MISS → graceful degradation.

    Same reasoning as input degradation: avoid blocking benign LLM responses
    on classifier outage. Adversarial pass^5 ≥0.95 (V-AE-11) is the cement
    that catches paraphrased prescription suggestions at end-to-end eval level.
    """
    result = await medical_safety_no_prescription_output_check(
        llm_response="El control que te pidió el psiquiatra es importante.",
        tenant_id=_TENANT_ID,
        dr_name="Dra. Pérez",
        clinic_name="Mindful Santiago",
        classifier=classifier_failing,
        audit_log=audit_log,
        retry_attempted=False,
    )
    assert result.blocked is False
    assert audit_log.entries == []


# ── Tenant isolation invariant (cement) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_log_records_tenant_id_input(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """Cement: every audit_log write carries the tenant_id (tenant isolation rule)."""
    custom_tenant = uuid.uuid4()
    custom_patient = uuid.uuid4()
    await medical_safety_no_prescription_input_check(
        user_msg="¿Puedo cambiar mi escitalopram?",
        tenant_id=custom_tenant,
        patient_id=custom_patient,
        classifier=classifier_negative,
        audit_log=audit_log,
    )
    assert audit_log.entries[0]["tenant_id"] == custom_tenant
    assert audit_log.entries[0]["patient_id"] == custom_patient


@pytest.mark.asyncio
async def test_audit_log_records_tenant_id_output(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """Cement: every output audit_log write carries the tenant_id."""
    custom_tenant = uuid.uuid4()
    await medical_safety_no_prescription_output_check(
        llm_response="Te recomiendo tomar 50mg de fluoxetina.",
        tenant_id=custom_tenant,
        dr_name="Dr. Tenant",
        clinic_name="Tenant Clinic",
        classifier=classifier_negative,
        audit_log=audit_log,
        retry_attempted=False,
    )
    assert audit_log.entries[0]["tenant_id"] == custom_tenant


# ── PII non-leakage in audit payload ────────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_payload_does_not_leak_user_msg_verbatim(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """PII guard: audit payload contains lengths + flags + classifier confidence,
    NEVER the user_msg verbatim (per .tessl/RULES.md pii-sanitisation)."""
    await medical_safety_no_prescription_input_check(
        user_msg="Quiero aumentar mi sertralina y mi DNI es 12345678",
        tenant_id=_TENANT_ID,
        classifier=classifier_negative,
        audit_log=audit_log,
    )
    payload = audit_log.entries[0]["payload"]
    payload_str = str(payload)
    assert "12345678" not in payload_str, "PII (DNI) leaked to audit payload"
    assert "DNI es" not in payload_str, "user_msg verbatim leaked"
    # Length-only tracking cement
    assert "input_length" in payload


@pytest.mark.asyncio
async def test_audit_payload_does_not_leak_llm_response_verbatim(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """PII guard: output audit payload contains lengths only, NEVER llm_response."""
    sensitive_response = "Te recomiendo tomar 50mg de sertralina, marca Zoloft, todas las mañanas."
    await medical_safety_no_prescription_output_check(
        llm_response=sensitive_response,
        tenant_id=_TENANT_ID,
        dr_name="Dra. Pérez",
        clinic_name="Sanaré LATAM",
        classifier=classifier_negative,
        audit_log=audit_log,
        retry_attempted=False,
    )
    payload = audit_log.entries[0]["payload"]
    payload_str = str(payload)
    assert "Zoloft" not in payload_str
    assert "sertralina" not in payload_str
    assert "response_length" in payload


# ── Result type shape (frozen dataclass cement) ─────────────────────────────


def test_input_guardrail_result_is_immutable() -> None:
    """Cement: frozen dataclass — caller cannot mutate verdict after dispatch."""
    result = InputGuardrailResult(fired=False)
    with pytest.raises(Exception):  # FrozenInstanceError under dataclasses
        result.fired = True  # type: ignore[misc]


def test_output_guardrail_result_is_immutable() -> None:
    """Cement: frozen dataclass — caller cannot mutate verdict after dispatch."""
    result = OutputGuardrailResult(blocked=False)
    with pytest.raises(Exception):
        result.blocked = True  # type: ignore[misc]
