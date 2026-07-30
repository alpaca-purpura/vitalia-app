# T-AG-GAP1 — wire EP-3 DI service resolvers (impl log)

> Brand: vitalia · Module: sales_agent (brand extension) · Ticket: T-AG-GAP1
> Builder: builder-agentic (flagship) · Date (Step 0 captured): 2026-06-23

## Step 0 — date + workspace
- `date -u`: 2026-06-23 · `{current_year}` = 2026
- WS = `/home/chalreme/Proyectos/luana-vitalia` · branch `wip/vitalia` (in-place, HB-32/M9 — no worktree)
- Tree had pre-existing WIP from other lanes (scheduling files = `code:scheduling` bucket). My scope = `code:sales_agent`. I touch ONLY sales_agent + extensions.py + the two new test files. No cross-lane staging.

## Skills Consulted (Step 0 GATE)

- **sales-agent-expert** (loaded via command): consulted §0 anti-duplication cardinal + §3 "NO se toca" + SSoT vivos. Decision: the 5 wrapped tools delegate to brand-local services (NOT engine `core/luana-core-sales-agent`); wiring resolvers is pure brand DI in `extensions.py` — NO §3 surface touched (no Closer Studio, no OutputManager, no SmartBuffer, no PromptVersionModel). Anti-dup: services already exist (DI hook is the only gap) — EXTEND/WIRE, not NEW. No mirror of any `luana_core_observability` abstraction introduced.
- **copilot-expert** (loaded via command): consulted ENGINE vs BRAND-EXTENSION boundary table + "Regla cero: grep before declaring missing". Decision: confirmed by grep that all 5 `set_*_service_resolver` setters exist and are NEVER called in src/ or tests/ (genuine RED). EP-3 is the unified tool registry surface (copilot + sales_agent share it per Story 9 SDK cement).
- **LangGraph canonical docs** (WebFetched `docs.langchain.com/oss/python/langgraph/workflows-agents`, accessed 2026-06-23): current SOTA = `ToolNode` + `ToolRuntime[Context, State]` for state/service injection. The engine here predates that with a custom sync `node_tool_executor` ABI (`tool_fn(state, db=state.get("_db"))` reading `state["_pending_tool"]["args"]`). Per skill guidance, the established + empirically-validated codebase pattern (sync `structured_tool_adapter` + main-loop `run_async` bridge) is authoritative over the generic doc. No engine ABI change.
- **graceful-degradation** (timeout + fallback + circuit breaker): each resolver builds a service that opens an AsyncSession + does DB/LLM work. The bridge already runs on the main loop; resolver wraps the service's primary async method in a commit/rollback/close UoW so a write failure rolls back and the tool's existing `try/except` degrades to a Spanish fallback (never crashes the turn).
- **pytest async testing patterns**: execution test invokes handlers EXACTLY as `node_tool_executor` (`handler(state, db=None)`) with realistic `state["_pending_tool"]["args"]`; uses real `register_all` into a fresh `ToolRegistry` (mirrors existing `test_ep3_handler_execution.py`). RED before wiring (resolver-not-configured), GREEN after.

## Cross-module / NO-NEW-LAYER audit

- grep confirmed the 5 setters exist (`screening_questions.py:96`, `payment_link.py:112`, `reschedule_appointment.py:89`, `send_proactive_reengagement.py:189`, `retract_last_message.py:130`).
- All 5 services already exist; production DI already wired for **proactive** (`fidelizacion/api/re_engagement_endpoints.py:337`) + **retract** (`inbox/api/router.py:256`). payment_link/reschedule/screening had construction only in tests → no production composition root → THIS is the gap.
- The ONLY new file is a brand composition module `sales_agent/composition.py` (the resolver wiring helper). No new infra layer, no new registry, no mirror of engine abstractions. `register_all` calls it (single entry, called from `main.py:80` lifespan after `set_main_loop`).

## "6th" question (book_appointment / scheduling)

`book_appointment` is **native-sync** and constructs `CreateAppointmentService` inside its own `get_async_session_committing()` UoW (`book_appointment.py:124-167`) — it has NO `set_*_service_resolver` hook. So book is NOT a resolver-wiring target. Scope = the 5 async StructuredTools. (book remains ESC-19/GAP-4 blocked, out of this ticket.)

## Design

Service constructors (verified by reading each `__init__`):
- `ScreeningQuestionsService(screening_repo, audit_log_repo, llm_service)` — repos need AsyncSession; llm_service needs `.generate(prompt)->obj.content`. Adapt `LLMFactory.get_service().get_client(ModelRole.NANO)` (LangChain client, `.ainvoke`) via a thin `_NanoLLMAdapter.generate`.
- `PaymentLinkService(channel_guard, mercadopago_adapter, whatsapp_adapter, audit_log_repo, session)` — all concrete classes exist.
- `RescheduleAppointmentService(appointment_service, audit_log_repo)` — `appointment_service.update_slot(...)` has NO production impl yet → service constructs, but `update_slot` will fail → tool's own `except` returns Spanish fallback "No pude reprogramar". That is NOT a resolver-error → satisfies the RED→GREEN bar (reaches the service). Documented sub-limitation (parallels book's domain gap).
- `ProactiveOutboundService(session, re_engagement_repo, audit_repo, compliance_service)` — fidelizacion variant (the one the tool imports). Mirror `re_engagement_endpoints.py:337`.
- `RetractMessageService(msg_repo, receipt_repo, conv_repo, audit_writer, event_bus, channel_adapters, session)` — mirror `inbox/api/router.py:256`.

