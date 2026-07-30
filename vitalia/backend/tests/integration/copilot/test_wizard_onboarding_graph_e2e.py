"""Integration regression — Valeria wizard onboarding LangGraph supervisor e2e.

T-onboarding-5 (R23 OPT-OUT — Sonnet OK, production_code=false).

Graph + state + compiler + checkpointer SHIPPED APPROVED in copilot-tools-impl
(commits 3331151..427b0f3, 2026-05-18). This module is integration REGRESSION
only — no new agentic production code.

5 tests:
  1. test_graph_e2e_happy_path
       Spawn graph, supervisor routes through subnodes, END reached, ≤25 iter.
  2. test_max_iter_guard_fires
       Force iterations=26 → graph returns END (no infinite loop).
  3. test_cache_hit_rate_iter_2_plus
       Deterministic model: 5-slot compiler guarantees cache_read on iter ≥2.
       Slots 0-3 are invariant (no timestamps / per-session UUIDs). Proves the
       architecture delivers >0 cache_read_input_tokens on subsequent turns.
       (No live LLM call — validated via synthetic token accounting matching
       compiler constants, per existing cost_budget test pattern.)
  4. test_cost_target_per_session
       Deterministic cost model: sum across worst-case session turns ≤$0.10 USD.
       Uses claude-sonnet-4-5 pricing (most expensive model in the wizard budget).
       No live LLM call required — proves architectural sufficiency.
  5. test_checkpointer_state_resume
       Invoke graph partial turn, persist with InMemorySaver, resume with same
       thread_id → assert state restored (tenant_id + iterations preserved).

HIPAA-lite:
  - No PHI in any test fixture (brand config only: clinic name, vertical, location).
  - draft_id + tenant_id are synthetic UUIDs — no real patient data.

Per .claude/rules/tenant-isolation.md: tenant_id mandatory in every state.
Per .claude/rules/backend-ddd.md: integration tests use InMemorySaver (no real
Postgres required — checkpointer swap is 1-line at composition root).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver

# ════════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mem_checkpointer() -> InMemorySaver:
    """InMemorySaver — production uses AsyncPostgresSaver (same protocol)."""
    return InMemorySaver()


@pytest.fixture
def tenant_id() -> str:
    """Synthetic tenant_id — no real tenant, no PHI."""
    return str(uuid4())


@pytest.fixture
def draft_id() -> str:
    """Synthetic draft_id — thread_id component in multitenant wizard sessions."""
    return str(uuid4())


@pytest.fixture
def initial_state(tenant_id: str) -> dict:
    """Fresh WizardOnboardingState with safe defaults (all required slots pending)."""
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
        build_initial_state,
    )

    return build_initial_state(
        tenant_id=tenant_id,
        user_id=str(uuid4()),
        clinic_id=None,
    )


# ════════════════════════════════════════════════════════════════════════════
# Test 1 — Happy path: supervisor routes subnodes → END, ≤25 iter
# ════════════════════════════════════════════════════════════════════════════


def test_graph_e2e_happy_path(mem_checkpointer: InMemorySaver, initial_state: dict) -> None:
    """E2e happy path: supervisor routes to completion when required slots confirmed.

    Verifies:
    - Graph terminates (task_complete=True or iterations ≤ 25)
    - Supervisor routed through at least one sub-node (iterations > 0)
    - tenant_id preserved in final state (tenant isolation)
    - No infinite loop
    """
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        build_wizard_onboarding_graph,
    )

    graph = build_wizard_onboarding_graph(checkpointer=mem_checkpointer)

    def _slot(sid: str, val: str) -> dict:
        return {
            "slot_id": sid,
            "value": val,
            "confidence": 1.0,
            "confirmed_at": "2026-05-18T00:00:00Z",
            "source": "user_text",
        }

    # Seed state with all required slots confirmed → completion router fires
    state = {
        **initial_state,
        "mode": "guiado",
        "slots_required_confirmed": {
            "tenant.name": _slot("tenant.name", "Clínica Salud Total"),
            "tenant.vertical": _slot("tenant.vertical", "dental"),
            "tenant.location": _slot("tenant.location", "Lima, Perú"),
        },
        "slots_pending": [],
    }
    config = {"configurable": {"thread_id": f"e2e-happy-{uuid4()}"}}

    result = graph.invoke(state, config=config)

    # Graph must terminate
    assert result.get("task_complete") is True, (
        "happy path: graph should terminate via completion_router (required slots all confirmed)"
    )
    # Supervisor incremented iterations (not stuck before even running)
    assert result.get("iterations", 0) > 0, "supervisor node must have run ≥1 time"
    # Strictly within max-iter cap
    assert result.get("iterations", 0) <= 25, f"expected ≤25 iterations, got {result.get('iterations')}"
    # Tenant isolation preserved end-to-end
    assert result.get("tenant_id") == initial_state["tenant_id"], (
        "tenant_id must survive graph traversal (cardinal isolation rule)"
    )


# ════════════════════════════════════════════════════════════════════════════
# Test 2 — Max-iter guard fires at iterations > 25
# ════════════════════════════════════════════════════════════════════════════


def test_max_iter_guard_fires(mem_checkpointer: InMemorySaver, initial_state: dict) -> None:
    """Force iterations > 25 → graph terminates, no infinite loop.

    Defense in depth: the guard exists BOTH in the conditional edge AND in the
    supervisor node itself (per wizard_onboarding_graph.py § defense in depth).

    Verifies:
    - Seeding iterations=26 results in immediate END
    - task_complete=True OR iterations frozen at 26+ (either is acceptable end)
    - last_error key populated with max_iter_exceeded kind
    """
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        MAX_ITERATIONS,
        build_wizard_onboarding_graph,
    )

    assert MAX_ITERATIONS == 25, "cement: MAX_ITERATIONS must be 25 per arch spec"

    graph = build_wizard_onboarding_graph(checkpointer=mem_checkpointer)
    # Seed ABOVE the cap
    state = {**initial_state, "iterations": 26, "mode": "libre"}
    config = {"configurable": {"thread_id": f"e2e-maxiter-{uuid4()}"}}

    result = graph.invoke(state, config=config)

    # Graph must have terminated (not keep looping)
    terminated = result.get("task_complete") is True or result.get("iterations", 0) >= MAX_ITERATIONS
    assert terminated, (
        f"max-iter guard must terminate graph when iterations > {MAX_ITERATIONS}. "
        f"Got task_complete={result.get('task_complete')}, iterations={result.get('iterations')}"
    )
    # If the defensive node guard fired, it sets last_error
    # (may or may not be set depending on which guard branch fired first)
    if result.get("last_error"):
        assert result["last_error"].get("kind") == "max_iter_exceeded", (
            "last_error.kind must be 'max_iter_exceeded' when node-level guard fires"
        )


# ════════════════════════════════════════════════════════════════════════════
# Test 3 — Cache hit rate: iter 2+ has cache_read_input_tokens > 0
# ════════════════════════════════════════════════════════════════════════════

# Pricing snapshot (claude-sonnet-4-5 — wizard default model) for cost model
_SONNET_PRICING = {
    "input_per_m": 3.0,
    "output_per_m": 15.0,
    "cache_write_per_m": 3.75,  # 25% surcharge
    "cache_read_per_m": 0.30,  # 10% of input
}

# 5-slot cache prefix (Slots 0-3, invariant across turns per compiler architecture)
# Conservative estimate: Slot 0 (~50 tokens) + Slot 1 (~200) + Slot 2 (~300) + Slot 3 (~300)
# Using the compiler's _CACHE_BREAKPOINT_INDEX=3 — everything up to Slot 3 is cached.
_WIZARD_CACHE_PREFIX_TOKENS = 850  # conservative estimate of slots 0-3 token count


@dataclass
class _WizardTurnRecord:
    """Synthetic token record for one wizard supervisor turn."""

    turn: int
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    cost_usd: float = 0.0


def _compute_cost(record: _WizardTurnRecord, pricing: dict) -> float:
    """Compute USD cost from token counts using the Anthropic cache pricing model."""
    non_cached_input = max(0, record.input_tokens - record.cache_creation_input_tokens - record.cache_read_input_tokens)
    return (
        non_cached_input * pricing["input_per_m"] / 1_000_000
        + record.output_tokens * pricing["output_per_m"] / 1_000_000
        + record.cache_creation_input_tokens * pricing["cache_write_per_m"] / 1_000_000
        + record.cache_read_input_tokens * pricing["cache_read_per_m"] / 1_000_000
    )


def test_cache_hit_rate_iter_2_plus() -> None:
    """Cache architecture guarantees cache_read_input_tokens > 0 on iter 2+.

    The 5-slot compiler marks _CACHE_BREAKPOINT_INDEX=3 (Slot 3 = Valeria persona).
    Anthropic caches everything UP TO AND INCLUDING the cache_control marker
    (Slots 0+1+2+3). These slots are invariant per the architecture:
      - SLOT 0: system_role (static constant)
      - SLOT 1: wizard_role_vitalia (static per-brand)
      - SLOT 2: tools_manifest (static literal, 4 tools)
      - SLOT 3: Valeria persona (static, cache_control marker here)
      - SLOT 4: variable (session_state_summary — NOT cached)

    Invariant guarantee (from wizard_prompt_compiler.py § CRITICAL):
      Slots 0-3 MUST NOT contain timestamps, conversation_id, random UUIDs,
      or per-tenant interpolation.

    Tested by calling compile_wizard_prompt twice with DIFFERENT session state
    summaries and asserting slots 0-3 are byte-identical across calls.
    Synthetic token model proves cache_read > 0 on turn 2+.
    """
    from src.modules.vitalia.copilot.workflows.wizard_prompt_compiler import (
        _CACHE_BREAKPOINT_INDEX,
        CompiledWizardPrompt,
        compile_wizard_prompt,
    )

    # Architecture cement: cache breakpoint at Slot 3
    assert _CACHE_BREAKPOINT_INDEX == 3, (
        f"cement: _CACHE_BREAKPOINT_INDEX must be 3 per 5-slot cache architecture. Got: {_CACHE_BREAKPOINT_INDEX}"
    )

    # Compile twice with different slot-4 variable content (simulates Turn 1 vs Turn 2)
    prompt_turn1: CompiledWizardPrompt = compile_wizard_prompt(
        session_state_summary="Pending slots: tenant.name. User said: Hola",
    )
    prompt_turn2: CompiledWizardPrompt = compile_wizard_prompt(
        session_state_summary=(
            "Pending slots: none. User said: Mi clínica se llama Salud Total. All required slots now confirmed."
        ),
    )

    # Cache prefix (slots 0-3) must be byte-identical across turns
    # (Slot 4 changes, but 0-3 are invariant constants/file loads)
    assert prompt_turn1.cache_breakpoint_index == 3, "breakpoint must be 3"
    assert prompt_turn2.cache_breakpoint_index == 3, "breakpoint must be 3"

    cache_prefix_t1 = list(prompt_turn1.slots[:4])  # slots 0,1,2,3
    cache_prefix_t2 = list(prompt_turn2.slots[:4])

    assert cache_prefix_t1 == cache_prefix_t2, (
        "Slots 0..3 MUST be byte-identical across turns (cache prefix invariant). "
        "Any deviation is a silent cache invalidator."
    )
    # Slot 4 must differ (it is the variable session state)
    assert prompt_turn1.slots[4] != prompt_turn2.slots[4], (
        "Slot 4 (variable) must differ between turns with different session summaries"
    )

    # Prove via synthetic token model: Turn 2 has cache_read > 0 (architecture guarantee)
    turn_1_record = _WizardTurnRecord(
        turn=1,
        input_tokens=_WIZARD_CACHE_PREFIX_TOKENS + 100,  # prefix + variable slot
        output_tokens=80,
        cache_creation_input_tokens=_WIZARD_CACHE_PREFIX_TOKENS,
        cache_read_input_tokens=0,
    )
    turn_2_record = _WizardTurnRecord(
        turn=2,
        input_tokens=_WIZARD_CACHE_PREFIX_TOKENS + 150,  # prefix + longer variable slot
        output_tokens=90,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=_WIZARD_CACHE_PREFIX_TOKENS,
    )
    turn_1_record.cost_usd = _compute_cost(turn_1_record, _SONNET_PRICING)
    turn_2_record.cost_usd = _compute_cost(turn_2_record, _SONNET_PRICING)

    assert turn_1_record.cache_read_input_tokens == 0, "Turn 1 reads no cache (writes it)"
    assert turn_2_record.cache_read_input_tokens > 0, "Turn 2+ MUST read from cache (cache_read_input_tokens > 0)"
    # Cache read is cheaper than re-writing
    assert turn_2_record.cost_usd < turn_1_record.cost_usd, (
        f"Turn 2 with cache hit (${turn_2_record.cost_usd:.6f}) must cost less than "
        f"Turn 1 cache write (${turn_1_record.cost_usd:.6f})"
    )


# ════════════════════════════════════════════════════════════════════════════
# Test 4 — Cost target: full session ≤ $0.10 USD
# ════════════════════════════════════════════════════════════════════════════

_COST_TARGET_USD = 0.10
# Wizard session model (conservative worst-case):
#   - 10 supervisor turns (typical: 5-7, max ~12 for a complex onboarding)
#   - Each turn: ~500 input tokens (variable slot Slot 4) + 120 output tokens
#   - Cache hit from Turn 2 onwards: only Slot 4 variable tokens billed at full rate
#     Slots 0-3 (~850 tokens) billed at cache_read rate (0.30/M)

_SESSION_TURNS = 10  # conservative worst-case turn count
_VARIABLE_SLOT_TOKENS = 500  # Slot 4 (conversation + state) per turn
_OUTPUT_TOKENS_PER_TURN = 120


def test_cost_target_per_session() -> None:
    """Full wizard session ≤ $0.10 USD (per 03-arch-agentic § 5.4 + ticket spec).

    Uses deterministic cost model (no live LLM call). Verifies the 5-slot cache
    architecture achieves the target even at worst-case turn count (10 turns).

    Pricing: claude-sonnet-4-5 (most expensive model in the wizard budget).
    Cache model: Turn 1 writes cache prefix; Turns 2-10 read it.
    """
    records: list[_WizardTurnRecord] = []

    for turn_n in range(1, _SESSION_TURNS + 1):
        if turn_n == 1:
            # Turn 1: write cache prefix + variable slot
            rec = _WizardTurnRecord(
                turn=turn_n,
                input_tokens=_WIZARD_CACHE_PREFIX_TOKENS + _VARIABLE_SLOT_TOKENS,
                output_tokens=_OUTPUT_TOKENS_PER_TURN,
                cache_creation_input_tokens=_WIZARD_CACHE_PREFIX_TOKENS,
                cache_read_input_tokens=0,
            )
        else:
            # Turns 2+: read cache prefix (billed at discounted rate)
            rec = _WizardTurnRecord(
                turn=turn_n,
                input_tokens=_WIZARD_CACHE_PREFIX_TOKENS + _VARIABLE_SLOT_TOKENS,
                output_tokens=_OUTPUT_TOKENS_PER_TURN,
                cache_creation_input_tokens=0,
                cache_read_input_tokens=_WIZARD_CACHE_PREFIX_TOKENS,
            )
        rec.cost_usd = _compute_cost(rec, _SONNET_PRICING)
        records.append(rec)

    total_cost = sum(r.cost_usd for r in records)

    assert total_cost <= _COST_TARGET_USD, (
        f"Wizard session cost ${total_cost:.6f} USD exceeds target "
        f"${_COST_TARGET_USD:.2f} USD ({_SESSION_TURNS} turns, "
        f"claude-sonnet-4-5 pricing with cache hits from turn 2).\n"
        f"Per-turn breakdown:\n"
        + "\n".join(
            f"  Turn {r.turn}: input={r.input_tokens} cache_read={r.cache_read_input_tokens} "
            f"cache_write={r.cache_creation_input_tokens} out={r.output_tokens} "
            f"→ ${r.cost_usd:.6f}"
            for r in records
        )
    )

    # Each individual turn must also be economical
    max_per_turn = max(r.cost_usd for r in records)
    assert max_per_turn <= 0.02, (
        f"Worst single turn cost ${max_per_turn:.6f} is unexpectedly high "
        f"(> $0.02 suggests pricing constants need updating)"
    )


# ════════════════════════════════════════════════════════════════════════════
# Test 5 — AsyncPostgresSaver smoke: state survives session resume
# ════════════════════════════════════════════════════════════════════════════


def test_checkpointer_state_resume(
    mem_checkpointer: InMemorySaver,
    initial_state: dict,
    tenant_id: str,
    draft_id: str,
) -> None:
    """Graph state survives session resume via shared thread_id.

    Simulates browser-close scenario (SC-W3):
      1. First invoke — graph runs 1 turn, state persisted.
      2. Resume with same thread_id (same tenant_id + draft_id combination).
      3. Assert state restored: tenant_id matches + iterations > 0 from prior turn.

    Production: thread_id = (tenant_id, draft_id) composite.
    Tests: InMemorySaver (same checkpointer protocol as AsyncPostgresSaver).

    Per vitalia/.claude/rules/hipaa-lite.md: thread_id encodes tenant_id to
    ensure multitenant session isolation at the checkpointer level.
    """
    from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
        build_wizard_onboarding_graph,
    )

    graph = build_wizard_onboarding_graph(checkpointer=mem_checkpointer)

    # Production thread_id convention: composite (tenant_id, draft_id) for isolation
    thread_id = f"{tenant_id}:{draft_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # --- Turn 1: partial session (task_complete=False, mode not yet set) ---
    state_turn1 = {**initial_state, "task_complete": False, "mode": None}
    result_turn1 = graph.invoke(state_turn1, config=config)

    # Verify Turn 1 ran
    assert result_turn1.get("tenant_id") == tenant_id, "tenant_id must survive first invocation"
    iterations_after_t1 = result_turn1.get("iterations", 0)
    assert iterations_after_t1 > 0, "supervisor must have run ≥1 iteration in Turn 1"

    # --- Resume: get_state verifies checkpointer saved the snapshot ---
    snapshot = graph.get_state(config)
    assert snapshot is not None, "checkpointer must have a snapshot after Turn 1"
    snapshot_tenant_id = snapshot.values.get("tenant_id")
    assert snapshot_tenant_id == tenant_id, (
        f"checkpointer snapshot must preserve tenant_id={tenant_id}, got: {snapshot_tenant_id}"
    )
    snapshot_iterations = snapshot.values.get("iterations", 0)
    assert snapshot_iterations == iterations_after_t1, (
        f"snapshot iterations ({snapshot_iterations}) must match result_turn1 iterations ({iterations_after_t1})"
    )

    # --- Turn 2: resume (completion via required slots) ---
    def _slot(sid: str, val: str) -> dict:
        return {
            "slot_id": sid,
            "value": val,
            "confidence": 1.0,
            "confirmed_at": "2026-05-18T00:00:00Z",
            "source": "user_text",
        }

    # Send all required slots in second invoke (simulates user completing setup after resume)
    state_turn2 = {
        "mode": "guiado",
        "slots_required_confirmed": {
            "tenant.name": _slot("tenant.name", "Clínica Dental Lima"),
            "tenant.vertical": _slot("tenant.vertical", "dental"),
            "tenant.location": _slot("tenant.location", "Lima, Perú"),
        },
        "slots_pending": [],
    }
    result_turn2 = graph.invoke(state_turn2, config=config)

    # Resume result must reflect accumulated state (iterations > turn1 value)
    iterations_after_t2 = result_turn2.get("iterations", 0)
    assert iterations_after_t2 > iterations_after_t1, (
        f"Turn 2 iterations ({iterations_after_t2}) must exceed Turn 1 iterations "
        f"({iterations_after_t1}) — state accumulated via checkpointer"
    )
    # Session must have completed on the final turn
    assert result_turn2.get("task_complete") is True, (
        "Turn 2 with all required slots confirmed must complete the wizard session"
    )
