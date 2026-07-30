# cap: agentic.lucas-daily-analysis
# story-origin: TBD
"""Lucas daily analysis prompt compiler — Anthropic prompt cache slots.

Story: vitalia-copilot-tools-impl T-ag-workflows-2 (R23 Opus 4.7 production AGENTIC code).

Per 03-arch-agentic.md § 5.3 (Lucas cache slots, 3-slot batch-nature):

  Slot 1 — Lucas persona MD                (cacheable per-brand · 1h TTL · batch)
  Slot 2 — Stage-specific reasoning frame  (cacheable per-stage · 1h TTL · batch)
  Slot 3 — Analysis constraints MD          (cacheable per-brand · 1h TTL · batch)
                                            ↑ cache_control marker HERE ↑
  Slot 4 — Tenant data + period stats       (variable: period + aggregates — NOT cached)

Cache TTL: 1h (batch nature — slots 1+2+3 reused across all tenants per cron run
                = high read multiple). Break-even at 3 reads (1h write 2× input,
                read 0.1× input per `claude-api`).

Cache prefix invariance (CARDINAL — silent invalidator audit):
  ❌ NO timestamps in cacheable slots (silent invalidator)
  ❌ NO `{tenant_name}` interpolated mid-block (silent invalidator)
  ❌ NO conversation_id / turn counter (silent invalidator)
  ❌ NO random UUIDs in cacheable text
  ✅ `{stage}` IS allowed in slot 2 (per-stage cached separately — frame template
     pre-rendered once per stage; cache key includes stage value)

Validation (per `claude-api` § Validation hooks — mandatory):
  Every LLM call MUST log `cache_creation_input_tokens` + `cache_read_input_tokens`.
  If `cache_read_input_tokens` stays 0 across iter 2+ of the SAME stage in the
  SAME run → silent invalidator → audit FAIL (`test_vitalia_no_pii_in_cacheable_slots.py`).

Anti-duplication §0 audit (Step 0 GATE):
  - Reads `.md` files via `pathlib` (stdlib).
  - No equivalent compiler in `core/luana-core-*/` (Lucas-specific 3-slot batch
    layout — Adrián has 6-slot, Valeria has 5-slot per arch § 5).
  - The MD files are SSoT — this compiler ASSEMBLES them, NEVER duplicates content.

downstream-regression-na: brand-local prompt compiler; no cross-brand consumers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ──────────────────────────────────────────────────────────────────────────
# Slot file resolution — anchored to the prompts/ directory next to this
# module. NEVER hardcode absolute paths; package-relative is portable across
# dev / docker / CI.
# ──────────────────────────────────────────────────────────────────────────

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

_PERSONA_FILE = "lucas_growth_setter_role.md"
_STAGE_FRAME_FILE = "lucas_stage_reasoning_frame.md"
_CONSTRAINTS_FILE = "analysis_constraints.md"


# Magic string the test suite asserts is present at the slot boundary.
# Engine LLM router may interpret this as `{"cache_control": {"type": "ephemeral",
# "ttl": "1h"}}` when assembling the Anthropic message envelope; tests assert
# the textual marker is present so prefix is byte-identical across runs.
CACHE_BOUNDARY_MARKER = "<!-- CACHE_CONTROL_EPHEMERAL_1H_BOUNDARY -->"


@dataclass(frozen=True, slots=True)
class CompiledLucasPrompt:
    """Compiled prompt envelope ready for LLM dispatch.

    Frozen + slots — defensive against accidental mutation that could alter
    cache prefix bytes between successive turns of the same run.

    Attributes:
        cacheable_prefix: slots 1+2+3 concatenated with CACHE_BOUNDARY_MARKER
                          terminating the cacheable region.
        variable_suffix:  slot 4 — period + tenant aggregates JSON (NOT cached).
        full_prompt:      cacheable_prefix + "\\n\\n" + variable_suffix (convenience
                          for non-Anthropic providers).
        stage:            stage value used for slot 2 selection (cache key partition).
    """

    cacheable_prefix: str
    variable_suffix: str
    full_prompt: str
    stage: str


class LucasAnalysisPromptCompiler:
    """Assemble Lucas analysis LLM prompt with Anthropic prompt cache slot layout.

    Slot 1 + 2 + 3 are read once at construction (file I/O minimised — single
    pass per compiler instance) and reused for every stage compile call.
    Slot 2 is interpolated with `{stage}` (the only allowed cache-key partition).
    Slot 4 is composed fresh per call from `period` + `tenant_data`.

    Usage:
        compiler = LucasAnalysisPromptCompiler()
        compiled = compiler.compile(
            stage="attraction",
            period="2026-05",
            tenant_data={"channel_breakdown": {...}, "metrics_summary": {...}},
        )
        # → compiled.cacheable_prefix bytes-identical across stages with same {stage}
        # → compiled.variable_suffix differs per run (tenant data + period)
    """

    def __init__(
        self,
        *,
        prompts_dir: Path | None = None,
    ) -> None:
        """Load slot MDs once at construction.

        Args:
            prompts_dir: Override path to prompts directory (test injection).
                         Defaults to package-relative `agentic/lucas/prompts/`.
        """
        self._prompts_dir = prompts_dir or _PROMPTS_DIR

        # Read slot 1 + slot 3 once — invariant per compiler lifetime.
        self._persona_md = self._read_md(_PERSONA_FILE)
        self._constraints_md = self._read_md(_CONSTRAINTS_FILE)

        # Slot 2 has `{stage}` interpolation — read template once, interpolate
        # per compile call. Note: actual current
        # `lucas_stage_reasoning_frame.md` does NOT use `{stage}` placeholder
        # (it documents all 5 stages in a table). We preserve the template
        # contract (str → str) for future per-stage frame variants without
        # breaking cache prefix byte equality.
        self._stage_frame_template = self._read_md(_STAGE_FRAME_FILE)

    def _read_md(self, filename: str) -> str:
        """Read a slot MD file from prompts/ directory."""
        path = self._prompts_dir / filename
        if not path.is_file():
            raise FileNotFoundError(
                f"Lucas prompt slot file missing: {path}. T-ag-tools-3 cement was expected to create this file.",
            )
        return path.read_text(encoding="utf-8")

    def compile(  # noqa: A003 — Python's `compile` is a different builtin
        self,
        *,
        stage: str,
        period: str,
        tenant_data: dict[str, Any] | None = None,
    ) -> CompiledLucasPrompt:
        """Compile cacheable_prefix + variable_suffix for a given stage + period.

        Args:
            stage: Stage value used for slot 2 cache-key partition.
                   MUST be one of the 5 design stages (attraction, qualification,
                   reservation, adoption, expansion). Caller validates.
            period: YYYY-MM month-granular period string. Goes into slot 4.
            tenant_data: Optional tenant aggregates dict (channel_breakdown,
                         metrics_summary). Goes into slot 4. None → empty dict.

        Returns:
            CompiledLucasPrompt with cache-safe boundary.

        Raises:
            ValueError: If `period` is not a valid YYYY-MM string.
        """
        if not self._is_valid_period(period):
            raise ValueError(f"Invalid period format (expected YYYY-MM): {period!r}")

        # ── Slot 2 — stage-specific reasoning frame ──────────────────────
        # Substitute `{stage}` if template contains it; otherwise emit as-is.
        # Either way the result is deterministic per stage value (cache safe).
        slot_2 = self._stage_frame_template.replace("{stage}", stage)

        # ── Cacheable region: slot 1 + slot 2 + slot 3 + boundary ────────
        # Sandwich slot order is INVARIANT — reordering breaks cache prefix.
        cacheable_prefix = (
            "# === SLOT 1: Lucas growth setter persona ===\n"
            f"{self._persona_md.rstrip()}\n\n"
            "# === SLOT 2: Stage-specific reasoning frame ===\n"
            f"{slot_2.rstrip()}\n\n"
            "# === SLOT 3: Analysis constraints ===\n"
            f"{self._constraints_md.rstrip()}\n\n"
            f"{CACHE_BOUNDARY_MARKER}\n"
        )

        # ── Variable suffix: slot 4 — period + tenant data ───────────────
        # Stable JSON serialisation (sort_keys=True) so identical tenant_data
        # produces byte-equal suffix — useful for diff-based debugging when
        # cache hit rate dips unexpectedly.
        td = tenant_data or {}
        variable_suffix = (
            "# === SLOT 4: Tenant analysis context (variable, NOT cached) ===\n"
            f"Period: {period}\n"
            f"Stage: {stage}\n\n"
            "Tenant data (aggregates only — NO PHI per HIPAA-lite cardinal):\n"
            "```json\n"
            f"{json.dumps(td, ensure_ascii=False, sort_keys=True, indent=2)}\n"
            "```\n"
        )

        full_prompt = f"{cacheable_prefix}\n{variable_suffix}"

        return CompiledLucasPrompt(
            cacheable_prefix=cacheable_prefix,
            variable_suffix=variable_suffix,
            full_prompt=full_prompt,
            stage=stage,
        )

    @staticmethod
    def _is_valid_period(period: str) -> bool:
        """Validate YYYY-MM period string (e.g. "2026-05")."""
        if not isinstance(period, str) or len(period) != 7 or period[4] != "-":
            return False
        year_str, month_str = period.split("-", 1)
        if not (year_str.isdigit() and month_str.isdigit()):
            return False
        month = int(month_str)
        return 1 <= month <= 12


__all__ = [
    "CACHE_BOUNDARY_MARKER",
    "CompiledLucasPrompt",
    "LucasAnalysisPromptCompiler",
]
