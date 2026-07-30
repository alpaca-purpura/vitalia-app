---
story_id: vitalia-slice-1-agenda
outcome: vitalia-mvp-ui-foundation
parent_spec: vitalia-ux-discovery (archived 2026-05-20 — inheritance carryover)
state: dropped                                              # paradigm v4: 'superseded' no existe · usar dropped con superseded_by
superseded_by: vitalia-fase2-valeria-agenda                # ★ refactor 2026-05-22 paradigma shell-organism
dropped_at: 2026-05-22
superseded_at: 2026-05-22
superseded_reason: "Paradigma shell-organism agéntico cementado 2026-05-22 reemplaza outcome v1.0 slice-based por outcome v2.0 fase-based. Capacidades agenda preservadas en F2-S1 vitalia-fase2-valeria-agenda (calendario + drawer slot + subform cobrar saldo). Reuso conceptos: scheduling engine + payment-adapter + fiscal-emission preservado. Cambios: UI migrada a espacio shell-organism `(shell-organism)/valeria/agenda` · drawer pattern Shadcn Sheet · tokens vitalia (agent valeria color) · plan Fase 2 documentado en outcome v2.0."
phase: SUPERSEDED
last_artifact: 02-design-ui-mockup.html (legacy · reemplazado por mockup dual-mode-shell.html + Design Contract atomic design)
last_modified: 2026-05-22
ratified_by_chris: true
ratified_refactor_by_chris: true                            # post 2026-05-22 ratification
spawned_at: 2026-05-17
spawned_by: /pm-vitalia (split decision post /architect ready package)
parallel_safe: true
ola_assigned: null                                          # ya no aplica · paradigm shift
ola_rationale: "REPLACED — outcome v2.0 fase-based reemplaza Ola-based"
ticket_subset_inherited: []                                 # preserved in F2-S1 spec
blocker_dependencies: []
side_story_blockers: [vitalia-payment-adapter-mvp, vitalia-fiscal-emission-pe]  # mismas deps en F2-S1
priority: high
estimated_dev_weeks: 2-3
next_action: "NONE — superseded por vitalia-fase2-valeria-agenda. Proceder con F2-S1 cuando Fase 1 done + service-stories payment-adapter + fiscal-emission shipped."

# Schema v2 migration (cement 2026-05-27)
release: F0   # release ID · ver releases/
cap_target: null   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-slice-1-agenda — checkpoint

## Goal

Ruta `/agenda` Slice 1 (Batch 4 cementado): vista Semana default + 4 origins (sales_agent + walk_in + phone_manual + proactive_outbound) preservando atribución agentic + 3 capas cobranza (sheet inline + Nubefact boleta PE toggle + window.print() PDF) + Walk-in/Phone drawers NEW + DnD + modal fallback reschedule + 5 Extension SDK registries plugin-ready + 5 cron jobs + política reembolso 24h hardcoded.

## Mockup heredado (SSoT visual)

`02-design-ui-mockup.html` — copia del parent ratificado Chris 2026-05-17. Build respeta paleta 4 colores + chat-RIGHT rail + sidebar progresivo v3.

## Reuso explícito (Slice 1)

| Surface | Reuso de | Razón |
|---|---|---|
| FE calendar Semana view + DnD | Construir mix patterns nicolify/crm-hub (list+detail) + nicolify/closer-studio (DnD board) | NO hay equivalente directo Nicolify para calendar — mix patterns |
| FE drawer Walk-in / Phone | nicolify/closer-studio detail panel patterns | reuso drawer-pattern |
| FE rail copilot derecha | nicolify/frontend/src/features/copilot/ | rail unificado |
| BE Appointment + AvailabilitySchema + EventTypeSchema | `core/luana-core-scheduling/src/luana_core_scheduling/domain/` | engine domain entities |
| BE payment adapters (MercadoPago, Stripe, tokenized recurring) | `core/luana-core-channels/src/luana_core_channels/payment/{mercadopago_adapter,stripe_connect_adapter,tokenized_recurring_adapter}.py` | engine ya tiene adapters |
| BE cron envelope (recordatorios + 24h refund window + auto-cancel) | `core/luana-core-platform/workers/cron_envelope` (post lift) | reemplaza vitalia/_shared |
| BE PHI dual-filter (appointments + payment_events + fiscal_receipts PHI encrypted) | `core/luana-core-platform/repositories/CompoundScopeRepositoryBase` (post lift) | reemplaza vitalia/_shared |
| BE idempotency webhook payment/fiscal | `core/luana-core-idempotency/` `@idempotent` decorator | engine ya consumido |
| Side payment-adapter-mvp | `vitalia-payment-adapter-mvp` story shipped | provee cobranza saldo final |
| Side fiscal-emission-pe | `vitalia-fiscal-emission-pe` story shipped | provee Capa 2 Nubefact + CDR archive |

## Side stories paralelas relevantes

- `vitalia-payment-adapter-mvp` — BLOQUEA cobranza saldo. Refining en paralelo a Ola 1 (sesión actual arranca `/po draft`).
- `vitalia-fiscal-emission-pe` — BLOQUEA Capa 2 fiscal Nubefact PE. Refining en paralelo a Ola 1.

## HANDOFF-cross-story coordination

Agenda hereda contratos Lead + Customer + Conversation de Olas 1+2 (inbox + pipeline). Comparte payment + fiscal con side stories shipped. Ver `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation/HANDOFF-cross-story.md`.

## Bitácora

- 2026-05-17 spawned: split decision Chris post /architect ready package mega-story
- 2026-05-20 REPLAN: Ola 3 asignada (sola, más compleja). Pre-flight + lift core + side payment + side fiscal documentados.
- **2026-05-22 SUPERSEDED:** paradigma shell-organism agéntico cementado. Capacidades migradas a `vitalia-fase2-valeria-agenda` (F2-S1). Ver detalle: `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/checkpoint.md`. Outcome refactor v2.0 documentado en `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md` (CHANGELOG v2.0). 17 decisiones cementadas baseline shell-organism: `vitalia/docs/product/stories/vitalia-shell-organism/00-session-baseline.md`. State `superseded` (no `done` ni `dropped`) — preserva inheritance carryover de specs/UX para auditor referencia futura.
