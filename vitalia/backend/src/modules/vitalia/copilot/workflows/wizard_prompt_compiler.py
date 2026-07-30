# cap: copilot.valeria-wizard-onboarding-agentic
# story-origin: TBD
"""Wizard prompt compiler — 5-slot architecture (Anthropic prompt caching).

Per 03-arch-agentic.md § 5.2 + claude-api § Validation:

```
SLOT 0 — System role (engine constant)              cacheable, invariant
SLOT 1 — Wizard role + Vitalia onboarding ctx       cacheable, per-brand
SLOT 2 — Tools manifest (4 wizard tools)            cacheable, per-graph
SLOT 3 — Valeria persona prompt                     cacheable, per-brand
                                                    ↑ cache_control HERE ↑
SLOT 4 — Conversation + current slots state + user  variable (NOT cached)
```

★ CRITICAL ★ slots 0-3 are cache prefix invariant — MUST NOT contain
timestamps, conversation_id, random UUIDs, or per-tenant interpolation. Cache
forms from the LAST ``cache_control`` marker BACKWARDS (Anthropic semantics);
only slot 3 carries the marker, and slots 0-2 are implicitly cached.

Anti-duplication audit:
  - This compiler is brand-specific (Valeria wizard layout). The sales_agent
    compiler v2 (6-slot layout) lives in engine `core/luana-core-sales-agent/`
    and is consumed by Adrián directly — NOT mirrored here.
  - Engine has no per-tenant onboarding wizard, so no engine equivalent to lift
    from. If a second brand emerges with similar wizard onboarding, lift this
    compiler to engine `core/luana-core-copilot/` via promotion proposal.

Cache TTL: 5 min default per-conversation (sufficient for 10-20 min active
wizard session). Validation: every LLM call MUST log
``cache_creation_input_tokens`` + ``cache_read_input_tokens`` (callback handler
already does this in ``VitaliaCopilotCallbackHandler``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# ════════════════════════════════════════════════════════════════════════════
# Slot 0 — Engine system role (invariant cross-tenant)
# ════════════════════════════════════════════════════════════════════════════
#
# Kept literal here (no env var, no timestamp). When the engine surfaces an
# equivalent constant via luana_core_copilot, switch to import — for now this
# is the brand-side baseline that the wizard supervisor uses as the first
# cacheable system block.

_SLOT_0_SYSTEM_ROLE: str = (
    "# System role\n"
    "\n"
    "You operate as the Vitalia onboarding wizard supervisor. You orchestrate "
    "Valeria, a specialist persona that guides medical clinic administrators "
    "through their initial account setup. You route between extraction, slot "
    "questions, live preview, and completion phases. You NEVER process PHI; "
    "the wizard collects business configuration only."
)


# ════════════════════════════════════════════════════════════════════════════
# Slot 2 — Tools manifest (per-graph invariant; mirrors Extension SDK EP-3 wiring)
# ════════════════════════════════════════════════════════════════════════════
#
# Static literal — 4 wizard tools per Slice 1 (extract_tenant_context +
# confirm_slot + simulate_personality + complete_onboarding). Re-generation
# from the registry would inject runtime-varying ordering / formatting, which
# would be a silent cache invalidator. Kept as a stable string here; the
# arch fitness gate `test_extension_sdk_registration.py` already ensures the
# four tools stay registered. Update this constant in the SAME COMMIT as any
# tool registry change.

_SLOT_2_TOOLS_MANIFEST: str = (
    "# Tools manifest (4 wizard tools)\n"
    "\n"
    "You may call exactly these tools, with the indicated semantics:\n"
    "\n"
    "1. `extract_tenant_context(draft_id, tenant_id, url?, text_content?)`\n"
    "   Spawn the sandboxed extractor subagent to read a URL or pasted text.\n"
    "   Returns a short summary; details persisted by the service layer.\n"
    "\n"
    "2. `confirm_slot(draft_id, tenant_id, slot_id, value, source?)`\n"
    "   Mark a wizard slot user-confirmed (confidence 1.0). Use ONLY after the\n"
    "   user explicitly confirmed (yes/dale/ok/perfecto-like).\n"
    "\n"
    "3. `simulate_personality(tenant_id, profile_partial, scenario)`\n"
    "   Produce a live preview text sample. Rate limited 5 calls/min/tenant +\n"
    "   cached 10 min TTL by (profile_partial, scenario).\n"
    "\n"
    "4. `complete_onboarding(draft_id, tenant_id, user_id)`\n"
    "   Finalize the session — compile full personality, activate the tenant,\n"
    "   emit TenantOnboardedEvent. Only call once all required slots are\n"
    "   confirmed and the user accepted the preview.\n"
)


# ════════════════════════════════════════════════════════════════════════════
# Cache breakpoint config
# ════════════════════════════════════════════════════════════════════════════

_CACHE_BREAKPOINT_INDEX: int = 3
"""The LAST cacheable slot index — cache_control marker goes here.

