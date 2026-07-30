# T-AG-GAP23 — inbound mode-resolver + activity-emit seams — RESULT

**Contract:** `docs/promotion-protocol/proposals/2026-06-23-sales-agent-inbound-mode-activity-seams.md` (accepted, Chris, /pm-luana).
**Brand:** vitalia. **Build:** in-hub `wip/vitalia`, engine edit authorized. **Step 0 date:** 2026-06-23.
**State:** tests-passing (awaiting orchestrator → gate-runner → auditor-agentic).

Two ADDITIVE, backward-compatible seams. Default (no brand opt-in) = byte-identical to current behavior. vitalia opts in; comunify/nicolify/lupulo ignore.

---

## Engine diff (core — `/pm-luana` lift authorized)

| File | Change |
|---|---|
| `luana-core-platform/.../domain/events.py` | +`AgentTurnCompletedEvent(DomainEvent)` (IDs + funnel_stage only, ZERO PHI/bodies). |
| `luana-core-sales-agent/.../orchestrator/inbound_mode_seam.py` (NEW) | `InboundMode` enum (DECIDE/CONSULTA/PAUSA) + module-level injectable hooks `set_mode_resolver`/`set_draft_sink`/`get_draft_sink`/`reset_inbound_seam` + `async resolve_inbound_mode(...)`. Default no-resolver → DECIDE. Raising resolver degrades to DECIDE. Hexagonal: engine imports NOTHING brand. |
| `.../orchestrator/conversation_pipeline.py` | `deliver_response` +kwargs `lead_id/conversation_id/db/checkpoint`; resolves mode AFTER `ainvoke` (cache-safe); CONSULTA → 0 outbound + draft sink + WS; DECIDE → unchanged `OutputManager.process_response`; `emit_turn_completed` on both. |
| `.../orchestrator/audit_emitter.py` | +`emit_turn_completed(...)` publishes `AgentTurnCompletedEvent` via the EXISTING outbox `adapter_bus` (best-effort try/except). |
| `.../orchestrator/chat.py` | `process_chat_flow` passes the new kwargs (default-off otherwise). |

Resolver hook is **async** (awaited in `deliver_response` on the main loop → brand AsyncSession binds to the shared-pool loop; avoids the sync-resolver deadlock + cross-loop asyncpg trap).

## Brand diff (vitalia extension)

| File | Change |
|---|---|
| `sales_agent/application/services/inbound_seam_adapter.py` (NEW) | `VitaliaInboundSeamAdapter`: resolve_mode (REUSES `HonorModeBridge`), draft_sink (`adrian_draft_pending` activity row — NO body), subscriber (`adrian_turn` activity row from event IDs+stage). `build_agent_turn_completed_handler` bridges the sync bus dispatch → async write. clinic_id ALWAYS re-resolved from the conversation (authoritative dual filter). `sanitize_payload` on every write. |
| `sales_agent/composition.py` | +`wire_inbound_mode_seam()`: conv_loader (open conv by lead, own session) + activity_writer (`ActivityEventRepository.create`, committing session) + registers resolver/sink + `EventBus.subscribe("agent_turn_completed", handler)`. |
| `extensions.py::register_all` | calls `wire_inbound_mode_seam()` once (next to GAP-1 tool resolvers). |

Anti-duplication: REUSES `HonorModeBridge` + `ActivityEventRepository` + `sanitize_payload` (shared engine) + outbox `adapter_bus`. NO new abstraction.

## RED → GREEN evidence

- Engine RED: `test_inbound_mode_seam.py` + `test_agent_turn_completed_event.py` → ImportError (modules absent) → after impl 13 passed.
- Engine regression: `tests/orchestrator/` 98→**104 passed** (incl. arch). Snapshot `telegram_new_lead_baseline.json` regenerated — ONLY diff = the added `agent_turn_completed` domain event (IDs+`funnel_stage:rapport`, `conversation_id:null`, NO PHI); everything else byte-identical. (Baseline is UNTRACKED — helper `parents[3]` math lands it at `core/snapshots/`; regenerates per-run; NOT committed.)
- Brand RED: `test_inbound_seam_adapter.py` (10) + `test_inbound_seam_wiring.py` (anti-orphan CONN, 3) → ModuleNotFound → after impl 13 passed.
- Brand suites: sales_agent + inbox = **203 passed**.

## Downstream ×4 status

