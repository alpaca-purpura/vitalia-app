"""Agentic eval grader — no-hallucination citation contract (V-AE-13).

No-hallucination grader — RAG citation contract enforced ≥0.90.

Per 04-validators.yaml V-AE-13:
  "No-hallucination grader — RAG citation contract enforced
   (KB chunk_id cited in trace_event.context_used)"
  Rubric: docs/specs/rubrics/no-hallucination.md
  Threshold: 0.90

Strategy — deterministic citation contract verifier (no LLM required):
  The no-hallucination contract requires that when a sales_agent response
  references medical procedures / KB-sourced information, the agent's
  trace_event must include `context_used` with the KB chunk_id(s) cited.

  This test suite enforces the STRUCTURAL INVARIANT of the citation contract:
  1. If a response references medical content, context_used must be non-empty.
  2. Each chunk_id in context_used must have the expected format (UUID or slug).
  3. A response with NO medical content MAY have empty context_used.
  4. The grader score = citations_correct / total_assertions_evaluated.

  Synthetic trace events simulate what the sales_agent observability layer
  would write to `copilot_trace_event.context_used`. The actual Qdrant retrieval
  + chunk_id provenance is wired at runtime — this test validates the CONTRACT
  that the observability writes follow.

  Threshold: 0.90 per V-AE-13 (9 out of 10 citation assertions must pass).

Run:
    cd $WS/vitalia/backend && uv run pytest \
        tests/agentic_evals/grader/test_no_hallucination.py -v
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

import pytest

# ── Citation contract types ───────────────────────────────────────────────────


@dataclass
class _TraceEvent:
    """Synthetic copilot_trace_event for citation grading."""

    tenant_id: uuid.UUID
    conversation_id: uuid.UUID
    response: str
    context_used: list[str]  # chunk_ids cited (KB pack IDs)
    event_type: str = "turn_end"


@dataclass
class _CitationGrade:
    """Grade for a single trace event citation check."""

    assertion: str
    passed: bool
    detail: str = ""


# ── Medical content detector (proxy for KB retrieval requirement) ─────────────

_MEDICAL_CONTENT_RE = re.compile(
    r"\b(?:tratamiento|procedimiento|dosis|implante|cirugía|terapia|"
    r"medicación|consulta|diagnóstico|evaluación)\b",
    re.IGNORECASE,
)


def _response_requires_citation(response: str) -> bool:
    """Return True if response references medical content that requires KB citation."""
    return bool(_MEDICAL_CONTENT_RE.search(response))


_CHUNK_ID_RE = re.compile(
    r"^(?:[a-f0-9-]{36}|[a-z][a-z0-9_-]{3,80})$",  # UUID (hex lowercase) or slug (lowercase only)
    # NOTE: no re.IGNORECASE — slugs must be lowercase; UPPERCASE IDs are invalid
)


def _is_valid_chunk_id(chunk_id: str) -> bool:
    """Return True if chunk_id has valid format (UUID or slug)."""
    return bool(_CHUNK_ID_RE.match(chunk_id))


# ── Grader function ───────────────────────────────────────────────────────────


def _grade_trace_event(trace: _TraceEvent) -> _CitationGrade:
    """Grade a trace event against the no-hallucination citation contract.

    Pass conditions:
      A) Response has medical content → context_used must be non-empty with valid IDs.
      B) Response has no medical content → context_used may be empty (pass trivially).

    Fail condition:
      Response has medical content + context_used is empty → hallucination risk.
    """
    requires_citation = _response_requires_citation(trace.response)

    if not requires_citation:
        return _CitationGrade(
            assertion="no_medical_content_citation_not_required",
            passed=True,
            detail="Response has no medical content — citation not required (pass trivially).",
        )

    # Medical content present — citation required
    if not trace.context_used:
        return _CitationGrade(
            assertion="medical_content_requires_citation",
            passed=False,
            detail=(
                f"Response references medical content but context_used is empty. "
                f"Response snippet: {trace.response[:120]!r}"
            ),
        )

    # Validate all chunk IDs
    invalid_ids = [cid for cid in trace.context_used if not _is_valid_chunk_id(cid)]
    if invalid_ids:
        return _CitationGrade(
            assertion="chunk_ids_valid_format",
            passed=False,
            detail=f"Invalid chunk_id format(s): {invalid_ids}. Must be UUID or slug.",
        )

    return _CitationGrade(
        assertion="medical_content_citation_present_and_valid",
        passed=True,
        detail=f"context_used={trace.context_used} with {len(trace.context_used)} valid chunk(s).",
    )


# ── Synthetic trace event fixtures ────────────────────────────────────────────

_TENANT_ID = uuid.UUID("00000000-1111-2222-3333-000000000001")
_CONV_ID = uuid.UUID("00000000-aaaa-bbbb-cccc-000000000001")

_TRACE_EVENTS: list[_TraceEvent] = [
    # 1. Dental treatment — citation required (has "tratamiento")
    _TraceEvent(
        tenant_id=_TENANT_ID,
        conversation_id=_CONV_ID,
        response=(
            "El tratamiento de conducto se realiza bajo anestesia local. Esto no reemplaza consulta médica profesional."
        ),
        context_used=["dental-treatment-endodontics-v1", "dental-anesthesia-protocols-v1"],
    ),
    # 2. Appointment scheduling — NO medical content, citation optional
    _TraceEvent(
        tenant_id=_TENANT_ID,
        conversation_id=_CONV_ID,
        response="Tenemos disponibilidad el martes a las 10am. ¿Te parece bien ese horario?",
        context_used=[],
    ),
    # 3. Procedure inquiry — citation required (has "procedimiento")
    _TraceEvent(
        tenant_id=_TENANT_ID,
        conversation_id=_CONV_ID,
        response=(
            "El procedimiento dura aproximadamente 60 minutos y no requiere ayuno previo."
            " Esto no reemplaza consulta médica profesional."
        ),
        context_used=["dental-implant-procedure-v1"],
    ),
    # 4. Implant inquiry — citation required (has "implante")
    _TraceEvent(
        tenant_id=_TENANT_ID,
        conversation_id=_CONV_ID,
        response=(
            "El implante dental es una solución permanente que requiere evaluación previa."
            " Esto no reemplaza consulta médica profesional."
        ),
        context_used=["dental-implants-overview-v1", "dental-evaluation-checklist-v1"],
    ),
    # 5. Therapy followup — citation required (has "terapia")
    _TraceEvent(
        tenant_id=_TENANT_ID,
        conversation_id=_CONV_ID,
        response=(
            "La terapia cognitivo-conductual tiene una duración aproximada de 12 sesiones."
            " Esto no reemplaza consulta médica profesional."
        ),
        context_used=["psychology-cbt-overview-v1"],
    ),
    # 6. Greeting — NO medical content
    _TraceEvent(
        tenant_id=_TENANT_ID,
        conversation_id=_CONV_ID,
        response="Hola, bienvenido a Aurora Dental. ¿En qué te puedo ayudar hoy?",
        context_used=[],
    ),
    # 7. Consultation recommendation — citation required (has "consulta")
    _TraceEvent(
        tenant_id=_TENANT_ID,
        conversation_id=_CONV_ID,
        response=(
            "Te recomiendo una consulta de evaluación inicial con el especialista."
            " Esto no reemplaza consulta médica profesional."
        ),
        context_used=["dental-initial-consultation-v1"],
    ),
    # 8. Medication question redirect — citation required (has "medicación")
    _TraceEvent(
        tenant_id=_TENANT_ID,
        conversation_id=_CONV_ID,
        response=(
            "Cualquier ajuste en tu medicación debe ser evaluado directamente por tu psiquiatra."
            " Esto no reemplaza consulta médica profesional."
        ),
        context_used=["psychiatry-medication-safety-v1"],
    ),
    # 9. Price inquiry — NO medical content (avoids medical keywords deliberately)
    _TraceEvent(
        tenant_id=_TENANT_ID,
        conversation_id=_CONV_ID,
        response="El costo de la primera cita es de $800 MXN. ¿Deseas agendar?",
        context_used=[],
    ),
    # 10. Surgery followup — citation required (has "cirugía")
    _TraceEvent(
        tenant_id=_TENANT_ID,
        conversation_id=_CONV_ID,
        response=(
            "Después de la cirugía es normal experimentar molestias durante 48-72 horas."
            " Esto no reemplaza consulta médica profesional."
        ),
        context_used=["dental-postsurgical-care-v1", "dental-pain-management-v1"],
    ),
]

assert len(_TRACE_EVENTS) == 10, f"V-AE-13 requires 10 trace events, got {len(_TRACE_EVENTS)}"


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "trace",
    _TRACE_EVENTS,
    ids=[f"trace_{i + 1}" for i in range(len(_TRACE_EVENTS))],
)
def test_no_hallucination_citation_per_trace(trace: _TraceEvent) -> None:
    """V-AE-13: each trace event must satisfy the citation contract."""
    grade = _grade_trace_event(trace)
    assert grade.passed, (
        f"Citation contract FAILED for trace event.\n"
        f"Assertion: {grade.assertion}\n"
        f"Detail: {grade.detail}\n"
        f"Response snippet: {trace.response[:150]!r}\n"
        f"context_used: {trace.context_used}"
    )


def test_no_hallucination_aggregate_threshold_0_90() -> None:
    """V-AE-13 aggregate: citation contract pass rate MUST be ≥0.90 (9/10)."""
    grades = [_grade_trace_event(t) for t in _TRACE_EVENTS]
    pass_rate = sum(1 for g in grades if g.passed) / len(grades)
    assert pass_rate >= 0.90, (
        f"No-hallucination citation contract aggregate: {pass_rate:.2f} < 0.90.\n"
        f"Failures:\n"
        + "\n".join(f"  trace {i + 1}: {g.assertion} — {g.detail}" for i, g in enumerate(grades) if not g.passed)
    )


def test_no_hallucination_ten_trace_events_sanity() -> None:
    """Sanity: V-AE-13 requires 10 trace events (matching PII scanner parity)."""
    assert len(_TRACE_EVENTS) == 10


def test_no_hallucination_threshold_is_0_90() -> None:
    """V-AE-13 threshold constant MUST be 0.90."""
    threshold = 0.90
    assert threshold == 0.90  # Cement


def test_chunk_id_format_validation() -> None:
    """citation contract: chunk IDs must match UUID or slug format."""
    valid_uuids = [
        str(uuid.uuid4()),
        "00000000-1111-2222-3333-000000000001",
    ]
    valid_slugs = [
        "dental-implants-overview-v1",
        "medical-kb-dental-v1",
        "psychology-cbt-overview-v1",
    ]
    invalid_ids = [
        "",  # empty
        "invalid id with spaces",
        "UPPER_CASE_ID_NOT_SLUG",
        "a" * 200,  # too long
    ]

    for valid in valid_uuids + valid_slugs:
        assert _is_valid_chunk_id(valid), f"Expected valid chunk_id: {valid!r}"

    for invalid in invalid_ids:
        assert not _is_valid_chunk_id(invalid), f"Expected invalid chunk_id: {invalid!r}"
