# vitalia-slice-1-fidelizacion — Backend sub-architecture

> **Consumer:** `builder-backend` (Sonnet build) + `auditor-backend` (Opus audit).
> **Index:** `03-arch.md` § 0-9 (read first).
> **Brand surface:** `vitalia/backend/src/modules/vitalia/fidelizacion/{domain,application,api,infrastructure}/` + `vitalia/backend/src/modules/vitalia/crm/` column extensions + `vitalia/backend/src/modules/vitalia/connections/whatsapp/templates/fidelizacion/`.
> **Engine consultation (READ-ONLY):** `core/luana-core-{platform,campaigns,events,observability,sales-agent,compliance,idempotency}/`.

## 1. Module structure (DDD Inside-Out per `.claude/rules/backend-ddd.md`)

```
vitalia/backend/src/modules/vitalia/fidelizacion/
├── domain/
│   ├── entities/
│   │   ├── treatment_plan.py              ← TreatmentPlan aggregate (tenant+clinic+patient_id+offer_id+sessions)
│   │   ├── re_engagement_event.py         ← ReEngagementEvent (pattern + trigger_source + template + outcome)
│   │   └── nps_response.py                ← NPSResponse (score + comment encrypted + appointment_id)
│   ├── value_objects/
│   │   ├── re_engagement_pattern.py       ← StrEnum: MULTI_SESSION | FOLLOW_UP | MAINTENANCE | ABSENCE | NPS
│   │   ├── re_engagement_outcome.py       ← StrEnum: SENT | RESPONDED | RESCHEDULED | DECLINED | NOT_RESPONSIVE | OPTED_OUT | FAILED_SENDING
│   │   ├── urgency_level.py               ← StrEnum: CRITICAL | ALERT | NEAR | WAITING | UP_TO_DATE
│   │   └── nps_band.py                    ← StrEnum: PROMOTER (9-10) | PASSIVE (7-8) | DETRACTOR (0-6)
│   └── events.py                          ← Domain events: ReEngagementTriggered, NPSScoreCollected, PatientOptedOut, PatientPausedReEngagement
├── infrastructure/
│   ├── models/
│   │   ├── treatment_plan_model.py        ← SQLA 2.0 mapped_column vitalia_treatment_plans
│   │   ├── re_engagement_event_model.py   ← SQLA 2.0 vitalia_re_engagement_events
│   │   └── nps_response_model.py          ← SQLA 2.0 vitalia_nps_responses
│   └── repositories/
│       ├── treatment_plan_repository.py   ← Subclase CompoundScopeRepositoryBase (scope_field='clinic_id')
│       ├── re_engagement_event_repository.py
│       └── nps_response_repository.py
├── application/
│   ├── services/
│   │   ├── re_engagement_service.py       ← Pattern detection + dispatch (multi_session/follow_up/maintenance/absence)
│   │   ├── proactive_outbound_service.py  ← Adrián integration (send template + persist re_engagement_event)
│   │   ├── pause_patient_service.py       ← Pause re-engagement N days
│   │   ├── manual_call_service.py         ← Log manual call + outcome
│   │   ├── opt_out_service.py             ← Patient opt-out marketing
│   │   └── nps_service.py                 ← NPS submission lifecycle
│   ├── dtos/
│   │   ├── re_engagement_dtos.py          ← Pydantic v2: ReEngagementPatternListResponse, SendProactiveRequest/Response, PausePatientRequest/Response, ...
│   │   ├── nps_dtos.py                    ← NpsSummaryResponse, NpsSubmitRequest/Response
│   │   └── fidelizacion_summary_dtos.py   ← FidelizacionSummaryResponse (5 KPIs hero)
│   └── workers/
│       ├── __init__.py                    ← ARQ registration (per cron_envelope engine)
│       ├── multi_session_gap_sweep.py     ← Cron daily 07:00 UTC
│       ├── follow_up_due_sweep.py         ← Cron daily 07:30 UTC
│       ├── maintenance_due_sweep.py       ← Cron daily 08:00 UTC (evaluación)
│       ├── absence_sweep.py               ← Cron weekly Mon 06:00 UTC
│       ├── nps_post_treatment_sweep.py    ← Cron hourly :15
│       └── re_engagement_response_timeout_sweep.py  ← Cron daily 09:00 UTC
└── api/
    ├── router.py                          ← FastAPI router mount /api/v1/vitalia/fidelization
    ├── re_engagement_endpoints.py         ← Pattern listings + actions
    ├── nps_endpoints.py                   ← NPS summary + submit
    └── fidelizacion_summary_endpoints.py  ← KPIs hero summary

vitalia/backend/src/modules/vitalia/crm/
├── infrastructure/models/patient_model.py  ← (existing — add columns marketing_opt_in, opt_out, opt_out_reason, opt_out_at)
├── application/services/patient_consent_service.py  ← (new) opt-in/opt-out lifecycle
└── api/                                    ← PATCH endpoint /api/v1/vitalia/crm/patients/{id}/opt-out (Ola 1)

vitalia/backend/src/modules/vitalia/connections/whatsapp/templates/fidelizacion/
├── recordatorio_proxima_sesion.json       ← Meta-approved template config (variables + UTILITY category)
├── recordatorio_control_doctor.json       ← UTILITY
├── invitacion_mantenimiento.json          ← UTILITY
├── re_engagement_ausencia.json            ← MARKETING (opt-in required)
└── nps_post_tratamiento.json              ← MARKETING (opt-in required)

vitalia/backend/src/modules/vitalia/persistence/migrations/
├── 020_slice1_treatment_plans.py          ← (raw SQL idempotent)
├── 021_slice1_re_engagement_events.py
├── 022_slice1_nps_responses.py
└── 023_slice1_patients_opt_in_columns.py  ← ALTER vitalia_patients ADD COLUMN IF NOT EXISTS marketing_opt_in/opt_out/opt_out_reason/opt_out_at
```

