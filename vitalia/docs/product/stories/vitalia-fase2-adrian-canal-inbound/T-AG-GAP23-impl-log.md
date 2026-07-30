# T-AG-GAP23 — inbound mode-resolver + activity-emit seams (impl log)

Origin contract: `docs/promotion-protocol/proposals/2026-06-23-sales-agent-inbound-mode-activity-seams.md` (accepted, Chris, /pm-luana).
Brand: vitalia. Engine edit AUTHORIZED (in-hub wip/vitalia, SCOPE_GATE_SKIP=1).
Step 0 date (UTC): 2026-06-23.

## Skills Consulted

- **sales-agent-expert** (loaded in context): §0 anti-duplication cardinal — observability/event/channel patterns are shared abstractions; outbox `adapter_bus` lives in `luana_core_events`; do NOT mirror. §3 NO-TOUCH list checked: `OutputManager.process_response`, `SmartBufferService`, `follow_up_engine`, `agent_state_checkpoints` schema — NONE touched (the seam lives BEFORE/AROUND `deliver_response`'s `OutputManager.process_response`, gating the call, not editing it). Decision: SEAM 1 intercepts in `deliver_response` (skip `OutputManager.process_response` for CONSULTA, hand draft to brand sink); SEAM 2 emits a platform `DomainEvent` via `adapter_bus` (the existing outbox bus used in `audit_emitter.py`), brand subscribes via in-memory `EventBus.subscribe`. Both default-off (None resolver / no subscriber = byte-identical current behavior).
- **copilot-expert** (loaded in context): N/A surface (no copilot edit), but its anti-duplication cardinal + "verify exists before declaring missing" rule applied to confirm the outbox `adapter_bus` + `EventBus.subscribe` mechanism already exists (grep-confirmed in `event_bus_adapter.py`).
- **LangGraph canonical docs**: NOT fetched — no graph node/state/edge modified. The seam wraps `deliver_response` (post-`agent_app.ainvoke`), leaving the StateGraph + prompt-cache slots untouched (cache-safety requirement of the contract). WebFetch skipped with rationale: zero graph topology change.
- **graceful-degradation (timeout+fallback+circuit breaker)**: applied to brand draft sink + brand subscriber (both best-effort try/except + structlog warning; never break the turn). No NEW external LLM/HTTP call introduced by the seam itself.

## Cross-module / NO-NEW-LAYER audit

- Outbox EventBus: REUSE `luana_core_events.outbox.adapter_bus` (already imported as `EventBus` in `audit_emitter.py`). No new bus.
- Domain event base: REUSE `luana_core_platform.domain.events.DomainEvent` (dataclass; `event_name`/`tenant_id`/`payload`). `AgentTurnCompletedEvent` added there next to `LeadCapturedEvent` (cross-module shared event home). IDs+stage only, ZERO PHI.
- Activity write: REUSE vitalia `ActivityEventRepository` (CompoundScopeRepositoryBase dual-filter tenant+clinic) via the `ActivityRepoPort` Protocol from `operator_instruction_service.py`.
- Mode resolver: REUSE vitalia `HonorModeBridge` (already a pure resolver returning DECIDE/CONSULTA/PAUSA).
- Brand registration: REUSE `extensions.py::register_all` (composition root) + `sales_agent/composition.py` (GAP-1 module) for resolver/sink/subscriber wiring at lifespan.

## Plan (technical design)

### SEAM 1 — engine `inbound_mode_seam.py` (NEW engine module, additive)
- Module-level registry: `InboundMode` enum (DECIDE/CONSULTA/PAUSA), `set_mode_resolver(fn)`, `set_draft_sink(fn)`, `resolve_inbound_mode(*, tenant_id, lead_id, checkpoint) -> InboundMode` (default DECIDE when no resolver), `get_draft_sink()`, `reset_inbound_seam()` (test isolation).
- `conversation_pipeline.deliver_response`: NEW optional kwarg `lead_id`. After sanitize+log, resolve mode. If CONSULTA → log + WS-to-inbox (reuse `AuditEmitter.emit_assistant_message`) + call brand draft sink + RETURN (NO `OutputManager.process_response`). Else (DECIDE/None) → current behavior EXACT.
- PAUSA stays pre-graph in `handle_human_mode` (already only intercepts `handler_mode=='human'`; the brand resolver's PAUSA path maps to that — engine default unchanged). The seam's CONSULTA branch runs POST-`ainvoke` (graph already ran).
- `chat.py::process_chat_flow`: pass `lead_id=user.id` into `deliver_response`. (additive kwarg, default None).

### SEAM 2 — `AgentTurnCompletedEvent` (platform events) + emit in `audit_emitter.py`
- `AgentTurnCompletedEvent(DomainEvent)` in `luana_core_platform/domain/events.py`. `create(*, tenant_id, lead_id, conversation_id, role, funnel_stage)` → payload IDs+stage ONLY.
- `AuditEmitter.emit_turn_completed(tenant_uuid, user, result, *, conversation_id, db)` publishes via `adapter_bus.publish(event, session=db)`. Called from `deliver_response` once per inbound turn (DECIDE path) — also fired on CONSULTA (the turn completed, send suppressed; activity still nourishes inbox).
- Brand: `sales_agent/inbound_activity_subscriber.py` subscribes `EventBus.subscribe("agent_turn_completed", handler)`; handler opens AsyncSession, resolves clinic_id from the Conversation, writes `vitalia_activity_events` (generic description_es + sanitized payload, dual filter). Best-effort.

### Brand wiring (`composition.py` + `extensions.py::register_all`)
- `wire_inbound_mode_seam()`: `set_mode_resolver(_vitalia_resolve_mode)` + `set_draft_sink(_vitalia_draft_sink)` + `EventBus.subscribe("agent_turn_completed", _on_agent_turn_completed)`.
- `register_all` calls it once (alongside `wire_sales_agent_tool_resolvers`).

### TDD order
1. RED engine unit `tests/orchestrator/test_inbound_mode_seam.py` + extend `test_conversation_pipeline.py`.
2. RED engine unit for `AgentTurnCompletedEvent` payload (IDs+stage, NO PHI).
3. GREEN engine seam.
4. RED brand integration (`test_inbound_activity_subscriber.py` + resolver/sink wiring).
5. GREEN brand wiring.
6. Downstream ×4 + live-verify.

## Progress

### Engine (GREEN)
- `luana_core_platform/domain/events.py`: `AgentTurnCompletedEvent(DomainEvent)` added (IDs+stage only).
- `luana_core_sales_agent/application/orchestrator/inbound_mode_seam.py`: NEW seam module (InboundMode enum + set/get/resolve/reset). Default DECIDE. Raising resolver degrades to DECIDE.
- `audit_emitter.py`: `emit_turn_completed(...)` publishes `AgentTurnCompletedEvent` via outbox `adapter_bus`, best-effort.
- `conversation_pipeline.deliver_response`: NEW `lead_id`/`conversation_id`/`db`/`checkpoint` kwargs; CONSULTA → 0 outbound + draft sink + WS; DECIDE → unchanged; emit_turn_completed on both.
- `chat.py::process_chat_flow`: passes the new kwargs (default-off otherwise).
- RED→GREEN: `tests/orchestrator/test_inbound_mode_seam.py` (8) + `test_agent_turn_completed_event.py` (5) → 13 passed.
- Regression: engine orchestrator suite 98 passed (snapshot baseline regenerated — ONLY diff = added `agent_turn_completed` event, byte-identical otherwise; baseline is UNTRACKED at `core/snapshots/` due to helper `parents[3]` math, regenerates per-run, NOT committed).
- Full engine suite: 29 failed / 476 passed. Baseline (main copy, zero edits) = 30 failed / 462 passed. The 29 are PRE-EXISTING DB-connection infra failures (Postgres unreachable in sandbox: payment_webhooks, inbound_campaign_recognition, scheduling, follow_up_engine, knowledge_builder) — NONE touch the seam. My change added 0 new failures (count dropped by 1: snapshot test now passes).
- **Engine validation method:** `PYTHONPATH=<worktree core src>` override (venv symlinks to main; `.pth` resolves `core/*` to main copy — MEMORY `2026-06-16-engine-edits-brand-worktree-invisible-to-venv`). Subprocess inherits PYTHONPATH → wins over `.pth`.

### Brand (GREEN)
- `sales_agent/application/services/inbound_seam_adapter.py`: NEW `VitaliaInboundSeamAdapter` (resolve_mode via HonorModeBridge; draft_sink → `adrian_draft_pending` activity row, NO body; subscriber → `adrian_turn` activity row) + `build_agent_turn_completed_handler` (sync→async bridge for in-memory/outbox dispatch).
- `sales_agent/composition.py`: `wire_inbound_mode_seam()` — conv_loader (open conv by lead, tenant-scoped, own session) + activity_writer (ActivityEventRepository.create, committing session) + `set_mode_resolver`/`set_draft_sink` + `EventBus.subscribe("agent_turn_completed", handler)`.
- `extensions.py::register_all`: calls `wire_inbound_mode_seam()` once (next to GAP-1 tool resolvers).
- Engine refactor: resolver hook made ASYNC (awaited in `deliver_response` on the main loop → brand AsyncSession binds to the shared-pool loop, no cross-loop trap; avoids the sync-resolver-on-main-loop deadlock).
- RED→GREEN: `tests/modules/vitalia/sales_agent/test_inbound_seam_adapter.py` (10) + `test_inbound_seam_wiring.py` (anti-orphan CONN, 3) → 13 passed.
- Brand suites: sales_agent + inbox = 203 passed. Brand arch = 365 passed, 1 PRE-EXISTING failure (`test_pgcrypto_phi_columns::..._notes_...` — documented false-positive `notes` regex, MEMORY `main-integration-cap-drift`; triggered by ANOTHER session's untracked migration `test_migration_052_notes_internal.py`; my change touches NO PHI model/migration — verified fails identically on baseline).

### Downstream regression (×4)
- vitalia: engine orchestrator+arch 104 + sales_agent/inbox 203 + brand arch 365 (−1 pre-existing) GREEN.
- comunify: arch 144 passed (engine override on). nicolify: arch 20 passed. lupulo: no arch dir (placeholder). All unaffected by the additive default-off seam.
- engine observability 36 passed; platform event consumer tests 19 passed.

### Live-verify (Rule #37 — REAL dev Postgres vitalia_dev :5435)
Direct orchestrator-equivalent invocation (worktree engine via PYTHONPATH; the running
backend container still runs MAIN's engine — engine edits invisible until squash-merge,
MEMORY `engine-edits-brand-worktree-invisible-to-venv`). Real conversation
`22222222-…` (tenant e69a…, clinic f035…, lead ee61…):
- **DECIDE** (proposal_required=false): resolve_mode→decide; `AgentTurnCompletedEvent` → subscriber wrote 1 `adrian_turn` activity row. payload = `{role, lead_id, funnel_stage}` — ZERO PHI/body. DB read confirmed.
- **CONSULTA** (proposal_required=true): resolve_mode→consulta; draft_sink wrote 1 `adrian_draft_pending` row; the draft text "…martes…Dra. Pérez" did NOT land in the row (body containment); 0 outbound (engine deliver_response suppresses OutputManager on CONSULTA — verified in engine unit `test_deliver_response_consulta_suppresses_outbound_and_drafts`). DB read confirmed.
- Cleanup: 2 test activity rows deleted; `proposal_required` reset to false; DB back to baseline (0 activity rows).
- **FLAGGED for Chris's G gate:** the live Telegram channel round-trip (real bot → 0 outbound on consulta) needs the merged engine running in the backend container + the tunnel — out of reach from the worktree. The seam LOGIC + real DB writes/reads + no-PHI invariant are verified; the channel-send suppression is covered by engine unit tests.

### Skill no-skip note
copilot-expert N/A (no copilot surface). LangGraph WebFetch skipped: zero graph topology change (seam wraps post-ainvoke delivery; prompt-cache slots + StateGraph untouched).
