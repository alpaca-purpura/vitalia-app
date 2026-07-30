---
story_id: empleados-ia-auto-extension
brand: platform
arch_version: 1
schema_version: v4.1
architect_run_on: 2026-06-02
story_type: service-story / agentic (engine infra — NO UI, NO FE)
authorization: docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md (state: accepted, ratified Chris)
spike_source: docs/product/stories/empleados-ia-auto-extension/spike-durable-flows.md
adr: ADR-013-empleados-ia-auto-extension
model_knowledge_cutoff: 2026-01   # Opus 4.8; all post-cutoff facts verified live via WebSearch/WebFetch 2026-06-02
scope: two-layer (L1 build-now + L2 design-only)
---

# Contract: Motor de flujos durables brand-agnostic (`luana-core-flows`)

> **ENCUADRE.** Story platform de ENGINE INFRA, spike-derived. NO tiene `01-spec.md`, NO tiene mockups, NO toca FE. Los gates de UI (ADR-vitalia-003/004, playwright_visual_scope, FSD) NO aplican. El "spec" = `spike-durable-flows.md` + `00-research.md` + `ADR-013` + el drift map de la proposal. **Editar `core/` está AUTORIZADO** por la proposal `accepted` 2026-06-02 — los tickets engine la citan; NO se escala a `/pm-luana` por eso (la proposal YA es el lift gate, ratificado).

---

## 0. Context Summary

- **Story:** `empleados-ia-auto-extension` (platform). Artefacto: este `03-arch.md` cierra el ready-package L1 + diseño L2.
- **Architect run on:** 2026-06-02 (from `date -u +%Y-%m-%d`).
- **Modules touched:**
  - **Engine (NEW):** `core/luana-core-flows/` (provider durable + L2 design surface)
  - **Engine (MODIFIED, L2 design-only):** `core/luana-core-extension-sdk/` (EP-19 — design only, no build now)
  - **Engine (MODIFIED, pyproject):** add `langgraph-checkpoint-postgres` dep to consumer engine pkgs (copilot, sales-agent) + new `luana-core-flows` member in root `pyproject.toml`
  - **vitalia:** 3 graph compile sites + composition roots + delete factory mirror + checkpoint migration
  - **comunify:** 2 graph compile sites + composition roots + checkpoint migration
- **Surface → builder → auditor mapping** (`/dev-team` spawns from this):

  | Surface | Builder | Auditor |
  |---|---|---|
  | `core/luana-core-flows/src/**` (provider L1) | **`builder-agentic`** (Opus — agentic engine, R23) | **`auditor-agentic`** (Opus) |
  | `core/luana-core-flows/` pyproject + uv member + arch scaffold | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
  | `vitalia/.../{copilot,agentic}/workflows/` + composition roots wiring | **`builder-agentic`** (Opus) | **`auditor-agentic`** (Opus) |
  | `comunify/.../copilot/workflows/` + composition roots wiring | **`builder-agentic`** (Opus) | **`auditor-agentic`** (Opus) |
  | `vitalia/backend/alembic/versions/*` + `comunify/.../*` (checkpoint table migrations) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
  | `core/luana-core-extension-sdk/` EP-19 (**L2 design-only — NOT built**) | n/a (deferred-next-story) | n/a |

- **Skills consulted:**
  - `copilot-expert` — checkpointer wiring respects copilot resilience; anti-dup cardinal (no mirror of shared abstractions); production checkpointer ≠ MemorySaver.
  - `sales-agent-expert` — `§3 NO se toca` confirms `agent_state_checkpoints` schema is protected; durable-flows checkpointer is a NEW orthogonal surface, not touching the sales_agent per-conversation checkpoint table.
  - `backend-expert` — idempotent raw-SQL migration pattern; `AsyncPostgresSaver.setup()` integration; new core package scaffold (mirror `luana-core-idempotency`).
  - `hipaa-lite` (vitalia overlay) — `EncryptedSerializer` for PHI at-rest in vitalia checkpoints; dual-filter (tenant+clinic) baked into `thread_id`.
  - LangGraph canonical docs (durable-execution) — `EncryptedSerializer.from_pycryptodome_aes()` serde wiring, replay re-executes nodes → idempotency mandatory, `thread_id` = primary key, durability modes.
  - `.claude/rules/anti-duplication.md` — the factory brand-mirror MUST be lifted, never mirrored.
- **CONTEXT-BRIEF source:** none (engine spike — no context-builder run). Prior-art audit taken from spike §5 (NO-NEW-LAYER, self-run greps) + proposal drift map (greps 2026-06-02) + this architect's own greps (§ Prior art audit below).
- **capability YAML affected:** none. This is platform-level engine infra (`cap_target: null` per checkpoint). At L1 close → `proposal state: accepted → migrated` + `core/luana-core-flows/CHANGELOG.md` + `docs/core-modules/` entry. No brand cap YAML.
- **Architecture gates that must keep passing:** see § 12.

---

## Prior art audit (NO-NEW-LAYER rule)