## 2. Tables (3 NEW + 4 column additions)

All `vitalia_` prefix. PHI tables mandatory `tenant_id UUID NOT NULL`, `clinic_id UUID NOT NULL`, `deleted_at TIMESTAMPTZ NULL`, `created_at`, `updated_at`. Indexes composite `(tenant_id, clinic_id, ...)`.

### 2.1 `vitalia_treatment_plans` (NEW — PHI encrypted)

```sql
-- Migration 020_slice1_treatment_plans.py
op.execute("""
CREATE TABLE IF NOT EXISTS vitalia_treatment_plans (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  offer_id UUID NULL,
  doctor_id UUID NULL,
  sessions_total INT NOT NULL,
  sessions_completed INT NOT NULL DEFAULT 0,
  next_session_due_at TIMESTAMPTZ NULL,
  gap_alert_days INT NULL,                      -- inherited from offer.gap_alert_days; null = no alert
  status VARCHAR(16) NOT NULL DEFAULT 'active', -- active | completed | abandoned | paused
  notes BYTEA NULL,                              -- pgcrypto symmetric encrypted (PHI)
  last_session_at TIMESTAMPTZ NULL,
  paused_until TIMESTAMPTZ NULL,
  pause_reason TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
)
""")
op.execute("""
CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_plans_tenant_clinic_status
  ON vitalia_treatment_plans (tenant_id, clinic_id, status)
  WHERE deleted_at IS NULL
""")
op.execute("""
CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_plans_patient
  ON vitalia_treatment_plans (tenant_id, clinic_id, patient_id, status)
  WHERE deleted_at IS NULL
""")
op.execute("""
CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_plans_gap_query
  ON vitalia_treatment_plans (tenant_id, clinic_id, last_session_at, gap_alert_days)
  WHERE status = 'active' AND deleted_at IS NULL
""")
```

### 2.2 `vitalia_re_engagement_events` (NEW — PHI encrypted payload)

```sql
op.execute("""
CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  pattern VARCHAR(32) NOT NULL,                  -- multi_session | follow_up | maintenance | absence | nps
  trigger_source VARCHAR(64) NOT NULL,           -- cron_multi_session_gap_sweep | cron_follow_up_due_sweep | manual | doctor_field
  trigger_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  template_id VARCHAR(64) NULL,                  -- WhatsApp Meta-approved template id
  sent_at TIMESTAMPTZ NULL,
  response_at TIMESTAMPTZ NULL,
  outcome VARCHAR(32) NULL,                      -- sent | responded | rescheduled | declined | not_responsive | opted_out | failed_sending
  converted_to_appointment_id UUID NULL,         -- if patient reagendó
  payload_phi BYTEA NULL,                        -- pgcrypto encrypted (sanitized payload)
  audit_log_id UUID NULL,                        -- FK to vitalia_audit_log
  notes TEXT NULL,                               -- operator notes (DOMPurify-sanitized server-side, no PHI)
  retry_count INT NOT NULL DEFAULT 0,
  last_error TEXT NULL,
  idempotency_key VARCHAR(128) NULL,             -- natural key for cron dedup
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
) PARTITION BY RANGE (trigger_at)
""")
-- Monthly partitions (HIPAA-lite 10y retention)
op.execute("""
CREATE INDEX IF NOT EXISTS ix_vitalia_re_engagement_events_pattern_patient
  ON vitalia_re_engagement_events (tenant_id, clinic_id, patient_id, pattern, trigger_at DESC)
""")
op.execute("""
CREATE INDEX IF NOT EXISTS ix_vitalia_re_engagement_events_throttle
  ON vitalia_re_engagement_events (tenant_id, clinic_id, patient_id, pattern, sent_at DESC)
  WHERE sent_at IS NOT NULL
""")
op.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_re_engagement_events_idempotency
  ON vitalia_re_engagement_events (idempotency_key)
  WHERE idempotency_key IS NOT NULL
""")
op.execute("""
CREATE INDEX IF NOT EXISTS ix_vitalia_re_engagement_events_outcome_status
  ON vitalia_re_engagement_events (tenant_id, clinic_id, outcome, trigger_at DESC)
""")
```

