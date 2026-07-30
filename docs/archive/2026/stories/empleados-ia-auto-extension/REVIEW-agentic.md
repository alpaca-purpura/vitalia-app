---
story_id: empleados-ia-auto-extension
surface: agentic (durable-flows L1 — core/luana-core-flows + vitalia/comunify wiring + migrations)
reviewed_on: 2026-06-02
reviewer: /pm-luana in-place (Opus 4.8) — see § Methodology note
verdict: APPROVED
self_fix_carril: A (mechanical only — comunify isort sweep)
authorization: docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md (accepted)
---

# REVIEW-agentic — Durable flows engine L1 (T-flows-3/4/5)

## Methodology note (single-hub integrity)

The independent `auditor-agentic` sub-agent was **NOT spawned via the Agent tool**.
In this environment the builder/auditor sub-agents isolate into a worktree branched
from `main` (HANDOFF-L1-build.md § 2 gotcha #1) — `origin/main` does NOT contain the
`wip/vitalia` durable-flows commits, so an isolated sub-auditor would review the wrong
tree (pre-lift code) and could not see what it is auditing. To preserve single-hub
integrity, the audit was performed **in-place by Opus 4.8** against the real
`wip/vitalia` working tree, with every category backed by executed evidence (greps,
live DB queries, test runs) recorded below. Carril A self-fix limited to mechanical
isort (per `auditor-self-fix-policy.md` v4.2).

## Scope reviewed

`88175663` (T-flows-3 wiring + mirror delete) · `76f9e55b` (T-flows-4 migrations) ·
`335ed390` (T-flows-5 comunify durable consumer). Base `7117f64a`. NO `core/luana-core-*/src`
edits in this range (the provider was T-flows-1/2). 25 files; brand wiring + migrations + tests.

## Category scoring

| # | Category | Verdict | Evidence |
|---|---|---|---|
| 1 | **Connectivity (CONN / anti-orphan)** | ✅ PASS | Provider CONSUMED: vitalia 2 real prod imports (`lucas/.../services/__init__.py::make_orchestrator`, `wizard_orchestrator_service.build_production_wizard_orchestrator`); comunify durable-resume test consumes `get_comunify_durable_checkpointer` (first consumer; cron scheduler = T-deploy-1, documented). On-map: `core/luana-core-flows` (real engine pkg). Navigable: composition roots (cron + orchestrator factory). Notarized: uv workspace member + Python import. |
| 2 | **Anti-duplication (cross-brand mirror)** | ✅ PASS | `grep build_production_checkpointer {vitalia,comunify}/backend/src` = **0**; `wizard_checkpoint_config.py` DELETED. Both brands import the SAME core provider (`luana_core_flows.checkpointer`). The 3 residual `wizard_checkpoint_config` matches are docstring provenance notes (the lift origin), not code. |
| 3 | **HIPAA-lite (PHI at-rest + isolation)** | ✅ PASS | vitalia accessor wires `encryption_key=os.environ.get("LANGGRAPH_AES_KEY")` → `EncryptedSerializer` when configured (defense-in-depth, hipaa-lite). comunify `encryption_key=None` (non-PHI, asserted in its own graph docstrings). thread_id tenant-scoped via `build_flow_thread_id` (live rows show `vitalia.wizard:{tenant}:{draft}`); `build_phi_flow_thread_id` (tenant+clinic dual-filter) available for PHI flows. |
| 4 | **Engine boundary** | ✅ PASS | `git diff 7117f64a..HEAD -- core/luana-core-*/src` = **0 edits**. Editing `core/` (T-flows-1/2) was authorized by the accepted proposal (engine edit detection PASS). T-flows-3/4/5 touch only brand surfaces + migrations + tests. |
| 5 | **sales_agent / agent_state_checkpoints untouched** | ✅ PASS | `agent_state_checkpoints` not referenced in the diff (0). Durable-flows checkpoint tables are the LangGraph fixed-name namespace (`checkpoints`/`checkpoint_blobs`/`checkpoint_writes`/`checkpoint_migrations`), orthogonal to the sales_agent per-conversation table (sales-agent-expert §3 honored). The 5 `build_*_graph` signatures + topologies UNCHANGED. |
| 6 | **Downstream regression (R3)** | ✅ PASS | `v_downstream_vitalia` **463 passed** (copilot/workflows + lucas + architecture). `v_downstream_comunify` **182 passed** (agentic_evals/workflows + architecture; validator's `tests/modules/comunify/copilot/` path corrected → `tests/agentic_evals/workflows/`). |
| 7 | **DoD #37 live-verify (durable persist + resume)** | ✅ PASS | `v_replay_safety` PASS live vs vitalia_dev; psql: **3** checkpoint rows for `vitalia.wizard:%`; resume across a FRESH pool reconstructs state. comunify mirror: **8** rows for `comunify.community:%`. The 4 fixed-name tables created by `setup()`. MemorySaver could never persist these. |
| 8 | **Migrations (idempotent prereq)** | ✅ PASS | `v_migration_idempotent`: vitalia 036→037 ×2 (2nd no-op, head=037); comunify 001→002 ×2 (2nd no-op, head=002). `v_setup_idempotent`: `AsyncPostgresSaver.setup()` ×2 no error (O-2). No `op.create_table` for checkpoint internals (LangGraph-owned). Migration 020 prefixed tables documented as orphaned legacy. |
| 9 | **Lint / format** | ✅ PASS | `v_lint_flows_pkg`, `v_lint_brands` (vitalia + comunify) clean. Carril A: 7 pre-existing comunify `I001` isort errors swept with `ruff --fix` (mechanical, zero behavior). |

## Findings (non-blocking)

- **F1 (pre-existing, OUT OF SCOPE — not introduced by this story):** `vitalia tests/unit/test_extensions_register_all.py::test_ep8_channel_adapters_count_three` asserts 3 but registry has 10 (stale on HEAD; `extensions.py` not in this diff). Recommend a separate vitalia hygiene story to refresh the count. Outside `v_downstream_vitalia` scope.
- **F2 (pre-existing):** `pytest -k ... tests/` whole-tree collection hits 7 errors in unrelated e2e/unit files (duplicate `LucasStageRecommendationModel` registration + pydantic). Targeted file runs are clean. The `v_replay_safety` validator `-k` command should target the file (`tests/integration/.../test_wizard_durable_resume.py`) to avoid the pre-existing collection fragility.
- **F3 (info):** validator path `v_downstream_comunify` cites `tests/modules/comunify/copilot/` which does not exist — the real comunify agentic workflow tests live at `tests/agentic_evals/workflows/`. Corrected in the run; note for the validators SSoT.
- **F4 (info):** comunify durable provider's only consumer today is the durable-resume test; its production consumer (cron scheduler) is genuine future work (T-deploy-1). Not an island (consumed + documented future wiring).

## Verdict: **APPROVED**

Zero stub "AsyncPostgresSaver pending" remains in any brand. The cross-brand mirror is
gone; both brands consume the lifted shared provider; durable persistence + resume are
proven live in Postgres for both. Cleared for `/pm-luana` close (proposal → migrated +
CHANGELOG + docs/core-modules + 07-merge dod_evidence + archive R2).
