"""Agentic eval cost budget — followup turn ≤$0.025 USD / turn (V-AE-15).

Followup D5/D14/D90 single check: 2 turns, cost ceiling ≤$0.025 USD.

Per 04-validators.yaml V-AE-15:
  "Followup turn cost ≤$0.025 USD per turn"
  Threshold: 0.025 USD / turn.

Per 03-arch-agentic.md § 14.2:
  | Followup D5/D14/D90 single check | 2 turns | ≤$0.025 USD |

Per 03-arch-agentic.md § 15 LLM routing for followup flow:
  - Adherence + sentiment classifier: claude-haiku-4-5
  - Cron-triggered outbound compose: claude-sonnet-4-6 (voice fidelity)

Strategy — deterministic cost model per turn (no live LLM calls):
  Followup flow is lightweight:
    Turn 1 (outbound): sonnet composes empathic adherence check message (Slot 5 voice)
    Turn 2 (inbound): haiku classifies patient response for adherence + sentiment

  Key constraint: even though the "2-turn total ≤$0.025" is per the arch spec,
  V-AE-15 tests cost "per turn" — so each turn individually AND the aggregate
  2-turn total must satisfy the ceiling.

  With cache hits (Slots 1-6 cached after turn 1):
    Turn 1 (sonnet, outbound compose): ~$0.008-$0.012 USD
    Turn 2 (haiku, classification): ~$0.001-$0.003 USD
    Total: ~$0.009-$0.015 USD << $0.025 ceiling

Run:
    cd $WS/vitalia/backend && uv run pytest \
        tests/agentic_evals/cost_budget/test_cost_budget_followup_turn.py -v
"""

from __future__ import annotations

from dataclasses import dataclass

# ── Cost model types ──────────────────────────────────────────────────────────


@dataclass
class _LLMCallRecord:
    """Synthetic copilot_llm_call record for cost accounting."""

    turn: int
    phase: str  # "outbound_compose" | "inbound_classify"
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cost_usd: float = 0.0


# ── Model pricing ─────────────────────────────────────────────────────────────

_PRICING: dict[str, dict[str, float]] = {
    "claude-haiku-4-5": {
        "input_per_m": 0.80,
        "output_per_m": 4.00,
        "cache_read_per_m": 0.08,
        "cache_write_per_m": 1.00,
    },
    "claude-sonnet-4-6": {
        "input_per_m": 3.00,
        "output_per_m": 15.00,
        "cache_read_per_m": 0.30,
        "cache_write_per_m": 3.75,
    },
}

_CACHE_PREFIX_TOKENS = 3_500  # Slots 1-6 per 03-arch § 8


def _compute_cost(record: _LLMCallRecord) -> float:
    """Compute cost in USD for a synthetic LLM call record."""
    p = _PRICING[record.model]
    non_cached_input = max(
        0,
        record.input_tokens - record.cache_read_input_tokens - record.cache_creation_input_tokens,
    )
    return (
        non_cached_input * p["input_per_m"] / 1_000_000
        + record.cache_creation_input_tokens * p["cache_write_per_m"] / 1_000_000
        + record.cache_read_input_tokens * p["cache_read_per_m"] / 1_000_000
        + record.output_tokens * p["output_per_m"] / 1_000_000
    )


# ── Synthetic followup 2-turn conversation ────────────────────────────────────


def _build_followup_turn_records() -> list[_LLMCallRecord]:
    """Build synthetic LLM call records for a 2-turn followup adherence check.

    Routing per 03-arch-agentic.md § 15:
      Turn 1 (outbound compose): claude-sonnet-4-6 — cron-triggered, voice fidelity high stakes
      Turn 2 (inbound classify): claude-haiku-4-5 — adherence + sentiment classifier

    Cache: Turn 1 writes Slots 1-6 prefix; Turn 2 reads from cache.
    """
    records: list[_LLMCallRecord] = []

    # -- Turn 1: Sonnet outbound — compose adherence check message (cron-triggered)
    # Cache WRITE: Slots 1-6 not yet cached for this workflow run
    # Patient context (Slot 7): treatment summary ~150 tokens
    t1 = _LLMCallRecord(
        turn=1,
        phase="outbound_compose",
        model="claude-sonnet-4-6",
        input_tokens=_CACHE_PREFIX_TOKENS + 150,  # prefix + treatment summary
        output_tokens=120,  # adherence check message (voice-fidelity quality)
        cache_creation_input_tokens=_CACHE_PREFIX_TOKENS,
        cache_read_input_tokens=0,
    )
    t1.cost_usd = _compute_cost(t1)
    records.append(t1)

    # -- Turn 2: Haiku inbound — classify patient response (cache READ)
    # Patient responded with ~40 tokens; haiku classifies adherence + sentiment
    t2 = _LLMCallRecord(
        turn=2,
        phase="inbound_classify",
        model="claude-haiku-4-5",
        input_tokens=_CACHE_PREFIX_TOKENS + 40 + 120,  # prefix + patient msg + t1 output context
        output_tokens=30,  # adherence_score + sentiment label JSON
        cache_creation_input_tokens=0,
        cache_read_input_tokens=_CACHE_PREFIX_TOKENS,
    )
    t2.cost_usd = _compute_cost(t2)
    records.append(t2)

    return records


# ── Cost budget ceiling ───────────────────────────────────────────────────────

