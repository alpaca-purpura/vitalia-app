"""Guardrail tests — `medical_safety_no_diagnosis` (vitalia AGENTIC, R23 Opus 4.7).

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Acceptance per 06-tickets.yaml::T-guards-1 + 02-design § 17.1 + 03-arch § 10.2:
  A1: test_input_fires — input regex + Haiku classifier fallback fire on diagnosis
      request; benign clinical input passes through.
  A2: test_output_blocks — output regex + Haiku classifier fallback block diagnosis
      phrase; regenerate hint emitted; fallback string used after 1 retry.
  A3: Adversarial diagnosis persona pass^5 ≥0.95 — DEFERRED to T-eval-1 W17 cross-ticket
      (`tests/agentic_evals/grader/test_vertical_medical_fidelity_adversarial.py`).
      Documented gap in T-guards-1-result.md.

Covers (02-design § 17.1 spec):
  - Runtime layer: BOTH input + output (single module, two entry points).
  - INPUT trigger:
      * Regex `(tengo|tendré|sufro|padezco|me dio|estoy con).*(cáncer|diabetes|VIH|infarto|covid|trastorno|síndrome)`
      * Haiku classifier fallback "Is user asking for a diagnosis? bool only."
  - OUTPUT trigger:
      * Regex `(tienes|sufres|padeces|te diagnostico|es probable que tengas).*(condición|enfermedad|trastorno)`
      * Haiku classifier fallback "Does response contain medical diagnosis? bool only."
  - INPUT action: augment Slot 4 safety reminder + disclaimer + derive to doctor +
    emergency line by country (caller composes; guardrail returns hint flag).
  - OUTPUT action: BLOCK + regenerate hint + retry 1x → fallback string
    "Te derivo con el {doctor_specialty} de {clinic_name} para evaluación profesional."
  - Audit log: `medical_safety_no_diagnosis_fired` (severity medium).
  - Best-effort observability: audit_log + classifier failures NEVER break decision.
  - Tenant isolation: tenant_id propagated through every audit_log write.

These are UNIT tests — guardrail check is mostly pure (regex) with mocked LLM
classifier (in-memory `_FakeLLMClassifier`) + audit_log mocked via in-memory fake.

Anti-duplication: Step 0 GATE grep returned zero collisions (T-guards-1 impl-log).
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

# ── Imports under test (deferred until impl exists; module-level OK because
# T-guards-1 lands the impl together with this file) ────────────────────────
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

    Programmable per-call result via ``next_result`` queue OR fixed
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
    """Classifier always returns False (no diagnosis attempt)."""
    return _FakeLLMClassifier(default_result=False)


@pytest.fixture
def classifier_positive() -> _FakeLLMClassifier:
    """Classifier always returns True (diagnosis attempt)."""
    return _FakeLLMClassifier(default_result=True)


@pytest.fixture
def classifier_failing() -> _FakeLLMClassifier:
    """Classifier always raises (LiteLLM timeout / error)."""
    return _FakeLLMClassifier(raise_on_call=True)


# ── Spec constants present + verbatim ───────────────────────────────────────


def test_fallback_response_template_matches_spec() -> None:
    """A2: fallback string MUST contain spec-mandated phrasing per § 17.1.

    Spec: "Te derivo con el {doctor_specialty} de {clinic_name} para evaluación profesional."
    """
    assert "{doctor_specialty}" in FALLBACK_RESPONSE_TEMPLATE
    assert "{clinic_name}" in FALLBACK_RESPONSE_TEMPLATE
    assert "Te derivo" in FALLBACK_RESPONSE_TEMPLATE
    assert "evaluación profesional" in FALLBACK_RESPONSE_TEMPLATE


def test_render_fallback_response_substitutes_placeholders() -> None:
    """A2: template renders with doctor_specialty + clinic_name substituted."""
    rendered = render_fallback_response(doctor_specialty="psiquiatra", clinic_name="Sanaré LATAM")
    assert "psiquiatra" in rendered
    assert "Sanaré LATAM" in rendered
    assert "{" not in rendered, "rendered template MUST NOT leave unresolved placeholders"


# ── A1 — INPUT regex detection ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "user_msg",
    [
        "Tengo cáncer, ¿qué hago?",
        "Sufro diabetes desde hace años.",
        "Padezco VIH y tengo dudas.",
        "Tendré un infarto si sigo así.",
        "Tengo covid otra vez.",
        "Sufro un trastorno bipolar.",
        "Tengo un síndrome raro que me diagnosticaron.",
        "Me dio un infarto el mes pasado.",
        "Estoy con diabetes desde el 2020.",
    ],
)
def test_input_regex_fires_on_diagnosis_claim(user_msg: str) -> None:
    """A1: spec § 17.1 regex catches direct diagnosis claims."""
    assert fires_input_regex(user_msg) is True


@pytest.mark.parametrize(
    "user_msg",
    [
        "Hola, quiero agendar una consulta.",
        "¿Cuánto cuesta el implante dental?",
        "Quiero reagendar mi turno.",
        "¿Atienden los sábados?",
        "Necesito información sobre tratamientos psicológicos.",
        "¿Tienen disponibilidad la próxima semana?",
        "Mi doctor me pidió que viniera a control.",
    ],
)
def test_input_regex_passes_benign_clinical_queries(user_msg: str) -> None:
    """A1: regex does NOT false-positive on appointment / pricing / info queries."""
    assert fires_input_regex(user_msg) is False


# ── A1 — INPUT layer end-to-end (regex + classifier + audit_log) ─────────


@pytest.mark.asyncio
async def test_input_check_fires_on_regex_match_without_calling_classifier(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A1: regex match → guardrail fires WITHOUT invoking classifier (cost optimization).

    When the cheap regex already detects the diagnosis claim, the more expensive
    Haiku classifier MUST NOT be called — saves cost + latency on the hot path.
    """
    result = await medical_safety_no_diagnosis_input_check(
        user_msg="Tengo cáncer, ¿qué hago?",
        tenant_id=_TENANT_ID,
        patient_id=_PATIENT_ID,
        classifier=classifier_negative,
        audit_log=audit_log,
    )
    assert result.fired is True
    assert result.action == "augment_slot_4_safety_reminder"
    assert classifier_negative.calls == [], "Classifier MUST NOT be called when regex already matched (cost guard)."
    assert len(audit_log.entries) == 1
    assert audit_log.entries[0]["event_type"] == "medical_safety_no_diagnosis_fired"
    assert audit_log.entries[0]["payload"]["severity"] == "medium"
    assert audit_log.entries[0]["payload"]["layer"] == "input"
    assert audit_log.entries[0]["payload"]["detection_source"] == "regex"