Session/UoW: resolver is sync `() -> Service` but invoked on the MAIN loop (during `tool.ainvoke` via `run_async`). It opens a fresh `AsyncSession` from the brand `_AsyncSessionLocal` (main-loop bound) and wraps the service's primary write method in a commit/rollback/close UoW (the tools currently lack a UoW — repos only `flush()`). Read-only screening first-turn path needs no commit.

Tenant/clinic dual-filter: the adapter overrides `tenant_id`/`clinic_id` from `state` (authoritative). Resolvers do NOT scope — services enforce dual-filter per query. Preserved.

## TDD ledger — RED → GREEN evidence

### Execution test (`tests/modules/vitalia/sales_agent/test_ep3_resolvers_execution.py`)
- **RED** (before wiring): `5 failed, 1 passed` — all 5 `reaches_service` probes returned the resolver-unwired signal:
  - screening/payment_link/reschedule → `{"status":"error", "message": "...service resolver not configured. Call set_*_service_resolver(...)..."}`
  - send_proactive_reengagement → "Hubo un problema interno con el dispatcher de mensajes proactivos..."
  - retract_last_message → "No pude revertir el mensaje. Quedó registrado para revisión." (`resolver_missing` log)
  - (the 1 pass = `test_all_five_wrapped_tools_present` guard)
- **GREEN** (after wiring `register_all → wire_sales_agent_tool_resolvers()`): `6 passed`.

### Arch/regression test (`tests/architecture/test_ep3_resolvers_wired.py`)
- `3 passed` — asserts `register_all` wires every `set_*_service_resolver` (resets each tool's `_service_resolver` to None, runs real `register_all`, asserts each is now callable). A future resolver-backed EP-3 tool added without wiring → suite FAILS (GAP-1 regression structurally guarded).

### Suites (G5 gate)
- `ruff check .` (full brand) → All checks passed. `ruff format --check` → clean.
- `pytest tests/modules/vitalia/sales_agent/ tests/architecture/` → **454 passed**.
- inbox regression (`regression_guard`): `pytest tests/modules/vitalia/inbox/ tests/integration/test_inbox_send_retract_audit_log.py` → **103 passed, 7 skipped** (zero regressions).
- Pre-existing unrelated failure (NOT mine): `tests/modules/vitalia/fidelizacion/infrastructure/test_re_engagement_event_repository.py` → `UndefinedColumnError: column "trigger_at" of relation "vitalia_re_engagement_events" does not exist` (dev-DB migration drift). **Proven pre-existing** by stashing all my changes and re-running → same failure. Outside ticket scope (I touch nothing in fidelizacion repo/model/migration).

## Live-verify (Critical Rule #37 — real dispatch vs dev Postgres)
Ran a dispatch script INSIDE `luana-dev-vitalia_backend_dev-1` (dev DB reachable), `set_main_loop(running_loop)`, `register_all` (wires resolvers), then dispatched through the REAL merged `ToolRegistry`:
- Log: `vitalia.sales_agent.tool_resolvers_wired tools=[screening_questions, send_payment_link, reschedule_appointment, send_proactive_reengagement, retract_last_message]` — wiring fired at composition.
- `screening_questions` → `reached_service=True` — returned the real dental vertical question list (resolver fired + service built; no resolver-error).
- `retract_last_message` → `reached_service=True` + log `vitalia.sales_agent.tools.retract_last_message.not_retractable` — the resolver opened a REAL dev-DB AsyncSession and the service executed a REAL query (no active receipt for the random msg → structured "marcado como erróneo", NOT resolver-not-configured). This is the tool executing real logic instead of an error-dict.

**Pending Chris G:** full Telegram round-trip (webhook → Adrián dispatches a wrapped tool live → reads `sales_agent.tool_dispatched` + the tool's data log) is the G gate (needs the dev bot + tunnel exercise + Chris). The real-DB dispatch above proves the resolver path works end-to-end through the registry.

## Scope boundary verification
- Engine `core/` untouched (`git diff --stat HEAD -- core/` empty). No `/pm-luana` lift needed — pure brand wiring.
- No cross-brand, no frontend, no scheduling/business modules touched.
- Files: `extensions.py` (M, +import +`wire_sales_agent_tool_resolvers()` call), `sales_agent/composition.py` (NEW), 2 NEW test files.

## Known sub-limitation (documented, NOT GAP-1)
`reschedule_appointment`: no production `AppointmentService.update_slot(...)` exists (scheduling-domain gap, parallels book/ESC-19). The resolver fires + the service builds (reaches PAST the resolver = GAP-1 bar met), but a real reschedule write fails inside `update_slot` (`_RescheduleAppointmentNotWiredStub` raises NotImplementedError) → the tool degrades to its Spanish "No pude reprogramar" fallback. Wiring the real scheduling AppointmentService is a scheduling-domain follow-up.
