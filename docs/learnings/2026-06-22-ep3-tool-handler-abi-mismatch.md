# EP-3 tool handler ABI mismatch — registered ≠ executable (arch-green ≠ runtime)

**Date:** 2026-06-22 · **Scope:** cross-brand (engine `core/luana-core-sales-agent` + every brand that registers EP-3 sales_agent tools) · **Severity:** 🔴 silent-killer · **Origin:** /pm-vitalia self-paced lift loop, Tier 2.4 pre-flight (verifying before building book/match/share).

## What happened

The sales_agent graph dispatches a tool like this (`application/agents/sales/nodes.py::node_tool_executor`):

```python
tool_fn = get_tool_registry().merged_tools().get(tool_name)
result = tool_fn(state, db=state.get("_db"))          # SYNC, positional state, kwarg db; reads args FROM state
```

Every **engine** tool matches that ABI: `def tool_check_schedule(state: dict, db=None) -> dict`. The LLM's
`[TOOL_REQUEST: {"args": {...}}]` args are **ignored** by dispatch (used only for the dedup tracker) — engine
tools read what they need from `state`.

Every **brand** (vitalia) tool registered via EP-3 is the WRONG shape:

```python
@tool("screening_questions", args_schema=ScreeningQuestionsInput)   # LangChain StructuredTool
async def screening_questions(...): ...                              # async, Pydantic args (lead_id, vertical, …)
```

Empirically: `screening_questions(state, db=None)` → `TypeError: 'StructuredTool' object is not callable`.
So when the LLM dispatches any of vitalia's 9 "real" EP-3 tools, dispatch raises → the `except` returns
`{"status":"error"}` to the LLM. **The tool never executes.** Ironically the 4 `_not_implemented_yet`
placeholders (plain `def _placeholder(*a, **k)`) ARE callable and degrade gracefully — the placeholders work,
the real tools don't.

## Why it stayed invisible

- The seam was **dead end-to-end** until the lifespan wiring (846388a6) — the tools "reached the running graph
  through nothing", so the ABI was never exercised.
- T-AG-1 eval goldens tested the tools **in isolation** (invoking the StructuredTool with its proper Pydantic
  args), NEVER through `node_tool_executor`'s `tool_fn(state, db)` path. Green goldens, broken integration.
- 846388a6 verified "13 tools register into the singleton; real tools dispatchable" — but "dispatchable" was
  checked as *present in `merged_tools()`*, not as *callable under the engine ABI*. **Registered ≠ executable.**

This is the **embudo pattern again** (`2026-06-04-embudo-imagined-contract-never-integrated.md`): two sides
green in isolation, the contract between them never exercised live. And the **arch-green ≠ runtime** lesson
(`verification-real-not-200`): "dispatchable" verified structurally, not by ejercising a real dispatch.

## ✅ Resolution (Tier 2.4a · `b13c6455`)

Fixed brand-side (hexagonal — the engine ABI is the port). `sales_agent/tool_bridge.py::structured_tool_adapter`
wraps each async StructuredTool as a sync `(state, db) -> dict` handler; `run_async` bridges to the async tool in
a **dedicated thread with a fresh event loop** (a DB session opened inside connects within that loop → no
cross-loop asyncpg trap). The pilot `share_doctor_profile` is written native-sync (public read, no bridge).
Arch test (every EP-3 handler is a plain sync callable) + execution test (dispatch as `fn(state, db)` w/o
TypeError). **Live-verified** via the real merged registry + real dev DB → real doctor URL.

Two design assumptions were overridden by *verifying before building* (the lesson recursing on itself):
1. The design said the bridge could reuse the `db: Session` the engine passes — but `state["_db"]` is **never
   seeded** at inbound (it's `None`). The adapter makes its own session.
2. The 9 StructuredTools' DI service resolvers (`set_*_service_resolver`) were **never wired at lifespan** → the
   tools never worked end-to-end through *any* path (ESC-17 *and* unwired DI). The adapters now degrade
   gracefully (error dict) instead of crashing; wiring the resolvers is 2.4b/follow-up.

## The fix (sub-phased — original plan, kept for history)

The engine dispatch ABI is the **port**; brands must register **adapters** shaped to it (hexagonal). The brand
must register a sync `(state, db) -> dict` callable that (1) extracts the tool's args from `state`
(tenant_id/clinic_id/lead_id/vertical/… — the engine convention is state-driven, not LLM-arg-driven), (2)
bridges to the async service, (3) returns a plain dict. Footgun: the async→sync bridge inside a node that may
run within an existing event loop → `asyncio.run` would raise "event loop already running"; needs a sync
session or a thread-offload bridge (the 03-arch-agentic §2.1 sync/async note already anticipated this for the
scheduler provider). This is HIPAA-sensitive (booking/PHI dual filter) → builder-agentic flagship + a focused
mini-design, NOT a rushed hand-roll.

Proposed as **ESC-17** / sub-phase **2.4a** (EP-3 handler ABI) before **2.4b** (book/match/share + provider).

## Durable rule (promotable)

- A seam is **alive** only when a real call crosses it live, not when both sides register/import. "Registered",
  "advertised", "dispatchable-by-name" are necessary, not sufficient — add an **execution** check that invokes
  the handler exactly as the runtime does (`tool_fn(state, db)`), and assert a non-error result.
- Cross-package handler registration MUST pin the **call ABI** (signature + sync/async + arg source), not just
  the registry key. A registry that accepts `Any` handler (as `ToolRegistry.register_tool_from_extension`
  does) hides ABI drift — consider validating the handler is a plain sync callable at registration, or an
  arch test that every EP-3 handler is `callable(h)` and not a `StructuredTool`/coroutine.

## Refs

- `core/luana-core-sales-agent/src/luana_core_sales_agent/application/agents/sales/nodes.py::node_tool_executor`
- `vitalia/backend/src/modules/vitalia/extensions.py` (EP-3 registrations — all 9 real handlers are StructuredTools)
- `docs/architecture/luana-platform/sales-agent-multibrand-hexagonal-lift.md` § ESC-17
- Extends [[verification-real-not-200]] · [[embudo-imagined-contract-never-integrated]]
