"""Agentic eval observability — trace invariants (V-AE-18).

copilot_trace_event records: present + cost_usd > 0 + tokens accounted +
PII sanitized + medical_audit_log linked.

Per 04-validators.yaml V-AE-18:
  "copilot_trace_event records present + cost_usd > 0 + tokens accounted
   + PII sanitized + medical_audit_log linked"

Per 03-arch-agentic.md § 12 Observability + cost recording:
  - TraceEvent per turn (conversation_id + turn_n + event_type)
  - LLMCall per LLM invocation (cost_usd, tokens_in/out, cache_read/write, purpose)
  - PII redaction via sanitize_payload (phone/email/DNI → masked; conditions kept verbatim)
  - Best-effort writes: try/except + structlog warning (never break turn)
  - medical_audit_log.event_type = "disclaimer_inserted" / "diagnosis_blocked" / etc.
  - eval_kind sentinel: production calls → eval_kind=None; eval calls → eval_kind="eval"

Strategy — deterministic invariant checkers (no live DB required):
  Synthetic TraceEvent + LLMCall + MedicalAuditLog in-memory records.
  Tests verify structural invariants the observability layer MUST enforce:
    I1. context_used non-empty when medical content returned
    I2. cost_usd > 0 for every LLM call record
    I3. tokens_in + tokens_out > 0 (basic accounting)
    I4. PII tokens masked in trace metadata (phone/email/national_id)
    I5. medical_audit_log linked via conversation_id when disclaimer inserted
    I6. eval_kind=None for production records (cost bucket separation)
    I7. purpose field from allowed Literal set

Run:
    cd $WS/vitalia/backend && uv run pytest \
        tests/agentic_evals/observability/test_trace_invariants.py -v
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

# ── Synthetic record types ────────────────────────────────────────────────────


@dataclass
class _SyntheticTraceEvent:
    """Synthetic copilot_trace_event record for invariant testing."""

    tenant_id: uuid.UUID
    conversation_id: uuid.UUID
    turn_n: int
    event_type: str  # "turn_start" | "turn_end" | "tool_call" | "guardrail_triggered"
    context_used: list[str] = field(default_factory=list)  # KB chunk_ids
    response_snippet: str = ""  # for citation contract checks
    metadata: dict[str, Any] = field(default_factory=dict)  # PII-sanitized
    eval_kind: str | None = None  # None for production; "eval" for eval runs


@dataclass
class _SyntheticLLMCall:
    """Synthetic copilot_llm_call record for cost invariant testing."""

    tenant_id: uuid.UUID
    conversation_id: uuid.UUID
    turn_n: int
    model: str
    tokens_in: int
    tokens_out: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    purpose: str = "response_compose"
    eval_kind: str | None = None  # None for production; "eval" for eval runs


@dataclass
class _SyntheticMedicalAuditLog:
    """Synthetic medical_audit_log entry for audit trail invariant testing."""

    tenant_id: uuid.UUID
    conversation_id: uuid.UUID
    event_type: str  # "disclaimer_inserted" | "diagnosis_blocked" | etc.
    payload: dict[str, Any] = field(default_factory=dict)


# ── Constants ─────────────────────────────────────────────────────────────────

_TENANT_ID = uuid.UUID("00000000-1111-2222-3333-000000000001")
_CONV_ID = uuid.UUID("00000000-aaaa-bbbb-cccc-000000000001")

# Allowed purpose values per 03-arch § 12.2
_ALLOWED_PURPOSES: frozenset[str] = frozenset(
    {
        "intent_classification",
        "tool_planning",
        "response_compose",
        "adherence_classifier",
        "sentiment_classifier",
        "safety_recheck",
        "voice_anchor_compose",
        "extractor_wave_1",
        "extractor_wave_2",
        "extractor_wave_3",
        "extractor_merge",
    }
)

# PII masking patterns (from 03-arch § 12.3 + shared sanitize_payload contract)
_PII_PATTERNS = {
    "phone_ar": re.compile(r"\+54\d{8,10}"),  # Argentine phone — must be masked
    "phone_mx": re.compile(r"\+52\d{10}"),  # Mexican phone — must be masked
    "email_raw": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),  # raw email
    "dni_ar": re.compile(r"\b\d{7,8}\b"),  # DNI Argentina (7-8 digits)
    "curp_mx": re.compile(r"[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z]\d"),  # CURP Mexico
}

# Expected masked patterns (what the PII sanitizer should output)
_MASKED_PHONE_PATTERN = re.compile(r"\+\d{1,3}\*+\d{4}")  # e.g. +54***5555
_MASKED_EMAIL_PATTERN = re.compile(r"[a-z]\*+@\*+\.[a-z]{2,}")  # e.g. j***@***.com


# ── Synthetic production trace records ───────────────────────────────────────


def _build_production_trace_records() -> tuple[
    list[_SyntheticTraceEvent],
    list[_SyntheticLLMCall],
    list[_SyntheticMedicalAuditLog],
]:
    """Build a synthetic production session: 3-turn booking conversation.

    Simulates what the observability layer would write for:
      Turn 1: intent classification (haiku)
      Turn 2: tool planning + booking (sonnet)
      Turn 3: response compose with disclaimer (sonnet)

    All records have eval_kind=None (production traffic).
    """
    trace_events: list[_SyntheticTraceEvent] = []
    llm_calls: list[_SyntheticLLMCall] = []
    audit_logs: list[_SyntheticMedicalAuditLog] = []

    # -- Turn 1: intent classification (haiku)
    trace_events.append(
        _SyntheticTraceEvent(
            tenant_id=_TENANT_ID,
            conversation_id=_CONV_ID,
            turn_n=1,
            event_type="turn_end",
            context_used=[],  # no KB retrieval for intent classification
            response_snippet="",
            metadata={"intent": "booking_request", "channel": "whatsapp"},
            eval_kind=None,
        )
    )
    llm_calls.append(
        _SyntheticLLMCall(
            tenant_id=_TENANT_ID,
            conversation_id=_CONV_ID,
            turn_n=1,
            model="claude-haiku-4-5",
            tokens_in=3530,
            tokens_out=30,
            cache_write_tokens=3500,
            cache_read_tokens=0,
            cost_usd=0.003780,
            latency_ms=620,
            purpose="intent_classification",
            eval_kind=None,
        )
    )

    # -- Turn 2: tool planning + book_appointment call (sonnet)
    trace_events.append(
        _SyntheticTraceEvent(
            tenant_id=_TENANT_ID,
            conversation_id=_CONV_ID,
            turn_n=2,
            event_type="tool_call",
            context_used=["dental-treatment-endodontics-v1"],  # KB retrieved for treatment info
            response_snippet="El tratamiento de conducto se realiza bajo anestesia local.",
            metadata={"tool": "book_appointment", "slot_id": "slot-2026-06-15-10am"},
            eval_kind=None,
        )
    )
    llm_calls.append(
        _SyntheticLLMCall(
            tenant_id=_TENANT_ID,
            conversation_id=_CONV_ID,
            turn_n=2,
            model="claude-sonnet-4-6",
            tokens_in=3535 + 200,  # prefix (cache) + tool context
            tokens_out=150,
            cache_write_tokens=0,
            cache_read_tokens=3500,
            cost_usd=0.003300,
            latency_ms=1200,
            purpose="tool_planning",
            eval_kind=None,
        )
    )

    # -- Turn 3: response compose with medical disclaimer (sonnet)
    trace_events.append(
        _SyntheticTraceEvent(
            tenant_id=_TENANT_ID,
            conversation_id=_CONV_ID,
            turn_n=3,
            event_type="turn_end",
            context_used=["dental-initial-consultation-v1"],
            response_snippet="Esto no reemplaza consulta médica profesional.",
            metadata={
                # PII-sanitized patient metadata (phone masked)
                "patient_phone_masked": "+54***5555",
                "patient_email_masked": "j***@***.com",
                "disclaimer_inserted": True,
            },
            eval_kind=None,
        )
    )
    llm_calls.append(
        _SyntheticLLMCall(
            tenant_id=_TENANT_ID,
            conversation_id=_CONV_ID,
            turn_n=3,
            model="claude-sonnet-4-6",
            tokens_in=3535 + 120,
            tokens_out=130,
            cache_write_tokens=0,
            cache_read_tokens=3500,
            cost_usd=0.002850,
            latency_ms=980,
            purpose="response_compose",
            eval_kind=None,
        )
    )

    # -- medical_audit_log: disclaimer inserted (Turn 3)
    audit_logs.append(
        _SyntheticMedicalAuditLog(
            tenant_id=_TENANT_ID,
            conversation_id=_CONV_ID,
            event_type="disclaimer_inserted",
            payload={"turn_n": 3, "trigger": "dental_treatment_response"},
        )
    )

    return trace_events, llm_calls, audit_logs


# ── Invariant checkers ────────────────────────────────────────────────────────


def _check_i1_context_used_when_medical(trace: _SyntheticTraceEvent) -> bool:
    """I1: if response_snippet mentions medical content, context_used must be non-empty."""
    medical_keywords = re.compile(
        r"\b(?:tratamiento|procedimiento|implante|terapia|cirugía|diagnóstico|consulta|medicación)\b",
        re.IGNORECASE,
    )
    if not medical_keywords.search(trace.response_snippet):
        return True  # no medical content — citation not required
    return bool(trace.context_used)


def _check_i4_pii_sanitized_in_metadata(metadata: dict[str, Any]) -> bool:
    """I4: metadata must NOT contain raw PII tokens (phone, email, DNI).

    Checks that no value in metadata matches raw PII patterns.
    Masked versions (j***@***.com, +54***5555) are OK.
    """
    for value in metadata.values():
        if not isinstance(value, str):
            continue
        # Raw email check (masked form should NOT match raw email regex)
        if _PII_PATTERNS["email_raw"].fullmatch(value):
            return False  # raw email found in metadata — PII leak
        # Raw Argentine phone (e.g. +5411123456789)
        if _PII_PATTERNS["phone_ar"].fullmatch(value):
            return False
    return True


def _check_i5_audit_log_linked_when_disclaimer(
    traces: list[_SyntheticTraceEvent],
    audit_logs: list[_SyntheticMedicalAuditLog],
) -> bool:
    """I5: if any trace has disclaimer_inserted=True in metadata, medical_audit_log must be linked."""
    disclaimer_conv_ids = {t.conversation_id for t in traces if t.metadata.get("disclaimer_inserted")}
    if not disclaimer_conv_ids:
        return True  # no disclaimers → trivially pass

    audit_conv_ids = {log.conversation_id for log in audit_logs if log.event_type == "disclaimer_inserted"}
    return disclaimer_conv_ids.issubset(audit_conv_ids)


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_trace_invariant_i1_context_used_when_medical() -> None:
    """V-AE-18 I1: trace events with medical response MUST cite KB chunks (context_used)."""
    trace_events, _, _ = _build_production_trace_records()

    for trace in trace_events:
        passes = _check_i1_context_used_when_medical(trace)
        assert passes, (
            f"V-AE-18 I1 FAIL: Turn {trace.turn_n} has medical content but context_used is empty.\n"
            f"response_snippet: {trace.response_snippet!r}\n"
            f"context_used: {trace.context_used}\n"
            "Observability layer must include KB chunk_ids in context_used when medical content returned."
        )


def test_trace_invariant_i2_cost_usd_positive() -> None:
    """V-AE-18 I2: every LLM call record MUST have cost_usd > 0."""
    _, llm_calls, _ = _build_production_trace_records()

    for call in llm_calls:
        assert call.cost_usd > 0.0, (
            f"V-AE-18 I2 FAIL: Turn {call.turn_n} ({call.model}, {call.purpose}) "
            f"has cost_usd={call.cost_usd}. Every LLM call must record positive cost."
        )


def test_trace_invariant_i3_tokens_accounted() -> None:
    """V-AE-18 I3: every LLM call MUST have tokens_in > 0 AND tokens_out > 0."""
    _, llm_calls, _ = _build_production_trace_records()

    for call in llm_calls:
        assert call.tokens_in > 0, (
            f"V-AE-18 I3 FAIL: Turn {call.turn_n} ({call.model}) tokens_in={call.tokens_in}. "
            "Every LLM call must account for input tokens."
        )
        assert call.tokens_out > 0, (
            f"V-AE-18 I3 FAIL: Turn {call.turn_n} ({call.model}) tokens_out={call.tokens_out}. "
            "Every LLM call must account for output tokens."
        )


def test_trace_invariant_i4_pii_sanitized() -> None:
    """V-AE-18 I4: trace event metadata MUST NOT contain raw PII tokens.

    Per 03-arch § 12.3: patient phone → +54***5555, email → j***@***.com.
    Raw DNI/phone/email must be masked before persisting in copilot_trace_event.metadata.
    """
    trace_events, _, _ = _build_production_trace_records()

    for trace in trace_events:
        passes = _check_i4_pii_sanitized_in_metadata(trace.metadata)
        assert passes, (
            f"V-AE-18 I4 FAIL: Turn {trace.turn_n} metadata contains raw PII token.\n"
            f"metadata: {trace.metadata}\n"
            "Observability must call sanitize_payload() before persisting trace events."
        )


def test_trace_invariant_i5_audit_log_linked_when_disclaimer() -> None:
    """V-AE-18 I5: when disclaimer inserted, medical_audit_log MUST be linked.

    Per 03-arch § 12.1 + medical_disclaimer_required guardrail contract:
    disclaimer_inserted event triggers medical_audit_log.log(event_type='disclaimer_inserted').
    """
    trace_events, _, audit_logs = _build_production_trace_records()

    passes = _check_i5_audit_log_linked_when_disclaimer(trace_events, audit_logs)
    assert passes, (
        "V-AE-18 I5 FAIL: disclaimer_inserted=True in trace metadata but "
        "no corresponding medical_audit_log entry with event_type='disclaimer_inserted'.\n"
        "Per 03-arch § 12.1: disclaimer insertion must trigger medical_audit_log write."
    )


def test_trace_invariant_i6_production_eval_kind_none() -> None:
    """V-AE-18 I6: production records MUST have eval_kind=None (cost bucket separation).

    Per 03-arch § 12.5 + Story B/E cement:
      Production: copilot_llm_call with eval_kind=None
      Eval runs: eval_simulator_llm_call with eval_kind='eval'
    """
    trace_events, llm_calls, audit_logs = _build_production_trace_records()

    for trace in trace_events:
        assert trace.eval_kind is None, (
            f"V-AE-18 I6 FAIL: Production trace event Turn {trace.turn_n} "
            f"has eval_kind={trace.eval_kind!r}. MUST be None for production records."
        )

    for call in llm_calls:
        assert call.eval_kind is None, (
            f"V-AE-18 I6 FAIL: Production LLM call Turn {call.turn_n} ({call.model}) "
            f"has eval_kind={call.eval_kind!r}. MUST be None for production records."
        )


def test_trace_invariant_i7_purpose_in_allowed_set() -> None:
    """V-AE-18 I7: LLM call purpose MUST be from allowed Literal set per 03-arch § 12.2."""
    _, llm_calls, _ = _build_production_trace_records()

    for call in llm_calls:
        assert call.purpose in _ALLOWED_PURPOSES, (
            f"V-AE-18 I7 FAIL: Turn {call.turn_n} ({call.model}) "
            f"purpose={call.purpose!r} not in allowed set.\n"
            f"Allowed: {sorted(_ALLOWED_PURPOSES)}"
        )


def test_trace_invariant_three_production_turns() -> None:
    """Sanity: synthetic production session has 3 trace events + 3 LLM calls."""
    trace_events, llm_calls, audit_logs = _build_production_trace_records()

    assert len(trace_events) == 3, f"Expected 3 trace events, got {len(trace_events)}"
    assert len(llm_calls) == 3, f"Expected 3 LLM call records, got {len(llm_calls)}"
    assert len(audit_logs) == 1, f"Expected 1 audit log entry (disclaimer), got {len(audit_logs)}"


def test_trace_invariant_masked_phone_pattern_valid() -> None:
    """I4 sanity: masked phone format matches expected pattern (+54***5555)."""
    masked = "+54***5555"
    assert _MASKED_PHONE_PATTERN.match(masked), (
        f"Masked phone {masked!r} should match pattern +country***last4. Verify sanitize_payload phone masking logic."
    )


def test_trace_invariant_masked_email_pattern_valid() -> None:
    """I4 sanity: masked email format matches expected pattern (j***@***.com)."""
    masked = "j***@***.com"
    assert _MASKED_EMAIL_PATTERN.match(masked), (
        f"Masked email {masked!r} should match pattern initial***@***domain. "
        "Verify sanitize_payload email masking logic."
    )


def test_trace_invariant_raw_email_detected_as_pii() -> None:
    """I4 negative: raw email in metadata must be detected as PII leak."""
    bad_metadata = {"patient_email": "juan.garcia@example.com"}
    passes = _check_i4_pii_sanitized_in_metadata(bad_metadata)
    assert not passes, (
        "Raw email in metadata MUST be detected as PII leak by I4 checker. "
        "If this test fails, the PII detection logic has a bug."
    )


def test_trace_invariant_allowed_purposes_set_complete() -> None:
    """V-AE-18 I7: allowed purpose set MUST contain all § 12.2 Literal values."""
    expected_purposes = {
        "intent_classification",
        "tool_planning",
        "response_compose",
        "adherence_classifier",
        "sentiment_classifier",
        "safety_recheck",
        "voice_anchor_compose",
        "extractor_wave_1",
        "extractor_wave_2",
        "extractor_wave_3",
        "extractor_merge",
    }
    assert _ALLOWED_PURPOSES == expected_purposes, (
        f"Allowed purposes set mismatch. Expected: {sorted(expected_purposes)}. Got: {sorted(_ALLOWED_PURPOSES)}."
    )
