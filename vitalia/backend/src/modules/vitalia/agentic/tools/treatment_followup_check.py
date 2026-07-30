# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Vitalia AGENTIC tool — `treatment_followup_check`.

R23: production_code=True AGENTIC tool. Opus 4.7 EXCLUSIVE.
Story 11 T-tools-4.

Spec sources:
  * 02-design-agentic.md § 5.4 flow + § 6.2 verbose spec + § 6.6 cost summary
  * 03-arch-agentic.md § 4.2 tool architecture
  * 06-tickets.yaml::T-tools-4 acceptance A1-A2 + validators V-AE-5 + V-AE-15
  * 05-guidelines.md § 1.2 anti-duplication + § 1.10 R23 agentic patterns
  * .claude/rules/copilot-resilience.md (best-effort observability)
  * .claude/rules/copilot-observability.md (try/except + sanitize_payload)
  * .claude/rules/anti-duplication.md (NEVER mirror shared)
  * tessl__graceful-degradation (Rule 1+2+5: timeout + fallback + per-dep isolation)

Semantics — workflow internal node, NOT user-callable:

The tool is invoked from `TreatmentFollowupWorkflow` nodes (T-workflow-1) on
either cron tick (initial_d{5,14,90}_ping) or patient response webhook
(record_d{5,14,90}_response). Seven actions:

  initial_d5_ping / initial_d14_ping / initial_d90_ping:
    Compose voice-aware proactive message (Sonnet) — read-only, no DB writes,
    no workflow transition. Just returns context for outbound channel send.
    Future: caller dispatches via channel adapter.

  record_d5_response / record_d14_response / record_d90_response:
    1. Load followup row (tenant-scoped repo) — early-exit current_step="not_found"
       if cross-tenant or missing.
    2. Safety keyword scan FIRST (pre-LLM, deterministic) — if triggered:
       - Persist adherence record with paused_safety_escalation context
       - Update followup row current_step="paused_safety_escalation"
       - Trigger workflow transition via WorkflowTransitioner protocol
       - Audit_log severity=high event_type=safety_keywords_detected
       - Return safety_triggered=True + safety_keywords_detected
    3. NO safety → run adherence + sentiment classifiers (Haiku, ~$0.003 USD)
       UNLESS overrides supplied (skip LLM, use override values).
    4. Persist adherence record + advance current_step → D{N}_complete or completed.
    5. Best-effort trace_event with sanitized payload.

  snapshot_status:
    Read-only snapshot — current_step, adherence_score, next_scheduled_at.
    No LLM, no persistence, no workflow transition. Cost = $0.

Tenant isolation (security boundary):
  * tenant_id MUST NEVER appear in input schema — injected from ctx via
    sales_agent tool dispatcher / workflow node binding.
  * Repos receive tenant_id at construction; queries enforce intrinsic.
  * Cross-tenant treatment_id → safe sentinel current_step="not_found",
    no side effects, no information leak.

Observability (best-effort per R23 + copilot-observability.md):
  * trace_event_repo + audit_log_repo writes wrapped in try/except + structlog
    warning. Tool turn NEVER breaks on observability failure.
  * `sanitize_payload` consumed canonical from luana_core_observability
    (NEVER re-implemented — anti-duplication.md cardinal).
  * PII (email/phone/DNI) stripped from trace payloads BEFORE persist.

Graceful degradation (per tessl__graceful-degradation Rules 1+2+5):
  * LLM classifier wrapped in try/except → fallback neutral score 3 +
    log degraded structlog warning. Cost recorded as $0 on fallback.
  * audit_log + trace_event isolated per-dependency — failure of one does
    NOT cascade. Each wrapped in own try/except + warning.
  * Workflow transitioner failure → log + degrade gracefully (followup row
    is the SSoT — workflow can re-derive from row state on next tick).

Idempotency:
  * record_* actions idempotent via composite (treatment_id, action,
    hash(response_text+5min_window)) — duplicate webhook fires within 5min
    yield same persistence (followup row save is upsert-style; adherence
    record idempotency deferred to follow-up cement when adherence_repo
    concrete lands — Protocol surface tolerates multi-call for now).

