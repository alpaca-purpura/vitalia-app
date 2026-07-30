# cap: sales_agent.honor-mode-bridge
"""ESC-17 / Tier 2.4b — ``run_async`` submits to the registered app main loop.

Regression for the cross-loop asyncpg trap (verified empirically 2026-06-22): a
coroutine using an AsyncSession from the shared engine pool must run on the loop
that created those pooled connections (the app main loop). The fix is
``set_main_loop`` (wired at FastAPI lifespan) + ``run_coroutine_threadsafe`` in
``run_async``. This test proves the mechanism WITHOUT a DB: a coro reports the
loop it ran on, and across two calls it is the registered loop (not a fresh
per-call loop) — which is exactly what makes the shared pool safe.
"""

from __future__ import annotations

import asyncio
import threading

from src.modules.vitalia.sales_agent import tool_bridge


def test_run_async_submits_to_registered_main_loop() -> None:
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=loop.run_forever, name="test-main-loop", daemon=True)
    t.start()
    prev = tool_bridge._main_loop  # noqa: SLF001 — test isolation
    tool_bridge.set_main_loop(loop)
    try:

        async def _which_loop() -> int:
            return id(asyncio.get_running_loop())

        # Called from this (non-loop) thread → must submit to the registered loop.
        got1 = tool_bridge.run_async(_which_loop())
        got2 = tool_bridge.run_async(_which_loop())
        assert got1 == id(loop), "run_async did not submit to the registered main loop"
        assert got2 == id(loop), "2nd call ran on a different loop (cross-loop trap not fixed)"
    finally:
        tool_bridge._main_loop = prev  # noqa: SLF001
        loop.call_soon_threadsafe(loop.stop)


def test_run_async_fallback_without_main_loop() -> None:
    """No registered main loop (tests/no-app) → fresh-loop fallback still runs the coro."""
    prev = tool_bridge._main_loop  # noqa: SLF001
    tool_bridge._main_loop = None  # noqa: SLF001
    try:

        async def _answer() -> int:
            return 42

        assert tool_bridge.run_async(_answer()) == 42
    finally:
        tool_bridge._main_loop = prev  # noqa: SLF001
