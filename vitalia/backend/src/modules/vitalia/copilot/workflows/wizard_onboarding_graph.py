# cap: copilot.valeria-wizard-onboarding-agentic
# story-origin: TBD
"""Valeria wizard supervisor LangGraph topology + deepagents extract_subagent.

Per 03-arch-agentic.md § 3.1 + § 7 + tessl__langgraph + tessl__deepagents:

Topology:

```
[START] → supervisor
            ↓ route based on state (decide_next_node)
          ┌─→ extract_subagent  (deepagents sandbox)
          ├─→ slot_question_router
          ├─→ live_preview_router
          ├─→ completion_router
          └─→ END
```

Conditional edges total: every branch reaches END or a named node. Max-iter
guard cap 25 (per copilot-resilience COPILOT_RECURSION_LIMIT) enforced both at
the conditional edge AND defensively inside the supervisor node — defense in
depth against state schema regressions.

Anti-duplication audit (per `.claude/rules/anti-duplication.md`):
  - State machinery (`WizardOnboardingState`) is brand-specific (see state
    module). NO engine equivalent.
  - Subagent middleware semantics come from `deepagents` package — consumed
    as-is, no mirror.
  - Checkpointer protocol is brand-side composition root (file
    `wizard_checkpoint_config.py`). Production uses AsyncPostgresSaver from
    langgraph-checkpoint-postgres (engine-recommended).
  - The 4 wizard tools (extract_tenant_context, confirm_slot,
    simulate_personality, complete_onboarding) live in
    `vitalia/.../copilot/tools/` and are imported here for binding to the
    supervisor — NOT redefined.

Tenant isolation:
  - Every state carries tenant_id (cardinal). Checkpointer thread_id at
    composition root composes (tenant_id, draft_id) so multitenant wizard
    sessions never collide on threads.

Hot-path observability:
  - Each node entry logs structlog event with state["tenant_id"]; LLM calls
    inside the supervisor LLM binding (when wired) go through
    VitaliaCopilotCallbackHandler (anti-duplication subclass) which writes
    copilot_trace_event + copilot_llm_call best-effort.
"""

from __future__ import annotations

from typing import Any, Optional

import structlog
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
    MAX_ITERATIONS,
    WizardOnboardingState,
    has_pending_extraction,
    required_all_confirmed,
)

logger = structlog.get_logger()


# ════════════════════════════════════════════════════════════════════════════
# Node names (kept as module-level constants — supervisor router references)
# ════════════════════════════════════════════════════════════════════════════

NODE_SUPERVISOR: str = "supervisor"
NODE_EXTRACT_SUBAGENT: str = "extract_subagent"
NODE_SLOT_QUESTION: str = "slot_question_router"
NODE_LIVE_PREVIEW: str = "live_preview_router"
NODE_COMPLETION: str = "completion_router"


# ════════════════════════════════════════════════════════════════════════════
# Router decision function (pure)
# ════════════════════════════════════════════════════════════════════════════


def decide_next_node(state: WizardOnboardingState) -> str:
    """Pure router function used by ``add_conditional_edges``.

    Returns the next node KEY which the graph maps to a concrete node. The
    function is pure / deterministic — no I/O, no LLM calls. Same state →
    same routing decision.

    Precedence (order matters — first matching branch wins):

      1. iterations > MAX_ITERATIONS → "end"   (max-iter guard)
      2. task_complete=True          → "end"
      3. has pending extraction      → "extract"
      4. mode unset                  → "ask_slot" (supervisor asks mode first)
      5. required_all_confirmed      → "complete"
      6. default                     → "ask_slot"
    """
    if state.get("iterations", 0) > MAX_ITERATIONS:
        return "end"
    if state.get("task_complete") is True:
        return "end"
    if has_pending_extraction(state):
        return "extract"
    if not state.get("mode"):
        return "ask_slot"
    if required_all_confirmed(state):
        return "complete"
    # Live preview branch — voice_profile_partial set but last sample doesn't reflect it
    voice_profile = state.get("voice_profile_partial")
    voice_samples = state.get("voice_samples") or []
    if voice_profile and not voice_samples:
        return "preview"
    return "ask_slot"


# ════════════════════════════════════════════════════════════════════════════
# Node implementations
# ════════════════════════════════════════════════════════════════════════════


