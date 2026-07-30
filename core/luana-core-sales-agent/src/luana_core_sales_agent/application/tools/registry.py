"""Stage-scoped tool registry for the sales agent (S8).

Today the LLM sees the full ``TOOL_REGISTRY`` regardless of stage. That
made sense early — but post-S8 we now have ~14 tools and some are only
appropriate in specific stages (e.g. ``create_booking_link`` should not
appear in ``rapport`` because the lead is unqualified). This registry
filters tools per stage without altering the existing dict-style
contract.

DRY:

* ``TOOL_REGISTRY`` (in ``application/agents/sales/tools.py``) remains
  the SSoT for tool implementations.
* This file owns the **scoping** map — adding a new stage or moving a
  tool between stages touches one place.

Cohesion:

* ``ALWAYS_AVAILABLE`` for cross-stage utilities (escalation, intent).
* ``STAGE_TOOL_SCOPE`` for stage-specific gates.

Coupling:

* Imports only ``TOOL_REGISTRY`` symbol — no orchestrator, no LLM, no
  state. Pure mapping.
* Tests assert that every name in ``ALWAYS_AVAILABLE`` plus the
  union of ``STAGE_TOOL_SCOPE.values()`` exists in ``TOOL_REGISTRY``.
"""

# [SALES-AGENT-S8-TOOLS]  # noqa: ERA001

from __future__ import annotations

from typing import Any

# ──────────────────────────────────────────────────────────────
# Scoping map
# ──────────────────────────────────────────────────────────────


ALWAYS_AVAILABLE: frozenset[str] = frozenset(
    {
        # Safety net — every stage must allow these.
        "escalate_to_human",
        "recommend_product",
        # Read-only verifications — useful at any stage post-creation.
        "verify_booking_status",
        "check_schedule",
        "check_payment_status",
        # S9 — payment status check is cross-stage (lead may ask mid-rapport).
        "verify_payment_status",
    },
)


STAGE_TOOL_SCOPE: dict[str, frozenset[str]] = {
    "rapport": frozenset(),
    "discovery": frozenset(
        {
            "get_available_slots",
            "list_public_editions",
        },
    ),
    "presentation": frozenset(
        {
            "get_available_slots",
            "create_booking_link",
            "list_public_editions",
            "list_waitlist",
        },
    ),
    "closing": frozenset(
        {
            "create_booking_link",
            "get_available_slots",
            "send_payment_link",
            "create_enrollment",
            "generate_payment_link",
            "mark_enrollment_paid_manual",
            "promote_waitlist_to_edition",
            "list_public_editions",
            "list_waitlist",
            # S9 — payment lifecycle tools
            "create_payment_link",
            "grant_access",
        },
    ),
}


def get_tools_for_stage(
    stage: str,
    tool_registry: dict[str, Any],
) -> dict[str, Any]:
    """Return ``{name: callable}`` filtered to the stage's allowed set.

    Unknown stages fall back to ``rapport`` (most restrictive). Tools
    referenced in the scoping but missing from ``tool_registry`` are
    silently skipped — keeps the runtime resilient if a tool is
    deactivated for a tenant via feature flag.
    """
    stage_set = STAGE_TOOL_SCOPE.get(stage, STAGE_TOOL_SCOPE["rapport"])
    allowed = ALWAYS_AVAILABLE | stage_set
    return {name: tool_registry[name] for name in allowed if name in tool_registry}


def is_tool_available_in_stage(tool_name: str, stage: str) -> bool:
    """Return True if ``tool_name`` is allowed at ``stage``."""
    stage_set = STAGE_TOOL_SCOPE.get(stage, STAGE_TOOL_SCOPE["rapport"])
    if tool_name in (ALWAYS_AVAILABLE | stage_set):
        return True
    # Tier-2 (multibrand-graph-runtime): a brand extension tool is allowed at a stage when
    # its declared stage_scope includes the stage (or it declares none → cross-stage).
    return get_tool_registry().is_extension_tool_in_stage(tool_name, stage)


# ──────────────────────────────────────────────────────────────
# Tier-2 (2026-06-22 · multibrand-graph-runtime) — stateful tool registry.
#
# Hexagonal seam: the engine ships a STATIC tool set
# (application/agents/sales/tools.py::TOOL_REGISTRY). Brands own their own business tools
# and register them via EP-3 (sales_agent_tool_register) → the SDK
# `_SalesAgentToolRegistryAdapter` calls `register_tool_from_extension` on the singleton
# below at brand FastAPI lifespan. Dispatch (agents/sales/nodes.py), the prompt tool-hint
# (application/prompts/compose.py) and stage-scope all read the MERGED view, so a
# brand-registered tool is dispatchable, advertised to the LLM, and stage-gated — i.e.
# "each brand owns its own tools" is real, not aspirational.
# ──────────────────────────────────────────────────────────────


