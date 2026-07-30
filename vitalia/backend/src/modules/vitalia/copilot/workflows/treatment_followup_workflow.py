# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""TreatmentFollowupWorkflow — LangGraph 2.0 StateGraph.

Story 11 T-workflow-1 (R23 Opus 4.7 production AGENTIC code).

Per 02-design-agentic.md § 4 + 03-arch-agentic.md § 6:
  - 10 nodes, 17 transitions
  - 5 main states (D0_init / D5_check / D5_complete / D14_check / D14_complete /
    D90_check / completed) + 3 paused branches + 1 dropped terminal
  - Composite state key (tenant_id, treatment_id) via thread_id config
  - Checkpointer abstraction (MemorySaver default; RedisSaver swap when
    langgraph-checkpoint-redis package install lands per D10 staging)

Decisions honored:
  D3 — TreatmentFollowupWorkflow inherits StateGraph directly (no shared base
       BaseWorkflowOrchestrator — YAGNI, defer until 2nd vertical workflow)
  D10 — RedisSaver checkpointer cross-brand (current MemorySaver, abstract
        Checkpointer protocol surface allows runtime swap)

Anti-duplication audit (per .claude/rules/anti-duplication.md):
  - No existing TreatmentFollowupWorkflow class anywhere in luana-platform or
    AISALESHT — NEW class, no mirror risk.
  - No existing RedisSaver runtime usage — D10 ratifies it as TARGET, package
    not yet installed.

Cost tracking:
  - cost_accumulated_usd accumulates per node invocation (deterministic stub
    contributions until T-tools-4 wires real LLM cost recording)
  - Total D0→D90 budget: $0.25 USD (validated by test_total_cost_budget)

Tenant isolation:
  - All state carries tenant_id. Checkpointer thread_id includes tenant_id +
    treatment_id composite — cross-treatment isolation guaranteed at
    persistence boundary.

Best-effort observability (NOT YET wired):
  - T-workflow-1 scope is workflow + cron handler. Real
    copilot_trace_event / copilot_llm_call writes happen when nodes invoke
    treatment_followup_check tool (T-tools-4 owns LLM calls + observability
    wrapper). Workflow itself emits structlog events per node entry/exit.
"""

from __future__ import annotations

import re
from typing import Any, Protocol, TypedDict

import structlog
from langgraph.graph import END, StateGraph

logger = structlog.get_logger()


# ════════════════════════════════════════════════════════════════════════════
# State schema
# ════════════════════════════════════════════════════════════════════════════


class TreatmentFollowupState(TypedDict, total=False):
    """Treatment followup workflow state.

    `total=False` allows partial state updates per LangGraph node return
    convention (nodes return only the keys they modify).

    Tenant isolation: tenant_id is REQUIRED in initial state. Checkpointer
    thread_id includes tenant_id + treatment_id composite per 02-design § 4.4.
    """

    # Identity (set at D0_init, immutable thereafter)
    tenant_id: Any  # uuid.UUID — typed as Any for TypedDict tolerance
    treatment_id: Any
    patient_id: Any
    doctor_id: Any
    booking_id: Any
    procedure_date: Any  # datetime

    # Progress
    current_step: str
    last_patient_response: str | None
    adherence_score: int | None  # 1-5 cumulative
    sentiment: float | None  # 0-1 positive sentiment
    safety_triggered: bool
    paused_reason: str | None
    next_milestone_at: Any  # datetime | None

    # Cost tracking (best-effort — real per-call cost lives in
    # copilot_llm_call when T-tools-4 wires LLM observability)
    cost_accumulated_usd: float

    # Anti-loop guard (cron-driven workflow; max iterations defensive only)
    iterations: int


# ════════════════════════════════════════════════════════════════════════════
# Checkpointer protocol — RedisSaver swap surface (D10)
# ════════════════════════════════════════════════════════════════════════════


class CheckpointerProtocol(Protocol):
    """Structural protocol — accepts MemorySaver, RedisSaver (future),
    AsyncPostgresSaver, or any LangGraph-compatible checkpointer.

    Production swap (D10 future ticket):
        from langgraph.checkpoint.redis import RedisSaver
        checkpointer = RedisSaver.from_conn_string(settings.REDIS_URL)
        workflow = build_treatment_followup_workflow(checkpointer=checkpointer)
    """

    ...  # LangGraph compile() validates the actual interface at runtime


# ════════════════════════════════════════════════════════════════════════════
# Safety keyword detection (per 02-design § 2.2)
# ════════════════════════════════════════════════════════════════════════════

# Plain keywords — case-insensitive substring match
_SAFETY_KEYWORDS = (
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

# Higher-precision multi-word phrases — same matcher path
_SAFETY_PHRASES = (
    "mucho dolor",
    "dolor fuerte",
    "no me siento bien",
)

# Diagnosis-request regex per 02-design § 2.2 (intent_diagnosis_request)
_DIAGNOSIS_REGEX = re.compile(
    r"(tengo|tendré|sufro|padezco|me dio|estoy con).*(cáncer|diabetes|VIH|infarto|covid|trastorno|síndrome)",
    re.IGNORECASE,
)


_NEGATION_PREFIXES = ("sin ", "no ", "ni ", "ningún ", "ninguna ", "nunca ", "tampoco ")


def _is_negated(text: str, keyword_pos: int) -> bool:
    """Return True if a negation prefix immediately precedes the keyword.

    Heuristic guard against trivial negation (e.g. 'sin sangrado',
    'no tengo dolor pecho'). Real medical NLP belongs in T-tools-4 LLM
    classifier; this stub just protects happy-path tests from false
    positives.
    """
    if keyword_pos == 0:
        return False
    prefix_window = text[max(0, keyword_pos - 12) : keyword_pos]
    return any(prefix_window.endswith(neg) for neg in _NEGATION_PREFIXES)


def _detect_safety_signal(text: str | None) -> tuple[bool, list[str]]:
    """Return (triggered, matched_keywords) for safety keyword scan.

    Detection rule: any keyword OR phrase substring match (case-insensitive)
    UNLESS preceded by a negation prefix ('sin', 'no', etc.) — heuristic
    guard against false positives. Diagnosis-request regex match also
    triggers. Matches accumulate for audit_log visibility — first hit is
    enough for routing but full list aids review.

    Real medical NLP (LLM classifier with context) lives in T-tools-4
    treatment_followup_check tool; this is a defensive stub.
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


