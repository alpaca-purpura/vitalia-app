---
story_id: vitalia-fase1-ribbon-6-tabs
outcome: vitalia-mvp-ui-foundation
phase: fase-1
type: ui-story
agent_owner: shell
module: shell-organism
capability: shell.ribbon
state: done
last_modified: 2026-05-25
dev_team_pickup_at: 2026-05-25T02:30:00Z
dev_team_phase: BUILD_T5_DONE
auditor_pickup_at: 2026-05-25T03:50:00Z
auditor_phase: HANDOFF_TO_PM_MERGE
pm_merged_at: 2026-05-25T04:40:00Z
pm_merged_by: /pm-vitalia
merge_artifact: 07-merge.md
main_merge_status: deferred
main_merge_note: "Patrón establecido F1-S5/S6: state machine cerrada wip/vitalia + archive + capability live. Mass squash-merge a main es acto separado cross-story release orquestado por Chris. Acumulado wip/vitalia desde fa921711 (Ola 2 Slice 1 pre-Fase 1) = 70+ commits (Fase 1 F1-S0..S7 + Slice 1 marketing follow-ups). REQUIRES /pase-produccion o sesión dedicada Chris para merge a main."
auditor_verdict: APPROVED
auditor_warns: 1
auditor_warns_inventory:
  - "WARN-1 Q16 active:hover JIT purge mechanism (non-blocking, optional follow-up F1-S8)"
last_artifact: CHECKPOINTS.md
phase: HANDOFF_TO_PM_MERGE
gherkin_matrix: 06-audit/gherkin-matrix.md
review_doc: REVIEW.md
next_action: "/pm-vitalia aplica merge: escribir 07-merge.md (5 secciones cementadas) · update capabilities/shell-organism/ribbon.yaml NEW · refresh modules/shell-organism.md · 2 learnings (q16-jit-purge + mockup-playwright-audit) · squash-merge wip/vitalia → main · git mv archive · state reviewing→done"
ratified_by_chris: true
ratified_visual_by_chris: true
ratified_visual_at: 2026-05-25T02:00:00Z
ratified_visual_iter: 2
ratified_visual_mockups:
  - vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/mockups/ribbon-6-tabs.html
po_ux_version: 2
architect_iter: 1
architect_iter_amendments:
  - iter: "1-A"
    date: 2026-05-25
    reason: "Playwright visual audit (post architect iter 1) detectó 4 bugs visuales/a11y. Aplicados en place sin re-spawn architect-orchestrator (alcance dentro de RibbonTab/ConfigTab API)."
    cement_changes:
      - Q13: ConfigTab role=tab + aria-selected + tabindex (a11y semantic peer del tablist)
      - Q14: Tabs orgánicos (no min-w uniform, label-driven width)
      - Q15: whitespace-nowrap en tabLabel + role spans (ribbon h-14 uniforme)
      - Q16: active:hover preserva tint del agente (CSS specificity HARD)
    files_amended:
      - vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/01-spec.md (po_ux_version v1→v2, Q-table extended Q13-Q16, Estados visuales table updated, Accessibility § keyboard nav clarified 6 tabs)
      - vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/03-arch.md (RibbonTab.tsx code amended con whitespace-nowrap + active:hover preservation + decisiones D17.1/D17.2/D17.3)
      - vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/mockups/ribbon-6-tabs.html (rename desde ribbon.html per overlay rule shell-mockup-per-component + CSS fixes + ConfigTab role=tab)
    playwright_verification:
      - "Q15 nowrap PASS — tab heights uniform 55px (Lisa=Lucas)"
      - "Q13 ConfigTab role=tab PASS — aria-selected + tabindex correctos"
      - "Q16 active:hover preserves tint PASS — Lisa rgba(0,208,132,0.12) idéntico no-hover y hovered"
architect_run_on: 2026-05-25
last_artifact: T-5-result.md
phase: BUILD_T5_DONE
next_action: "AUTO-HANDOFF /auditor — story state=developed, ALL T-1..T-5 pushed GREEN. Playwright 32/32 smoke + 13/13 visual + 1328/1328 Vitest. D18 a11y cement (WCAG AA axe fix) + D19 AvatarFallback testid. Commit: e7992727. Awaiting auditor-frontend REVIEW."
ratified_artifacts:
  - 01-spec.md (v1)
  - mockups/ribbon.html (preview interactivo · 7 bloques)
  - 03-arch.md (v1 — consolidado FE-only, architect_iter=1)
  - 04-validators.yaml (5 categorías ★ v4.1, scenario_coverage 9/9 = 100%, test_construction_plan complete)
  - 05-guidelines.md (must_load_skills enforceable, patterns required/forbidden, files_in_scope verbatim)
  - 06-tickets.yaml (5 atomic tickets, owner_eligibility=qwen-opencode|claude-sonnet, DAG sequential, gherkin_coverage per ticket)
parallel_safe: true
priority: high
estimated_dev_days: 1-2
estimated_dev_hours: 14
dependencies:
  hard: [vitalia-fase1-shell-layout-5050, vitalia-fase1-design-tokens-theme, vitalia-fase1-valeria-chat-skeleton]
  soft: []
blocks_hard: [vitalia-fase1-sub-tabs-line2, vitalia-fase1-routing-shell]
reuse_map_summary: "EXTEND agent-catalog.ts (anti-duplication HARD) · MODIFY AppPanelSlot swap skeleton → <Ribbon /> · REUSE Shadcn Avatar+Tooltip · REUSE _agent-tw-classes.ts bg-soft helper · NEW Ribbon+RibbonTab+ConfigTab moléculas/organism · NEW arch test test-ribbon-no-shadcn-tabs.test.ts · NEW e2e/regression/vitalia-fase1-ribbon-6-tabs/ suite + 11 visual goldens"
spawned_at: 2026-05-22

