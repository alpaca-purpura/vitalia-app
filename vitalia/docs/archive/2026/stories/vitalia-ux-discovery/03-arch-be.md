# vitalia-ux-discovery — Backend sub-architecture

> **Consumer:** `builder-backend` (Sonnet build) + `auditor-backend` (Opus audit).
> **Index:** `03-arch.md` § 0-10 (read first for cross-cutting principles).
> **Brand surface:** `vitalia/backend/src/modules/vitalia/{inbox,pipeline,agenda,fidelizacion,marketing,onboarding,connections,iam,crm,compliance}/{domain,application,api,infrastructure}/` + `vitalia/backend/src/modules/vitalia/extensions.py`.
> **Engine consultation:** READ-ONLY `core/luana-core-*/` — modifications require `/pm-luana` promotion proposal (see `delta-arch-notes.md` for Slice 2 lift candidates).

## 1. Module structure (DDD Inside-Out per `.claude/rules/backend-ddd.md`)

```
vitalia/backend/src/modules/vitalia/
├── _shared/                                ← brand-internal shared (NOT cross-brand)
│   ├── repositories/
│   │   ├── phi_repository.py               ← PhiRepositoryBase (tenant+clinic dual filter)
│   │   └── audit_log_repository.py         ← AuditLogRepository sync write
│   ├── encryption/
│   │   └── kek_client.py                   ← Vault/KMS client for pgcrypto KEK
│   └── auth/
│       └── rbac.py                         ← @require_phi_access decorator
├── compliance/                             ← PHI compliance brand-specific
│   ├── domain/
│   │   └── phi_fields.py                   ← SSoT PHI field list (canonical Vitalia)
│   └── application/
│       └── compliance_service_adapter.py   ← extends core/luana-core-compliance
├── inbox/                                  ← /inbox route backend
│   ├── domain/
│   │   ├── entities/conversation.py        ← Conversation (tenant_id+clinic_id+patient_id)
│   │   ├── entities/message.py             ← Message + retraction support
│   │   ├── entities/activity_event.py      ← ActivityEvent (agent attribution)
│   │   ├── entities/action_receipt.py      ← ActionReceipt (5min undo window)
│   │   ├── entities/proposal_card.py       ← ProposalCard "Adrián propone"
│   │   └── events.py                       ← ConversationStarted, MessageRetracted, etc.
│   ├── infrastructure/
│   │   ├── models/                         ← SQLAlchemy 2.0 mapped_column
│   │   └── repositories/
│   ├── application/
│   │   ├── services/inbox_service.py
│   │   ├── services/proactive_outbound_service.py
│   │   ├── services/whisper_transcribe_service.py  ← Audio IN STT
│   │   └── dtos/
│   └── api/
│       └── router.py
├── pipeline/                               ← /pipeline route backend
│   ├── domain/entities/{lead.py, screening_outcome.py}
│   ├── infrastructure/{models/, repositories/}
│   ├── application/
│   │   ├── services/pipeline_service.py
│   │   └── services/screening_service.py   ← screening clínico Lucas
│   └── api/router.py
├── agenda/                                 ← /agenda route backend
│   ├── domain/
│   │   ├── entities/appointment.py         ← columns: origin, balance_status, follow_up_due_at, completed_at, utm_source, utm_campaign
│   │   ├── entities/payment_event.py
│   │   ├── entities/fiscal_receipt.py
│   │   └── events.py
│   ├── infrastructure/{models/, repositories/, providers/}
│   ├── application/
│   │   ├── services/agenda_service.py
│   │   ├── services/payment_service.py     ← 3 capas cobranza
│   │   ├── services/fiscal_service.py      ← Nubefact PE adapter
│   │   └── services/refund_service.py
│   └── api/router.py
├── fidelizacion/                           ← /fidelización route backend
│   ├── domain/
│   │   ├── entities/treatment_plan.py
│   │   ├── entities/re_engagement_event.py
│   │   ├── entities/nps_response.py
│   │   └── events.py
│   ├── infrastructure/{models/, repositories/}
│   ├── application/
│   │   ├── services/treatment_followup_service.py
│   │   ├── services/re_engagement_service.py
│   │   ├── services/nps_service.py
│   │   └── workers/                        ← ARQ cron jobs (6)
│   └── api/router.py
├── marketing/                              ← /marketing route backend
│   ├── domain/
│   │   ├── entities/lucas_recommendation.py
│   │   ├── entities/referral.py
│   │   ├── entities/channel_sync_state.py
│   │   ├── entities/channel_metric.py
│   │   └── events.py
│   ├── infrastructure/
│   │   ├── models/
│   │   ├── repositories/
│   │   └── providers/{meta_ads.py, google_ads.py}
│   ├── application/
│   │   ├── services/marketing_service.py
│   │   ├── services/lucas_recommendations_service.py
│   │   ├── services/attribution_service.py
│   │   ├── services/referrals_service.py
│   │   └── workers/                        ← ARQ cron jobs (4)
│   └── api/router.py
├── onboarding/                             ← Wizard agentic backend
│   ├── domain/
│   │   ├── entities/onboarding_progress.py
│   │   ├── entities/brand_studio_draft.py
│   │   └── slot_taxonomy.py                ← 3 req + 2 opt + bonus NLU slots
│   ├── infrastructure/
│   │   ├── models/
│   │   ├── repositories/
│   │   └── providers/
│   │       ├── website_scraper.py
│   │       ├── document_extractor.py
│   │       └── audio_transcriber.py        ← Whisper STT wizard variant
│   ├── application/
│   │   ├── services/onboarding_service.py
│   │   ├── services/slot_extraction_service.py
│   │   └── services/live_preview_service.py
│   └── api/router.py
├── connections/                            ← External integrations
│   ├── fiscal/nubefact_pe/                 ← side story dependency
│   │   ├── adapter.py
│   │   ├── retry_queue.py
│   │   └── cdr_archive.py
│   ├── payment/mercadopago/                ← side story dependency
│   │   ├── adapter.py
│   │   └── refund_handler.py
│   ├── whatsapp/
│   │   ├── adapter.py
│   │   └── templates/                      ← 5 fidelización + 1 marketing + 1 onboarding
│   ├── meta_ads/adapter.py
│   ├── google_ads/adapter.py
│   └── whisper/adapter.py
├── iam/                                    ← RBAC + Clerk integration
│   ├── domain/role.py                      ← doctor/nurse/admin_clinic/patient/marketing/sales
│   ├── application/clinic_resolver.py      ← resolve X-Clinic-ID from JWT
│   └── api/router.py
├── crm/                                    ← Patient + lead management
│   ├── domain/
│   │   ├── entities/patient.py             ← columns: marketing_opt_in, opt_out
│   │   ├── entities/lead.py
│   │   └── events.py
│   ├── infrastructure/
│   ├── application/
│   └── api/router.py
├── copilot/                                ← Valeria brand extension (agentic — see 03-arch-agentic.md)
│   └── (extractors, tools, workflows, kb — managed by builder-agentic)
├── sales_agent/                            ← Adrián brand extension (agentic — see 03-arch-agentic.md)
│   └── (tools, personas, goldens — managed by builder-agentic)
├── extensions.py                           ← MOUNTS EVERYTHING via Extension SDK (single entry)
├── persistence/migrations/                 ← Alembic idempotent raw SQL
│   ├── 001_initial_vitalia_tables.py       ← (Story 11 cement)
│   ├── 002_slice1_appointments_extensions.py     (NEW Slice 1)
│   ├── 003_slice1_payment_events.py
│   ├── 004_slice1_fiscal_receipts.py
│   ├── 005_slice1_treatment_plans.py
│   ├── 006_slice1_re_engagement_events.py
│   ├── 007_slice1_channel_sync_state.py
│   ├── 008_slice1_channel_metrics.py
│   ├── 009_slice1_lucas_recommendations.py
│   ├── 010_slice1_referrals.py
│   ├── 011_slice1_onboarding_progress.py
│   ├── 012_slice1_brand_studio_drafts.py
│   ├── 013_slice1_audit_log_vitalia.py
│   ├── 014_slice1_tenants_columns.py             (is_onboarded, location_country, location_city, timezone)
│   ├── 015_slice1_offers_columns.py              (requires_multi_session, sessions_expected, gap_alert_days, maintenance_schedule, maintenance_custom_days)
│   └── 016_slice1_patients_columns.py            (marketing_opt_in, opt_out)
└── main.py                                 ← FastAPI(redirect_slashes=False) mounts routers
```

