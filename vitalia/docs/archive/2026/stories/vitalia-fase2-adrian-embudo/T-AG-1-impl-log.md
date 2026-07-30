# T-AG-1 Impl Log — Override-context wire (RN-4.1)

**Ticket:** T-AG-1 (vitalia-fase2-adrian-embudo)
**Surface:** agentic brand-extension (`vitalia/backend/src/modules/vitalia/sales_agent/`)
**Model:** Opus 4.8 (R23 HARD — AGENTIC production_code)
**Step 0 date:** 2026-06-04

---

## ⚠ Environment note (sandbox vs hub)

This builder runs in an isolated worktree sandboxed at branch `worktree-agent-...` (HEAD `a2c38840` = main),
which does NOT contain T-BE-1/T-BE-2 (they live on the hub `wip/vitalia`). The harness write-guard blocks
writing to the hub's `~/Proyectos/luana-vitalia/` paths. To build + run RED→GREEN against the T-BE-2
`lead_stage_overridden` substrate, I materialized the crm dependency tree into my sandbox via
`git checkout wip/vitalia -- vitalia/backend/src/modules/vitalia/crm/` (CONSUMED, not delivered).
**Deliverables (the 2 NEW sales_agent files + 1 test) are written in-sandbox; the orchestrator applies them
to the hub by pathspec.** The materialized crm/* files MUST NOT be committed by the orchestrator (already
on hub). See § Files for the exact deliverable pathspec.

## R24 brief acceptance gate

CONTEXT-BRIEF.md header: `Validator pass: DEFERRED` · `Faithfulness flag: partial`.
`partial` is NOT `blocking` → PROCEED + cite § 11 gaps.
§ 11 gap relevant to T-AG-1: **#3** — wire persists context (real, BE-valid) but conversational effect
("Adrián adjusts next step") only observable when Inbox/sales_agent live (deferred, LOW, acknowledged in
03-arch § Open Questions #4 + 06-tickets `notes_for_downstream`). My ticket scope = persist + read surface
+ handover activity (SC-1b BE).

## ENGINE vs BRAND-EXTENSION boundary check

- Target: `vitalia/backend/src/modules/vitalia/sales_agent/application/services/` → **BRAND EXTENSION ✅**
- `agent_state_checkpoints` schema: **NOT touched** (engine-owned §3). Write lands in existing nullable
  `metadata_info` JSONB under key `override_context` — zero DDL, zero column.
- `core/luana-core-*/src/**`: read-only awareness (confirmed `metadata_info` is the next-turn read surface
  keyed `(tenant_id, lead_id, is_active)` via engine `StateRepository.get_active_checkpoint`).

## Skills Consulted (must_load enforcement v4.1)

| Skill / doc | Why | Decision captured |
|---|---|---|
| `sales-agent-expert` | mandatory (06-tickets T-AG-1 must_load_skills) | §0 anti-dup cardinal → grep cross-codebase for override-context/checkpoint-metadata writer = 0 hits (NET-NEW). §3 NO-TOUCH confirms `agent_state_checkpoints` schema protected → write into existing `metadata_info` JSONB, no DDL. Cross-module ban → NO `from ...crm import` inside `sales_agent/`; receive via event payload + inject deps via brand-local Protocol ports. NO new graph/tool/prompt/specialist — 03-arch § 8.1/8.2/8.4/8.6 all "NO se modifica / sin topología / NO tool / N/A". Override-context = volatile per-turn signal (§ 8.5), NOT cacheable prefix. |
| `.claude/rules/anti-duplication.md` | mandatory | Inventory has NO override-context abstraction (brand-local vertical-specific). Checkpoint read is engine `StateRepository.get_active_checkpoint` (SYNC). Wire does NOT mirror it — abstracts read/update behind brand-local `CheckpointMetadataPort` Protocol whose concrete impl is injected (tests=AsyncMock; prod adapter deferred — wire stays decoupled from sync engine repo + from crm). |
| `.claude/rules/tenant-isolation.md` | mandatory | Every wire method requires tenant_id; event payload carries tenant_id; checkpoint write + activity record both filter tenant_id. Missing tenant → ValueError (no silent cross-tenant). |
| `.claude/rules/backend-ddd.md` | mandatory | Inside-Out: wire = application service. Cross-module crm↔sales_agent via domain event + injected ports (no direct import — DDD boundary). structlog (no print). Pydantic v2 ConfigDict for event DTO. |

LangGraph canonical docs: NOT fetched — no state/graph/edge modified.
graceful-degradation: all wire writes best-effort try/except (never breaks origin override turn).

## Cross-module / NO-NEW-LAYER audit

```
grep override_context|OverrideContext|handle_lead_stage_overridden|next_turn_context core/ {4 brands}/backend/src
  → 0 hits (only docstring mention in crm/domain/lead_stage_transition.py) ⇒ NET-NEW brand-local justified
engine next-turn read surface: agent_state_checkpoint_model.py::metadata_info (JSONB nullable), keyed
  (tenant_id, lead_id, is_active) via StateRepository.get_active_checkpoint (SYNC)
LeadActivityRepository.record(lead_id, *, tenant_id, actor, kind, description_es) — async, NON-PHI
event emission already shipped: funnel_service.py step 10 publishes lead_stage_overridden when
  triggered_by=manual_override and reason
```

Decision: **EXTEND-by-consume** — no new infra layer. Wire consumes (a) existing `lead_stage_overridden`
payload, (b) existing `metadata_info` checkpoint field via injected port, (c) existing `LeadActivity.record`
via injected port. No mirror, no engine edit, no schema change.

## Plan (TDD RED first — see § Tests)

(implementation captured in T-AG-1-result.md § Decisions)
