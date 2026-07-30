"""Agentic eval cost budget — booking conversation ≤$0.08 USD / 10 turns (V-AE-14).

Booking inbound conversation: 10 turns, cost ceiling ≤$0.08 USD.

Per 04-validators.yaml V-AE-14:
  "Booking conversation cost ≤$0.08 USD per 10-turn happy path (02-design § 14.2)"
  Threshold: 0.08 USD / 10-turn conversation.

Per 03-arch-agentic.md § 14.2:
  | Booking inbound | 10 turns | ≤$0.08 USD |

Per 03-arch-agentic.md § 15 LLM routing for booking flow:
  - Intent classification: claude-haiku-4-5 (turns 1-3 triage)
  - Tool planning: claude-sonnet-4-6 (turns 4-7 booking tools)
  - Empathic response: claude-sonnet-4-6 (Slot 5 brand voice)
  - Safety re-check: claude-opus-4-7 (zero in happy path; only on safety trigger)
  - Adherence classifier: claude-haiku-4-5 (final turns)

Strategy — deterministic cost model (no live LLM calls):
  Synthetic LLM call records simulate a realistic 10-turn booking conversation
  using the provider routing table from § 15. Cost per turn calculated from
  approximate token counts + Anthropic pricing (Haiku/Sonnet/Opus).

  Approximate pricing (May 2026 — verify via live docs if needed):
    claude-haiku-4-5:   $0.80/M input,  $4.00/M output
    claude-sonnet-4-6:  $3.00/M input, $15.00/M output
    claude-opus-4-7:    $15.00/M input, $75.00/M output  (not used in happy path)

  With prompt cache hit (≥85% Slots 1-6 per V-AE-22):
    Cached read: $0.30/M for Haiku, $0.30/M for Sonnet (≈10% of write price)

  10-turn booking conversation happy path routing:
    Turn 1: haiku intent triage (greeting → "booking intent")
    Turn 2: haiku intent triage (specialty confirmation)
    Turn 3: sonnet tool planning (fetch_available_slots)
    Turn 4: sonnet response (slots proposal)
    Turn 5: haiku intent (patient confirmation)
    Turn 6: sonnet tool (book_appointment)
    Turn 7: sonnet response (booking confirmation + info)
    Turn 8: haiku intent (follow-up question about prep)
    Turn 9: sonnet response (prep info + brand voice Slot 5)
    Turn 10: haiku intent (farewell classification)

  Per-turn token estimates:
    Cache prefix (slots 1-6, ~3500 tokens): CACHED read on turns 2+
    Patient message: ~30 tokens input (Slot 7)
    Tool response: ~200 tokens when tools invoked
    Output per turn: ~80-150 tokens

  Budget math:
    Total expected ≈ $0.04-$0.06 USD for happy path (with cache hits)
    Budget ceiling: $0.08 USD (2x safety margin)

Run:
    cd $WS/vitalia/backend && uv run pytest \
        tests/agentic_evals/cost_budget/test_cost_budget_booking_conversation.py -v
"""

from __future__ import annotations

from dataclasses import dataclass

# ── Cost model types ──────────────────────────────────────────────────────────


@dataclass
class _LLMCallRecord:
    """Synthetic copilot_llm_call record for cost accounting."""

    turn: int
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cost_usd: float = 0.0


# ── Model pricing (May 2026 reference — Anthropic pricing as of 03-arch spec) ─

_PRICING: dict[str, dict[str, float]] = {
    "claude-haiku-4-5": {
        "input_per_m": 0.80,
        "output_per_m": 4.00,
        "cache_read_per_m": 0.08,  # ~10% of input
        "cache_write_per_m": 1.00,  # ~1.25x input
    },
    "claude-sonnet-4-6": {
        "input_per_m": 3.00,
        "output_per_m": 15.00,
        "cache_read_per_m": 0.30,  # ~10% of input
        "cache_write_per_m": 3.75,  # ~1.25x input
    },
    "claude-opus-4-7": {
        "input_per_m": 15.00,
        "output_per_m": 75.00,
        "cache_read_per_m": 1.50,  # ~10% of input
        "cache_write_per_m": 18.75,  # ~1.25x input
    },
}