### 2.3 `vitalia_nps_responses` (NEW — PHI encrypted comment)

```sql
op.execute("""
CREATE TABLE IF NOT EXISTS vitalia_nps_responses (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  appointment_id UUID NULL,                       -- nullable: NPS unrelated to specific appt OK Slice 2
  score INT NOT NULL CHECK (score >= 0 AND score <= 10),
  band VARCHAR(16) NOT NULL,                      -- promoter | passive | detractor (derived from score)
  comment BYTEA NULL,                             -- pgcrypto encrypted (PHI — patient text)
  source VARCHAR(32) NOT NULL DEFAULT 'whatsapp_template', -- whatsapp_template | portal_link | sms (Slice 2) | email (Slice 2)
  trigger_re_engagement_event_id UUID NULL,       -- FK to vitalia_re_engagement_events
  responded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  tagged_in_inbox BOOLEAN NOT NULL DEFAULT FALSE, -- set TRUE on first /inbox consumer event
  audit_log_id UUID NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
)
""")
op.execute("""
CREATE INDEX IF NOT EXISTS ix_vitalia_nps_responses_tenant_clinic_band
  ON vitalia_nps_responses (tenant_id, clinic_id, band, responded_at DESC)
  WHERE deleted_at IS NULL
""")
op.execute("""
CREATE INDEX IF NOT EXISTS ix_vitalia_nps_responses_patient
  ON vitalia_nps_responses (tenant_id, clinic_id, patient_id, responded_at DESC)
  WHERE deleted_at IS NULL
""")
```

### 2.4 `vitalia_patients` column additions (existing table Story 11 — extend)

```sql
-- Migration 023_slice1_patients_opt_in_columns.py
op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS marketing_opt_in BOOLEAN NOT NULL DEFAULT FALSE")
op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out BOOLEAN NOT NULL DEFAULT FALSE")
op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out_reason TEXT NULL")
op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out_at TIMESTAMPTZ NULL")
op.execute("""
CREATE INDEX IF NOT EXISTS ix_vitalia_patients_opt_in_status
  ON vitalia_patients (tenant_id, clinic_id, marketing_opt_in, opt_out)
  WHERE deleted_at IS NULL
""")
```

### 2.5 Engine columns CONSUMED (already added Ola 0 / pre-flight)

```sql
-- Engine vitalia_appointments columns (Ola 3 will populate values; Ola 1 reads)
-- Existing per pre-flight gate promotion proposal:
--   follow_up_due_at TIMESTAMPTZ NULL
--   follow_up_reason TEXT NULL
--   completed_at TIMESTAMPTZ NULL
--   balance_status VARCHAR(16) DEFAULT 'pending'
--   origin VARCHAR(32) DEFAULT 'sales_agent'

-- Engine offers columns (already migrated per proposal `2026-05-17-offer-studio-multi-session-maintenance`)
--   requires_multi_session BOOLEAN DEFAULT FALSE
--   sessions_expected INT NULL
--   gap_alert_days INT NULL
--   maintenance_schedule VARCHAR(32) DEFAULT 'none'
--   maintenance_custom_days INT NULL
```

## 3. API endpoints (~9 endpoints)

All routes under `/api/v1/vitalia/fidelization/...`. Bearer + `X-Tenant-ID` + `X-Clinic-ID` headers. `response_model=` mandatory. `FastAPI(redirect_slashes=False)`.

### 3.1 Fidelización core endpoints

