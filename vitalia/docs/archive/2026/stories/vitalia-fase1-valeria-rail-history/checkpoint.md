---
story_id: vitalia-fase1-valeria-rail-history
brand: vitalia
outcome: vitalia-mvp-ui-foundation
phase: fase-1
type: ui-story
agent_owner: shell
module: shell-organism
capability: shell.valeria-sidebar
state: done                                        # ★ reviewing→done 2026-05-24 (/pm-vitalia merge complete)
last_modified: 2026-05-24T23:30:00-05:00
phase_pm: MERGED
merge_artifact: 07-merge.md
merge_date: 2026-05-24
merged_to_main: false                              # ⏸ squash-merge wip/vitalia→main pendiente ratificación Chris (action destructive)
capability_created: vitalia/docs/product/capabilities/shell-organism/valeria-sidebar.yaml
auditor_iter: 1
auditor_started_at: 2026-05-24T22:35:00-05:00
auditor_finished_at: 2026-05-24T23:00:00-05:00
auditor_verdict: APPROVED                           # ★ 5/5 C1-C5 + 14/14 categorías + gates GREEN
auditor_summary:
  checkpoints_passed: 5                             # C1 C2 C3 C4 C5 all PASS
  categories_passed: 14                             # 14 applicable Cat (no FAILs, 2 WARNs non-blocking)
  warnings:
    - "W-1: HistoryGroup doc inaccuracy ('Server Component' label vs render context) — post-merge cleanup"
    - "W-2: ValeriaSidebar console.warn in render body should be in useEffect — post-merge cleanup"
  gherkin_matrix: "9/9 SC scenarios PASS (06-audit/gherkin-matrix.md)"
  visual_goldens: "13/13 PNGs ratchet baseline iter 1 (Chris mockups ratified)"
  axe_wcag2aa: "0 violations across rail/full/collapsed/mobile drawer"
  cross_brand_mirror: "0/8 names (anti-duplication clean)"
  engine_edits: "0 (zero touch core/luana-core-*)"
  scope_discipline: "held STRICT — zero out-of-scope file touches"
audit_artifacts:
  - vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/T-story-review.md
  - vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/CHECKPOINTS.md
  - vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/06-audit/gherkin-matrix.md
dev_team_iter: 1
dev_team_run_on: 2026-05-24
dev_team_summary:
  tickets_completed: 8                              # T-1..T-8 all pushed
  bonus_tickets: 2                                  # T-5.bis (Portal fix) + T-8.bis (a11y role+contrast inline by orchestrator)
  vitest_full_suite: "1080/1080 PASS (126 test files)"
  playwright_functional: "45/45 PASS (project=smoke)"
  playwright_visual: "13/13 PASS (project=visual, ratchet baseline iter 1)"
  axe_wcag2aa: "0 violations (post T-8.bis fixes)"
  tsc_eslint_prettier: "all clean"
  scope_discipline_held: true                       # zero out-of-scope files touched (shell-store + other agent components intact)
ratified_by_chris: true                            # ★ spec 01-spec.md ratificado iter 1
ratified_at: 2026-05-23T19:55:00-05:00
ratified_iter: 1
ratified_visual_by_chris: true                     # ★ mockups HTML ratificados iter 1 ("me gustaron")
ratified_visual_at: 2026-05-23T19:55:00-05:00
ratified_visual_iter: 1
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-rail.html
  - vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-history.html
po_ux_version: 1
architect_iter: 1
architect_run_on: 2026-05-24
last_artifact: 06-tickets.yaml
hipaa_lite_scope: not_applicable                   # shell chrome UI, mock data sin PHI
parallel_safe: true
priority: high
estimated_dev_days: 2-3
estimated_dev_hours: 19.5                          # de 06-tickets.yaml total
dependencies:
  hard: [vitalia-fase1-shell-layout-5050]          # done 2026-05-23 archived
  soft: []
