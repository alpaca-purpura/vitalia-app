---
story_id: vitalia-slice-1-marketing
outcome: vitalia-mvp-ui-foundation
parent_spec: vitalia-ux-discovery (archived 2026-05-20 — inheritance carryover)
state: done
phase: ARCHIVED
merged_to_main_at: 2026-05-21
merged_via_squash_commit: fa921711
archived_at: 2026-05-21
audit_verdict: APPROVED
audit_cycle: 3 iterations (cap 3 reached, succeeded)
audit_artifacts: 06-audit/CHECKPOINTS.md + 06-audit/T-mk-*-review.md (13) + 06-audit/gherkin-matrix-{backend,frontend}.md + gate-output.json (audit-3)
last_artifact: T-mk-fe-7-result.md (Wave 6 closure)
last_modified: 2026-05-20
all_tickets_pushed_at: 2026-05-20
build_summary:
  tickets_pushed: 13                                     # T-mk-be-{1..6} + T-mk-fe-{1..7}
  validators_green_local: 17/21                          # 4 DEFERRED (Chromatic + Playwright E2E + Axe + Lighthouse — infra/CI gating)
  validators_deferred_ci:
    - visual_regression_bowtie_svg::chromatic            # CHROMATIC_PROJECT_TOKEN missing local — Chris ratifies baselines on merge
    - e2e_smoke_marketing                                # Turbopack dev server connection instability under concurrent Playwright load (learning 2026-05-20)
    - visual_a11y_axe                                    # idem stack stability
    - visual_perf_budget_lighthouse                      # idem
  tests_total: 700+ unit + integration GREEN (BE+FE)     # marketing module 111/111 BE + 700+ FE suite
  arch_fitness: 270/270 BE + 42/42 FE GREEN
  loc_implementation: ~5000 (estimated) across 26 commits (f0e395e..258a42f)
phase_d_local_coverage:                                  # /dev-team Step 4.5 pre-handoff gate
  scenarios_in_spec: 4                                   # SC-MK-01..04 in 01-spec-extract.md
  scenarios_in_gherkin_coverage: 4                       # all 4 covered across multiple tickets (17 ticket entries)
  status: PASS                                           # all scenarios mapped to ≥1 test
learning_emitted:
  - vitalia/docs/learnings/2026-05-20-docker-frontend-ram-turbopack-issue.md (promotable: candidate)
ratified_by_chris: true
spawned_at: 2026-05-17
spawned_by: /pm-vitalia (split decision post /architect ready package)
parallel_safe: true
ola_assigned: 2
ola_rationale: "Reuso simple Lucas tools ya shipped. NO usar nicolify/growth-studio (Chris 2026-05-20 ratificó)."
ticket_subset_inherited: [T-marketing-1, T-marketing-2, T-marketing-3, T-marketing-4, T-marketing-5, T-marketing-6, T-marketing-7, T-marketing-8]
ticket_subset_refreshed: [T-mk-be-1, T-mk-be-2, T-mk-be-3, T-mk-be-4, T-mk-be-5, T-mk-be-6, T-mk-fe-1, T-mk-fe-2, T-mk-fe-3, T-mk-fe-4, T-mk-fe-5, T-mk-fe-6, T-mk-fe-7]
ready_package_version: v1.0
blocker_dependencies: []                     # infra-cross-cutting DONE
side_story_blockers: []                      # vitalia-copilot-tools-impl ya DONE 2026-05-18 (Lucas tools shipped)
preflight_gates_required:
  - clerk_test_token_fresh_and_webhook_secret_configured     # GREEN
  - clerk_test_users_3_created                                # GREEN
  - playwright_storage_state_generated                        # GREEN
  - playwright_smoke_suite_green_23_specs                     # GREEN (36/36 actual)
  - promotion_proposal_core_platform_extensions_slice_1_migrated  # GREEN (v0.4.0 migrated 2026-05-20)
priority: high
estimated_dev_weeks: 3-4
architect_refresh_date: 2026-05-20
architect_model: claude-opus-4-7
next_action: "/auditor toma story para Conv 3 review+merge (AUTO-HANDOFF default post 2026-05-18). Lee T-mk-*-result.md + 06-audit/ + ejecuta Phase D gherkin verification matrix + CHECKPOINTS.md C1-C5. NO arrancar nueva story hasta state=done."

# Schema v2 migration (cement 2026-05-27)
release: F0   # release ID · ver releases/
cap_target: lucas-stage-recommendations   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-slice-1-marketing — checkpoint

## Goal

Ruta `/marketing` Bowtie salud 5 stages: Bowtie SVG pixel-invariante + Lucas StageRecommendations protagonista 3 cards top per stage + AttributionMatrixWidget Stage Reserva (4 origins) + ReferralsWidget Stage Expansión + Meta+Google APIs sync simplificado read-only Slice 1 + UTM tracking lead→origin.

## ★ Decisión Chris 2026-05-20: NO usar growth-studio Nicolify

Nicolify `frontend/src/features/growth-studio/` tiene arquitectura diferente (progressive loading 4 tiers, stage services, channel registry compleja, 13 hooks, 8 endpoints separados, etc.) NO compatible con el patrón vitalia más simple. Build de vitalia/marketing es NUEVO desde cero usando como referencia el mockup HTML + tokens cementados + Lucas tools ya shipped.

## Mockup heredado (SSoT visual)

`02-design-ui-mockup.html` — copia del parent ratificado Chris 2026-05-17. Build respeta paleta 4+1 colores + chat-RIGHT rail + sidebar progresivo v3. Bowtie SVG es el componente visual central pixel-invariante.