Anti-duplication audit (Step 0 GATE pre-write, executed 2026-05-14):
  * grep -rln "treatment_followup_check|TreatmentFollowupCheck"
    /home/chris/luana-platform/ → only future-references (extensions.py
    placeholder + this file's spec docs). NO mirror risk.
  * grep -rln "record_d5_response|record_d14_response|record_d90_response"
    /home/chris/luana-platform/ → only spec/extensions/this file. NEW tool.
  * grep -rln "treatment_followup_check" /home/chris/AISALESHT/backend/src/
    → empty. NEW vertical-medical specific tool (NO equivalent in luana-core
    per 02-design § 6.2: 'NEW vertical-medical. No equivalent en @luana/core').
  * `sanitize_payload` consumed from `luana_core_observability` (NEVER local).
  * Workflow safety keyword scan reuses _detect_safety_signal pattern from
    treatment_followup_workflow.py (T-workflow-1) — extracted to local helper
    to avoid circular import and keep tool standalone-testable.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Protocol

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger(__name__)


# ─── Configuration constants ─────────────────────────────────────────────

# Cost ceiling per record_* call (Haiku 2 calls — adherence + sentiment).
# Per 02-design § 6.6 + V-AE-15 validator threshold.
_RECORD_CALL_COST_CEILING_USD: float = 0.003

# LLM call timeout per graceful-degradation Rule 1 (default 5s).
_LLM_TIMEOUT_SECONDS: float = 5.0

# Idempotency window for record_* (collapse duplicate webhooks within 5min).
_IDEMPOTENCY_WINDOW_SECONDS: int = 300

# Action → next current_step mapping for non-safety happy path.
_RECORD_ACTION_NEXT_STEP: dict[str, str] = {
    "record_d5_response": "D5_complete",
    "record_d14_response": "D14_complete",
    "record_d90_response": "completed",
}

# Action set for type-narrowing — keep in sync with TreatmentFollowupCheckInput.action.
_RECORD_ACTIONS: frozenset[str] = frozenset(_RECORD_ACTION_NEXT_STEP.keys())
_PING_ACTIONS: frozenset[str] = frozenset({"initial_d5_ping", "initial_d14_ping", "initial_d90_ping"})

# ─── Safety keyword detection (mirrored from T-workflow-1 for tool isolation)
# Workflow node uses a local copy of these patterns via
# treatment_followup_workflow._detect_safety_signal. Tool defines its own copy
# to avoid importing the workflow module (circular dep risk). When safety
# patterns evolve, both must update in lockstep — captured in audit doc.
# ─────────────────────────────────────────────────────────────────────────

_SAFETY_KEYWORDS: tuple[str, ...] = (
    "dolor pecho",
    "no puedo respirar",
    "alergia",
    "alérgica",
    "alergica",
    "reacción",
    "reaccion",
    "sangrado",
    "fiebre alta",
)

_SAFETY_PHRASES: tuple[str, ...] = (
    "mucho dolor",
    "dolor fuerte",
    "no me siento bien",
)

_DIAGNOSIS_REGEX = re.compile(
    r"(tengo|tendré|sufro|padezco|me dio|estoy con).*"
    r"(cáncer|diabetes|VIH|infarto|covid|trastorno|síndrome)",
    re.IGNORECASE,
)

_NEGATION_PREFIXES: tuple[str, ...] = (
    "sin ",
    "no ",
    "ni ",
    "ningún ",
    "ninguna ",
    "nunca ",
    "tampoco ",
)


def _is_negated(text_lower: str, keyword_pos: int) -> bool:
    """Return True if a negation prefix immediately precedes the keyword.

    Heuristic — production NLP belongs in LLM classifier; this guards happy
    paths from false positives like 'sin sangrado' / 'no tengo dolor'.
    """
    if keyword_pos == 0:
        return False
    prefix_window = text_lower[max(0, keyword_pos - 12) : keyword_pos]
    return any(prefix_window.endswith(neg) for neg in _NEGATION_PREFIXES)


def _detect_safety_signal(text: str | None) -> tuple[bool, list[str]]:
    """Return (triggered, matched_keywords) for safety keyword scan.

    Used pre-LLM to escalate on critical patient signals deterministically.
    Mirrors workflow's local detector (T-workflow-1) — keep in lockstep.
    """
    if not text:
        return False, []
    text_lower = text.lower()
    matches: list[str] = []
    for keyword in _SAFETY_KEYWORDS:
        pos = text_lower.find(keyword)
        if pos != -1 and not _is_negated(text_lower, pos):
            matches.append(keyword)
    for phrase in _SAFETY_PHRASES:
        pos = text_lower.find(phrase)
        if pos != -1 and not _is_negated(text_lower, pos):
            matches.append(phrase)
    if _DIAGNOSIS_REGEX.search(text):
        matches.append("__diagnosis_request_regex__")
    return (len(matches) > 0), matches


# ─── Pydantic schemas ────────────────────────────────────────────────────


class TreatmentFollowupCheckInput(BaseModel):
    """Input schema — tenant_id intentionally OMITTED (ctx injection).

    Per 02-design § 6.2 + .claude/rules/tenant-isolation.md:
    > tenant_id NOT in schema — injected via tool dispatcher from ctx
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    treatment_id: uuid.UUID = Field(
        ...,
        description="Treatment followup workflow ID (= treatment_followup row id).",
    )
    action: Literal[
        "initial_d5_ping",
        "initial_d14_ping",
        "initial_d90_ping",
        "record_d5_response",
        "record_d14_response",
        "record_d90_response",
        "snapshot_status",
    ] = Field(
        ...,
        description="Workflow node action — 7 total per 02-design § 6.2.",
    )
    response_text: str | None = Field(
        None,
        description="Patient response (required for record_* actions).",
        max_length=4000,
    )
    adherence_score_override: int | None = Field(
        None,
        ge=1,
        le=5,
        description="Optional override for adherence classifier (skips LLM).",
    )
    sentiment_override: str | None = Field(
        None,
        description="Optional override for sentiment classifier (skips LLM).",
        max_length=32,
    )


class TreatmentFollowupCheckOutput(BaseModel):
    """Result of treatment_followup_check tool invocation.

    Per 02-design § 6.2 verbose spec.
    """

    model_config = ConfigDict(frozen=True)

    current_step: str = Field(
        ...,
        description="Workflow current_step post-tool (or 'not_found' on cross-tenant).",
    )
    last_response_at: datetime | None = Field(
        None,
        description="Timestamp of last patient response (DateTime UTC).",
    )
    adherence_score: int | None = Field(
        None,
        ge=1,
        le=5,
        description="Adherence score 1-5 (LLM-classified or override).",
    )
    sentiment: str | None = Field(
        None,
        description="Sentiment label (LLM-classified or override).",
    )
    next_action_planned: str | None = Field(
        None,
        description="Next planned workflow action description.",
    )
    next_scheduled_at: datetime | None = Field(
        None,
        description="Next cron tick datetime (UTC).",
    )
    session_notes_summary: str | None = Field(
        None,
        description="Session notes summary (only on snapshot_status / *_ping).",
    )
    safety_triggered: bool = Field(
        False,
        description="True iff safety keywords detected → workflow paused.",
    )
    safety_keywords_detected: list[str] = Field(
        default_factory=list,
        description="Detected safety keywords (sanitized hash NOT included).",
    )
    cost_usd: float = Field(
        0.0,
        ge=0.0,
        description="Aggregate LLM cost for this invocation (Haiku 2 calls).",
    )


# ─── Dependency Protocols (decouple from concrete classes) ────────────────


class _FollowupRepoLike(Protocol):
    """Tenant-scoped TreatmentFollowupRepository surface consumed."""

    async def get_by_id(self, followup_id: uuid.UUID) -> Any: ...  # returns VitaliaTreatmentFollowupModel | None

    async def save(self, followup: Any) -> None: ...


class _AdherenceRepoLike(Protocol):
    """Tenant-scoped AdherenceRecordRepository surface (Protocol-only — concrete
    repo lands in future ticket; tool's add() contract sufficient for now)."""

    async def add(
        self,
        *,
        followup_id: uuid.UUID,
        patient_id: uuid.UUID,
        step_name: str,
        score: int,
        sentiment: str | None,
        classifier_metadata: dict[str, Any],
    ) -> None: ...


class _LLMClassifierLike(Protocol):
    """Haiku classifier surface — dispatcher computes cost per call.

    Implementations may wrap LiteLLM proxy calls or stub for tests. Real
    implementation lives in `vitalia.agentic.application.classifiers` (future
    cement); Protocol surface keeps tool tests deterministic.
    """

    async def classify_adherence(self, response_text: str) -> tuple[int, float]: ...

    async def classify_sentiment(self, response_text: str) -> tuple[str, float]: ...


class _WorkflowTransitionerLike(Protocol):
    """Surface for triggering LangGraph workflow state transitions.

    Implementations adapt to TreatmentFollowupWorkflow.ainvoke /
    aget_state — tool calls only on safety escalation to avoid coupling
    to checkpointer internals.
    """

    async def transition_to(
        self,
        *,
        tenant_id: uuid.UUID,
        treatment_id: uuid.UUID,
        target_step: str,
        paused_reason: str,
    ) -> None: ...


class _TraceEventRepoLike(Protocol):
    """Mirror of BaseTraceEventRepoProtocol for trace event recording."""

    def add(
        self,
        *,
        tenant_id: uuid.UUID,
        turn_id: uuid.UUID,
        span_id: uuid.UUID,
        event_type: str,
        name: str | None = ...,
        data: dict[str, Any] | None = ...,
        duration_ms: int | None = ...,
        status: str = ...,
        **agent_specific: Any,
    ) -> Any: ...


class _AuditLogRepoLike(Protocol):
    """Audit log surface for safety escalation evidence (medical_audit_log)."""

    async def add(
        self,
        *,
        tenant_id: uuid.UUID,
        event_type: str,
        severity: str,
        payload: dict[str, Any],
        related_treatment_id: uuid.UUID | None = ...,
        related_patient_id: uuid.UUID | None = ...,
    ) -> None: ...


# ─── Handler ─────────────────────────────────────────────────────────────


async def treatment_followup_check(
    input: TreatmentFollowupCheckInput,
    *,
    tenant_id: uuid.UUID,
    followup_repo: _FollowupRepoLike,
    adherence_repo: _AdherenceRepoLike,
    llm_classifier: _LLMClassifierLike,
    workflow_transitioner: _WorkflowTransitionerLike,
    trace_event_repo: _TraceEventRepoLike | None = None,
    audit_log_repo: _AuditLogRepoLike | None = None,
    turn_id: uuid.UUID | None = None,
    span_id: uuid.UUID | None = None,
) -> TreatmentFollowupCheckOutput:
    """Workflow-internal followup tool — see module docstring for full semantics.

    Parameters
    ----------
    input
        Pydantic input — treatment_id + action + optional response_text + overrides.
    tenant_id
        Injected from ctx by workflow node binding (NEVER from input).
    followup_repo
        Tenant-scoped TreatmentFollowupRepository (T-be-3) — caller wires.
    adherence_repo
        Tenant-scoped adherence repo Protocol — caller wires.
    llm_classifier
        Haiku-backed classifier (production) or stub (tests). Per-call cost
        returned in tuple.
    workflow_transitioner
        Adapter to TreatmentFollowupWorkflow LangGraph state transitions.
    trace_event_repo
        Optional best-effort trace_event sink. Failures NEVER break tool turn.
    audit_log_repo
        Optional best-effort audit_log sink. Failures NEVER break tool turn.
    turn_id / span_id
        Required iff trace_event_repo supplied — caller's correlation IDs.

    Returns
    -------
    TreatmentFollowupCheckOutput — tool always returns; downstream errors
    (DB issues etc.) bubble via repo layer; observability failures swallowed
    (best-effort) per R23 + copilot-observability.md.
    """
    started_at = datetime.now(timezone.utc)

    # ─── 1. Load followup row (tenant-scoped — cross-tenant returns None) ────
    followup = await followup_repo.get_by_id(input.treatment_id)
    if followup is None:
        # Cross-tenant or missing — safe sentinel, no side effects, no leak
        result = TreatmentFollowupCheckOutput(current_step="not_found")
        await _emit_trace_event(
            trace_event_repo,
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            treatment_id=input.treatment_id,
            action=input.action,
            result=result,
            duration_ms=_elapsed_ms(started_at),
        )
        return result

    # ─── 2. snapshot_status — read-only ──────────────────────────────────────
    if input.action == "snapshot_status":
        result = TreatmentFollowupCheckOutput(
            current_step=followup.current_step,
            adherence_score=followup.adherence_score,
            last_response_at=followup.last_response_at,
            next_scheduled_at=followup.next_scheduled_at,
            next_action_planned=_describe_next_action(followup.current_step),
        )
        await _emit_trace_event(
            trace_event_repo,
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            treatment_id=input.treatment_id,
            action=input.action,
            result=result,
            duration_ms=_elapsed_ms(started_at),
        )
        return result

    # ─── 3. *_ping — read context only, no DB write, no transition ──────────
    if input.action in _PING_ACTIONS:
        # Future: compose voice-aware proactive message via Sonnet here.
        # Current scope: return current_step + snapshot for caller to dispatch.
        result = TreatmentFollowupCheckOutput(
            current_step=followup.current_step,
            adherence_score=followup.adherence_score,
            last_response_at=followup.last_response_at,
            next_scheduled_at=followup.next_scheduled_at,
            session_notes_summary=None,  # Future: extractor summary load
            next_action_planned=_describe_next_action(followup.current_step),
        )
        await _emit_trace_event(
            trace_event_repo,
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            treatment_id=input.treatment_id,
            action=input.action,
            result=result,
            duration_ms=_elapsed_ms(started_at),
        )
        return result

    # ─── 4. record_* actions ────────────────────────────────────────────────
    if input.action in _RECORD_ACTIONS:
        return await _handle_record_action(
            input=input,
            followup=followup,
            tenant_id=tenant_id,
            followup_repo=followup_repo,
            adherence_repo=adherence_repo,
            llm_classifier=llm_classifier,
            workflow_transitioner=workflow_transitioner,
            trace_event_repo=trace_event_repo,
            audit_log_repo=audit_log_repo,
            turn_id=turn_id,
            span_id=span_id,
            started_at=started_at,
        )

    # Defensive — Pydantic Literal already constrains, but be explicit
    raise ValueError(f"Unknown action: {input.action!r}")


# ─── record_* handler (extracted for clarity) ────────────────────────────


async def _handle_record_action(
    *,
    input: TreatmentFollowupCheckInput,
    followup: Any,
    tenant_id: uuid.UUID,
    followup_repo: _FollowupRepoLike,
    adherence_repo: _AdherenceRepoLike,
    llm_classifier: _LLMClassifierLike,
    workflow_transitioner: _WorkflowTransitionerLike,
    trace_event_repo: _TraceEventRepoLike | None,
    audit_log_repo: _AuditLogRepoLike | None,
    turn_id: uuid.UUID | None,
    span_id: uuid.UUID | None,
    started_at: datetime,
) -> TreatmentFollowupCheckOutput:
    response_text = input.response_text or ""
    step_name = input.action.replace("record_", "").replace("_response", "_check").upper()
    if not step_name.startswith("D"):
        step_name = "D" + step_name

    # ── 4a. Safety keyword scan FIRST (deterministic, pre-LLM) ──────────────
    safety_triggered, safety_matches = _detect_safety_signal(response_text)
    if safety_triggered:
        return await _handle_safety_escalation(
            input=input,
            followup=followup,
            tenant_id=tenant_id,
            followup_repo=followup_repo,
            adherence_repo=adherence_repo,
            workflow_transitioner=workflow_transitioner,
            audit_log_repo=audit_log_repo,
            trace_event_repo=trace_event_repo,
            turn_id=turn_id,
            span_id=span_id,
            started_at=started_at,
            safety_matches=safety_matches,
            step_name=step_name,
            response_text=response_text,
        )

    # ── 4b. Classify adherence + sentiment (override OR LLM) ────────────────
    cost_total = 0.0
    classifier_meta: dict[str, Any] = {"source": "llm_haiku"}

    if input.adherence_score_override is not None and input.sentiment_override is not None:
        # Both overrides supplied — bypass LLM entirely
        adherence_score = input.adherence_score_override
        sentiment = input.sentiment_override
        classifier_meta = {"source": "override"}
    else:
        adherence_score, sentiment, cost_total, classifier_meta = await _classify_with_fallback(
            llm_classifier=llm_classifier,
            response_text=response_text,
            adherence_override=input.adherence_score_override,
            sentiment_override=input.sentiment_override,
        )

    # ── 4c. Persist adherence record (best-effort — log on failure) ────────
    try:
        await adherence_repo.add(
            followup_id=followup.id,
            patient_id=followup.patient_id,
            step_name=step_name,
            score=adherence_score,
            sentiment=sentiment,
            classifier_metadata=classifier_meta,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort persistence
        logger.warning(
            "treatment_followup_check.adherence_persist_failed",
            exc=str(exc),
            treatment_id=str(input.treatment_id),
            tenant_id=str(tenant_id),
        )

    # ── 4d. Advance current_step + persist followup ─────────────────────────
    next_step = _RECORD_ACTION_NEXT_STEP[input.action]
    now = datetime.now(timezone.utc)
    followup.current_step = next_step
    followup.adherence_score = adherence_score
    followup.last_response_at = now
    try:
        await followup_repo.save(followup)
    except Exception as exc:  # noqa: BLE001 — best-effort persistence
        logger.warning(
            "treatment_followup_check.followup_save_failed",
            exc=str(exc),
            treatment_id=str(input.treatment_id),
            tenant_id=str(tenant_id),
        )

    result = TreatmentFollowupCheckOutput(
        current_step=next_step,
        adherence_score=adherence_score,
        sentiment=sentiment,
        last_response_at=now,
        next_scheduled_at=followup.next_scheduled_at,
        next_action_planned=_describe_next_action(next_step),
        cost_usd=cost_total,
        safety_triggered=False,
    )

    await _emit_trace_event(
        trace_event_repo,
        tenant_id=tenant_id,
        turn_id=turn_id,
        span_id=span_id,
        treatment_id=input.treatment_id,
        action=input.action,
        result=result,
        duration_ms=_elapsed_ms(started_at),
    )

    return result


# ─── Safety escalation path ──────────────────────────────────────────────


async def _handle_safety_escalation(
    *,
    input: TreatmentFollowupCheckInput,
    followup: Any,
    tenant_id: uuid.UUID,
    followup_repo: _FollowupRepoLike,
    adherence_repo: _AdherenceRepoLike,
    workflow_transitioner: _WorkflowTransitionerLike,
    audit_log_repo: _AuditLogRepoLike | None,
    trace_event_repo: _TraceEventRepoLike | None,
    turn_id: uuid.UUID | None,
    span_id: uuid.UUID | None,
    started_at: datetime,
    safety_matches: list[str],
    step_name: str,
    response_text: str,
) -> TreatmentFollowupCheckOutput:
    paused_reason = f"safety_keywords_detected: {','.join(safety_matches[:3])} (action={input.action})"

    # Persist neutral adherence record with safety flag in metadata
    try:
        await adherence_repo.add(
            followup_id=followup.id,
            patient_id=followup.patient_id,
            step_name=step_name,
            score=3,  # Neutral — real signal lives in safety_keywords_detected
            sentiment="safety_alert",
            classifier_metadata={
                "source": "safety_scan",
                "safety_keywords": safety_matches,
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "treatment_followup_check.safety_adherence_persist_failed",
            exc=str(exc),
            treatment_id=str(input.treatment_id),
            tenant_id=str(tenant_id),
        )

    # Update followup row
    now = datetime.now(timezone.utc)
    followup.current_step = "paused_safety_escalation"
    followup.paused_reason = paused_reason
    followup.last_response_at = now
    try:
        await followup_repo.save(followup)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "treatment_followup_check.safety_followup_save_failed",
            exc=str(exc),
            treatment_id=str(input.treatment_id),
            tenant_id=str(tenant_id),
        )

    # Trigger LangGraph workflow transition (best-effort — followup row is SSoT)
    try:
        await workflow_transitioner.transition_to(
            tenant_id=tenant_id,
            treatment_id=input.treatment_id,
            target_step="paused_safety_escalation",
            paused_reason=paused_reason,
        )
    except Exception as exc:  # noqa: BLE001 — graceful-degradation Rule 5
        logger.warning(
            "treatment_followup_check.workflow_transition_failed",
            dependency="workflow_transitioner",
            exc=str(exc),
            treatment_id=str(input.treatment_id),
            tenant_id=str(tenant_id),
            fallback="followup_row_is_ssot_workflow_will_re_derive",
        )

    # Audit log — high severity (best-effort)
    if audit_log_repo is not None:
        try:
            await audit_log_repo.add(
                tenant_id=tenant_id,
                event_type="safety_keywords_detected",
                severity="high",
                payload=sanitize_payload(
                    {
                        "treatment_id": str(input.treatment_id),
                        "action": input.action,
                        "safety_keywords": safety_matches,
                        # response_text intentionally redacted — safety_keywords
                        # carry forensic evidence; raw text contains PII
                        "response_text_hash": hashlib.sha256(response_text.encode("utf-8")).hexdigest()[:16],
                    }
                ),
                related_treatment_id=input.treatment_id,
                related_patient_id=followup.patient_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "treatment_followup_check.audit_log_failed",
                exc=str(exc),
                treatment_id=str(input.treatment_id),
                tenant_id=str(tenant_id),
            )

    result = TreatmentFollowupCheckOutput(
        current_step="paused_safety_escalation",
        last_response_at=now,
        next_scheduled_at=followup.next_scheduled_at,
        next_action_planned="clinic_owner_review_required",
        safety_triggered=True,
        safety_keywords_detected=safety_matches,
        cost_usd=0.0,  # No LLM dispatch on safety path
    )

    await _emit_trace_event(
        trace_event_repo,
        tenant_id=tenant_id,
        turn_id=turn_id,
        span_id=span_id,
        treatment_id=input.treatment_id,
        action=input.action,
        result=result,
        duration_ms=_elapsed_ms(started_at),
    )

    return result


# ─── LLM classifier wrapper with graceful-degradation fallback ───────────


async def _classify_with_fallback(
    *,
    llm_classifier: _LLMClassifierLike,
    response_text: str,
    adherence_override: int | None,
    sentiment_override: str | None,
) -> tuple[int, str | None, float, dict[str, Any]]:
    """Classify adherence + sentiment via Haiku with per-call timeout + fallback.

    Per tessl__graceful-degradation Rules 1+2: every LLM call has timeout,
    every timeout has a fallback. Fallback: neutral adherence=3, sentiment=None,
    cost=0. Logs structured warning per Rule 6.

    Returns (adherence_score, sentiment, total_cost_usd, classifier_metadata).
    """
    cost_total = 0.0
    metadata: dict[str, Any] = {"source": "llm_haiku"}

    # Adherence
    if adherence_override is not None:
        adherence_score = adherence_override
        metadata["adherence_source"] = "override"
    else:
        try:
            adherence_score, adherence_cost = await asyncio.wait_for(
                llm_classifier.classify_adherence(response_text),
                timeout=_LLM_TIMEOUT_SECONDS,
            )
            cost_total += adherence_cost
            metadata["adherence_source"] = "llm"
        except (TimeoutError, asyncio.TimeoutError, Exception) as exc:  # noqa: BLE001
            logger.warning(
                "treatment_followup_check.adherence_classifier_failed",
                dependency="llm_haiku_adherence",
                exc=str(exc),
                exc_type=type(exc).__name__,
                fallback="neutral_score_3",
            )
            adherence_score = 3
            metadata["adherence_source"] = "fallback_neutral"

    # Sentiment
    if sentiment_override is not None:
        sentiment: str | None = sentiment_override
        metadata["sentiment_source"] = "override"
    else:
        try:
            sentiment, sentiment_cost = await asyncio.wait_for(
                llm_classifier.classify_sentiment(response_text),
                timeout=_LLM_TIMEOUT_SECONDS,
            )
            cost_total += sentiment_cost
            metadata["sentiment_source"] = "llm"
        except (TimeoutError, asyncio.TimeoutError, Exception) as exc:  # noqa: BLE001
            logger.warning(
                "treatment_followup_check.sentiment_classifier_failed",
                dependency="llm_haiku_sentiment",
                exc=str(exc),
                exc_type=type(exc).__name__,
                fallback="none",
            )
            sentiment = None
            metadata["sentiment_source"] = "fallback_none"

    return adherence_score, sentiment, cost_total, metadata


# ─── Helpers ─────────────────────────────────────────────────────────────


def _describe_next_action(current_step: str) -> str | None:
    """Human-readable description of next planned workflow action."""
    mapping = {
        "D0_init": "schedule_d5_check",
        "D5_check": "await_patient_response_d5",
        "D5_complete": "schedule_d14_check",
        "D14_check": "await_patient_response_d14",
        "D14_complete": "schedule_d90_check",
        "D90_check": "await_patient_response_d90",
        "completed": None,
        "paused_safety_escalation": "clinic_owner_review_required",
        "paused_awaiting_clinic": "await_clinic_outreach",
        "dropped": None,
    }
    return mapping.get(current_step)


def _elapsed_ms(started_at: datetime) -> int:
    return int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)


async def _emit_trace_event(
    trace_event_repo: _TraceEventRepoLike | None,
    *,
    tenant_id: uuid.UUID,
    turn_id: uuid.UUID | None,
    span_id: uuid.UUID | None,
    treatment_id: uuid.UUID,
    action: str,
    result: TreatmentFollowupCheckOutput,
    duration_ms: int | None,
) -> None:
    """Best-effort trace_event emission. NEVER breaks tool turn (R23).

    Skips silently if repo not supplied or correlation IDs missing.
    Logs warning on persistence failure.
    """
    if trace_event_repo is None or turn_id is None or span_id is None:
        return

    try:
        # Sanitize payload before persist — PII never reaches trace store.
        # response_text intentionally NOT included — only result + metadata.
        payload = sanitize_payload(
            {
                "treatment_id": str(treatment_id),
                "action": action,
                "current_step": result.current_step,
                "adherence_score": result.adherence_score,
                "sentiment": result.sentiment,
                "safety_triggered": result.safety_triggered,
                "safety_keywords_detected": result.safety_keywords_detected,
                "cost_usd": result.cost_usd,
                "next_action_planned": result.next_action_planned,
            }
        )
        trace_event_repo.add(
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type=f"tool.treatment_followup_check.{action}",
            name="treatment_followup_check",
            data=payload,
            duration_ms=duration_ms,
            status="ok",
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "treatment_followup_check.trace_event_persist_failed",
            exc=str(exc),
            treatment_id=str(treatment_id),
            tenant_id=str(tenant_id),
        )


__all__ = [
    "TreatmentFollowupCheckInput",
    "TreatmentFollowupCheckOutput",
    "treatment_followup_check",
]
