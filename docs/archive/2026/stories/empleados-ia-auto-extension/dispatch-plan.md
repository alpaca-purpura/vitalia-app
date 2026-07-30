---
story_id: empleados-ia-auto-extension
brand: platform
autonomous_mode: false   # architect proposes; Chris ratifies. Engine + cross-brand + HIPAA = stake-asimétrico → NOT autonomous.
authorization: docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md (accepted)
scope: two-layer (L1 build / L2 design-only)
---

# Dispatch plan — Durable flows engine L1

## autonomous_mode: false (rationale)
This story edits `core/` + 2 brands + touches HIPAA (PHI checkpoint encryption) + a cross-brand mirror delete. Per the auditor-self-fix stake-asimétrico carriles + the cross-brand downstream-regression gate, this is NOT a safe candidate for unattended architect→done. Chris ratifies progression; `/dev-team` runs the DAG with auditor handoff per story-closure-gate.

## Handoff matrix (L1 — DAG order)

| Ticket | Surface | Primary agent | Model | Auditor | Est. cost | Depends on |
|---|---|---|---|---|---|---|
| T-flows-1 | backend (scaffold + uv) | builder-backend | Sonnet | auditor-backend (Opus) | low | — |
| T-flows-2 | agentic (core provider) | builder-agentic | **Opus** (R23) | auditor-agentic (Opus) | med | T-flows-1 |
| T-flows-3 | agentic (5-graph wiring + mirror delete) | builder-agentic | **Opus** (R23) | auditor-agentic (Opus) | high (cross-brand) | T-flows-2 |
| T-flows-4 | backend (migrations) | builder-backend | Sonnet | auditor-backend (Opus) | low | T-flows-3 |
| T-flows-5 | agentic (downstream + live-verify) | builder-agentic | **Opus** | auditor-agentic (Opus) | med | T-flows-3, T-flows-4 |

## Execution notes
- **Sequential DAG** (each ticket depends on prior). No parallel lanes — the wiring (T-3) depends on the provider (T-2), migrations (T-4) on wiring, verify (T-5) on both. Single `code:flows`-style bucket (M14) — serialize.
- **R23:** all agentic tickets (T-2, T-3, T-5) MUST be Opus (LangGraph production code). T-1, T-4 (scaffold/migrations) = Sonnet OK.
- **Engine edit detection:** every ticket cites the accepted proposal — `auditor-downstream-regression` engine-edit-detection PASSES (proposal `state: accepted`).
- **Cross-brand mirror scan (auditor Cat 12):** after T-3, must find 0 `build_production_checkpointer` in any brand.
- **Story-closure-gate:** T-flows-5 (live-verify) is the closing ticket — `developed → reviewing` (auditor-agentic) → `reviewing → done` (/pm-luana) only with `dod_live_verified: true` + `dod_evidence`. NO false-done on green tests (DoD #37).
- **Caps:** `audit_iterations ≤ 4`, `self_fix_iter ≤ 5` (Carril A mechanical only — agentic behavior changes → Carril B spawn dev-team). HIPAA encryption path = stake-asimétrico → Carril C escalate Chris if the auditor finds a fix touching the PHI serde.

## L2 (deferred-next-story)
T-l2-1..4 are NOT dispatched. They feed the next `/architect` ready-package (empleados-IA FlowCompiler story). build_status: deferred-next-story.

## Live-verify env (DoD #37)
`make dev-app-vitalia` → dev-app.vitalialat.com (Chrome DevTools MCP + psql against `luana-dev-vitalia_backend_dev-1`). Test user `dr.demo@vitalialat.com`. Fallback (O-3): scripted real durable invocation against dev Postgres.
