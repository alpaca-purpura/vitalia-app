---
story_id: vitalia-slice-1-pipeline
outcome: vitalia-mvp-ui-foundation
parent_spec: vitalia-ux-discovery (archived 2026-05-20 — inheritance carryover)
state: dropped                                              # paradigm v4: 'superseded' no existe · usar dropped con superseded_by
superseded_by: vitalia-fase2-adrian-embudo                  # ★ refactor 2026-05-22 paradigma shell-organism
dropped_at: 2026-05-22
superseded_at: 2026-05-22
superseded_reason: "Paradigma shell-organism agéntico cementado 2026-05-22 reemplaza outcome v1.0 slice-based por outcome v2.0 fase-based. Capacidades pipeline preservadas en F2-S4 vitalia-fase2-adrian-embudo (Kanban|Lista toggle + 6 stages dental customizable + lead detail N3-dyn workspace). Cambios: ownership Adrián tab Vender · ruta `(shell-organism)/adrian/embudo` · 6 stages dental defaults (interesado · calificando · considerando · listo · reservado · decidio-no) versus 6 anteriores (similar) · @dnd-kit/core para DnD · screening Lucas ya shipped consumido sin cambios. Side payment-adapter-mvp preservado dep."
phase: SUPERSEDED
last_artifact: 02-design-ui-mockup.html (legacy · reemplazado por dual-mode-shell.html + Design Contract)
last_modified: 2026-05-22
ratified_by_chris: true
ratified_refactor_by_chris: true
spawned_at: 2026-05-17
spawned_by: /pm-vitalia (split decision post /architect ready package)
parallel_safe: true
ola_assigned: null
ola_rationale: "REPLACED — outcome v2.0 fase-based"
ticket_subset_inherited: []                                 # preserved in F2-S4 spec
blocker_dependencies: []
side_story_blockers: [vitalia-payment-adapter-mvp]
priority: high
estimated_dev_weeks: 2-3
next_action: "NONE — superseded por vitalia-fase2-adrian-embudo. Proceder con F2-S4 cuando Fase 1 done + payment-adapter-mvp shipped."

# Schema v2 migration (cement 2026-05-27)
release: F0   # release ID · ver releases/
cap_target: null   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-slice-1-pipeline — checkpoint

## Goal

Ruta `/pipeline` Kanban venta consultiva ética Slice 1 (Batch 3 cementado): 6 stages (Interesado · Calificando · Considerando · Listo · Reservado depósito · Decidió no) + atribución agentic per stage + DnD manual + auto-progression event-driven + screening clínico Lucas NEW + diferenciador MUST #2 badge depósito 30%.

## Mockup heredado (SSoT visual)

`02-design-ui-mockup.html` — copia del parent ratificado Chris 2026-05-17. Build respeta paleta 4 colores + chat-RIGHT rail + sidebar progresivo v3.

## Reuso explícito (Slice 1)

| Surface | Reuso de | Razón |
|---|---|---|
| FE kanban board | `nicolify/frontend/src/features/closer-studio/` (board kanban + detail panel) | closer-studio es el patrón pipeline Nicolify equivalente |
| FE rail copilot derecha | `nicolify/frontend/src/features/copilot/` | rail unificado cross-brand |
| BE Sale + Lead stages domain | `core/luana-core-crm/src/luana_core_crm/domain/sale.py` + `lead.py` | engine domain entities |
| BE StageAdvanced event | `core/luana-core-events/` domain event bus | engine event flow |
| BE PHI dual-filter | `core/luana-core-platform/repositories/CompoundScopeRepositoryBase` (post lift) | reemplaza vitalia/_shared |
| Lucas screening tool | `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_stage_recommendation.py` (ya shipped) | reuso directo |
| BE rate limiting | `core/luana-core-billing/RateLimiter` | engine ya consumido |

## Side stories paralelas relevantes

- `vitalia-payment-adapter-mvp` — BLOQUEA badge depósito 30%. Debe estar state≥developed antes Ola 2.
- `vitalia-copilot-tools-impl` — ya DONE 2026-05-18 (Lucas screening tool shipped).

## HANDOFF-cross-story coordination

Pipeline + inbox comparten contratos Lead + Conversation (provistos por Ola 1 inbox). Pipeline + marketing comparten Lucas stage_recommendations. Ver `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation/HANDOFF-cross-story.md`.

## Bitácora

- 2026-05-17 spawned: split decision Chris post /architect ready package mega-story
- 2026-05-20 REPLAN: Ola 2 asignada (paralela con marketing). Pre-flight gates + side payment-adapter-mvp documentados. vitalia-copilot-tools-impl unblock removido (ya done).
- **2026-05-22 SUPERSEDED:** paradigma shell-organism agéntico. Capacidades migradas a `vitalia-fase2-adrian-embudo` (F2-S4). Owner Adrián tab Vender. Ver `vitalia/docs/product/stories/vitalia-fase2-adrian-embudo/checkpoint.md`. Outcome refactor v2.0 cementado.