blocks_hard: [vitalia-fase1-valeria-chat-skeleton]
reuse_map_summary: "REUSE 80% nicolify CopilotSidebar (TRANSPONER grid · invertir [chat][rail] → [rail][chat]) · adapt widths · renombrar Valeria · CSS vars Vitalia · auto-coupling collapsed→shellMode='web' (NEW vs Nicolify)"
side_effects_F1_S4:                                # ★ ratificados Chris batches 1b+2 2026-05-23
  - "MODIFY vitalia/frontend/src/components/shared/shell-organism/ShellOrganismLayoutClient.tsx::MIN_VALERIA_PX (full 620 → 580)"
  - "MODIFY vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx (agregar hamburger <md viewport)"
  - "DELETE vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.tsx (reemplazado por ValeriaSidebar real)"
  - "DELETE vitalia/frontend/src/components/shared/shell-organism/ValeriaSidebarSlot.test.tsx"
spawned_at: 2026-05-22
next_action: "/pm-vitalia merge vitalia-fase1-valeria-rail-history → 07-merge.md 5 secciones + capability YAML + module MD auto-list + git mv archive/2026/stories/ + squash-merge wip/vitalia → main → state=reviewing→done"
autonomous_build_requested: true                    # ★ Chris ratificó "implementalo hasta el done de forma autónoma" 2026-05-23
scope_discipline: "STRICT — solo F1-S5 + side-effects ratificados. NO touch otros componentes shell-organism que ya funcionan (TopBarGlobal cambio solo agrega hamburger, no modifica logic existente; ShellOrganismLayoutClient cambio solo ajusta MIN + replace slot import). 05-guidelines.md § 5 enumera files in scope / never touch"
ready_package:
  files:
    - vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/03-arch.md
    - vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/04-validators.yaml
    - vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/05-guidelines.md
    - vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/06-tickets.yaml
  tickets_total: 8
  opus_required: 0
  sonnet_eligible: 8
  parallelizable_tickets: [T-1, T-2, T-3, T-6]    # Wave 1 (T-6 paralelo con T-3 — distinct files)
  serialized_tickets: [T-4, T-5, T-7, T-8]
  scenarios_mapped: 9
  scenarios_coverage_pct: 100
  visual_goldens_pngs: 13
  test_construction_plan_present: true

# Schema v2 migration (cement 2026-05-27)
release: F1   # release ID · ver releases/
cap_target: valeria-sidebar   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F1-S5 vitalia-fase1-valeria-rail-history — checkpoint

## State summary

| Field | Value |
|---|---|
| State | **`ready`** (post architect iter 1 paquete completo 2026-05-24) |
| Phase | READY_PACKAGE_CLOSED |
| Owner active | Hand-off → `/dev-team vitalia vitalia-fase1-valeria-rail-history` |
| Surfaces | FE_ONLY (cero BE, cero AGENTIC, cero engine touch) |
| Tickets | 8 atómicos (4 paralelizables Wave 1, 4 serializados Waves 2-4) |
| Gherkin scenarios | 9 mapeados 1:1 a Playwright specs |
| Visual goldens | 13 PNGs (5 desktop states × theme + history-empty × theme + drawer-mobile) |
| Estimated dev hours | 19.5h (≈ 2.4 días @ 8h workday) |
| Autonomous build | **REQUESTED** Chris 2026-05-23 |

## Architect iter 1 output (2026-05-24)

Paquete completo:
- **03-arch.md** (943 LOC) — Context Summary + Existing Systems Audit + Component tree atomic design + State machine + Handlers contract + Side-effects MODIFY diff verbatim + File tree + Test construction order + Server/Client decision tree + Cross-cutting concerns + Research notes date-aware
- **04-validators.yaml** (404 LOC) — 5 categorías (non_functional + functional + visual + agentic_eval N/A + architectural_validation) + scenario_coverage 9/9 + sub_categories_coverage (empty_state/accessibility/i18n covered, race/concurrent/network/large_dataset N/A reasons) + test_construction_plan + POMs + fixtures + preflight notes
- **05-guidelines.md** (377 LOC) — Must-load skills (frontend-expert + playwright-expert + tessl react/shadcn/tailwind/vitest) + must-load rules (raíz + vitalia overlay) + 22 patterns required + 22 patterns forbidden + files in scope/modify/delete/NEVER-touch + auditor handoff expectations
- **06-tickets.yaml** (551 LOC) — 8 tickets atómicos + DAG + R23 production_code matrix (cero Opus, todos Sonnet/opencode/qwen eligible) + gherkin_coverage per ticket + cross_stack_handoff notes + paralelización Wave 1 (T-1+T-2+T-3+T-6)

