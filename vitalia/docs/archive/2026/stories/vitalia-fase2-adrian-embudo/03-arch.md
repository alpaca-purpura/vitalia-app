---
story_id: vitalia-fase2-adrian-embudo
brand: vitalia
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
phi_classification: non_phi
module: crm
capability_target: crm/adrian-embudo
cap_change_type: new
autonomous_mode: true          # Chris ratificó (pipeline architect→dev-team→auditor→[demo_signoff]→merge)
architect_run_on: 2026-06-03
dev_app_verified_required: true
surfaces: [BE, FE, AGENTIC]
---

# Contract: F2-S4 vitalia-fase2-adrian-embudo (Embudo de Adrián)

> SSoT de implementación paralela cross-surface. Detalle FE → `03-arch-fe.md`; detalle BE → `03-arch-be.md`.
> Contrato visual fiel a `mockups/embudo-v3.html` + `01-spec.md § Design specification D.0–D.16`.

## 0. Context Summary

- **Story:** `vitalia-fase2-adrian-embudo` (F3 release). Sub-tab `Adrián → Embudo` = superficie de supervisión sobre Adrián (empleado-IA que vende). Board funnel clínico dental 6 etapas + lista + página del lead (URL propia, 2 vistas) + override manual + alta de lead (ruta-hoja) + sub-tab hermana Recuperar (congelados + diagnose).
- **Architect run on:** 2026-06-03 (date -u). Modelo Opus 4.8 (cutoff Jan 2026); patrones agentic/SLA verificados contra research files de la story + canonical docs accedidos hoy (§ 15).
- **Módulos tocados:** `crm` (EXTEND — Lead/lead_service/lead_repository/lead_dto ya shipped) + `crm` NEW funnel layer + brand-extension agentic thin wire (override-context → checkpoint del agente).