# Schema v2 migration (cement 2026-05-27)
release: F1   # release ID · ver releases/
cap_target: ribbon   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# F1-S7 vitalia-fase1-ribbon-6-tabs — checkpoint

## Goal

`Ribbon` organismo: barra horizontal arriba del AppPanel con 5 RibbonTabs (Lisa · Lucas · Adrián · Valeria · Camila) + 1 ConfigTab (⚙️ Configurar al final right-aligned). Active state per URL segment `[agent]`. Click navega a default subtab del agente. WAI-ARIA tablist completo con roving tabindex (Arrow + Home/End + Enter/Space). Avatar fallback graceful Shadcn `<AvatarFallback>` con initial letter.

## Anti-objetivos

- NO incluir sub-tabs línea 2 (eso es F1-S8)
- NO implementar content per tab (eso son empty-states F1-S10 + Fase 2)
- NO bell icon notifications (Fase 2 postponed)
- NO Mateo en el Ribbon (agente transversal — surface futura)
- NO RBAC para ConfigTab (Fase 2)
- NO telemetría wireada (TODO Fase 2)

## Ready package delivered (2026-05-25)

`/architect vitalia vitalia-fase1-ribbon-6-tabs` ejecutó iter 1 y produjo 4 artefactos cementados:

| Artefacto | Path | Resumen |
|---|---|---|
| `03-arch.md` | `vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/03-arch.md` | Consolidado FE-only: § 0 context + skills consulted + § 0.1 anti-duplication audit (EXTEND in-place catalog SSoT) + § 2 FE detail (catalog extend, Ribbon roving tabindex, RibbonTab forwardRef+Avatar, ConfigTab Tooltip+IconButton, AppPanelSlot MODIFY swap skeleton, arch test NEW no-shadcn-tabs) + § 6 cross-cutting decisions (11 CC-N) + § 7 LIFT_CANDIDATE notes (3 L-N) + § 8 Risks + § 9 Test surfaces TDD + § 10 Test Construction Plan v4.1 + § 11 AC verbatim + § 12 Architectural fitness + § 13 capability YAML updates + § 14 cross-cutting concerns + § 15 Research Notes date-aware |
| `04-validators.yaml` | `vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/04-validators.yaml` | 5 categorías v4.1: non_functional (tsc/lint/prettier/vitest) + functional (9 E2E Playwright specs 1 per SC) + visual (11 goldens shrink-only mockup ratchet) + agentic_eval N/A justified + architectural_validation (10 sub-tests). scenario_coverage 9/9 = 100%. test_construction_plan complete con POMs + fixtures. |
| `05-guidelines.md` | `vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/05-guidelines.md` | must_load_skills enforceable (frontend-expert + tessl__{react-patterns,shadcn-ui,tailwind,vitest,nextjs-app-router-modularization} + playwright-expert + claude-md-management) + must_load_rules (raíz + vitalia overlay) + 18 patterns required + 25 patterns forbidden + files_in_scope verbatim (NEW/MODIFY/DELETE/out-of-scope explicit) + testing strategy TDD per layer + commit protocol + native dev workflow + quality gates summary table |
| `06-tickets.yaml` | `vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/06-tickets.yaml` | 5 atomic tickets sequential DAG: T-1 catalog extend (foundation) → T-2 RibbonTab+ConfigTab moléculas → T-3 Ribbon organism → T-4 AppPanelSlot integration + 4 arch tests (1 NEW + 3 EXTEND) → T-5 Playwright suite (POM + 9 specs + 11 goldens + axe + i18n). ZERO Opus (all FE production_code+test surfaces, R23 N/A). ~14 hours estimated. gherkin_coverage explícito per ticket mapeando SC-1..SC-9. |

## Resolved open question (heredada F1-S4)

**Q: Cómo se ve el Ribbon en modo `web` vs modo `agentic`?**

**R cementada en spec § 0 + 03-arch.md § 6 CC-8:** Misma horizontal en ambos modos (5 tabs + ConfigTab, `overflow-x-auto`). NO if-statements `mode === 'web'`. La única diferencia entre modos es el ancho disponible del AppPanel; el Ribbon se adapta vía `flex` + `overflow-x-auto` natural.

## Next action

`/dev-team vitalia vitalia-fase1-ribbon-6-tabs` arranca Conv 2 autonomous build:

1. Bootstrap `/dev-team` Step 0 closure gate (state=ready ✓)
2. Spawn `builder-frontend` Sonnet/opencode/qwen consumiendo:
   - `01-spec.md` (gherkin scenarios + microcopy + wireframes + visual goldens scope)
   - `03-arch.md` (architecture decisions + files/components contracts)
   - `04-validators.yaml` (test_construction_plan + validator commands)
   - `05-guidelines.md` (must_load_skills + patterns required/forbidden + files_in_scope)
   - `06-tickets.yaml` (DAG tickets T-1..T-5 sequential)
3. Builder ejecuta TDD per ticket (RED tests → GREEN code) cap 2 iter per ticket
4. AUTO-HANDOFF `/auditor` post `developed` per story-closure-gate.md
5. APPROVED → AUTO-HANDOFF `/pm-vitalia` merge Fase F → state `done` + archive

## Próximo paso post-done

F1-S8 sub-tabs-line2 arranca (depende de Ribbon para active agent context).
