# Changelog — luana-core-flows

All notable changes to the durable-flows engine package.
Format: [Keep a Changelog](https://keepachangelog.com/) · SemVer.

## [0.1.0] — 2026-06-02

L1 of the durable-flows engine (proposal `2026-06-02-durable-flows-engine`, accepted →
migrated). Lifts the per-brand `AsyncPostgresSaver` checkpointer factory mirror
(`vitalia/.../copilot/workflows/wizard_checkpoint_config.py::build_production_checkpointer`
+ comunify inline equivalents) into a single shared engine provider, per
`.claude/rules/anti-duplication.md` + ADR-013 (Fase B cornerstone — durable flow as a
first-class engine primitive).

### Added
- `luana_core_flows.checkpointer.make_durable_checkpointer(*, postgres_dsn, encryption_key=None,
  run_setup=True, pool_max_size=20)` — builds the production durable `AsyncPostgresSaver`
  (`langgraph-checkpoint-postgres>=3.1.0`). Lifespan-safe pooled construction
  (`AsyncConnectionPool`, `autocommit=True` + `dict_row` + `prepare_threshold=0`); deferred
  psycopg import (module stays importable without libpq); `EncryptedSerializer.from_pycryptodome_aes()`
  wired when `encryption_key` is set (PHI at-rest); idempotent `setup()` once at construction.
  NEVER returns `MemorySaver`.
- `luana_core_flows.checkpointer.build_flow_thread_id(*, flow_id, tenant_id, instance_id)` and
  `build_phi_flow_thread_id(*, flow_id, tenant_id, clinic_id, instance_id)` — tenant-scoped
  (and PHI dual-filter) durable thread_id composition with separator-collision guards.

### Notes
- `langgraph-checkpoint-postgres` 3.1.0 has FIXED checkpoint table names (no `table_prefix`):
  brand isolation is the per-brand Postgres DB; tenant isolation is the `thread_id` tenant segment.
- Resolves against the already-locked `langgraph 1.2.0` / `langgraph-checkpoint 4.1.0` — **no
  version bump** to the engine stack.
- Consumers (L1): vitalia (wizard onboarding, lucas daily analysis, treatment follow-up) +
  comunify (community engagement, cohort enrollment), each via a per-brand durable-checkpointer
  accessor that calls this provider.

### Deferred (L2 — next story, design-only here)
- `FlowDefinition` (Pydantic declarative) + `FlowCompiler.compile` (`domain/`).
- Extension SDK `EP-19 durable_flow_register`.
- Per-node `luana-core-idempotency` replay guards + `copilot_trace_event` flow observability.
