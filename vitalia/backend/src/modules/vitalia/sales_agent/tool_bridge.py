# cap: sales_agent.honor-mode-bridge
"""ESC-17 — brand sync ``(state, db) -> dict`` adapter for EP-3 sales_agent tools.

The engine sales graph dispatches every tool SYNC
(``application/agents/sales/nodes.py::node_tool_executor``)::

    result = tool_fn(state, db=state.get("_db"))   # sync; args read FROM state; _db is None at inbound

Vitalia's real EP-3 handlers are async LangChain ``StructuredTool``s, which are
NOT callable that way (``StructuredTool(state, db)`` → ``TypeError`` → the tool
errors on dispatch and never runs — the ESC-17 embudo, *registered != executable*).

The engine ABI is the **port**; the brand **adapts** (hexagonal — the engine never
learns about LangChain). This module provides:

* ``run_async(coro)`` — run an async coroutine to completion from the SYNC graph
  node. ``node_tool_executor`` is a sync node, so LangGraph offloads it to a worker
  thread; but rather than *assume* whether a loop is running, we ALWAYS run the coro
  in a dedicated thread that owns a fresh event loop. Any DB session created inside
  therefore connects within that loop → no cross-loop asyncpg trap, and it is safe
  whether or not the caller already has a running loop.
* ``structured_tool_adapter(tool)`` — wrap an async ``StructuredTool`` as a sync
  ``(state, db) -> dict | str`` handler. Args come from the LLM ``[TOOL_REQUEST]``
  (``state["_pending_tool"]["args"]``); ``tenant_id`` / ``clinic_id`` are OVERRIDDEN
  from ``state`` (authoritative — never trust the LLM for tenant scoping);
  ``lead_id`` / ``user_id`` / ``conversation_id`` fall back to ``state`` when the LLM
  omits them. Never raises — returns a structured error dict (engine also catches).

Learning: docs/learnings/2026-06-22-ep3-tool-handler-abi-mismatch.md
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Awaitable, Callable

import structlog

logger = structlog.get_logger(__name__)

# Tenant scoping is authoritative from state — the LLM must NEVER pick the tenant.
_AUTHORITATIVE_STATE_KEYS = ("tenant_id", "clinic_id")
# Identity/context the engine seeds in state; inject only when the LLM omitted it.
_FALLBACK_STATE_KEYS = ("lead_id", "user_id", "conversation_id")

# The app's main event loop, captured at FastAPI lifespan startup (main.py).
# Async-DB coroutines are submitted HERE so they run on the loop that owns the
# shared SQLAlchemy async engine pool — eliminating the cross-loop asyncpg trap
# (see run_async). None in tests / before startup → fresh-loop fallback.
_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Register the app's main event loop (call once at FastAPI lifespan startup)."""
    global _main_loop  # noqa: PLW0603 — process-wide bridge bootstrap
    _main_loop = loop


def run_async(coro: Awaitable[Any]) -> Any:
    """Run ``coro`` to completion from the SYNC graph tool node.

    The sales graph runs ``await agent_app.ainvoke(...)`` on the app's main loop;
    sync nodes (``node_tool_executor``) are offloaded by LangGraph to a worker
    thread with no running loop. From that worker thread we **submit the coro to the
    app's main loop** via ``asyncio.run_coroutine_threadsafe`` and block on the
    result. This is the fix for the cross-loop asyncpg trap (verified 2026-06-22): a
    coroutine using an AsyncSession from the **shared** engine pool must run on the
    loop that created those pooled connections (the main loop) — running it on a
    fresh per-call loop raises ``got Future attached to a different loop`` on the 2nd
    call. Running on the main loop also makes ``book_appointment`` and the (currently
    unwired) StructuredTool DI resolvers safe.

    Fallback (no main loop registered — unit tests, or a context with no running app):
    a dedicated daemon thread with a fresh event loop. That fallback is only safe for
    coroutines that do NOT reuse the shared pool across calls (CPU-bound, NullPool,
    or own-connection) — fine for tests.
    """
    # If we're already on an event loop thread, we cannot block on .result() of a
    # coro submitted to the same loop (deadlock). Sync tool nodes never run on the
    # loop thread, so this only guards misuse / the fallback path.
    try:
        asyncio.get_running_loop()
        on_event_loop = True
    except RuntimeError:
        on_event_loop = False

    if not on_event_loop and _main_loop is not None and _main_loop.is_running():
        return asyncio.run_coroutine_threadsafe(coro, _main_loop).result()

    # Fallback: fresh-loop in a dedicated thread.
    box: dict[str, Any] = {}

    def _runner() -> None:
        try:
            box["result"] = asyncio.run(coro)
        except BaseException as exc:  # noqa: BLE001 — re-raised in the caller thread
            box["error"] = exc

    thread = threading.Thread(target=_runner, name="ep3-tool-bridge", daemon=True)
    thread.start()
    thread.join()
    if "error" in box:
        raise box["error"]
    return box["result"]


def _build_args(tool: Any, state: dict[str, Any]) -> dict[str, Any]:
    """Merge LLM-provided args with authoritative/fallback values from state."""
    pending = state.get("_pending_tool") or {}
    args: dict[str, Any] = dict(pending.get("args") or {})
    schema: dict[str, Any] = getattr(tool, "args", None) or {}

    for key in _AUTHORITATIVE_STATE_KEYS:
        if key in schema and state.get(key) is not None:
            args[key] = state[key]
    for key in _FALLBACK_STATE_KEYS:
        if key in schema and not args.get(key) and state.get(key) is not None:
            args[key] = state[key]
    return args


def structured_tool_adapter(tool: Any) -> Callable[..., Any]:
    """Wrap an async LangChain ``StructuredTool`` as a sync ``(state, db) -> dict``.

    Matches the engine ``node_tool_executor`` ABI. Returns the tool's result
    (dict/str) or a structured ``{"status": "error", ...}`` dict — never raises.
    """
    name = getattr(tool, "name", repr(tool))

    def _handler(state: dict[str, Any], db: Any = None) -> Any:  # noqa: ANN401
        try:
            args = _build_args(tool, state)
            result = run_async(tool.ainvoke(args))
            if isinstance(result, (dict, str)):
                return result
            return {"status": "ok", "result": str(result)}
        except Exception as exc:  # noqa: BLE001 — agent resilience (engine also catches)
            logger.warning("vitalia.ep3.adapter_error", tool=name, error=str(exc))
            return {"status": "error", "tool": name, "message": str(exc)}

    _handler.__name__ = f"ep3_adapter__{name.replace('.', '_')}"
    _handler.__qualname__ = _handler.__name__
    # Introspection markers for the ESC-17 arch test + debugging.
    _handler._ep3_wrapped_tool = name  # type: ignore[attr-defined]
    _handler._ep3_sync_adapter = True  # type: ignore[attr-defined]
    return _handler
