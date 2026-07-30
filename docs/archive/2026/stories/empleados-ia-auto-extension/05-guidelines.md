---
story_id: empleados-ia-auto-extension
brand: platform
authorization: docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md (accepted)
scope: two-layer (L1 build / L2 design)
---

# 05-guidelines — Durable flows engine (L1 build)

## must_load_skills (per surface)

| Surface | Skills (load BEFORE coding) |
|---|---|
| `core/luana-core-flows` provider + graph wiring (builder-agentic) | `copilot-expert` · `sales-agent-expert` · LangGraph canonical docs (`https://docs.langchain.com/oss/python/langgraph/durable-execution`) · `.claude/rules/anti-duplication.md` · `vitalia/.claude/rules/hipaa-lite.md` (for the encryption_key/PHI path) |
| package scaffold + uv + migrations (builder-backend) | `backend-expert` · `.claude/rules/backend-migrations.md` · `.claude/rules/anti-duplication.md` |

## must_load_artifacts
- `03-arch.md` (consolidated), `03-arch-agentic.md`, `03-arch-be.md`
- `spike-durable-flows.md` (§4 EP contract, §5 NO-NEW-LAYER, §6 risks)
- `docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md` (the lift authorization — cite in every engine ticket)
- `ADR-013-empleados-ia-auto-extension.md` (D2)

## Patterns REQUIRED
- **`make_durable_checkpointer` is the ONLY production checkpointer construction site, in `core/`.** Both brands import it. ZERO brand-local factory.
- `AsyncPostgresSaver` (langgraph.checkpoint.postgres.aio) for production. `InMemorySaver` ONLY in tests, injected directly at the composition root (never via the factory).
- `.setup()` called ONCE at app lifespan startup (idempotent). NEVER per-invocation.
- `encryption_key` → `serde=EncryptedSerializer.from_pycryptodome_aes()` for vitalia (PHI at-rest). comunify `None`.
- `thread_id` ALWAYS tenant-scoped via `build_flow_thread_id` (+ clinic for PHI). The tenant segment is the isolation boundary.
- Migrations: raw SQL idempotent (`IF NOT EXISTS`). Checkpoint table internals are LangGraph-owned (`.setup()`) — alembic only does prerequisites/namespace record.
- `structlog` only; async-first; Pydantic v2 (`ConfigDict`) for any model.
- uv member inserted in strict alphabetical position; `uv sync` from ROOT only.
- Cite the accepted proposal in every commit touching `core/`.

## Patterns FORBIDDEN
- ❌ Mirroring the checkpointer factory in any brand (the whole story deletes the existing mirror — do not re-create it). `anti-duplication.md` cardinal.
- ❌ Returning `MemorySaver`/`InMemorySaver` from `make_durable_checkpointer` (tutorial-only — production MUST be durable).
- ❌ Bumping `langgraph>=0.2` floor in copilot/sales-agent/brand-studio (NOT needed — uv already resolves 1.2.0; bump = needless downstream churn).
- ❌ Adding `langgraph-checkpoint-postgres` to copilot/sales-agent ENGINE pkgs (they don't construct checkpointers in L1).
- ❌ `op.create_table()` / `sa.Enum(create_type=True)` / non-idempotent DDL.
- ❌ Hand-writing the checkpoint table column DDL in alembic (LangGraph owns it — schema drift risk).
- ❌ Touching the 5 `build_*_graph` signatures or graph topologies (only composition roots change).
- ❌ Touching `agent_state_checkpoints` (sales_agent per-conversation table — sales-agent-expert §3 protected, orthogonal).
- ❌ Touching `copilot/` engine topology/registries/anchors (brand graphs only).
- ❌ Building ANY L2 surface (FlowCompiler/FlowDefinition/EP-19) — those are design-only this conversation.
- ❌ `docker exec` for lint/tests/migrations — native only (`${WS}/.venv/bin/...`).
- ❌ `git add .`/`-A` — pathspec only (single-hub shared index).

## Files in scope
- **CREATE:** `core/luana-core-flows/**` (pkg + provider + thread_id + tests)
- **MODIFY (AUTHORIZED engine):** root `pyproject.toml`, `core/tests/architecture/test_workspace_members_alphabetical_story8.py`
- **MODIFY (brand):** `vitalia/backend/pyproject.toml`, `comunify/backend/pyproject.toml`, the 5 composition roots (cron handlers / orchestrator services), `uv.lock`
- **DELETE:** `vitalia/.../copilot/workflows/wizard_checkpoint_config.py` + comunify inline factory bits
- **CREATE (migrations):** `vitalia/backend/alembic/versions/037_*.py`, `comunify/backend/alembic/versions/002_*.py`

## Files NEVER touch
- Any OTHER brand (`nicolify/`, `lupulo/`) — esqueletos, inherit at bootstrap.
- ANY FE (`*/frontend/`) — no UI surface in this story.
- `core/luana-core-copilot/src/` / `core/luana-core-sales-agent/src/` engine TOPOLOGY (only their pyproject is untouched; brand graphs wire to core-flows).
- `agent_state_checkpoints` schema (sales_agent).
- L2 surfaces (`core/luana-core-flows/domain/`, `core/luana-core-extension-sdk/`) — design-only.

## DoD (rule #37)
L1 NOT done until: all `04-validators` L1 gates GREEN in BOTH brands + `dod_live_verified: true` with `dod_evidence` proving the checkpoint PERSISTS in Postgres (psql) + survives backend restart (resume). At close: proposal `accepted → migrated` + `core/luana-core-flows/CHANGELOG.md` + `docs/core-modules/` entry.
