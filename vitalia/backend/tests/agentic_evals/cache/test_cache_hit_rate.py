"""Agentic eval — A3: cache hit rate ≥85% on slots 1-6.

Per Story 11 T-prompts-1 acceptance criterion A3:
  Cache hit rate ≥85% slots 1-6 measured via cache_read/creation ratio.

Spec sources:
  * 02-design-agentic.md § 10.3 cache hit rate target & invalidation triggers
  * 03-arch-agentic.md § 8.5 idem
  * 04-validators.yaml::V-AE-22 threshold cache_hit_rate_min: 0.85
  * 06-tickets.yaml::T-prompts-1 acceptance A3

Strategy — synthetic in-process cache simulator:

  Anthropic prompt cache treats a content block as a cache HIT if its byte
  payload is byte-identical to a previously-seen block under the same
  prompt_cache_key (per-tenant scoping). This test simulates that contract
  in pure Python — no real LLM API call required (which would cost real $$
  + introduce flakiness from network/rate limits).

  For each tenant turn:
    1. Build cacheable prefix blocks via `cacheable_prefix_blocks(...)`.
    2. Hash each block's text payload.
    3. Look up hash in per-tenant cache (keyed by prompt_cache_key(tenant_id)).
    4. If hash present → COUNT as cache_read_input_tokens (read).
       If hash absent → COUNT as cache_creation_input_tokens (write), insert hash.
    5. Aggregate ratio = read_tokens / (read_tokens + creation_tokens).

  This proxies Anthropic's real behavior faithfully because:
    * Anthropic compares byte-payload of cacheable blocks under the cache key.
    * Our simulator does the same byte-payload comparison.
    * Differences (TTL eviction, cluster-locality misses, fragment reordering)
      are not deterministic in real prod and only LOWER hit rate in real prod.
      Our deterministic upper-bound is the right thing to measure here — if our
      compose pipeline causes mismatch, real Anthropic would too.

  Real production measurement happens via `copilot_llm_call.cache_read_input_tokens
  / cache_creation_input_tokens` ratio per tenant (per spec § 8.5) — that comes
  online when the orchestrator wires the LiteLLM client. This test is the
  PRE-WIRING contract that the COMPOSE PIPELINE produces stable byte-equal
  prefixes per-tenant across turns.

Pure data: no LLM call, no Postgres, no Anthropic SDK required.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from src.modules.vitalia.agentic.prompts.compose import (
    cacheable_prefix_blocks,
    prompt_cache_key,
)

# ─────────────────────────────────────────────────────────────────────────────
# Synthetic prompt-cache simulator
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class _SimulatedCacheStats:
    """Aggregator for simulated Anthropic cache hits."""

    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    # Per-tenant hash bucket (key = prompt_cache_key, value = set of seen block hashes)
    _seen: dict[str, set[str]] = field(default_factory=dict)

    @property
    def hit_rate(self) -> float:
        total = self.cache_read_input_tokens + self.cache_creation_input_tokens
        if total == 0:
            return 0.0
        return self.cache_read_input_tokens / total

    def record_turn(
        self,
        *,
        cache_key: str,
        cacheable_blocks: list[dict[str, Any]],
    ) -> None:
        """Simulate Anthropic cache lookup for one turn's cacheable blocks.

        Each block's text payload is hashed; if the hash was seen previously
        for this cache_key, count as read; else count as creation + insert.
        Token cost is approximated by character count (real Anthropic counts
        true tokens — char-count is a conservative proxy that preserves
        relative ratios; the threshold of 0.85 holds either way).
        """
        bucket = self._seen.setdefault(cache_key, set())
        for block in cacheable_blocks:
            text = block.get("text", "")
            # Approximate token count by character count / 4 (Anthropic English ratio
            # ~4 chars/token; Spanish ~3.5; conservative use of /4 keeps the metric
            # consistent across blocks for ratio purposes).
            approx_tokens = max(1, len(text) // 4)
            block_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if block_hash in bucket:
                self.cache_read_input_tokens += approx_tokens
            else:
                self.cache_creation_input_tokens += approx_tokens
                bucket.add(block_hash)


# ─────────────────────────────────────────────────────────────────────────────
# Story 11 fixture tenants (per 02-design § 11.2)
# ─────────────────────────────────────────────────────────────────────────────

# Three Story-11 fixture tenants with distinct voices (Slot 5 BRAND_VOICE).
# Slots 1-4, 6 invariant cross-tenant; Slot 5 varies per tenant. Within-tenant
# turns share Slot 5 (cache hit on slot 5 too).
_FIXTURE_TENANTS = [
    {
        "tenant_id": "aurora-dental-ar-uuid",
        "channel": "whatsapp",
        "brand_voice": (
            "# Voz Aurora Dental AR (warm_close, voseo)\n\n"
            "Hablás con calidez y cercanía. Usás voseo argentino: 'mirá', "
            "'tenés', 'querés', 'che', 'dale'. Cierre asertivo en oferta de "
            "agendamiento. Tono profesional pero familiar, como amiga del "
            "barrio que también es dentista."
        ),
    },
    {
        "tenant_id": "mindful-cl-uuid",
        "channel": "whatsapp",
        "brand_voice": (
            "# Voz Centro Mindful Santiago CL (empathic-paciente, neutro chileno)\n\n"
            "Tono empático, pausado, validador. Tuteo neutro chileno: "
            "'tú puedes', 'tienes', 'mira'. NO voseo. Acompaña al paciente "
            "psicológico con tiempo y comprensión. Evitas presionar al "
            "agendamiento — invitas suavemente."
        ),
    },
    {
        "tenant_id": "sanare-mx-uuid",
        "channel": "whatsapp",
        "brand_voice": (
            "# Voz Sanaré LATAM MX (serene, neutro broad LatAm)\n\n"
            "Tono sereno, profesional, cálido sin floreo regional. Tuteo "
            "neutro LatAm broad. Estructura clara, frases cortas. Apta para "
            "públicos panregionales — evita voseo y léxico mexicano específico."
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# A3 — cache hit rate ≥85% across simulated multi-turn conversations
# ─────────────────────────────────────────────────────────────────────────────


_TURNS_PER_TENANT = 10  # representative multi-turn session
_TOTAL_TURNS = _TURNS_PER_TENANT * len(_FIXTURE_TENANTS)


def test_cache_hit_rate_target_85_percent_min() -> None:
    """A3: simulated cache hit rate on slots 1-6 ≥85% across 3 tenants × 10 turns.

    For each tenant, simulate 10 turns where compose returns the SAME
    cacheable prefix (slots 1-4 + 6 invariant cross-tenant; slot 5 invariant
    per-tenant within session). First turn = creation; turns 2-10 = reads.

    Expected: 9/10 turns × 6 slots = 54 reads, 1/10 × 6 = 6 creations per
    tenant. Aggregate hit rate per tenant = 9/10 = 90%, well above 85% bar.
    Across 3 tenants: same ratio. This validates the COMPOSE PIPELINE produces
    byte-stable prefixes — without that, real Anthropic cache would never hit.
    """
    stats = _SimulatedCacheStats()

    for tenant in _FIXTURE_TENANTS:
        cache_key = prompt_cache_key(tenant["tenant_id"])
        for _turn in range(_TURNS_PER_TENANT):
            blocks = cacheable_prefix_blocks(
                channel=tenant["channel"],
                brand_voice_compiled=tenant["brand_voice"],
            )
            stats.record_turn(cache_key=cache_key, cacheable_blocks=blocks)

    hit_rate = stats.hit_rate
    assert hit_rate >= 0.85, (
        f"Cache hit rate {hit_rate:.3f} < 0.85 threshold. "
        f"reads={stats.cache_read_input_tokens}, "
        f"creations={stats.cache_creation_input_tokens}. "
        f"Slot pipeline is producing byte-DIFFERENT prefixes across turns "
        f"for the same tenant — this would break Anthropic prompt cache in "
        f"production. Likely cause: dynamic interpolation (timestamps, "
        f"conversation_id, tenant_name) sneaking into a cacheable slot. "
        f"Run test_vitalia_no_pii_in_cacheable_slots.py to localize."
    )


def test_cross_tenant_cache_isolation_slot_5_varies() -> None:
    """A3 corollary: Slot 5 BRAND_VOICE differs per tenant (cache_key isolates).

    Validates that two distinct tenants under their OWN cache_keys do NOT
    cross-contaminate hits. Aurora's voice should not register as a cache hit
    when Mindful queries (different prompt_cache_key bucket), even though
    slots 1-4 + 6 are byte-equal.
    """
    stats = _SimulatedCacheStats()

    aurora = _FIXTURE_TENANTS[0]
    mindful = _FIXTURE_TENANTS[1]

    # Turn 1: Aurora — all 6 slots are creations (first time seen).
    aurora_blocks = cacheable_prefix_blocks(channel=aurora["channel"], brand_voice_compiled=aurora["brand_voice"])
    stats.record_turn(
        cache_key=prompt_cache_key(aurora["tenant_id"]),
        cacheable_blocks=aurora_blocks,
    )
    creations_after_aurora_t1 = stats.cache_creation_input_tokens
    assert creations_after_aurora_t1 > 0
    assert stats.cache_read_input_tokens == 0

    # Turn 2: Mindful — under its OWN cache_key, all 6 slots are creations
    # too (different bucket). NO cross-tenant cache hit.
    mindful_blocks = cacheable_prefix_blocks(channel=mindful["channel"], brand_voice_compiled=mindful["brand_voice"])
    stats.record_turn(
        cache_key=prompt_cache_key(mindful["tenant_id"]),
        cacheable_blocks=mindful_blocks,
    )
    assert stats.cache_creation_input_tokens > creations_after_aurora_t1, (
        "Mindful turn must register as creation (new cache bucket) — got "
        f"creations unchanged at {stats.cache_creation_input_tokens}. "
        "Cross-tenant isolation broken: Aurora's blocks should NOT count as "
        "cache hits for Mindful (different prompt_cache_key)."
    )
    assert stats.cache_read_input_tokens == 0, (
        "No reads expected on first turn of either tenant — got "
        f"reads={stats.cache_read_input_tokens}. Cross-tenant isolation broken."
    )


def test_within_tenant_repeated_turn_full_cache_hit() -> None:
    """A3 cement: within one tenant, 2nd turn = 100% cache hit on slots 1-6.

    Edge case: single tenant, 2 identical turns. After turn 1 (creation), turn 2
    must be 100% read (all 6 blocks byte-identical, all hash to existing entries).
    """
    stats = _SimulatedCacheStats()
    aurora = _FIXTURE_TENANTS[0]
    cache_key = prompt_cache_key(aurora["tenant_id"])

    # Turn 1
    blocks = cacheable_prefix_blocks(channel=aurora["channel"], brand_voice_compiled=aurora["brand_voice"])
    stats.record_turn(cache_key=cache_key, cacheable_blocks=blocks)

    # Track creation-only baseline
    baseline_creations = stats.cache_creation_input_tokens
    assert stats.cache_read_input_tokens == 0

    # Turn 2: same blocks, expect 100% read
    blocks_2 = cacheable_prefix_blocks(channel=aurora["channel"], brand_voice_compiled=aurora["brand_voice"])
    stats.record_turn(cache_key=cache_key, cacheable_blocks=blocks_2)

    assert stats.cache_creation_input_tokens == baseline_creations, (
        "Turn 2 should NOT add new creations — got "
        f"{stats.cache_creation_input_tokens} vs baseline {baseline_creations}. "
        "Slot prefix is varying within tenant — cache cement broken."
    )
    assert stats.cache_read_input_tokens == baseline_creations, (
        "Turn 2 should read EXACTLY the baseline creation tokens (1:1). "
        f"reads={stats.cache_read_input_tokens}, expected={baseline_creations}."
    )

    # 100% hit rate on the 2nd turn alone implies overall 50% (1 creation
    # turn + 1 read turn). Real V-AE-22 threshold is per session aggregate
    # (10 turns → 90%); this micro-test just asserts the per-block determinism.


def test_prompt_cache_key_canonical_str() -> None:
    """A3 sanity: prompt_cache_key coerces to str regardless of input type."""
    import uuid

    tid_uuid = uuid.uuid4()
    tid_str = "aurora-dental-ar-uuid"
    tid_int = 42

    assert prompt_cache_key(tid_uuid) == str(tid_uuid)
    assert prompt_cache_key(tid_str) == tid_str
    assert prompt_cache_key(tid_int) == "42"
