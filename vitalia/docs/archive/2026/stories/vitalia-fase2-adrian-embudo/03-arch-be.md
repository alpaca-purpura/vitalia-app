---
story_id: vitalia-fase2-adrian-embudo
surface: backend
parent: 03-arch.md
owner_builder: builder-backend
owner_auditor: auditor-backend
---

# 03-arch-be.md — Backend (crm funnel) · Embudo de Adrián

> Detalle BE para `builder-backend`. Consolidado en `03-arch.md`. Módulo `crm` (EXTEND). Lead = **non-PHI** (single `tenant_id` filter; PII pgcrypto preservado en name/email/phone/notes). Mount existente `/api/v1/crm`.

## 1. Domain Entities

### `Lead` (EXTEND `crm/domain/lead.py` — dataclass puro, sin ORM)
Agregar (todos default → migration backward-compatible):
```python
stage: str = "interesado"                 # interesado|calificando|consulta_agendada|plan_presentado|reservado|decidio_no
stage_entered_at: datetime | None = None  # time-in-stage SLA (RN-11)
score: int = 0                            # 0-100 glass-box
temperature: str = "cold"                 # hot|warm|cold
operated_by: str = "agent"                # agent|human (espejo handler_mode checkpoint, RN-12)
channel: str | None = None                # canal origen (ChannelBadge)
service_interest: str | None = None
assigned_doctor_id: UUID | None = None
estimated_value: Decimal | None = None
currency: str | None = None               # PEN/MXN (RN-15) — NUNCA default "USD"
buying_signals: list[str] = field(default_factory=list)  # pregunto_precio|urgencia|presupuesto_ok|...
is_frozen: bool = False
frozen_reason: str | None = None          # inactividad_lead|sin_respuesta_presupuesto|agente_trabado
frozen_at: datetime | None = None
closure_reason: str | None = None
reactivation_cohort_at: datetime | None = None
deposit_status: str | None = None         # pending|received (STUB MSW esta story)
version: int = 1                          # optimistic lock (RN-4 / SC-5)
is_blacklisted: bool = False              # RN-13
```
> `id`, `tenant_id` (UUID mandatory), `deleted_at`, `created_at`, `updated_at`, `name/email/phone/source/status/notes` ya existen. `status` flat se MANTIENE (back-compat) pero `stage` es el SSoT del funnel.

### `LeadStageTransition` (NEW `crm/domain/lead_stage_transition.py`)
```python
@dataclass
class LeadStageTransition:
    id: UUID
    tenant_id: UUID                # mandatory
    lead_id: UUID
    from_stage: str | None
    to_stage: str
    triggered_by: str              # agent|manual_override|webhook|reactivation|auto_freeze
    reason: str | None             # override_context RN-4.1 (NO PHI — motivo comercial)
    score_at_transition: int | None
    actor_user_id: UUID | None
    occurred_at: datetime
    deleted_at: datetime | None = None
```

### `LeadActivity` (NEW `crm/domain/lead_activity.py`) — micro-log atribuido (§ Procedencia)
```python
@dataclass
class LeadActivity:
    id: UUID
    tenant_id: UUID                # mandatory
    lead_id: UUID
    actor: str                     # agent|human|lead|system
    kind: str                      # message|stage_move|info_sent|deposit|note
    description_es: str            # Spanish neutro, 3ª persona, NUNCA PHI clínico
    occurred_at: datetime
    deleted_at: datetime | None = None
```
> ⚠️ NO confundir con `crm/domain/activity_event.py` (existente, PHI dual-filter, conversaciones inbox). `LeadActivity` es non-PHI, comercial, single tenant filter.