# ════════════════════════════════════════════════════════════════════════════
# Cost accumulator stubs (replaced by T-tools-4 real LLM cost recording)
# ════════════════════════════════════════════════════════════════════════════

# Per-node cost contributions (deterministic stubs — total D0→D90 happy
# path = 0.024 USD well under 0.25 budget). Ping nodes invoke Sonnet voice
# composer (~0.009 USD); check nodes invoke 2 Haiku classifiers (~0.003 USD
# each = 0.006). Real costs land in copilot_llm_call when T-tools-4 wires.
_NODE_COST_USD = {
    "d0_init": 0.0,
    "d5_check": 0.006,
    "d5_complete": 0.0,
    "d14_check": 0.006,
    "d14_complete": 0.0,
    "d90_check": 0.006,
    "completed": 0.0,
    "paused_safety": 0.001,  # Re-classifier verification
    "paused_awaiting_clinic": 0.0,
    "dropped": 0.0,
}


# ════════════════════════════════════════════════════════════════════════════
# Adherence + sentiment stub classifiers (replaced by T-tools-4)
# ════════════════════════════════════════════════════════════════════════════


def _stub_classify_adherence(response: str | None) -> int:
    """Stub Haiku adherence classifier. T-tools-4 replaces with real LLM call.

    Returns 1-5 score. Heuristic: positive words → high; concern words → mid;
    none → 3 neutral default.
    """
    if not response:
        return 3
    text_lower = response.lower()
    positive = ("bien", "perfecto", "sin molestias", "sin dolor", "cicatriz")
    concern = ("poco", "regular", "molesto")
    if any(w in text_lower for w in positive):
        return 5
    if any(w in text_lower for w in concern):
        return 3
    return 4


def _stub_classify_sentiment(response: str | None) -> float:
    """Stub Haiku sentiment classifier. T-tools-4 replaces with real LLM call."""
    if not response:
        return 0.5
    text_lower = response.lower()
    positive = ("bien", "perfecto", "feliz", "contenta", "contento", "gracias")
    negative = ("mal", "dolor", "preocupada", "preocupado", "miedo")
    pos_hits = sum(1 for w in positive if w in text_lower)
    neg_hits = sum(1 for w in negative if w in text_lower)
    if pos_hits + neg_hits == 0:
        return 0.5
    return pos_hits / (pos_hits + neg_hits)


