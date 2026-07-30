---
story_id: empleados-ia-auto-extension
surface: agentic (engine core/luana-core-flows + vitalia/comunify graph wiring)
builder: builder-agentic (Opus — R23 agentic production code)
auditor: auditor-agentic (Opus)
authorization: docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md (accepted)
parent: 03-arch.md
---

# 03-arch-agentic — Durable checkpointer provider + 5-graph wiring (L1)

> Read `03-arch.md` (consolidated) first. This is the agentic-surface slice. **L2 (FlowCompiler/FlowDefinition/EP-19) is design-only — see 03-arch.md § L2, NOT built here.**

## Scope (build now)

1. **NEW** `core/luana-core-flows/src/luana_core_flows/checkpointer/` — `make_durable_checkpointer` + `build_flow_thread_id`.
2. **Wire** the 5 brand graphs' composition roots to consume the core provider (graph signatures + topology UNCHANGED — they already take `checkpointer` via DI).
3. **DELETE** the brand checkpointer factory mirror (vitalia `wizard_checkpoint_config.py` + comunify inline equivalents).

## Provider contract (core/luana-core-flows/checkpointer/provider.py)

```python
async def make_durable_checkpointer(
    *, postgres_dsn: str, encryption_key: str | None = None,
    table_prefix: str = "luana_flows_", run_setup: bool = True,
) -> BaseCheckpointSaver: ...
```

Wiring rules (LangGraph canonical docs, verified 2026-06-02):
- `AsyncPostgresSaver` from `langgraph.checkpoint.postgres.aio`. `from_conn_string` is an **async CM** → use lifespan-safe pattern (pooled psycopg conn with `autocommit=True` + `row_factory=dict_row`, OR enter CM for app lifespan). Document the choice (O-1).
- `encryption_key` set → `serde=EncryptedSerializer.from_pycryptodome_aes()` (reads `LANGGRAPH_AES_KEY`; vitalia PHI). comunify passes `None`.
- `run_setup=True` → `await saver.setup()` ONCE at lifespan startup (idempotent, internal IF NOT EXISTS). NEVER per-invocation.
- **NEVER returns MemorySaver** (tutorial-only). Tests inject `InMemorySaver` directly at the composition root, NOT via this factory.
- `structlog` only; async-first.

## thread_id helper (checkpointer/thread_id.py)

```python
def build_flow_thread_id(*, flow_id: str, tenant_id: str, instance_id: str) -> str:
    # f"{flow_id}:{tenant_id}:{instance_id}"  — tenant segment = isolation
def build_phi_flow_thread_id(*, flow_id, tenant_id, clinic_id, instance_id) -> str:
    # embeds clinic_id (vitalia hipaa-lite dual-filter)
```
The 5 sites adopt this, mapping their current keys into `flow_id`/`instance_id` slots — **preserve existing collision/isolation semantics, no behavior change to thread keying**:
- vitalia wizard: `vitalia.wizard.{tenant}.{draft}` → `flow_id="vitalia.wizard"`, `instance_id=draft_id`
- vitalia treatment cron: `{tenant}:{treatment}` → `flow_id="vitalia.treatment_followup"`, `instance_id=treatment_id`
- vitalia lucas: composite `(tenant, clinic, period)` → use `build_phi_flow_thread_id` variant
- comunify community: `{tenant}:{subscriber}` → `flow_id="comunify.community_engagement"`, `instance_id=subscriber_id`
- comunify cohort: `{tenant}:{lead}` → `flow_id="comunify.cohort_enrollment"`, `instance_id=lead_id`

## 5-graph wiring (composition roots only — signatures unchanged)

| Site | Compile (DO NOT TOUCH) | Composition root (REWIRE) |
|---|---|---|
| vitalia wizard | `copilot/workflows/wizard_onboarding_graph.py:323` | `copilot/application/services/wizard_orchestrator_service.py` + `copilot/workflows/cron_handler.py` |
| vitalia treatment | `copilot/workflows/treatment_followup_workflow.py:753` | `copilot/workflows/cron_handler.py` |
| vitalia lucas | `agentic/lucas/workflows/lucas_daily_analysis_graph.py:503` | `agentic/lucas/application/services/lucas_orchestrator_service.py` (replace inline `MemorySaver()`) |
| comunify community | `copilot/workflows/community_engagement_workflow.py:593` | `comunify/.../copilot/workflows/cron_handler.py` |
| comunify cohort | `copilot/workflows/cohort_enrollment_workflow.py:913` | `comunify/.../copilot/workflows/cron_handler.py` |

At each composition root: `cp = await make_durable_checkpointer(postgres_dsn=settings..., encryption_key=<vitalia: env LANGGRAPH_AES_KEY | comunify: None>, table_prefix="<brand>_flows_")` → `.setup()` once at startup → pass into existing `build_*_graph(checkpointer=cp)`.

## DELETE (anti-dup — the whole point)

- `vitalia/.../copilot/workflows/wizard_checkpoint_config.py::build_production_checkpointer` + `WIZARD_CHECKPOINT_TABLE_PREFIX`. If `CheckpointerProtocol` is imported elsewhere → re-export from `luana_core_flows.checkpointer`; else delete.
- comunify inline factory bits (the `from langgraph.checkpoint.redis import RedisSaver` deferred-import blocks in `community_engagement_workflow.py` / `cohort_enrollment_workflow.py` that were the prod-construction comments — replace with the core provider call at the cron composition root; the workflow files keep accepting injected `checkpointer`).
- Post-L1 invariant: `grep -rln build_production_checkpointer {vitalia,comunify}/backend/src` → 0.

## copilot-expert / sales-agent-expert decisions referenced
- **copilot-expert:** production checkpointer ≠ MemorySaver (cardinal); no mirror of shared abstractions (anti-dup); the wizard/treatment/lucas graphs are brand extensions — wiring them to a core provider respects the engine boundary. NO touch to `copilot/` engine topology, registries, or anchors.
- **sales-agent-expert §3:** `agent_state_checkpoints` (sales_agent per-conversation table) is PROTECTED and ORTHOGONAL — durable-flows checkpoint tables (`<brand>_flows_*`, LangGraph-owned) are a separate namespace. Do NOT touch the sales_agent checkpoint schema. sales_agent graphs are NOT in the 5-site scope.
- **LangGraph canonical:** replay re-executes post-checkpoint nodes → L1 documents the idempotency seam (full guard wrapping is L2 via `luana-core-idempotency`); L1's 5 graphs are existing + already idempotent-aware at their cron layer (lucas `idempotent_cron` upstream, etc.).

## Tests (TDD RED-first, this surface)
- `core/luana-core-flows/tests/checkpointer/test_provider.py` — RED: signature, serde wiring when `encryption_key` set, `table_prefix` honored, `run_setup` calls `.setup()`, returns a `BaseCheckpointSaver` (NOT MemorySaver). Mock/stub the AsyncPostgresSaver where a live DB isn't available; an integration test (marker `integration`) hits a real Postgres for `.setup()` idempotency.
- `core/luana-core-flows/tests/checkpointer/test_thread_id.py` — RED: tenant-scoped composition + collision-safety + PHI clinic variant.
- **Replay-safety** (validator `v_replay_safety`): an integration test that compiles one of the 5 graphs with the durable checkpointer, advances ≥1 checkpoint, simulates resume (re-invoke same thread_id), asserts state resumes from the persisted checkpoint (not restart). Lives brand-side (vitalia wizard preferred).
- Brand suites: vitalia copilot workflows + lucas + comunify copilot GREEN with the package installed (downstream regression).