### `funnel_machine.py` (NEW `crm/domain/funnel_machine.py`) — SSoT determinista
```python
STAGE_MACHINE: dict[str, list[str]] = {
    "interesado":        ["calificando", "decidio_no"],
    "calificando":       ["consulta_agendada", "decidio_no"],
    "consulta_agendada": ["plan_presentado", "decidio_no"],
    "plan_presentado":   ["reservado", "decidio_no"],   # reservado solo por webhook (RN-5), NO manual
    "reservado":         [],                              # terminal-éxito
    "decidio_no":        [],                              # terminal
}
# allowed_next para override: adyacente fwd permitido directo; salto → confirm+reason; back → reason.
# reservado NUNCA en allowed_next manual (RN-4: drag→reservado = 403/tooltip).

SLA_DAYS: dict[str, dict[str, int]] = {   # RN-11 (green ≤ / amber > / red >)
    "interesado":        {"green": 7, "amber": 7, "red": 14},
    "calificando":       {"green": 7, "amber": 7, "red": 14},
    "consulta_agendada": {"green": 5, "amber": 5, "red": 10},
    "plan_presentado":   {"green": 14, "amber": 14, "red": 21},
}
FREEZE_RULES = {"no_response_days": 14, "hard_days": 30, "sla_multiplier": 2.0}  # RN-13
HOT_BOARD_STAGES = ["interesado", "calificando", "consulta_agendada", "plan_presentado", "reservado"]  # RN-18
```

## 2. SQLAlchemy 2.0 Models

- **EXTEND `vitalia_leads`** vía migration (ADD COLUMN IF NOT EXISTS). Model: `crm/infrastructure/persistence/models/lead_model.py` — agregar columnas. PII (`name/email/phone/notes`) ya pgcrypto; columnas funnel = plaintext. `version INTEGER NOT NULL DEFAULT 1`. `buying_signals JSONB DEFAULT '[]'`. `estimated_value NUMERIC`. Timestamps `DateTime(timezone=True)`.
- **NEW `vitalia_lead_stage_transition`** — `mapped_column()` SA 2.0. PK `id UUID`, `tenant_id UUID NOT NULL`, FK `lead_id` (sin JOIN cross-module; resolve en app), `reason TEXT` (⚠️ campo `reason` NO `notes` → evita falso positivo arch test PHI pgcrypto `notes\s+TEXT`). Index `ix_lst_tenant_lead (tenant_id, lead_id, occurred_at DESC)`.
- **NEW `vitalia_lead_activity`** — idem. Index `(tenant_id, lead_id, occurred_at DESC)`.
- SA 2.0 only: `select(LeadStageTransitionModel).where(...)`. NUNCA `session.query()`.

## 3. Pydantic v2 DTOs (`crm/application/dto/`)
Todos `model_config = ConfigDict(from_attributes=True)`. Tipos explícitos.

- **EXTEND `LeadResponse`** (`lead_dto.py`): + `stage, score, temperature, operated_by, channel, estimated_value (Decimal|None), currency (str|None), service_interest, buying_signals (list[str]), stage_entered_at (datetime|None), is_frozen, frozen_reason, deposit_status, version`.
- **EXTEND `LeadCreateRequest`**: + `stage (default "interesado"), channel, service_interest, tags (list[str]), estimated_value, currency`.
- **NEW `board_dto.py`**: `BoardColumn{stage, label, count, sum_value (Decimal), currency (str|None), over_sla_count, leads: list[LeadCardDTO]}` · `LeadCardDTO{id, name, stage, score, temperature, channel, estimated_value, currency, operated_by, buying_signals, stage_entered_at, sla_state (green|amber|red), last_activity (str|None), deposit_status, is_highlighted}` · `BoardKpis{active, agent_count, human_count, hot, warm, cold, avg_score, deposit_rate, frozen_count}` · `BoardResponse{columns, kpis}`.
- **NEW `transition_dto.py`**: `StageTransitionRequest{to_stage: str, reason: str|None, note: str|None, version: int, triggered_by: str = "manual_override"}` · `TransitionDTO{from_stage, to_stage, triggered_by, reason, occurred_at}` · `StageTransitionResponse{lead: LeadResponse, transition: TransitionDTO}` · `TimelineEntry{actor, kind, description_es, occurred_at, signal: str|None}` · `TimelineResponse{events: list[TimelineEntry]}`.
- **NEW `lead_detail_dto.py`**: `ScoreFactor{label, delta: int}` · `AutonomyInfo{operated_by, can: list[str], needs_ok: list[str]}` · `LeadDetailResponse{lead: LeadResponse, score_breakdown: list[ScoreFactor], autonomy: AutonomyInfo}`.
- **NEW `frozen_dto.py`**: `FrozenLeadDTO{id, name, channel, stage, frozen_reason, frozen_at, diagnosis: str|None, closure_reason: str|None}` · `FrozenListResponse{recien_congelados: list[...], decidio_no: list[...]}` · `DiagnoseResponse{recommendation_es: str, suggested_action: str}` · `ReactivateRequest{objective: str|None}`.
- **422 body** (salto inválido): `{"detail": "...", "allowed_next": ["calificando"]}`.