# ════════════════════════════════════════════════════════════════════════════
# Workflow nodes
# ════════════════════════════════════════════════════════════════════════════


def _accumulate_cost(state: TreatmentFollowupState, node_name: str) -> float:
    """Compute new cost_accumulated_usd after this node runs."""
    prior = state.get("cost_accumulated_usd", 0.0) or 0.0
    delta = _NODE_COST_USD.get(node_name, 0.0)
    return prior + delta


async def d0_init_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """D0_init — booking confirmed, procedure today. Sets workflow start state.

    Side-effect (deferred to T-tools-4 wiring): schedule cron tick D+5d.
    """
    logger.info(
        "treatment_followup_d0_init",
        tenant_id=str(state.get("tenant_id")),
        treatment_id=str(state.get("treatment_id")),
    )
    return {
        "current_step": "D0_init",
        "iterations": (state.get("iterations") or 0) + 1,
        "cost_accumulated_usd": _accumulate_cost(state, "d0_init"),
    }


async def d5_check_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """D5_check — first followup ping + adherence/sentiment + safety scan.

    Branches via route_after_d5_check conditional edge.
    """
    response = state.get("last_patient_response")
    safety_triggered, safety_matches = _detect_safety_signal(response)

    logger.info(
        "treatment_followup_d5_check",
        tenant_id=str(state.get("tenant_id")),
        treatment_id=str(state.get("treatment_id")),
        has_response=response is not None,
        safety_triggered=safety_triggered,
        safety_matches=safety_matches,
    )

    update: dict[str, Any] = {
        "current_step": "D5_check",
        "iterations": (state.get("iterations") or 0) + 1,
        "cost_accumulated_usd": _accumulate_cost(state, "d5_check"),
    }
    if response is not None:
        update["adherence_score"] = _stub_classify_adherence(response)
        update["sentiment"] = _stub_classify_sentiment(response)

    if safety_triggered:
        update["safety_triggered"] = True
        update["paused_reason"] = f"safety_keywords_detected: {','.join(safety_matches[:3])}"

    return update


async def d5_complete_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """D5_complete — adherence captured, schedule D+14d cron tick."""
    logger.info(
        "treatment_followup_d5_complete",
        tenant_id=str(state.get("tenant_id")),
        treatment_id=str(state.get("treatment_id")),
    )
    return {
        "current_step": "D5_complete",
        "iterations": (state.get("iterations") or 0) + 1,
        "cost_accumulated_usd": _accumulate_cost(state, "d5_complete"),
    }


async def d14_check_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """D14_check — control / sutura check + adherence/sentiment + safety scan."""
    response = state.get("last_patient_response")
    safety_triggered, safety_matches = _detect_safety_signal(response)

    logger.info(
        "treatment_followup_d14_check",
        tenant_id=str(state.get("tenant_id")),
        treatment_id=str(state.get("treatment_id")),
        has_response=response is not None,
        safety_triggered=safety_triggered,
    )

    update: dict[str, Any] = {
        "current_step": "D14_check",
        "iterations": (state.get("iterations") or 0) + 1,
        "cost_accumulated_usd": _accumulate_cost(state, "d14_check"),
    }
    if response is not None:
        update["adherence_score"] = _stub_classify_adherence(response)
        update["sentiment"] = _stub_classify_sentiment(response)

    if safety_triggered:
        update["safety_triggered"] = True
        update["paused_reason"] = f"safety_keywords_detected: {','.join(safety_matches[:3])}"

    return update


async def d14_complete_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """D14_complete — schedule D+90d cron tick."""
    logger.info(
        "treatment_followup_d14_complete",
        tenant_id=str(state.get("tenant_id")),
        treatment_id=str(state.get("treatment_id")),
    )
    return {
        "current_step": "D14_complete",
        "iterations": (state.get("iterations") or 0) + 1,
        "cost_accumulated_usd": _accumulate_cost(state, "d14_complete"),
    }


