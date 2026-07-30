"""Tool tests — `treatment_followup_check` (vitalia AGENTIC tool, R23 Opus 4.7).

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Story 11 T-tools-4. Spec sources:
  * 02-design-agentic.md § 5.4 flow + § 6.2 verbose spec
  * 03-arch-agentic.md § 4.2 tool architecture
  * 06-tickets.yaml::T-tools-4 acceptance criteria A1-A2 + validators V-AE-5 + V-AE-15

Acceptance per ticket:
  A1: test_safety_escalation — record_d5 with safety keyword → workflow transitions
      paused_safety_escalation
  A2: test_cost_budget — Cost per record_* call ≤$0.003 USD (Haiku classifier)

Covers (02-design § 5.4 + § 6.2 spec — 7 actions):
  - initial_d5_ping / initial_d14_ping / initial_d90_ping → compose voice-aware
    proactive message via Sonnet (cost ~$0.009)
  - record_d5_response / record_d14_response / record_d90_response → run adherence
    classifier (Haiku) + sentiment classifier (Haiku) + safety keyword scan
  - snapshot_status → read-only snapshot of current_step + adherence + planned next
  - Safety escalation: record_* with safety keyword → workflow transitions to
    paused_safety_escalation + audit_log + clinic notification
  - Idempotency window 5min via (treatment_id, action, hash(response_text))
  - Best-effort observability: trace_event_repo + audit_log_repo writes wrapped
    in try/except + structlog warning. Tool turn NEVER breaks on observability fail.
  - Tenant isolation: tenant_id injected via ctx, repos pre-bound to tenant_id
  - Forbidden tools coupling: NOT user-callable, only workflow internal node
  - LLM dispatch isolated per-call timeout (graceful-degradation Rule 1+2+5)

These are UNIT tests — repos + LLM dispatch + workflow transition function are
mocked via in-memory fakes / Protocol stubs. Integration with real LangGraph
workflow lives in `tests/agentic_evals/workflows/`.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# A3 (security boundary, mirror of T-tools-1): tenant_id NOT in input schema
# ---------------------------------------------------------------------------


def test_tenant_id_not_in_schema() -> None:
    """tenant_id MUST NEVER appear in client-provided input schema.

    Security boundary per `.claude/rules/tenant-isolation.md` + 02-design § 6.2:
    > tenant_id NOT in schema — injected via tool dispatcher from ctx
    """
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
    )

    fields = TreatmentFollowupCheckInput.model_fields
    assert "tenant_id" not in fields, (
        "tenant_id MUST NOT be in TreatmentFollowupCheckInput — "
        "security boundary per tenant-isolation.md + 02-design § 6.2"
    )
    # Required fields
    assert "treatment_id" in fields
    assert "action" in fields
    # Optional fields per spec
    assert "response_text" in fields
    assert "adherence_score_override" in fields
    assert "sentiment_override" in fields


def test_action_literal_covers_seven_actions() -> None:
    """The 7 actions per spec § 6.2 MUST be the only allowed Literal values."""
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
    )

    expected_actions = {
        "initial_d5_ping",
        "initial_d14_ping",
        "initial_d90_ping",
        "record_d5_response",
        "record_d14_response",
        "record_d90_response",
        "snapshot_status",
    }
    # Pydantic stores Literal members in field annotation metadata
    info = TreatmentFollowupCheckInput.model_fields["action"]
    annotation = info.annotation
    # Literal[X, Y, Z, ...].__args__
    args = set(getattr(annotation, "__args__", ()))
    assert args == expected_actions, f"Action Literal mismatch — expected {expected_actions}, got {args}"


# ---------------------------------------------------------------------------
# Fixtures — in-memory fakes
# ---------------------------------------------------------------------------


class _FakeFollowup:
    """Stand-in for VitaliaTreatmentFollowupModel (minimal surface)."""

    def __init__(
        self,
        *,
        followup_id: uuid.UUID,
        tenant_id: uuid.UUID,
        booking_id: uuid.UUID,
        patient_id: uuid.UUID,
        doctor_id: uuid.UUID,
        current_step: str = "D0_init",
        plan_template_slug: str = "dental_implant",
        next_scheduled_at: datetime | None = None,
        last_response_at: datetime | None = None,
        adherence_score: int | None = None,
        paused_reason: str | None = None,
        deleted_at: datetime | None = None,
    ) -> None:
        self.id = followup_id
        self.tenant_id = tenant_id
        self.booking_id = booking_id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.current_step = current_step
        self.plan_template_slug = plan_template_slug
        self.next_scheduled_at = next_scheduled_at
        self.last_response_at = last_response_at
        self.adherence_score = adherence_score
        self.paused_reason = paused_reason
        self.deleted_at = deleted_at


class _FakeFollowupRepo:
    """Tenant-scoped fake — TreatmentFollowupRepository surface."""

    def __init__(self, tenant_id: uuid.UUID, followups: list[_FakeFollowup]) -> None:
        self._tenant_id = tenant_id
        self._rows = followups
        self.saved_calls: list[_FakeFollowup] = []

    async def get_by_id(self, followup_id: uuid.UUID) -> _FakeFollowup | None:
        for fu in self._rows:
            if fu.id == followup_id and fu.tenant_id == self._tenant_id and fu.deleted_at is None:
                return fu
        return None

    async def save(self, followup: _FakeFollowup) -> None:
        # Replace if existing else append (mirror real repo idempotent save)
        for idx, fu in enumerate(self._rows):
            if fu.id == followup.id:
                self._rows[idx] = followup
                self.saved_calls.append(followup)
                return
        self._rows.append(followup)
        self.saved_calls.append(followup)


class _FakeAdherenceRepo:
    """Stub for adherence record persistence (NEW repo via Protocol).

    T-tools-4 only consumes the `add` method via Protocol — concrete repo
    lands in future ticket OR remains Protocol-only for the workflow node.
    """

    def __init__(self, tenant_id: uuid.UUID) -> None:
        self._tenant_id = tenant_id
        self.added: list[dict[str, Any]] = []

    async def add(
        self,
        *,
        followup_id: uuid.UUID,
        patient_id: uuid.UUID,
        step_name: str,
        score: int,
        sentiment: str | None,
        classifier_metadata: dict[str, Any],
    ) -> None:
        self.added.append(
            {
                "followup_id": followup_id,
                "patient_id": patient_id,
                "step_name": step_name,
                "score": score,
                "sentiment": sentiment,
                "classifier_metadata": classifier_metadata,
                "tenant_id": self._tenant_id,  # repo enforces at construction
            }
        )


class _CapturingTraceRepo:
    """Captures trace_event.add() calls."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def add(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