| Method | Path | Auth (roles) | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| GET | `/fidelization/summary` | doctor/nurse/admin_clinic/marketing | query: `period` (7d/30d/90d) | `FidelizacionSummaryResponse` | 5 KPIs hero (patients_in_followup, near_abandonment, return_rate, re_engaged_count_period, nps_average) |
| GET | `/fidelization/re-engagement/patterns` | doctor/nurse/admin_clinic | query: `pattern` (multi_session/follow_up/maintenance/absence), `vertical`, `doctor`, `urgency`, `period` | `ReEngagementPatternListResponse` | Pattern listing per tab (rows = patient + urgency + acciones contextuales) |
| POST | `/fidelization/patients/{patient_id}/send-proactive` | marketing/admin_clinic | `SendProactiveRequest` (template_id, pattern, slot_values, idempotency_key) | `SendProactiveResponse` (re_engagement_event_id, status) | Adrián abre conv solicitado · header `Idempotency-Key` required |
| POST | `/fidelization/patients/{patient_id}/pause` | doctor/nurse/admin_clinic | `PausePatientRequest` (duration_days, reason) | `PausePatientResponse` (resume_at) | Pause re-engagement |
| POST | `/fidelization/patients/{patient_id}/mark-external` | doctor/nurse/admin_clinic | `MarkExternalRequest` (pattern, note) | `MarkExternalResponse` | Silence pattern (paciente scheduled externamente) |
| POST | `/fidelization/patients/{patient_id}/mark-no-continue` | doctor/nurse/admin_clinic | `MarkNoContinueRequest` (reason, audit_responsible_user_id) | `MarkNoContinueResponse` | Marcar paciente decidió no continuar |
| POST | `/fidelization/patients/{patient_id}/manual-call` | doctor/nurse/admin_clinic | `ManualCallRequest` (notes, outcome) | `ManualCallResponse` (audit_log_id) | Registrar llamada manual operadora |
| GET | `/fidelization/activity-stream` | doctor/nurse/admin_clinic | query: `limit` (default 20), `since` (ISO datetime) | `ActivityStreamResponse` | Activity footer events (sent reminders, responses, cron runs) |

### 3.2 NPS endpoints

| Method | Path | Auth (roles) | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| GET | `/fidelization/nps/summary` | doctor/nurse/admin_clinic/marketing | query: `period` | `NpsSummaryResponse` (average_score, total_responses, table_rows[]) | NPS lista reducida Slice 1 + average (NO chart distribution Slice 1) |
| POST | `/fidelization/nps/submit` | patient (paciente token specific) | `NpsSubmitRequest` (score, comment, source, trigger_re_engagement_event_id) + `Idempotency-Key` header | `NpsSubmitResponse` (id, band) | Webhook desde Adrián WhatsApp response · patient role specific token (NPS short-link tokenized) |

### 3.3 CRM consent endpoint (extension)

| Method | Path | Auth (roles) | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| POST | `/crm/patients/{patient_id}/opt-out` | doctor/nurse/admin_clinic | `OptOutRequest` (reason) | `OptOutResponse` | Mark opt_out=true + cascade re_engagement cancel pending events |
| PATCH | `/crm/patients/{patient_id}/marketing-opt-in` | doctor/nurse/admin_clinic | `MarketingOptInRequest` (consent_at, consent_source) | `PatientResponse` | Update opt_in (during clinic visit consentimiento firma) |

## 4. Cron jobs (6 ARQ workers)

All cron wrap `@cron_envelope` engine (idempotency + OTel + audit + sentry). Best-effort writes. Soft-fail. Idempotency natural key `(tenant_id, clinic_id, patient_id, pattern, sweep_date)`.

| Cron name | Frequency | Owner | Purpose |
|---|---|---|---|
| `multi_session_gap_sweep` | daily 07:00 UTC | fidelizacion.workers | Detect treatment_plans active + gap > gap_alert_days → insert re_engagement_event pattern=multi_session |
| `follow_up_due_sweep` | daily 07:30 UTC | fidelizacion.workers | Detect appointments.follow_up_due_at within 7d AND no new appt → insert re_engagement_event pattern=follow_up |
| `maintenance_due_sweep` | daily 08:00 UTC | fidelizacion.workers | Detect offers.maintenance_schedule!=none + last_appt_completed_at + cadencia next vencida → insert re_engagement_event pattern=maintenance |
| `absence_sweep` | weekly Mon 06:00 UTC | fidelizacion.workers | Detect patients last_appt < now()-6m AND lifetime_appointments >= 1 AND NOT opt_out → insert pattern=absence |
| `nps_post_treatment_sweep` | hourly :15 | fidelizacion.workers | Detect appointments.balance_status=full_paid + 24h elapsed + no NPS sent → trigger nps_post_tratamiento template |
| `re_engagement_response_timeout_sweep` | daily 09:00 UTC | fidelizacion.workers | Mark re_engagement_events outcome=not_responsive after 7d sin response_at |

### 4.1 Cron implementation pattern

