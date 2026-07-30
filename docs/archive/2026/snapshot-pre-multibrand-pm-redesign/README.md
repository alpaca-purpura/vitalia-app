# Legacy SSoT snapshot — 2026-05-09

This directory is a **read-only snapshot** of `docs/product/` taken from `ap_sales_agent/` (AISALESHT single-brand Nicolify codebase) on **2026-05-09**, the date the multi-brand `luana-platform` migration was initiated.

## Status: STALE since 2026-05-15

Since the snapshot was taken, the following work was completed directly in `luana-platform/` **without updating this SSoT**:

- **Story 11 — Vitalia** (medical/dental/wellness LATAM): full backend + frontend + agentic + deploy + docs. Commits in `git log --grep="story-11"`.
- **Story 12 — Comunify** (creator economy): full BE + FE + agentic + payment adapters + voice cloning + KB pack + workflows + guardrails + e2e + audit fix iter 1+2. Plus WIP `T-extensions-1` / `T-workflows-1` / `T-voice-1..4` / `T-kb-1` recovered separately. Commits in `git log --grep="comunify"`.

## Use

- **Read-only reference** for institutional context: what stories existed pre-migration, what capabilities were mapped, what gaps were known.
- **Do NOT edit** files here as if they were live SSoT.
- **Do NOT rely** on capability statuses, ticket states, or backlog ordering — they are frozen at 2026-05-09.

## Going forward

The live `docs/product/` SSoT lives at `docs/product/` (parent of this dir). To resume `/pm` workflow:

1. Regenerate `docs/product/BACKLOG.md` via `scripts/generate_backlog.py` (when stories are reconciled).
2. Reconcile capability statuses for Stories 11-12 (Vitalia + Comunify) via `scripts/reconcile_capabilities.py`.
3. Create fresh capabilities under `docs/product/capabilities/{vitalia,comunify,lupulo}/` as the multi-brand verticals get their first capabilities promoted.

## Contents (snapshot)

- `capabilities/` — 95 files / 18 module dirs (single-brand Nicolify perspective)
- `stories/` — 151 files / ~30 story dirs
- `outcomes/` — 14 files (PI-12 era outcomes + a few cross-brand outcomes)
- `modules/` — 18 files (one per Nicolify backend module)
- `ideas/` — 2 files
- `opportunities/` — 6 files
- `story-map/` — 1 file
- `BACKLOG.md`, `BACKLOG-TLDR.md`, `INDEX.md`, `glossary.md`, `roadmap.md`, `vision.md` (auto-gen + manual)

## Provenance

- Migrated from: `ap_sales_agent/docs/product/` (taken from old laptop copy at `/home/chalreme/Documentos/ap_sales_agent/`)
- Migration date: 2026-05-15
- Migration owner: Chris (alpacapurpura@) + Claude Opus 4.7
- Reason for snapshot vs live: `ap_sales_agent` was the SDD framework's working SSoT at the time the multi-brand carve-out began. The migration to `luana-platform` was in progress when the host laptop was reformatted on 2026-05-14/15. This snapshot preserves the institutional state at the migration's halt point.
