# cap: sales_agent.honor-mode-bridge
"""OLA-2 ``match_service_and_specialist`` — engine-ABI execution + shape tests.

Native sync ``(state, db) -> dict`` (ESC-17 ABI): service_intent → product (name
ilike) → offer_service_specialist_links → doctor(s). Primary = first shareable
doctor (visible_en_landing + active + public_slug → URL); callbacks = the rest.
``tenant_id`` is authoritative from state (never the LLM).

DB-free assertions (ABI + fast paths); the real match against seeded data is
live-verified in-container (real merged registry + real dev DB).
"""

from __future__ import annotations

import json

from src.modules.vitalia.sales_agent.tools.match_service_and_specialist import (
    match_service_and_specialist,
)


def test_handler_is_sync_callable_engine_abi() -> None:
    """Callable exactly as node_tool_executor dispatches: fn(state, db)."""
    out = match_service_and_specialist({"_pending_tool": {"args": {}}}, db=None)
    assert isinstance(out, dict)
    assert out["status"] == "error"  # missing tenant_id → structured early return
    json.dumps(out, ensure_ascii=False)


def test_missing_intent_returns_structured() -> None:
    """A tenant but no service_intent → structured dict (not a crash)."""
    out = match_service_and_specialist(
        {"tenant_id": "e69a691d-070e-5caf-a053-6e74642ec100", "_pending_tool": {"args": {}}},
        db=None,
    )
    assert isinstance(out, dict)
    assert out["status"] in {"success", "not_found", "error"}
    json.dumps(out, ensure_ascii=False)
