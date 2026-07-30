"""Unit tests — Wizard prompt compiler (5-slot architecture cache safety).

Per 03-arch-agentic.md § 5.2 Valeria wizard 5-slot layout + cache prefix
invariance contract. Slot 0 (system constant) + Slot 1 (wizard role from MD) +
Slot 2 (tools manifest) + Slot 3 (Valeria persona from MD) + Slot 4 (session
state, VARIABLE — not cached).

★ CRITICAL ★ slots 0-3 cacheable invariant — MUST NOT contain timestamps /
conversation_id / random UUIDs / tenant_id interpolated mid-block (silent
invalidator triggers per claude-api § Validation).

Test plan:
  1. Compiled slots 0-3 are byte-stable across calls with same compile params
     (turn -> turn safety)
  2. Compiled slot 4 IS allowed to vary turn-to-turn (variable session state)
  3. No timestamps regex / no UUIDs regex / no `conversation_id=` substring in
     slots 0-3 (cache prefix safety)
  4. Slot 1 reads wizard_role_vitalia.md content (byte-equal)
  5. Slot 3 reads valeria_persona.md content (byte-equal)
  6. cache_control marker positioned at END of slot 3 (last cacheable block)
"""

from __future__ import annotations

import re
from pathlib import Path

# Regex sentinels for cache prefix forbidden patterns.
_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
_UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_CONVERSATION_ID_RE = re.compile(r"conversation_id\s*[=:]")


def test_slots_cacheable_are_byte_stable_across_calls():
    """Same compile params → byte-identical cacheable slots (0-3)."""
    from src.modules.vitalia.copilot.workflows.wizard_prompt_compiler import (
        compile_wizard_prompt,
    )

    out1 = compile_wizard_prompt(session_state_summary="placeholder summary")
    out2 = compile_wizard_prompt(session_state_summary="placeholder summary")

    # Slots 0-3 (cacheable) byte-equal
    for slot_idx in (0, 1, 2, 3):
        assert out1.slots[slot_idx] == out2.slots[slot_idx], (
            f"Cacheable slot {slot_idx} drifted between calls — silent cache invalidator!"
        )


def test_slot_4_variable_session_state_is_isolated_from_cacheable_prefix():
    """Slot 4 session_state changes → slots 0-3 unaffected."""
    from src.modules.vitalia.copilot.workflows.wizard_prompt_compiler import (
        compile_wizard_prompt,
    )

    out1 = compile_wizard_prompt(session_state_summary="step 1")
    out2 = compile_wizard_prompt(session_state_summary="step 2 different")

    # Slot 4 differs
    assert out1.slots[4] != out2.slots[4]
    # But cacheable slots 0-3 invariant
    for slot_idx in (0, 1, 2, 3):
        assert out1.slots[slot_idx] == out2.slots[slot_idx]


def test_cacheable_slots_have_no_timestamps():
    """No ISO 8601 timestamps in cacheable prefix (silent invalidator)."""
    from src.modules.vitalia.copilot.workflows.wizard_prompt_compiler import (
        compile_wizard_prompt,
    )

    out = compile_wizard_prompt(session_state_summary="any")
    for slot_idx in (0, 1, 2, 3):
        block = out.slots[slot_idx]
        match = _TIMESTAMP_RE.search(block)
        assert match is None, (
            f"Slot {slot_idx} contains a timestamp '{match.group() if match else ''}' "
            "— cacheable prefix MUST be invariant (claude-api validation)"
        )


def test_cacheable_slots_have_no_uuids():
    """No UUIDs in cacheable prefix (silent invalidator — conv/turn ids)."""
    from src.modules.vitalia.copilot.workflows.wizard_prompt_compiler import (
        compile_wizard_prompt,
    )

    out = compile_wizard_prompt(session_state_summary="any")
    for slot_idx in (0, 1, 2, 3):
        block = out.slots[slot_idx]
        match = _UUID_RE.search(block)
        assert match is None, (
            f"Slot {slot_idx} contains a UUID '{match.group() if match else ''}' — cacheable prefix MUST be invariant"
        )


def test_cacheable_slots_have_no_conversation_id_substring():
    """No `conversation_id=` substring in cacheable prefix."""
    from src.modules.vitalia.copilot.workflows.wizard_prompt_compiler import (
        compile_wizard_prompt,
    )

    out = compile_wizard_prompt(session_state_summary="any")
    for slot_idx in (0, 1, 2, 3):
        block = out.slots[slot_idx]
        match = _CONVERSATION_ID_RE.search(block)
        assert match is None, (
            f"Slot {slot_idx} contains `conversation_id` reference — cacheable prefix MUST be invariant"
        )


def test_slot_1_loads_wizard_role_md():
    """Slot 1 content sourced from wizard_role_vitalia.md (byte-equal)."""
    from src.modules.vitalia.copilot.workflows.wizard_prompt_compiler import (
        compile_wizard_prompt,
    )

    prompts_dir = Path(__file__).resolve().parents[6] / "src" / "modules" / "vitalia" / "copilot" / "prompts"
    expected = (prompts_dir / "wizard_role_vitalia.md").read_text(encoding="utf-8")
    out = compile_wizard_prompt(session_state_summary="any")
    # The content must be embedded literally (allow surrounding header/footer added by compiler).
    assert expected.strip() in out.slots[1]


def test_slot_3_loads_valeria_persona_md():
    """Slot 3 content sourced from valeria_persona.md (byte-equal)."""
    from src.modules.vitalia.copilot.workflows.wizard_prompt_compiler import (
        compile_wizard_prompt,
    )

    prompts_dir = Path(__file__).resolve().parents[6] / "src" / "modules" / "vitalia" / "copilot" / "prompts"
    expected = (prompts_dir / "valeria_persona.md").read_text(encoding="utf-8")
    out = compile_wizard_prompt(session_state_summary="any")
    assert expected.strip() in out.slots[3]


def test_cache_marker_at_end_of_last_cacheable_slot():
    """`cache_breakpoint_index` reports the LAST cacheable slot (= 3 for 5-slot)."""
    from src.modules.vitalia.copilot.workflows.wizard_prompt_compiler import (
        compile_wizard_prompt,
    )

    out = compile_wizard_prompt(session_state_summary="any")
    assert out.cache_breakpoint_index == 3, (
        "cache_control marker must mark END of slot 3 (Valeria persona) — slot 4 is variable session state, NOT cached"
    )


def test_anthropic_messages_blocks_have_cache_control_on_last_cacheable():
    """When converted to Anthropic message blocks, cache_control set on slot 3."""
    from src.modules.vitalia.copilot.workflows.wizard_prompt_compiler import (
        as_anthropic_system_blocks,
        compile_wizard_prompt,
    )

    out = compile_wizard_prompt(session_state_summary="any")
    blocks = as_anthropic_system_blocks(out)
    # System message uses slots 0-3 as system blocks; slot 4 goes to user message turn.
    # Block 3 (Valeria persona) gets cache_control ephemeral.
    assert len(blocks) >= 4, "Should produce ≥ 4 system blocks"
    assert "cache_control" in blocks[3], "Last cacheable slot (3) needs cache_control marker"
    # Earlier slots SHOULD NOT have cache_control (only last marker forms the cache).
    for i in (0, 1, 2):
        assert "cache_control" not in blocks[i], (
            f"Block {i} must NOT have cache_control marker (Anthropic forms cache "
            "from the marker backwards) — only LAST cacheable block carries it"
        )
