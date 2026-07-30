---
story_id: vitalia-fase1-shell-layout-5050
outcome: vitalia-mvp-ui-foundation
phase: fase-1
type: ui-story
agent_owner: shell
module: shell-organism
capability: shell.layout-5050
state: done
phase: MERGED
last_artifact: 07-merge.md
gherkin_matrix: 06-audit/gherkin-matrix.md
last_modified: 2026-05-23T18:35:00-05:00
transitioned_to_developing_at: 2026-05-23T14:15:00Z
transitioned_to_developed_at: 2026-05-23T15:50:00-05:00
transitioned_to_reviewing_at: 2026-05-23T16:00:00-05:00
transitioned_to_done_at: 2026-05-23T18:35:00-05:00
dev_team_iter: 1
auditor_iter: 3
audit_iterations: 3
current_ticket: T-7  # all done
verdict: APPROVED-WITH-DEFER
deferred_scenario: "SC-3 last assertion (rail→full snap-up race condition) — F1-S5/S6 lifecycle refactor — tracked en vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050-race-fix/ state=parked"
merge_commits_range: e630e5d6..bbd79024
capability_created: vitalia.shell-organism.layout-5050
learning_created: vitalia/docs/learnings/2026-05-23-shell-layout-race-condition-defer.md (promotable: candidate)
followup_story_parked: vitalia-fase1-shell-layout-5050-race-fix
next_action: "MERGED. Archived to vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/"
ratified_by_chris: true
ratified_at: 2026-05-23T13:45:00Z
ratified_visual_by_chris: true                     # gate bloqueante satisfecho
ratified_visual_at: 2026-05-23T13:45:00Z
ratified_visual_iter: 4                            # v1 base · v2 resize dynamic + state toggle · v3 LogoMark assets · v4 CSS swap fix
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050/mockups/shell-layout-agentic.html
  - vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050/mockups/shell-layout-web.html
transitioned_to_refined_at: 2026-05-23T13:45:00Z
transitioned_to_ready_at: 2026-05-23T14:07:08Z
architect_iter: 1
architect_run_on: 2026-05-23
parallel_safe: false
priority: critical
estimated_dev_days: 1-2
total_tickets: 7
opus_tickets: 0
sonnet_tickets: 7
playwright_required: true
hipaa_lite_scope: not_applicable
dependencies:
  hard: [vitalia-fase1-stack-stability, vitalia-fase1-design-tokens-theme, vitalia-fase1-topbar-global]
  soft: [vitalia-fase1-tenant-switcher]
blocks_hard: [vitalia-fase1-valeria-rail-history, vitalia-fase1-valeria-chat-skeleton, vitalia-fase1-ribbon-6-tabs, vitalia-fase1-routing-shell, vitalia-fase1-empty-states]
hard_deps_status: "CHAIN F1-S0..S3 COMPLETE 2026-05-23 — blocker_hard removido por /pm-vitalia"
reuse_map_summary: "NEW shell layout · route group `(shell-organism)/` paralelo a `(dashboard)/` legacy · zustand shellStore para mode (agentic/web) · react-resizable-panels v4 lib (Shadcn canonical)"
spawned_at: 2026-05-22
transitioned_to_refining_at: 2026-05-23
phase_marker: READY_PACKAGE_CLOSED
next_action: "Conv 2 autonomous build EN CURSO — T-1+T-2 paralelos (no deps) primero, después T-3→T-4+T-5→T-6→T-7"

# Schema v2 migration (cement 2026-05-27)
release: F1   # release ID · ver releases/
cap_target: layout-5050   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F1-S4 vitalia-fase1-shell-layout-5050 — checkpoint

## Goal

Crear el layout root del route group `(shell-organism)/` con split 50/50 (modo agentic default): TopBarGlobal arriba + Grid `[ValeriaPanel 50%] [AppPanel 50%]` debajo. Soportar modo web alternativo (Valeria collapsed a rail · App 100%). Mobile responsive.

## Anti-objetivos

- NO incluir contenido del ValeriaPanel (eso es F1-S5 + F1-S6)
- NO incluir contenido del AppPanel (eso es F1-S7 + F1-S8 + F1-S10)
- NO touch `(dashboard)/` legacy
- NO modificar TopBarGlobal/LogoMark/ThemeToggle/TenantSwitcher (F1-S1/S2/S3 REUSE)
- NO scope cross-brand ni engine core (brand-local Vitalia)

## Ready package (closed by `/architect` 2026-05-23)