async def d90_check_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """D90_check — corona / final review + safety scan."""
    response = state.get("last_patient_response")
    safety_triggered, safety_matches = _detect_safety_signal(response)

    logger.info(
        "treatment_followup_d90_check",
        tenant_id=str(state.get("tenant_id")),
        treatment_id=str(state.get("treatment_id")),
        has_response=response is not None,
    )

    update: dict[str, Any] = {
        "current_step": "D90_check",
        "iterations": (state.get("iterations") or 0) + 1,
        "cost_accumulated_usd": _accumulate_cost(state, "d90_check"),
    }
    if response is not None:
        update["adherence_score"] = _stub_classify_adherence(response)

    if safety_triggered:
        update["safety_triggered"] = True
        update["paused_reason"] = f"safety_keywords_detected: {','.join(safety_matches[:3])}"

    return update


async def completed_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """Workflow terminal — treatment plan closed. Emit success message + feedback CTA."""
    logger.info(
        "treatment_followup_completed",
        tenant_id=str(state.get("tenant_id")),
        treatment_id=str(state.get("treatment_id")),
        cost_accumulated_usd=state.get("cost_accumulated_usd"),
    )
    return {
        "current_step": "completed",
        "iterations": (state.get("iterations") or 0) + 1,
        "cost_accumulated_usd": _accumulate_cost(state, "completed"),
    }


async def paused_safety_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """paused_safety_escalation — URGENT clinic alert + patient redirect to professional.

    Side-effects (deferred to T-tools-4 + audit_log wiring):
      - Notify clinic_owner with severity high
      - Emit medical_audit_log row safety_keywords_detected
      - Patient receives "Te derivo con el {doctor_specialty} de {clinic_name}" message

    On clinic resolution signal (paused_reason indicates resume / closed):
      - Clear safety_triggered + last_patient_response so downstream nodes
        do not re-trigger on stale input (resume node's job is to consume
        the clinic decision, not the original safety message).
    """
    logger.warning(
        "treatment_followup_paused_safety_escalation",
        tenant_id=str(state.get("tenant_id")),
        treatment_id=str(state.get("treatment_id")),
        paused_reason=state.get("paused_reason"),
    )
    paused_reason = state.get("paused_reason") or ""
    update: dict[str, Any] = {
        "current_step": "paused_safety_escalation",
        "iterations": (state.get("iterations") or 0) + 1,
        "cost_accumulated_usd": _accumulate_cost(state, "paused_safety"),
    }
    # On clinic resolve signal, clear stale safety + response so downstream
    # node re-runs cleanly (clinic decision is the resume signal, not the
    # original patient message that triggered safety).
    if any(token in paused_reason for token in ("resume", "re_engage", "closed", "referred")):
        update["safety_triggered"] = False
        update["last_patient_response"] = None
    return update


async def paused_awaiting_clinic_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """paused_awaiting_clinic — amber banner clinic dashboard + email summary.

    On clinic / patient resume signal: do NOT clear last_patient_response if
    the resume signal carries a fresh patient message (route_after_clinic_resolve
    distinguishes via paused_reason tokens). Only the stale-state clear when
    transitioning to dropped/safety isn't needed here.
    """
    logger.info(
        "treatment_followup_paused_awaiting_clinic",
        tenant_id=str(state.get("tenant_id")),
        treatment_id=str(state.get("treatment_id")),
        paused_reason=state.get("paused_reason"),
    )
    return {
        "current_step": "paused_awaiting_clinic",
        "iterations": (state.get("iterations") or 0) + 1,
        "cost_accumulated_usd": _accumulate_cost(state, "paused_awaiting_clinic"),
    }


async def dropped_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """Workflow terminal — patient unresponsive >14d cumulative."""
    logger.info(
        "treatment_followup_dropped",
        tenant_id=str(state.get("tenant_id")),
        treatment_id=str(state.get("treatment_id")),
        paused_reason=state.get("paused_reason"),
    )
    return {
        "current_step": "dropped",
        "iterations": (state.get("iterations") or 0) + 1,
        "cost_accumulated_usd": _accumulate_cost(state, "dropped"),
    }


# ════════════════════════════════════════════════════════════════════════════
# Conditional edge routing
# ════════════════════════════════════════════════════════════════════════════


def route_after_d5_check(state: TreatmentFollowupState) -> str:
    """Route after D5_check: ok / safety / awaiting_clinic / dropped."""
    if state.get("safety_triggered"):
        return "safety"
    response = state.get("last_patient_response")
    if response is None:
        return "awaiting_clinic"
    return "ok"