## 2. Tables (11 NEW + 8 column additions)

All tables prefix `vitalia_` (per `infra.dev.database_name=vitalia_dev` per `brand.yaml`). Mandatory columns on every PHI table: `tenant_id UUID NOT NULL`, `clinic_id UUID NOT NULL`, `deleted_at TIMESTAMPTZ NULL`, `created_at TIMESTAMPTZ NOT NULL`, `updated_at TIMESTAMPTZ NOT NULL`. Indexes: `(tenant_id, clinic_id, ...)` composite.

### 2.1 `vitalia_appointments` (8 column additions, table already exists Story 11)

```sql
ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS origin VARCHAR(32) NOT NULL DEFAULT 'sales_agent';
-- enum: sales_agent | walk_in | phone_manual | proactive_outbound
ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS balance_status VARCHAR(16) NOT NULL DEFAULT 'pending';
-- enum: pending | deposit_paid | full_paid | refunded
ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS follow_up_due_at TIMESTAMPTZ NULL;
ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS follow_up_reason TEXT NULL;
ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ NULL;
ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS utm_source VARCHAR(64) NULL;
ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS utm_campaign VARCHAR(128) NULL;
CREATE INDEX IF NOT EXISTS ix_vitalia_appointments_tenant_clinic_origin
  ON vitalia_appointments (tenant_id, clinic_id, origin);
CREATE INDEX IF NOT EXISTS ix_vitalia_appointments_follow_up_due
  ON vitalia_appointments (tenant_id, clinic_id, follow_up_due_at)
  WHERE follow_up_due_at IS NOT NULL AND deleted_at IS NULL;
```