def supervisor_node(state: WizardOnboardingState) -> dict:
    """Supervisor router node — bumps iteration counter + logs.

    Returns a partial state dict (LangGraph convention — never mutate state in
    place). The conditional edge attached to this node is the one that does
    the routing via ``decide_next_node``.
    """
    tenant_id = state.get("tenant_id", "unknown")
    iterations = int(state.get("iterations", 0)) + 1
    logger.info(
        "vitalia.copilot.workflows.wizard.supervisor_tick",
        tenant_id=tenant_id,
        iterations=iterations,
        mode=state.get("mode"),
        task_complete=state.get("task_complete", False),
        has_pending_extraction=has_pending_extraction(state),
    )

    # Defensive max-iter guard at the node level (defense in depth — the
    # conditional edge ALSO checks, but the node-level guard makes the trace
    # honest if a regression somewhere skips the edge guard).
    if iterations > MAX_ITERATIONS:
        return {
            "iterations": iterations,
            "task_complete": True,
            "last_error": {"kind": "max_iter_exceeded", "limit": MAX_ITERATIONS},
        }

    return {"iterations": iterations}


def extract_subagent_node(state: WizardOnboardingState) -> dict:
    """Extract subagent placeholder node — bridges to deepagents at composition.

    For Slice 1, this node is the bridge surface: it consumes
    ``extraction_subagent_input``, runs the sandbox tools (or, when wired to
    the real ``SubAgentMiddleware``, delegates to the deepagents `task` tool),
    and writes a structured ``extraction_subagent_output`` back to the parent
    state.

    Isolation contract (per design § 1.3 + arch § 3.2):
      - INPUT: subagent sees ONLY ``extraction_subagent_input`` + tenant_id
      - OUTPUT: subagent writes ONLY ``extraction_subagent_output``
      - Parent tools NEVER reachable from inside the subagent (see
        ``extract_subagent_tools.py`` for the explicit sandbox list).

    Slice 1 stub: returns an empty extraction output indicating no slots were
    extracted (the real adapter wiring lives in
    ``ExtractTenantContextService``, invoked via the parent
    ``extract_tenant_context`` tool, not via this node directly). The node's
    purpose in the topology is to consume the input bridge key and clear it
    so the supervisor doesn't loop on extraction.
    """
    tenant_id = state.get("tenant_id", "unknown")
    subagent_input = state.get("extraction_subagent_input") or {}
    logger.info(
        "vitalia.copilot.workflows.wizard.extract_subagent_invoked",
        tenant_id=tenant_id,
        sources=[k for k in ("url", "text_content", "audio_url") if subagent_input.get(k)],
    )

    # Stub output — real extraction goes through the service layer + adapters.
    # The subagent's REAL invocation path uses SubAgentMiddleware injected by
    # `create_deep_agent` at composition root (not in this Slice 1 stub).
    output: dict = {
        "slots": {},
        "pii_detected": False,
        "extraction_duration_ms": 0,
        "source_summary": "Slice 1 stub — real adapter calls live in ExtractTenantContextService",
        "warnings": ["extract_subagent_stub_slice_1"],
    }

    return {
        "extraction_subagent_input": None,  # clear the input bridge
        "extraction_subagent_output": output,
    }


def slot_question_node(state: WizardOnboardingState) -> dict:
    """Slot-question router node — picks the next slot to ask the user about.

    Slice 1 stub: bumps no state by itself — the supervisor LLM (when wired)
    is the one that composes the next question. This node logs the decision
    and updates ``slots_pending`` cleanup if needed.
    """
    tenant_id = state.get("tenant_id", "unknown")
    pending = state.get("slots_pending") or []
    logger.info(
        "vitalia.copilot.workflows.wizard.slot_question_tick",
        tenant_id=tenant_id,
        pending=pending,
        confirmed_count=len(state.get("slots_required_confirmed", {})),
    )
    return {}  # supervisor LLM produces the actual question text


def live_preview_node(state: WizardOnboardingState) -> dict:
    """Live preview router node — fires ``simulate_personality`` when applicable.

    Slice 1 stub: the real ``simulate_personality`` invocation happens through
    the supervisor's tool binding (handled at composition). This node logs
    the preview intent.
    """
    tenant_id = state.get("tenant_id", "unknown")
    logger.info(
        "vitalia.copilot.workflows.wizard.live_preview_tick",
        tenant_id=tenant_id,
        has_partial_profile=bool(state.get("voice_profile_partial")),
    )
    return {}


