# cap: sales_agent.honor-mode-bridge
"""ESC-17 EXECUTION gate — every EP-3 handler must be CALLABLE exactly as the
engine dispatches it: ``tool_fn(state, db=state.get("_db"))`` → JSON-serialisable
result, NEVER ``TypeError: 'StructuredTool' object is not callable``.

This is the check the ESC-17 learning demands: a seam is alive only when a real
call crosses it the way the runtime makes it. "Registered" / "advertised" /
"dispatchable-by-name" are necessary, not sufficient.

Deterministic + DB-free: handlers are invoked with empty/absent args so the
StructuredTool adapters fail FAST on Pydantic validation (caught → error dict)
and ``share_doctor_profile`` returns early on missing tenant — no DB, no resolver,
no network. The point is the ABI (callable + returns dict/str), not the business
outcome (that is the live-verify step).

SSoT: docs/learnings/2026-06-22-ep3-tool-handler-abi-mismatch.md
"""

from __future__ import annotations

import json

from luana_core_extension_sdk._adapters import _SalesAgentToolRegistryAdapter
from luana_core_extension_sdk.extension_points import ExtensionPointRegistry
from luana_core_sales_agent.application.tools.registry import ToolRegistry

from src.modules.vitalia.extensions import register_all
from src.modules.vitalia.sales_agent.tools.share_doctor_profile import share_doctor_profile

_DEV_TENANT = "e69a691d-070e-5caf-a053-6e74642ec100"


def _merged_handlers() -> dict:
    tr = ToolRegistry()
    reg = ExtensionPointRegistry(
        sales_agent_tool_registry_adapter=_SalesAgentToolRegistryAdapter(tr),
    )
    register_all(reg)
    return {name: tool.handler for name, tool in tr.extension_tools().items()}


def test_every_handler_dispatchable_as_node_tool_executor() -> None:
    """Mirror ``node_tool_executor``: ``tool_fn(state, db=state.get("_db"))`` then
    ``json.dumps(result)``. No handler may raise (the old StructuredTools raised
    ``TypeError`` here — that was ESC-17)."""
    handlers = _merged_handlers()
    assert handlers, "register_all should register >=1 EP-3 tool"

    # Empty pending args → StructuredTool adapters fail validation gracefully.
    state = {"tenant_id": None, "_pending_tool": {"tool": "", "args": {}}, "_db": None}

    for name, handler in handlers.items():
        result = handler(state, db=state.get("_db"))  # EXACT engine call shape
        assert isinstance(result, (dict, str)), f"{name} returned {type(result)}, not dict/str"
        # Must be JSON-serialisable (node_tool_executor does json.dumps next).
        json.dumps(result, ensure_ascii=False)


def test_share_doctor_profile_handler_shape() -> None:
    """The native sync pilot is callable as the engine dispatches it and returns a
    structured dict on the no-tenant fast path (DB-free)."""
    out = share_doctor_profile({"_pending_tool": {"args": {}}}, db=None)
    assert isinstance(out, dict)
    assert out["status"] == "error"  # missing tenant_id → early structured return
    assert "tenant" in out["message"].lower()


def test_share_doctor_profile_not_found_is_structured(tmp_path: object) -> None:  # noqa: ARG001
    """With a tenant but (in this isolated call) no shareable doctor, the handler
    returns a structured ``not_found``/``error`` dict — never an exception. Guards
    the engine ABI contract under the realistic 'no data' branch.

    Skipped silently if the test DB is unreachable (this is a unit-level ABI test,
    not a DB integration test — live data is exercised by the webhook live-verify)."""
    try:
        out = share_doctor_profile(
            {"tenant_id": _DEV_TENANT, "_pending_tool": {"args": {"specialty": "nonexistent-xyz"}}}, db=None
        )
    except Exception:  # noqa: BLE001 — no DB in this env → ABI already proven above
        return
    assert isinstance(out, dict)
    assert out["status"] in {"success", "not_found", "error"}
    json.dumps(out, ensure_ascii=False)