### 2.2 `vitalia_payment_events` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_payment_events (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  appointment_id UUID NOT NULL REFERENCES vitalia_appointments(id),
  provider VARCHAR(32) NOT NULL, -- mercadopago | stripe | manual_cash | manual_card | manual_transfer | other
  provider_payment_id VARCHAR(128) NULL,
  amount_cents BIGINT NOT NULL,
  currency CHAR(3) NOT NULL,
  status VARCHAR(16) NOT NULL, -- pending | approved | rejected | refunded
  is_deposit BOOLEAN NOT NULL DEFAULT FALSE,
  deposit_percent INT NULL, -- 30 default
  receipt_number VARCHAR(64) NULL, -- internal VLT-{year}-{seq}
  audit_log_id UUID NULL REFERENCES vitalia_audit_log(id),
  payload JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS ix_vitalia_payment_events_tenant_clinic_appt
  ON vitalia_payment_events (tenant_id, clinic_id, appointment_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_payment_events_provider
  ON vitalia_payment_events (provider, provider_payment_id)
  WHERE provider_payment_id IS NOT NULL;
```

### 2.3 `vitalia_fiscal_receipts` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_fiscal_receipts (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  payment_event_id UUID NOT NULL REFERENCES vitalia_payment_events(id),
  provider VARCHAR(32) NOT NULL, -- nubefact_pe (Slice 1) | future MX/CO/AR/CL Slice 2/3
  fiscal_doc_type VARCHAR(16) NOT NULL, -- boleta | factura | nota_credito
  fiscal_serial VARCHAR(16) NOT NULL,
  fiscal_number VARCHAR(32) NOT NULL,
  fiscal_url TEXT NULL,
  cdr_xml_archived_at TIMESTAMPTZ NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'pending', -- pending | submitted | accepted | rejected | retrying
  retry_count INT NOT NULL DEFAULT 0,
  last_error TEXT NULL,
  submitted_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_fiscal_receipts_serial_number
  ON vitalia_fiscal_receipts (tenant_id, clinic_id, fiscal_serial, fiscal_number);
CREATE INDEX IF NOT EXISTS ix_vitalia_fiscal_receipts_status
  ON vitalia_fiscal_receipts (status, retry_count)
  WHERE status IN ('pending', 'retrying');
```

### 2.4 `vitalia_treatment_plans` (NEW — PHI encrypted)

```sql
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
  gap_alert_days INT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'active', -- active | completed | abandoned | paused
  notes BYTEA NULL, -- pgcrypto symmetric encrypted (PHI)
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_plans_tenant_clinic_status
  ON vitalia_treatment_plans (tenant_id, clinic_id, status)
  WHERE deleted_at IS NULL;
```

### 2.5 `vitalia_re_engagement_events` (NEW — PHI encrypted)

```sql
CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  patient_id UUID NOT NULL,
  pattern VARCHAR(32) NOT NULL, -- multi_session | follow_up | maintenance | absence | nps
  trigger_source VARCHAR(32) NOT NULL, -- cron_X | manual | doctor_field
  template_id VARCHAR(64) NULL, -- WhatsApp Meta-approved template
  sent_at TIMESTAMPTZ NULL,
  response_at TIMESTAMPTZ NULL,
  outcome VARCHAR(32) NULL, -- rescheduled | declined | not_responsive | opted_out
  payload_phi BYTEA NULL, -- pgcrypto encrypted
  audit_log_id UUID NULL REFERENCES vitalia_audit_log(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS ix_vitalia_re_engagement_events_pattern_patient
  ON vitalia_re_engagement_events (tenant_id, clinic_id, patient_id, pattern);
CREATE INDEX IF NOT EXISTS ix_vitalia_re_engagement_events_throttle
  ON vitalia_re_engagement_events (tenant_id, clinic_id, patient_id, pattern, sent_at);
```

### 2.6 `vitalia_channel_sync_state` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_channel_sync_state (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  provider VARCHAR(32) NOT NULL, -- meta_ads | google_ads
  last_sync_at TIMESTAMPTZ NULL,
  last_success_at TIMESTAMPTZ NULL,
  last_error TEXT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'idle', -- idle | running | error | disconnected
  oauth_token_encrypted BYTEA NULL,
  account_id VARCHAR(128) NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_channel_sync_state_tenant_provider
  ON vitalia_channel_sync_state (tenant_id, clinic_id, provider);
```

### 2.7 `vitalia_channel_metrics` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_channel_metrics (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  provider VARCHAR(32) NOT NULL,
  channel_slug VARCHAR(64) NOT NULL,
  metric_date DATE NOT NULL,
  impressions BIGINT NULL,
  clicks BIGINT NULL,
  conversions BIGINT NULL,
  spend_cents BIGINT NULL,
  currency CHAR(3) NULL,
  raw_payload JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_channel_metrics_unique
  ON vitalia_channel_metrics (tenant_id, clinic_id, provider, channel_slug, metric_date);
CREATE INDEX IF NOT EXISTS ix_vitalia_channel_metrics_date
  ON vitalia_channel_metrics (tenant_id, clinic_id, metric_date);
```

### 2.8 `vitalia_lucas_recommendations` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_lucas_recommendations (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  stage VARCHAR(32) NOT NULL, -- attraction | qualification | reservation | adoption | expansion
  recommendation_kind VARCHAR(64) NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  rationale_json JSONB NOT NULL DEFAULT '{}',
  priority INT NOT NULL DEFAULT 50,
  status VARCHAR(16) NOT NULL DEFAULT 'open', -- open | approved | rejected | expired | undone
  approved_by_user_id UUID NULL,
  approved_at TIMESTAMPTZ NULL,
  undo_until TIMESTAMPTZ NULL, -- 5min window
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS ix_vitalia_lucas_recommendations_stage_status
  ON vitalia_lucas_recommendations (tenant_id, clinic_id, stage, status, priority DESC)
  WHERE deleted_at IS NULL;
```

### 2.9 `vitalia_referrals` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_referrals (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  referrer_patient_id UUID NOT NULL,
  referred_patient_id UUID NULL,
  referral_code VARCHAR(16) NOT NULL,
  shared_at TIMESTAMPTZ NULL,
  signed_up_at TIMESTAMPTZ NULL,
  converted_at TIMESTAMPTZ NULL,
  conversion_value_cents BIGINT NULL,
  currency CHAR(3) NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'open', -- open | shared | signed_up | converted | expired
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_referrals_code
  ON vitalia_referrals (tenant_id, clinic_id, referral_code);
CREATE INDEX IF NOT EXISTS ix_vitalia_referrals_referrer
  ON vitalia_referrals (tenant_id, clinic_id, referrer_patient_id, status);
```

### 2.10 `vitalia_onboarding_progress` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_onboarding_progress (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  user_id UUID NOT NULL,
  step VARCHAR(64) NOT NULL,
  slots_confirmed JSONB NOT NULL DEFAULT '{}', -- {slot_id: {value, confidence, confirmed_at}}
  slots_pending JSONB NOT NULL DEFAULT '{}',
  mode VARCHAR(16) NULL, -- libre | guiado
  draft_id UUID NULL, -- references vitalia_brand_studio_drafts
  attachments JSONB NOT NULL DEFAULT '[]', -- {url, type, transcript_id}[]
  status VARCHAR(16) NOT NULL DEFAULT 'in_progress', -- in_progress | completed | abandoned
  completed_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_onboarding_progress_tenant_user
  ON vitalia_onboarding_progress (tenant_id, user_id);
```

### 2.11 `vitalia_brand_studio_drafts` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_brand_studio_drafts (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  user_id UUID NOT NULL,
  draft_kind VARCHAR(32) NOT NULL DEFAULT 'onboarding_extraction',
  draft_payload JSONB NOT NULL DEFAULT '{}', -- extracted slots, bonus fields, voice samples
  voice_profile_partial_json JSONB NULL, -- compiled personality_profile partial
  committed_at TIMESTAMPTZ NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_vitalia_brand_studio_drafts_tenant_user
  ON vitalia_brand_studio_drafts (tenant_id, user_id, committed_at);
```

### 2.12 `vitalia_audit_log` (NEW per `hipaa-lite.md` § Audit log)

```sql
CREATE TABLE IF NOT EXISTS vitalia_audit_log (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  user_id UUID NOT NULL,
  action VARCHAR(64) NOT NULL, -- view_diagnosis | edit_treatment_plan | view_dni | ...
  resource_type VARCHAR(64) NOT NULL,
  resource_id UUID NULL,
  from_ip INET NULL,
  user_agent TEXT NULL,
  payload_redacted BYTEA NULL, -- pgcrypto encrypted (defense in depth)
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (occurred_at);
-- Monthly partitions, retention 10 years per hipaa-lite.md
CREATE INDEX IF NOT EXISTS ix_vitalia_audit_log_tenant_clinic_action
  ON vitalia_audit_log (tenant_id, clinic_id, action, occurred_at DESC);
CREATE INDEX IF NOT EXISTS ix_vitalia_audit_log_resource
  ON vitalia_audit_log (tenant_id, clinic_id, resource_type, resource_id);
```

### 2.13 `tenants` column additions (engine consumes — modify via brand override pattern, NOT engine fork)

```sql
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS is_onboarded BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS location_country CHAR(2) NULL;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS location_city VARCHAR(128) NULL;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS timezone VARCHAR(64) NULL;
```

**Note:** `tenants` table lives in `core/luana-core-platform/`. Column additions here are platform-shared candidates → escalate to `/pm-luana` promotion proposal `2026-05-17-platform-tenants-location-columns.md` (NEW). PRE-MERGE GATE: `/pm-luana` ratifies before /dev-team picks T-be-migration-014.

### 2.14 `offers` column additions (engine consumes — promotion proposal required)

```sql
ALTER TABLE offers ADD COLUMN IF NOT EXISTS requires_multi_session BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE offers ADD COLUMN IF NOT EXISTS sessions_expected INT NULL;
ALTER TABLE offers ADD COLUMN IF NOT EXISTS gap_alert_days INT NULL;
ALTER TABLE offers ADD COLUMN IF NOT EXISTS maintenance_schedule VARCHAR(32) NULL; -- enum: monthly | quarterly | semiannual | annual | custom | none
ALTER TABLE offers ADD COLUMN IF NOT EXISTS maintenance_custom_days INT NULL;
```

**Note:** `offers` lives in `core/luana-core-offer-studio/`. Promotion proposal `2026-05-17-offer-studio-multi-session-maintenance.md` (NEW) required before T-be-migration-015 picks.

### 2.15 `patients` column additions

```sql
ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS marketing_opt_in BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out_reason TEXT NULL;
ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out_at TIMESTAMPTZ NULL;
```

## 3. API endpoints (~50 endpoints)

All routes under `/api/v1/vitalia/...`. Bearer auth + `X-Tenant-ID` + `X-Clinic-ID` headers mandatory. `response_model=` on every route (PII allowlist enforcement). `FastAPI(redirect_slashes=False)`.

### 3.1 Inbox routes (8 endpoints)

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| GET | `/inbox/conversations` | doctor/nurse/admin_clinic/marketing | query: status, mode_filter, channel, period | `ConversationListResponse` | List conversations 3-modos filter |
| GET | `/inbox/conversations/{conv_id}` | doctor/nurse/admin_clinic | — | `ConversationDetailResponse` | Conv detail + messages + activity |
| POST | `/inbox/conversations/{conv_id}/messages` | doctor/nurse/admin_clinic | `SendMessageRequest` | `MessageResponse` | Send manual message (handles attach) |
| POST | `/inbox/conversations/{conv_id}/retract/{msg_id}` | doctor/nurse/admin_clinic | — | `RetractResponse` | Retract within 5min undo window |
| POST | `/inbox/conversations/{conv_id}/pause-adrian` | admin_clinic | `PauseAdrianRequest` (duration_minutes=60) | `PauseAdrianResponse` | Pause Adrián for conversation |
| GET | `/inbox/conversations/{conv_id}/activity-stream` | doctor/nurse/admin_clinic | query: limit, since | `ActivityStreamResponse` | Sticky 32px expand 240px feed |
| POST | `/inbox/proactive-outbound` | marketing/sales | `ProactiveOutboundRequest` | `ProactiveOutboundResponse` | Cross-link /agenda /pipeline /marketing |
| GET | `/inbox/conversations/{conv_id}/tools-state` | doctor/nurse/admin_clinic | — | `ToolsStateResponse` | Read-only sheet last-used display |

### 3.2 Pipeline routes (6 endpoints)

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| GET | `/pipeline/leads` | doctor/nurse/admin_clinic/marketing | query: stage, offer, channel, period | `LeadListResponse` | Kanban Slice 1 / Lista Slice 2 |
| GET | `/pipeline/leads/{lead_id}` | doctor/nurse/admin_clinic | — | `LeadDetailResponse` | Lead detail card expand |
| POST | `/pipeline/leads/{lead_id}/move` | doctor/nurse/admin_clinic | `MoveLead Request` (target_stage, reason) | `MoveLeadResponse` | Manual DnD + reason |
| POST | `/pipeline/leads/{lead_id}/screening` | doctor/nurse/admin_clinic | `ScreeningRequest` | `ScreeningResponse` | Lucas screening clínico per vertical |
| GET | `/pipeline/summary` | doctor/nurse/admin_clinic/marketing | query: period | `PipelineSummaryResponse` | Header metrics (total leads, value, funnel, conv rate) |
| POST | `/pipeline/leads/{lead_id}/undo-move/{event_id}` | doctor/nurse/admin_clinic | — | `UndoMoveResponse` | 5min undo auto-move (Slice 2 — Slice 1 stub returns 501) |

### 3.3 Agenda routes (12 endpoints)

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| GET | `/agenda/slots` | doctor/nurse/admin_clinic | query: view, date, doctor, specialty, status_pago | `AgendaSlotsResponse` | Week/Day/Month view |
| POST | `/agenda/appointments` | doctor/nurse/admin_clinic | `CreateAppointmentRequest` (4 origins) | `AppointmentResponse` | Create (walk_in / phone_manual / sales_agent / proactive_outbound) |
| GET | `/agenda/appointments/{appt_id}` | doctor/nurse/admin_clinic | — | `AppointmentDetailResponse` | Slot detail PHI gate |
| PATCH | `/agenda/appointments/{appt_id}/reschedule` | doctor/nurse/admin_clinic | `RescheduleRequest` (`Idempotency-Key`) | `RescheduleResponse` | DnD + modal fallback |
| POST | `/agenda/appointments/{appt_id}/cancel` | doctor/nurse/admin_clinic | `CancelRequest` | `CancelResponse` | 24h refund policy hardcoded Slice 1 |
| POST | `/agenda/appointments/{appt_id}/checkin` | doctor/nurse/admin_clinic | — | `CheckinResponse` | Mark arrived |
| POST | `/agenda/appointments/{appt_id}/complete` | doctor/nurse | `CompleteRequest` (follow_up_due_at, follow_up_reason) | `CompleteResponse` | Close appointment + trigger NPS cron |
| POST | `/agenda/appointments/{appt_id}/payments` | doctor/nurse/admin_clinic | `PaymentCaptureRequest` (Idempotency-Key) | `PaymentResponse` | Capa 1 captura + audit + receipt internal VLT |
| POST | `/agenda/appointments/{appt_id}/fiscal-emit` | admin_clinic | `FiscalEmitRequest` (provider=nubefact_pe) | `FiscalReceiptResponse` | Capa 2 fiscal emission via Nubefact PE |
| POST | `/agenda/appointments/{appt_id}/refund` | admin_clinic | `RefundRequest` | `RefundResponse` | Refund flow (24h hardcoded) |
| GET | `/agenda/appointments/{appt_id}/receipt-pdf` | doctor/nurse/admin_clinic | — | `Response` (application/pdf) | Capa 3 window.print() PDF |
| GET | `/agenda/availability` | doctor/nurse/admin_clinic | query: date_range, specialty | `AvailabilityResponse` | Open slots calculation |

### 3.4 Fidelizacion routes (8 endpoints)

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| GET | `/fidelizacion/treatments` | doctor/nurse/admin_clinic | query: tab, period, vertical, doctor, urgency | `TreatmentsListResponse` | Tab 1 — multi-session in progress |
| GET | `/fidelizacion/follow-ups` | doctor/nurse/admin_clinic | query: tab params | `FollowUpsListResponse` | Tab 2 — doctor-set follow-ups |
| GET | `/fidelizacion/maintenance` | doctor/nurse/admin_clinic | query: tab params | `MaintenanceListResponse` | Tab 3 — maintenance schedules due |
| GET | `/fidelizacion/absences` | doctor/nurse/admin_clinic | query: tab params | `AbsencesListResponse` | Tab 4 — long absences |
| GET | `/fidelizacion/nps` | doctor/nurse/admin_clinic/marketing | query: period | `NpsStatCardResponse` | Tab 5 — NPS resumido stat card Slice 1 |
| POST | `/fidelizacion/patients/{patient_id}/send-proactive` | marketing/admin_clinic | `SendProactiveRequest` (template_id, slot_values) | `SendProactiveResponse` | Adrián abre conv solicitado |
| POST | `/fidelizacion/patients/{patient_id}/pause` | doctor/nurse/admin_clinic | `PausePatientRequest` (duration_days, reason) | `PausePatientResponse` | Pause re-engagement |
| POST | `/fidelizacion/patients/{patient_id}/mark-external` | doctor/nurse/admin_clinic | `MarkExternalRequest` | `MarkExternalResponse` | Silence pattern (external scheduling) |

### 3.5 Marketing routes (10 endpoints)

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| GET | `/marketing/bowtie/summary` | marketing/admin_clinic | query: period | `BowtieSummaryResponse` | 5 stages overview (Tier 0 cache) |
| GET | `/marketing/stage/{stage_slug}` | marketing/admin_clinic | path: attraction|qualification|reservation|adoption|expansion | `StageDetailResponse` | Per-stage detail (Tier 2) |
| GET | `/marketing/channels/{provider}` | marketing/admin_clinic | path: meta_ads|google_ads | `ChannelDetailResponse` | Channel detail sidebar drill |
| POST | `/marketing/channels/{provider}/connect` | admin_clinic | `OAuthConnectRequest` | `OAuthConnectResponse` | OAuth wizard 3 pasos |
| POST | `/marketing/channels/{provider}/sync` | admin_clinic | — | `SyncResponse` | Force sync (cron c/4h normal) |
| GET | `/marketing/recommendations` | marketing/admin_clinic | query: stage, status, limit | `LucasRecommendationsResponse` | Lucas 3 cards per stage |
| POST | `/marketing/recommendations/{rec_id}/approve` | admin_clinic | `ApproveRequest` (Idempotency-Key) | `ApproveResponse` | Owner approves Lucas + 5min undo window |
| POST | `/marketing/recommendations/{rec_id}/reject` | admin_clinic | `RejectRequest` (reason) | `RejectResponse` | Reject Lucas + reason audit |
| POST | `/marketing/recommendations/{rec_id}/undo` | admin_clinic | — | `UndoResponse` | Undo within 5min window |
| GET | `/marketing/attribution-matrix` | marketing/admin_clinic | query: period | `AttributionMatrixResponse` | 4 origins (Stage Reserva) |
| GET | `/marketing/referrals` | marketing/admin_clinic | query: period, leaderboard_limit | `ReferralsResponse` | Stage Expansión widget |

### 3.6 Onboarding routes (5 endpoints — depend on `vitalia-copilot-tools-impl`)

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| POST | `/onboarding/start` | authenticated user | — | `OnboardingStartResponse` | Initialize progress + greet |
| POST | `/onboarding/extract` | authenticated user | `ExtractRequest` (urls, doc_uploads, audio_uploads) | `ExtractResponse` | NLU extraction subagent (URL/doc/audio) |
| POST | `/onboarding/confirm-slot` | authenticated user | `ConfirmSlotRequest` (slot_id, value, confidence) | `ConfirmSlotResponse` | Confirm extracted slot inline |
| POST | `/onboarding/simulate-voice` | authenticated user | `SimulateVoiceRequest` (profile_partial, scenario) | `SimulateVoiceResponse` | Adrián voice preview (live preview area) — throttled 5/min |
| POST | `/onboarding/complete` | authenticated user | `CompleteOnboardingRequest` | `CompleteOnboardingResponse` | Commit draft → BrandStudio + activate |

### 3.7 IAM + CRM routes (5 endpoints)

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| GET | `/iam/me` | authenticated | — | `MeResponse` | Current user + role + clinic_id |
| GET | `/crm/patients/{patient_id}` | doctor/nurse/admin_clinic | — | `PatientDetailResponse` | PHI gate + audit |
| PATCH | `/crm/patients/{patient_id}` | doctor/nurse/admin_clinic | `PatientPatchRequest` | `PatientResponse` | Update opt_in/opt_out |
| GET | `/crm/leads/{lead_id}` | doctor/nurse/admin_clinic/marketing | — | `LeadDetailResponse` | Lead detail (no PHI in DTO) |
| POST | `/crm/patients/{patient_id}/opt-out` | doctor/nurse/admin_clinic | `OptOutRequest` (reason) | `OptOutResponse` | Mark opt_out + cascade re-engagement cancel |

## 4. Cron jobs (11 ARQ workers)

All cron jobs traced via OpenTelemetry (per `03-arch.md § 6`). Best-effort writes, structlog warnings, soft-fail. Idempotency via natural keys.

| Cron name | Frequency | Owner module | Purpose |
|---|---|---|---|
| `lucas_daily_analysis_sweep` | daily 06:00 UTC | marketing | Compute Lucas recommendations per tenant+clinic+stage |
| `multi_session_gap_sweep` | daily 07:00 UTC | fidelizacion | Detect treatment_plans with gap > gap_alert_days |
| `follow_up_due_sweep` | daily 07:30 UTC | fidelizacion | Detect appointments.follow_up_due_at within 7 days |
| `maintenance_due_sweep` | daily 08:00 UTC | fidelizacion | Detect offers.maintenance_schedule + last appt > schedule |
| `absence_sweep` | weekly Mon 06:00 UTC | fidelizacion | Detect patients with last appt > 6 months |
| `nps_post_treatment_sweep` | hourly :15 | fidelizacion | Send NPS 24h post-completion |
| `re_engagement_response_timeout_sweep` | daily 09:00 UTC | fidelizacion | Mark not_responsive after 7d |
| `channel_metrics_sync_meta` | every 4h | marketing | Pull Meta Ads metrics |
| `channel_metrics_sync_google` | every 4h | marketing | Pull Google Ads metrics |
| `payment_timeout_sweep` | hourly :45 | agenda | Auto-cancel appointments with phone_manual unpaid 72h |
| `referrals_value_sync` | daily 10:00 UTC | marketing | Compute referrals conv values from appointments |

ARQ runner config: `vitalia/backend/src/modules/vitalia/_shared/workers/arq_settings.py` registers all 11 cron functions with retry logic (max 3 attempts, exponential backoff).

## 5. Services (7+ new)

| Service | Module | Purpose |
|---|---|---|
| `WebsiteScraperService` | onboarding | Scrape tenant website for brand context (extends `core/luana-core-brand-studio/.../brand_data_adapter.py`) |
| `DocumentExtractorService` | onboarding | Parse PDF/DOCX uploads for slot extraction |
| `AudioTranscriberService` | onboarding + inbox | Whisper STT (audio IN) |
| `NubefactAdapterService` | connections/fiscal | PE fiscal emission (side story `vitalia-fiscal-emission-pe`) |
| `MercadoPagoAdapterService` | connections/payment | Payment deposit 30% (side story `vitalia-payment-adapter-mvp`) |
| `MercadoPagoRefundHandler` | connections/payment | Refund flow within 24h policy |
| `LucasRecommendationsService` | marketing | Compute + persist recommendations (Lucas agentic — see 03-arch-agentic.md) |
| `AttributionService` | marketing | UTM tracking lead→origin matrix |
| `ReferralsService` | marketing | Referral codes + leaderboard + conv tracking |
| `ScreeningService` | pipeline | Lucas screening clínico per vertical |
| `TreatmentFollowupService` | fidelizacion | Manage treatment_plans + re_engagement triggers |
| `ReEngagementService` | fidelizacion | Send proactive WhatsApp templates |
| `NpsService` | fidelizacion | NPS post-treatment lifecycle |
| `PaymentService` | agenda | 3 capas cobranza orchestration |
| `FiscalService` | agenda | Fiscal emission orchestration |
| `RefundService` | agenda | Refund policy enforcement |
| `OnboardingService` | onboarding | Slot lifecycle + draft commit |
| `SlotExtractionService` | onboarding | NLU slot extraction routing |
| `LivePreviewService` | onboarding | WhatsApp + Landing snippet preview (debounced + cached) |

## 6. Extension SDK registries (5 NEW Vitalia + existing EP-1..EP-18 mounts)

All 5 NEW registries mount via existing EP-3 (tools) or EP-4 (workflows) or EP-2 (presets) — they are **brand-specific dict structures** internal to Vitalia, NOT engine modifications. Slice 2 lift candidates (NEW core EP-19..EP-23) documented in `delta-arch-notes.md`.

### 6.1 `payment_provider_registry`

```python
# vitalia/backend/src/modules/vitalia/connections/payment/registry.py
@dataclass(frozen=True)
class PaymentProviderDef:
    provider_id: str
    label_es: str
    capture_method: Literal["manual", "webhook", "qr_live"]
    supports_refund: bool
    supports_recurring: bool
    handler_ref: str  # callable path

PAYMENT_PROVIDER_REGISTRY: dict[str, PaymentProviderDef] = {
    "manual_cash":      PaymentProviderDef(...),  # Slice 1
    "manual_card":      PaymentProviderDef(...),  # Slice 1
    "manual_transfer":  PaymentProviderDef(...),  # Slice 1
    "manual_mp":        PaymentProviderDef(...),  # Slice 1
    "other":            PaymentProviderDef(...),  # Slice 1
    "mercadopago":      PaymentProviderDef(...),  # depends vitalia-payment-adapter-mvp
    # Slice 2 candidates: mercadopago_qr_live, culqi, niubiz, stripe_connect
}
```

Mount: `extensions.py::register_all(registry)` → `registry.register_tool(tool_id="vitalia.capture_payment", handler=capture_payment_router)`.

### 6.2 `fiscal_provider_registry`

```python
FISCAL_PROVIDER_REGISTRY: dict[str, FiscalProviderDef] = {
    "nubefact_pe": FiscalProviderDef(
        provider_id="nubefact_pe",
        country="PE",
        emits=["boleta", "factura", "nota_credito"],
        handler_ref="vitalia.connections.fiscal.nubefact_pe.adapter:submit_receipt",
        retry_queue=True,
        cdr_archive=True,
    ),
    # Slice 2 candidates: tefacturo_pe, facturak_pe
    # Slice 3 candidates: facturama_mx, dian_co, afip_ar, sii_cl
}
```

### 6.3 `appointment_origin_registry`

```python
APPOINTMENT_ORIGIN_REGISTRY: dict[str, AppointmentOriginDef] = {
    "sales_agent":         AppointmentOriginDef(...),  # default
    "walk_in":             AppointmentOriginDef(...),  # NEW Slice 1
    "phone_manual":        AppointmentOriginDef(...),  # NEW Slice 1
    "proactive_outbound":  AppointmentOriginDef(...),  # NEW Slice 1
    # Slice 2 candidates: kiosk_self_checkin, partner_referral, recurring_treatment
}
```

### 6.4 `conversation_initiation_registry`

```python
CONVERSATION_INITIATION_REGISTRY: dict[str, ConversationInitiationDef] = {
    "whatsapp_template_meta": ConversationInitiationDef(
        kind="whatsapp_template",
        category=Literal["UTILITY", "MARKETING"],
        requires_opt_in_if_marketing=True,
        handler_ref="vitalia.connections.whatsapp.adapter:send_template",
    ),
    # Slice 2: sms_twilio, email_sendgrid
    # Slice 3: voice_call_agent_twilio
}
```

### 6.5 `print_method_registry`

```python
PRINT_METHOD_REGISTRY: dict[str, PrintMethodDef] = {
    "browser_pdf": PrintMethodDef(
        method="window.print()",  # FE-only Slice 1
        formats=["pdf"],
    ),
    # Slice 2: webusb_escpos (NielsLeenheer library, 58mm/80mm)
    # Slice 3: network_ipp
}
```

### 6.6 EP-1..EP-18 mounts (existing Story 11 cement)

`vitalia/backend/src/modules/vitalia/extensions.py::register_all(registry)` mounts:
- EP-2 offer preset pack `medical_services_v1`
- EP-3 tools (Slice 1 placeholders + side story `vitalia-copilot-tools-impl` real handlers)
- EP-4 workflows (`TreatmentFollowupWorkflow` Slice 1)
- EP-7 extractors (`MedicalKBExtractor`, `DentalHistoryExtractor`)
- EP-8 channel adapters (whatsapp_business, manychat_instagram, email_async, web_chat)
- EP-13 guardrails (`medical_safety_no_diagnosis`, `medical_safety_no_prescription`, `medical_disclaimer_required`, `prompt_injection_block`)
- EP-14 KB packs (`medical_kb_dental_v1`, `medical_kb_psychology_v1`, `medical_kb_psychiatry_v1`)

## 7. Domain entities (key shapes)

All entities follow Inside-Out DDD per `.claude/rules/backend-ddd.md`. `tenant_id` + `clinic_id` mandatory. `deleted_at` for soft delete.

### 7.1 `Appointment` (updated Slice 1)

```python
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from enum import StrEnum

class AppointmentOrigin(StrEnum):
    SALES_AGENT = "sales_agent"
    WALK_IN = "walk_in"
    PHONE_MANUAL = "phone_manual"
    PROACTIVE_OUTBOUND = "proactive_outbound"

class BalanceStatus(StrEnum):
    PENDING = "pending"
    DEPOSIT_PAID = "deposit_paid"
    FULL_PAID = "full_paid"
    REFUNDED = "refunded"

class Appointment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID
    doctor_id: UUID | None
    offer_id: UUID | None
    starts_at: datetime  # UTC, timezone-aware
    ends_at: datetime
    origin: AppointmentOrigin
    balance_status: BalanceStatus
    follow_up_due_at: datetime | None
    follow_up_reason: str | None
    completed_at: datetime | None
    utm_source: str | None
    utm_campaign: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 7.2 `TreatmentPlan` (NEW)

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
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 7.3 `LucasRecommendation` (NEW)

```python
class LucasRecommendationStatus(StrEnum):
    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    UNDONE = "undone"

class LucasRecommendation(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    stage: str  # attraction|qualification|reservation|adoption|expansion
    recommendation_kind: str
    title: str
    body: str
    rationale_json: dict
    priority: int  # higher = surfaced first
    status: LucasRecommendationStatus
    approved_by_user_id: UUID | None
    approved_at: datetime | None
    undo_until: datetime | None  # 5min window
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### 7.4 `OnboardingProgress` (NEW)

```python
class OnboardingStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class OnboardingProgress(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    user_id: UUID
    step: str
    slots_confirmed: dict  # {slot_id: {value, confidence, confirmed_at}}
    slots_pending: dict
    mode: Literal["libre", "guiado"] | None
    draft_id: UUID | None
    attachments: list[dict]
    status: OnboardingStatus
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

## 8. Repository interfaces

All repositories async, every method receives `tenant_id` + `clinic_id` (PHI tables) — including `get_by_id`.

```python
# vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py
from abc import ABC, abstractmethod
from uuid import UUID

class PhiRepositoryBase(ABC):
    """Mandatory base class for repositories accessing PHI tables.
    
    Enforces tenant_id + clinic_id dual filter cardinal per hipaa-lite.md.
    Arch fitness test_phi_dual_filter.py validates subclasses.
    """
    
    @abstractmethod
    async def get_by_id(self, entity_id: UUID, *, tenant_id: UUID, clinic_id: UUID): ...
    
    @abstractmethod
    async def list_by_filter(self, *, tenant_id: UUID, clinic_id: UUID, **filters): ...
```

Concrete example:

```python
# vitalia/backend/src/modules/vitalia/agenda/infrastructure/repositories/appointment_repository.py
class AppointmentRepository(PhiRepositoryBase):
    async def get_by_id(self, appt_id: UUID, *, tenant_id: UUID, clinic_id: UUID) -> Appointment | None:
        stmt = select(AppointmentModel).where(
            AppointmentModel.id == appt_id,
            AppointmentModel.tenant_id == tenant_id,
            AppointmentModel.clinic_id == clinic_id,  # dual filter — CARDINAL
            AppointmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return Appointment.model_validate(row) if row else None
```

## 9. Application services (transaction boundaries + events)

Services emit DomainEvents via `core/luana-core-events/` outbox bus (`USE_OUTBOX_PATTERN_*=True` post 2026-04-30 default).

```python
# vitalia/backend/src/modules/vitalia/agenda/application/services/payment_service.py
class PaymentService:
    async def capture_payment(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        appointment_id: UUID,
        user_id: UUID,
        request: PaymentCaptureRequest,
        idempotency_key: str,
    ) -> PaymentResponse:
        # 1. Idempotency check (core/luana-core-idempotency/)
        existing = await self.idempotency_repo.check(idempotency_key)
        if existing: return existing
        
        async with self.uow.begin():  # transaction boundary
            # 2. Dual filter load
            appt = await self.appt_repo.get_by_id(
                appointment_id, tenant_id=tenant_id, clinic_id=clinic_id
            )
            if not appt: raise NotFound()
            
            # 3. Audit log sync write FIRST (defense in depth)
            await self.audit_log_repo.record(
                tenant_id=tenant_id, clinic_id=clinic_id, user_id=user_id,
                action="capture_payment", resource_type="appointment",
                resource_id=appointment_id,
                payload_redacted=sanitize_payload(request.model_dump(), "hipaa_lite"),
            )
            
            # 4. Provider dispatch via registry (Slice 1 manual only; mercadopago via side story)
            handler = PAYMENT_PROVIDER_REGISTRY[request.provider].handler_ref
            provider_result = await handler(request)
            
            # 5. Persist payment_event
            event = PaymentEvent(...)
            await self.payment_repo.create(event)
            
            # 6. Update appointment balance_status
            appt.balance_status = BalanceStatus.DEPOSIT_PAID if request.is_deposit else BalanceStatus.FULL_PAID
            await self.appt_repo.save(appt)
            
            # 7. Idempotency cache result
            await self.idempotency_repo.set(idempotency_key, result)
            
            # 8. Emit DomainEvent via outbox
            await self.event_bus.publish(
                PaymentCapturedEvent(
                    tenant_id=tenant_id, clinic_id=clinic_id,
                    appointment_id=appointment_id, payment_event_id=event.id,
                ),
                session=self.session,
            )
        
        return PaymentResponse.model_validate(event)
```

## 10. Cross-cutting concerns (BE-specific)

- **`structlog`** mandatory. No `print()` / stdlib `logging`. Log via `logger.bind(tenant_id=..., clinic_id=..., trace_id=...)`.
- **Async-first.** All repos, services, route handlers `async def`. AsyncSession.
- **SQLAlchemy 2.0** only. `mapped_column()`, `select(...)`, no `Column()` or `session.query()`.
- **Pydantic v2** ConfigDict. No inner `class Config`.
- **`response_model=`** mandatory every route (PII allowlist).
- **`X-Tenant-ID` + `X-Clinic-ID`** middleware-injected from Clerk JWT claims.
- **`FastAPI(redirect_slashes=False)`** in `main.py`.
- **TenantLocale VO** from `core/luana-core-platform/` for timezone + currency. NEVER `datetime.utcnow()` — use `utc_now()` helper.
- **Migrations idempotent** raw SQL `IF NOT EXISTS`. Test pre-prod with clone DB workflow per `.claude/rules/backend-migrations.md`.
- **Anti-default-flip-audit** — Slice 1 introduces NO default flag flips (per `.claude/rules/anti-default-flip-audit.md`). If future story flips → audit Step 1-4 mandatory.

## 11. Test surfaces (TDD-mandatory per layer)

Per `.claude/rules/tdd-mandatory.md`:

| Layer | Test file pattern | RED first |
|---|---|---|
| Domain | `vitalia/backend/tests/modules/vitalia/{m}/domain/test_*.py` | YES |
| Infrastructure (models, repos) | `vitalia/backend/tests/modules/vitalia/{m}/infrastructure/test_*.py` | YES |
| Application (services) | `vitalia/backend/tests/modules/vitalia/{m}/application/test_*.py` | YES |
| API/E2E (route handlers) | `vitalia/backend/tests/modules/vitalia/{m}/api/test_*.py` | YES |
| Migrations (smoke) | `vitalia/backend/tests/migrations/test_slice1_migrations.py` | NO (smoke only) |
| Architecture fitness | `vitalia/backend/tests/architecture/test_*.py` | YES (allowlist shrinkage) |
| PHI compliance | `vitalia/backend/tests/architecture/test_phi_dual_filter.py`, `test_audit_log_sync_write.py`, `test_pgcrypto_phi_columns.py` | YES |
| Cron jobs | `vitalia/backend/tests/workers/test_*.py` | YES (smoke) |
| Extension SDK registration | `vitalia/backend/tests/test_extensions.py` | YES |

Coverage threshold: 43% BE (per `.claude/rules/backend-quality.md`). Slice 1 target ≥ 50% per module.

## 12. Architectural fitness impact

Allowlist shrinkage planned:
- `test_no_cross_brand_imports.py` — zero growth
- `test_response_model_required.py` — zero new exceptions (all new routes MUST declare)
- `test_phi_dual_filter.py` — NEW gate Slice 1 (enforces from start)
- `test_audit_log_sync_write.py` — NEW gate Slice 1
- `test_pgcrypto_phi_columns.py` — NEW gate Slice 1
- `test_extension_sdk_registration.py` — verify 5 NEW registries register via EP-3/EP-4/EP-2 (no parallel EP layer)
- `test_no_legacy_paths.py` — zero `backend/src/shared/` imports (post-multibrand-reorg)