## Reuso explícito (Slice 1) — NO growth-studio

| Surface | Reuso de | Razón |
|---|---|---|
| FE Bowtie SVG component | Promote scaffold `vitalia/frontend/src/components/shared/marketing/MarketingBowtieSVG.tsx` → feature-scoped + real impl | Build simple SVG + Tailwind, no FSD-Lite legacy growth-studio |
| FE Lucas recommendations cards | Promote scaffold `vitalia/frontend/src/components/shared/lucas-recommendations/` → feature-scoped + real impl | Build simple, scaffold-promoted pattern |
| FE AttributionMatrix widget | Promote scaffold `vitalia/frontend/src/components/shared/attribution/` | idem |
| FE Channels viewport | Promote scaffold `vitalia/frontend/src/components/shared/channels/` | idem |
| FE Referrals widget | NEW (sin scaffold previo) — consume `LucasReferralsService` ya shipped | NEW Slice 1 |
| BE Lucas tools | `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/{compute_attribution_matrix,compute_referrals_leaderboard,compute_stage_recommendation}.py` (ya shipped 2026-05-18) | Reuso directo consumer-only |
| BE Lucas application services | `LucasStageRecommendationService` + `LucasAttributionService` + `LucasReferralsService` + `LucasOrchestratorService` (ya shipped) | Reuso directo via Python import |
| BE cron envelope | `luana_core_platform.workers.cron_envelope` (engine v0.4.0 migrated 2026-05-20) | Engine consume |
| BE dual-scope repo | `luana_core_platform.repositories.compound_scope_repository.CompoundScopeRepositoryBase` (engine v0.4.0) con `scope_field="clinic_id"` | Engine consume |
| BE Meta + Google APIs OAuth | `vitalia/backend/src/modules/vitalia/connections/{meta_ads,google_ads}/adapter.py` (NEW Slice 1 + EP-8 registry) | Brand-local con Extension SDK |

## Ready package artifacts (v1.0)

| Artifact | Path | Purpose |
|---|---|---|
| 01-spec-extract.md | `vitalia/docs/product/stories/vitalia-slice-1-marketing/01-spec-extract.md` | Spec scoped a marketing route — gherkin SC-MK-01..04 + JTBD + acceptance A1-A10 |
| 02-design-ui.md | idem path | Design notes — refresh from mockup HTML + estados + breakpoints + a11y + tokens map + visual baselines list |
| 02-design-ui-mockup.html | idem path | SSoT visual heredado parent (Chris ratificó 2026-05-17) |
| 03-arch.md | idem path | Consolidated full-stack architecture index |
| 03-arch-be.md | idem path | BE sub-arch — DDD layers + 4 tables + 10 endpoints + 4 cron jobs + OAuth adapters + Extension SDK EP-8 |
| 03-arch-fe.md | idem path | FE sub-arch — FSD-Lite layout + TS types + nuqs URL state + React Query hooks + Zustand store + Storybook |
| 03-arch-agentic.md | idem path | Agentic sub-arch — consumer-only of Lucas stack, NO new tools/personas/goldens |
| 04-validators.yaml | idem path | ★ CRITICAL — 6 non_functional + 10 functional + 5 visual + 0 agentic_eval gates `must_pass: true` |
| 05-guidelines.md | idem path | Patterns required/forbidden + files in scope + skills/rules to load + anti-patterns specific to marketing |
| 06-tickets.yaml | idem path | 13 tickets DAG (6 BE + 7 FE) wave-1..wave-6 + gherkin_coverage[] per ticket |
| HANDOFF-cross-story-updates.md | idem path | Deltas to apply to global `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md` at `/pm-vitalia` Fase F MERGE |

## Side stories paralelas relevantes

- `vitalia-copilot-tools-impl` — ya DONE 2026-05-18, Lucas tools shipped. Consumer-only access this story.
- Ninguna otra side story bloquea.
- Ola 2 parallel: `vitalia-slice-1-pipeline` (separate worktree).

## HANDOFF-cross-story coordination

Marketing + pipeline (Ola 2) comparten Lucas StageRecommendations cards (mismo backend tool, diferente render). Ver `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md` + `HANDOFF-cross-story-updates.md` (deltas to apply at merge).

## Story closure gate cement (per .claude/rules/story-closure-gate.md)

Default forward-motion:
1. `/dev-team` cierra all GREEN tickets → state `developing → developed` + AUTO-HANDOFF `/auditor`
2. `/auditor` cierra APPROVED → state `developed → reviewing → done` + AUTO-HANDOFF `/pm-vitalia` Fase F MERGE
3. `/pm-vitalia` Fase E DOCS + Fase F MERGE writes `07-merge.md` (5 secciones cementadas) + capability update + archive story to `vitalia/docs/archive/2026/stories/vitalia-slice-1-marketing/` (R2 cement)

No `defer_audit: true` requested. WIP cap: `developing ≤ 1` per worktree (Ola 2 parallel `/pipeline` is separate worktree per parallel-safety.md D2).

## Bitácora

- 2026-05-17 spawned: split decision Chris post /architect ready package mega-story.
- 2026-05-20 REPLAN: Ola 2 paralela con pipeline. growth-studio NO reusar (Chris ratificó arch diferente). vitalia-copilot-tools-impl unblock removido (ya done).
- 2026-05-20 /architect refresh ready package v1.0 produced. Pre-flight gates GREEN. Engine extensions (cron_envelope + CompoundScopeRepositoryBase) migrated 2026-05-20 v0.4.0. state=refined → ready. AWAITING /dev-team picks T-mk-be-1 wave-1.