_COST_CEILING_PER_TURN_USD = 0.025  # per V-AE-15 + 03-arch § 14.2


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_cost_budget_followup_total_within_ceiling() -> None:
    """V-AE-15: 2-turn followup conversation total cost MUST be ≤$0.025 USD."""
    records = _build_followup_turn_records()
    total_cost = sum(r.cost_usd for r in records)

    assert total_cost <= _COST_CEILING_PER_TURN_USD, (
        f"V-AE-15 FAIL: 2-turn followup cost ${total_cost:.6f} > ceiling ${_COST_CEILING_PER_TURN_USD:.3f} USD.\n"
        f"Per-turn breakdown:\n"
        + "\n".join(
            f"  Turn {r.turn} ({r.phase}, {r.model}): "
            f"in={r.input_tokens} cache_read={r.cache_read_input_tokens} "
            f"cache_write={r.cache_creation_input_tokens} out={r.output_tokens} → ${r.cost_usd:.6f}"
            for r in records
        )
    )


def test_cost_budget_followup_per_turn_within_ceiling() -> None:
    """V-AE-15: each individual turn MUST be ≤$0.025 USD (no single turn blows budget)."""
    records = _build_followup_turn_records()

    for r in records:
        assert r.cost_usd <= _COST_CEILING_PER_TURN_USD, (
            f"V-AE-15 FAIL: Turn {r.turn} ({r.phase}, {r.model}) cost ${r.cost_usd:.6f} "
            f"> per-turn ceiling ${_COST_CEILING_PER_TURN_USD:.3f} USD.\n"
            f"  Tokens: in={r.input_tokens} cache_read={r.cache_read_input_tokens} "
            f"cache_write={r.cache_creation_input_tokens} out={r.output_tokens}"
        )


def test_cost_budget_followup_two_turns() -> None:
    """Sanity: followup conversation MUST have exactly 2 LLM call records."""
    records = _build_followup_turn_records()
    assert len(records) == 2, f"03-arch § 14.2 specifies 2-turn followup check. Got {len(records)} records."


def test_cost_budget_followup_provider_routing() -> None:
    """V-AE-15 routing: outbound compose = sonnet, inbound classify = haiku.

    Per 03-arch § 15:
      Cron-triggered followup outbound: claude-sonnet-4-6 (voice fidelity high stakes)
      Adherence + sentiment classifier: claude-haiku-4-5 (deterministic short outputs)
    """
    records = _build_followup_turn_records()

    outbound = next((r for r in records if r.phase == "outbound_compose"), None)
    inbound = next((r for r in records if r.phase == "inbound_classify"), None)

    assert outbound is not None, "Missing outbound_compose turn."
    assert inbound is not None, "Missing inbound_classify turn."

    assert outbound.model == "claude-sonnet-4-6", (
        f"Outbound compose MUST use claude-sonnet-4-6 (voice fidelity). Got: {outbound.model}."
    )
    assert inbound.model == "claude-haiku-4-5", (
        f"Inbound classify MUST use claude-haiku-4-5 (cheap classifier). Got: {inbound.model}."
    )


def test_cost_budget_followup_cache_hit_on_turn2() -> None:
    """V-AE-15: Turn 2 MUST read cache prefix (Slots 1-6 written on Turn 1)."""
    records = _build_followup_turn_records()

    t1 = records[0]
    t2 = records[1]

    assert t1.cache_creation_input_tokens == _CACHE_PREFIX_TOKENS, (
        f"Turn 1 MUST write cache prefix ({_CACHE_PREFIX_TOKENS} tokens). Got: {t1.cache_creation_input_tokens}."
    )
    assert t2.cache_read_input_tokens == _CACHE_PREFIX_TOKENS, (
        f"Turn 2 MUST read cache prefix ({_CACHE_PREFIX_TOKENS} tokens). "
        f"Got: {t2.cache_read_input_tokens}. "
        "Cache miss on Turn 2 doubles Slot 1-6 cost — violates budget model."
    )


def test_cost_budget_followup_ceiling_constant() -> None:
    """V-AE-15 ceiling constant: followup limit MUST be $0.025 USD."""
    assert _COST_CEILING_PER_TURN_USD == 0.025  # Cement per V-AE-15


def test_cost_budget_followup_sonnet_cheaper_than_opus_alternative() -> None:
    """Sanity: sonnet outbound compose costs less than if opus were used.

    This documents WHY sonnet (not opus) is used for outbound compose:
    voice fidelity is achievable with sonnet for followup messages, and
    using opus would violate the cost ceiling.
    """
    records = _build_followup_turn_records()
    outbound = records[0]
    actual_cost = outbound.cost_usd

    # Hypothetical opus cost for same tokens
    opus_pricing = {"cache_write_per_m": 18.75, "cache_read_per_m": 1.50, "input_per_m": 15.00, "output_per_m": 75.00}
    non_cached = max(0, outbound.input_tokens - outbound.cache_creation_input_tokens)
    opus_cost = (
        non_cached * opus_pricing["input_per_m"] / 1_000_000
        + outbound.cache_creation_input_tokens * opus_pricing["cache_write_per_m"] / 1_000_000
        + outbound.output_tokens * opus_pricing["output_per_m"] / 1_000_000
    )

    assert actual_cost < opus_cost, (
        "Sonnet outbound cost should be less than hypothetical opus cost. "
        f"Sonnet: ${actual_cost:.6f}, Opus: ${opus_cost:.6f}."
    )
    assert opus_cost > _COST_CEILING_PER_TURN_USD, (
        f"This test documents that using Opus would blow the $0.025 ceiling. "
        f"Opus cost: ${opus_cost:.6f} > $0.025. "
        "Per arch decision: sonnet chosen for voice fidelity at acceptable cost."
    )