### Source of evidence
- [x] Spike §5 (self-run greps, Path B) — `spike-durable-flows.md` lines 132-161
- [x] Proposal drift map (greps 2026-06-02) — `2026-06-02-durable-flows-engine.md` § 3
- [x] Architect re-validation greps (this run, 2026-06-02)

### Existing systems found (re-confirmed this run)

| System | Path | What it does today | Decision |
|---|---|---|---|
| **Outbox / event bus** | `core/luana-core-events/outbox/` | Coreografía evento-único (PENDING→DISPATCHED, idempotency_key + retry). NO multi-step state, NO replay del conjunto. | **REUSE** — flow's final node publishes to outbox; does NOT replace it. |
| **Idempotency** | `core/luana-core-idempotency/` | Dedup de una llamada (Redis, key + TTL). | **REUSE** — wrap side-effect nodes → replay-safe (L2; L1 documents the seam). |
| **LangGraph supervisor** | `core/luana-core-copilot` + `core/luana-core-sales-agent` (`langgraph` resolved 1.2.0). `AsyncPostgresSaver` = **0 imports** (only "production target" comments). | Reasoning/routing. NO durable checkpointer wired. | **EXTEND** — add `checkpointer=AsyncPostgresSaver` UNDER the same framework. NOT replaced. |
| **Observability recorder** | `core/luana-core-observability/recording/` + `copilot_trace_event` | Trazas event-sourced + cost + PII sanitization. | **REUSE** — flow nodes emit to `copilot_trace_event` (L2; L1 keeps existing recorders intact). |
| **Extension SDK** | `core/luana-core-extension-sdk/extension_points.py` (EP-1..18; `_EP_IDS = range(1,19)`) | Brand extension registry. | **EXTEND (L2 design-only)** — EP-19 `durable_flow_register` (NEW EP, not widen EP-4). |
| **Compliance gates** | `core/luana-core-compliance/` | Blocks PHI on unencrypted channel. | **REUSE** in L2 `compliance_gate`. |
| **Vitalia factory mirror** | `vitalia/.../copilot/workflows/wizard_checkpoint_config.py::build_production_checkpointer` (+ comunify inline equivalents) | Brand-local `AsyncPostgresSaver` factory w/ deferred import + `RuntimeError`. **NEVER invoked in prod code** (grep: 0 callers outside tests). | **REPLACE → DELETE** — lift to `core/luana-core-flows`; brands import from core. This is the cross-brand mirror `anti-duplication.md` prohibits. |

### Decision per system
- **EXTEND (default):** LangGraph (add durable checkpointer below supervisor), Extension SDK (EP-19 design only), reuse outbox/idempotency/observability/compliance.
- **REPLACE (justified):** the brand `build_production_checkpointer` factory mirror (+ comunify equivalents) → deleted, replaced by `core/luana-core-flows.make_durable_checkpointer`. Justification: it's a cross-brand mirror (vitalia + comunify) of an identical concept → `anti-duplication.md` mandates lift-to-core. It was never wired to prod (latent dead code), so REPLACE has zero runtime regression on the construction site itself.
- **NEW (acotado, justificado):** `luana-core-flows.checkpointer` (L1 provider) + `FlowDefinition`/`FlowCompiler`/EP-19 (L2). No existing system is a durable-flow compositor (outbox = single-event choreography; `agent_state_checkpoints` = sales_agent per-conversation custom state, sales-agent-expert §3 protected). Lives in `core/` from first commit (no per-brand mirror). Authorized by the accepted proposal.
- **Cross-brand mirror check:** the factory exists in vitalia AND comunify → textbook lift-to-core trigger. Resolved by this story (the whole point).

### Greps re-run (2026-06-02, this architect)
```
grep AsyncPostgresSaver core/luana-core-{copilot,sales-agent}/src   → 0 (only comments)
grep build_production_checkpointer  ... | grep -v def | grep -v /tests/  → 0 prod callers (dead swap surface)
uv.lock: langgraph=1.2.0, langgraph-checkpoint=4.1.0, langgraph-checkpoint-postgres=ABSENT
ls -d core/luana-core-flows  → does not exist
core/luana-core-extension-sdk: _EP_IDS = range(1,19) → EP-19 needs range(1,20) bump (L2)
```

---

## L1 design — provider durable + wiring + migrations + version strategy

> **Owner:** `builder-agentic` (Opus) for the provider + graph wiring; `builder-backend` (Sonnet) for pyproject/uv + migrations. **Buildable THIS conversation.**

### L1.0 — Home decision: NEW package `core/luana-core-flows` (vs module in `luana-core-platform`)

**Decision: NEW dedicated package `core/luana-core-flows`.** Rationale:
1. **L2 needs it as a home anyway** — `FlowDefinition` + `FlowCompiler` + the flow registry are a cohesive bounded context that does NOT belong in `luana-core-platform` (which is the cross-module ports/links/locale hub, NOT an orchestration runtime). Putting the checkpointer in platform now would force a move when L2 lands.
2. **Dependency direction.** `luana-core-flows` will depend on `langgraph-checkpoint-postgres` (a heavy transitive: psycopg, psycopg-pool, orjson). Adding that to `luana-core-platform` (consumed by ~every package) pollutes the dependency graph of packages that have nothing to do with durable flows. A dedicated package isolates the blast radius.
3. **Cost of a new package is low + one-time** — mirror `luana-core-idempotency` scaffold (pyproject + `src/luana_core_flows/` + `tests/` + 1 root `pyproject.toml` member line + `uv sync` + alphabetical-order arch test bump). The arch fitness scaffold is mechanical.
4. **Semver/changelog isolation** — `luana-core-flows` versions independently; the proposal's `semver_bump: minor` applies cleanly to a fresh package at `0.1.0`.

