---
story_id: vitalia-slice-1-inbox
outcome: vitalia-mvp-ui-foundation
parent_spec: vitalia-ux-discovery (archived 2026-05-20 — inheritance carryover)
state: done                                    # ← DEVELOPED → REVIEWING → DONE 2026-05-20 (auditor APPROVED iter 2 BE+FE + merged to main)
phase: MERGED                                  # 07-merge.md written + capabilities updated + archived
preflight_gates_status:                        # ★ 2026-05-20 verificación
  clerk_test_token_fresh_and_webhook_secret_configured: GREEN  # token regenerated via clerk CLI + webhook secret confirmed in .env.dev
  clerk_test_users_3_created: GREEN                            # dr.demo + recepcion + admin @vitalialat.com verified in Clerk + DB
  playwright_storage_state_generated: GREEN                    # vitalia/frontend/playwright/.clerk/user.json (9 cookies) via clerk.setup.ts ticket strategy (~10s)
  playwright_smoke_suite_green_local: GREEN                    # 36/36 specs PASS 9.2min (vitalia/frontend/playwright-report/)
  promotion_proposal_core_platform_extensions_slice_1_migrated: GREEN  # luana-core-platform 0.4.0 commit e8d3c04
preflight_gates_deferred_followup:             # non-blocking — registered for separate session
  playwright_smoke_suite_green_live: DEFERRED  # needs cloudflared tunnel verified + can run post-merge
  playwright_mobile_smoke_green: DEFERRED      # responsive specs included in smoke run actually
  playwright_a11y_smoke_green: DEFERRED        # axe scans non-blocking for Slice 1 build start
last_artifact: 06-tickets.yaml + HANDOFF-cross-story-updates.md + 05-guidelines.md + 04-validators.yaml + 03-arch-{be,fe,agentic}.md + 03-arch.md + 02-design-ui.md + 01-spec-extract.md (all emitted 2026-05-20)
last_modified: 2026-05-20
ratified_by_chris: true                       # replan 2026-05-20
spawned_at: 2026-05-17
spawned_by: /pm-vitalia (split decision post /architect ready package)
parallel_safe: true
ola_assigned: 1                                # Ola 1 (paralela con vitalia-slice-1-fidelizacion)
ola_rationale: "Auto-contenida, sin sub-blockers de side stories. Reuso fuerte nicolify/crm-hub + nicolify/copilot + nicolify/closer-studio."
ticket_count: 13                               # T-inbox-be-{1..6} + T-inbox-agentic-1 + T-inbox-fe-{1..7} + T-inbox-integ-{1..2}
blocker_dependencies: []                       # vitalia-slice-1-infra-cross-cutting ya DONE (2026-05-18)
side_story_blockers: []                        # ninguna
preflight_gates_required:
  - clerk_test_token_fresh_and_webhook_secret_configured
  - clerk_test_users_3_created                 # dr.demo + recepcion + admin
  - playwright_storage_state_generated
  - playwright_smoke_suite_green_23_specs
  - promotion_proposal_core_platform_extensions_slice_1_migrated  # cron_envelope + CompoundScopeRepositoryBase (verified migrated 2026-05-20)
priority: high
estimated_dev_weeks: 2-3
defer_audit: false                            # default forward-motion · auto-handoff /auditor at developed
next_action: |
  READY for /dev-team pickup. /dev-team consumes 06-tickets.yaml in DAG order:
    T-inbox-be-1 (domain) → T-inbox-be-2 (infra+migration) ‖ T-inbox-be-4 (connections)
    → T-inbox-be-3 (services) → T-inbox-agentic-1 (Opus tool) ‖ T-inbox-be-5 (API)
    → T-inbox-be-6 (extensions register) → T-inbox-fe-1 (FE scaffold)
    → T-inbox-fe-2 (hooks) → T-inbox-fe-3 (list+filters) → T-inbox-fe-4 (thread+segmented)
    → T-inbox-fe-{5,6} (composer+media+ActionReceipt ‖ Sheet+ActivityStream+ContactSidebar+ProactiveOutbound)
    → T-inbox-fe-7 (Storybook+arch test) → T-inbox-integ-{1,2}
  Verify pre-flight gates GREEN before pickup. All gherkin_coverage fields populated per ticket.
  Auto-handoff /auditor at state=developed (per .claude/rules/story-closure-gate.md).

# Schema v2 migration (cement 2026-05-27)
release: F0   # release ID · ver releases/
cap_target: inbox-tools-extensions   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-slice-1-inbox — checkpoint

## Goal

Ruta `/inbox` conversacional Slice 1 (Batch 2 cementado): segmented 3-modos "Adrián decide" + 6 filtros venta consultiva ética + audio IN Whisper STT + imagen IN stub + composer attach + Tools Sheet read-only + Activity Stream sticky + Action Receipts undo 5min + proactive outbound modal.

## Ready package (emitted 2026-05-20)