```python
# vitalia/backend/src/modules/vitalia/fidelizacion/application/workers/multi_session_gap_sweep.py
from luana_core_platform.workers.cron_envelope import cron_envelope
from luana_core_idempotency.application.decorator import idempotent
from src.modules.vitalia.fidelizacion.application.services.re_engagement_service import ReEngagementService

@cron_envelope(
    cron_name="multi_session_gap_sweep",
    schedule="0 7 * * *",  # daily 07:00 UTC
    timeout_sec=300,       # 5min
    max_retries=3,
    audit=True,            # writes audit_log row on success/failure
    sentry=True,
)
async def multi_session_gap_sweep_task(ctx: dict) -> dict:
    """Detect treatment_plans with gap > gap_alert_days for each tenant+clinic.
    
    Idempotency key: f"multi_session_gap_sweep::{tenant_id}::{clinic_id}::{sweep_date}"
    """
    settings = ctx["settings"]
    db_session = ctx["db_session"]
    
    service = ReEngagementService(db_session)
    
    results = []
    async for tenant_id, clinic_id in service.iter_active_tenants_clinics():
        sweep_date = utc_now().date().isoformat()
        idem_key = f"multi_session_gap_sweep::{tenant_id}::{clinic_id}::{sweep_date}"
        
        detected = await service.detect_multi_session_gaps(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            idempotency_key=idem_key,
        )
        results.append({"tenant_id": tenant_id, "clinic_id": clinic_id, "detected_count": len(detected)})
    
    return {"sweeps": results, "total_events_inserted": sum(r["detected_count"] for r in results)}
```

Similar pattern for the 5 remaining crons. Each calls a `ReEngagementService.detect_{pattern}()` method that queries the appropriate base data, computes urgency, and inserts `vitalia_re_engagement_events` rows with idempotency dedup.

### 4.2 Service `ReEngagementService` core methods

```python
class ReEngagementService:
    async def detect_multi_session_gaps(self, *, tenant_id, clinic_id, idempotency_key) -> list[ReEngagementEvent]: ...
    async def detect_follow_up_due(self, *, tenant_id, clinic_id, idempotency_key) -> list[ReEngagementEvent]: ...
    async def detect_maintenance_due(self, *, tenant_id, clinic_id, idempotency_key) -> list[ReEngagementEvent]: ...
    async def detect_absence(self, *, tenant_id, clinic_id, idempotency_key) -> list[ReEngagementEvent]: ...
    async def trigger_nps_post_treatment(self, *, tenant_id, clinic_id, appointment_id) -> ReEngagementEvent: ...
    async def mark_response_timeout(self, *, tenant_id, clinic_id, max_age_days=7) -> int: ...

    async def list_patterns(self, *, tenant_id, clinic_id, pattern, filters) -> list[PatternRowDTO]: ...
    async def send_proactive_reminder(self, *, tenant_id, clinic_id, patient_id, re_engagement_event_id, template_id, slot_values, idempotency_key) -> SendProactiveResponse: ...
    async def pause_patient(self, *, tenant_id, clinic_id, patient_id, duration_days, reason, user_id) -> PausePatientResponse: ...
```

`send_proactive_reminder` flow:
1. Idempotency check
2. Compliance gate: `ComplianceService.validate_outbound_message(template, channel="whatsapp_business")`
3. Audit log sync write
4. Inject Adrián service: `adrian_service.send_proactive_outbound(template_id, slot_values, conv_origin="proactive_outbound", sub_attribution=f"sistema (cron {trigger_source}) confirmado operador {user_id}")`
5. Persist `re_engagement_events.outcome=sent + sent_at=now`
6. Emit `ReEngagementTriggered` domain event via `luana_core_events.outbox.adapter_bus.publish(...)`

## 5. Repository interfaces (post lift core)

All repositories async, subclase `CompoundScopeRepositoryBase` (engine post lift) con `scope_field="clinic_id"`. Every method receives `tenant_id` + `clinic_id`.