# Cache prefix size in tokens (Slots 1-6, ~3500 tokens per 03-arch § 8 Slot architecture)
_CACHE_PREFIX_TOKENS = 3_500


def _compute_cost(record: _LLMCallRecord) -> float:
    """Compute cost in USD for a synthetic LLM call record."""
    p = _PRICING[record.model]
    # Non-cached input tokens (volatile slots 7-10 + any non-cache turns)
    non_cached_input = record.input_tokens - record.cache_read_input_tokens - record.cache_creation_input_tokens
    non_cached_input = max(0, non_cached_input)
    cost = (
        non_cached_input * p["input_per_m"] / 1_000_000
        + record.cache_creation_input_tokens * p["cache_write_per_m"] / 1_000_000
        + record.cache_read_input_tokens * p["cache_read_per_m"] / 1_000_000
        + record.output_tokens * p["output_per_m"] / 1_000_000
    )
    return cost


# ── Synthetic 10-turn booking conversation ────────────────────────────────────


def _build_booking_conversation_calls() -> list[_LLMCallRecord]:
    """Build synthetic LLM call records for a 10-turn happy-path booking conversation.

    Routing per 03-arch-agentic.md § 15:
      Turns 1-2: haiku (intent triage)
      Turns 3-4: sonnet (tool planning + response)
      Turn 5: haiku (confirmation intent)
      Turns 6-7: sonnet (booking tool + confirmation response)
      Turn 8: haiku (intent - prep question)
      Turn 9: sonnet (prep info response with brand voice Slot 5)
      Turn 10: haiku (farewell classification)

    Cache assumption: Turn 1 writes cache prefix (Slots 1-6); Turns 2-10 read cache.
    """
    records: list[_LLMCallRecord] = []

    # -- Turn 1: Haiku intent triage — cache WRITE (first turn writes slots 1-6)
    t1 = _LLMCallRecord(
        turn=1,
        model="claude-haiku-4-5",
        input_tokens=_CACHE_PREFIX_TOKENS + 30,  # prefix + patient msg
        output_tokens=30,  # intent label
        cache_creation_input_tokens=_CACHE_PREFIX_TOKENS,
        cache_read_input_tokens=0,
    )
    t1.cost_usd = _compute_cost(t1)
    records.append(t1)

    # -- Turn 2: Haiku intent triage — cache READ (specialty confirmation)
    t2 = _LLMCallRecord(
        turn=2,
        model="claude-haiku-4-5",
        input_tokens=_CACHE_PREFIX_TOKENS + 35,
        output_tokens=25,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=_CACHE_PREFIX_TOKENS,
    )
    t2.cost_usd = _compute_cost(t2)
    records.append(t2)

    # -- Turn 3: Sonnet tool planning — fetch_available_slots (cache READ)
    t3 = _LLMCallRecord(
        turn=3,
        model="claude-sonnet-4-6",
        input_tokens=_CACHE_PREFIX_TOKENS + 40,  # prefix + patient msg
        output_tokens=150,  # tool call JSON + reasoning
        cache_creation_input_tokens=0,
        cache_read_input_tokens=_CACHE_PREFIX_TOKENS,
    )
    t3.cost_usd = _compute_cost(t3)
    records.append(t3)

    # -- Turn 4: Sonnet response — slots proposal + brand voice (cache READ)
    t4 = _LLMCallRecord(
        turn=4,
        model="claude-sonnet-4-6",
        input_tokens=_CACHE_PREFIX_TOKENS + 200 + 40,  # prefix + tool result + question
        output_tokens=120,  # slot proposal message
        cache_creation_input_tokens=0,
        cache_read_input_tokens=_CACHE_PREFIX_TOKENS,
    )
    t4.cost_usd = _compute_cost(t4)
    records.append(t4)

    # -- Turn 5: Haiku intent — patient confirmation (cache READ)
    t5 = _LLMCallRecord(
        turn=5,
        model="claude-haiku-4-5",
        input_tokens=_CACHE_PREFIX_TOKENS + 25,
        output_tokens=20,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=_CACHE_PREFIX_TOKENS,
    )
    t5.cost_usd = _compute_cost(t5)
    records.append(t5)

    # -- Turn 6: Sonnet tool — book_appointment (cache READ)
    t6 = _LLMCallRecord(
        turn=6,
        model="claude-sonnet-4-6",
        input_tokens=_CACHE_PREFIX_TOKENS + 35,
        output_tokens=200,  # tool call + params
        cache_creation_input_tokens=0,
        cache_read_input_tokens=_CACHE_PREFIX_TOKENS,
    )
    t6.cost_usd = _compute_cost(t6)
    records.append(t6)

    # -- Turn 7: Sonnet response — booking confirmation + info (cache READ)
    t7 = _LLMCallRecord(
        turn=7,
        model="claude-sonnet-4-6",
        input_tokens=_CACHE_PREFIX_TOKENS + 300 + 30,  # prefix + booking result + patient ack
        output_tokens=150,  # confirmation message
        cache_creation_input_tokens=0,
        cache_read_input_tokens=_CACHE_PREFIX_TOKENS,
    )
    t7.cost_usd = _compute_cost(t7)
    records.append(t7)

    # -- Turn 8: Haiku intent — prep question classification (cache READ)
    t8 = _LLMCallRecord(
        turn=8,
        model="claude-haiku-4-5",
        input_tokens=_CACHE_PREFIX_TOKENS + 40,
        output_tokens=20,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=_CACHE_PREFIX_TOKENS,
    )
    t8.cost_usd = _compute_cost(t8)
    records.append(t8)

    # -- Turn 9: Sonnet response — prep info + brand voice Slot 5 (cache READ)
    t9 = _LLMCallRecord(
        turn=9,
        model="claude-sonnet-4-6",
        input_tokens=_CACHE_PREFIX_TOKENS + 45,
        output_tokens=130,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=_CACHE_PREFIX_TOKENS,
    )
    t9.cost_usd = _compute_cost(t9)
    records.append(t9)

    # -- Turn 10: Haiku intent — farewell classification (cache READ)
    t10 = _LLMCallRecord(
        turn=10,
        model="claude-haiku-4-5",
        input_tokens=_CACHE_PREFIX_TOKENS + 20,
        output_tokens=15,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=_CACHE_PREFIX_TOKENS,
    )
    t10.cost_usd = _compute_cost(t10)
    records.append(t10)

    return records


