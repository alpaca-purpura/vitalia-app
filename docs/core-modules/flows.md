---
package: luana-core-flows
verdict: durable-runtime
version: 0.1.0
eps: [EP-19]            # L2 design-only (deferred-next-story) — NOT yet built
consumers: [vitalia, comunify]
status: active
---

# luana-core-flows — public contract

Brand-agnostic **durable-flows engine**. L1 ships the durable checkpointer provider (the
runtime that makes multi-step agent flows survive process restarts via Postgres); L2 (design
only, deferred) adds the declarative `FlowDefinition` / `FlowCompiler` + Extension SDK `EP-19`.

Origin: ADR-013 (Fase B cornerstone — "flujo durable de 1ª clase") + promotion proposal
`docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md` (migrated 2026-06-02).
Lifted the per-brand `AsyncPostgresSaver` factory mirror into this single engine package
(`anti-duplication.md`).

## Contract público (L1)

```python
from luana_core_flows.checkpointer import (
    make_durable_checkpointer,    # async → production AsyncPostgresSaver (NEVER MemorySaver)
    build_flow_thread_id,          # tenant-scoped durable thread_id
    build_phi_flow_thread_id,      # + clinic_id (vitalia hipaa-lite dual-filter)
)

async def make_durable_checkpointer(
    *, postgres_dsn: str, encryption_key: str | None = None,
    run_setup: bool = True, pool_max_size: int = 20,
) -> BaseCheckpointSaver: ...
```

- `encryption_key` set → `EncryptedSerializer.from_pycryptodome_aes()` (PHI at-rest).
- `run_setup=True` → idempotent `.setup()` once at construction (lifespan-safe pooled conn).
- Fixed checkpoint table names (`checkpoints` / `checkpoint_blobs` / `checkpoint_writes` /
  `checkpoint_migrations`) — **no `table_prefix`** in `langgraph-checkpoint-postgres` 3.1.0;
  isolation = per-brand Postgres DB + tenant segment in `thread_id`.

## Extension points

- **EP-19 `durable_flow_register`** — DESIGN ONLY (L2, deferred-next-story). See
  `docs/architecture/luana-platform/durable-flows-L2-design.md § L2.3`. NOT in
  `extension_points.py::_EP_IDS` yet.

## Brands consumidoras

| Brand | Flows wired (L1) | Encryption |
|---|---|---|
| vitalia | wizard onboarding · lucas daily analysis · treatment follow-up | `LANGGRAPH_AES_KEY` (when set) |
| comunify | community engagement · cohort enrollment | none (non-PHI) |

Each brand consumes the provider via a per-brand durable-checkpointer accessor
(`get_{brand}_durable_checkpointer`) — the single production construction surface.

## Promotion history

- `2026-06-02-durable-flows-engine` (migrated 2026-06-02) — L1 provider lift + 5-graph wiring +
  mirror delete + idempotent migrations + downstream regression + DoD #37 live-verify.

## Drill-down

- Code: `core/luana-core-flows/src/luana_core_flows/checkpointer/{provider,thread_id}.py`
- Tests: `core/luana-core-flows/tests/checkpointer/` (+ brand durable-resume integration tests)
- CHANGELOG: `core/luana-core-flows/CHANGELOG.md`
- L2 design SSoT: `docs/architecture/luana-platform/durable-flows-L2-design.md`