class ExtensionTool:
    """A brand-registered sales-agent tool (EP-3 ToolDef projected into the engine)."""

    __slots__ = ("description", "handler", "input_schema", "name", "stage_scope")

    def __init__(
        self,
        *,
        name: str,
        handler: Any,
        description: str = "",
        input_schema: dict[str, Any] | None = None,
        tool_groups: tuple[str, ...] = (),
    ) -> None:
        self.name = name
        self.handler = handler
        self.description = description
        self.input_schema = input_schema or {}
        # tool_groups doubles as the stage scope hint (e.g. ("closing","presentation")).
        # Empty → cross-stage (available everywhere), like ALWAYS_AVAILABLE engine tools.
        self.stage_scope: frozenset[str] = frozenset(tool_groups)


class ToolRegistry:
    """Stateful registry merging engine tools with brand extension tools (EP-3).

    Singleton per process (see ``get_tool_registry``). The engine static set stays the
    SSoT for engine tools; this object only adds the brand layer + the merged view the
    runtime reads. Pure in-memory; no I/O.
    """

    def __init__(self) -> None:
        self._extension_tools: dict[str, ExtensionTool] = {}

    def register_tool_from_extension(
        self,
        *,
        name: str,
        handler: Any,
        description: str = "",
        input_schema: dict[str, Any] | None = None,
        tool_groups: tuple[str, ...] = (),
    ) -> None:
        """Register a brand tool. Public surface the SDK adapter delegates to."""
        self._extension_tools[name] = ExtensionTool(
            name=name,
            handler=handler,
            description=description,
            input_schema=input_schema,
            tool_groups=tool_groups,
        )

    def merged_tools(self) -> dict[str, Any]:
        """Return ``{name: handler}`` = engine tools ⊕ brand extension tools.

        Brand tools override engine homonyms last-write-wins (a brand may specialise an
        engine tool). Lazy import of the engine static set avoids a circular import.
        """
        from luana_core_sales_agent.application.agents.sales.tools import (  # noqa: PLC0415
            TOOL_REGISTRY as _ENGINE_TOOLS,
        )

        merged: dict[str, Any] = dict(_ENGINE_TOOLS)
        for name, tool in self._extension_tools.items():
            merged[name] = tool.handler
        return merged

    def extension_tools(self) -> dict[str, ExtensionTool]:
        """Return the brand-registered tools (for the prompt tool-hint composer)."""
        return dict(self._extension_tools)

    def is_extension_tool_in_stage(self, tool_name: str, stage: str) -> bool:
        """True if a brand tool is allowed at ``stage`` (empty scope → cross-stage)."""
        tool = self._extension_tools.get(tool_name)
        if tool is None:
            return False
        return not tool.stage_scope or stage in tool.stage_scope

    def reset(self) -> None:
        """Drop all brand tools (test isolation)."""
        self._extension_tools.clear()


_tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Return the process-singleton sales-agent ToolRegistry (engine ⊕ brand tools)."""
    return _tool_registry


def _sanitize_tool_name(name: str) -> str:
    """Make a tool name valid for OpenAI/DeepSeek function-calling.

    Providers require function names to match ``^[a-zA-Z0-9_-]+$`` — a DOT is
    rejected with a 400. Brand EP-3 tools are namespaced ``{brand}.{tool}``, so
    swap ``.`` → ``-`` (both allowed). No engine/brand tool name contains a
    literal ``-``, so :func:`desanitize_tool_name` reverses it losslessly.
    """
    return name.replace(".", "-")


def desanitize_tool_name(name: str) -> str:
    """Reverse :func:`_sanitize_tool_name` so the dispatcher looks up the real name."""
    return name.replace("-", ".")


def extension_tool_schemas(stage: str | None = None) -> list[dict[str, Any]]:
    """OpenAI function schemas for the brand EP-3 tools — for NATIVE function-calling.

    The text-``[TOOL_REQUEST]`` protocol is unreliable for getting models to dispatch
    brand tools (measured 0→25%); passing these schemas to the LLM via ``bind_tools``
    makes dispatch reliable. Each brand tool self-describes (name + description + its own
    ``input_schema``) → hexagonal, no brand hardcoding. Stage-scoped when ``stage`` is
    given (only tools whose ``stage_scope`` includes it). Engine tools are NOT included —
    they stay on the working text protocol (closer's concrete examples).
    """
    reg = get_tool_registry()
    schemas: list[dict[str, Any]] = []
    for name, tool in reg.extension_tools().items():
        if stage is not None and not reg.is_extension_tool_in_stage(name, stage):
            continue
        schemas.append(
            {
                "type": "function",
                "function": {
                    "name": _sanitize_tool_name(name),
                    "description": tool.description or name,
                    "parameters": tool.input_schema
                    or {"type": "object", "properties": {}},
                },
            }
        )
    return schemas
