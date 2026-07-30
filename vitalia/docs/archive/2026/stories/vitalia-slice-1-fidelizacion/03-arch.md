# vitalia-slice-1-fidelizacion — Architecture (consolidated index)

> **Status:** ready package · architect run on **2026-05-20** (Opus 4.7)
> **State transition target:** refined → ready (al cerrar este package).
> **Brand:** `vitalia` (Salud + Bienestar · HIPAA-lite · `compliance_level=hipaa_lite`)
> **Inherits from:** parent `vitalia-ux-discovery` (archived 2026-05-20). Consolidated 03-arch carved to fidelización scope only.
> **Ola:** 1 (paralela con `/inbox`). Pre-flight gates documented en § 0.

## 0. Context summary

### Artifact map (este story package)

| Surface | File | Owner builder | Auditor |
|---|---|---|---|
| Consolidated index | `03-arch.md` (este) | — | — |
| Spec extract | `01-spec-extract.md` | — | — |
| Design UI | `02-design-ui.md` (+ mockup HTML) | — | — |
| Backend sub-arch | `03-arch-be.md` | `builder-backend` (Sonnet) | `auditor-backend` (Opus) |
| Frontend sub-arch | `03-arch-fe.md` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| Agentic sub-arch | `03-arch-agentic.md` | `builder-agentic` (Opus 4.7 R23 production) | `auditor-agentic` (Opus 4.7) |
| Validators ★ | `04-validators.yaml` | — | — |
| Guidelines | `05-guidelines.md` | — | — |
| Tickets | `06-tickets.yaml` | — | — |
| HANDOFF cross-story updates | `HANDOFF-cross-story-updates.md` | — | `/pm-vitalia` |

### Surface → builder → auditor mapping (consume by `/dev-team`)

