---
story_id: vitalia-slice-1-fidelizacion
outcome: vitalia-mvp-ui-foundation
parent_spec: vitalia-ux-discovery (archived 2026-05-20 — inheritance carryover)
state: done                                    # ← DEVELOPED → REVIEWING → DONE 2026-05-20 (auditor APPROVED iter 3 BE post F1+F2 + iter 2 FE + merged to main)
phase: MERGED                                  # 07-merge.md written + capabilities updated + archived
preflight_gates_status:                        # ★ 2026-05-20 verificación
  clerk_test_token_fresh_and_webhook_secret_configured: GREEN
  clerk_test_users_3_created: GREEN
  playwright_storage_state_generated: GREEN    # vitalia/frontend/playwright/.clerk/user.json via clerk.setup.ts ticket strategy
  playwright_smoke_suite_green_local: GREEN    # 36/36 specs PASS 9.2min
  promotion_proposal_core_platform_extensions_slice_1_migrated: GREEN
preflight_gates_deferred_followup:
  playwright_smoke_suite_green_live: DEFERRED
  playwright_mobile_smoke_green: DEFERRED
  playwright_a11y_smoke_green: DEFERRED
last_artifact: 06-tickets.yaml + HANDOFF-cross-story-updates.md (architect refresh 2026-05-20)
last_modified: 2026-05-20
ratified_by_chris: true
spawned_at: 2026-05-17
spawned_by: /pm-vitalia (split decision post /architect ready package)
parallel_safe: true
ola_assigned: 1
ola_rationale: "Auto-contenida, sin side blockers. Reuso fuerte nicolify/campaigns-lite + nicolify/notifications + core/luana-core-campaigns workers + cron_envelope core post lift."
ticket_subset_inherited: [T-fidelizacion-1, T-fidelizacion-2, T-fidelizacion-3, T-fidelizacion-4, T-fidelizacion-5, T-fidelizacion-6, T-fidelizacion-7]
ticket_subset_final: [T-1, T-2, T-3, T-4, T-5, T-6, T-7, T-8, T-9, T-10, T-11, T-12, T-13, T-14, T-15, T-16]   # 16 tickets cementados ready package
blocker_dependencies: []                     # infra-cross-cutting DONE 2026-05-18
side_story_blockers: []
preflight_gates_required:
  - clerk_test_token_fresh_and_webhook_secret_configured
  - clerk_test_users_3_created
  - playwright_storage_state_generated
  - playwright_smoke_suite_green_23_specs
  - promotion_proposal_core_platform_extensions_slice_1_migrated
priority: high
estimated_dev_weeks: 2-3
estimated_total_tickets: 16
agentic_opus_required_tickets: [T-9, T-10]                  # R23 hard — agentic production_code=true
next_action: "Pre-flight gates GREEN → /dev-team picks T-1 (migrations). DAG Stage 1 → 8 per 06-tickets.yaml. Auto-handoff /auditor al cierre state=developed."

# Schema v2 migration (cement 2026-05-27)
release: F0   # release ID · ver releases/
cap_target: nps-tracking   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-slice-1-fidelizacion — checkpoint

## Goal

Ruta `/fidelización` Slice 1: 4 patrones re-engagement automatizado (multi-sesión + follow-up médico + mantenimiento periódico + ausencia prolongada) + NPS reducido stat card secundaria + 6 cron jobs scheduled + 5 templates Meta-approved. Detalle deferred a Slice 2: dashboard NPS completo (4 KPIs + chart + detractor flow + Google Reviews + birthday cron + doctor view).

## Mockup heredado (SSoT visual cementado Chris 2026-05-17)

`02-design-ui-mockup.html` — copia del parent ratificado. Build respeta paleta 4 colores + chat-RIGHT rail + sidebar progresivo v3 + tabs verticales 5 patrones.

## Ready package (post /architect refresh 2026-05-20)

