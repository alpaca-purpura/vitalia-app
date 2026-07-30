# T-AG-1 Result — Override-context wire (RN-4.1)

**Ticket:** T-AG-1 (vitalia-fase2-adrian-embudo)
**Surface:** agentic brand-extension (`vitalia/backend/src/modules/vitalia/sales_agent/`)
**Model:** Opus 4.8 (R23 HARD — AGENTIC production_code)
**Status:** tests-passing
**Date:** 2026-06-04

---

## ⚠ Environment note for the orchestrator (READ FIRST)

This builder ran in an **isolated worktree** (sandbox `agent-abd3ce8e34b47a09c`, HEAD `a2c38840` = main),
which does NOT contain T-BE-1/T-BE-2 (they live only on the hub `wip/vitalia`). The harness write-guard
blocks writing to the hub's `~/Proyectos/luana-vitalia/` paths. To build + run RED→GREEN against the
`lead_stage_overridden` substrate, I materialized the crm dependency tree into the sandbox via
`git checkout wip/vitalia -- vitalia/backend/src/modules/vitalia/crm/` (CONSUMED, not delivered).

**The 3 deliverable files were written in-sandbox and must be applied to the hub by the orchestrator.**
The materialized `crm/*` files are already on the hub — DO NOT re-commit them.

### Apply to hub (orchestrator, by pathspec — only these 3)

```
vitalia/backend/src/modules/vitalia/sales_agent/application/services/override_context_wire.py   (NEW)
vitalia/backend/tests/modules/vitalia/sales_agent/test_manual_override_feeds_agent_context.py    (NEW)
vitalia/docs/product/stories/vitalia-fase2-adrian-embudo/T-AG-1-result.md + T-AG-1-impl-log.md   (docs)
```

Sandbox content is byte-identical to what the hub should receive (sandbox crm substrate ==
`wip/vitalia` HEAD, so the new files build against the exact substrate present on the hub).

---

## Files Created / Modified (paths relative to repo root)

### NEW — deliverables (apply to hub)
- `vitalia/backend/src/modules/vitalia/sales_agent/application/services/override_context_wire.py`
  (`LeadStageOverriddenEvent` Pydantic v2 DTO · `CheckpointMetadataPort` Protocol · `HandoverActivityPort`
  Protocol · `OverrideContextWire` service · `OVERRIDE_CONTEXT_KEY` constant)
- `vitalia/backend/tests/modules/vitalia/sales_agent/test_manual_override_feeds_agent_context.py`
  (10 tests — SC-1b / AE-1 / RN-4.1 / tenant-isolation / graceful-degradation / anti-dup-DDD)
- `vitalia/docs/product/stories/vitalia-fase2-adrian-embudo/T-AG-1-result.md` + `T-AG-1-impl-log.md`

### MODIFIED — none
No engine edit. No `agent_state_checkpoints` schema change. No crm edit. No FE. No prompt/graph/tool.

### Materialized substrate (NOT a deliverable — already on hub)
`vitalia/backend/src/modules/vitalia/crm/**` checked out from `wip/vitalia` solely so the wire could
build + run. Orchestrator: ignore these (they are the T-BE-1/T-BE-2 dependency, unchanged).

---

## Validator Gates Output (literal)

```
# Wire test (10 tests):
cd vitalia/backend && pytest tests/modules/vitalia/sales_agent/test_manual_override_feeds_agent_context.py -q
→ .......... [100%]   (10 passed)

# Validator gate (ticket spec — wire test + arch tests, AE-1/RN-4.1 GREEN):
cd vitalia/backend && pytest tests/modules/vitalia/sales_agent/test_manual_override_feeds_agent_context.py tests/architecture/ -q
→ 345 passed, 2 warnings in 3.52s
   (10 wire + 335 arch; the 2 warnings = pre-existing PytestUnknownMarkWarning no_eval, unrelated)

# Full sales_agent module suite (regression — no break):
cd vitalia/backend && pytest tests/modules/vitalia/sales_agent/ -q
→ 33 passed in 0.34s

# Ruff check (both new files):
ruff check src/modules/vitalia/sales_agent/application/services/override_context_wire.py \
           tests/modules/vitalia/sales_agent/test_manual_override_feeds_agent_context.py --no-cache
→ All checks passed!

# Ruff format check:
ruff format --check <both files>
→ 2 files already formatted

# DDD boundary (crm ↛ sales_agent) + all arch fitness:
cd vitalia/backend && pytest tests/architecture/ -q
→ 335 passed, 2 warnings in 3.66s
```