## Decisiones arquitectónicas cementadas (de 03-arch.md § 2 + § 4)

| Decision | Resolution |
|---|---|
| Cross-brand mirror scan | 0 matches en nicolify/comunify/lupulo (8 nombres NEW Valeria*/History*/EmptyStateInline/useKeyboardShortcuts verificados) — NEW correctly per anti-duplication.md primera ocurrencia |
| `useKeyboardShortcuts` ubicación | `vitalia/frontend/src/hooks/` (brand-local NEW). LIFT CANDIDATE cross-brand a `core/@luana/hooks/` post 2do consumer (documentar learning post-merge, NO ahora) |
| ShellOrganismLayoutClient MODIFY diff | Único: `MIN_VALERIA_PX 620→580` (full ternary) + replace `<ValeriaSidebarSlot/>` import → `<ValeriaSidebar/>` real. NADA más |
| TopBarGlobal MODIFY diff | Único: agregar hamburger `Menu` button visible `<md` + handler `setValeriaState('full')+setShellMode('agentic')`. Convert Server→Client Component obligatorio. NADA más |
| `ValeriaSidebarSlot.tsx` + test | DELETE ambos (cleanup F1-S5) |
| Auto-coupling state | `setValeriaState('collapsed')` → AUTO `setShellMode('web')`; `setValeriaState('rail'|'full')` → AUTO `setShellMode('agentic')`. Mobile drawer cierre NO auto-shellMode change |
| Adversarial guard runtime | ValeriaSidebar valida `valeriaState` válido o `console.warn` + fallback render (cero white screen) |
| Mobile drawer | Focus trap manual Tab cycling (sin focus-trap-react dep), focus restoration al hamburger button, aria-modal solo cuando isExpanded mobile |
| Visual goldens iter 1 | 13 PNGs total · side-by-side ratify Chris OBLIGATORIO antes `--update-snapshots` · ratchet shrink-only |
| Capability YAML | `/pm-vitalia` crea `valeria-sidebar.yaml` post-merge (builders NO crean) + auto-regen `modules/shell-organism.md` via reconcile_capabilities |
| Audit handoff | `auditor-frontend` (Opus) — Cat 1 FSD + Cat 9 PII (N/A declared + mock data audit) + Cat 10 TDD + Cat 12 anti-duplication + Cat 17 SSoT + a11y axe wcag2aa + spanish neutro + scope discipline check |

## Próximos pasos

```
state=ready  →  /dev-team vitalia vitalia-fase1-valeria-rail-history
                 ↓
state=developing (Wave 1: T-1 + T-2 + T-3 + T-6 en paralelo posible)
                 ↓
state=developed  → AUTO-HANDOFF /auditor (story-closure-gate.md mandatory)
                 ↓
state=reviewing  → APPROVED → AUTO-HANDOFF /pm-vitalia merge → state=done
```

## Post-merge tasks (`/pm-vitalia`)

1. Crear `vitalia/docs/product/capabilities/shell-organism/valeria-sidebar.yaml`
2. Update `vitalia/docs/product/capabilities/shell-organism/layout-5050.yaml` (mencionar replace slot → real)
3. Regen `vitalia/docs/product/modules/shell-organism.md` via `scripts/reconcile_capabilities.py --brand vitalia`
4. Squash-merge `wip/vitalia` → `main` con story directory move a `vitalia/docs/archive/2026/stories/vitalia-fase1-valeria-rail-history/` (mismo commit per R2 brand-docs-schema)
5. Documentar `vitalia/docs/learnings/2026-05-DD-useKeyboardShortcuts-lift-candidate.md` (LIFT CANDIDATE cross-brand)
6. Spawn F1-S6 `vitalia-fase1-valeria-chat-skeleton` (sucesor unblocked)

## Histórico

- 2026-05-22: spawned (placeholder)
- 2026-05-23: /po-ux iter 1 — spec 01-spec.md ratificado + mockups HTML ratificados ("me gustaron")
- 2026-05-23: state refining→refined + autonomous_build_requested ratificado
- 2026-05-24: /architect iter 1 — ready package paquete completo (03+04+05+06 cementados) + state refined→ready
- (próximo) 2026-05-DD: /dev-team autonomous build state ready→developing→developed→reviewing→done