def completion_node(state: WizardOnboardingState) -> dict:
    """Completion router node — fires ``complete_onboarding`` and ends the graph.

    Sets ``task_complete=True`` so the supervisor / decide_next_node routes to
    END on the next pass. The actual ``complete_onboarding`` tool invocation
    happens via the supervisor LLM tool binding at composition — this node
    only flips the termination flag.
    """
    tenant_id = state.get("tenant_id", "unknown")
    logger.info(
        "vitalia.copilot.workflows.wizard.completion_tick",
        tenant_id=tenant_id,
        confirmed_slots=list(state.get("slots_required_confirmed", {}).keys()),
    )
    return {"task_complete": True}


# ════════════════════════════════════════════════════════════════════════════
# Graph builder
# ════════════════════════════════════════════════════════════════════════════


def build_wizard_onboarding_graph(
    *,
    checkpointer: BaseCheckpointSaver,
    supervisor_model: Optional[Any] = None,
) -> Any:
    """Construct + compile the wizard onboarding LangGraph.

    Args:
        checkpointer: Any LangGraph-compatible checkpointer. Production builds
            the durable ``AsyncPostgresSaver`` via the shared engine provider
            ``luana_core_flows.checkpointer.make_durable_checkpointer`` (lifted
            from the deleted brand mirror); tests use ``InMemorySaver``.
        supervisor_model: Optional LLM model identifier or BaseChatModel for
            the supervisor LLM binding (used when the composition root binds
            the 4 wizard tools to a model). Slice 1: not used inside this
            factory — composition root attaches it. Kept as parameter so the
            factory signature matches the production wiring contract.

    Returns:
        Compiled LangGraph ready for ``.invoke()`` / ``.stream()`` /
        ``.ainvoke()``. Checkpointer is wired — supervisor state persists per
        thread_id.

    Topology summary:
        START → supervisor → [extract | ask_slot | preview | complete | END]
        extract → supervisor (loop)
        ask_slot → supervisor (loop)
        preview → supervisor (loop)
        complete → END

        Max-iter guard caps the loop at MAX_ITERATIONS (25).
    """
    graph = StateGraph(WizardOnboardingState)

    # Nodes
    graph.add_node(NODE_SUPERVISOR, supervisor_node)
    graph.add_node(NODE_EXTRACT_SUBAGENT, extract_subagent_node)
    graph.add_node(NODE_SLOT_QUESTION, slot_question_node)
    graph.add_node(NODE_LIVE_PREVIEW, live_preview_node)
    graph.add_node(NODE_COMPLETION, completion_node)

    # Entry
    graph.add_edge(START, NODE_SUPERVISOR)

    # Conditional edge from supervisor — uses pure router function
    graph.add_conditional_edges(
        NODE_SUPERVISOR,
        decide_next_node,
        {
            "extract": NODE_EXTRACT_SUBAGENT,
            "ask_slot": NODE_SLOT_QUESTION,
            "preview": NODE_LIVE_PREVIEW,
            "complete": NODE_COMPLETION,
            "end": END,
        },
    )

    # Sub-nodes loop back to supervisor (so the router decides the next phase)
    graph.add_edge(NODE_EXTRACT_SUBAGENT, NODE_SUPERVISOR)
    graph.add_edge(NODE_SLOT_QUESTION, NODE_SUPERVISOR)
    graph.add_edge(NODE_LIVE_PREVIEW, NODE_SUPERVISOR)
    # Completion node loops back to supervisor too — supervisor sees
    # task_complete=True and routes to END (clean exit through the canonical
    # router branch).
    graph.add_edge(NODE_COMPLETION, NODE_SUPERVISOR)

    compiled = graph.compile(checkpointer=checkpointer)
    return compiled


__all__ = [
    "NODE_COMPLETION",
    "NODE_EXTRACT_SUBAGENT",
    "NODE_LIVE_PREVIEW",
    "NODE_SLOT_QUESTION",
    "NODE_SUPERVISOR",
    "build_wizard_onboarding_graph",
    "completion_node",
    "decide_next_node",
    "extract_subagent_node",
    "live_preview_node",
    "slot_question_node",
    "supervisor_node",
]