Trade-off accepted: +1 workspace member (28 total), which trips `test_python_member_count_is_27` → must bump to 28 (documented allowlist ratchet, § 12).

### L1.1 — Package scaffold (`builder-backend`)

```
core/luana-core-flows/
├── pyproject.toml                # name=luana-core-flows, v0.1.0, deps: langgraph-checkpoint-postgres + langgraph + pydantic + structlog + luana-core-platform
├── src/luana_core_flows/
│   ├── __init__.py               # public API exports
│   ├── checkpointer/
│   │   ├── __init__.py
│   │   ├── provider.py           # make_durable_checkpointer(...) + CheckpointerProtocol
│   │   └── thread_id.py          # build_flow_thread_id(...) tenant-scoped (+ dual-filter helper)
│   └── domain/                   # (L2 — FlowDefinition lands here next story; L1 leaves dir absent or empty placeholder)
└── tests/
    ├── conftest.py
    └── checkpointer/
        ├── test_provider.py      # signature + serde wiring + table_prefix + setup() idempotency contract
        └── test_thread_id.py     # tenant-scoped composition + collision-safety
```

`pyproject.toml` (mirror `luana-core-idempotency`):
```toml
[project]
name = "luana-core-flows"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "langgraph",                       # floor unpinned — uv resolves 1.2.0 already locked (see L1.5)
    "langgraph-checkpoint-postgres>=3.1.0,<4",   # AsyncPostgresSaver + setup(); compat w/ langgraph-checkpoint>=4.1.0 (already locked)
    "pydantic>=2.0",
    "structlog>=24.0",
    "luana-core-platform",             # for TenantLocale VO / future ports (L2)
]
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_flows"]
```

### L1.2 — `make_durable_checkpointer` provider (`builder-agentic`)

`core/luana-core-flows/src/luana_core_flows/checkpointer/provider.py`:

```python
# Public contract (signature — builder implements body, async-first, structlog only)
from typing import Protocol
from langgraph.checkpoint.base import BaseCheckpointSaver

class CheckpointerProtocol(Protocol):
    """Structural protocol — LangGraph validates the real interface at compile()."""
    ...

async def make_durable_checkpointer(
    *,
    postgres_dsn: str,
    encryption_key: str | None = None,   # if set → EncryptedSerializer.from_pycryptodome_aes (PHI/HIPAA)
    table_prefix: str = "luana_flows_",
    run_setup: bool = True,              # call .setup() once (idempotent — CREATE TABLE IF NOT EXISTS internally)
) -> BaseCheckpointSaver:
    """Build the production durable checkpointer (AsyncPostgresSaver).

    - Constructs AsyncPostgresSaver from postgres_dsn (async-capable: psycopg).
    - If encryption_key provided: wires serde=EncryptedSerializer.from_pycryptodome_aes()
      reading the AES key (vitalia PHI checkpoints at-rest encryption).
    - run_setup=True → awaits .setup() (idempotent table creation + migrations).
    - table_prefix parameterizes per-brand checkpoint table names (DI / BrandConfig).
    NEVER returns MemorySaver — that is tutorial-only. Tests inject InMemorySaver directly
    at the composition root, NOT via this factory.
    """
    ...
```

**Wiring notes the builder MUST honor (from LangGraph canonical docs, verified 2026-06-02):**
- `from_conn_string(...)` is an **async context manager** in `aio` — the provider must NOT leak a context-managed connection that closes prematurely. Use the long-lived constructor path (pass a pooled psycopg connection/pool with `autocommit=True` + `row_factory=dict_row`) OR enter the context for the app lifespan. **Open question O-1** (§ 16) — builder picks the lifespan-safe pattern and documents it. The current vitalia mirror used `from_conn_string` returning a saver directly without `autocommit/row_factory` — a latent bug the lift fixes.
- `encryption_key` path: `serde=EncryptedSerializer.from_pycryptodome_aes()` (reads `LANGGRAPH_AES_KEY` env). Wired via the `serde=` constructor param. Requires `pycryptodome` — add to deps if the builder confirms it's not transitive.
- `.setup()` is idempotent (creates tables IF NOT EXISTS + runs internal migrations). Call once at lifespan startup, NOT per-invocation.

### L1.3 — `build_flow_thread_id` helper (`builder-agentic`)

`core/luana-core-flows/src/luana_core_flows/checkpointer/thread_id.py`:

```python
def build_flow_thread_id(*, flow_id: str, tenant_id: str, instance_id: str) -> str:
    """Tenant-scoped thread_id = primary key of the durable thread.
    Format: f"{flow_id}:{tenant_id}:{instance_id}" (dual-filter HIPAA via tenant segment).
    """
    ...

def build_phi_flow_thread_id(*, flow_id: str, tenant_id: str, clinic_id: str, instance_id: str) -> str:
    """vitalia PHI variant — embeds clinic_id (dual-filter tenant+clinic per hipaa-lite.md)."""
    ...
```

This **generalizes** the existing per-site `thread_id` rules (today fragmented: `vitalia.wizard.{tenant}.{draft}` in wizard, `{tenant}:{treatment}` in treatment cron, `{tenant}:{subscriber}` in comunify). L1 provides the canonical helper; the 5 sites adopt it (preserving their existing collision semantics — the builder maps each site's current key into the helper's `flow_id`/`instance_id` slots; no behavior change to thread isolation).

### L1.4 — Wire the 5 graphs + delete the mirror (`builder-agentic`)

The 5 graphs **already accept `checkpointer` as an injected param** (clean DI — confirmed via grep). L1 does NOT touch the `build_*_graph` signatures or topology. It changes WHERE the production checkpointer is constructed:

| Site | Compile site (unchanged) | Composition root to rewire |
|---|---|---|
| vitalia wizard | `wizard_onboarding_graph.py:323` | `copilot/application/services/wizard_orchestrator_service.py` + `copilot/workflows/cron_handler.py` |
| vitalia treatment | `treatment_followup_workflow.py:753` | `copilot/workflows/cron_handler.py` |
| vitalia lucas | `lucas_daily_analysis_graph.py:503` | `agentic/lucas/application/services/lucas_orchestrator_service.py` (replace inline `MemorySaver()` placeholder) |
| comunify community | `community_engagement_workflow.py:593` | `comunify/.../copilot/workflows/cron_handler.py` |
| comunify cohort | `cohort_enrollment_workflow.py:913` | `comunify/.../copilot/workflows/cron_handler.py` |

**Actions:**
1. At each brand composition root (cron job / FastAPI lifespan / orchestrator constructor), construct the production checkpointer via `await make_durable_checkpointer(postgres_dsn=..., encryption_key=<vitalia: LANGGRAPH_AES_KEY; comunify: None>, table_prefix="<brand>_flows_")`. Call `.setup()` once at startup.
2. **DELETE** `vitalia/.../copilot/workflows/wizard_checkpoint_config.py::build_production_checkpointer` + `WIZARD_CHECKPOINT_TABLE_PREFIX` (and `CheckpointerProtocol` if nothing else imports it; otherwise re-export from core). DELETE comunify inline equivalents.
3. Replace the `lucas_orchestrator_service.py` inline `MemorySaver()` "or AsyncPostgresSaver in prod" placeholder with the core provider at the actual cron composition root (tests still inject `InMemorySaver` directly — unchanged).
4. Keep tests injecting `InMemorySaver`/`MemorySaver` directly at construction (the provider is prod-only). **NO test mocks the deleted factory** — the factory was never invoked in prod, so this is a dead-code delete, not a default flip (see § 9.5).

**Anti-dup invariant:** after L1, ZERO brand-local checkpointer factory exists. Both brands import `make_durable_checkpointer` from `luana_core_flows`. `auditor-downstream-regression` Cross-brand mirror scan must find no `build_production_checkpointer` basename in any brand.

### L1.5 — Version strategy (MATERIAL refinement to spike/proposal)

**The repo TODAY already resolves `langgraph 1.2.0` + `langgraph-checkpoint 4.1.0`** (verified in `uv.lock`, 2026-06-02). The engine `langgraph>=0.2` pins are FLOORS, not ceilings — uv resolved latest.

Consequence: **L1 requires ZERO version bump.** `langgraph-checkpoint-postgres 3.1.0` requires `langgraph-checkpoint>=4.1.0,<5.0.0` — already satisfied by the locked 4.1.0. Adding the dep resolves cleanly against the existing lock.

- Do NOT change the `langgraph>=0.2` floor in copilot/sales-agent/brand-studio (no need; touching it = needless downstream churn).
- Add `langgraph-checkpoint-postgres>=3.1.0,<4` to `luana-core-flows` only. The engine consumer pkgs (copilot, sales-agent) get it transitively once their brand graphs import the core provider — **OR** add it explicitly to the brand backend pyproject (vitalia/comunify) since the wiring lives brand-side. **Decision: add `luana-core-flows` as a dep of the brand backends** (`vitalia/backend/pyproject.toml`, `comunify/backend/pyproject.toml`) — the brands consume the provider, so the dep belongs at the brand boundary, not pushed into engine pkgs that don't use it. (copilot/sales-agent engine pkgs do NOT need the dep for L1; they don't construct checkpointers.)
- HITL v0.4 / `DeltaChannel` are ALREADY available (langgraph 1.2.0) — but they are L2 nice-to-haves, not consumed in L1. No action.
- After `uv sync`: `langgraph-checkpoint-postgres` + transitives (psycopg, psycopg-pool, orjson, pycryptodome if needed) enter `uv.lock`. Commit the lock.

### L1.6 — Migrations (checkpoint tables per brand) (`builder-backend`)