| File | Lines | Purpose |
|---|---|---|
| `01-spec-extract.md` | 331 | Recorte fiel del mega-spec parent acotado a /inbox. Gherkin SC-01..04 + microcopy + componentes mapping. |
| `02-design-ui.md` | 178 | Component tree + tokens + states + hooks + reuse mapping. Refers to `02-design-ui-mockup.html` as SSoT visual. |
| `02-design-ui-mockup.html` | 49KB | SSoT visual heredado parent (clickable state switcher 8 estados). |
| `03-arch.md` | 287 | Consolidated index · surface→builder→auditor mapping · existing systems audit (ALL EXTEND, zero NEW layers). |
| `03-arch-be.md` | 803 | Backend DDD · 4 tables + 4 domain entities + 6 events + 8 inbox endpoints + 4 crm endpoints + repos heredan CompoundScopeRepositoryBase. |
| `03-arch-fe.md` | 555 | FSD-Lite · components + hooks + nuqs URL state + PHI components + Storybook stories + E2E POM. |
| `03-arch-agentic.md` | 361 | R23 Opus production · 1 NEW tool `retract_last_message` + cache slot architecture preserved + 1 opcional golden. |
| `04-validators.yaml` | 324 | 4 categorías validators · 25+ must_pass:true gates + pre-flight gates Ola 1. |
| `05-guidelines.md` | 305 | Skills+rules to load · files in scope · patterns REQUIRED+FORBIDDEN · reuso explícito · commit workflow · open questions. |
| `06-tickets.yaml` | 691 | 13 atomic tickets · DAG + blockers + gherkin_coverage per ticket · owner_eligibility per R23. |
| `HANDOFF-cross-story-updates.md` | 190 | Contratos producidos para Olas 2+3 (TS types · Zod · endpoints · events · BE modules). |

## Mockup heredado (SSoT visual)

`02-design-ui-mockup.html` — copia del parent `vitalia-ux-discovery/mockups/inbox.html` ratificado Chris 2026-05-17. Colores cementados en `vitalia/frontend/src/app/globals.css` (T-arch-1 shipped). Build debe respetar:

- Paleta 4 colores principales: `--vitalia-cian #01B2F8` · `--vitalia-purpura #7B2D91` · `--vitalia-azul-marino #180D95` · `--vitalia-verde-lima #B8DC2A` (avatar Lucas).
- Layout: chat-RIGHT rail 72-80px (operación diaria post-wizard) + sidebar progresivo v3.
- Componentes shared ya existen Story 11: `shared/contact-sidebar` + `shared/activity-stream` + `shared/copilot-rail` + `shared/agents` + `shared/phi` + `shared/shell`.

## Reuso explícito (Slice 1 — cementado en 05-guidelines.md § 5)

| Surface | Reuso de | Razón |
|---|---|---|
| FE conversación list + detail | `nicolify/frontend/src/features/closer-studio/components/inbox/` | Fork físico Slice 1 ratificado ADR-vitalia-001 |
| FE composer voice record | `nicolify/frontend/src/features/copilot/components/composer/VoiceOverlay.tsx` | REUSE direct + retoken |
| FE crm-hub reference | `nicolify/frontend/src/features/crm-hub/components/{ContactDetailContent,LifecycleStageChip,ContactFiltersPanel}.tsx` | Reference only para ContactSidebar PHI-aware + FilterChips Vitalia |
| BE Lead + Patient (existing) | `vitalia/backend/src/modules/vitalia/crm/` (Story 11) | EXTEND scaffold con Conversation/Message/ActivityEvent/ActionReceipt |
| BE channel format dispatch | `core/luana-core-channels/format_for_channel` + `intent_detector` | engine CONSUME direct |
| BE PHI dual-filter queries | `core/luana-core-platform.repositories.CompoundScopeRepositoryBase` (scope_field="clinic_id") | post lift Slice 1 — replaces local PhiRepositoryBase |
| BE trace observability | `core/luana-core-observability` (turn_envelope · sanitize_payload · cost_recorder) | engine CONSUME via heredancia (NEVER mirror) |
| Compliance gates | `core/luana-core-compliance.ComplianceService` | engine CONSUME direct |
| Idempotency keys | `core/luana-core-idempotency` | engine CONSUME direct (Idempotency-Key header) |
| Outbox events | `core/luana-core-events.outbox.adapter_bus` | engine CONSUME direct |
| Sales_agent runtime | `core/luana-core-sales-agent` | engine CONSUME · NO modify |

## Side stories paralelas relevantes

Ninguna — `/inbox` arranca sin side blockers.

Ola 1 paralela: `vitalia-slice-1-fidelizacion` (auto-contenida también).

## HANDOFF-cross-story coordination

Producer Ola 1 inbox para Ola 2+3 — ver detalle en `HANDOFF-cross-story-updates.md`:
- TS types: `Lead` + `Conversation` + `LeadStage` (en `crm-shared/types.ts`)
- Zod schemas: `leadSchema` + `conversationSchema` (en `lib/zod-schemas/`)
- API endpoints: `GET /api/v1/vitalia/crm/{leads,conversations}/*` + `POST /api/v1/vitalia/inbox/proactive-outbound`
- Domain events: `ConversationStarted` · `MessageSent` · `MessageRetracted` · `ModeChanged` · `AdrianPaused` · `ProactiveOutboundSent`

Cross-story update obligatorio post-merge: `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md` § 10 Bitácora marca contracts como "shipped".

## Bitácora

- 2026-05-17 spawned: split decision Chris post /architect ready package mega-story
- 2026-05-20 REPLAN: ux-discovery → done (parent SSoT cumplido). Mockup heredado. Ola 1 asignada paralela con fidelización. Reuso explícito cementado. Pre-flight gates requeridos antes /architect refresh.
- 2026-05-20 READY package emitted: /architect produced 01-spec-extract + 02-design-ui + 03-arch* + 04-validators + 05-guidelines + 06-tickets + HANDOFF-cross-story-updates. State transition refined → ready. Awaiting /dev-team pickup post pre-flight gates GREEN.