| Artifact | Path | Status |
|---|---|---|
| Spec extract | `01-spec-extract.md` | ✓ |
| Design UI | `02-design-ui.md` + `02-design-ui-mockup.html` | ✓ |
| Arch consolidated | `03-arch.md` | ✓ |
| Arch BE | `03-arch-be.md` | ✓ |
| Arch FE | `03-arch-fe.md` | ✓ |
| Arch Agentic | `03-arch-agentic.md` | ✓ |
| Validators | `04-validators.yaml` (4 categories × ~25 validators) | ✓ |
| Guidelines | `05-guidelines.md` (patterns required/forbidden + files + skills + 25 decisions) | ✓ |
| Tickets | `06-tickets.yaml` (16 tickets DAG Stage 1-8) | ✓ |
| HANDOFF cross-story | `HANDOFF-cross-story-updates.md` | ✓ |

## Reuso explícito (Slice 1)

| Surface | Reuso de | Razón |
|---|---|---|
| FE re-engagement cards + segments | `nicolify/frontend/src/features/campaigns-lite/` | Token adapter — pattern Nicolify equivalente |
| FE notification dispatch | `nicolify/frontend/src/features/notifications/` | Reference pattern rendering + hooks shape |
| BE workers re-engagement scheduling | `core/luana-core-campaigns/workers/{scheduler_tick,execution_task,segment_refresh_tick,audit_retention_task}.py` | Engine batch reference — fidelización crons custom invocation siguen patrón |
| BE cron envelope (idempotency + OTel + audit + sentry) | `core/luana-core-platform/workers/cron_envelope` (post lift 2026-05-20) | Reemplaza vitalia/_shared/workers/base.py legacy |
| BE PHI dual-filter queries | `core/luana-core-platform/repositories/CompoundScopeRepositoryBase` (post lift) | Reemplaza vitalia/_shared/repositories/phi_repository.py legacy |
| BE NPS + ReEngagementTriggered events | `core/luana-core-events/outbox/adapter_bus` (default post 2026-04-30) | Engine event bus |
| Adrián runtime | `core/luana-core-sales-agent/` (read-only via service inject) | NO modify engine |
| Lucas tool simple ReAct | `core/luana-core-llm/providers/litellm` (canonical post 2026-05-06) | LLM dispatch reasoning |

## Side stories paralelas relevantes

Ninguna — `/fidelización` arranca sin side blockers.

## HANDOFF-cross-story coordination

Ola 1 fidelización **PRODUCE** (consumido por sibling Olas 1+):
- NPS schema (NPSRowDTO + NPSSummaryResponse Zod + TS) → /inbox tag detractor chip
- Endpoints `/api/v1/vitalia/fidelization/*` (11 endpoints)
- Domain events `ReEngagementTriggered + NPSScoreCollected + PatientOptedOut + PatientPausedReEngagement`
- BE module Public API + FE feature Public API + `<NPSTagBadge>` shared cross-feature

Ola 1 fidelización **CONSUME**:
- Engine columns (appointments + offers + patients post Ola 0/promotion proposals)
- `cron_envelope` + `CompoundScopeRepositoryBase` (engine pre-flight gate `2026-05-20-core-platform-extensions-slice-1`)
- Adrián runtime (engine sales-agent) via service inject
- WhatsApp Business API (5 templates Meta-approved)

Ola 1 inbox + Ola 1 fidelización NO comparten contratos directos UI. Sí comparten engine pre-flights (cron_envelope + CompoundScopeRepositoryBase) — refactor cross-story esperable cuando lift merge.

Ver `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md` para coordinación full Slice 1 + `HANDOFF-cross-story-updates.md` (este story package) para diff append-only.

## Bitácora

- 2026-05-17 spawned: split decision Chris post /architect ready package mega-story
- 2026-05-20 REPLAN: Ola 1 asignada paralela con inbox. Pre-flight gates + lift core requirements documentados.
- **2026-05-20 /architect refresh ready package:** 7 artifacts cementados (01-spec-extract, 02-design-ui, 03-arch consolidated + 3 sub-archs, 04-validators, 05-guidelines, 06-tickets, HANDOFF-cross-story-updates). 16 tickets DAG Stage 1-8. Agentic tickets T-9 + T-10 flagged R23 Opus 4.7 required. state: refined → ready. Awaiting pre-flight gates GREEN → /dev-team pickup T-1.