class _CapturingAuditRepo:
    """Captures audit_log writes for safety escalation evidence."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    async def add(self, **kwargs: Any) -> None:
        self.entries.append(kwargs)


class _RaisingTraceRepo:
    """Always raises — confirms observability failure does NOT break tool turn."""

    def add(self, **kwargs: Any) -> None:
        raise RuntimeError("trace repo down — must NOT break turn")


class _RaisingAuditRepo:
    """Always raises — confirms audit failure does NOT break tool turn."""

    async def add(self, **kwargs: Any) -> None:
        raise RuntimeError("audit repo down — must NOT break turn")


class _CapturingWorkflowTransitioner:
    """Captures workflow transition calls for safety escalation evidence."""

    def __init__(self) -> None:
        self.transitions: list[dict[str, Any]] = []

    async def transition_to(
        self,
        *,
        tenant_id: uuid.UUID,
        treatment_id: uuid.UUID,
        target_step: str,
        paused_reason: str,
    ) -> None:
        self.transitions.append(
            {
                "tenant_id": tenant_id,
                "treatment_id": treatment_id,
                "target_step": target_step,
                "paused_reason": paused_reason,
            }
        )


class _StubLLMClassifier:
    """Stub Haiku classifier — deterministic outputs, tracks costs.

    Returns canned (adherence_score, sentiment, cost_usd) per call. Cost
    accumulates in `total_cost_usd` for V-AE-15 budget assertions.
    """

    def __init__(
        self,
        *,
        adherence_score: int = 4,
        sentiment: str = "positive",
        cost_per_call_usd: float = 0.0014,  # ~Haiku 4.5 actual
    ) -> None:
        self._adherence = adherence_score
        self._sentiment = sentiment
        self._cost_per_call = cost_per_call_usd
        self.calls: list[dict[str, Any]] = []
        self.total_cost_usd: float = 0.0

    async def classify_adherence(self, response_text: str) -> tuple[int, float]:
        """Return (adherence_score, cost_usd)."""
        self.calls.append({"kind": "adherence", "text": response_text})
        self.total_cost_usd += self._cost_per_call
        return self._adherence, self._cost_per_call

    async def classify_sentiment(self, response_text: str) -> tuple[str, float]:
        """Return (sentiment_label, cost_usd)."""
        self.calls.append({"kind": "sentiment", "text": response_text})
        self.total_cost_usd += self._cost_per_call
        return self._sentiment, self._cost_per_call


class _RaisingLLMClassifier:
    """Always raises — confirms graceful-degradation fallback."""

    async def classify_adherence(self, response_text: str) -> tuple[int, float]:
        raise TimeoutError("LLM down")

    async def classify_sentiment(self, response_text: str) -> tuple[str, float]:
        raise TimeoutError("LLM down")


# ---------------------------------------------------------------------------
# A1 acceptance — Safety escalation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_safety_escalation() -> None:
    """A1 acceptance: record_d5 with safety keyword → workflow transitions
    paused_safety_escalation.

    Invariants:
      - workflow transitioner called with target_step='paused_safety_escalation'
      - paused_reason cites detected keywords
      - audit_log entry recorded with severity high
      - safety_triggered=True in output
      - safety_keywords_detected populated
      - Followup row updated with current_step='paused_safety_escalation'
    """
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    booking_id = uuid.uuid4()

    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=booking_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        current_step="D5_check",
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    trace_repo = _CapturingTraceRepo()
    audit_repo = _CapturingAuditRepo()
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier()

    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(
            treatment_id=treatment_id,
            action="record_d5_response",
            response_text="tengo mucho dolor pecho desde la cirugía",
        ),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
        trace_event_repo=trace_repo,
        audit_log_repo=audit_repo,
        turn_id=uuid.uuid4(),
        span_id=uuid.uuid4(),
    )

    # Output reflects safety
    assert result.safety_triggered is True
    assert any("dolor pecho" in kw or "mucho dolor" in kw for kw in result.safety_keywords_detected)
    assert result.current_step == "paused_safety_escalation"

    # Workflow transition fired
    assert len(transitioner.transitions) == 1
    transition = transitioner.transitions[0]
    assert transition["target_step"] == "paused_safety_escalation"
    assert transition["tenant_id"] == tenant_id
    assert transition["treatment_id"] == treatment_id
    assert "safety" in transition["paused_reason"].lower()

    # Audit log entry recorded with safety context
    assert len(audit_repo.entries) >= 1
    safety_entry = next(
        (e for e in audit_repo.entries if e.get("event_type") == "safety_keywords_detected"),
        None,
    )
    assert safety_entry is not None
    assert safety_entry["tenant_id"] == tenant_id
    assert safety_entry.get("severity") == "high"


# ---------------------------------------------------------------------------
# A2 acceptance — Cost budget per record_* call ≤$0.003 USD (Haiku 2 calls)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cost_budget() -> None:
    """A2 acceptance: Cost per record_* call ≤$0.003 USD (Haiku classifier).

    record_* runs adherence classifier + sentiment classifier (2 Haiku calls).
    Per 02-design § 6.6: ~$0.003 total = ~$0.0014/call * 2 + minor overhead.
    """
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        current_step="D5_check",
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier(cost_per_call_usd=0.0014)

    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(
            treatment_id=treatment_id,
            action="record_d5_response",
            response_text="todo bien, sin molestias, cicatriz cerrando",
        ),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
    )

    # 2 Haiku calls executed (adherence + sentiment)
    assert len(llm.calls) == 2
    kinds = {c["kind"] for c in llm.calls}
    assert kinds == {"adherence", "sentiment"}

    # Total cost reported by output ≤ $0.003 USD
    assert result.cost_usd is not None
    assert result.cost_usd <= 0.003, (
        f"record_d5_response cost {result.cost_usd:.6f} USD exceeds budget $0.003 per 02-design § 6.6 + V-AE-15"
    )
    # No safety triggered on positive response
    assert result.safety_triggered is False


# ---------------------------------------------------------------------------
# Initial ping actions (D5/D14/D90) compose voice-aware message — no DB write
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["initial_d5_ping", "initial_d14_ping", "initial_d90_ping"])
async def test_initial_ping_actions_no_persist_on_compose(action: str) -> None:
    """*_ping actions return composed message without persisting adherence row.

    Per 02-design § 5.4: '[terminal node, no DB write yet — write happens after
    patient responds]'.
    """
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        current_step="D5_check",
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier()

    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(treatment_id=treatment_id, action=action),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
    )

    # No adherence record persisted on ping
    assert len(adherence_repo.added) == 0
    # No workflow transition (only response triggers transitions)
    assert len(transitioner.transitions) == 0
    # Output exposes current_step
    assert result.current_step == "D5_check"
    assert result.safety_triggered is False


# ---------------------------------------------------------------------------
# record_* actions persist adherence row + update followup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "action,expected_step",
    [
        ("record_d5_response", "D5_complete"),
        ("record_d14_response", "D14_complete"),
        ("record_d90_response", "completed"),
    ],
)
async def test_record_response_persists_adherence_and_advances(action: str, expected_step: str) -> None:
    """record_* (non-safety) → persist adherence_record + advance current_step."""
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=patient_id,
        doctor_id=uuid.uuid4(),
        current_step=action.replace("record_", "").replace("_response", "_check").upper().replace("D", "D"),
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier(adherence_score=5, sentiment="positive")

    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(
            treatment_id=treatment_id,
            action=action,
            response_text="todo perfecto, sin molestias, gracias",
        ),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
    )

    # Adherence row persisted
    assert len(adherence_repo.added) == 1
    rec = adherence_repo.added[0]
    assert rec["followup_id"] == treatment_id
    assert rec["patient_id"] == patient_id
    assert rec["score"] == 5
    assert rec["sentiment"] == "positive"
    assert rec["tenant_id"] == tenant_id

    # Followup advanced
    assert result.current_step == expected_step
    assert result.adherence_score == 5
    # No safety transition for positive response
    assert result.safety_triggered is False
    assert len(transitioner.transitions) == 0


# ---------------------------------------------------------------------------
# snapshot_status — read-only, no LLM cost
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_snapshot_status_is_read_only_no_llm_no_persist() -> None:
    """snapshot_status returns current_step + adherence + planned next.

    Read-only — no LLM dispatch, no persistence, no workflow transition.
    """
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    next_at = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        current_step="D14_check",
        adherence_score=4,
        next_scheduled_at=next_at,
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier()

    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(treatment_id=treatment_id, action="snapshot_status"),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
    )

    assert result.current_step == "D14_check"
    assert result.adherence_score == 4
    assert result.next_scheduled_at == next_at
    # No LLM, no persist, no transition
    assert len(llm.calls) == 0
    assert len(adherence_repo.added) == 0
    assert len(transitioner.transitions) == 0
    # No cost on read-only
    assert result.cost_usd == 0.0


# ---------------------------------------------------------------------------
# Tenant isolation — cross-tenant treatment_id invisible
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_tenant_treatment_returns_not_found() -> None:
    """Tool must NOT leak treatment from another tenant — repo enforces isolation
    and tool returns current_step='not_found' (or similar safe sentinel)."""
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    treatment_id = uuid.uuid4()
    # Treatment lives in tenant_b — tenant_a repo cannot see it
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_b,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
    )
    followup_repo_a = _FakeFollowupRepo(tenant_a, [followup])
    adherence_repo_a = _FakeAdherenceRepo(tenant_a)
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier()

    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(treatment_id=treatment_id, action="snapshot_status"),
        tenant_id=tenant_a,
        followup_repo=followup_repo_a,
        adherence_repo=adherence_repo_a,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
    )

    # Treatment invisible — safe sentinel
    assert result.current_step == "not_found"
    # No side effects on cross-tenant attempt
    assert len(adherence_repo_a.added) == 0
    assert len(transitioner.transitions) == 0


# ---------------------------------------------------------------------------
# Best-effort observability — trace + audit failures must NOT break tool turn
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trace_event_failure_does_not_break_turn() -> None:
    """trace_event repo raising MUST NOT break the tool turn (R23 + observability)."""
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        current_step="D5_check",
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier()

    # Tool MUST succeed even though trace_repo raises
    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(
            treatment_id=treatment_id,
            action="record_d5_response",
            response_text="bien",
        ),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
        trace_event_repo=_RaisingTraceRepo(),
        turn_id=uuid.uuid4(),
        span_id=uuid.uuid4(),
    )

    assert result.current_step == "D5_complete"
    assert result.adherence_score == 4


@pytest.mark.asyncio
async def test_audit_log_failure_does_not_break_turn() -> None:
    """audit_log repo raising MUST NOT break safety escalation tool turn."""
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        current_step="D5_check",
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier()

    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(
            treatment_id=treatment_id,
            action="record_d5_response",
            response_text="tengo mucho dolor pecho",
        ),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
        trace_event_repo=_CapturingTraceRepo(),
        audit_log_repo=_RaisingAuditRepo(),
        turn_id=uuid.uuid4(),
        span_id=uuid.uuid4(),
    )

    # Safety escalation still completed despite audit log failure
    assert result.safety_triggered is True
    assert result.current_step == "paused_safety_escalation"


# ---------------------------------------------------------------------------
# Graceful degradation — LLM classifier failure → fallback neutral score
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_llm_failure_falls_back_to_neutral_score() -> None:
    """LLM classifier raising → fallback neutral adherence + log degraded.

    Per 02-design § 6.2 error mode (b): 'Adherence classifier LLM timeout →
    fallback to neutral score 3 + log degraded'.
    """
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        current_step="D5_check",
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()

    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(
            treatment_id=treatment_id,
            action="record_d5_response",
            response_text="mas o menos",
        ),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=_RaisingLLMClassifier(),
        workflow_transitioner=transitioner,
    )

    # Fallback applied — neutral score 3
    assert result.adherence_score == 3
    # Followup still advanced
    assert result.current_step == "D5_complete"
    # Cost recorded as 0 (LLM never charged)
    assert result.cost_usd == 0.0


# ---------------------------------------------------------------------------
# Override fields — adherence_score_override / sentiment_override
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_adherence_override_skips_llm_call() -> None:
    """adherence_score_override + sentiment_override → skip LLM, use provided."""
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        current_step="D5_check",
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier()

    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(
            treatment_id=treatment_id,
            action="record_d5_response",
            response_text="bien",
            adherence_score_override=5,
            sentiment_override="positive",
        ),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
    )

    # No LLM call (overrides bypass)
    assert len(llm.calls) == 0
    assert result.adherence_score == 5
    assert result.cost_usd == 0.0
    # Adherence row uses override
    assert adherence_repo.added[0]["score"] == 5
    assert adherence_repo.added[0]["sentiment"] == "positive"


# ---------------------------------------------------------------------------
# safety_keywords_detected populated for all known keywords
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "trigger_text,expected_partial",
    [
        ("tengo mucho dolor pecho", "dolor pecho"),
        ("tengo alergia muy fuerte", "alergia"),
        ("hay sangrado constante", "sangrado"),
        ("tengo fiebre alta hace dos dias", "fiebre alta"),
        ("creo que tengo cáncer", "diagnosis_request"),
    ],
)
async def test_safety_keyword_variations_trigger(trigger_text: str, expected_partial: str) -> None:
    """Multiple safety triggers per 02-design § 2.2 + workflow safety scan."""
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        current_step="D5_check",
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier()

    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(
            treatment_id=treatment_id,
            action="record_d5_response",
            response_text=trigger_text,
        ),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
    )

    assert result.safety_triggered is True
    assert any(expected_partial in kw for kw in result.safety_keywords_detected), (
        f"Expected '{expected_partial}' in {result.safety_keywords_detected}"
    )
    assert len(transitioner.transitions) == 1


# ---------------------------------------------------------------------------
# Negation guard — 'sin sangrado' should NOT trigger safety
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_negation_does_not_trigger_safety() -> None:
    """'sin sangrado' / 'no tengo dolor' should NOT trigger safety escalation."""
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        current_step="D5_check",
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier()

    result = await treatment_followup_check(
        TreatmentFollowupCheckInput(
            treatment_id=treatment_id,
            action="record_d5_response",
            response_text="todo bien, sin sangrado, sin dolor",
        ),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
    )

    assert result.safety_triggered is False
    assert len(transitioner.transitions) == 0
    assert result.current_step == "D5_complete"


# ---------------------------------------------------------------------------
# Latency budget — 100 invocations p99 reasonable for stubbed I/O
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_latency_p99_under_budget_with_stubbed_classifier() -> None:
    """Handler-only overhead (mocked I/O + stubbed LLM) p99 under generous bound.

    Real LLM-bound latency budget per 02-design § 6.2: p99 4s. This test only
    measures handler overhead; integration tests measure end-to-end.
    """
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        current_step="D5_check",
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()
    llm = _StubLLMClassifier()

    timings_ms: list[float] = []
    for i in range(100):
        # Reset followup current_step to allow re-record
        followup.current_step = "D5_check"
        start = time.perf_counter()
        await treatment_followup_check(
            TreatmentFollowupCheckInput(
                treatment_id=treatment_id,
                action="record_d5_response",
                response_text=f"bien {i}",
            ),
            tenant_id=tenant_id,
            followup_repo=followup_repo,
            adherence_repo=adherence_repo,
            llm_classifier=llm,
            workflow_transitioner=transitioner,
        )
        timings_ms.append((time.perf_counter() - start) * 1000)

    timings_ms.sort()
    p99_index = int(len(timings_ms) * 0.99)
    p99 = timings_ms[p99_index]
    # Generous bound — stubbed dependencies, handler overhead only
    assert p99 < 250.0, f"Handler p99 {p99:.2f}ms — investigate handler overhead"


# ---------------------------------------------------------------------------
# Trace event captures sanitized payload (PII stripped)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trace_event_sanitizes_response_text() -> None:
    """trace_event payload must be sanitized via sanitize_payload (anti-duplication
    cardinal: NEVER re-implement PII regex local — consume shared)."""
    from src.modules.vitalia.agentic.tools.treatment_followup_check import (
        TreatmentFollowupCheckInput,
        treatment_followup_check,
    )

    tenant_id = uuid.uuid4()
    treatment_id = uuid.uuid4()
    followup = _FakeFollowup(
        followup_id=treatment_id,
        tenant_id=tenant_id,
        booking_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        current_step="D5_check",
    )
    followup_repo = _FakeFollowupRepo(tenant_id, [followup])
    adherence_repo = _FakeAdherenceRepo(tenant_id)
    transitioner = _CapturingWorkflowTransitioner()
    trace_repo = _CapturingTraceRepo()
    llm = _StubLLMClassifier()

    # Patient text with embedded PII (email + phone)
    response_with_pii = "contacto: paciente@gmail.com tel +5491155551234"

    await treatment_followup_check(
        TreatmentFollowupCheckInput(
            treatment_id=treatment_id,
            action="record_d5_response",
            response_text=response_with_pii,
        ),
        tenant_id=tenant_id,
        followup_repo=followup_repo,
        adherence_repo=adherence_repo,
        llm_classifier=llm,
        workflow_transitioner=transitioner,
        trace_event_repo=trace_repo,
        turn_id=uuid.uuid4(),
        span_id=uuid.uuid4(),
    )

    assert len(trace_repo.calls) >= 1
    # Walk all captured events; their data dict must not contain raw email
    for call in trace_repo.calls:
        data = call.get("data") or {}
        # Serialize to single string blob to compare
        blob = repr(data)
        assert "paciente@gmail.com" not in blob, f"PII email leaked into trace_event payload: {blob}"