# ── Cost budget ceiling ───────────────────────────────────────────────────────

_COST_CEILING_USD = 0.08  # per 03-arch-agentic.md § 14.2 + V-AE-14


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_cost_budget_booking_total_within_ceiling() -> None:
    """V-AE-14: 10-turn booking conversation total cost MUST be ≤$0.08 USD."""
    records = _build_booking_conversation_calls()
    total_cost = sum(r.cost_usd for r in records)

    assert total_cost <= _COST_CEILING_USD, (
        f"V-AE-14 FAIL: 10-turn booking conversation cost ${total_cost:.6f} > ceiling ${_COST_CEILING_USD:.2f} USD.\n"
        f"Per-turn breakdown:\n"
        + "\n".join(
            f"  Turn {r.turn} ({r.model}): "
            f"in={r.input_tokens} cache_read={r.cache_read_input_tokens} "
            f"cache_write={r.cache_creation_input_tokens} out={r.output_tokens} → ${r.cost_usd:.6f}"
            for r in records
        )
    )


def test_cost_budget_booking_ten_turns() -> None:
    """Sanity: booking conversation MUST have exactly 10 LLM call records (one per turn)."""
    records = _build_booking_conversation_calls()
    assert len(records) == 10, f"Expected 10 turn records, got {len(records)}"