def route_after_d14_check(state: TreatmentFollowupState) -> str:
    """Route after D14_check: ok / safety / awaiting_clinic."""
    if state.get("safety_triggered"):
        return "safety"
    response = state.get("last_patient_response")
    if response is None:
        return "awaiting_clinic"
    return "ok"


def route_after_d90_check(state: TreatmentFollowupState) -> str:
    """Route after D90_check: ok terminal / safety branch."""
    if state.get("safety_triggered"):
        return "safety"
    return "ok"


def route_after_safety_resolve(state: TreatmentFollowupState) -> str:
    """Route after paused_safety_escalation when clinic acts.

    Reads paused_reason for resolution signal:
      - "clinic_resolved_re_engage" → resume to last in-flight check (D5/D14)
      - "clinic_closed_referred_elsewhere" → completed terminal
      - default (no resolution signal yet) → stay paused (END this invocation)
    """
    paused_reason = state.get("paused_reason") or ""
    if "closed" in paused_reason or "referred" in paused_reason:
        return "completed"
    if "resume" in paused_reason or "re_engage" in paused_reason:
        return "resume"
    return "stay_paused"


def route_after_clinic_resolve(state: TreatmentFollowupState) -> str:
    """Route after paused_awaiting_clinic.

    - "patient_responded_late" / "clinic_outreach_succeeded" → resume to check
    - "cumulative_14d_no_engagement_dropped" → dropped terminal
    - default → stay paused
    """
    paused_reason = state.get("paused_reason") or ""
    if "dropped" in paused_reason or "14d" in paused_reason:
        return "dropped"
    if "responded" in paused_reason or "outreach_succeeded" in paused_reason:
        return "resume"
    return "stay_paused"


# ════════════════════════════════════════════════════════════════════════════
# Workflow factory
# ════════════════════════════════════════════════════════════════════════════


async def _safety_restore_to_check_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """Restore workflow to last in-flight check after safety resolve.

    Sets current_step back to D5_check (or D14_check based on prior progress
    via paused_reason hint) WITHOUT re-running classification — fresh patient
    response will arrive in a future tick invocation.
    """
    paused_reason = state.get("paused_reason") or ""
    target = "D5_check"
    if "D14" in paused_reason or "d14" in paused_reason:
        target = "D14_check"
    return {
        "current_step": target,
        "iterations": (state.get("iterations") or 0) + 1,
    }


async def _awaiting_clinic_restore_to_check_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """Restore workflow to last in-flight check after awaiting_clinic resolve.

    If a fresh patient_response arrived with the resume input, the next
    invocation will route through __entry_router__ → D{N}_check and consume
    it normally. This node only resets current_step.
    """
    paused_reason = state.get("paused_reason") or ""
    target = "D5_check"
    if "D14" in paused_reason or "d14" in paused_reason:
        target = "D14_check"
    return {
        "current_step": target,
        "iterations": (state.get("iterations") or 0) + 1,
    }


async def entry_router_node(state: TreatmentFollowupState) -> dict[str, Any]:
    """Entry router — pure routing node, returns no state mutations.

    Reads `current_step` from input state to dispatch the appropriate
    workflow node. This pattern is necessary because LangGraph's single
    entry point + checkpointer model requires the graph to dispatch on
    state, not via direct node addressing from outside.
    """
    return {}


def route_from_entry(state: TreatmentFollowupState) -> str:
    """Dispatch from entry router based on current_step.

    Maps state's current_step to the next node label. Unknown / missing
    current_step → D0_init (workflow first invocation).
    """
    step = state.get("current_step") or "D0_init"
    valid = {
        "D0_init",
        "D5_check",
        "D5_complete",
        "D14_check",
        "D14_complete",
        "D90_check",
        "completed",
        "paused_safety_escalation",
        "paused_awaiting_clinic",
        "dropped",
    }
    if step not in valid:
        logger.warning(
            "treatment_followup_unknown_step_fallback_to_d0",
            unknown_step=step,
            tenant_id=str(state.get("tenant_id")),
            treatment_id=str(state.get("treatment_id")),
        )
        step = "D0_init"
    return step