## 4. API Routes (`crm/api/router.py` EXTEND)
Ver `03-arch.md § 4` tabla. Todas `/api/v1/crm/...`, Bearer + `X-Tenant-ID` (non-PHI → usar `_resolve_context_sync` existente; `X-Clinic-ID` opcional). `response_model=` mandatory.
- Wiring DI: `FunnelService(lead_repo, transition_repo, activity_repo, scorer, audit_repo, telemetry, event_bus)` con `Depends(get_async_session_committing)`.
- `PATCH /leads/{id}/stage`: validar `allowed_next` → 422 `{allowed_next}` (SC-2); `→reservado` manual → 403 (RN-4); optimistic lock conflict → 409 (SC-5); retroceso/salto → require `reason` (400 si falta); emite audit_log sync + telemetry + outbox `lead_stage_overridden` (si manual con reason → wire agentic).

## 5. (n/a — frontend)

## 6. Repository Interfaces (`crm/infrastructure/persistence/`)
Async, `tenant_id` required en cada método (incl `get_by_id`).
- **`LeadRepository` EXTEND**: `update_stage(lead_id, *, tenant_id, to_stage, expected_version, score, actor_user_id) -> Lead | None` (raw SQL `UPDATE ... WHERE tenant_id=:t AND id=:id AND version=:expected_version AND deleted_at IS NULL` → rowcount 0 = conflict → caller raises 409; on success `version = version + 1`, `stage_entered_at = now()`). `list_for_board(*, tenant_id, stage_filter, origin, search, sort) -> list[Lead]` (sort `stage_age_desc` default = `ORDER BY stage_entered_at ASC` — más viejo arriba RN-17). `freeze(lead_id, *, tenant_id, reason)`, `reactivate(lead_id, *, tenant_id)`. Mantener pgcrypto decrypt en reads.
- **`LeadStageTransitionRepository` NEW**: `record(...) -> LeadStageTransition`, `list_for_lead(lead_id, *, tenant_id)`.
- **`LeadActivityRepository` NEW**: `record(...)`, `last_for_lead(lead_id, *, tenant_id) -> LeadActivity | None`, `list_for_lead(...)`.
- ❌ NO `PhiRepositoryBase` (non-PHI). ❌ NO cross-module JOIN (assigned_doctor_id resuelto en app si se necesita nombre del doctor — pero el board NO trae nombre doctor, solo id).

## 7. Application Services (`crm/application/services/`)
- **`FunnelService` NEW**: orquesta. `transition_stage()` en 1 transacción: validar machine → recompute score → `lead_repo.update_stage` (lock) → `transition_repo.record` → `activity_repo.record` → audit_log sync → telemetry → si `triggered_by=manual_override` con reason → emite `lead_stage_overridden` event (outbox) para el wire agentic. `get_board()` arma columnas (solo HOT_BOARD_STAGES, RN-18) + KPIs + sla_state read-time. `freeze_sweep()` (RN-13 — evaluado on-read del board + worker stub ARQ). `create_lead()` extend.
- **`LeadScoreService` NEW**: `compute(lead, signals) -> (int, list[ScoreFactor])`. Determinista glass-box (research § 5.1): base por etapa + Σ(buying_signals weights: pregunto_precio +25, respondio_rapido +15, campana_pagada +10, presupuesto_ok +20) − recencia penalty (sin_agendar −2/día capped). SIN ML.
- **`DiagnoseService` NEW**: regla determinista desde read-model (frozen_reason + stage + signals → recommendation_es). Patrón engine closer_studio.diagnose (referencia, no import).
- Transaction boundary: `get_async_session_committing` — todo en una sesión, commit al final.
- Idempotency: `version` optimistic lock = dedup natural en stage. `reservado-side-effect` stub idempotente (chequea `deposit_status` ya `received`).

