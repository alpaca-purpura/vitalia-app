---
story_id: vitalia-fase1-empty-states
outcome: vitalia-mvp-ui-foundation
phase: fase-1
type: ui-story
agent_owner: shell
module: shell-organism
capability: shell.empty-states
state: done
phase: MERGED_F1_S10
last_modified: 2026-05-26T13:55:00-05:00
transitioned_to_reviewing_at: 2026-05-26T13:35:00-05:00
transitioned_to_done_at: 2026-05-26T13:55:00-05:00
merged_by: /pm-vitalia
auditor_verdict: APPROVED
phase_1_complete: true   # ★ F1-S10 cierra CHAIN F1-S0..F1-S10 outcome vitalia-mvp-ui-foundation
t1_state: pushed
transitioned_to_refining_at: 2026-05-26
transitioned_to_refined_at: 2026-05-26T11:55:00-05:00
transitioned_to_ready_at: 2026-05-26T12:15:00-05:00
transitioned_to_developing_at: 2026-05-26T12:20:00-05:00
transitioned_to_developed_at: 2026-05-26T18:00:00-05:00
current_ticket: null
completed_tickets: [T-1, T-2, T-3, T-4, T-5, T-6, T-7, T-8, T-9, T-10, T-11]
pending_chris_visual_ratify: true
ratified_by_chris: true
ratified_at: 2026-05-26T11:55:00-05:00
ratified_visual_by_chris: true                     # ★ gate shell-mockup-per-component.md PASS
ratified_visual_at: 2026-05-26T11:55:00-05:00
ratified_visual_iter: 2
po_ux_version: 2
po_ux_iter: 2
po_ux_batches_ratified: [batch_1, batch_2, batch_3]
architect_iter: 1
last_artifact: 06-tickets.yaml
ratified_visual_mockups_expected:
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/empty-states-grid.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/lisa-servicios-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/adrian-embudo-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/adrian-inbox-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/camila-voz-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/valeria-agenda-placeholder.html
  - vitalia/docs/product/stories/vitalia-fase1-empty-states/mockups/config-conexiones-placeholder.html
ready_package:
  - 03-arch.md            # full-stack architect (FE only · BE/AGENTIC N/A)
  - 04-validators.yaml    # 5 categorías ★ v4.1 (non_functional · functional · visual · agentic_eval N/A · architectural_validation)
  - 05-guidelines.md      # patterns required + forbidden + scope + skills + reference artifacts
  - 06-tickets.yaml       # 11 tickets DAG sequential ~24h total, claude_opus_required:false TODOS
parallel_safe: false
priority: critical
estimated_dev_days: 2-3
dependencies:
  hard: [vitalia-fase1-routing-shell, vitalia-fase1-sub-tabs-line2]
  soft: []
hard_deps_status: "CHAIN F1-S0..S9 COMPLETE 2026-05-25 — blocker_hard removido (F1-S8 + F1-S9 archived)"
blocks_hard: []                                    # último átomo Fase 1 — Fase 2 puede arrancar después
reuse_map_summary: "NEW 17 moléculas + 8 organismos + 1 page MODIFY + 3 arch tests + 11 Playwright specs + ~70 visual goldens. SubTabContent dispatcher consume RIBBON_SUBTABS SSoT. Sales_studio parity inbox brand-local (NO cross-brand mirror). Takeover UX visual con local React useState (Zustand documented F2-S3). Agenda enriquecida 5 moléculas (toolbar+filters+dayHeader+slot+summaryFooter)."
spawned_at: 2026-05-22
next_action: "AUTO-HANDOFF /auditor — story state=developed. All 11 tickets pushed. Visual goldens pending_chris_visual_ratify: true (live generation on stack required)."

# Schema v2 migration (cement 2026-05-27)
release: F1   # release ID · ver releases/
cap_target: empty-states   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F1-S10 vitalia-fase1-empty-states — checkpoint

## State

`state: ready` (post architect run 2026-05-26T12:15:00-05:00). Ready package completo (03-arch.md · 04-validators.yaml · 05-guidelines.md · 06-tickets.yaml). Próximo: `/dev-team` Conv 2 autonomous build.

## Goal

Última story Fase 1: implementar `SubTabContent` dispatcher que renderiza 22 sub-tab pages con placeholders.
- 6 sub-tabs especiales (Lisa Servicios · Adrián Embudo · Adrián Inbox · Camila Voz · Valeria Agenda · Config Conexiones) replican UI mockup HTML ratificada.
- 16 sub-tabs genéricas usan `EmptyState` molécula con icon + label del catalog SSoT.

## Surfaces

- FE only: `vitalia/frontend/src/components/shared/shell-organism/` + `features/{lisa,lucas,adrian,valeria,camila,config}/components/` + page MODIFY `app/[tenantId]/(shell-organism)/[agent]/[subtab]/page.tsx`.
- NO BE. NO agentic. NO engine `core/luana-core-*/` edits.

## Anti-objetivos

- NO interactividad real (Kanban DnD, agenda CRUD, inbox conversación) — Fase 2.
- NO fetch data API real — mocks hardcoded en placeholder components.
- NO filtros funcionales / búsqueda / paginación.
- NO Mateo sub-tabs (catalog SSoT confirma `mateo: []`).
- NO routing nuevo (F1-S9 ya cementó URL tree).

## Acceptance criteria (resumen)

| AC | Verificación |
|---|---|
| AC-1 | 22 sub-tab pages navegables sin 404 (SC-1) |
| AC-2 | 6 sub-tabs especiales replican mockup HTML (SC-2/3/4/4.bis/8 visual) |
| AC-3 | 16 sub-tabs genéricas usan EmptyState consistente (SC-8) |
| AC-4 | SubTabHeader visible con title + description (SC-1) |
| AC-5 | Visual goldens ~70 PNG (light/dark/takeover/responsive) |
| AC-6 | a11y heading hierarchy h2→h3 + axe wcag2aa (SC-9) |
| AC-7 | Mobile responsive sub-tabs especiales (SC-4 responsive · spec § 11) |
| AC-8 | Playwright functional 22 URLs sin error (SC-1) |
| AC-9 | Vitest unit por placeholder especial + arch tests NEW (3) |
| AC-10 | Takeover UX state A↔B local React useState + sidebar toggle (SC-4.bis) |

## Próximo paso post-ready

`/dev-team vitalia vitalia-fase1-empty-states`:
1. Step 0 worktree gate
2. T-1 spawn builder-frontend Sonnet (foundation 6 moléculas + vitest unit)
3. DAG: T-1 → (T-2..T-5, T-8) paralelo → T-5 → T-6 → T-9 → T-10 → T-11
4. Cierre Conv 2: `developed` + AUTO-HANDOFF `/auditor`
5. Conv 3 auditor verde → AUTO-HANDOFF `/pm-vitalia merge`
6. **FASE 1 COMPLETA** — shell vacío navegable production-ready. Fase 2 puede arrancar.