```python
# vitalia/backend/src/modules/vitalia/fidelizacion/infrastructure/repositories/re_engagement_event_repository.py
from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase
from src.modules.vitalia.fidelizacion.domain.entities.re_engagement_event import ReEngagementEvent
from src.modules.vitalia.fidelizacion.infrastructure.models.re_engagement_event_model import ReEngagementEventModel
from sqlalchemy import select
from uuid import UUID

class ReEngagementEventRepository(CompoundScopeRepositoryBase[ReEngagementEvent, ReEngagementEventModel]):
    """PHI dual-filter repository per hipaa-lite.md + post lift core 2026-05-20."""
    
    scope_field = "clinic_id"  # engine base enforces tenant_id + scope_field dual filter
    
    async def get_by_id(self, event_id: UUID, *, tenant_id: UUID, clinic_id: UUID) -> ReEngagementEvent | None:
        stmt = select(ReEngagementEventModel).where(
            ReEngagementEventModel.id == event_id,
            ReEngagementEventModel.tenant_id == tenant_id,
            ReEngagementEventModel.clinic_id == clinic_id,   # dual filter — CARDINAL
            ReEngagementEventModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return ReEngagementEvent.model_validate(row) if row else None
    
    async def list_by_pattern(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        pattern: str,
        urgency: list[str] | None = None,
        vertical: str | None = None,
        doctor_id: UUID | None = None,
        limit: int = 100,
    ) -> list[ReEngagementEvent]:
        stmt = select(ReEngagementEventModel).where(
            ReEngagementEventModel.tenant_id == tenant_id,
            ReEngagementEventModel.clinic_id == clinic_id,
            ReEngagementEventModel.pattern == pattern,
            ReEngagementEventModel.deleted_at.is_(None),
        )
        # apply filters
        if urgency:
            stmt = stmt.where(...)  # urgency derived field — may need join or computed at app layer
        stmt = stmt.order_by(ReEngagementEventModel.trigger_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return [ReEngagementEvent.model_validate(r) for r in result.scalars().all()]
    
    async def check_throttle(
        self, *, tenant_id: UUID, clinic_id: UUID, patient_id: UUID, pattern: str, throttle_days: int = 7
    ) -> bool:
        """Return True if patient can receive new reminder (no recent sent within throttle window)."""
        cutoff = utc_now() - timedelta(days=throttle_days)
        stmt = select(ReEngagementEventModel.id).where(
            ReEngagementEventModel.tenant_id == tenant_id,
            ReEngagementEventModel.clinic_id == clinic_id,
            ReEngagementEventModel.patient_id == patient_id,
            ReEngagementEventModel.pattern == pattern,
            ReEngagementEventModel.sent_at > cutoff,
        ).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is None
```

Similar repos `TreatmentPlanRepository`, `NPSResponseRepository`.

## 6. Domain entities (key shapes)

### 6.1 `ReEngagementEvent`

```python
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from enum import StrEnum

class ReEngagementPattern(StrEnum):
    MULTI_SESSION = "multi_session"
    FOLLOW_UP = "follow_up"
    MAINTENANCE = "maintenance"
    ABSENCE = "absence"
    NPS = "nps"

class ReEngagementOutcome(StrEnum):
    SENT = "sent"
    RESPONDED = "responded"
    RESCHEDULED = "rescheduled"
    DECLINED = "declined"
    NOT_RESPONSIVE = "not_responsive"
    OPTED_OUT = "opted_out"
    FAILED_SENDING = "failed_sending"

class ReEngagementEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID
    pattern: ReEngagementPattern
    trigger_source: str  # cron_X | manual | doctor_field
    trigger_at: datetime
    template_id: str | None
    sent_at: datetime | None
    response_at: datetime | None
    outcome: ReEngagementOutcome | None
    converted_to_appointment_id: UUID | None
    audit_log_id: UUID | None
    notes: str | None
    retry_count: int
    last_error: str | None
    idempotency_key: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 6.2 `TreatmentPlan`

```python
class TreatmentPlanStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    PAUSED = "paused"