### Surface → builder → auditor mapping (PM usa para spawn de agentes)

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/crm/{domain,infrastructure,application,api}/` (funnel: stage machine, transition, score, freeze, board) | **`builder-backend`** (Sonnet) | **`auditor-backend`** (Opus) |
| `vitalia/frontend/src/features/adrian/components/embudo/**` + `recuperar/**` + `components/shared/{channel,score}/**` | **`builder-frontend`** (Sonnet) | **`auditor-frontend`** (Opus) |
| `vitalia/backend/src/modules/vitalia/sales_agent/**` (override-context wire RN-4.1, brand-extension) | **`builder-agentic`** (Opus, R23) | **`auditor-agentic`** (Opus) |

### Skills consulted (decisión tomada de cada uno)

- **backend-expert** → Lead repo es PII (pgcrypto `vitalia_leads`), NO `PhiRepositoryBase`; funnel = repos NO-PHI nuevos (single tenant filter); raw-SQL idempotent migrations; SA 2.0 `select()`; `response_model=` mandatory.
- **frontend-expert** + **vitalia-design-system** → REUSE `EntitySubNavBar`/`TogglePill`/`EmptyState`/`PiiMaskedSpan` (shipped); board = single panel (NO SubSubTabsBar); React Query server / Zustand UI; RHF+Zod; tokens de `globals.css` (no hardcode).
- **sales-agent-expert** → `agent_state_checkpoints` es engine-owned (sync Session, `core/luana-core-sales-agent`). NO modificar el schema engine (§3 protected). `override_context` (RN-4.1) vive **brand-local** (en `vitalia_lead_stage_transition.reason` + wire de inyección al próximo turno), NO se añade columna al checkpoint engine. Diagnose/reactivate/frozen del engine se **consumen como referencia de patrón** — esta story los reimplementa brand-local sobre el read-model del lead (engine corre sync + auth distinta; mount directo = boundary mismatch).
- **copilot-expert** → no aplica (Embudo no es copilot; es sales_agent + crm supervision UI).
- **offer/metrics/brand-expert** → no aplican (no se tocan catálogos offer ni analytics ETL ni brand-studio).

### CONTEXT-BRIEF source

- **Self-ran greps (Path B)** — no había `CONTEXT-BRIEF.md` (story brief skipped). Auditoría cross-module ejecutada manualmente (§ Existing systems audit).

### capability YAML + modules/{m}.md afectados (post-merge — paradigma post 2026-05)

- `vitalia/docs/product/capabilities/crm/adrian-embudo.yaml` (ya `planned` — completar `scenarios[]` + `access` + `business_rules` + `Surface/Test coverage` al merge, ADR-004 § 5).
- `vitalia/docs/product/modules/crm.md` — agregar narrativa del funnel agent-operated (si existe; si no, surface a PM en § Open Questions).

### Architecture gates que deben seguir verdes

- `vitalia/backend/tests/architecture/`: `test_response_model_required.py` · `test_phi_dual_filter.py` (funnel NO-PHI no debe heredar PhiRepositoryBase → no rompe) · `test_lead_repository_is_not_phi_repository.py` · `test_growth_studio_event_no_phi.py` · DDD boundaries (no cross-module imports) · SA 2.0 + no-hard-deletes.
- `vitalia/frontend/src/__tests__/architecture/`: `test-no-clerk-organizations.test.ts` · `test_react_query_keys_convention.test.ts` · `test_features_no_cross_imports.test.ts` · `test_no_phi_in_url_params.test.ts` · `test_no_hardcoded_colors` (ChannelBadge usa tokens) · FSD boundaries.

---

## Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (Path B — fallback; no CONTEXT-BRIEF)

### Audit cross-module ejecutado
```bash
# Funnel/board/pipeline/stage en vitalia → NO existe layer (solo clinics/lucas usan "stage" en otro sentido)
grep -rln "lead_stage_transition|funnel|board|pipeline" vitalia/backend/src/modules/vitalia/   # → 0 matches en crm funnel
# Engine pipeline substrate (read-only consult)
find core/luana-core-{crm,sales-agent}/src -name "*.py" | grep -iE "pipeline|closer_studio|checkpoint|scoring"
# Cross-brand mirror check (comunify/nicolify/lupulo)
for b in comunify nicolify lupulo; do grep -rln "lead_stage_transition|adrian.*embudo|funnel_transition" $b/backend/src; done  # → 0 matches
# Reusable FE molecules
find vitalia/frontend/src/components -iname "*ChannelBadge*" -o -iname "*EntitySubNavBar*" -o -iname "*TogglePill*"  # → ALL EXIST
```

### Sistemas existentes encontrados

| Sistema | Path | Enum/Config | Factory/Router | Providers/Adapters | Estado |
|---|---|---|---|---|---|
| Lead PII entity + repo + service + dto | `vitalia/backend/src/modules/vitalia/crm/{domain/lead.py, infrastructure/persistence/lead_repository.py, application/services/lead_service.py, application/dto/lead_dto.py}` | `status` flat 5-valores (`new|contacted|qualified|lost|converted`) | crm router `/api/v1/crm/leads` (GET·list·POST·PATCH) | pgcrypto `vitalia_leads` (PII, single tenant filter) | active — **EXTEND** |
| Engine pipeline substrate | `core/luana-core-crm/.../api/pipeline.py` + `scoring.py` + `lifecycle_transition_model.py` | `LifecycleStage` (marketing bowtie) · `FunnelStage` (conversación) | engine `PUT /pipeline/{id}/stage` (sync Session, `luana_core_iam` auth) | `lifecycle_transitions` audit | active — **reference only** (NO mount: boundary mismatch sync/async + auth) |
| Agentic checkpoint substrate | `core/luana-core-sales-agent/.../models/agent_state_checkpoint_model.py` + `closer_studio/{command,query,kpi}_service.py` | `current_stage`, `lead_score`, `buying_signals`, `handler_mode`, `frozen_reason/at/diagnosis` keyed `(tenant_id, lead_id)` | engine closer_studio API (sync) | — | active — **consume read-only via projection** (§3 protected — NO schema edit) |
| `ChannelBadge` (FE) | `vitalia/frontend/src/components/shared/shell-organism/ChannelBadge.tsx` | slugs `whatsapp|instagram|email|web|telegram` (Tailwind token classes, lucide icons) | — | — | active — **EXTEND** (spec dice "NEW"; ya existe → extender) |
| `EntitySubNavBar` (FE) | `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.tsx` | rootHref/leaves/entity/activeLeaf · WAI-ARIA tablist | — | — | active — **REUSE verbatim** (workspace mode) |
| `TogglePill` · `EmptyState`/`EmptyStateInline` · `PiiMaskedSpan` | `vitalia/frontend/src/components/shared/{shell-organism,phi}/` | — | — | — | active — **REUSE** |
| `@dnd-kit/core ^6.3.1` + `@dnd-kit/utilities ^3.2.2` | `vitalia/frontend/package.json` | — | — | — | installed — **REUSE** |
| `vitalia_growth_studio_event` telemetry emitter | `vitalia/backend/src/modules/vitalia/_shared/telemetry/` | bucketed amounts | `growth_studio_emitter.py` | — | active — **REUSE** |
| `useTenantId` / `useClinicId` / `fetchClient` | `vitalia/frontend/src/{hooks,lib/api}/` | X-Tenant-ID auto-inject | — | — | active — **REUSE** |

### Decisión por sistema

- **Lead PII entity + repo (`crm/domain/lead.py`)**: **EXTEND** — el `Lead` actual tiene solo `status` flat (5 valores). El funnel necesita: `stage` (6 etapas dentales), `score`, `temperature`, `operated_by`, `stage_entered_at`, `is_frozen/frozen_reason/frozen_at`, `closure_reason`, `reactivation_cohort_at`, `deposit_status`, `version` (optimistic lock), `service_interest`, `assigned_doctor_id`, `estimated_value`/`currency`, `buying_signals[]`, `channel`. Se amplía el aggregate + tabla `vitalia_leads` (ADD COLUMN IF NOT EXISTS, idempotent). NO se crea `sales_pipeline` (Chris ratificó EXTEND crm). PII pgcrypto preservado (name/email/phone/notes encrypted); campos funnel = plaintext NO-PII.
- **Engine pipeline (`core/luana-core-crm`)**: **reference only, NO mount.** El engine corre sync `Session` + `luana_core_iam.get_current_user`; el crm router vitalia es async + Clerk JWT. Montar el router engine sería un boundary mismatch. Se replica el **patrón** `lifecycle_transitions` (schema audit) en una tabla brand-local `vitalia_lead_stage_transition` — esto NO es mirror cross-brand (no existe en otra brand) ni mirror del engine (engine es marketing-bowtie `LifecycleStage`, este es funnel dental brand-specific). Justificado NET-NEW por vertical-specificity (research/02-core-engine § Boundary REUSE vs BUILD lo recomienda explícitamente).
- **Agentic checkpoint (`agent_state_checkpoints`)**: **consume read-only.** Es §3-protected (sales-agent-expert) + engine-owned → NO se le añade columna. La superficie de lectura es `current_stage`/`buying_signals`/`handler_mode`/`frozen_*`. Para esta story (Inbox/sales_agent aún no live), `buying_signals` se siembran del dataset; cuando el agente esté live, el read-model los proyecta. **`override_context` (RN-4.1) vive brand-local** en `vitalia_lead_stage_transition.reason` + un wire thin (ticket agentic) que lo inyecta al próximo turno — NO columna nueva en el checkpoint engine.
- **`ChannelBadge`**: **EXTEND** (no NEW). Ya existe pero (a) usa Tailwind token-classes en vez de color de marca de la red social, (b) le faltan `meta`, `referido`, `tiktok`. Se extiende con un registro `channel-meta` (NEW, brand-local) que mapea slug → color de marca + glyph; `ChannelBadge` consume el registro. Esto satisface el § Registro de canales del spec sin romper `test_no_hardcoded_colors` (los colores de marca de redes sociales viven en el registro central con CSS vars dedicadas, no hardcoded inline por vista).
- **`EntitySubNavBar`, `TogglePill`, `EmptyState`, `PiiMaskedSpan`, `@dnd-kit`, telemetry emitter, fetchClient/hooks**: **REUSE** verbatim.

### NEW justificado (ningún existente sirve)

- **`vitalia_lead_stage_transition` tabla + `LeadStageTransition` entity + funnel stage machine + glass-box scorer + auto-freeze rule + board aggregation endpoint** → NET-NEW. Justificación: (a) el `status` flat actual no modela un funnel de 6 etapas con `allowed_next` ni audit; (b) el engine `lifecycle_transitions` es marketing-bowtie sync, no consumible async + es etapas distintas; (c) no existe scorer glass-box dental ni regla de freeze en ningún paquete; (d) cross-brand: NO existe mirror en comunify/nicolify/lupulo (grep = 0). Criterio Chris escala 1000+ tenants: stage machine determinista (sin ML), audit row por transición, optimistic lock por `version`. Cero deuda: la tabla nace con índices `(tenant_id, lead_id)`, soft-delete, idempotent migration.
- **`channel-meta` registry (FE)** → NEW brand-local. Candidato lift cross-brand (ver § Cross-cutting + § 16). NO se crea `/pm-luana` proposal en esta story — solo se flaggea.

**Lift escalation:** ninguna requerida en esta story. ChannelBadge + channel-meta marcadas `lift candidate` (comentario en código, ya presente en ChannelBadge.tsx) → si una 2ª brand lo necesita, `/pm-luana` lift a `@luana/ui-kit`. NO bloquea.

---

## 1. Domain Entities (BE)

> Detalle completo en `03-arch-be.md § 1`. Resumen de shape:

### `Lead` (EXTEND — `crm/domain/lead.py`)
Campos nuevos (todos con default → backward compatible):
- `stage: str = "interesado"` — `interesado|calificando|consulta_agendada|plan_presentado|reservado|decidio_no`
- `stage_entered_at: datetime` — para time-in-stage SLA (RN-11)
- `score: int = 0` (0-100, glass-box derivado) · `temperature: str = "cold"` (`hot|warm|cold`)
- `operated_by: str = "agent"` (`agent|human`) — espejo de `handler_mode` del checkpoint (RN-12)
- `channel: str | None` (canal origen — alimenta ChannelBadge)
- `service_interest: str | None` · `assigned_doctor_id: UUID | None`
- `estimated_value: Decimal | None` · `currency: str | None` (PEN/MXN — RN-15)
- `buying_signals: list[str]` (enum `pregunto_precio|urgencia|presupuesto_ok|…`) — sembrado/proyectado
- `is_frozen: bool = False` · `frozen_reason: str | None` (`inactividad_lead|sin_respuesta_presupuesto|agente_trabado`) · `frozen_at: datetime | None`
- `closure_reason: str | None` · `reactivation_cohort_at: datetime | None`
- `deposit_status: str | None` (`pending|received` — STUB MSW esta story)
- `version: int = 1` — optimistic lock (RN-4 / SC-5)
- `is_blacklisted: bool = False` (RN-13 — excluido de todo)

> `id`, `tenant_id` (UUID, mandatory), `deleted_at` (soft delete), `created_at`, `updated_at` ya presentes.

### `LeadStageTransition` (NEW — `crm/domain/lead_stage_transition.py`)
`id: UUID` · `tenant_id: UUID` (mandatory) · `lead_id: UUID` · `from_stage: str | None` · `to_stage: str` · `triggered_by: str` (`agent|manual_override|webhook|reactivation|auto_freeze`) · `reason: str | None` (override_context RN-4.1) · `score_at_transition: int | None` · `occurred_at: datetime` · `actor_user_id: UUID | None` · `deleted_at: datetime | None`.

### `LeadActivity` (NEW — `crm/domain/lead_activity.py`)
Micro-log atribuido (§ Procedencia). `id` · `tenant_id` · `lead_id` · `actor` (`agent|human|lead|system`) · `kind` (`message|stage_move|info_sent|deposit|note`) · `description_es` · `occurred_at` · `deleted_at`. (NO confundir con `crm/domain/activity_event.py` que es PHI-dual-filter de conversaciones inbox.)

## 2. SQLAlchemy 2.0 Models (BE)

- **EXTEND** `vitalia_leads`: migration idempotent `ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS {stage, stage_entered_at, score, temperature, operated_by, channel, service_interest, assigned_doctor_id, estimated_value, currency, buying_signals JSONB, is_frozen, frozen_reason, frozen_at, closure_reason, reactivation_cohort_at, deposit_status, version, is_blacklisted}`. Index `CREATE INDEX IF NOT EXISTS ix_vitalia_leads_tenant_stage ON vitalia_leads (tenant_id, stage, is_frozen)` + `ix_vitalia_leads_tenant_stage_entered (tenant_id, stage, stage_entered_at)`.
- **NEW** `vitalia_lead_stage_transition` (table prefix `crm` conceptual → `vitalia_lead_stage_transition`): `id UUID PK`, `tenant_id UUID NOT NULL`, `lead_id UUID NOT NULL`, `from_stage VARCHAR`, `to_stage VARCHAR NOT NULL`, `triggered_by VARCHAR NOT NULL`, `reason TEXT`, `score_at_transition INTEGER`, `actor_user_id UUID`, `occurred_at TIMESTAMPTZ NOT NULL`, `deleted_at TIMESTAMPTZ`. Index `ix_lst_tenant_lead (tenant_id, lead_id, occurred_at DESC)`.
- **NEW** `vitalia_lead_activity`: `id`, `tenant_id`, `lead_id`, `actor`, `kind`, `description_es`, `occurred_at`, `deleted_at`. Index `(tenant_id, lead_id, occurred_at DESC)`.
- `DateTime(timezone=True)` en todos los timestamps; store UTC (master-data). `reason TEXT` NO contiene PHI (override context = motivo comercial; arch test word-boundary `notes\s+TEXT` no aplica — campo se llama `reason`).

> ⚠️ `reason TEXT` — para evitar el falso positivo del arch test PHI pgcrypto regex (`notes\s+TEXT`, ver MEMORY main-integration-cap-drift), el campo se llama `reason`, NO `notes`. Documentado en `03-arch-be.md § 2`.

## 3. Pydantic v2 DTOs (BE)

> `03-arch-be.md § 3` detalle. Todos `model_config = ConfigDict(from_attributes=True)`, tipos explícitos (no `Any`).
- `LeadResponse` (EXTEND): agregar `stage, score, temperature, operated_by, channel, estimated_value, currency, service_interest, buying_signals, stage_entered_at, is_frozen, frozen_reason, deposit_status, version`. Name vía PiiMaskedSpan en FE (DTO devuelve `name` real, masking es FE — pero `response_model` allowlist NO incluye PHI clínico; lead es non-PHI).
- `BoardResponse` (NEW): `columns: list[BoardColumn]` (cada `BoardColumn`: `stage, label, count, sum_value, currency, over_sla_count, leads: list[LeadCardDTO]`) + `kpis: BoardKpis`.
- `LeadCardDTO` (NEW): proyección read-only de la card (D.4).
- `StageTransitionRequest` (NEW): `to_stage: str`, `reason: str | None`, `note: str | None`, `version: int`, `triggered_by: str = "manual_override"`.
- `StageTransitionResponse` (NEW): `lead: LeadResponse`, `transition: TransitionDTO`.
- `LeadDetailResponse` (NEW): lead + `score_breakdown: list[ScoreFactor]` + `autonomy: AutonomyInfo`.
- `TimelineResponse` (NEW): `events: list[TimelineEntry]` (mezcla transitions + activity).
- `FrozenListResponse` / `DiagnoseResponse` / `ReactivateResponse` (NEW).
- `LeadCreateRequest` (EXTEND): agregar `stage` (default `interesado`), `channel`, `service_interest`, `tags`, `estimated_value`, `currency`.
- 422 error body para salto inválido: `{detail, allowed_next: list[str]}`.

## 4. API Routes (BE)

Todas bajo `/api/v1/crm/...` (mount existente `app.include_router(crm_router, prefix="/api/v1/crm")`). Bearer + `X-Tenant-ID` mandatory (non-PHI → `X-Clinic-ID` opcional, NO requerido). `response_model=` en cada una. `redirect_slashes=False` (app-level, ya seteado).

| Method | Path | Auth | Request DTO | response_model | Descripción |
|---|---|---|---|---|---|
| GET | `/crm/board?view=&stage=&origin=&search=&sort=&page=` | Bearer+Tenant | — | `BoardResponse` | Board agrupado (RN-18 hot only) + KPIs. `sort` default `stage_age_desc` (RN-17) |
| GET | `/crm/leads/{id}` | Bearer+Tenant | — | `LeadDetailResponse` | Página lead (Resumen: datos+score+autonomy). 404 cross-tenant (RN-1) |
| PATCH | `/crm/leads/{id}/stage` | Bearer+Tenant | `StageTransitionRequest` | `StageTransitionResponse` | Override/transición. 409 optimistic lock (SC-5), 422 salto inválido (SC-2), 403 `→reservado`/drag bloqueado (RN-4) |
| POST | `/crm/leads` (EXTEND existente) | Bearer+Tenant | `LeadCreateRequest` | `LeadResponse` (201) | Alta (V5) — idempotency natural-key opcional |
| GET | `/crm/leads/{id}/transitions` | Bearer+Tenant | — | `TimelineResponse` | Historial (transitions + activity) |
| GET | `/crm/frozen` | Bearer+Tenant | — | `FrozenListResponse` | Recuperar (V4) — congelados + decidió-no |
| POST | `/crm/leads/{id}/diagnose` | Bearer+Tenant | — | `DiagnoseResponse` | AI diagnose brand-local (patrón engine closer_studio.diagnose) |
| POST | `/crm/leads/{id}/reactivate` | Bearer+Tenant | `ReactivateRequest` (objetivo) | `LeadResponse` | Vuelve al board en última etapa (RN-13) |
| POST | `/crm/leads/{id}/reservado-side-effect` | Bearer+Tenant | — | `LeadResponse` | **STUB MSW** (RN-5; webhook real = payment-adapter-mvp) |

> Reuse existentes: `GET /crm/leads` (list/lista view), `GET /crm/leads/{id}` (extiende), `POST /crm/leads`, `PATCH /crm/leads/{id}`.
> **Nota FE→BE path**: el FE actual (`use-leads`) llama `/api/v1/vitalia/crm/leads` pero el BE monta en `/api/v1/crm`. Pre-existing inconsistencia (§ 16 Open Questions). Esta story alinea las **nuevas** hooks al mount real `/api/v1/crm` y verifica live cuál resuelve en dev-app — el builder confirma con `curl` el path servido antes de cablear (DoD live-verify).

## 5. TypeScript Types (Frontend)

> camelCase mirror de los DTOs Pydantic. `03-arch-fe.md § types`. ISO 8601 datetimes como `string`. Tipos en `features/adrian/types/embudo.types.ts` + `embudo-schema.ts` (Zod).
- `Lead` (extend `crm-shared/types.ts`): `stage`, `score`, `temperature`, `operatedBy`, `channel`, `estimatedValue`, `currency`, `serviceInterest`, `buyingSignals`, `stageEnteredAt`, `isFrozen`, `frozenReason`, `depositStatus`, `version`.
- `BoardColumn`, `BoardResponse`, `LeadCard`, `LeadDetail`, `ScoreFactor`, `TimelineEntry`, `FrozenLead`, `Diagnose`, `StageTransitionPayload`.
- Zod: `newLeadSchema` (nombre*, canal*, teléfono/email ≥1, etapa, servicio, etiquetas, notas), `overrideReasonSchema` (reason required min 1).

## 6. Repository Interfaces (BE)

> Async, `tenant_id` en cada método (incl. `get_by_id`). `03-arch-be.md § 6`.
- `LeadRepository` (EXTEND `lead_repository.py`): `update_stage(lead_id, *, tenant_id, to_stage, reason, triggered_by, expected_version, actor_user_id) -> Lead` (optimistic lock — `WHERE version = :expected_version`, returns rowcount; 0 → conflict); `list_for_board(*, tenant_id, filters, sort) -> list[Lead]`; `freeze(lead_id, *, tenant_id, reason)`; `reactivate(lead_id, *, tenant_id)`. PII pgcrypto preservado en reads.
- `LeadStageTransitionRepository` (NEW): `record(*, tenant_id, lead_id, from_stage, to_stage, triggered_by, reason, score, actor_user_id) -> LeadStageTransition`; `list_for_lead(lead_id, *, tenant_id) -> list[...]`.
- `LeadActivityRepository` (NEW): `record(...)`; `last_for_lead(lead_id, *, tenant_id)`; `list_for_lead(...)`.
- Funnel repos = **NO** `PhiRepositoryBase` (non-PHI, single tenant filter). Arch test `test_phi_dual_filter` no aplica a estos (no son PHI).

## 7. Application Services (BE)

> `03-arch-be.md § 7`. Transaction boundaries: 1 transición = lead.update + transition.record + activity.record en una sesión (committing dependency).
- `FunnelService` (NEW): `get_board(...)`, `transition_stage(...)` (valida `allowed_next` → 422 con `allowed_next`; `→reservado` manual → 403; optimistic lock → 409; retroceso/salto → require reason; emite audit_log + telemetry + outbox event `lead_stage_changed`; inyecta override_context al wire agentic), `create_lead(...)` (extend), `freeze_sweep(...)` (auto-freeze RN-13 — evaluado on-read + worker stub), `reactivate(...)`.
- `LeadScoreService` (NEW): glass-box determinista (recencia + buying_signals + etapa). `compute(lead, signals) -> (score, breakdown)`. SIN ML (research § 5.3). Recalcula en read-time + en cada transición.
- `DiagnoseService` (NEW brand-local): genera recomendación estructurada desde el read-model del lead (patrón engine closer_studio.diagnose). Esta story: regla determinista (no LLM call obligatoria — si sales_agent live, puede delegar).
- **`allowed_next` SSoT** (NEW `crm/domain/funnel_machine.py`): `STAGE_MACHINE: dict[stage, list[allowed_next]]` + `SLA_DAYS: dict[stage, {green, amber, red}]` (RN-11: 7/7/5/14) + `FREEZE_RULES` (14d/30d/2×SLA — RN-13).
- **Idempotency**: `PATCH /stage` usa optimistic lock `version` como dedup natural (re-submit con version vieja → 409). `POST /leads` → idempotency natural-key opcional (phone+tenant). `reservado-side-effect` stub idempotente.

## 8. Agentic Surfaces

> Owner: `builder-agentic` (Opus, R23). Auditor: `auditor-agentic` (Opus). **Ticket SEPARADO** de BE/FE (T-AG-1). `production_code: true` → model_preference Opus HARD.
>
> **Scope minimal**: esta story NO toca el LangGraph runtime del sales_agent ni el schema `agent_state_checkpoints` (§3 protected). El único trabajo agentic es un **wire thin brand-local** que implementa RN-4.1: cuando un humano hace override manual de etapa con razón, esa razón se debe inyectar como contexto en el próximo turno del agente (no reiniciarlo).

### 8.1 LangGraph state
- **NO se modifica.** El override-context se persiste en `vitalia_lead_stage_transition.reason` (brand-local). El wire lo lee y lo pasa como señal al pipeline del sales_agent en el próximo turno vía el read del checkpoint (campo de lectura existente `metadata_info` o `resume_objective`-style del checkpoint engine — NO se añade columna).

### 8.2 Topology
- [x] **Sin topología nueva.** Reusa el runtime sales_agent existente. El wire es un servicio brand-local (`sales_agent/application/services/override_context_wire.py`) que el `FunnelService.transition_stage` invoca tras un override manual.

### 8.4 Tools
- **NO se crea tool nuevo.** El override no es una acción del agente; es contexto que el agente lee. El wire escribe el contexto donde el próximo turno del agente lo va a leer (brand-local lookup que el system_prompt builder del sales_agent ya consulta, o `metadata_info` del checkpoint).

### 8.5 Prompt cache slots
- **NO se toca.** El override-context es señal volátil per-turn (slot variable), NO entra en prefix cacheable. Si en una iteración futura el sales_agent inyecta esto en el system prompt, va en el slot volátil (último, NO cacheable) — documentado para el builder-agentic.

### 8.6 Checkpointer
- N/A esta story (no se corre grafo nuevo). El checkpoint engine `agent_state_checkpoints` ya usa el saver de producción del sales_agent.

### 8.8 Observability writes
- El override + handover queda asentado en `vitalia_lead_activity` (atribuido `🙋 humano → 🤖 Adrián`) + audit_log. Telemetry `embudo_stage_changed{from,to,trigger:manual_override}`. NO toca `copilot_trace_event` / `sales_agent_trace_event` (engine).

### 8.9 Eval goldens
- **N/A** esta story (no se modifica prompt ni specialist). Si el wire toca el system_prompt builder en una iteración futura → ≥3 goldens. Por ahora el ticket es persistencia + lectura, no generación.

### 8.11 Skill decisions referenced
- `sales-agent-expert`: NO modificar `agent_state_checkpoints` schema (§3 protected) · NO importar `sales_agent/` desde `crm/` (cross-module ban; el wire vive en `sales_agent/` y `crm/FunnelService` lo invoca vía port o domain event) · override-context es brand-local, no engine lift.
- **Decisión de acoplamiento**: `crm/FunnelService` → `sales_agent` wire vía **domain event** (`lead_stage_changed` por outbox) que el sales_agent brand-extension consume, O vía port en `core/luana-core-platform/links/ports/`. Evita cross-module import directo (backend-ddd). El builder-agentic decide event vs port en technical_design; recomendación: **domain event** (`lead_stage_overridden`) emitido por FunnelService, consumido por subscriber en `sales_agent/` que escribe el contexto.

---

## 9. Migration Notes

- 1 migration idempotent raw SQL: `ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS ...` (×~18 columnas, defaults backward-compatible) + `CREATE TABLE IF NOT EXISTS vitalia_lead_stage_transition (...)` + `CREATE TABLE IF NOT EXISTS vitalia_lead_activity (...)` + indexes `IF NOT EXISTS`.
- NUNCA `op.create_table()` / `sa.Enum(create_type=True)`. Stage/triggered_by/etc. = `VARCHAR` (enum lógico en domain, no PG type).
- Prod-clone test: `make verify-vitalia-migration-idempotency` (o steps manuales `docs/domains/migrations.md` — runbook MISSING, usar clone DB workflow de `backend-migrations.md`).
- Backfill: leads existentes con `status` flat → map a `stage` (`new→interesado`, `contacted→calificando`, `qualified→consulta_agendada`, `converted→reservado`, `lost→decidio_no`) en la misma migration (UPDATE idempotente).

## 9.5 Tests audit (default flip)

- [x] **No aplica** — 03-arch.md NO flipea defaults de feature flags side-effect (`USE_*_PATTERN_*`, etc.). El STUB MSW de `reservado-side-effect` es un endpoint nuevo, no un flag flip.

## 10. File Structure

> NEW vs MODIFIED. Detalle FE `03-arch-fe.md § 10`, BE `03-arch-be.md § 10`.

**Backend** (`vitalia/backend/src/modules/vitalia/crm/`):
- MODIFIED: `domain/lead.py`, `application/dto/lead_dto.py`, `application/services/lead_service.py`, `infrastructure/persistence/lead_repository.py`, `api/router.py`
- NEW: `domain/{lead_stage_transition.py, lead_activity.py, funnel_machine.py}`, `application/services/{funnel_service.py, lead_score_service.py, diagnose_service.py}`, `application/dto/{board_dto.py, transition_dto.py, frozen_dto.py}`, `infrastructure/persistence/{lead_stage_transition_repository.py, lead_activity_repository.py}`, `infrastructure/persistence/models/{lead_stage_transition_model.py, lead_activity_model.py}`, migration `alembic/versions/{rev}_adrian_embudo_funnel.py`
- NEW (agentic, separate ticket): `sales_agent/application/services/override_context_wire.py` + subscriber

**Frontend** (`vitalia/frontend/src/`):
- NEW route: `app/[tenantId]/(shell-organism)/adrian/embudo/page.tsx` (board) · `embudo/[leadId]/{resumen,historial}/page.tsx` · `embudo/nuevo/page.tsx` · `adrian/recuperar/page.tsx`
- NEW feature: `features/adrian/components/embudo/{AdrianEmbudoView, KanbanBoard, PipelineColumn, LeadCard, LeadsTable, EmbudoHeader, EmbudoFilters, EmbudoMetrics, SortBySelect, OverrideReasonDialog}.tsx` + `embudo/lead/{LeadWorkspace, ResumenView, HistorialView, LeadSummaryHeader, ScoreBreakdown}.tsx` + `embudo/nuevo/NewLeadPage.tsx` + `components/recuperar/{RecuperarView, FrozenLeadRow}.tsx`
- NEW api: `features/adrian/api/{embudo-board, lead, lead-stage-mutation, frozen, diagnose, create-lead, embudo-server}.ts`
- NEW shared: `components/shared/score/ScoreDonut.tsx` + `lib/channels/channel-meta.ts` (MODIFY `components/shared/shell-organism/ChannelBadge.tsx` para consumir channel-meta)
- MODIFY: `lib/shell-routes.ts` (agregar `embudo`+`recuperar` a AGENT_SUBTABS adrian si falta), `features/adrian/index.ts` (public API), `features/crm-shared/types.ts` (extend Lead)
- NEW mocks: `mocks/handlers/embudo.ts` (MSW — board, stage, frozen, reservado-stub)

## 11. Cross-Cutting Concerns

- **Tenant isolation** — toda query `WHERE tenant_id = :tenant_id` (incl. `get_by_id`, `update_stage`, board). Cross-tenant → 404 genérico (RN-1, SC-4). Funnel repos reciben `tenant_id` required.
- **PHI / non-PHI** — Lead = **non-PHI** (marketing prospect). NO dual `clinic_id` filter en funnel. **PERO**: `name`/`email`/`phone`/`notes` siguen pgcrypto-encrypted (PII) en `vitalia_leads`. Campos funnel = plaintext NO-PII. El historial V3 muestra mensajes de conversación → SI muestra contenido clínico del paciente convertido, eso es PHI → pero el spec RN-2 establece firewall: el embudo opera datos de interés (procedimiento/presupuesto/agenda), NUNCA clínicos; el link al Inbox (PHI-gated) abre la conversación real allá. **Resolución: el Historial del embudo NO renderiza datos clínicos** — solo transitions + activity (interés/comercial). El contenido de mensajes WA/IG con posible PHI vive en Inbox (dual-filter). El builder NO debe traer el body de mensajes clínicos al timeline del embudo.
- **Currency** — DTOs con monetary fields (`estimated_value`) incluyen `currency: str | None`. ETL/storage mantiene source currency. FE `formatMoney(amount, currency ?? useTenantLocale().currency)` (RN-15). NUNCA hardcode `'USD'` (tenant Sanaré = PEN).
- **Master data** — `DateTime(timezone=True)`, store UTC, display vía `useTenantLocale()`/`formatTenantDate*()`. Time-in-stage = `now() − stage_entered_at` calculado read-time.
- **Spanish neutro LatAm** — UI strings + microcopy (§ Microcopy del spec) + `description_es` de activity. Sin voseo. Tildes + ¿¡. Output del sales_agent (override handover message) respeta voz tenant (excepción sales-agent).
- **PII** — `response_model=` allowlist en cada route. Lead name real va en DTO (non-PHI); masking es responsabilidad del FE (PiiMaskedSpan). NO loguear name en telemetry (bucketed/sin PII). Audit log sync write en transiciones (business event, no PHI dual-filter — pero usa AuditLogRepository existente).
- **Native-first dev** — lint/tests native (`${WS}/.venv/bin/{ruff,pytest}`, `npx {tsc,eslint,vitest,playwright}`). NUNCA docker exec.
- **Anti-orphan (CONN)** — ver § Integration design.

## 12. Architecture Fitness Impact

- **Corren contra el cambio** (BE): `test_response_model_required.py`, `test_lead_repository_is_not_phi_repository.py`, `test_phi_dual_filter.py` (funnel repos NO-PHI → no deben heredar PhiRepositoryBase; arch test verifica que solo repos PHI lo heredan), DDD boundary tests (no cross-module import `crm`↔`sales_agent` directo → usar event/port), SA 2.0 + no-hard-delete.
- **Corren contra el cambio** (FE): `test_no_hardcoded_colors` (ChannelBadge + channel-meta usan CSS vars/registro), `test_react_query_keys_convention`, `test_features_no_cross_imports`, `test_no_phi_in_url_params` (`leadId` = UUID, RN-16), `test-no-clerk-organizations`.
- **Allowlist updates**: ninguna esperada (allowlists shrink-only). Si el override event introduce un cross-module touch, debe ir vía port/event (no allowlist grow).

## 13. capability YAML + modules/{m}.md Updates Required (post-merge)

- `vitalia/docs/product/capabilities/crm/adrian-embudo.yaml` — completar `scenarios[]` (SC-1..SC-11 + sub-cat), `access` (rol coordinadora), `business_rules` (RN-1..19), `Surface{Config/Backend/Frontend}`, `Test coverage` (vitest/playwright/pytest paths), `Dependencies`, `Scenarios live` (dev_app_verified evidence).
- `vitalia/docs/product/modules/crm.md` — agregar sección funnel agent-operated (si el archivo existe).
- Header `# cap: crm.adrian-embudo` (Python líneas 1-3) / `// cap: crm.adrian-embudo` (TS/TSX) en TODO archivo nuevo (bidirectional code↔cap v3.2).

## 14. Test Surfaces (TDD-mandatory)

- **BE**: domain (funnel_machine allowed_next, scorer determinista, freeze rule) → infrastructure (repos optimistic lock, transition record) → application (FunnelService transition happy/422/409/403, freeze sweep) → API/E2E (cross-tenant 404, response_model). RED first per capa.
- **FE**: hook (`use-embudo-board`, `use-lead-stage-mutation` con MSW) → component (LeadCard, ScoreDonut, KanbanBoard drag, OverrideReasonDialog, EntitySubNavBar workspace) → store (drag/filter Zustand).
- **E2E Playwright** (anti-burbuja base.ts): `embudo-board.spec.ts`, `embudo-lead-workspace.spec.ts`, `embudo-nuevo-lead.spec.ts`, `embudo-override-drag.spec.ts`, `recuperar.spec.ts` + visual goldens (D.16 map) light+dark + axe.
- **Agentic** (T-AG-1): test del subscriber/wire (override_context persistido + leído en próximo turno) — `test_manual_override_feeds_agent_context.py` (SC-1b).

## 15. Research Notes (DATE-AWARE — accessed 2026-06-03)

- **SLA / freeze / orden de cards** — `research/06-pipeline-sla-benchmark.md` (accessed 2026-06-03). Fuentes: support.pipedrive.com (rotting + ordering), outreach.ai (deal-aging 14d/30d), rework.com, HBR (speed-to-lead). Takeaway: SLA dental verde 7/7/5/14d; freeze 14d sin actividad ∨ 2×SLA ∨ 30d duro; orden = antigüedad-en-etapa desc (urgente arriba). Por qué: convención del rubro; reset-por-actividad (Pipedrive); Adrián es IA → SLA mide avance, no primer toque.
- **Lead detail UX** — `research/05-lead-detail-benchmark.md`. HubSpot/Clientify/Pabau/LeadMAX → 2 tabs (no 3), score = bloque no tab, timeline al centro. Por qué: convención cross-tool.
- **Agentic CRM patterns** — `research/03-agentic-best-practices.md` (state of the art 2025-2026). Autonomía 3-tier, glass-box scoring sin ML (compound signal), exception-based approval, takeover preserva contexto. Aplicado: RN-9 (gated autonomy), Score glass-box (RN-Score), RN-10 (takeover), RN-4.1 (override feeds agent).
- **Engine substrate** — `research/02-core-engine.md`. closer_studio byte-idéntico al legacy; `AgentStateCheckpointModel.current_stage` es el vehículo agent-operating; sustrato vertical-agnóstico salvo labels+prompts. Decisión: consumir read-only, brand-local el funnel dental.
- **Knowledge cutoff disclosure**: Opus 4.8 cutoff Jan 2026. Los patrones agentic/SLA post-cutoff fueron tomados de los research files de la story (investigados live por /po-ux 2026-06-02/03), no de memoria del modelo. LangGraph/deepagents canonical NO se consultaron porque esta story NO crea grafo nuevo (wire thin only).

## 16. Open Questions for PM

1. **FE→BE path inconsistencia (pre-existing):** `use-leads` llama `/api/v1/vitalia/crm/leads` pero el BE monta crm en `/api/v1/crm`. ¿El path `/vitalia/` resuelve por algún rewrite/proxy no encontrado, o el inbox usa otro mount? El builder DEBE confirmar con `curl` en dev-app cuál path responde antes de cablear las nuevas hooks (DoD live-verify). Si `/api/v1/vitalia/crm` NO resuelve hoy → el inbox leads list podría estar roto live (fuera de scope, flag a /pm-vitalia).
2. **ChannelBadge lift cross-brand:** recomiendo **brand-local** (`channel-meta` en `vitalia/frontend/src/lib/channels/`) por ahora; lift a `@luana/ui-kit` solo cuando una 2ª brand lo necesite (`/pm-luana`). NO creo proposal en esta story — ¿OK?
3. **modules/crm.md existencia:** verificar si `vitalia/docs/product/modules/crm.md` existe para actualizar narrativa post-merge; si no, ¿se crea?
4. **override-context wire (RN-4.1) cuando sales_agent no está live:** el wire persiste el contexto (real), pero el "Adrián ajusta su próximo paso" solo es observable cuando Inbox/sales_agent estén live. En esta story se verifica que el contexto **se persiste + se asienta en el Historial** (SC-1b BE); el efecto conversacional real queda demostrado cuando el agente conversacional esté operativo. ¿OK como alcance?

---

## Integration design (CONN — anti-orphan, ningún surface llega a `done` como isla)

**Home cap:** `crm/adrian-embudo` (zona Agentes · caja Adrián). `cap_target` declarado en frontmatter.

**Reachability path concreto (board → lead → back):**
1. Usuario entra a `/{tenant}/adrian/embudo` (Ribbon Adrián → SubTab Embudo) → `AdrianEmbudoView` (board) ← `EmbudoPlaceholder.tsx` se reemplaza por sentinel "moved to dedicated route".
2. Click LeadCard → `router.push('/{tenant}/adrian/embudo/{leadId}/resumen')` → `LeadWorkspace` (EntitySubNavBar pinta `[‹ Embudo] · nombre · Resumen·Historial`).
3. `[‹ Embudo]` → vuelve al board. KPI 🧊 congeladas → `/{tenant}/adrian/recuperar` (sub-tab hermana).
4. `+ Nuevo lead` → `/{tenant}/adrian/embudo/nuevo` → submit → redirect `/embudo?highlight={id}` → card resaltada.

**Consumers (≥1 real por surface):**
- Board endpoint `GET /crm/board` ← consumido por `use-embudo-board` hook ← `AdrianEmbudoView`.
- `PATCH /crm/leads/{id}/stage` ← `use-lead-stage-mutation` ← LeadCard drag + OverrideReasonDialog + ResumenView "Mover de etapa".
- `lead_stage_overridden` event ← consumido por `sales_agent` subscriber (override_context_wire).
- ChannelBadge (extended) + channel-meta ← consumido por LeadCard + LeadsTable + LeadSummaryHeader + FrozenLeadRow.

**Registration points (notarized):**
- BE: rutas nuevas en `crm/api/router.py` (ya `include_router` en main.py `/api/v1/crm`). NO nuevo include_router (extiende el existente).
- FE nav: rutas en App Router route group `(shell-organism)/adrian/{embudo,recuperar}` — static segments toman precedencia sobre dispatcher dinámico (ADR-004 § 3.1). `AGENT_SUBTABS.adrian` debe incluir `embudo`+`recuperar` en `lib/shell-routes.ts` (verificar/agregar). NO SubSubTabsBar (board single panel; `[leadId]` = N3-dynamic workspace).
- FE public API: `features/adrian/index.ts` re-exporta `AdrianEmbudoView`, `RecuperarView`.
- Agentic: subscriber registrado vía outbox/event bus (NO nuevo tool en EP-3; es subscriber de domain event).

**Verificación de no-isla:** cada archivo nuevo tiene ≥1 consumer real arriba. El placeholder `EmbudoPlaceholder` se retira en el mismo PR.

---

## Architecture Decisions

### adr_004_compliance: **full**

Las 9 secciones del ADR-vitalia-004 se cumplen:
1. **Routing** ✓ — route group `(shell-organism)/adrian/embudo/page.tsx` static + `[leadId]/{resumen,historial}` (N3-dynamic workspace vía página, opción C ratificada — NO Sheet drawer, NO SubSubTabsBar para el board) + `/nuevo` + `adrian/recuperar`. Server Component default + SSR initial state. PHI nunca en URL (`leadId`=UUID).
2. **FSD-Lite** ✓ — `features/adrian/components/embudo/`, `/recuperar/`, `api/`, `hooks/`, `store/`, `types/`. Componentes shell en `components/shared/`. Sin cross-feature imports.
3. **Client root** ✓ — `AdrianEmbudoView.tsx` `"use client"` + props hidratación.
4. **Data layer** ✓ — React Query (board/lead/frozen/transitions) + Zustand (drag/toggle/filtros UI). Sin mezclar.
5. **Forms** ✓ — RHF+Zod (`newLeadSchema`, `overrideReasonSchema`). Submit-driven (alta atómica, override atómico). Toasts sonner.
6. **BE DDD Inside-Out** ✓ — domain (funnel_machine, entities) → infra (repos + models + migration) → application (services) → api (thin). Funnel repos NO-PHI (no PhiRepositoryBase — son non-PHI, arch test lo permite). Audit log sync write en transiciones.
7. **Migrations** ✓ — raw SQL idempotent `IF NOT EXISTS`. Sin `op.create_table()`/`sa.Enum`.
8. **Telemetría** ✓ — `vitalia_growth_studio_event` (emitter shipped) bucketed amounts. Eventos `embudo_*` (§ spec Telemetría).
9. **Tests** ✓ — Vitest + Playwright funcional + visual goldens (D.16 map) + axe + BE pytest cross-tenant + arch fitness EXTEND.

**Divergencias documentadas:**
- **§ 3.6 PhiRepositoryBase**: los repos del funnel NO heredan `PhiRepositoryBase` — **correcto** porque Lead es non-PHI (single tenant filter), no es divergencia sino el caso "Repositories no-PHI" que el propio ADR § 3.6 contempla. El LeadRepository existente es PII (pgcrypto) pero NO PHI — preservado.
- **§ 3.1 detalle pattern**: el board es **single panel SIN SubSubTabsBar** (el Tablero es directamente el board, spec V1); el detalle del lead es **N3-dynamic vía página con URL propia** (opción C ratificada), NO Sheet drawer (el ADR § 3.1 contempla N3-dynamic con Sheet O página). Recuperar es **sub-tab hermana** (N2), no N3. Todo dentro del patrón, sin divergencia que requiera rationale extra.

### Decisión clave: scope 1-story, ≤10 tickets
Spec § Decisiones #3 resolvió **1 sola story** (no S4a/S4b). Esta arquitectura usa **9 tickets cohesivos** (ver `06-tickets.yaml`) — bajo el cap de 10. DAG permite paralelismo BE/FE/agentic.

### Decisión clave: engine consumo = read-only, funnel = brand-local NET-NEW
El sustrato agentic (`agent_state_checkpoints`, closer_studio) se consume como **referencia de patrón + read-model**, NO se monta el router engine (sync/auth mismatch) NI se modifica su schema (§3 protected). El funnel dental de 6 etapas + scorer + freeze + transition audit son brand-local NET-NEW (vertical-specific, sin mirror cross-brand). Esto es lo que `research/02-core-engine § Boundary REUSE vs BUILD` recomienda explícitamente.

---

## Test Construction Plan

> Consumido por `builder-*` (technical_design phase) + `gate-runner`. Orden de creación RED→GREEN por capa. Mapping completo Gherkin→spec→assertions en `04-validators.yaml § test_construction_plan`.

**Creation order (TDD RED-first):**
1. **BE domain**: `funnel_machine_test.py` (allowed_next, SLA table, freeze rule) → `lead_score_service_test.py` (glass-box determinista, breakdown).
2. **BE infra**: `lead_repository_test.py` (update_stage optimistic lock → 0 rowcount = conflict; list_for_board sort) → `lead_stage_transition_repository_test.py`.
3. **BE app**: `funnel_service_test.py` (transition happy SC-1, 422 salto SC-2, 409 lock SC-5, 403 →reservado, freeze sweep SC-freeze, reactivate).
4. **BE api/e2e**: cross-tenant 404 SC-4, response_model present, 422 body `{allowed_next}`.
5. **Agentic**: `test_manual_override_feeds_agent_context.py` (SC-1b — override_context persisted + readable next turn).
6. **FE hook**: `use-embudo-board.test.ts`, `use-lead-stage-mutation.test.ts` (MSW: 200/409/422).
7. **FE component**: `LeadCard.test.tsx`, `ScoreDonut.test.tsx`, `KanbanBoard.test.tsx` (drag KeyboardSensor SC-10), `OverrideReasonDialog.test.tsx`, `EntitySubNavBar` workspace reuse.
8. **FE store**: drag/filter Zustand.
9. **E2E Playwright** (base.ts anti-burbuja): board, lead-workspace, nuevo-lead, override-drag, recuperar + visual goldens + axe.

**POMs required**: `EmbudoBoardPage`, `LeadWorkspacePage`, `NewLeadPage`, `RecuperarPage` (e2e/pages/).
**Fixtures required**: dataset canónico (§ Dataset spec — 11 leads dental PEN + 2 frozen) seed BE + MSW handlers FE (`mocks/handlers/embudo.ts`).