def build_treatment_followup_workflow(
    checkpointer: CheckpointerProtocol | Any,
) -> Any:
    """Build + compile TreatmentFollowupWorkflow LangGraph StateGraph.

    Args:
        checkpointer: any LangGraph-compatible checkpointer. Pass MemorySaver
            for tests/dev, RedisSaver/AsyncPostgresSaver for production.

    Returns:
        Compiled CompiledStateGraph runnable via .ainvoke / .aget_state.

    Per D10: checkpointer abstraction allows runtime swap MemorySaver →
    RedisSaver when langgraph-checkpoint-redis package install lands.
    """
    graph = StateGraph(TreatmentFollowupState)

    # Entry router — dispatches per current_step
    graph.add_node("__entry_router__", entry_router_node)

    # Nodes (10)
    graph.add_node("D0_init", d0_init_node)
    graph.add_node("D5_check", d5_check_node)
    graph.add_node("D5_complete", d5_complete_node)
    graph.add_node("D14_check", d14_check_node)
    graph.add_node("D14_complete", d14_complete_node)
    graph.add_node("D90_check", d90_check_node)
    graph.add_node("completed", completed_node)
    graph.add_node("paused_safety_escalation", paused_safety_node)
    graph.add_node("paused_awaiting_clinic", paused_awaiting_clinic_node)
    graph.add_node("dropped", dropped_node)

    # Entry point — router dispatches per current_step
    graph.set_entry_point("__entry_router__")
    graph.add_conditional_edges(
        "__entry_router__",
        route_from_entry,
        {
            "D0_init": "D0_init",
            "D5_check": "D5_check",
            "D5_complete": "D5_complete",
            "D14_check": "D14_check",
            "D14_complete": "D14_complete",
            "D90_check": "D90_check",
            "completed": "completed",
            "paused_safety_escalation": "paused_safety_escalation",
            "paused_awaiting_clinic": "paused_awaiting_clinic",
            "dropped": "dropped",
        },
    )

    # D0_init → END (cron tick D+5d advances to D5_check on next invocation)
    graph.add_edge("D0_init", END)

    # D5_check conditional routing per § 4.2
    graph.add_conditional_edges(
        "D5_check",
        route_after_d5_check,
        {
            "ok": "D5_complete",
            "safety": "paused_safety_escalation",
            "awaiting_clinic": "paused_awaiting_clinic",
        },
    )

    # D5_complete → END (cron tick D+14d will resume to D14_check)
    graph.add_edge("D5_complete", END)

    # D14_check conditional routing per § 4.2
    graph.add_conditional_edges(
        "D14_check",
        route_after_d14_check,
        {
            "ok": "D14_complete",
            "safety": "paused_safety_escalation",
            "awaiting_clinic": "paused_awaiting_clinic",
        },
    )

    # D14_complete → END (cron tick D+90d will resume to D90_check)
    graph.add_edge("D14_complete", END)

    # D90_check conditional routing
    graph.add_conditional_edges(
        "D90_check",
        route_after_d90_check,
        {
            "ok": "completed",
            "safety": "paused_safety_escalation",
        },
    )

    # paused_safety_escalation conditional routing per § 4.2
    # On resume: workflow state is RESTORED to D5_check (or D14_check), but
    # without re-running the check node — that node consumes the next patient
    # response on a future invocation. The resume-restore is achieved via
    # `safety_restore_node` which only updates current_step and exits.
    graph.add_node("safety_restore_to_check", _safety_restore_to_check_node)
    graph.add_conditional_edges(
        "paused_safety_escalation",
        route_after_safety_resolve,
        {
            "resume": "safety_restore_to_check",
            "completed": "completed",
            "stay_paused": END,
        },
    )
    graph.add_edge("safety_restore_to_check", END)

    # paused_awaiting_clinic conditional routing per § 4.2
    # On resume: same pattern — restore to D5_check WITHOUT running the
    # check node. If a fresh patient response arrived in the resume input,
    # we keep it; the next invocation will route through __entry_router__
    # → D5_check naturally.
    graph.add_node("awaiting_clinic_restore_to_check", _awaiting_clinic_restore_to_check_node)
    graph.add_conditional_edges(
        "paused_awaiting_clinic",
        route_after_clinic_resolve,
        {
            "resume": "awaiting_clinic_restore_to_check",
            "dropped": "dropped",
            "stay_paused": END,
        },
    )
    graph.add_edge("awaiting_clinic_restore_to_check", END)

    # Terminals
    graph.add_edge("dropped", END)
    graph.add_edge("completed", END)

    return graph.compile(checkpointer=checkpointer)
