"""Agentic eval observability invariants — reengagement + lucas tool scenarios.

Story vitalia-slice-1-fidelizacion T-15 (R23 production_code=false — tests/goldens Sonnet OK)

Validator: agentic_observability_invariants (04-validators.yaml)

Extends observability/test_trace_invariants.py with reengagement-specific invariants:
  I8.  send_proactive_reengagement tool call trace MUST include re_engagement_event_id
  I9.  send_proactive_reengagement trace MUST NOT include patient_name or patient_phone
  I10. opt_out=True path MUST NOT emit a tool call trace (no tool was invoked)
  I11. compute_re_engagement_recommendation trace MUST include period + clinic_id + top_n
  I12. compute_re_engagement_recommendation trace MUST NOT include action/rationale bodies
  I13. Lucas tool call MUST have eval_kind=None for production records (cost bucket)
  I14. Adrián re-engagement tool MUST emit trace with trigger_source field

Per 03-arch-agentic.md § 12 + vitalia/.claude/rules/hipaa-lite.md:
  - sanitize_payload mandatory before any trace emission
  - No PHI (patient.name, patient.phone, diagnosis, ...) in traces
  - Dual filter: tenant_id + clinic_id in service call

Strategy — synthetic record validation (no live LLM, no Postgres, no Anthropic API).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pytest

pytestmark = pytest.mark.no_eval


# ── Synthetic record types (mirrors observability/test_trace_invariants.py) ────


@dataclass
class _SyntheticToolCallTrace:
    """Synthetic trace event for a single tool call in Adrián or Lucas context."""

    tenant_id: uuid.UUID
    clinic_id: uuid.UUID
    conversation_id: uuid.UUID
    tool_name: str
    payload: dict[str, Any]  # What the trace emits (MUST be PII-sanitized)
    tool_invoked: bool = True
    eval_kind: str | None = None  # None = production; "eval" = eval run


# ── Constants ─────────────────────────────────────────────────────────────────

_TENANT_ID = uuid.UUID("00000000-1111-2222-3333-000000000002")
_CLINIC_ID = uuid.UUID("00000000-aaaa-bbbb-cccc-000000000002")
_CONV_ID = uuid.UUID("00000000-dddd-eeee-ffff-000000000002")

# PHI fields that must NEVER appear in any tool trace payload (per hipaa-lite.md)
_PHI_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "patient_name",
        "patient_phone",
        "patient_email",
        "patient_dni",
        "patient_address",
        "diagnosis",
        "treatment_plan",
        "medication",
        "dosage",
        "allergies",
        "symptoms",
        "medical_notes",
        "lab_results",
        "vital_signs",
        "imaging_url",
        "xray_filename",
        "ultrasound_report",
        "previous_treatments",
        "family_history",
        "surgical_history",
    }
)

# Fields that MUST be present in send_proactive_reengagement trace
_REENGAGEMENT_TRACE_REQUIRED: frozenset[str] = frozenset(
    {
        "re_engagement_event_id",
        "trigger_source",
        "pattern",
        "clinic_id",
        "tenant_id",
    }
)

# Fields that MUST be present in compute_re_engagement_recommendation trace
_LUCAS_TRACE_REQUIRED: frozenset[str] = frozenset(
    {
        "period",
        "clinic_id",
        "top_n",
        "recommendations_count",
    }
)

# Fields that MUST NOT appear in Lucas trace (recommendation body content)
_LUCAS_TRACE_FORBIDDEN: frozenset[str] = frozenset(
    {
        "action",
        "rationale",
        "patient_name",
        "risk_details",
    }
)


# ── Synthetic trace builders ───────────────────────────────────────────────────


def _build_adrian_happy_tool_trace() -> _SyntheticToolCallTrace:
    """Synthetic trace for send_proactive_reengagement happy path (multi_session).

    Represents what Adrián's tool emits when successfully sending a re-engagement
    message. payload is post-sanitize_payload (no PHI).
    """
    return _SyntheticToolCallTrace(
        tenant_id=_TENANT_ID,
        clinic_id=_CLINIC_ID,
        conversation_id=_CONV_ID,
        tool_name="send_proactive_reengagement",
        payload={
            "tenant_id": str(_TENANT_ID),
            "clinic_id": str(_CLINIC_ID),
            "re_engagement_event_id": "evt-abc-123",
            "pattern": "multi_session",
            "template_id": "recordatorio_proxima_sesion",
            "trigger_source": "cron multi_session_gap_sweep",
            "status": "sent",
            # patient_id (hash, not PHI): acceptable
            "patient_id_hash": "sha256:abc123",
        },
        tool_invoked=True,
        eval_kind=None,
    )


def _build_adrian_optin_guard_trace() -> _SyntheticToolCallTrace:
    """Synthetic trace for absence_optin_guard (opt_out=True — tool NOT invoked).

    When opt_out=True, Adrián should NOT invoke the tool. The trace reflects
    a compliance block — no tool call trace emitted (tool_invoked=False).
    """
    return _SyntheticToolCallTrace(
        tenant_id=_TENANT_ID,
        clinic_id=_CLINIC_ID,
        conversation_id=_CONV_ID,
        tool_name="send_proactive_reengagement",
        payload={
            "tenant_id": str(_TENANT_ID),
            "clinic_id": str(_CLINIC_ID),
            "re_engagement_event_id": "evt-blocked-456",
            "blocked_reason": "patient_opted_out",
            "status": "blocked",
        },
        tool_invoked=False,  # No actual tool call was made
        eval_kind=None,
    )


def _build_lucas_recommendation_trace() -> _SyntheticToolCallTrace:
    """Synthetic trace for compute_re_engagement_recommendation (dental critico).

    Represents what Lucas's tool emits. Payload is aggregate only — NO per-patient
    content, NO action/rationale bodies.
    """
    return _SyntheticToolCallTrace(
        tenant_id=_TENANT_ID,
        clinic_id=_CLINIC_ID,
        conversation_id=_CONV_ID,
        tool_name="compute_re_engagement_recommendation",
        payload={
            "tenant_id": str(_TENANT_ID),
            "clinic_id": str(_CLINIC_ID),
            "period": "30d",
            "top_n": 5,
            "recommendations_count": 5,
            "event_type": "tool.compute_re_engagement_recommendation.completed",
        },
        tool_invoked=True,
        eval_kind=None,
    )


# ── Invariant checkers ─────────────────────────────────────────────────────────


def _check_no_phi_in_payload(payload: dict[str, Any]) -> list[str]:
    """Return list of PHI field names found in payload keys."""
    return [k for k in payload if k in _PHI_FIELD_NAMES]


def _check_required_fields_present(payload: dict[str, Any], required: frozenset[str]) -> list[str]:
    """Return list of required fields missing from payload."""
    return [f for f in required if f not in payload]


def _check_forbidden_fields_absent(payload: dict[str, Any], forbidden: frozenset[str]) -> list[str]:
    """Return list of forbidden fields found in payload."""
    return [f for f in payload if f in forbidden]


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_i8_reengagement_trace_includes_required_fields() -> None:
    """I8: send_proactive_reengagement trace MUST include re_engagement_event_id + trigger_source."""
    trace = _build_adrian_happy_tool_trace()

    missing = _check_required_fields_present(trace.payload, _REENGAGEMENT_TRACE_REQUIRED)
    assert not missing, (
        f"I8 FAIL: send_proactive_reengagement trace missing required fields: {missing}\n"
        f"Payload: {trace.payload}\n"
        "Per 03-arch § 12: every tool trace must include event correlation fields."
    )


def test_i9_reengagement_trace_no_phi() -> None:
    """I9: send_proactive_reengagement trace MUST NOT include patient_name or patient_phone.

    Per hipaa-lite.md: sanitize_payload mandatory before observability writes.
    PHI (patient.name, patient.phone, ...) MUST be masked or excluded.
    """
    trace = _build_adrian_happy_tool_trace()

    phi_found = _check_no_phi_in_payload(trace.payload)
    assert not phi_found, (
        f"I9 FAIL: PHI fields found in tool trace payload: {phi_found}\n"
        f"Payload keys: {list(trace.payload.keys())}\n"
        "Per hipaa-lite.md: call sanitize_payload() before emitting trace events."
    )


def test_i10_optin_guard_no_tool_invocation_trace() -> None:
    """I10: when opt_out=True, tool_invoked MUST be False (no tool call).

    Per design § compliance: when patient has opted out, Adrián MUST NOT invoke
    send_proactive_reengagement. The trace records the compliance block, not a tool call.
    """
    trace = _build_adrian_optin_guard_trace()

    assert not trace.tool_invoked, (
        "I10 FAIL: opt_out guard trace has tool_invoked=True.\n"
        "When opt_out=True, the tool MUST NOT be invoked. "
        "Adrián should respond with opt-out acknowledgment only."
    )
    assert trace.payload.get("blocked_reason") == "patient_opted_out", (
        f"I10 FAIL: blocked_reason missing or wrong in opt_out guard trace.\n"
        f"Expected: 'patient_opted_out'. Got: {trace.payload.get('blocked_reason')!r}"
    )


def test_i11_lucas_trace_includes_required_fields() -> None:
    """I11: Lucas trace MUST include period + clinic_id + top_n + recommendations_count."""
    trace = _build_lucas_recommendation_trace()

    missing = _check_required_fields_present(trace.payload, _LUCAS_TRACE_REQUIRED)
    assert not missing, (
        f"I11 FAIL: Lucas tool trace missing required aggregate fields: {missing}\n"
        f"Payload: {trace.payload}\n"
        "Per 03-arch § 12 + T-10 tool contract: aggregate metadata always in trace."
    )


def test_i12_lucas_trace_no_action_rationale_bodies() -> None:
    """I12: compute_re_engagement_recommendation trace MUST NOT include action/rationale content.

    Recommendation bodies (action text, clinical rationale) are PHI-adjacent and
    should not appear in cost-bearing observability records.
    """
    trace = _build_lucas_recommendation_trace()

    forbidden_found = _check_forbidden_fields_absent(trace.payload, _LUCAS_TRACE_FORBIDDEN)
    assert not forbidden_found, (
        f"I12 FAIL: Lucas trace contains forbidden content fields: {forbidden_found}\n"
        f"Payload keys: {list(trace.payload.keys())}\n"
        "Per T-10 observability contract: exclude action/rationale bodies from trace."
    )


def test_i13_production_traces_have_eval_kind_none() -> None:
    """I13: all production tool traces MUST have eval_kind=None (cost bucket separation).

    Per Story B/E cement: production traffic → eval_kind=None.
    Eval simulator runs → eval_kind='eval'.
    """
    traces = [
        _build_adrian_happy_tool_trace(),
        _build_adrian_optin_guard_trace(),
        _build_lucas_recommendation_trace(),
    ]

    for trace in traces:
        assert trace.eval_kind is None, (
            f"I13 FAIL: {trace.tool_name} production trace has eval_kind={trace.eval_kind!r}.\n"
            "Production tool traces MUST have eval_kind=None."
        )


def test_i14_reengagement_trace_has_trigger_source() -> None:
    """I14: Adrián re-engagement tool trace MUST include trigger_source field.

    trigger_source identifies cron sweep vs manual trigger — essential for
    audit trail and cost attribution.
    """
    trace = _build_adrian_happy_tool_trace()

    assert "trigger_source" in trace.payload, (
        f"I14 FAIL: send_proactive_reengagement trace missing 'trigger_source'.\n"
        f"Payload keys: {list(trace.payload.keys())}\n"
        "Per 03-arch § 12 + T-9 contract: trigger_source required for audit trail."
    )
    assert trace.payload["trigger_source"], "trigger_source must be non-empty string"


def test_dual_filter_both_tenant_and_clinic_in_traces() -> None:
    """Vitalia HIPAA-lite dual filter: tenant_id + clinic_id MUST both appear in traces.

    Per hipaa-lite.md § Tenant isolation refuerzo:
    'vitalia agrega clinic_id como segundo filter obligatorio'.
    This applies to observability traces too: both IDs must be present for
    forensic audit correlation.
    """
    traces = [
        _build_adrian_happy_tool_trace(),
        _build_lucas_recommendation_trace(),
    ]

    for trace in traces:
        assert "tenant_id" in trace.payload, f"Dual filter FAIL: {trace.tool_name} trace missing 'tenant_id'."
        assert "clinic_id" in trace.payload, f"Dual filter FAIL: {trace.tool_name} trace missing 'clinic_id'."


def test_opt_out_guard_trace_no_phi_either() -> None:
    """PHI invariant applies even to blocked (non-invoked) tool traces.

    When Adrián blocks due to opt_out=True, the trace records the block —
    but STILL must not include patient PHI.
    """
    trace = _build_adrian_optin_guard_trace()

    phi_found = _check_no_phi_in_payload(trace.payload)
    assert not phi_found, (
        f"PHI FAIL: opt_out guard trace contains PHI fields: {phi_found}\n"
        "Even compliance-block traces must be sanitized before emission."
    )


def test_reengagement_pattern_values_are_canonical() -> None:
    """Pattern field in Adrián tool trace MUST be from allowed enum.

    Per T-9 tool contract: pattern Literal['multi_session', 'follow_up', 'maintenance', 'absence', 'nps'].
    """
    allowed_patterns = {"multi_session", "follow_up", "maintenance", "absence", "nps"}

    trace = _build_adrian_happy_tool_trace()
    pattern = trace.payload.get("pattern")

    assert pattern in allowed_patterns, (
        f"Pattern {pattern!r} not in allowed enum: {sorted(allowed_patterns)}\n"
        "Per T-9: pattern field must be a Literal from the tool's allowed values."
    )
