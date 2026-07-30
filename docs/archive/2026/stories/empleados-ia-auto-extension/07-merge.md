---
story_id: empleados-ia-auto-extension
deliverable: durable-flows-engine-L1   # outcome item 1b — NOT the whole umbrella story
merged_to: wip/vitalia
merged_on: 2026-06-02
merged_by: /pm-luana
verdict: APPROVED (REVIEW-agentic.md, in-place audit)
proposal: docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md (migrated)
---

# 07-merge — Durable flows engine L1 (T-flows-1..5)

> **Scope of THIS merge:** the durable-flows engine **L1 deliverable** (outcome item **1b**), NOT the
> whole `empleados-ia-auto-extension` umbrella story. The umbrella roadmap (outcome §) still has items
> 2+ pending ("post L1+L2") and L2 is design-only (deferred-next-story). See § 5.

## 1. What merged

L1 of the durable-flows engine — "cero stub AsyncPostgresSaver pending en ninguna marca":

| Commit | Ticket | Surface |
|---|---|---|
| `c8551ed7` + `98006df8` | T-flows-1/2 | `core/luana-core-flows` scaffold + provider (`make_durable_checkpointer` + thread_id, 13 unit tests) |
| `88175663` | T-flows-3 | wire 5 brand graphs → core provider + DELETE `wizard_checkpoint_config.py` mirror + per-brand durable accessors + brand deps |
| `76f9e55b` | T-flows-4 | idempotent checkpoint migrations vitalia 037 + comunify 002 |
| `335ed390` | T-flows-5 | comunify durable-resume consumer test (CONN) |

Engine boundary: `core/luana-core-*/src` edits were T-flows-1/2 only, authorized by the migrated proposal.
T-flows-3/4/5 touch brand surfaces + migrations + tests. The 5 `build_*_graph` signatures/topologies +
`agent_state_checkpoints` (sales_agent) UNCHANGED.

## 2. Verification (gates)

| Validator | Result |
|---|---|
| v_lint_flows_pkg / v_lint_brands (vitalia+comunify) | ✅ clean (Carril A: 7 pre-existing comunify isort swept) |
| v_uv_sync_resolves | ✅ (no langgraph version bump) |
| v_unit_checkpointer_provider / v_unit_thread_id | ✅ 13 passed |
| v_no_brand_mirror | ✅ `grep build_production_checkpointer src` = 0 |
| v_no_factory_test_mock | ✅ 0 |
| v_workspace_members | ✅ 27→28 (T-flows-1) |
| v_migration_idempotent | ✅ vitalia 036→037 ×2 + comunify 001→002 ×2 (live :5435, no error) |
| v_setup_idempotent | ✅ `AsyncPostgresSaver.setup()` ×2 real Postgres (O-2) |
| v_replay_safety | ✅ wizard durable resume across fresh pool (live vitalia_dev) |
| v_downstream_vitalia | ✅ 463 passed (copilot/workflows + lucas + architecture) |
| v_downstream_comunify | ✅ 182 passed (agentic_evals/workflows + architecture) |

Pre-existing OUT-OF-SCOPE (not introduced; on HEAD): `test_ep8_channel_adapters_count_three` (stale
3-vs-10) + whole-tree `-k` collection errors in unrelated e2e/unit files. See REVIEW-agentic.md F1/F2.

## 3. Verificación live (DoD #37) — durable persist + resume

```yaml
dod_live_verified: true
dod_env: "make dev-vitalia (stack up :5435) → in-container alembic + native pytest w/ psycopg[binary] + psql"
dod_evidence:
  - action: "wizard_onboarding durable graph: ainvoke a thread on AsyncPostgresSaver, then aget_state from a FRESH pool (v_replay_safety, vitalia_dev)"
    observed: "state resumed from persisted checkpoint (tenant_id + thread_id intact); 3 rows in public.checkpoints WHERE thread_id LIKE 'vitalia.wizard:%' (NOT MemorySaver)"
    backend_log: "no traceback; AsyncPostgresSaver.setup() created checkpoints/checkpoint_blobs/checkpoint_writes/checkpoint_migrations"
  - action: "comunify community_engagement durable graph: advance + resume across reset pool (comunify_dev)"
    observed: "8 rows in public.checkpoints WHERE thread_id LIKE 'comunify.community:%'; resume reconstructs current_step + tenant isolation"
  - action: "migration idempotency (both brands) applied live + re-run"
    observed: "036→037 / 001→002 applied; 2nd upgrade head = no-op no error; setup() twice = no error"
verified_at: 2026-06-02
```

> The honest gate: durable persistence proven by **real Postgres rows + resume across a new pool** — a
> `MemorySaver` could never produce these. Routes for the wizard graph are still Slice-1 stubs (the graph
> is not yet wired to a live HTTP route), so the live exercise is the scripted-real-invocation fallback
> (O-3) — still a real durable thread + real psql observation + real resume.

## 4. Docs / contract

- proposal → `migrated` (+ migrated_commits + migration_note).
- `core/luana-core-flows/CHANGELOG.md` [0.1.0].
- `docs/core-modules/flows.md` + README index row.
- No brand cap YAML (platform engine infra, `cap_target: null`).

## 5. Follow-ups (umbrella continues — story NOT fully done)

The `empleados-ia-auto-extension` umbrella (outcome roadmap) continues:
- **L2 (design-only, deferred-next-story):** `FlowCompiler` / `FlowDefinition` / EP-19 — ready-package seed
  in `03-arch.md § L2`. Build = separate story.
- **Outcome item 2+ (pending, post L1+L2):** derived story vitalia (instantiate the model on the existing
  SYSTEM-MAP + first real durable flow over L1), plus the broader empleados-IA derived stories.
- Therefore the umbrella `checkpoint.md` should reflect **L1 deliverable DONE + umbrella continues**, NOT
  flip the whole story to `done`+archive. Archive decision surfaced to Chris (the 00-research + L2 design +
  vision SSoT are still live references for items 2+).