Anthropic prompt cache forms cache from the marker BACKWARDS, so a single
marker at slot 3 implicitly caches slots 0-3 contiguously.
"""


# ════════════════════════════════════════════════════════════════════════════
# Prompt loader (file-system reads, byte-equal across calls)
# ════════════════════════════════════════════════════════════════════════════


def _prompts_dir() -> Path:
    """Return absolute path to the wizard prompts directory."""
    return Path(__file__).resolve().parent.parent / "prompts"


def _load_slot_1_wizard_role() -> str:
    """Load slot 1 from wizard_role_vitalia.md (per-brand cacheable invariant)."""
    return (_prompts_dir() / "wizard_role_vitalia.md").read_text(encoding="utf-8").strip()


def _load_slot_3_valeria_persona() -> str:
    """Load slot 3 from valeria_persona.md (per-brand cacheable invariant)."""
    return (_prompts_dir() / "valeria_persona.md").read_text(encoding="utf-8").strip()


# ════════════════════════════════════════════════════════════════════════════
# Compiled prompt
# ════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CompiledWizardPrompt:
    """Output of ``compile_wizard_prompt``.

    Attributes:
        slots: Tuple of 5 strings — slot 0..4 inclusive. Slots 0..3 cacheable;
            slot 4 variable (NOT cached).
        cache_breakpoint_index: Index of the LAST cacheable slot. Always 3 in
            the 5-slot wizard layout.
    """

    slots: tuple[str, str, str, str, str]
    cache_breakpoint_index: int = field(default=_CACHE_BREAKPOINT_INDEX)


def compile_wizard_prompt(*, session_state_summary: str) -> CompiledWizardPrompt:
    """Compose the 5-slot wizard system prompt.

    Args:
        session_state_summary: Free-form summary of the current wizard state
            (which slots remain pending, mode, last user message, etc.). This
            is the VARIABLE portion (slot 4) — caller MUST keep slots 0-3 free
            of dynamic content. The compiler enforces this by sourcing slots
            0-3 from invariant constants/files only.

    Returns:
        CompiledWizardPrompt with the 5 slot strings and the cache marker
        index.

    Invariants enforced (per test_wizard_prompt_compiler.py):
        - Slots 0-3 byte-stable across calls with identical compile params
        - Slots 0-3 contain NO timestamps / UUIDs / conversation_id substrings
        - Slot 4 varies freely (not cached)
    """
    slot_0 = _SLOT_0_SYSTEM_ROLE
    slot_1 = _load_slot_1_wizard_role()
    slot_2 = _SLOT_2_TOOLS_MANIFEST
    slot_3 = _load_slot_3_valeria_persona()
    slot_4 = _format_session_state_slot(session_state_summary)
    return CompiledWizardPrompt(slots=(slot_0, slot_1, slot_2, slot_3, slot_4))


def _format_session_state_slot(summary: str) -> str:
    """Format the variable session state slot (slot 4)."""
    return (
        "# Current session state\n"
        "\n"
        f"{summary}\n"
        "\n"
        "Decide the next action based on the state above and the conversation "
        "history."
    )


def as_anthropic_system_blocks(compiled: CompiledWizardPrompt) -> list[dict]:
    """Convert compiled slots into Anthropic Messages API ``system`` blocks.

    Slots 0-3 → system blocks. Slot 4 is NOT a system block — caller appends
    it to the user-message turn (or as a state-injection user message). Only
    the LAST cacheable block carries ``cache_control`` (Anthropic forms the
    cache from the marker backwards).

    Returns:
        List of 4 dicts — each ``{"type": "text", "text": "..."}`` with the
        last one also carrying ``cache_control: {"type": "ephemeral"}``.
    """
    blocks: list[dict] = []
    for i, text in enumerate(compiled.slots[: compiled.cache_breakpoint_index + 1]):
        block: dict = {"type": "text", "text": text}
        if i == compiled.cache_breakpoint_index:
            block["cache_control"] = {"type": "ephemeral"}
        blocks.append(block)
    return blocks


__all__ = [
    "CompiledWizardPrompt",
    "as_anthropic_system_blocks",
    "compile_wizard_prompt",
]

# voseo-allowed: doc/comentario interno citando glosario voseo, no user-facing
