---
story_id: vitalia-ux-discovery
outcome: vitalia-mvp-ui-foundation
state: done
phase: MERGED_AS_PARENT_SSOT
closure_type: parent_ssot_cumplido    # 17/56 tickets shipped vía 3 sub-stories archivadas. 5 sub-stories Slice 1 UI refined heredan mockups + design-system como referencia inmutable.
closed_at: 2026-05-20
closed_by: /pm-vitalia (Chris ratificó 2026-05-20)
inheritance_carryover:
  - mockups_redistributed_to: 5 sub-stories Slice 1 (02-design-ui-mockup.html each) + 1 archive snapshot onboarding-wizard
  - design_tokens_cemented_in: vitalia/frontend/src/app/globals.css (5 colores cian/púrpura/amarillo/marino/lima — T-arch-1 shipped)
  - audit_report_2026_05_20: audit-2026-05-20/AUDIT-REPORT.md (replan completo)
merge_commit_main: pending (archive happens in same commit del 07-merge — R2 brand-docs-schema.md)
last_artifact: 07-merge.md + audit-2026-05-20/AUDIT-REPORT.md
last_modified: 2026-05-20
split_accepted_by_chris: true
split_accepted_at: 2026-05-17
split_into:
  - vitalia-slice-1-infra-cross-cutting    # state=ready (no blockers) — /dev-team arranca acá
  - vitalia-slice-1-onboarding-wizard      # state=refined (blocked by infra + copilot-tools-impl)
  - vitalia-slice-1-inbox                  # state=refined (blocked by infra)
  - vitalia-slice-1-pipeline               # state=refined (blocked by infra + payment-adapter-mvp + copilot-tools-impl)
  - vitalia-slice-1-agenda                 # state=refined (blocked by infra + payment-adapter-mvp + fiscal-emission-pe)
  - vitalia-slice-1-fidelizacion           # state=refined (blocked by infra)
  - vitalia-slice-1-marketing              # state=refined (blocked by infra + copilot-tools-impl)
ratified_by_chris: true
v1_status_overall: ALL_BATCHES_RATIFIED
ready_package_status: READY_FOR_DEV_TEAM
architect_run_on: 2026-05-17
architect_model: claude-opus-4-7
split_recommendation: 7 sub-stories (per 03-arch.md § 8 + 06-tickets.yaml split_recommendation block)
next_action: "★ READY package CERRADO 2026-05-17 (Opus 4.7). Artifacts: 03-arch.md (consolidated index) + 03-arch-be.md + 03-arch-fe.md + 03-arch-agentic.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml (56 tickets) + delta-arch-notes.md. ★ NEXT STEP /pm-vitalia decisión: (A) ACCEPTAR split recommendation 7 sub-stories → migrar tickets a sub-stories + spawn /dev-team per sub-story respetando WIP cap; o (B) RECHAZAR split + spawn /dev-team directo sobre esta mega-story (advertencia: 56 tickets exceden 10-ticket cap, WIP developing ≤ 3 será cuello de botella). RECOMENDADO opción (A). PRE-REQUISITO ambos casos: (1) /pm-luana ratifica 2 promotion proposals NEW en docs/promotion-protocol/proposals/2026-05-17-{platform-tenants-location-columns,offer-studio-multi-session-maintenance}.md ANTES /dev-team pick T-be-migration-014 + T-be-migration-015 sub-tasks. (2) Side stories paralelas (vitalia-payment-adapter-mvp · vitalia-copilot-tools-impl · vitalia-fiscal-emission-pe) DEBEN estar state≥developed ANTES /dev-team picks blocked tickets — ver 06-tickets.yaml side_story_blockers tabla. State refined→ready cementado."
ratification_scope: "v1 spec ratificada Chris 2026-05-17 (7 batches) + ready package /architect cerrado 2026-05-17 (consolidated 03-arch + 3 sub-archs + validators + guidelines + tickets + delta notes)."
spawned_at: 2026-05-17
spawned_by: Chris + Claude direct (sesión vitalia UI exploration)
parallel_safe: true
blocked_reason: null

