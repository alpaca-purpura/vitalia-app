# cap: sales_agent.honor-mode-bridge
"""ESC-17 arch gate — every EP-3 sales_agent tool handler MUST be a plain SYNC
callable matching the engine dispatch ABI ``tool_fn(state, db) -> dict``.

The engine sales graph dispatches ``merged_tools()[name](state, db=...)`` SYNC
(``application/agents/sales/nodes.py::node_tool_executor``). A LangChain
StructuredTool / coroutine function is NOT callable that way
(``TypeError: 'StructuredTool' object is not callable``) → the tool errors on
dispatch and never executes (``registered != executable`` — the ESC-17 embudo).

This test fails the build if any brand EP-3 handler regresses to an
async / StructuredTool shape. SSoT:
docs/learnings/2026-06-22-ep3-tool-handler-abi-mismatch.md
"""

from __future__ import annotations

import inspect

from luana_core_extension_sdk._adapters import _SalesAgentToolRegistryAdapter
from luana_core_extension_sdk.extension_points import ExtensionPointRegistry
from luana_core_sales_agent.application.tools.registry import ToolRegistry

from src.modules.vitalia.extensions import register_all


def _registered_handlers() -> dict:
    """Run the real ``register_all`` into a fresh ToolRegistry and return the
    brand EP-3 tools exactly as the engine would see them at lifespan."""
    tr = ToolRegistry()
    reg = ExtensionPointRegistry(
        sales_agent_tool_registry_adapter=_SalesAgentToolRegistryAdapter(tr),
    )
    register_all(reg)
    return tr.extension_tools()


def test_all_ep3_handlers_are_plain_sync_callables() -> None:
    handlers = _registered_handlers()
    assert handlers, "register_all should register >=1 EP-3 tool"

    offenders: list[tuple[str, str]] = []
    for name, tool in handlers.items():
        handler = tool.handler
        if not callable(handler):
            offenders.append((name, "not callable"))
        elif inspect.iscoroutinefunction(handler):
            offenders.append((name, "coroutine function (async)"))
        elif type(handler).__name__ in ("StructuredTool", "Tool", "BaseTool"):
            offenders.append((name, f"LangChain {type(handler).__name__}"))
        elif hasattr(handler, "ainvoke") or hasattr(handler, "invoke"):
            offenders.append((name, "LangChain Runnable (has invoke/ainvoke)"))

    assert not offenders, (
        "EP-3 handlers violate the sync (state, db) -> dict ABI (ESC-17). "
        f"Offenders: {offenders}. Wrap async StructuredTools with "
        "sales_agent.tool_bridge.structured_tool_adapter, or write a native sync handler."
    )


def test_ep3_handler_accepts_state_db_signature() -> None:
    """Each handler must accept ``(state, db=...)`` per node_tool_executor."""
    handlers = _registered_handlers()
    for name, tool in handlers.items():
        handler = tool.handler
        if not callable(handler) or type(handler).__name__ in ("StructuredTool", "Tool", "BaseTool"):
            continue  # covered by the ABI test above
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())
        accepts_state = any(p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.VAR_POSITIONAL) for p in params)
        accepts_db = "db" in sig.parameters or any(p.kind == p.VAR_KEYWORD for p in params)
        assert accepts_state and accepts_db, f"{name}: signature {sig} is not (state, db=...)"
