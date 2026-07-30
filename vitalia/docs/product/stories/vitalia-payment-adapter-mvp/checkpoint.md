---
story_id: vitalia-payment-adapter-mvp
state: refined                                       # ★ spec v3 ratificado Chris 2026-05-22T14:30Z (heredado de sesión efímera, absorbido 2026-05-22T15:30Z)
last_artifact: 01-spec.md (v3)
last_modified: 2026-05-22
ratified_by_chris: true                              # ★ spec v3 ratificado 2026-05-22T14:30Z (4 batches de ratificación)
ratified_at: 2026-05-22T14:30:00Z
spawned_at: 2026-05-17
transitioned_at: 2026-05-22T14:30:00Z
last_session_resume: 2026-05-22T15:30:00Z            # absorción wip/vitalia ← ephemeral worktree
spawned_by: /pm-vitalia
parallel_safe: true
blocked_reason: "★ TIER reclassified 2026-05-27 (audit sweep): NO es TIER 0 gating ALL Fase 2 — es TIER 2 (post agendamiento real con stubs MSW). valeria-agenda DONE prueba que Option A stubs es viable para unblock TIER 1 booking flow. Adrian-embudo (stage reservado) + adrian-propuestas (payment plans) son TIER 3 que SÍ requiere TIER 2 real. config-cuenta plan Luana es TIER 7 DEFERRED. SSoT orden: vitalia/docs/product/outcomes/vitalia-fase-2-tier-roadmap.md § TIER 2. Architect spawn deferido hasta TIER 1 (config-onboarding + valeria-pacientes + lisa-landing-public) developed."
priority: high
estimated_dev_weeks: 3-4                              # bump 2026-05-22 por multi-gateway scope (MercadoPago + Stripe MVP)
parent_spec: "vitalia/docs/product/stories/vitalia-ux-discovery/03-arch-be.md § Payment Provider Adapter + EP-8 payment_adapters registry"
cross_phase_2_consumers:                              # ★ explicita FE consumers que § 1.5 spec v3 menciona genéricamente
  - vitalia-fase2-valeria-agenda                      # F2-S1 — subform Cobrar saldo inline
  - vitalia-fase2-adrian-embudo                       # F2-S4 — stage transition reservado dispara payment
  - vitalia-fase2-adrian-propuestas                   # F2-S6 — payment plans Stripe/MP subscription
  - vitalia-fase2-config-cuenta                       # F2-S20 — Plan Luana checkout (meta-billing)
gateway_scope_cemented_2026_05_22:                    # ★ decisiones tácticas ratificadas Chris (preservadas de sesión efímera)
  decision: multi_gateway_strategy_from_mvp
  ratified_by: chris
  ratified_at: 2026-05-22T13:50:00Z
  ratified_via: /pm-vitalia AskUserQuestion
  live_adapters_mvp: [mercadopago, stripe]            # ambos LIVE MVP
  optional_slice_2: [culqi]                            # PE-only fallback, defer
  selection_mechanism: "tenant.payment_gateway en config (per-tenant fixed); paciente NO elige en checkout"
  failure_recovery: "downgrade graceful retry 3x con tenacity backoff 1s/4s/16s → escalate admin via inbox"
  refund_scope: "admin panel only (NO Adrián tool refund_booking)"
  confirmation_notif: "Adrián auto WhatsApp event-driven + recordatorio 24h"
  webhook_security: "HMAC + timestamp 5min window (per hipaa-lite.md)"
  idempotency: "keys per booking_id + cron sweeper dup detection"
  currency_resolution: "tenant.country lookup table (no override per-booking)"
  rationale: "EP-8 payment_adapters battle-tested con 2+ adapters live día 1; cobertura LATAM (MP) + US/EU (Stripe) desde MVP sin re-arquitectura"
  cost: "estimated_dev_weeks: 1-2 → 3-4 (x2 sandbox credentials + x2 integration tests + Strategy pattern wiring)"
ratification_details:                                 # ★ batches de ratificación preservados de sesión efímera
  spec_version: v3
  scenarios_ratified: 14   # 6 happy + 1 negative + 4 edge + 3 adversarial
  sections_ratified:
    - "§ 1 Context"
    - "§ 1.5 Backend-only + FE consumers map (alignment shell-organism P5)"
    - "§ 2 Goal"
    - "§ 3 Out-of-scope (3 sub-secciones expandidas)"
    - "§ 4 Architecture intent (handoff /architect)"
    - "§ 5 Acceptance criteria (14 scenarios)"
    - "§ 6 Cross-cutting requirements"
    - "§ 7 Open questions remanentes (ninguna)"
    - "§ 8 Verification commands"