| Artifact | Path | Status |
|---|---|---|
| 01-spec.md | `01-spec.md` | ratified (15 secciones, gate v4.1 PASS) |
| 03-arch.md (consolidado FE only) | `03-arch.md` | NEW · 851 lines · arch_iter 1 |
| 04-validators.yaml | `04-validators.yaml` | NEW · 5 categorías · scenario_coverage 100% · playwright_required HARD |
| 05-guidelines.md | `05-guidelines.md` | NEW · must_load_skills + must_load_rules + patterns required/forbidden + files in scope + verify commands |
| 06-tickets.yaml | `06-tickets.yaml` | NEW · 7 tickets · DAG sequential · gherkin_coverage per ticket |
| Mockups HTML ratificados | `mockups/shell-layout-{agentic,web}.html` | ratified Chris 2026-05-23 iter 4 |

## Architect resolutions (key decisions cementadas)

| Q | Resolution |
|---|---|
| Default valeriaState (DC §6.1 'rail' vs spec SC-1 'full') | `'full'` (override DC §6.1) — matches mockup ratificado + UX onboarding · /pm-vitalia updates DC post-merge |
| Resize implementation | `react-resizable-panels` v4 (Option A) — Shadcn-canonical, mature (v4.11.1 published 8 days ago 2026-05-23) |
| ShellModeToggle mount | Overlay sibling dentro ShellOrganismLayout (NO modificar TopBarGlobal) |
| Viewport [768-1023] + state='full' edge case | `useViewportGuard` one-way force a 'rail', no auto-restore |
| Triple `<main>` element pattern | CSS-driven viewport branching via `md:hidden`/`md:block`/`md:grid` mutually-exclusive — only ONE main visible per viewport |
| Visual goldens path | `vitalia/frontend/e2e/__screenshots__/shell-layout-5050/*.png` (6 PNGs) |
| Mobile drawer trigger | Deferred to F1-S5+ (burger button); F1-S4 mobile fallback solo AppPanelSlot visible |

## Cross-module audit (NO-NEW-LAYER rule)

- Cross-brand mirror scan: 0 matches en nicolify/comunify/lupulo para `ShellOrganismLayout`, `ValeriaSidebarSlot`, `AppPanelSlot`, `ShellModeToggle`, `shell-store`. **Clean.**
- Engine core: ningún equivalente TS shell en `core/luana-core-*/`. NEW correcto.
- Same-brand existing: 0 matches en vitalia/frontend/src. NEW correcto.
- Verdict: **NEW (justified brand-local)** — futuro lift candidate cuando lupulo/fitflow adopten patrón similar (via `core/luana-core-ui-shell/` promotion proposal /pm-luana).

## R23 status

NO aplica (zero AGENTIC surface). FE only.

## Estimated work

- 7 tickets · ~13 hours · ~1140 LOC.
- DAG: T-1+T-2 parallel-safe → T-3 (depends on T-1+T-2) → T-4+T-5 (depend on T-3) → T-6 (depends on T-1..T-5) → T-7 (depends on T-4+T-5+T-6).
- Owner eligibility: `[qwen-opencode, claude-sonnet]` (zero Opus — FE no-agentic).

## Next steps

1. `/dev-team vitalia vitalia-fase1-shell-layout-5050` — Conv 2 autonomous build. Takes T-1 first (state ready → developing).
2. Builders run TDD RED-first per ticket. Re-run validators per `04-validators.yaml`.
3. T-7 visual goldens iter 1: monta mockups en `python3 -m http.server 8888 mockups/` side-by-side con `localhost:3002` componente real. Chris ratifica side-by-side → `--update-snapshots` once.
4. ON ALL GREEN: state=developing → developed → AUTO-HANDOFF `/auditor` (default per `story-closure-gate.md`).
5. Auditor APPROVED → AUTO-HANDOFF `/pm-vitalia` merge.
6. `/pm-vitalia` writes `07-merge.md` (5 secciones cementadas) + creates `vitalia/docs/product/capabilities/platform/shell.layout-5050.yaml` (status: live) + updates SHELL-DESIGN-CONTRACT.md §6.1 default → 'full' + `git mv` story to archive.

## Próximo paso post-done

F1-S5 valeria-rail-history + F1-S7 ribbon-6-tabs pueden arrancar en paralelo (independientes entre sí). Ambos REPLACE placeholders ValeriaSidebarSlot/AppPanelSlot generados por F1-S4.
