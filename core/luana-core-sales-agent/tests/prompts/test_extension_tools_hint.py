"""Tier-2 (multibrand-graph-runtime 2026-06-22) — brand extension tools must be
advertised to the LLM in the cacheable STATIC_TOOLS_HINT slot.

The seam: a brand registers its own sales-agent tools via EP-3 into the engine
``ToolRegistry`` singleton at FastAPI lifespan. For the LLM to actually *call*
``vitalia.book_appointment`` it must first *know* the tool exists — i.e. the tool
must appear in the system prompt tools-hint. Before this ticket ``_TOOLS_HINT``
was a hardcoded string divorced from the registry → brand tools were dispatchable
(nodes.py reads ``merged_tools()``) but invisible to the LLM → never called.

CACHE BOUNDARY INVARIANT (the footgun): STATIC_TOOLS_HINT is slot 2 — cacheable.
The rendered brand-tool list MUST be stage-independent (brands register once at
lifespan, never per-turn) so the cacheable prefix stays byte-stable across turns.
Stage-filtering here would make the prefix vary with ``current_state`` and shatter
the prompt cache for every tenant — see
``test_build_specialist_system_prompt.py::test_current_state_change_does_not_alter_prefix``.

ADVERTISED == DISPATCHABLE: every advertised brand tool is in ``merged_tools()``
(what ``node_tool_executor`` dispatches), and every registered brand tool is
advertised. No phantom tools either way.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any

import pytest

from luana_core_sales_agent.application.orchestrator.state import create_initial_state
from luana_core_sales_agent.application.prompts.compose import (
    CACHE_BOUNDARY_MARKER,
    SpecialistRole,
    build_specialist_system_prompt,
)
from luana_core_sales_agent.application.tools.registry import get_tool_registry


@pytest.fixture(autouse=True)
def _clean_registry() -> Iterator[None]:
    """Each test owns a pristine extension-tool registry (process singleton)."""
    reg = get_tool_registry()
    reg.reset()
    yield
    reg.reset()


def _state(**overrides: Any) -> dict[str, Any]:
    state = create_initial_state(
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        agent_identity="# IDENTIDAD\n\nAsistente de **Clínica Test**.",
        tenant_config={"brand_name": "Clínica Test"},
        channel_type="whatsapp",
    )
    state.update(overrides)
    return state


def _register(
    name: str, *, description: str, tool_groups: tuple[str, ...] = ()
) -> None:
    def _handler(state: Any, db: Any = None) -> dict[str, Any]:  # noqa: ARG001
        return {"status": "ok"}

    get_tool_registry().register_tool_from_extension(
        name=name,
        handler=_handler,
        description=description,
        tool_groups=tool_groups,
    )


def _prefix(prompt: str) -> str:
    return prompt.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[0]


class TestBrandToolsAdvertised:
    def test_registered_tool_name_and_description_appear_in_prompt(self) -> None:
        _register(
            "vitalia.book_appointment",
            description="Agenda una cita con el doctor disponible.",
        )
        prompt = build_specialist_system_prompt(_state(), SpecialistRole.CLOSER)
        assert "vitalia.book_appointment" in prompt
        assert "Agenda una cita con el doctor disponible." in prompt

    def test_brand_tool_lives_in_cacheable_prefix(self) -> None:
        _register(
            "vitalia.share_doctor_profile", description="Comparte el perfil del doctor."
        )
        prompt = build_specialist_system_prompt(_state(), SpecialistRole.PRODUCT_EXPERT)
        # The tools-hint is a cacheable slot → brand tool must be BEFORE the boundary.
        assert "vitalia.share_doctor_profile" in _prefix(prompt)

    def test_all_registered_tools_advertised(self) -> None:
        names = [
            "vitalia.book_appointment",
            "vitalia.match_service_and_specialist",
            "vitalia.share_doctor_profile",
        ]
        for n in names:
            _register(n, description=f"desc {n}")
        prompt = build_specialist_system_prompt(_state(), SpecialistRole.CLOSER)
        for n in names:
            assert n in prompt, f"{n} registered but not advertised"


class TestCacheSafety:
    """Brand-tool rendering must not poison the cacheable prefix."""

    def test_empty_registry_leaves_prefix_unchanged_vs_no_brand_tools(self) -> None:
        # With no brand tools, the cacheable prefix must equal a fresh render
        # (back-compat: engine-only behaviour is byte-identical).
        a = _prefix(build_specialist_system_prompt(_state(), SpecialistRole.QUALIFIER))
        b = _prefix(build_specialist_system_prompt(_state(), SpecialistRole.QUALIFIER))
        assert a == b
        # And no brand section header leaks when there are no brand tools.
        assert "marca" not in a.lower() or "herramientas de marca" not in a.lower()

    def test_stage_change_does_not_alter_prefix_with_brand_tools(self) -> None:
        # THE footgun guard: brand tools in the cacheable slot must be
        # stage-independent. Prefix identical across stages.
        _register(
            "vitalia.book_appointment",
            description="Agenda cita.",
            tool_groups=("closing",),
        )
        a = build_specialist_system_prompt(
            _state(current_state="rapport"), SpecialistRole.QUALIFIER
        )
        b = build_specialist_system_prompt(
            _state(current_state="closing"), SpecialistRole.QUALIFIER
        )
        assert _prefix(a) == _prefix(b)

    def test_two_consecutive_renders_byte_identical(self) -> None:
        _register("vitalia.book_appointment", description="Agenda cita.")
        state = _state()
        a = build_specialist_system_prompt(state, SpecialistRole.CLOSER)
        b = build_specialist_system_prompt(state, SpecialistRole.CLOSER)
        assert _prefix(a) == _prefix(b)

    def test_render_order_deterministic_regardless_of_registration_order(self) -> None:
        _register("vitalia.zebra", description="z")
        _register("vitalia.alpha", description="a")
        first = _prefix(build_specialist_system_prompt(_state(), SpecialistRole.CLOSER))
        get_tool_registry().reset()
        _register("vitalia.alpha", description="a")
        _register("vitalia.zebra", description="z")
        second = _prefix(
            build_specialist_system_prompt(_state(), SpecialistRole.CLOSER)
        )
        assert first == second


class TestAdvertisedEqualsDispatchable:
    def test_every_advertised_brand_tool_is_dispatchable(self) -> None:
        names = ["vitalia.book_appointment", "vitalia.share_doctor_profile"]
        for n in names:
            _register(n, description=f"desc {n}")
        prompt = build_specialist_system_prompt(_state(), SpecialistRole.CLOSER)
        merged = get_tool_registry().merged_tools()
        for n in names:
            assert n in prompt, f"{n} not advertised"
            assert n in merged, f"{n} advertised but not dispatchable"