## 9. Migration (`alembic/versions/{rev}_adrian_embudo_funnel.py`)
```python
def upgrade():
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS stage VARCHAR DEFAULT 'interesado'")
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS stage_entered_at TIMESTAMPTZ")
    # ... (×18 columnas, IF NOT EXISTS, defaults)
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_leads_tenant_stage ON vitalia_leads (tenant_id, stage, is_frozen)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_leads_tenant_stage_entered ON vitalia_leads (tenant_id, stage, stage_entered_at)")
    op.execute("CREATE TABLE IF NOT EXISTS vitalia_lead_stage_transition (id UUID PRIMARY KEY, tenant_id UUID NOT NULL, lead_id UUID NOT NULL, from_stage VARCHAR, to_stage VARCHAR NOT NULL, triggered_by VARCHAR NOT NULL, reason TEXT, score_at_transition INTEGER, actor_user_id UUID, occurred_at TIMESTAMPTZ NOT NULL, deleted_at TIMESTAMPTZ)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_lst_tenant_lead ON vitalia_lead_stage_transition (tenant_id, lead_id, occurred_at DESC)")
    op.execute("CREATE TABLE IF NOT EXISTS vitalia_lead_activity (id UUID PRIMARY KEY, tenant_id UUID NOT NULL, lead_id UUID NOT NULL, actor VARCHAR NOT NULL, kind VARCHAR NOT NULL, description_es TEXT NOT NULL, occurred_at TIMESTAMPTZ NOT NULL, deleted_at TIMESTAMPTZ)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_la_tenant_lead ON vitalia_lead_activity (tenant_id, lead_id, occurred_at DESC)")
    # Backfill status→stage (idempotent UPDATE)
    op.execute("UPDATE vitalia_leads SET stage = CASE status WHEN 'new' THEN 'interesado' WHEN 'contacted' THEN 'calificando' WHEN 'qualified' THEN 'consulta_agendada' WHEN 'converted' THEN 'reservado' WHEN 'lost' THEN 'decidio_no' ELSE 'interesado' END WHERE stage IS NULL OR stage = 'interesado'")
```
> NUNCA `op.create_table()` / `sa.Enum(create_type=True)`. Prod-clone: `backend-migrations.md` clone DB workflow.

## 10. File Structure (BE)
MODIFIED: `domain/lead.py`, `application/dto/lead_dto.py`, `application/services/lead_service.py`, `infrastructure/persistence/{lead_repository.py, models/lead_model.py}`, `api/router.py`.
NEW: `domain/{lead_stage_transition.py, lead_activity.py, funnel_machine.py}`, `application/dto/{board_dto.py, transition_dto.py, lead_detail_dto.py, frozen_dto.py}`, `application/services/{funnel_service.py, lead_score_service.py, diagnose_service.py}`, `infrastructure/persistence/{lead_stage_transition_repository.py, lead_activity_repository.py, models/{lead_stage_transition_model.py, lead_activity_model.py}}`, `alembic/versions/{rev}_adrian_embudo_funnel.py`.
Header `# cap: crm.adrian-embudo` líneas 1-3 en cada archivo nuevo.

## 14. Tests (BE — RED first per capa)
`tests/modules/vitalia/crm/`: `test_funnel_machine.py`, `test_lead_score_service.py`, `test_lead_repository_stage.py` (optimistic lock), `test_lead_stage_transition_repository.py`, `test_funnel_service.py` (SC-1/2/5/freeze/reactivate), `test_funnel_api.py` (cross-tenant 404 SC-4, response_model, 422 body), `test_auto_freeze_and_reactivate.py` (SC-freeze), `test_stage_transition_optimistic_lock.py` (SC-5), `test_cross_tenant_lead_block.py` (SC-4). Arch fitness EXTEND (response_model, no-PHI-repo, SA 2.0, no-hard-delete). Schemathesis (opt-in) sobre los 5 endpoints nuevos. Hypothesis (opt-in) sobre score determinista + SLA boundary.