mypy: not installed in the venv; brand baseline gate = ruff + pytest + arch-fitness (mypy opt-in by
nature per rule #37, not in this brand's baseline). Wire is fully type-annotated regardless.

### Validator IDs covered
- **AE-1** (override manual con razón → override_context persistido + evento + subscriber escribe contexto
  next-turn): `test_override_persists_context_to_next_turn_read_surface` GREEN.
- **RN-4.1** (override feeds agent — happy SC-1b + negative "override sin reason → skip"):
  `test_override_persists_...` + `test_payload_missing_reason_is_skipped` + `test_payload_blank_reason_is_skipped` GREEN.
- **SC-1b** (persist + read; NO re-inicia agente + handover en Historial):
  `test_override_context_does_not_reinitialize_agent` + `test_override_records_handover_activity_human_to_agent` GREEN.

---

## Skills consulted (must_load enforcement v4.1)

| Skill / doc | Why invoked | Decision taken (cites section/rule) |
|---|---|---|
| `sales-agent-expert` | mandatory (06-tickets T-AG-1 `must_load_skills`) | **§0 anti-dup cardinal** → grep cross-codebase for override-context/checkpoint-metadata writer = 0 hits ⇒ NET-NEW brand-local. **§3 NO-TOUCH** confirms `agent_state_checkpoints` schema is protected → write into the EXISTING nullable `metadata_info` JSONB (key `override_context`), zero DDL. **Anti-pattern "importar crm/ desde sales_agent/"** → receive via `lead_stage_overridden` event payload + inject deps via brand-local Protocol ports (no crm import). **NO new graph/tool/prompt/specialist** (03-arch § 8.1/8.2/8.4/8.6). Override-context = volatile per-turn signal (§ 8.5), never a cacheable prefix. No goldens (§ 8.9 N/A — no prompt/specialist generation). |
| `.claude/rules/anti-duplication.md` | mandatory | Inventory has NO override-context abstraction (vertical-specific). The engine next-turn read is the SYNC `StateRepository.get_active_checkpoint` over `metadata_info`. Wire does NOT mirror it — it abstracts read/update behind `CheckpointMetadataPort` (Protocol) whose concrete impl is injected. Tests use AsyncMock; the prod adapter (deferred until Inbox/sales_agent live) is the only place that touches the engine read surface. No `turn_envelope` / `callback_handler` / cost / pricing mirror. |
| `.claude/rules/tenant-isolation.md` | mandatory | Every wire path requires `tenant_id`. Event payload carries `tenant_id`; both ports take `tenant_id` keyword-only. Missing `tenant_id` → `ValueError`/`KeyError` (no silent cross-tenant write) — covered by `test_payload_missing_tenant_id_raises`. |
| `.claude/rules/backend-ddd.md` | mandatory | Inside-Out: wire = application service consuming a domain event. Cross-module crm↔sales_agent via event + injected ports (no direct import — verified by `test_wire_does_not_import_crm_or_engine_concretions`). `structlog` (no print). Pydantic v2 `ConfigDict` on the event DTO. |

LangGraph canonical docs: **NOT fetched** — no LangGraph state/graph/edge/checkpointer modified (wire is
persistence + read-surface only). graceful-degradation (timeout+fallback+circuit-breaker family): all wire
writes are best-effort `try/except` + structlog warning; the origin override turn (PATCH /stage) has already
committed, so a wire failure never breaks anything.

### CONTEXT-BRIEF § 11 gaps acknowledged (R24 partial flag)
- **Gap #3** — override-context wire persists context (real, BE-valid here) but the conversational effect
  ("Adrián adjusts his next step") is only observable once Inbox/sales_agent are live (deferred, LOW,
  per 03-arch § Open Questions #4). This ticket = persist + read surface + handover activity (SC-1b BE).
  The concrete `CheckpointMetadataPort` / `HandoverActivityPort` adapters that bind to the live engine
  read + crm `LeadActivityRepository` are wired when the agent goes live (out of this ticket's scope —
  ticket is "wire thin: subscriber + persistence", not the runtime registration).

---

## Decisions

### How override_context is read in the next turn (no schema change)
The engine `agent_state_checkpoints` row has an **existing nullable `metadata_info` JSONB** column, keyed
`(tenant_id, lead_id, is_active)`, read by the sales_agent's next turn via the engine
`StateRepository.get_active_checkpoint`. The wire merges an `override_context` dict under the
`OVERRIDE_CONTEXT_KEY = "override_context"` key of that JSONB — **no new column, no DDL, no §3 schema edit**
(03-arch § 8.1 explicitly: "campo de lectura existente `metadata_info` … NO se añade columna"). The
`override_context` payload = `{reason, from_stage, to_stage, actor_user_id, source="manual_override",
occurred_at(ISO)}`. The next turn reads `reason` so Adrián resumes WITHOUT re-asking answered questions.

### Why NO reset (RN-4.1 "feeds, does not reinitialize")
The `CheckpointMetadataPort` surface is intentionally narrow — a single `set_override_context`. There is no
`deactivate` / `save_checkpoint` / `reset` / `set_current_stage`. `test_override_context_does_not_reinitialize_agent`
asserts none of those is ever called, so the agent resumes from accumulated state (current_stage / turn_count
untouched), only enriched with the human's reason.

### Port/event used for lead_activity (handover, no crm import)
The handover (🙋 humano → 🤖 Adrián) is recorded via the injected `HandoverActivityPort.record_handover`
Protocol, NOT a direct call into crm's `LeadActivityRepository`. This honors the DDD cross-module ban
(05-guidelines § Agentic: "NO importar crm/ desde sales_agent/"). The prod adapter for this port delegates
to crm `LeadActivity.record(actor="human", kind="stage_move"/"handover", description_es=…)` — but the wire
only knows the Protocol. `description_es` is Spanish neutro, 3rd person, NON-PHI (RN-2 firewall: the reason
is operator-authored commercial funnel context, never clinical data) — a `_REASON_SNIPPET_LEN=120` snippet
is surfaced for the Historial.

> Note: crm `FunnelService.transition_stage` already records a generic `stage_move` activity + emits the
> `lead_stage_overridden` event (T-BE-2 step 8 + step 10). The wire's activity is the **agentic-domain
> handover** (🙋→🤖 takeover semantics) — distinct from the generic funnel micro-log, owned by the
> sales_agent module per the agentic surface (03-arch § 8.8). No duplication: different actor/kind/semantics.

### Why NO schema touch / NO graph / NO tool / NO prompt
03-arch § 8 scope is "minimal: wire thin brand-local". The override is **context the agent reads**, not an
**action the agent takes** — so no tool (§ 8.4), no graph node (§ 8.2), no state field (§ 8.1), no prompt
slot edit (§ 8.5). The wire is a subscriber + two best-effort persistence writes. This keeps the engine
runtime + `agent_state_checkpoints` schema (§3-protected, `/pm-luana` lift territory) entirely untouched.

### Coupling decision: domain event over port (03-arch § 8.11 recommendation)
The crm→sales_agent direction uses the **domain event** `lead_stage_overridden` (already emitted via outbox
by T-BE-2), consumed by this subscriber — matching the architect's recommendation (03-arch § 8.11 "Decisión
de acoplamiento: recomendación domain event"). The wire's own dependencies (checkpoint write + activity
record) are **injected ports** so the subscriber stays unit-testable with AsyncMock and decoupled from both
the engine sync repo and crm.

### Subscriber registration (deferred, documented)
The wire exposes `handle_lead_stage_overridden(payload: dict)`. Its registration onto the outbox dispatcher
+ the concrete port adapters (engine `metadata_info` writer + crm `LeadActivity` writer) are wired when
Inbox/sales_agent goes live (gap #3). This ticket delivers the wire + its contract + full unit coverage —
the "thin subscriber + persistence" per the ticket title; the live runtime registration is downstream
(03-arch § Open Questions #4, acknowledged LOW). No orphan: the wire's consumer is the outbox dispatcher
for `lead_stage_overridden` (event already emitted today by T-BE-2); the registration point is the only
deferred piece, and it has no other home until the agent runtime is live.

done -> vitalia/docs/product/stories/vitalia-fase2-adrian-embudo/T-AG-1-result.md