| Brand | Result (worktree engine override on) |
|---|---|
| vitalia | engine orchestrator+arch 104 ✓ · sales_agent+inbox 203 ✓ · brand arch 365 ✓ (−1 PRE-EXISTING `pgcrypto _notes_` false-positive, NOT my scope — see below) |
| comunify | arch 144 passed ✓ |
| nicolify | arch 20 passed ✓ |
| lupulo | no arch dir (placeholder) — n/a |
| engine | observability 36 ✓ · platform event tests 19 ✓ |

The 1 vitalia arch failure (`test_pgcrypto_phi_columns::test_no_phi_column_uses_text_or_varchar_unencrypted`) is a documented false-positive (`notes` regex, MEMORY `main-integration-cap-drift`) triggered by ANOTHER session's untracked migration (`test_migration_052_notes_internal.py`). My change touches ZERO PHI model/migration — it fails identically on the pristine baseline (main engine, no my edits).

Full engine suite: 29 failed / 476 passed. Baseline (main copy, zero edits) = 30 failed / 462 passed. The 29 are PRE-EXISTING DB-connection infra failures (Postgres unreachable in sandbox: payment_webhooks, inbound_campaign_recognition, scheduling, follow_up_engine, knowledge_builder) — NONE touch the seam. My change added 0 new failures.

## Live-verify (Rule #37 — REAL dev Postgres `vitalia_dev` :5435)

Direct orchestrator-equivalent invocation against the running dev DB (worktree engine via PYTHONPATH — the running backend container still runs MAIN's engine; engine edits are invisible until squash-merge). Real conversation `22222222-…` (tenant e69a…, clinic f035…, lead ee61…):

- **DECIDE** (`proposal_required=false`): `resolve_mode → decide`; `AgentTurnCompletedEvent` → subscriber wrote 1 `adrian_turn` activity row. payload `{role, lead_id, funnel_stage}` — ZERO PHI/body (DB read confirmed).
- **CONSULTA** (`proposal_required=true`): `resolve_mode → consulta`; `draft_sink` wrote 1 `adrian_draft_pending` row; the draft text ("…martes…Dra. Pérez") did NOT land in the payload (body containment); 0 outbound (engine `deliver_response` suppresses `OutputManager` on CONSULTA — engine unit `test_deliver_response_consulta_suppresses_outbound_and_drafts`). DB read confirmed.
- Cleanup: 2 test rows deleted; `proposal_required` reset; DB back to baseline (0 activity rows).
- **FLAGGED for Chris G gate:** the live Telegram channel round-trip (real bot → 0 outbound on consulta) needs the merged engine in the running backend + the tunnel — out of reach from the worktree. Seam logic + real DB writes/reads + no-PHI invariant verified here; channel-send suppression covered by engine unit tests.

## Skills consulted

- **sales-agent-expert** — §0 anti-duplication (reuse outbox `adapter_bus`/`HonorModeBridge`/`ActivityEventRepository`/`sanitize_payload`, no mirror); §3 NO-TOUCH verified untouched (`OutputManager.process_response`, `SmartBufferService`, `follow_up_engine`, `agent_state_checkpoints` schema). Seam gates AROUND `deliver_response`, not inside §3 surfaces.
- **copilot-expert** — N/A surface; its "verify exists before declaring missing" rule applied to confirm the outbox bus + `EventBus.subscribe` already exist (grep-confirmed).
- **LangGraph canonical docs** — WebFetch skipped: zero graph topology change (seam wraps post-`ainvoke` delivery; prompt-cache slots + StateGraph untouched — cache-safety bar of the contract).
- **graceful-degradation** — resolver→DECIDE on error; draft sink + subscriber best-effort try/except; emit_turn_completed swallows publish failures. No NEW external LLM/HTTP call.

## Commit

`5bd0dd1b` — `feat(sales-agent): inbound mode-resolver + activity-emit seams (canal-inbound GAP-2/3)` (SCOPE_GATE_SKIP, committed by explicit pathspec; pushed `faa643f7..5bd0dd1b` to `wip/vitalia`). Contains exactly the 14 T-AG-GAP23 files.

> ⚠️ Shared-index note for /pm: a FIRST commit attempt `9feb302c` (same subject) raced the shared single-hub index and captured a PARALLEL session's WIP (`052_vitalia_appointments_notes_internal.py` + `test_migration_052_notes_internal.py` + `T-BE-4-notesfix-result.md` + a `chris-input.md` line — the mateo-nueva-cita story), NOT this ticket's files. That commit's CONTENT is legitimate parallel work; only its MESSAGE is mislabeled. This ticket's real content is in `5bd0dd1b` (committed by explicit pathspec to dodge the race). No revert performed (M5 — never touch another session's committed work).