`AsyncPostgresSaver.setup()` creates its own tables (idempotent). Two valid approaches; **decision: hybrid**:
- **Primary:** rely on `.setup()` at app lifespan startup (idempotent, internal `IF NOT EXISTS` + version migration). This is the LangGraph-canonical path and avoids hand-maintaining the checkpoint schema (which LangGraph owns and may migrate across versions).
- **Belt-and-suspenders (declarative existence + ownership in alembic history):** add ONE idempotent alembic migration per brand that documents the checkpoint table namespace + ensures the schema/extension prerequisites exist, WITHOUT redefining LangGraph's internal columns. Pattern:

```python
# vitalia/backend/alembic/versions/037_vitalia_durable_flow_checkpoints.py (next number after 036)
def upgrade():
    # LangGraph's AsyncPostgresSaver.setup() owns the checkpoint table DDL.
    # This migration only ensures prerequisites + records the namespace in alembic history.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")  # if any column-level needs; harmless if unused
    # NO CREATE TABLE for checkpoint tables — setup() owns them (avoids schema drift w/ LangGraph internals).
    # Comment documents table_prefix='vitalia_flows_' so ops/audit know the namespace.
```

- comunify: `comunify/backend/alembic/versions/002_comunify_durable_flow_checkpoints.py` (next after 001).
- **NEVER** `op.create_table()` / `sa.Enum(create_type=True)`. All raw SQL idempotent (`IF NOT EXISTS`).
- **Open question O-2** (§ 16): confirm whether the brand wants LangGraph-owned tables (`.setup()`) vs hand-declared. Recommendation above (LangGraph-owned + thin alembic prereq migration). Builder confirms with prod-clone test (§ 9 command).

---

## L2 design — `FlowCompiler` / `FlowDefinition` / EP-19 (DESIGN ONLY — NOT built this conversation)

> **`phase: L2-design-only`, `build_status: deferred-next-story`.** The auditor + dev do NOT build these tickets now. This section is the design seed for the NEXT `/architect` ready-package. Based on spike §4.

### L2.1 — `FlowDefinition` (Pydantic declarative, `core/luana-core-flows/domain/`)

Per spike §4.1 — declarative envelope a domain-owner (empleado-IA) uses to declare an N-node durable flow over EXISTING actions:

```
FlowDefinition (Pydantic v2, ConfigDict, brand-agnostic)
├── flow_id: str                  # natural key (slug)
├── version: int                  # bump → new def; in-flight instances keep their compiled version
├── owner_agent: str              # owning employee (ADR-013 D4 ownership)
├── tenant_scoped: Literal[True]  # ALWAYS — every instance carries tenant_id in thread_id
├── trigger: FlowTrigger          # kind: event|schedule|manual|signal; event_name → subscribes luana-core-events outbox
├── nodes: list[FlowNode]         # the DAG
│     ├── node_id, action_ref (→ Plano-2 registered action), inputs (state→action JSONPath map)
│     ├── on_success / on_failure (node_id | retry | END)
│     └── idempotency_key_template: str  # MANDATORY if action has side-effect (replay-safe via luana-core-idempotency)
├── waits: list[Wait]             # step.sleep equivalent → interrupt + resume by schedule/signal
├── human_gate: HumanGate | None  # interrupt() for T3/approval (ADR-013 separation of powers)
└── guardrails: FlowGuardrails    # compliance_gate (PHI → ComplianceService), forbidden_actions
```

### L2.2 — `FlowCompiler.compile(flow_def) -> CompiledGraph`

Per spike §4.2:
1. Build a `StateGraph`: each `FlowNode` → async node invoking `action_ref` (resolved against the owner-domain action registry).
2. Wrap side-effect nodes with `luana-core-idempotency` guard (key = rendered `idempotency_key_template`) → replay-safe.
3. `compile(checkpointer=make_durable_checkpointer(...))` (consumes L1 provider). `thread_id = build_flow_thread_id(flow_id, tenant_id, instance_id)`.
4. Final node publishes result to `luana-core-events` outbox (choreography — no agent calls another concretely; ADR-013 D3/D4).
5. State (TypedDict) MUST include `tenant_id: str` + an `iterations: int` max-iter guard.

### L2.3 — EP-19 `durable_flow_register` (Extension SDK)

- `core/luana-core-extension-sdk/extension_points.py`: bump `_EP_IDS = tuple(f"EP-{i}" for i in range(1, 20))`, add `EP-19` to `_BACKLOG_EPS` (signature-only v0.1.0), add `durable_flow_register(self, *, flow: FlowDefinition, mode="append")` + `durable_flows_for(ctx)` dispatch (filters by `ctx.brand_slug`).
- **Decision: NEW EP-19, not widen EP-4.** EP-4 (`copilot_workflow_register`) is coupled to copilot's frozen WorkflowRegistry byte-stable adapter; durable flows are transversal to ALL employees (copilot, sales_agent, lucas, future). New EP keeps the boundary clean (spike §8 Q2 recommendation, confirmed).
- Brands mount `FlowDefinition`s via `{brand}/.../extensions.py::register_all(registry)`.
- **NOT built now** — design seed only.