shell_organism_alignment:                             # ★ alignment paradigm 2026-05-21 preservado de sesión efímera
  alignment_check_2026_05_21: PASSED
  paradigm_p5_respected: true                         # backend invariante al paradigma agéntico FE
  fe_consumers_per_spec_§1.5_match_cross_phase_2_consumers: true   # § 1.5 spec v3 = cross_phase_2_consumers verbatim
next_action: "Próxima sesión retoma con `/architect <brand>: vitalia <story-id>: vitalia-payment-adapter-mvp` para producir 03-arch + 04-validators + 05-guidelines + 06-tickets. Recommended trigger: cuando F1 (Fase 1) entre `developing` — para que `developed` esté ANTES de F2-S1/F2-S4/F2-S6 arrancar. Spec v3 ratificado covers backend-only + FE consumers map § 1.5 alineado con cross_phase_2_consumers (paradigm shell-organism P5)."

# Schema v2 migration (cement 2026-05-27)
release: F3   # release ID · ver releases/
cap_target: null   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-payment-adapter-mvp — checkpoint

## Goal

Wirear al menos 1 payment gateway (de los 3 scaffold en backend Vitalia Story 11) para que el booking prepaid 30% funcione end-to-end:

- Backend `vitalia/backend/src/modules/vitalia/payment/` tiene scaffold para 3 adapters (per 00-research.md audit)
- Webhooks ya operativos
- Falta: implementación concreta de los adapters elegidos (MercadoPago + Stripe MVP) + flow checkout link + confirmación

## Scope

### In-scope (cementado 2026-05-22 — multi-gateway Strategy MVP)
- Strategy pattern EP-8 con 2 adapters live: **MercadoPago** (cobertura AR/PE/MX/CO/CL/BR) + **Stripe** (US/EU)
- Tenant elige gateway en config (`tenant.payment_gateway`, fijo per-tenant; paciente NO elige en checkout)
- Implementar ambos adapters conforme contract EP-8 (`payment_adapters`)
- Flow: agenda crear turno → genera checkout link via adapter del tenant → enviar paciente WhatsApp via Adrián → paciente paga → webhook confirma → status turno actualiza a `paid_deposit`
- Webhook HMAC signature + timestamp window 5min validation (per hipaa-lite.md encryption in transit)
- Idempotency keys per booking_id + cron sweeper detecta dups
- Failure recovery: downgrade graceful retry 3x con tenacity backoff 1s/4s/16s → escalate admin via inbox
- Refund: solo admin panel (NO Adrián tool `refund_booking`)
- Confirmation notif: Adrián auto WhatsApp event-driven + recordatorio 24h
- Currency: `tenant.country` lookup table (no override per-booking)
- Tests: integration test contra MercadoPago sandbox + Stripe sandbox + E2E flow paciente

### Out-of-scope (defer Slice 2+)
- **Culqi PE adapter** (defer Slice 2 si métrica adopción PE lo justifica)
- Selección runtime de gateway por paciente (siempre per-tenant config)
- Pagos finales post-tratamiento (solo depósito 30% MVP)
- Reembolsos automáticos por reglas (manual via panel admin OK)
- Multi-currency dentro de un mismo tenant (tenant.currency siempre — Stripe negocia local del tenant, no convierte)
- dLocal, Niubiz, otros gateways LATAM secundarios

## Dependencies (post 2026-05-22 paradigma shell-organism — Fase 1+2)

Consumers cruzados Fase 2 (FE consumers, backend invariante per P5):
- **vitalia-fase2-valeria-agenda** (F2-S1) — subform "Cobrar saldo" inline en AppointmentDrawer
- **vitalia-fase2-adrian-embudo** (F2-S4) — stage transition `* → reservado` dispara payment deposit request
- **vitalia-fase2-adrian-propuestas** (F2-S6) — payment plans Stripe (subscription) + MP (cuotas)
- **vitalia-fase2-config-cuenta** (F2-S20) — Plan Luana checkout (meta-billing self-service)

Service blockers: Backend Vitalia Story 11 ya tiene scaffold (3 adapters listos para wirear).

## Bitácora

