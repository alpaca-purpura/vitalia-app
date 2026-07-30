# T-AG-GAP1 — wire the 6 (→5) EP-3 DI service resolvers · RESULT

> Brand: vitalia · Module: sales_agent (brand extension) · Builder: builder-agentic (flagship) · 2026-06-23
> Verdict: **tests-passing** (build complete; awaiting orchestrator → gate-runner → auditor-agentic)

## What was wrong (GAP-1, RECONCILE-2026-06-22 §1)

The 5 async `StructuredTool`s (`screening_questions`, `send_payment_link`, `reschedule_appointment`, `send_proactive_reengagement`, `retract_last_message`) dispatch live via `structured_tool_adapter`, but their `set_*_service_resolver(...)` DI hooks were **never called at startup** → `_get_service()` raised `RuntimeError` → the tool returned a resolver-not-configured error and never executed real logic. Only the 3 native-sync tools (share/match/book) worked.

## Scope clarification on "6th"
`book_appointment` is native-sync and builds `CreateAppointmentService` inside its own `get_async_session_committing()` UoW — it has **no** `set_*_service_resolver` hook, so it is NOT a resolver-wiring target. The 6th resolver does not exist; scope = the **5** async StructuredTools. (book stays ESC-19/GAP-4 blocked, out of this ticket.)

## Diff summary

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/sales_agent/composition.py` | **NEW** — `wire_sales_agent_tool_resolvers()` + 5 `() -> Service` resolvers + committing-session UoW wrapper + nano LLM adapter. Mirrors prod DI of inbox (`router.py:256`) + fidelizacion (`re_engagement_endpoints.py:337`); builds the 3 tools that had only test-DI (screening/payment/reschedule). |
| `vitalia/backend/src/modules/vitalia/extensions.py` | **M** — import `wire_sales_agent_tool_resolvers` + call it once in `register_all` (the EP-3 composition root, run from `main.py` lifespan after `set_main_loop`). |
| `vitalia/backend/tests/modules/vitalia/sales_agent/test_ep3_resolvers_execution.py` | **NEW** — execution test: dispatch each tool as `node_tool_executor` (`handler(state, db)` w/ realistic `_pending_tool.args`), assert NOT resolver-unwired. |
| `vitalia/backend/tests/architecture/test_ep3_resolvers_wired.py` | **NEW** — arch/regression guard: `register_all` wires every `set_*_service_resolver`. |

## Design (the crux)
Resolver is sync `() -> Service` but invoked **on the main loop** (during `tool.ainvoke` via `tool_bridge.run_async` → `run_coroutine_threadsafe(coro, _main_loop)`), so it safely opens a main-loop-bound `AsyncSession`. The brand repos only `flush()` (no commit) and the tools have no UoW, so each resolver wraps the service's primary write coroutine in a commit/rollback/close UoW (mirrors `get_async_session_committing`). Tenant/clinic dual-filter stays authoritative from `state` (adapter overrides) — resolvers only build deps.

## RED → GREEN
- Execution test: **RED** `5 failed / 1 passed` (all 5 returned the resolver-unwired signal) → **GREEN** `6 passed` after wiring.
- Arch test: `3 passed` (regression structurally guarded).
- G5 suites: `ruff check .` clean · `pytest tests/modules/vitalia/sales_agent/ tests/architecture/` → **454 passed** · inbox regression → **103 passed, 7 skipped** (zero regressions).
- Pre-existing unrelated failure (proven by stashing my changes): `fidelizacion .../test_re_engagement_event_repository.py` `UndefinedColumnError: column "trigger_at"` = dev-DB migration drift, outside ticket scope.

## Live-verify (Critical Rule #37 — real dispatch vs dev Postgres)
Inside `luana-dev-vitalia_backend_dev-1`, `set_main_loop` + `register_all` + dispatch through the REAL merged `ToolRegistry`:
- `vitalia.sales_agent.tool_resolvers_wired` log fired.
- `screening_questions` → `reached_service=True` (real dental question list).
- `retract_last_message` → `reached_service=True` + `...retract_last_message.not_retractable` log = resolver opened a REAL dev-DB AsyncSession and executed a REAL query (no active receipt → structured result, NOT resolver-not-configured).
- **Pending Chris G:** full Telegram round-trip live (dev bot + tunnel) — separate gate.

## Skills consulted
- **sales-agent-expert**: §0 anti-dup + §3 NO-toca — no §3 surface; wiring is pure brand DI; services already exist (WIRE not NEW); no `luana_core_observability` mirror.
- **copilot-expert**: ENGINE↔BRAND boundary + "grep before declaring missing" — confirmed all 5 setters exist + never called (genuine RED); EP-3 is the unified registry.
- **LangGraph canonical docs** (accessed 2026-06-23): SOTA = ToolNode + ToolRuntime; engine uses custom sync `node_tool_executor` ABI → followed the established+empirically-validated codebase bridge pattern. No engine ABI change.
- **graceful-degradation**: resolvers never raise into the bridge; committing-UoW rollback on error → tool's own `try/except` returns Spanish fallback.
- **pytest async patterns**: execution test mirrors `node_tool_executor` exactly; uses real `register_all` into fresh `ToolRegistry`.

Full detail: `T-AG-GAP1-impl-log.md`.

## Commit
SHA: see footer (committed by exact pathspec — extensions.py + composition.py + 2 test files + impl-log + this result).