class TreatmentPlan(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID
    offer_id: UUID | None
    doctor_id: UUID | None
    sessions_total: int
    sessions_completed: int
    next_session_due_at: datetime | None
    gap_alert_days: int | None
    status: TreatmentPlanStatus
    notes_encrypted: bytes | None  # pgcrypto
    last_session_at: datetime | None
    paused_until: datetime | None
    pause_reason: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 6.3 `NPSResponse`

```python
class NPSBand(StrEnum):
    PROMOTER = "promoter"    # 9-10
    PASSIVE = "passive"      # 7-8
    DETRACTOR = "detractor"  # 0-6

class NPSResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID
    appointment_id: UUID | None
    score: int  # 0-10
    band: NPSBand
    comment_encrypted: bytes | None  # pgcrypto
    source: str  # whatsapp_template | portal_link
    trigger_re_engagement_event_id: UUID | None
    responded_at: datetime
    tagged_in_inbox: bool
    audit_log_id: UUID | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 6.4 Domain events

```python
# vitalia/backend/src/modules/vitalia/fidelizacion/domain/events.py
from luana_core_events.domain.event import DomainEvent

class ReEngagementTriggered(DomainEvent):
    event_type = "vitalia.fidelizacion.re_engagement_triggered"
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID
    pattern: str
    re_engagement_event_id: UUID
    template_id: str
    triggered_by_user_id: UUID

class NPSScoreCollected(DomainEvent):
    event_type = "vitalia.fidelizacion.nps_score_collected"
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID
    nps_response_id: UUID
    score: int
    band: str
    appointment_id: UUID | None

class PatientOptedOut(DomainEvent):
    event_type = "vitalia.fidelizacion.patient_opted_out"
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID
    reason: str | None
    triggered_by_user_id: UUID

class PatientPausedReEngagement(DomainEvent):
    event_type = "vitalia.fidelizacion.patient_paused_re_engagement"
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID
    duration_days: int
    reason: str | None
    resume_at: datetime
    triggered_by_user_id: UUID
```

Emitted via `luana_core_events.outbox.adapter_bus.publish(event, session=self.session)` con `USE_OUTBOX_PATTERN_*=True` (default post 2026-04-30 — anti-default-flip cementado).

## 7. Application services flow (sample)

```python
# vitalia/backend/src/modules/vitalia/fidelizacion/application/services/proactive_outbound_service.py
class ProactiveOutboundService:
    def __init__(
        self,
        uow,
        re_engagement_repo: ReEngagementEventRepository,
        audit_log_repo,                                         # luana_core_platform.audit_log
        compliance_service,                                     # luana_core_compliance.ComplianceService
        adrian_service,                                         # luana_core_sales_agent.SalesAgentRuntime
        event_bus,                                              # luana_core_events.outbox.adapter_bus
        idempotency_repo,                                       # luana_core_idempotency
    ): ...

    async def send_proactive_reminder(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        user_id: UUID,
        request: SendProactiveRequest,
        idempotency_key: str,
    ) -> SendProactiveResponse:
        # 1. Idempotency check
        existing = await self.idempotency_repo.check(idempotency_key)
        if existing:
            return existing

        async with self.uow.begin():
            # 2. Check throttle 7d
            allowed = await self.re_engagement_repo.check_throttle(
                tenant_id=tenant_id, clinic_id=clinic_id,
                patient_id=patient_id, pattern=request.pattern, throttle_days=7,
            )
            if not allowed:
                raise HTTPException(429, detail="Throttle 7d not elapsed")

            # 3. Check opt_out + marketing_opt_in (si MARKETING template)
            patient = await self.patient_repo.get_by_id(patient_id, tenant_id=tenant_id, clinic_id=clinic_id)
            if patient.opt_out:
                raise HTTPException(403, detail="Patient opted out")
            template = await self.template_registry.get(request.template_id)
            if template.category == "MARKETING" and not patient.marketing_opt_in:
                raise HTTPException(403, detail="Patient has no MARKETING opt-in")

            # 4. Compliance channel guard
            await self.compliance_service.validate_outbound_message(
                template_id=request.template_id, channel="whatsapp_business", tenant_id=tenant_id
            )

            # 5. Audit log sync write FIRST
            audit_id = await self.audit_log_repo.record(
                tenant_id=tenant_id, clinic_id=clinic_id, user_id=user_id,
                action="send_proactive_reengagement_template",
                resource_type="patient", resource_id=patient_id,
                payload_redacted=sanitize_payload(
                    request.model_dump(), compliance_level="hipaa_lite"
                ),
            )

            # 6. Dispatch Adrián
            try:
                conv_id = await self.adrian_service.send_proactive_outbound(
                    tenant_id=tenant_id, clinic_id=clinic_id,
                    patient_id=patient_id,
                    template_id=request.template_id,
                    slot_values=request.slot_values,
                    conv_origin="proactive_outbound",
                    sub_attribution=f"sistema (cron {request.trigger_source}) confirmado operador {user_id}",
                )
                outcome = ReEngagementOutcome.SENT
                last_error = None
            except Exception as e:
                outcome = ReEngagementOutcome.FAILED_SENDING
                last_error = str(e)[:500]
                conv_id = None

            # 7. Persist re_engagement_event
            event = ReEngagementEvent(
                id=uuid4(), tenant_id=tenant_id, clinic_id=clinic_id,
                patient_id=patient_id, pattern=request.pattern,
                trigger_source=request.trigger_source,
                trigger_at=utc_now(),
                template_id=request.template_id,
                sent_at=utc_now() if outcome == ReEngagementOutcome.SENT else None,
                outcome=outcome, last_error=last_error,
                audit_log_id=audit_id, idempotency_key=idempotency_key,
            )
            await self.re_engagement_repo.create(event)

            # 8. Idempotency cache
            response = SendProactiveResponse(
                re_engagement_event_id=event.id, status=outcome.value, conv_id=conv_id
            )
            await self.idempotency_repo.set(idempotency_key, response)

            # 9. Emit DomainEvent
            await self.event_bus.publish(
                ReEngagementTriggered(
                    tenant_id=tenant_id, clinic_id=clinic_id,
                    patient_id=patient_id, pattern=request.pattern,
                    re_engagement_event_id=event.id,
                    template_id=request.template_id,
                    triggered_by_user_id=user_id,
                ),
                session=self.session,
            )

        return response
```

## 8. Cross-cutting concerns (BE-specific)

- **`structlog`** mandatory. `logger.bind(tenant_id=..., clinic_id=..., pattern=..., trace_id=...)`.
- **Async-first.** All repos, services, route handlers `async def`. AsyncSession.
- **SQLAlchemy 2.0** only. `mapped_column()`, `select(...)`. NEVER `Column()` o `session.query()`.
- **Pydantic v2** ConfigDict. No inner `class Config`.
- **`response_model=`** mandatory every route.
- **`X-Tenant-ID + X-Clinic-ID`** middleware-injected from Clerk JWT claims.
- **`FastAPI(redirect_slashes=False)`** en `main.py`.
- **TenantLocale VO** from `core/luana-core-platform/` for timezone display. NEVER `datetime.utcnow()` — use `utc_now()` helper.
- **Migrations idempotent** raw SQL `IF NOT EXISTS`. Test pre-prod clone DB.
- **Anti-default-flip-audit:** Slice 1 NO flag flips esta story.
- **Per `.claude/rules/anti-duplication.md`:** NO mirror engine patterns (observability/cost/pricing/etc.) — consume direct/EXTEND.

## 9. Test surfaces (TDD-mandatory per layer)

Per `.claude/rules/tdd-mandatory.md`:

| Layer | Test file pattern | RED first |
|---|---|---|
| Domain | `vitalia/backend/tests/modules/vitalia/fidelizacion/domain/test_*.py` | YES |
| Infrastructure (models, repos) | `vitalia/backend/tests/modules/vitalia/fidelizacion/infrastructure/test_*_repository.py` | YES |
| Application (services) | `vitalia/backend/tests/modules/vitalia/fidelizacion/application/test_*_service.py` | YES |
| API/E2E (routes) | `vitalia/backend/tests/modules/vitalia/fidelizacion/api/test_*_router.py` | YES |
| Workers (cron jobs smoke + integration) | `vitalia/backend/tests/modules/vitalia/fidelizacion/workers/test_*_sweep.py` | YES (smoke + integration with real sched + Sanaré fixture data) |
| Migrations (smoke) | `vitalia/backend/tests/migrations/test_slice1_fidelizacion_migrations.py` | NO (smoke only) |
| Architecture fitness | `vitalia/backend/tests/architecture/test_*.py` | YES (allowlist shrinkage) |
| PHI compliance | `vitalia/backend/tests/architecture/test_phi_dual_filter.py`, `test_audit_log_sync_write.py`, `test_pgcrypto_phi_columns.py`, `test_cron_envelope_used.py`, `test_compound_scope_repository_used.py` | YES |
| Cross-story contracts | `vitalia/backend/tests/integration/test_cross_story_contracts.py` (verify NPSScoreCollected emit + ReEngagementTriggered emit consumed shape) | YES |

Coverage threshold: 43% BE baseline. Slice 1 fidelización target ≥ 50% per módulo.

## 10. Architectural fitness impact

Allowlists shrinkage planned:
- `test_no_cross_brand_imports.py` — zero growth
- `test_response_model_required.py` — zero new exceptions (all 11 fidelización routes declare)
- `test_phi_dual_filter.py` — fidelización repos enforced
- `test_audit_log_sync_write.py` — fidelización mutations enforced
- `test_pgcrypto_phi_columns.py` — new PHI columns (re_engagement_events.payload_phi, treatment_plans.notes, nps_responses.comment) enforced
- `test_extension_sdk_registration.py` — vitalia extensions.py mounts fidelización templates via EP-8 (whatsapp templates) — pre-existing pattern
- `test_no_legacy_paths.py` — zero `backend/src/shared/` imports
- `test_cron_envelope_used.py` (NEW) — fidelización workers MUST import `luana_core_platform.workers.cron_envelope`
- `test_compound_scope_repository_used.py` (NEW) — fidelización PHI repos MUST subclase `CompoundScopeRepositoryBase` (scope_field='clinic_id')

## 11. Capability YAML + modules MD updates required

Post-merge:
- NEW `vitalia/docs/product/capabilities/fidelizacion/4patterns-reengagement.yaml`
- NEW `vitalia/docs/product/capabilities/fidelizacion/nps-resumido-slice1.yaml`
- NEW `vitalia/docs/product/capabilities/fidelizacion/templates-meta-approved-5.yaml`
- NEW `vitalia/docs/product/capabilities/fidelizacion/crons-reengagement-6.yaml`
- NEW `vitalia/docs/product/modules/fidelizacion.md` (SSoT funcional viva)