### L2.4 — Observability (L2)
Each flow node emits to `copilot_trace_event` (shared recorder, `luana-core-observability`) — no new pane. Stream `updates` for live UI ("Auto-liberación de cupos: paso 2/4"). PII via `sanitize_payload` before any trace write.

---

## Cross-cutting concerns

- **HIPAA (vitalia):** `encryption_key` → `EncryptedSerializer.from_pycryptodome_aes()` (PHI checkpoints at-rest). `thread_id` embeds `tenant_id` (+ `clinic_id` for PHI flows) = dual-filter. `sanitize_payload` before any trace. comunify passes `encryption_key=None` (no PHI). Per `vitalia/.claude/rules/hipaa-lite.md`.
- **Tenant isolation:** every durable thread keyed by tenant-scoped `thread_id`. No cross-tenant checkpoint read possible (thread_id is the primary key). `table_prefix` is per-brand, not per-tenant — isolation is at the thread_id row level + the brand owns its own Postgres DB.
- **Anti-dup (mirror-delete):** the single most important cross-cutting outcome — ZERO brand checkpointer factory after L1. Both brands import from `luana_core_flows`. `anti-duplication.md` cardinal satisfied.
- **Currency / locale:** n/a (no monetary/datetime DTOs in the provider; L2 flows that touch money defer to existing brand services).
- **Spanish neutro:** n/a (engine infra, no user-facing strings; L2 UI deferred).
- **Native-first:** all lint/tests/migrations run native (`${WS}/.venv/bin/...`), never `docker exec`.
- **structlog only** in all provider code.

---

## Integration design (CONN — anti-orphan)

The L1 provider is NOT an island:
- **Consumed:** the 5 brand graph composition roots (vitalia ×3, comunify ×2) import + call `make_durable_checkpointer`. ≥5 real consumers from day one.
- **On the map:** lives in `core/luana-core-flows` (a real engine package, in `docs/core-modules/`). `cap_target: null` (platform infra, not a brand cap).
- **Navigable/reachable:** reachable via brand composition roots (cron jobs + FastAPI lifespan + orchestrator constructors) — concrete call path documented in L1.4 table.
- **Notarized/registered:** registered as a uv workspace member (root `pyproject.toml`) + consumed via Python import (`from luana_core_flows.checkpointer import make_durable_checkpointer`). L2 additionally registers via EP-19. The provider is wired at the composition root, NOT a dangling module.

Reachability path (L1): `cron job / FastAPI lifespan (brand)` → `make_durable_checkpointer (core)` → `graph.compile(checkpointer=...)` → durable Postgres thread keyed by `build_flow_thread_id`.

---

## Downstream regression plan (R3 / auditor-downstream-regression)

Engine edit (`core/luana-core-flows` NEW + brand wiring) → MANDATORY downstream regression in BOTH affected brands BEFORE close:

1. **Engine edit detection:** `auditor-downstream-regression` must find proposal `2026-06-02-durable-flows-engine.md` in `state: accepted` → PASS (it is). Cite it in every engine ticket.
2. **Cross-brand mirror scan:** must find NO `wizard_checkpoint_config.py`/`build_production_checkpointer` basename in any brand after L1 (deleted). PASS condition = mirror gone.
3. **Downstream test run (per brand):**
   ```bash
   WS=$(git rev-parse --show-toplevel)
   # new package
   cd ${WS}/core/luana-core-flows && ${WS}/.venv/bin/pytest -v
   # vitalia agentic + arch
   cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/unit/modules/vitalia/copilot/workflows/ tests/unit/modules/vitalia/agentic/lucas/ tests/architecture/ -x -q
   # comunify agentic + arch
   cd ${WS}/comunify/backend && ${WS}/.venv/bin/pytest tests/modules/comunify/copilot/ tests/architecture/ -x -q
   # workspace integrity (member count bumped 27→28)
   cd ${WS} && ${WS}/.venv/bin/pytest core/tests/architecture/test_workspace_members_alphabetical_story8.py -x -q
   ```
4. Both brands GREEN with `langgraph-checkpoint-postgres` installed BEFORE closing (proposal § 6 risk row).

---

## Live-verify plan (DoD rule #37)

> The engine provider is **técnica** nature; the live-verify is **funcional** over a real durable graph (the only honest way to prove the checkpoint PERSISTS to Postgres, not MemorySaver, and survives a resume).

**Scenario (vitalia, `make dev-app-vitalia` → dev-app.vitalialat.com):** exercise the **wizard_onboarding** durable graph (lowest-risk, no PHI write in the happy path, already shipped). Concretely:
1. Start a wizard onboarding session (authenticated `dr.demo@vitalialat.com`) that advances ≥2 supervisor steps → triggers ≥1 checkpoint write.
2. **Observe persistence in Postgres** (the load-bearing assertion):
   ```bash
   docker exec luana-dev-vitalia_backend_dev-1 bash -c \
     "psql \$DATABASE_URL -c \"SELECT thread_id, checkpoint_id, metadata->>'step' FROM checkpoints WHERE thread_id LIKE 'vitalia.wizard.%' ORDER BY checkpoint_id DESC LIMIT 5;\""
   ```
   (table name = whatever `AsyncPostgresSaver.setup()` created — `checkpoints` / `checkpoint_blobs` / `checkpoint_writes`; builder confirms exact names post-setup.)