- 2026-05-17 spawned: idea formal abierta por /pm-vitalia para tracking explícito. Diferenciador #2 MUST MVP (booking prepaid 30%) depende de esta story.
- 2026-05-22 cross-story deps update (sesión wip/vitalia): consumers Fase 2 enumerados (4 historias). Outcome refactor v2.0 documentado: `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md`.
- 2026-05-22T13:50Z resume sesión paralela efímera: worktree `luana-vitalia-vitalia-payment-adapter-mvp` (branch `wip/vitalia-vitalia-payment-adapter-mvp` born from origin/main@fa92171). Sesión principal `luana-vitalia/` continúa refinando Fase 1 en paralelo.
- 2026-05-22T13:50Z Chris ratificó **gateway scope multi-gateway Strategy desde MVP** via `/pm-vitalia` AskUserQuestion. Adapters live MVP: MercadoPago + Stripe. Culqi defer Slice 2. Selection per-tenant config. Bump `estimated_dev_weeks: 1-2 → 3-4`.
- 2026-05-22T14:00Z `/po` ejecutó bootstrap → descubrió que la story está **madurando scaffolds existentes** (no construyendo de cero): caps live `payment-gateways-latam-recurring` (3 adapters 2k/11k/18k) + `prepaid-booking-advisory-locks` (7 endpoints booking) + `adrian-3-tools-mvp` (Adrián `send_payment_link` ya wired). EP-8 es `channel_adapter_register` signature-only v0.1.0 (NO payment) → architect resuelve EP wiring strategy.
- 2026-05-22T14:15Z `/po` envió batch 1 (4 preguntas tácticas). Chris ratificó: scope=madurar scaffolds, failure recovery=downgrade graceful 3x retry → admin escalate, refund=admin panel only (no Adrián tool), notif confirma=Adrián auto WhatsApp + recordatorio 24h. Decisiones implícitas cerradas por discovery: (a) Culqi defer formal, (b) currency=tenant.country lookup, (d) webhook window=5min hipaa-lite.
- 2026-05-22T14:20Z `/po` redactó `01-spec.md` v1 con 14 scenarios Gherkin (6 happy + 1 negative + 4 edge + 3 adversarial). Cross-cutting hipaa-lite + tenant isolation + currency + failure recovery + observability.
- 2026-05-22T14:25Z Chris ratificó scenarios 6+8 (happy + edge/adversarial) pero levantó 2 dudas críticas: (1) ¿cómo probar E2E si FE no existe? (2) ¿sintonía con shell-organism paradigm 2026-05-21?
- 2026-05-22T14:28Z `/po` investigó shell-organism (`vitalia/docs/product/stories/vitalia-shell-organism/00-session-baseline.md`). Hallazgos: P5 cementa "Backend DDD NO se rearma según agentes". Esta story es backend-only — FE consumers están en stories Fase 1/2 paralelas (Valeria/Agenda + Adrián/Inbox + Configurar/Conexiones).
- 2026-05-22T14:30Z `/po` escribió spec v2 con § 1.5 NEW (backend-only + FE consumers map) + § 3 expandido (3 sub-secciones out-of-scope) + § 10 changelog. Spec evolucionó a v3 con 14 scenarios cementados AI-resistant. **Chris ratificó v3** → transition refining→refined.
- 2026-05-22T14:30Z Chris pidió **defer /architect handoff** (no por bloqueo — quiere alinear con Fase 1 specs paralelas antes de comprometer architecture).
- 2026-05-22T15:00Z **HALLAZGO CRÍTICO durante cierre worktree efímero** — sesión wip/vitalia ya había re-contextualizado la story post-bigbang shell-organism 2026-05-21 con `cross_phase_2_consumers` paradigm. Decisión cementada Chris: NO merge directo a main (conflict cross-session); crear HANDOFF doc + cleanup worktree manual + dejar branch wip/* vivo 30d para cherry-pick selectivo desde wip/vitalia.
- 2026-05-22T15:00Z HANDOFF doc creado en `vitalia/docs/product/stories/vitalia-payment-adapter-mvp/HANDOFF-to-luana-vitalia-2026-05-22.md` con cherry-pick instructions Variante A/B/C.
- 2026-05-22T15:30Z **ABSORCIÓN wip/vitalia ← worktree efímero** (Variante A cherry-pick selectivo):
  - Importados: `01-spec.md` v3 + `HANDOFF-to-luana-vitalia-2026-05-22.md`
  - Descartado: brand checkpoint mods (cita stories REFACTORED slice-1-pipeline/inbox/agenda)
  - Checkpoint story reconciliado: preserva paradigm Fase 2 (`cross_phase_2_consumers` + `phase: SPEC_RATIFIED_DEFERRED_ARCHITECT`) + decisiones tácticas ratificadas Chris (`gateway_scope_cemented_2026_05_22` + `ratification_details` + `shell_organism_alignment`) + bitácora completa
  - State bump: `refining → refined` heredado del spec v3 ratificado (Chris ratification stands; § 1.5 backend-only spec ya cumple paradigm P5 — los 4 `cross_phase_2_consumers` son FE consumers explícitos que § 1.5 menciona genéricamente)
  - Worktree efímero + branch local + branch remoto: cleanup completo
