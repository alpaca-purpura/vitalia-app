# core

Engine SSoT for the Luana Platform.

**Purpose:** Contains all shared abstractions, AI agent modules, and cross-brand business logic.
This is the canonical source from which brand-specific workspaces (`nicolify`, `vitalia`, `comunify`, `lupulo`) consume.

**Scope (forward-looking):**
- `core/copilot/` — AI copilot module (Story 2 lifts `shared/` from AISALESHT)
- `core/sales-agent/` — AI sales agent module (Story 3)
- `core/shared/` — Shared abstractions: observability, billing, compliance, DDD patterns

**Current state (Story 1):** Placeholder — populated in Stories 2-9.

See [docs/architecture/luana-platform/00-overview.md](../docs/architecture/luana-platform/00-overview.md) for full monorepo topology.