@pytest.mark.asyncio
async def test_input_check_fires_on_classifier_when_regex_misses(
    audit_log: _FakeAuditLog,
    classifier_positive: _FakeLLMClassifier,
) -> None:
    """A1: regex miss → classifier consulted; classifier=True → guardrail fires.

    Classifier fallback catches paraphrased / atypical diagnosis requests that
    the regex catalog (verb + condition list) cannot anticipate exhaustively.
    """
    user_msg = "¿Es esto un derrame? No me siento bien y no sé qué tengo."
    # Regex does NOT match (no verb/condition pair from the cement list)
    assert fires_input_regex(user_msg) is False

    result = await medical_safety_no_diagnosis_input_check(
        user_msg=user_msg,
        tenant_id=_TENANT_ID,
        classifier=classifier_positive,
        audit_log=audit_log,
    )
    assert result.fired is True
    assert result.action == "augment_slot_4_safety_reminder"
    assert len(classifier_positive.calls) == 1, "Classifier MUST be invoked when regex misses"
    assert len(audit_log.entries) == 1
    assert audit_log.entries[0]["payload"]["detection_source"] == "classifier"


@pytest.mark.asyncio
async def test_input_check_passes_when_both_regex_and_classifier_clear(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A1: benign input → no fire, no audit entry."""
    result = await medical_safety_no_diagnosis_input_check(
        user_msg="Quiero agendar una consulta para mañana.",
        tenant_id=_TENANT_ID,
        classifier=classifier_negative,
        audit_log=audit_log,
    )
    assert result.fired is False
    assert result.action is None
    assert len(classifier_negative.calls) == 1, (
        "Classifier IS consulted on regex miss — single classifier call confirms benign input."
    )
    assert audit_log.entries == [], "No audit entry on benign input."


# ── A2 — OUTPUT regex detection ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "llm_response",
    [
        "Por lo que describes, tienes una condición autoinmune.",
        "Sufres una enfermedad cardiovascular crónica.",
        "Padeces un trastorno de ansiedad generalizado.",
        "Te diagnostico un cuadro depresivo mayor.",
        "Es probable que tengas una condición renal subyacente.",
        "Es probable que tengas diabetes tipo 2 según los síntomas.",
    ],
)
def test_output_regex_fires_on_diagnosis_phrase(llm_response: str) -> None:
    """A2: spec § 17.1 regex catches LLM-generated diagnosis phrases."""
    assert fires_output_regex(llm_response) is True


@pytest.mark.parametrize(
    "llm_response",
    [
        "Te confirmo el horario de tu cita.",
        "El implante dental se coloca en una sesión.",
        "Aurora atiende de lunes a viernes.",
        "El doctor García está disponible el jueves.",
        "Si tienes dudas, te derivo con el odontólogo de la clínica.",
    ],
)
def test_output_regex_passes_benign_responses(llm_response: str) -> None:
    """A2: regex does NOT false-positive on scheduling / referral / info responses."""
    assert fires_output_regex(llm_response) is False


# ── A2 — OUTPUT layer end-to-end (regex + classifier + block + retry + fallback) ──


@pytest.mark.asyncio
async def test_output_check_blocks_on_regex_match_emits_regenerate_hint(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A2: regex match → blocked=True + action=regenerate (single retry hint).

    First failure path: caller retries the LLM call once with explicit
    "do not diagnose" instruction. Retry success path is exercised at the
    caller (orchestrator) level — guardrail surface emits the regenerate hint
    only.
    """
    result = await medical_safety_no_diagnosis_output_check(
        llm_response="Tienes una condición autoinmune según los síntomas.",
        tenant_id=_TENANT_ID,
        patient_id=_PATIENT_ID,
        doctor_specialty="reumatólogo",
        clinic_name="Aurora Dental Buenos Aires",
        classifier=classifier_negative,
        audit_log=audit_log,
        retry_attempted=False,
    )
    assert result.blocked is True
    assert result.action == "regenerate_with_no_diagnosis_instruction"
    assert result.fallback_response is None, "Fallback only used after retry has been attempted (retry_attempted=True)."
    assert classifier_negative.calls == [], "Cost guard — regex hit short-circuits classifier."
    assert len(audit_log.entries) == 1
    assert audit_log.entries[0]["payload"]["layer"] == "output"


@pytest.mark.asyncio
async def test_output_check_returns_fallback_after_retry_exhausted(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A2: regex match + retry_attempted=True → fallback string returned.

    Spec § 17.1 OUTPUT action: "retries 1x → if still fails, returns fallback".
    Caller passes ``retry_attempted=True`` on the second invocation; guardrail
    composes the safe fallback string verbatim per spec.
    """
    result = await medical_safety_no_diagnosis_output_check(
        llm_response="Te diagnostico una condición ansiosa generalizada.",
        tenant_id=_TENANT_ID,
        doctor_specialty="psiquiatra",
        clinic_name="Sanaré LATAM",
        classifier=classifier_negative,
        audit_log=audit_log,
        retry_attempted=True,
    )
    assert result.blocked is True
    assert result.action == "use_fallback_response"
    assert result.fallback_response is not None
    assert "psiquiatra" in result.fallback_response
    assert "Sanaré LATAM" in result.fallback_response
    assert "Te derivo" in result.fallback_response
    assert len(audit_log.entries) == 1
    assert audit_log.entries[0]["payload"]["retry_attempted"] is True


@pytest.mark.asyncio
async def test_output_check_classifier_fallback_when_regex_misses(
    audit_log: _FakeAuditLog,
    classifier_positive: _FakeLLMClassifier,
) -> None:
    """A2: regex miss → classifier consulted; classifier=True → blocked.

    Phrasing chosen avoids both verb-subject regex couples — uses indirect
    diagnosis ("se ve compatible con") that the cement regex catalog cannot
    enumerate exhaustively. The Haiku classifier flags semantic intent
    where the regex falls short — defense in depth per spec § 17.1.
    """
    llm_response = "Por la descripción, lo que describes parece compatible con migrañas crónicas."
    # Regex does NOT match this phrasing exactly
    assert fires_output_regex(llm_response) is False

    result = await medical_safety_no_diagnosis_output_check(
        llm_response=llm_response,
        tenant_id=_TENANT_ID,
        doctor_specialty="neurólogo",
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
    result = await medical_safety_no_diagnosis_output_check(
        llm_response="Te confirmo el horario de tu cita para el jueves a las 10.",
        tenant_id=_TENANT_ID,
        doctor_specialty="odontólogo",
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
async def test_input_check_blocks_even_if_audit_log_raises(
    audit_log_failing: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A1: audit_log failure MUST NOT prevent guardrail decision (R23 best-effort).

    Per .claude/rules/copilot-observability.md + tessl__graceful-degradation:
    > Best-effort observability — NEVER break the production path on failure.

    Decision (fire/no-fire) is production-critical safety; logging is observability.
    """
    result = await medical_safety_no_diagnosis_input_check(
        user_msg="Tengo cáncer, ¿qué hago?",
        tenant_id=_TENANT_ID,
        classifier=classifier_negative,
        audit_log=audit_log_failing,
    )
    assert result.fired is True, "Decision MUST succeed even if audit_log raises — block decision is safety-critical."


@pytest.mark.asyncio
async def test_output_check_blocks_even_if_audit_log_raises(
    audit_log_failing: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """A2: audit_log failure MUST NOT prevent OUTPUT block decision."""
    result = await medical_safety_no_diagnosis_output_check(
        llm_response="Tienes una enfermedad pulmonar crónica.",
        tenant_id=_TENANT_ID,
        doctor_specialty="neumonólogo",
        clinic_name="Aurora Dental",
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
    result = await medical_safety_no_diagnosis_input_check(
        user_msg="Tengo cáncer.",
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
    """A1: classifier timeout/error on regex MISS → graceful degradation.

    Per tessl__graceful-degradation Rule 2: "every timeout needs a fallback".
    When regex did NOT match AND classifier failed, the safe degradation is
    pass-through (do NOT block benign user input on classifier outage). The
    cost of false-positive (blocking a benign user message) > false-negative
    (missing one paraphrased diagnosis request that downstream output guard
    + adversarial pass^5 cement should catch).

    A structlog warning is emitted (best-effort observability), but the
    decision returns ``fired=False`` to avoid breaking the user experience.
    """
    result = await medical_safety_no_diagnosis_input_check(
        user_msg="¿Será que tengo algo en el pecho?",  # ambiguous, no regex match
        tenant_id=_TENANT_ID,
        classifier=classifier_failing,
        audit_log=audit_log,
    )
    assert result.fired is False, (
        "Pass-through on classifier failure when regex didn't match — "
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
    that catches paraphrased diagnosis attempts at end-to-end eval level.
    """
    result = await medical_safety_no_diagnosis_output_check(
        llm_response="El control que te pidió el doctor es importante.",
        tenant_id=_TENANT_ID,
        doctor_specialty="cardiólogo",
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
    await medical_safety_no_diagnosis_input_check(
        user_msg="Tengo VIH desde hace meses.",
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
    await medical_safety_no_diagnosis_output_check(
        llm_response="Tienes una condición autoinmune.",
        tenant_id=custom_tenant,
        doctor_specialty="reumatólogo",
        clinic_name="Aurora Dental",
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
    await medical_safety_no_diagnosis_input_check(
        user_msg="Tengo cáncer y mi DNI es 12345678",
        tenant_id=_TENANT_ID,
        classifier=classifier_negative,
        audit_log=audit_log,
    )
    payload = audit_log.entries[0]["payload"]
    payload_str = str(payload)
    assert "12345678" not in payload_str, "PII (DNI) leaked to audit payload"
    assert "cáncer y mi DNI" not in payload_str, "user_msg verbatim leaked"
    # Length-only tracking cement
    assert "input_length" in payload


@pytest.mark.asyncio
async def test_audit_payload_does_not_leak_llm_response_verbatim(
    audit_log: _FakeAuditLog,
    classifier_negative: _FakeLLMClassifier,
) -> None:
    """PII guard: output audit payload contains lengths only, NEVER llm_response."""
    sensitive_response = "Tienes una condición autoinmune llamada Lupus eritematoso sistémico."
    await medical_safety_no_diagnosis_output_check(
        llm_response=sensitive_response,
        tenant_id=_TENANT_ID,
        doctor_specialty="reumatólogo",
        clinic_name="Aurora Dental",
        classifier=classifier_negative,
        audit_log=audit_log,
        retry_attempted=False,
    )
    payload = audit_log.entries[0]["payload"]
    payload_str = str(payload)
    assert "Lupus" not in payload_str
    assert "autoinmune" not in payload_str
    assert "response_length" in payload


# ── Result type shape (frozen dataclass cement) ─────────────────────────────


def test_input_result_is_frozen() -> None:
    """Result types MUST be frozen — caller cannot mutate guard verdict."""
    result = InputGuardrailResult(fired=False)
    with pytest.raises((AttributeError, TypeError, Exception)):
        result.fired = True  # type: ignore[misc]


def test_output_result_is_frozen() -> None:
    """OutputGuardrailResult MUST be frozen."""
    result = OutputGuardrailResult(blocked=False)
    with pytest.raises((AttributeError, TypeError, Exception)):
        result.blocked = True  # type: ignore[misc]