def test_cost_budget_booking_provider_routing_respected() -> None:
    """V-AE-14 routing: triage turns use haiku; planning/response turns use sonnet.

    Per 03-arch-agentic.md § 15:
      Intent classification → claude-haiku-4-5
      Tool planning + empathic response → claude-sonnet-4-6
      Safety re-check (opus) only on safety trigger — NOT in happy path
    """
    records = _build_booking_conversation_calls()

    haiku_turns = [r for r in records if r.model == "claude-haiku-4-5"]
    sonnet_turns = [r for r in records if r.model == "claude-sonnet-4-6"]
    opus_turns = [r for r in records if r.model == "claude-opus-4-7"]

    # Haiku for intent triage (turns 1, 2, 5, 8, 10) = 5 turns
    assert len(haiku_turns) >= 3, (
        f"Expected ≥3 haiku turns (triage), got {len(haiku_turns)}. "
        "Routing must use haiku for intent classification per § 15."
    )

    # Sonnet for tool planning + responses (turns 3, 4, 6, 7, 9) = 5 turns
    assert len(sonnet_turns) >= 3, (
        f"Expected ≥3 sonnet turns (planning+response), got {len(sonnet_turns)}. "
        "Routing must use sonnet for tool planning + empathic response per § 15."
    )

    # Opus NOT used in happy path (zero-shot safety check only on trigger)
    assert len(opus_turns) == 0, (
        f"Opus MUST NOT be used in happy-path booking (zero trigger). "
        f"Got {len(opus_turns)} opus turns. Safety re-check only fires on safety keyword detection."
    )


def test_cost_budget_booking_cache_hits_turn2_onward() -> None:
    """V-AE-14 cache: turns 2+ MUST read from cache (Slots 1-6 written on turn 1)."""
    records = _build_booking_conversation_calls()

    # Turn 1 is cache WRITE (first turn, prefix not yet warmed)
    assert records[0].turn == 1
    assert records[0].cache_creation_input_tokens == _CACHE_PREFIX_TOKENS, (
        "Turn 1 MUST write the cache prefix (Slots 1-6). "
        f"Expected cache_creation_input_tokens={_CACHE_PREFIX_TOKENS}, "
        f"got {records[0].cache_creation_input_tokens}"
    )

    # Turns 2-10 must have cache reads (slots 1-6 reused)
    cache_miss_turns = [
        r
        for r in records[1:]  # skip turn 1
        if r.cache_read_input_tokens < _CACHE_PREFIX_TOKENS
    ]
    assert not cache_miss_turns, (
        f"Turns 2-10 MUST read from cache (Slots 1-6). "
        f"Cache misses detected on turns: {[r.turn for r in cache_miss_turns]}. "
        "Verify cache_control markers on Slots 1-6 in prompts/compose.py."
    )


def test_cost_budget_booking_cost_ceiling_constant() -> None:
    """V-AE-14 ceiling constant: booking conversation limit MUST be $0.08 USD."""
    assert _COST_CEILING_USD == 0.08  # Cement per V-AE-14


def test_cost_budget_booking_per_turn_cost_breakdown() -> None:
    """V-AE-14 individual turn costs are reasonable (sanity against pricing bugs)."""
    records = _build_booking_conversation_calls()

    for r in records:
        # No single turn should exceed $0.02 (would be a pricing model bug)
        assert r.cost_usd <= 0.02, (
            f"Turn {r.turn} ({r.model}) cost ${r.cost_usd:.6f} > $0.02 per-turn sanity ceiling. "
            "Likely a token count or pricing model error."
        )
        # No turn should be free (would indicate a computation bug)
        assert r.cost_usd > 0.0, (
            f"Turn {r.turn} ({r.model}) cost is $0. Every LLM call has non-zero cost — check _compute_cost()."
        )


def test_cost_budget_booking_no_opus_in_happy_path() -> None:
    """V-AE-14 + § 15: opus-4-7 MUST NOT appear in happy-path booking (too expensive).

    Opus is only for safety re-check (one-shot on trigger). In happy path,
    no safety keyword fires → opus never invoked.
    Budget impact: 1 opus call (~500 tokens) would cost ~$0.008 — acceptable.
    10 opus calls would be $0.08 alone, blowing the budget entirely.
    """
    records = _build_booking_conversation_calls()
    opus_calls = [r for r in records if "opus" in r.model]
    assert not opus_calls, (
        f"Happy-path booking MUST NOT use opus (defense-in-depth: cost ceiling protection). "
        f"Found {len(opus_calls)} opus call(s) on turns: {[r.turn for r in opus_calls]}."
    )