3. **Resume test:** restart the backend container (`docker compose ... restart vitalia_backend_dev`), re-invoke the SAME wizard thread → confirm it resumes from the persisted checkpoint (state survives process restart — impossible with MemorySaver). Observe the wizard continuing from its prior step, not restarting.
4. Read backend logs (no traceback, no `RuntimeError: AsyncPostgresSaver not available`).
5. **Encryption assertion (PHI):** confirm the checkpoint payload column is ciphertext when `encryption_key` set (not plaintext PHI) for a PHI-bearing flow (treatment_followup if exercised; otherwise document that wizard onboarding is non-PHI and the encryption path is unit-tested + the PHI flow's live-verify defers to its own derived story).

`dod_evidence` (record in `07-merge.md` § Verificación live + checkpoint):
```yaml
dod_live_verified: true
dod_env: "make dev-app-vitalia → dev-app.vitalialat.com (Chrome DevTools MCP + psql)"
dod_evidence:
  - action: "Advance wizard_onboarding ≥2 steps (authenticated dr.demo@vitalialat.com)"
    observed: "checkpoints rows present in Postgres for thread_id vitalia.wizard.* (NOT MemorySaver)"
    backend_log: "no traceback, no RuntimeError; AsyncPostgresSaver.setup() ran once at startup"
  - action: "Restart backend container, re-invoke same wizard thread"
    observed: "wizard resumes from persisted checkpoint (state survived process restart)"
verified_at: 2026-06-02
```

**Open question O-3** (§ 16): if exercising the wizard in dev-app proves heavy for a single session, the fallback live-verify is a scripted invocation of the wizard graph against the dev Postgres directly (still a real durable thread + real psql observation + real resume), documented as such. The bar (real write + persisted effect + resume) holds either way.

---

## Architecture fitness impact

| Gate | File | Impact |
|---|---|---|
| Workspace member count | `core/tests/architecture/test_workspace_members_alphabetical_story8.py` | `_EXPECTED_COUNT 27 → 28` + alphabetical insert of `luana-core-flows` (between `-extension-sdk`/`-extraction`... actually after `-extraction`? — `flows` > `extraction` > `extension-sdk`; builder inserts in correct alpha position). **Documented ratchet bump.** |
| Workspace versions uniform | `core/tests/architecture/test_workspace_versions_uniform_at_v0_1_0.py` | new pkg at `0.1.0` → keeps gate green (uniform v0.1.0). |
| Extension SDK zero workspace deps | `core/tests/architecture/test_extension_sdk_zero_workspace_deps.py` | L1 does NOT touch extension-sdk (EP-19 is L2). Stays green. |
| Brand arch fitness (vitalia/comunify) | `{brand}/backend/tests/architecture/` | DDD boundaries: provider imported from `core/` (allowed). No new cross-module import. Mirror-delete shrinks any allowlist (never grows). |
| Anti-dup mirror scan (auditor) | auditor Cat 12 | must confirm 0 brand checkpointer factories post-L1. |

Allowlists shrink only (mirror-delete removes entries). Member-count is a NEW package addition — the count bump is the standard "+1 core package" ratchet, justified in commit body.

---

## Tests audit (default flip)

- [x] **No aplica — 03-arch.md no flipea defaults side-effect.** L1 deletes a never-invoked factory (`build_production_checkpointer`, 0 prod callers) and wires the real provider at composition roots that previously ran on `MemorySaver`/placeholder. This is NOT a feature-flag default flip (no `USE_*` flag toggled). It IS a behavior change (MemorySaver → durable Postgres in prod), so the **live-verify (§ Live-verify) + downstream regression (§ Downstream)** cover it. Tests inject `InMemorySaver` directly (unchanged) — no test mocks the deleted factory, so no test migration needed. The builder confirms via grep `grep -rn build_production_checkpointer {vitalia,comunify}/backend/tests` → expected 0 (factory was never test-mocked).

---

## File structure (NEW vs MODIFIED)

```
core/luana-core-flows/                                              # NEW package
├── pyproject.toml                                                  # NEW
├── src/luana_core_flows/{__init__,checkpointer/{__init__,provider,thread_id}}.py  # NEW
└── tests/{conftest,checkpointer/{test_provider,test_thread_id}}.py # NEW
pyproject.toml (root)                                               # MODIFIED — +luana-core-flows member + [tool.uv.sources]
core/tests/architecture/test_workspace_members_alphabetical_story8.py  # MODIFIED — count 27→28
vitalia/backend/pyproject.toml                                     # MODIFIED — +luana-core-flows dep
vitalia/backend/src/modules/vitalia/copilot/workflows/wizard_checkpoint_config.py  # DELETED (mirror)
vitalia/backend/src/modules/vitalia/copilot/application/services/wizard_orchestrator_service.py  # MODIFIED — provider wiring
vitalia/backend/src/modules/vitalia/copilot/workflows/cron_handler.py  # MODIFIED — provider wiring
vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/lucas_orchestrator_service.py  # MODIFIED — replace inline MemorySaver
vitalia/backend/alembic/versions/037_vitalia_durable_flow_checkpoints.py  # NEW (thin prereq migration)
comunify/backend/pyproject.toml                                    # MODIFIED — +luana-core-flows dep
comunify/backend/src/modules/comunify/copilot/workflows/{cron_handler,community_engagement_workflow,cohort_enrollment_workflow}.py  # MODIFIED — provider wiring + delete inline factory bits
comunify/backend/alembic/versions/002_comunify_durable_flow_checkpoints.py  # NEW (thin prereq migration)
# ── L2 (DESIGN ONLY — NOT created this conversation) ──
core/luana-core-flows/src/luana_core_flows/domain/{flow_definition,flow_compiler}.py  # L2 deferred
core/luana-core-extension-sdk/src/.../extension_points.py          # L2 deferred (EP-19)
```

---

## Research notes (date-aware — accessed 2026-06-02; Opus 4.8 cutoff Jan 2026, post-cutoff verified live)

- **LangGraph durable execution** — https://docs.langchain.com/oss/python/langgraph/durable-execution · accessed 2026-06-02. `EncryptedSerializer.from_pycryptodome_aes()` wires via `serde=` param (reads `LANGGRAPH_AES_KEY`); `from_conn_string` + `.setup()` (idempotent schema init); durability modes exit/async/sync; **replay re-executes nodes after the checkpoint (LLM calls/API/interrupts always re-triggered → side-effects MUST be idempotent)**; `thread_id` = primary key for resume. Post-cutoff (v0.4/1.x): verified live.
- **langgraph-checkpoint-postgres on PyPI** — https://pypi.org/pypi/langgraph-checkpoint-postgres/json · accessed 2026-06-02. Latest **3.1.0** (2026-05-12). `requires_dist`: `langgraph-checkpoint<5.0.0,>=4.1.0`, `orjson>=3.11.5`, `psycopg-pool>=3.2.0`, `psycopg>=3.2.0`. **Does NOT depend on langgraph core directly** — only on `langgraph-checkpoint>=4.1.0`. Takeaway: compatibility question is about `langgraph-checkpoint`, not `langgraph` core.
- **langgraph on PyPI** — https://pypi.org/pypi/langgraph/json · accessed 2026-06-02. Latest **1.2.2**; `requires_dist` includes `langgraph-checkpoint<5.0.0,>=4.1.0`. Takeaway: latest langgraph already brings `langgraph-checkpoint>=4.1.0` — satisfies the postgres saver.
- **uv.lock (repo, this run)** — `langgraph 1.2.0` + `langgraph-checkpoint 4.1.0` ALREADY resolved (the `>=0.2` floor resolved to latest); `langgraph-checkpoint-postgres` ABSENT. **MATERIAL refinement to spike §2.3/proposal § 3:** L1 needs ZERO version bump — adding `langgraph-checkpoint-postgres>=3.1.0` resolves cleanly against the locked 1.2.0/4.1.0 stack. HITL v0.4/DeltaChannel are already available (1.2.0), unused in L1.
- **Knowledge cutoff disclosure:** Opus 4.8 cutoff Jan 2026; langgraph 1.2.x + langgraph-checkpoint-postgres 3.1.0 (May 2026) are post-cutoff — all version facts above sourced live from PyPI JSON + the repo's own uv.lock on 2026-06-02.
- **Internal:** spike-durable-flows.md (recommendation + §4 EP contract + §5 NO-NEW-LAYER + §6 risks), proposal 2026-06-02-durable-flows-engine.md (drift map + L1/L2 scope), ADR-013 (D2 flujo durable 1ª clase), anti-duplication.md (mirror lift mandate).

---

## Open questions for PM

- **O-1 (builder-resolvable):** `AsyncPostgresSaver.from_conn_string` is an async context manager in `aio`. The builder must pick the lifespan-safe construction (pooled psycopg connection with `autocommit=True` + `row_factory=dict_row`, or enter the CM for the app lifespan) so the connection doesn't close prematurely. The deleted vitalia mirror used `from_conn_string` returning a saver without those flags — a latent bug the lift fixes. Builder documents the chosen pattern; NOT blocking.
- **O-2 (builder-resolvable, confirm with prod-clone):** checkpoint table ownership — recommendation is LangGraph-owned (`.setup()`) + thin alembic prereq migration (no `CREATE TABLE` for checkpoint internals, avoiding schema drift with LangGraph). Builder confirms via prod-clone test.
- **O-3 (builder-resolvable):** live-verify scenario — primary is wizard_onboarding in dev-app; fallback is a scripted real durable invocation against dev Postgres (still real write + persisted effect + resume). The bar holds either way.
- **O-4 (Chris-decision, NON-blocking for L1):** EP-19 vs widen EP-4 — this arch recommends NEW EP-19 (spike §8 Q2). L2 design-only; final ratification at the L2 ready-package. No L1 impact.
- **O-5 (Chris-decision, NON-blocking):** first L2 durable flow = traza B vitalia (auto-liberación de cupos) per outcome story #2. Deferred to L2 story.