| Surface (paths) | Builder | Auditor | Model |
|---|---|---|---|
| `vitalia/backend/src/modules/vitalia/fidelizacion/{domain,application,api,infrastructure}/` | `builder-backend` | `auditor-backend` | Sonnet build · Opus audit |
| `vitalia/backend/src/modules/vitalia/fidelizacion/workers/` (6 ARQ cron jobs) | `builder-backend` | `auditor-backend` | Sonnet · Opus |
| `vitalia/backend/src/modules/vitalia/connections/whatsapp/templates/fidelizacion/` (5 Meta-approved templates JSON config) | `builder-backend` | `auditor-backend` | Sonnet · Opus |
| `vitalia/backend/src/modules/vitalia/crm/` extension columns `marketing_opt_in, opt_out, opt_out_reason, opt_out_at` (PATCH endpoint) | `builder-backend` | `auditor-backend` | Sonnet · Opus |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_re_engagement_recommendation.py` (Lucas recommendation tool consuming re_engagement_events — production_code=true AGENTIC) | `builder-agentic` | `auditor-agentic` | **Opus 4.7 R23** |
| `vitalia/backend/src/modules/vitalia/sales_agent/tools/send_proactive_reengagement.py` (Adrián sub-tool wrapping `send_template_confirmation` for re-engagement specific — production_code=true AGENTIC) | `builder-agentic` | `auditor-agentic` | **Opus 4.7 R23** |
| `vitalia/frontend/src/features/fidelizacion/**` (FSD-Lite components + hooks + store + copy) | `builder-frontend` | `auditor-frontend` | Sonnet · Opus |
| `vitalia/frontend/src/components/shared/nps/NPSTagBadge.tsx` (cross-feature shared) | `builder-frontend` | `auditor-frontend` | Sonnet · Opus |
| `vitalia/frontend/src/features/agenda/components/FollowUpField.tsx` (cross-link Ola 3 — **NOT in scope this story**, OWNED by /agenda Ola 3) | n/a (cross-ref only) | n/a | — |
| Eval goldens (`vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/**` · `tests/agentic_evals/lucas/reengagement/**`) | `builder-agentic` tests scope (R23 production_code=false) | `auditor-agentic` | Sonnet OK |

### Skills consulted (one-liner decisions)

- **`copilot-expert`** — Valeria copilot NOT in scope this story (wizard onboarding lives en story side `vitalia-copilot-tools-impl`). Lucas re-engagement recommendations tool (`compute_re_engagement_recommendation`) consumes engine `core/luana-core-copilot/` indirectly via Lucas brand-wide agentic surface. Anti-duplication §0 cardinal: observability/cost/pricing patterns viven en `core/luana-core-observability/` — Vitalia EXTEND via heredancia (no mirror).
- **`sales-agent-expert`** — Adrián consumes engine `core/luana-core-sales-agent/` directly. New tool `send_proactive_reengagement` wraps existing `send_template_confirmation` (cementado pre side story `vitalia-copilot-tools-impl` Ola 0). §3 NO se toca: Closer Studio, SmartBufferService, OutputManager chunking, agent_state_checkpoints. Slot 5 BRAND_VOICE cache prefix from `personality_profiles.system_instruction` (NO inject mid-block). Eval goldens 4 escenarios re-engagement (1 happy per pattern + 1 opt-in absence guard).
- **`backend-expert`** — DDD Inside-Out strict en `vitalia/backend/src/modules/vitalia/fidelizacion/`. Dual filter `tenant_id` + `clinic_id` cardinal per `hipaa-lite.md`. Migrations idempotentes raw SQL `IF NOT EXISTS`. PHI columns encrypted via pgcrypto. Audit log sync write pre-response.
- **`frontend-expert`** — FSD-Lite per `vitalia/frontend/src/features/fidelizacion/`. Server-First default RSC. `fetchClient` auto-inyecta `X-Tenant-ID + X-Clinic-ID`. nuqs URL state SSoT. Reuse pattern campaigns-lite + notifications de Nicolify (token adapter, no Public API import directo).
- **`brand-expert`** — NOT touched (no brand identity changes this story).
- **`offer-expert`** — Slice 1 stub fields `offers.{maintenance_schedule, maintenance_custom_days, requires_multi_session, sessions_expected, gap_alert_days}` ya creadas vía engine promotion proposal `2026-05-17-offer-studio-multi-session-maintenance` (state migrated pre-Ola 1). Esta story CONSUME runtime — no modifica engine ni FE offer-studio. Admin DB update + hardcoded defaults per vertical (dental: limpieza_dental=EVERY_6_MONTHS, etc.).
- **`metrics-expert`** — NPS metric NOT en engine analytics-engine stage_services. Tabla `vitalia_nps_responses` local brand. Slice 2 candidate lift to engine si segunda brand adopta NPS (creator economy comunify).
- **`tessl__langgraph`** — Lucas re-engagement tool: simple ReAct agent (no supervisor) for `compute_re_engagement_recommendation`. Consume engine LangGraph harness shared. Stream modes irrelevant (cron-triggered, no UI streaming).
- **`tessl__graceful-degradation`** — External calls: WhatsApp Business API (templates Meta-approved) wrap timeout 10s + soft-fail fallback ("marcar conversación pendiente revisar" + retry queue). Mercado Pago no usado en esta story.
- **`playwright-expert`** — E2E smoke `vitalia/frontend/e2e/specs/smoke/fidelizacion.smoke.spec.ts` (visualiza tabs + cards + KPIs sin disparar templates). Regression tests por scenario Gherkin (4 specs) en `vitalia/frontend/e2e/regression/fidelizacion-*.spec.ts`. Port 3002.
- **`worktree-protocol`** — story corre en `wip/vitalia-slice-1-shipping` (canónico vitalia). Lock bucket `code` para Ola 1 fidelización + Ola 1 inbox compartido si paralelo.

### CONTEXT-BRIEF source

Self-explored Path B (no Haiku context-builder pre-cocked CONTEXT-BRIEF.md). Sources de evidencia:
- Step 0: date capture 2026-05-20
- Step 0.5: workspace + brand resolved (`vitalia`)
- Step 1: read inputs declarados en prompt — `checkpoint.md` actual · parent archive (`01-spec.md` §§ Ruta /fidelización + `03-arch{-be,-fe,-agentic}.md`) · mockup HTML · HANDOFF cross-story · brand.yaml · existing extensions.py scaffold (Story 11 cement)
- Step cross-module audit: engine `core/luana-core-{platform,campaigns,events,observability,sales-agent}/` consultation (read-only) confirmed `cron_envelope` + `compound_scope_repository` + campaigns workers + outbox adapter + observability shared abstractions match `.claude/rules/anti-duplication.md` SSoT.

### Pre-flight gates (HARD BLOCK Ola 1)

Per checkpoint + HANDOFF cross-story:

- [ ] `CLERK_TESTING_TOKEN_VITALIA` + `VITALIA_CLERK_WEBHOOK_SECRET` configurados en `vitalia/.env.dev`
- [ ] 3 test users creados: `dr.demo@vitalia.test` (doctor) · `recepcion@vitalia.test` (recepcion) · `admin@vitalia.test` (super_admin)
- [ ] 3 tenants fixture seedeados (Aurora AR · Mindful CL · Sanaré MX — Sanaré primario tests)
- [ ] `vitalia/frontend/playwright/.clerk/user.json` generado
- [ ] Suite smoke 23 specs GREEN local + live
- [ ] Promotion proposal `2026-05-20-core-platform-extensions-slice-1` (cron_envelope + CompoundScopeRepositoryBase) `state=migrated` en main · `core/luana-core-platform` 0.2.0 → 0.3.0

### capability YAML + modules MD updates (post-merge required)

- NEW `vitalia/docs/product/capabilities/fidelizacion/4patterns-reengagement.yaml` (status: planned → live al merge)
- NEW `vitalia/docs/product/capabilities/fidelizacion/nps-resumido-slice1.yaml`
- NEW `vitalia/docs/product/capabilities/fidelizacion/templates-meta-approved-5.yaml`
- NEW `vitalia/docs/product/capabilities/fidelizacion/crons-reengagement-6.yaml`
- NEW `vitalia/docs/product/modules/fidelizacion.md` (SSoT funcional viva post-merge, auto-list R32 reconcile)

### Architecture fitness gates (must keep passing)

Engine + brand fitness suites afectados:
- `core/luana-core-{platform,campaigns,events,observability,sales-agent}/tests/architecture/` (engine — read-only consultation, no modifications)
- `vitalia/backend/tests/architecture/`:
  - `test_phi_dual_filter.py` — tenant_id+clinic_id dual filter cardinal (CRITICAL hipaa-lite)
  - `test_no_cross_brand_imports.py` — anti-duplication enforce
  - `test_no_legacy_paths.py` — no `backend/src/shared/` (root pre-multibrand) imports
  - `test_response_model_required.py` — PII allowlist hipaa-lite
  - `test_migrations_idempotent.py` — IF NOT EXISTS raw SQL
  - `test_extension_sdk_registration.py` — vitalia extensions.py registers via EP only
  - `test_audit_log_sync_write.py` — PHI mutations write audit_log pre-response
  - `test_pgcrypto_phi_columns.py` — PHI columns use pgcrypto symmetric encryption (re_engagement_events.payload_phi)
  - `test_cron_envelope_used.py` (NEW Slice 1 — enforces fidelización workers import `luana_core_platform.workers.cron_envelope` not bypass)
  - `test_compound_scope_repository_used.py` (NEW Slice 1 — enforces fidelización PHI repos subclase `luana_core_platform.repositories.compound_scope_repository.CompoundScopeRepositoryBase` with `scope_field='clinic_id'`)
- `vitalia/frontend/src/__tests__/architecture/`:
  - `test_no_hardcoded_colors.test.ts`
  - `test_no_hardcoded_strings.test.ts` — fidelización copy.ts SSoT
  - `test_fsd_boundaries.test.ts`
  - `test_no_cross_feature_imports.test.ts`
  - `test_server_first.test.ts`
  - `test_phi_pii_components_used.test.ts` — `<PiiMaskedSpan>`/`<RequireRole>` en ReEngagementContactSidebar
  - `test_no_voseo_in_copy.test.ts`

Allowlist shrinkage: zero new entries — fix-forward.

## 1. Top-level architecture (cross-surface contract)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│         USER doctor/recepcion/admin_clinic clínica (rol RBAC strict)            │
│         Desktop primary · mobile-responsive Slice 2                              │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │ HTTPS + Clerk JWT + X-Tenant-ID + X-Clinic-ID
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│      FRONTEND vitalia · /fidelización (Next.js 16 App Router · FSD-Lite)         │
│      Port 3002 dev · Server-First RSC default                                    │
│      features/fidelizacion/ — Tabs 5 + KPIs hero + ReEngagementCards + Modals   │
│      Reuse pattern: campaigns-lite + notifications (Nicolify token adapter)      │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │ REST + React Query (TanStack v5)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│      BACKEND vitalia · fidelización módulo (FastAPI async · DDD Inside-Out)      │
│      Port 8002 dev · uvicorn workers · redirect_slashes=False                    │
│      ~8 endpoints /api/v1/vitalia/fidelization/...                               │
│      6 ARQ cron jobs · 3+ application services · 2 NEW tables                    │
│      Dual filter tenant+clinic CARDINAL · audit_log sync write · pgcrypto PHI    │
└─┬─────────────────────────────────────────────────────────────────────────────┬─┘
  │                                                                             │
  │ AGENTIC                                                                     │
  ▼                                                                             ▼
┌─────────────────────────────┐                       ┌───────────────────────────────────┐
│ Engine core/luana-core-*    │                       │ External (graceful-degradation)   │
│ READ-ONLY consult           │                       │                                    │
│ ─ platform (cron_envelope,  │                       │ ─ WhatsApp Business API           │
│   CompoundScopeRepoBase)    │                       │   (templates Meta-approved)       │
│ ─ campaigns (workers batch) │                       │ ─ Adrián sales_agent runtime      │
│ ─ events (outbox adapter)   │                       │   (via service injection)         │
│ ─ observability (recording, │                       │ ─ Lucas brand-wide agentic        │
│   sanitize)                 │                       │   (reads re_engagement_events)    │
│ ─ sales-agent (Adrián)      │                       │                                    │
│ ─ compliance (channel guard)│                       │                                    │
│ ─ idempotency               │                       │                                    │
└─────────────────────────────┘                       └───────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│         DATA · Postgres 5435 + Qdrant + Redis db=1                               │
│   NEW tables: vitalia_treatment_plans · vitalia_re_engagement_events ·           │
│               vitalia_nps_responses                                              │
│   Columns added: vitalia_patients.{marketing_opt_in, opt_out, opt_out_reason,    │
│                  opt_out_at}                                                     │
│   Consumed runtime (already created Ola 0):                                      │
│     vitalia_appointments.{follow_up_due_at, follow_up_reason, completed_at,      │
│                            balance_status, origin}                               │
│     offers.{requires_multi_session, sessions_expected, gap_alert_days,           │
│             maintenance_schedule, maintenance_custom_days} (engine)              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Cross-cutting design principles (consumed by all 3 sub-archs)

Heredados del parent arch `vitalia-ux-discovery/03-arch.md` § 2. Recorte aplicable a esta story:

### 2.1 Tenant + Clinic dual filter (cardinal — HIPAA-lite)

**Rule:** every PHI query MUST filter `Model.tenant_id == tenant_id AND Model.clinic_id == clinic_id`. Incluye `get_by_id`. Repositorios fidelización subclase `CompoundScopeRepositoryBase` (engine) con `scope_field="clinic_id"`.

### 2.2 Audit log sync write

`vitalia_audit_log` row pre-response en cada PHI mutation/access. Sync, not fire-forget. Acciones nuevas esta story:
- `view_re_engagement_event`
- `send_proactive_reengagement_template`
- `pause_patient_re_engagement`
- `mark_external_re_engagement`
- `mark_no_continue_re_engagement`
- `log_manual_call_re_engagement`
- `view_nps_response`
- `submit_opt_out_re_engagement`

### 2.3 PII sanitization in traces

`sanitize_payload(payload, compliance_level="hipaa_lite")` engine canónica antes writes a `copilot_trace_event` / `sales_agent_trace_event` / `vitalia_audit_log.payload_redacted`. Vitalia PHI field list canonical en `vitalia/backend/src/modules/vitalia/compliance/phi_fields.py` (Story 11 cement).

### 2.4 Encryption at-rest (pgcrypto)

PHI columns esta story:
- `vitalia_treatment_plans.notes`
- `vitalia_re_engagement_events.payload_phi`
- `vitalia_audit_log.payload_redacted`
- `vitalia_nps_responses.comment` (PHI — comentario paciente)

### 2.5 RBAC strict (medical roles)

Roles allowed PHI: `doctor`, `nurse`, `admin_clinic`. Marketing/sales NEVER. Paciente `patient` solo data propia (NPS submit endpoint).

Decorator: `@require_phi_access(roles=["doctor", "nurse", "admin_clinic"])` en TODOS endpoints PHI fidelización excepto:
- `POST /api/v1/vitalia/fidelization/nps/submit` (paciente external — token NPS specific link)
- `GET /api/v1/vitalia/fidelization/nps/summary` allowed marketing también (no PHI individual, agregados)

### 2.6 Channel guards (no PHI on non-encrypted channels)

`ComplianceService.validate_outbound_message(template, channel)` engine canónica gates templates:
- WhatsApp Business API tier paid OK (Vitalia operativo)
- WhatsApp free tier BLOCK
- SMS BLOCK
- Email plaintext BLOCK (excepto portal-link email)

Templates fidelización (5 Meta-approved):
- `recordatorio_proxima_sesion` UTILITY — no PHI exposed (variables: `{patient_name}`, `{offer_label}`, `{sessions_completed}/{sessions_expected}`, `{slot_1_date}`, `{slot_2_date}`, `{slot_3_date}`)
- `recordatorio_control_doctor` UTILITY — variables: `{patient_name}`, `{doctor_name}`, `{follow_up_reason}` (PHI alert — sanitize razón si contains diagnóstico)
- `invitacion_mantenimiento` UTILITY — variables: `{patient_name}`, `{offer_label}`, `{cadence_label}`
- `re_engagement_ausencia` MARKETING — variables: `{patient_name}`, `{months_inactive}`, `{last_doctor_name}` (PHI alert — sanitize)
- `nps_post_tratamiento` MARKETING — variables: `{patient_name}`, `{offer_label}`, `{nps_short_link}` (no individual PHI in template body — link al portal seguro)

### 2.7 Currency policy (LatAm — NO hardcoded)

Fidelización NO maneja monetary fields directos (KPIs son counts/percentages/scores). NPS averages adimensional. Si Slice 2 agrega "valor histórico paciente $XXXX" → DTO con `currency: str | None` consumed por `formatMoney(amount, currency)` FE.

### 2.8 Spanish neutro LatAm strict

Templates WhatsApp + `FIDELIZACION_COPY` constants en tuteo `tú`. Voseo prohibido. Arch fitness `test_no_voseo_in_copy.test.ts` enforces.

**Exception:** Adrián output respeta voz tenant. Si tenant AR configura voseo → Adrián replies voseo (templates UTILITY/MARKETING son scaffold + variables — el texto fijo del template es Latam neutro Meta-approved, variables son substituidas).

### 2.9 Master data (UTC + timezone)

Cron timing all UTC. Display tenant timezone via `useTenantLocale()`. `DateTime(timezone=True)` mandatory. `utc_now()` helper. Cron triggers: 06:00/07:00/07:30/08:00/09:00/15:00 UTC daily/weekly.

### 2.10 Idempotency on writes

Cron jobs usan idempotency key naturalez `(tenant_id, clinic_id, patient_id, pattern, sweep_date)` para evitar dup `re_engagement_events` row si cron re-trigger. `core/luana-core-idempotency/` `@idempotent` decorator (parte de cron_envelope post lift).

`POST /api/v1/vitalia/fidelization/nps/submit` usa `Idempotency-Key` header (paciente puede reenviar el form si problema red).

### 2.11 No cross-brand mirror (anti-duplication)

Pattern detected en 2+ brands → STOP, escalate `/pm-luana`. NPS pattern + re-engagement card UI son candidates Slice 2 lift to core/`@luana/ui-kit` si comunify adopta.

Engine consumers EXTEND only:
- `luana_core_platform.workers.cron_envelope` (esta story usa)
- `luana_core_platform.repositories.compound_scope_repository.CompoundScopeRepositoryBase`
- `luana_core_campaigns.workers.{scheduler_tick, execution_task, segment_refresh_tick, audit_retention_task}` (REFERENCE pattern — fidelización NO usa direct, sus 6 cron son custom invocation pattern)
- `luana_core_events.outbox.adapter_bus` (emit NPSScoreCollected + ReEngagementTriggered)
- `luana_core_observability.recording.{sanitize_payload, BaseObservabilityContext}` (consume via Adrián sales_agent + Lucas tools)
- `luana_core_compliance.ComplianceService` (channel guard)
- `luana_core_sales_agent` (Adrián direct consume via service inject)

## 3. Existing systems audit (NO NEW LAYER rule per `.claude/rules/anti-duplication.md`)

### Source of evidence
- [x] CONTEXT-BRIEF.md not found in story folder — Path B self-run greps + parent arch retención
- [x] Engine package read-only consult: `core/luana-core-{platform,campaigns,events,observability,sales-agent,compliance,idempotency}/` verified
- [x] Cross-brand mirror check executed: `nicolify/`, `comunify/`, `lupulo/` — zero similar fidelización module found

### Sistemas existentes encontrados (mapping)

| Sistema | Path engine | Decisión Vitalia esta story |
|---|---|---|
| Cron envelope (idempotency + OTel + audit + sentry centralizado) | `core/luana-core-platform/src/luana_core_platform/workers/cron_envelope.py` (post promotion proposal `2026-05-20-core-platform-extensions-slice-1` migrated) | **EXTEND consume** — todos los 6 crons fidelización wrapan con `@cron_envelope` |
| Compound scope repository base (PHI dual filter) | `core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py::CompoundScopeRepositoryBase` (post idem proposal) | **EXTEND subclase** — `TreatmentPlanRepository`, `ReEngagementEventRepository`, `NPSResponseRepository` heredan con `scope_field="clinic_id"` |
| Campaigns workers (engine batch reference) | `core/luana-core-campaigns/src/luana_core_campaigns/workers/{scheduler_tick,execution_task,segment_refresh_tick,audit_retention_task}.py` | **CONSUME reference pattern** — fidelización crons custom invocation siguen mismo patrón ARQ + retry + idempotent. No direct import; engine ya shipped Story 11. |
| Outbox bus event emission | `core/luana-core-events/src/luana_core_events/outbox/adapter_bus.py` (default `USE_OUTBOX_PATTERN_*=True` post 2026-04-30) | **CONSUME direct** — emit `NPSScoreCollected` + `ReEngagementTriggered` events |
| Observability shared (sanitize_payload, BaseObservabilityContext, FXResolver, callback handler) | `core/luana-core-observability/src/luana_core_observability/{recording,cost,channels}/` | **CONSUME direct** Lucas tool + Adrián tool wrap. No mirror per anti-duplication.md §0 |
| Compliance service (channel guard) | `core/luana-core-compliance/src/luana_core_compliance/` | **CONSUME direct** — `validate_outbound_message(template, channel)` antes `send_proactive_reengagement` |
| Idempotency keys | `core/luana-core-idempotency/` | **CONSUME direct** — natural keys `(tenant, clinic, patient, pattern, sweep_date)` |
| Sales-agent Adrián | `core/luana-core-sales-agent/` | **CONSUME direct via service inject** — fidelización service llama `adrian.send_proactive_outbound(...)` no toca runtime |

### Decisión por sistema (EXTEND > REPLACE > NEW priority)

**ALL EXTEND/CONSUME** — zero NEW infrastructure layers proposed esta story. Zero engine modifications.

**Cross-brand mirror check resultado:** ZERO mirrors detected.

## 4. Side stories blockers (post HANDOFF cross-story § 1)

Esta story Ola 1 = **auto-contenida** (sin side blockers). Per checkpoint línea 16: `blocker_dependencies: []`.

Pre-flight gates (§ 0 supra) son universales Ola 1 (compartidos con `/inbox`). Promotion proposal core (`cron_envelope` + `compound_scope_repository`) es HARD GATE bloqueante.

## 5. Performance budgets (Slice 1)

| Metric | Budget |
|---|---|
| LCP `/fidelización` (KPIs hero render) | < 2.5s |
| INP tab switch | < 200ms |
| Cards list rendering 100 items | virtualization required (> 50 cards) |
| Cron `multi_session_gap_sweep` duración | < 30s per 1000 patients (engine cron_envelope timeout default 5min) |
| Cron `absence_sweep` duración | < 60s per 1000 patients |
| Adrián turn cost (proactive_outbound re-engagement) | ≤ $0.03 USD (template send no LLM call — solo formatting via personality compiler) |
| Lucas tool `compute_re_engagement_recommendation` per invocation | ≤ $0.05 USD (Kimi reasoning short prompt) |
| Cache hit rate (Adrián slot 1-5 prefix) | ≥ 60% |

Validators per § `04-validators.yaml::visual` + `agentic_eval`.

## 6. Observability + tracing (Slice 1)

### OpenTelemetry spans (NEW esta story)

- `vitalia.cron.multi_session_gap_sweep`
- `vitalia.cron.follow_up_due_sweep`
- `vitalia.cron.maintenance_due_sweep`
- `vitalia.cron.absence_sweep`
- `vitalia.cron.nps_post_treatment_sweep`
- `vitalia.cron.re_engagement_response_timeout_sweep`
- `vitalia.fidelizacion.send_proactive_reengagement`
- `vitalia.fidelizacion.nps_submit_webhook`
- `vitalia.lucas.compute_re_engagement_recommendation`
- `vitalia.adrian.proactive_outbound_reengagement` (sub-span de Adrián turn)

### Sentry/Observability alerts

- Cron fidelización falla > 3 consecutive → page on-call
- Adrián cost per turn re-engagement > $0.05 → warn (template send no LLM cost runaway expected)
- Lucas cost per recommendation > $0.10 → warn
- Cache hit rate Adrián slot < 30% → warn
- WhatsApp Business API rate limit hit (template send) → throttle + degrade graceful
- `vitalia_re_engagement_events` insertion rate > 1000/min (cron massive batch) → warn observability volume

## 7. Open questions deferred to /dev-team (NON-blocking per Chris ratification)

| # | Question | Resolution |
|---|---|---|
| 1 | NPS schema en columna `vitalia_patients.nps_score` (denormalized last) o tabla `vitalia_nps_responses` separada? | **Tabla separada** `vitalia_nps_responses` (Slice 2 dashboard NPS needs history full distribution). Slice 1 sufficient with table + index by patient_id desc + period. |
| 2 | Lucas `compute_re_engagement_recommendation` cron-triggered o on-demand pull? | **On-demand pull** Slice 1 — `/marketing` Lucas card source consume runtime cuando user navega Stage Adopción. Defer cron Slice 2 si volumen amerita pre-compute. |
| 3 | `vitalia_re_engagement_events` retention | 10 años (HIPAA-lite cron + audit_log standard). Partition por mes. |
| 4 | Throttle per tenant per día template MARKETING (cost guard) | Slice 1 = 200 templates MARKETING/día/tenant default (configurable per plan tier). Slice 2 quota system per `core/luana-core-billing/`. |
| 5 | Si template send falla (Meta API down) → retry queue persistente o discard | **Retry queue persistente** — re-engagement_events stay status=`failed_sending` con retry_count++. Cron `re_engagement_retry_sweep` daily 11:00 UTC reintenta (max 3 attempts). Slice 1 minimal: log failure, manual retry button. Slice 2 cron retry auto. |
| 6 | Activity footer cross-ruta refresh | Per spec — sticky bottom 32px / expand 240px. Server-Sent Events optional Slice 2; Slice 1 = React Query polling 10s. |
| 7 | Tag NPS en `/inbox` (consumer) implementación timing | Consumer story `/inbox` (Ola 1 paralela) consume `NPSScoreCollected` outbox event + `GET /api/v1/vitalia/fidelization/nps/summary` para chip render. Producer (esta story) emite event correctamente al insert NPS response. |
| 8 | `do_not_contact_re_engagement` patient flag column | Implementado vía `vitalia_patients.opt_out=true` + `opt_out_reason="paused_until_{date}"`. Slice 2 dedicada columna `paused_re_engagement_until DATE` + cron unpause. |
| 9 | Cross-link `/agenda` follow-up captured (Patrón 2 trigger) | Solo CONSUMER en Ola 1 fidelización. PRODUCER en Ola 3 `/agenda`. Slice 1 Ola 1 funciona con DB updates manuales (admin updates `vitalia_appointments.follow_up_due_at` via SQL o admin Streamlit). Cuando Ola 3 cierra → UI capture flow live. |

## 8. Research notes (DATE-AWARE — accessed 2026-05-20)

Knowledge cutoff Opus 4.7 = Jan 2026. Researched live 2026-05-20 via internal codebase greps + verified canonical docs. Topics post-cutoff (multibrand reorg 2026-05-15, story-closure-gate cement 2026-05-18, paradigm v4.1 2026-05-19, promotion proposal lift core 2026-05-20) — current codebase state verified.

| Source | Version | Accessed | Key takeaway |
|---|---|---|---|
| WhatsApp Business API templates | Cloud API 2026 | 2026-05-20 | UTILITY templates NO opt-in required (transactional). MARKETING templates REQUIRE explicit opt-in per Meta Platform Terms. Throttle 1 reminder per pattern per 7d compliance LatAm regulation. Cost: PE ~$0.0067 UTILITY / $0.038 MARKETING. |
| ARQ workers retry strategy | arq 0.25+ | 2026-05-20 | Cron envelope (engine post lift) handles retry exponential backoff max 3. Idempotency keys via `core/luana-core-idempotency/`. |
| Postgres partition by RANGE date | PG 16+ | 2026-05-20 | Monthly partitions for `vitalia_re_engagement_events` viability long-term (10y retention HIPAA-lite). Index on `(tenant_id, clinic_id, patient_id, pattern, sent_at DESC)` for throttle queries. |
| Anthropic prompt caching slot 5 BRAND_VOICE | API 2024-10-22+ | 2026-05-20 | Adrián compiler v2 slot 5 cacheable per-tenant. Slot 5 markers `cache_control` HERE. NO interpolation mid-block. Re-engagement templates (5 Meta-approved) son scaffold + variables substitution — no prompt LLM runtime call para template send (just formatting via personality compiler), so prompt cache irrelevant para template envío. Cache aplica al fallback ReAct cuando Adrián recibe respuesta paciente y entra conversación normal flow. |
| LangGraph 2.0 ReAct vs Supervisor | langgraph 0.6+ | 2026-05-20 | Lucas `compute_re_engagement_recommendation` simple ReAct alcanza (1 tool: query DB aggregates + 1 LLM reasoning call). No supervisor needed. |
| Mercado Pago refund webhook | API v1 2026 | 2026-05-20 | NOT USED esta story (refund flow lives en /agenda Ola 3). |

## 9. Referencias

- Inputs (provided by /pm-vitalia):
  - Mockup SSoT: `02-design-ui-mockup.html`
  - Parent spec extract: `01-spec.md` §§ Ruta /fidelización (líneas 2670-3324 parent archive)
  - Parent arch trio: `03-arch{,-be,-fe,-agentic}.md` (parent archive)
  - HANDOFF cross-story: `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md`
- Engine packages (READ-ONLY consult):
  - `core/luana-core-platform/src/luana_core_platform/{workers/cron_envelope.py, repositories/compound_scope_repository.py}`
  - `core/luana-core-campaigns/src/luana_core_campaigns/workers/{scheduler_tick, execution_task, segment_refresh_tick, audit_retention_task}.py`
  - `core/luana-core-events/src/luana_core_events/outbox/adapter_bus.py`
  - `core/luana-core-observability/src/luana_core_observability/recording/{sanitize_payload, BaseObservabilityContext}.py`
  - `core/luana-core-sales-agent/`
  - `core/luana-core-compliance/`
  - `core/luana-core-idempotency/`
- Reuse references:
  - `nicolify/frontend/src/features/campaigns-lite/`
  - `nicolify/frontend/src/features/notifications/`
- Rules:
  - `vitalia/.claude/rules/hipaa-lite.md`
  - `.claude/rules/{tenant-isolation,backend-ddd,frontend-fsd,architectural-fitness,anti-duplication,spanish-text,tdd-mandatory,story-closure-gate,brand-docs-schema,debugging,backend-quality,frontend-quality,master-data,currency-handling,backend-migrations,hotfix-repro-mandatory,e2e-testing,auditor-downstream-regression,auditor-self-fix-policy,parallel-safety,step-0-worktree,git-safety,git-haiku-delegation}.md`
- Configs:
  - `vitalia/config/brand.yaml`
  - `vitalia/backend/src/modules/vitalia/extensions.py` (existing Story 11 cement)
- Templates:
  - `docs/specs/templates/{03-arch,04-validators,05-guidelines,06-tickets,07-merge}-template*`
- Sub-archs:
  - `03-arch-be.md` (DDD + tables + endpoints + crons + Lucas + Adrián integration)
  - `03-arch-fe.md` (FSD-Lite + components + hooks + arch fitness)
  - `03-arch-agentic.md` (Lucas re-engagement tool + Adrián proactive_outbound integration + eval goldens + prompt cache slots)

---

**Next sub-archs:** read `03-arch-be.md`, `03-arch-fe.md`, `03-arch-agentic.md` for surface-specific contracts. Each cross-references this index.