# Inputs cementados (immutable post v1 cierre — 7 batches ratificados)
v1_scope_decisions:
  slice_1_routes_p1:
    - /inbox
    - /pipeline
    - /agenda
    - /fidelizacion
    - /marketing
  wizard_valeria_scope: "Wizard agentic conversacional Slice 1 — slot-filling adaptativo + extracción NLU automática URL/doc/audio + voz Adrián REAL desde primer setup vía backend engine personality_service. 3 slots req (tenant.name + tenant.vertical + tenant.location) + 2 opc (brand.tone_default + offer[0]) + bonus NLU. Fase 1 chat-LEFT 50/50 split + transición morph 400ms a app shell daily."
  fidelizacion_slice_1: "4 patrones re-engagement automatizado (multi-sesión + follow-up médico + mantenimiento periódico + ausencia prolongada) + NPS reducido stat card secundaria. 6 cron jobs scheduled."
  fidelizacion_deferred_slice_2:
    - "Dashboard NPS completo (4 KPIs + chart distribución + lista filtrable)"
    - "Detractor flow agentic real per band"
    - "Owner notification escalation crítico 0-3"
    - "Google Reviews Places API"
    - "Birthday cron mensual + offer especial"
    - "Doctor view dedicada Slice 2 P2"
  wireframes_format: "6 mockups HTML clickable producidos: mockups/inbox.html · pipeline.html · agenda.html · fidelizacion.html · marketing.html · wizard-brand-studio.html"
  layout_pattern_ratified: "Propuesta C — Wizard-First Asymmetric (ratificada Chris 2026-05-17)"
  layout_phase_wizard: "Chat-LEFT 50/50 split SOLO durante wizard onboarding Valeria"
  layout_phase_app_daily: "Layout Nicolify Refinado · Sidebar 240px izq + Main centro + Copilot rail derecha 80px idle / 460px chat / 680px chat+history"
  url_state_ssot: "nuqs (search params type-safe) + Next.js 16 App Router parallel routes + chat-driven nav via tool calling router.push() dispatch"
  visual_states_per_screen: "5 standard (idle/loading/success/error/empty) + 3 agentic (agent-thinking / agent-waiting-approval / agent-failed)"
  microcopy_scope: "Default completo por pantalla Spanish neutro LATAM en <feature>/copy.ts files arch fitness enforced"
  side_stories_orchestration: "Paralelo — 3 side stories Slice 1 (payment-adapter-mvp · copilot-tools-impl · fiscal-emission-pe) deben estar shipped o state≥developed antes /dev-team picks Slice 1 dependent tickets per 06-tickets.yaml side_story_blockers"
  components_mapping: "REUSE engine 5 (style_analyzer + personality_service + voice_fidelity + brand_data_adapter) + REUSE Nicolify ~30 (closer-studio + growth-studio + brand-studio + sales — fork físico Slice 1 + token adapter HEX→Vitalia tokens + PHI wrappers) + NEW 20+ componentes Vitalia + 6 microcopy files + 5 Extension SDK registries plugin-ready"
  fork_decision_ratified: "Fork físico Slice 1 cementado en 03-arch.md § 7 #1 + ADR-vitalia-001-shared-vs-fork.md (T-arch-1). Shared package candidato Slice 2 cuando 2do brand opta-in"

# Ready package artifacts (post /architect Opus 4.7 single-shot 2026-05-17)
ready_package_artifacts:
  - 03-arch.md                     # consolidated index + cross-cutting principles + existing systems audit + split recommendation
  - 03-arch-be.md                  # backend sub-architecture (DDD + 11 tables + ~50 endpoints + 11 cron jobs + 5 Extension SDK registries + PHI compliance infra)
  - 03-arch-fe.md                  # frontend sub-architecture (FSD-Lite + 6 routes + 20+ NEW components + Storybook + arch fitness + a11y + perf budgets)
  - 03-arch-agentic.md             # agentic sub-architecture (LangGraph supervisor + deepagents + Adrián + Valeria + Lucas + 12 goldens + prompt cache slots + LiteLLM canonical)
  - 04-validators.yaml             # 4 categories: non_functional + functional + visual + agentic_eval (~40 validators)
  - 05-guidelines.md               # required patterns + 13+13+15 forbidden anti-patterns + files in scope + skills/rules loadout
  - 06-tickets.yaml                # 56 tickets DAG + 7 sub-story split recommendation + side story blockers + engine promotion blockers
  - delta-arch-notes.md            # engine modify + 7 lift candidates Slice 2 + cross-brand mirror check + R23 cost-routing breakdown

v1_open_questions_remaining: []  # all 12 spec § Handoff questions resolved in ready package per 03-arch.md § 7

# Research support
v1_research_artifacts:
  - vitalia/docs/product/stories/vitalia-ux-discovery/00-research-chat-layout.md  # 436 LOC · 13 productos · 30+ fuentes

# Schema v2 migration (cement 2026-05-27)
release: F0   # release ID · ver releases/
cap_target: null   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-ux-discovery — checkpoint

## Goal

Definir el flujo de navegación + patrón UI primario del app Vitalia (post Story 11 shipped backend) + producir ready package /architect (technical contract) para autonomous build /dev-team.

## State transitions

- `idea` → `refining` (2026-05-17 mañana — /pm-vitalia handoff /po-ux)
- `refining` → `refined` (2026-05-17 tarde — Batches 1-7 ratificados Chris)
- `refined` → `ready` (2026-05-17 — /architect Opus 4.7 single-shot ready package CERRADO)

