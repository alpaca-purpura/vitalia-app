---
story_id: vitalia-fase2-lisa-servicios
brand: vitalia
mode: RECONCILE-DELTA
base: dispatch-plan.md
architect_run_on: 2026-06-16
autonomous_mode: false          # G reconcile — re-live-verify + Chris signoff gate post-build. architect proposes; Chris ratifies.
---

# Dispatch plan — reconcile delta (G round 1)

> The base `dispatch-plan.md` covered Sub-phase A (T-1..T-8, autonomous). This delta dispatches
> the 4 reconcile tickets. **NOT autonomous** — the previous signoff was withheld in G; the close gate
> is re-live-verify (DoD #37) + Chris `chris_verify.signoff`. /dev-team pauses for Chris in G.

## Autonomous mode: FALSE (rationale)
- This delta resolves a fidelity scope-delta Chris ratified after seeing the live workspace "horrible". Chris explicitly chose `path = /architect designs reconcile, then build`. The build MUST re-live-verify against the same dev-app and Chris MUST re-exercise the kit before signoff. → not safe to auto-close.
- T-R0 is a **/pm-luana promotion gate** (core change) — by definition cannot run autonomous inside vitalia.

## Handoff matrix (ticket → agent → model → cost lane)

| Ticket | Surface | primary_agent | model | est. cost lane | gate |
|---|---|---|---|---|---|
| **T-R0** | `core/@luana/ui-kit` | **/pm-luana** (promotion gate) | n/a | lift gate | promotion proposal `2026-06-16-collapsible-section-ui-kit.md` must be ACCEPTED first |
| **T-R1** | `vitalia/backend offer` | `builder-backend` | workhorse | BE/non-agentic | RED-first pytest · arch fitness GREEN |
| **T-R2** | `vitalia/frontend servicios shell` | `builder-frontend` | workhorse | FE/non-agentic | RED-first vitest · independent (parallel) |
| **T-R3** | `vitalia/frontend ResumenView` | `builder-frontend` | workhorse | FE/non-agentic | GATED [T-R0 accepted+built, T-R1] · 8 visual goldens |

## Spawn order (DAG)
1. **First, in parallel** (no inter-dep): **T-R1** (BE) + **T-R2** (FE StatusBar). Also: `/pm-luana` opens + accepts the promotion proposal → builds **T-R0** in `@luana/ui-kit`.
2. **Then:** **T-R3** (FE ResumenView fidelity) — requires T-R0 (CollapsibleSection exported) + T-R1 (rich fields readable+patchable).
3. **Close:** all built → **re-live-verify** (DoD #37 · Chrome DevTools MCP · LUANA_LANE=A · write+read+effect on dev-app.vitalialat.com) → `/auditor` → **G: Chris re-exercises `demo-script.md` + `chris_verify.signoff`** → `/pm-vitalia` merge.

## Parallel-safety (M14 buckets · single-hub)
- T-R1 → `code:offer` · T-R2/T-R3 → `code:lisa` (serialize T-R2 then T-R3, same FE module bucket). T-R0 lives in core (`/pm-luana` worktree or hub-scoped lift — separate bucket).
- Commit by pathspec always (shared index · solo-Chris hub). Never `git add -A`.
- `export LUANA_LANE=A` before launching the live-verify session (Chrome DevTools MCP SingletonLock isolation · HB-73).

## Playwright visual scope (HARD — out-of-scope forbidden)
- IN: `servicios/[offer-id]/resumen` + StatusBar (every leaf) + CollapsibleSection. 8 goldens @ 0.001.
- OUT: TopBar/Ribbon/SubTabsBar/ValeriaSidebar, EscaleraView/CatalogoView, the other 4 leaves, ui-kit accordion/Group internals. DO NOT re-screenshot or touch.

## Must-load skills (consolidated · per ticket in 06-tickets-reconcile-delta.yaml)
- BE (T-R1): `backend-expert` + `offer-expert` + `tenant-isolation` + `backend-ddd` + `currency-handling` + `hipaa-lite` + `tdd-mandatory`.
- FE (T-R2/T-R3): `frontend-expert` + `vitalia-design-system` + `frontend-visual-fidelity` + `frontend-fsd` + `playwright-expert` + `chrome-devtools-verify` (close) + `offer-expert`/`brand-expert` (T-R3) + `anti-duplication` + `spanish-text` + `tenant-isolation` + `tdd-mandatory` + `ADR-vitalia-004`.
- Core (T-R0): `frontend-expert` + `design-system-canon`.

## Checkpoint (architect does NOT transition state)
- Story stays `developed · phase: AWAIT_CHRIS_VERIFY`. `/pm-vitalia` reconcile (R) writes `reconciled: true` + records the ratified scope-delta in `chris_verify.rounds` (the allowlist the auditor honors) + spawns the follow-up `vitalia-fase2-adrian-ficha-rica-knowledge` story from the ledger.
- `/dev-team` consumes this delta + builds T-R1..T-R3 (T-R0 via /pm-luana). Re-live-verify + signoff close the loop.