## Ready package overview

| Artifact | LOC | Purpose |
|---|---|---|
| 03-arch.md | ~485 | Consolidated index + cross-cutting principles + existing systems audit + split recommendation |
| 03-arch-be.md | ~996 | Backend sub-arch (DDD + tables + endpoints + cron + Extension SDK + PHI compliance) |
| 03-arch-fe.md | ~615 | Frontend sub-arch (FSD-Lite + 6 routes + components + Storybook + arch fitness) |
| 03-arch-agentic.md | ~541 | Agentic sub-arch (LangGraph + deepagents + Adrián + Valeria + Lucas + cache slots + LiteLLM) |
| 04-validators.yaml | ~572 | 4 categories validators (40+ test runners) |
| 05-guidelines.md | ~316 | Required + forbidden patterns + files in scope + skills loadout |
| 06-tickets.yaml | ~1134 | 56 tickets DAG + 7 sub-story split + side story blockers + engine promotion blockers |
| delta-arch-notes.md | ~154 | Engine modify + lift candidates Slice 2 + cross-brand mirror check + R23 breakdown |
| **Total** | **~4813 LOC** | |

## Pre-requisites for /dev-team build start

1. **/pm-luana ratifica 2 promotion proposals NEW** (engine table column additions):
   - `docs/promotion-protocol/proposals/2026-05-17-platform-tenants-location-columns.md`
   - `docs/promotion-protocol/proposals/2026-05-17-offer-studio-multi-session-maintenance.md`

2. **3 side stories paralelas state≥developed** (per 06-tickets.yaml side_story_blockers):
   - `vitalia-payment-adapter-mvp` — Mercado Pago integration
   - `vitalia-copilot-tools-impl` — Valeria + Lucas tools harness
   - `vitalia-fiscal-emission-pe` — Nubefact PE adapter (NEW Slice 1)

3. **/pm-vitalia decisión split** — accept 7 sub-stories split (RECOMMENDED) o reject (advertencia WIP cap):
   - Si accept → migrar 56 tickets a 7 sub-stories per `split_recommendation` block en 06-tickets.yaml + spawn /dev-team per sub-story
   - Si reject → spawn /dev-team directo sobre mega-story (cuello de botella WIP cap developing ≤ 3)

## Architect single-shot ratification

`/architect` Opus 4.7 ran single-shot full-stack 2026-05-17, consuming:
- 01-spec.md (v1 cementado 7 batches Chris)
- 00-research.md + 00-research-chat-layout.md
- vitalia/docs/architecture/design-system.md
- vitalia/.claude/rules/hipaa-lite.md + README.md
- vitalia/config/brand.yaml
- vitalia/backend/src/modules/vitalia/extensions.py (Story 11 cement)
- core/luana-core-* engine packages (READ-ONLY consultation per anti-duplication §0 + auditor-downstream-regression.md)

Skills consulted per surface:
- BE: backend-expert, metrics-expert, brand-expert (wizard), offer-expert (medical_services_v1 preset)
- FE: frontend-expert, playwright-expert
- Agentic: sales-agent-expert, copilot-expert, brand-expert, claude-api (prompt cache slots), tessl__langgraph, tessl__deepagents, tessl__graceful-degradation

Cross-cutting rules loaded:
- tenant-isolation, backend-ddd, frontend-fsd, architectural-fitness, anti-duplication, spanish-text, tdd-mandatory, master-data, currency-handling, auditor-downstream-regression, parallel-safety, git-safety, anti-default-flip-audit

Brand overlay: vitalia/.claude/rules/hipaa-lite.md cardinal (dual filter tenant+clinic + audit_log + pgcrypto + RBAC + PII sanitize + channel guards).

## Bitácora

- **2026-05-17 v1 CIERRE completo + transition refining→refined** — spec 7 batches ratificados Chris.
- **2026-05-17 /architect ready package CERRADO + transition refined→ready** — Opus 4.7 single-shot full-stack produjo 8 artifacts (~4813 LOC) cubriendo BE + FE + AGENTIC + cross-cutting + delta notes. Split recommendation 7 sub-stories. 56 tickets DAG con side story blockers + 2 engine promotion proposals required. ZERO engine modifications proposed (per anti-duplication §0). ZERO cross-brand mirrors. R23 cost-routing: 8 production_code=true Opus tickets + 48 Sonnet/qwen-opencode tickets. Performance budgets cementados (LCP<2.5s · INP<200ms · CLS<0.1 · bowtie SVG <30KB gzipped). A11y WCAG 2.1 AA cementado. Spanish neutro UI chrome arch fitness enforced. PHI compliance hipaa-lite cardinal cementado. Anti-duplication §0 inventory respetado. State refined→ready.
