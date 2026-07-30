# vitalia-slice-1-inbox — Backend sub-architecture

> **Consumer:** `builder-backend` (Sonnet build) + `auditor-backend` (Opus audit).
> **Index:** `03-arch.md` § 0-9 (read first).
> **Brand surface:** `vitalia/backend/src/modules/vitalia/{inbox,crm,connections,iam}/` + `vitalia/backend/src/modules/vitalia/extensions.py` (extend existing Story 11 cement).
> **Engine consultation:** READ-ONLY `core/luana-core-{crm,channels,observability,platform,sales-agent,copilot,compliance,extension-sdk,idempotency,events}/`.

## 1. Module structure (DDD Inside-Out per `.claude/rules/backend-ddd.md`)

```
vitalia/backend/src/modules/vitalia/
├── _shared/                                ← brand-internal shared (Story 11 cement)
│   ├── repositories/                       ← phi_repository.PhiRepositoryBase MIGRATING to compound_scope (pre-flight gate HANDOFF § 2)
│   ├── encryption/kek_client.py
│   ├── auth/rbac.py                        ← @require_phi_access decorator
│   └── observability/                      ← otel_setup, agent_spans, sentry_alerts
├── crm/                                    ← EXISTING — extend with Conversation + Message + ActivityEvent + ActionReceipt
│   ├── domain/
│   │   ├── lead.py                         ← EXISTING (NOT PHI, tenant_id only filter)
│   │   ├── patient.py                      ← EXISTING (PHI dual-filter)
│   │   ├── conversation.py                 ← NEW (PHI dual-filter)
│   │   ├── message.py                      ← NEW (PHI dual-filter)
│   │   ├── activity_event.py               ← NEW (mirror of copilot_trace_event filtered per conv)
│   │   ├── action_receipt.py               ← NEW (5min undo window)
│   │   └── events.py                       ← NEW (ConversationStarted, MessageSent, MessageRetracted, ModeChanged, AdrianPaused, ProactiveOutboundSent)
│   ├── infrastructure/
│   │   └── persistence/
│   │       ├── lead_repository.py          ← EXISTING (migrate from phi_repository → tenant-only since Lead non-PHI)
│   │       ├── patient_repository.py       ← EXISTING (consume CompoundScopeRepositoryBase scope_field="clinic_id")
│   │       ├── conversation_repository.py  ← NEW (consume CompoundScopeRepositoryBase scope_field="clinic_id")
│   │       ├── message_repository.py       ← NEW (idem)
│   │       ├── activity_event_repository.py ← NEW (idem)
│   │       └── action_receipt_repository.py ← NEW (idem)
│   ├── application/
│   │   ├── services/
│   │   │   ├── lead_service.py             ← EXISTING — extend with `list_for_inbox(filters)`
│   │   │   ├── patient_service.py          ← EXISTING
│   │   │   ├── conversation_service.py     ← NEW
│   │   │   └── activity_event_service.py   ← NEW (consume copilot_trace_event filter by conversation_id)
│   │   └── dto/
│   │       ├── lead_dto.py                 ← EXISTING — extend with LeadFilterRequest + LeadListResponse
│   │       ├── patient_dto.py              ← EXISTING
│   │       ├── conversation_dto.py         ← NEW
│   │       ├── message_dto.py              ← NEW
│   │       ├── activity_event_dto.py       ← NEW
│   │       └── action_receipt_dto.py       ← NEW
│   └── api/
│       └── router.py                       ← EXISTING — extend with conversation endpoints
├── inbox/                                  ← NEW Slice 1 (orchestrator + actions, separate from CRM CRUD)
│   ├── application/
│   │   ├── services/
│   │   │   ├── inbox_orchestrator.py       ← NEW (compose lead+conv+msg+activity)
│   │   │   ├── send_message_service.py     ← NEW (handles ai|human paths · idempotency)
│   │   │   ├── retract_message_service.py  ← NEW (consume connections.{wa,ig,email}.retract · audit log)
│   │   │   ├── set_mode_service.py         ← NEW (mode change · OCC conflict resolve)
│   │   │   ├── pause_adrian_service.py     ← NEW (60min pause · Redis lock)
│   │   │   ├── proactive_outbound_service.py ← NEW (HSM template picker · compliance gate)
│   │   │   ├── whisper_transcribe_service.py ← NEW (wraps connections.whisper.adapter)
│   │   │   └── tools_state_service.py      ← NEW (derive from offer.tools_enabled · read-only)
│   │   └── dto/
│   │       ├── conversation_list_dto.py    ← list + filters
│   │       ├── send_message_dto.py
│   │       ├── retract_message_dto.py
│   │       ├── set_mode_dto.py
│   │       ├── proactive_outbound_dto.py
│   │       └── tools_state_dto.py
│   └── api/
│       └── router.py                       ← NEW · 8 endpoints inbox-specific (see § 4)
├── connections/                            ← EXISTING (Story 11 scaffold) — extend
│   ├── whatsapp/
│   │   ├── adapter.py                      ← EXISTING — extend with retract_message_id(message_id) method
│   │   └── webhook_handler.py              ← EXISTING (inbound msgs persist via conversation_repository)
│   ├── instagram/
│   │   └── adapter.py                      ← EXISTING — extend with retract_message_id
│   ├── email/
│   │   └── adapter.py                      ← EXISTING (retract = NOT supported, fallback "marcar erróneo")
│   └── whisper/                            ← NEW Slice 1
│       └── adapter.py                      ← NEW (OpenAI Whisper API client · timeout 30s · graceful-degradation)
├── iam/                                    ← EXISTING (Story 11) — RBAC decorator used by inbox endpoints
├── copilot/                                ← EXISTING (Story 11 placeholder)
│   ├── persistence/
│   │   └── models/
│   │       ├── copilot_trace_event.py      ← EXISTING (schema mirror per backend-ddd.md schema-mirror exception)
│   │       └── copilot_llm_call.py         ← EXISTING (idem)
│   └── (no logic changes Slice 1)
├── sales_agent/                            ← EXISTING (Story 11 + vitalia-copilot-tools-impl shipped 2026-05-19)
│   ├── tools/
│   │   ├── payment_link.py                 ← EXISTING (shipped)
│   │   ├── reschedule_appointment.py       ← EXISTING (shipped)
│   │   ├── screening_questions.py          ← EXISTING (shipped)
│   │   └── retract_last_message.py         ← NEW Slice 1 (R23 Opus — managed by builder-agentic)
│   └── (rest unchanged · see 03-arch-agentic.md)
├── audit/                                  ← EXISTING (Story 11)
│   └── audit_writer.py                     ← EXISTING — used by inbox services for sync write pre-response
├── extensions.py                           ← EXISTING — register new conversation/message tools via EP if applicable
└── persistence/migrations/                 ← Alembic idempotent raw SQL
    └── (migrations cementadas Story 11 + slice-1-infra) — NEW migration this story: 024_inbox_tables.py
```

## 2. Tables (4 NEW + 1 column addition)

Prefix `vitalia_` (per `infra.dev.database_name=vitalia_dev`). Mandatory columns en PHI tables: `tenant_id UUID NOT NULL`, `clinic_id UUID NOT NULL`, `deleted_at TIMESTAMPTZ NULL`, `created_at TIMESTAMPTZ NOT NULL`, `updated_at TIMESTAMPTZ NOT NULL`. Indexes composite `(tenant_id, clinic_id, ...)`.

### 2.1 `vitalia_conversations` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_conversations (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  lead_id UUID NOT NULL,
  patient_id UUID NULL,                     -- once lead converts to patient
  channel VARCHAR(32) NOT NULL,              -- whatsapp | instagram | facebook_messenger | web | walk_in | phone
  channel_external_id VARCHAR(128) NULL,     -- WA/IG conversation external ref
  status VARCHAR(16) NOT NULL DEFAULT 'active', -- active | paused | closed | archived
  handler_mode VARCHAR(16) NOT NULL DEFAULT 'ai',  -- ai | human
  proposal_required BOOLEAN NOT NULL DEFAULT FALSE,
  pause_until TIMESTAMPTZ NULL,              -- 60min pause window (handler_mode auto-resumes after)
  help_needed BOOLEAN NOT NULL DEFAULT FALSE,
  help_needed_reason TEXT NULL,
  unread_media_count INT NOT NULL DEFAULT 0,
  last_message_at TIMESTAMPTZ NULL,
  last_message_preview TEXT NULL,            -- truncated for list rendering
  messages_count INT NOT NULL DEFAULT 0,
  stage_decision VARCHAR(32) NULL,           -- interesado | considerando | listo | decidio_no (mirror of pipeline)
  linked_offer_id UUID NULL,                 -- engine offer reference
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_tenant_clinic_status
  ON vitalia_conversations (tenant_id, clinic_id, status)
  WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_lead
  ON vitalia_conversations (tenant_id, clinic_id, lead_id)
  WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_help_needed
  ON vitalia_conversations (tenant_id, clinic_id, help_needed, last_message_at DESC)
  WHERE help_needed = TRUE AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_unread_media
  ON vitalia_conversations (tenant_id, clinic_id, unread_media_count, last_message_at DESC)
  WHERE unread_media_count > 0 AND deleted_at IS NULL;
```

### 2.2 `vitalia_messages` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_messages (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  conversation_id UUID NOT NULL REFERENCES vitalia_conversations(id),
  channel VARCHAR(32) NOT NULL,              -- mirror of conversation.channel for query convenience
  external_message_id VARCHAR(128) NULL,     -- WA/IG message wamid / ig_msg_id
  sender_type VARCHAR(16) NOT NULL,          -- patient | agent_ai | agent_human | system
  sender_user_id UUID NULL,                  -- if sender_type=agent_human
  body_text TEXT NULL,
  media_kind VARCHAR(16) NULL,               -- audio | image | video | document | sticker
  media_url TEXT NULL,                       -- pre-signed S3 URL or external URL
  media_duration_s INT NULL,                 -- for audio
  media_phi_flagged BOOLEAN NOT NULL DEFAULT FALSE,
  transcription_text TEXT NULL,              -- Whisper STT output for audio IN
  transcription_confidence FLOAT NULL,       -- 0.0-1.0 (< 0.5 triggers fallback)
  retracted_at TIMESTAMPTZ NULL,
  retracted_by_user_id UUID NULL,
  retracted_reason TEXT NULL,
  retract_succeeded BOOLEAN NULL,            -- TRUE if channel API retract worked, FALSE if fallback "marcar erróneo"
  handler_mode VARCHAR(16) NOT NULL,         -- snapshot of conversation.handler_mode at send time
  cache_hit_rate FLOAT NULL,                 -- for ai messages: prompt cache hit rate
  llm_cost_usd NUMERIC(10, 6) NULL,          -- for ai messages
  sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  delivered_at TIMESTAMPTZ NULL,
  read_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS ix_vitalia_messages_conversation_sent_at
  ON vitalia_messages (tenant_id, clinic_id, conversation_id, sent_at DESC)
  WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_messages_external_id
  ON vitalia_messages (channel, external_message_id)
  WHERE external_message_id IS NOT NULL AND deleted_at IS NULL;
```

### 2.3 `vitalia_activity_events` (NEW)

Lightweight projection of `copilot_trace_event` filtered + decorated per conversation. NOT a mirror — it's a curated view for ActivityStream UI (≤8 events, ≤5min window).

```sql
CREATE TABLE IF NOT EXISTS vitalia_activity_events (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  conversation_id UUID NOT NULL REFERENCES vitalia_conversations(id),
  source_trace_event_id UUID NULL,           -- FK to copilot_trace_event if available
  event_kind VARCHAR(64) NOT NULL,           -- consulto_precio | verifico_agenda | propuso_turno | clasifico_interes | derivo_doctor | etc.
  description_es TEXT NOT NULL,              -- "consultó precio de Blanqueamiento Premium ($24.000)"
  agent_id VARCHAR(32) NOT NULL DEFAULT 'adrian',  -- adrian | valeria | lucas | system
  occurred_at TIMESTAMPTZ NOT NULL,
  payload_sanitized JSONB NOT NULL DEFAULT '{}',  -- PII-sanitized payload for debugging (DON'T render in UI directly)
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_vitalia_activity_events_conv_occurred
  ON vitalia_activity_events (tenant_id, clinic_id, conversation_id, occurred_at DESC);
```

> **Note:** alternative is to query `copilot_trace_event` engine table directly without this projection. Decision Slice 1: keep this projection for read isolation + UI-tuned shape. If projection drift detected post-Slice 1 → reconsider join engine table direct.

### 2.4 `vitalia_action_receipts` (NEW)

```sql
CREATE TABLE IF NOT EXISTS vitalia_action_receipts (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  clinic_id UUID NOT NULL,
  message_id UUID NOT NULL REFERENCES vitalia_messages(id),
  conversation_id UUID NOT NULL REFERENCES vitalia_conversations(id),
  expires_at TIMESTAMPTZ NOT NULL,           -- 5min from message sent_at
  retracted_at TIMESTAMPTZ NULL,
  retract_succeeded BOOLEAN NULL,
  retract_reason TEXT NULL,                  -- 'user_undo' | 'expired' | 'patient_replied'
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_vitalia_action_receipts_expires
  ON vitalia_action_receipts (tenant_id, clinic_id, expires_at)
  WHERE retracted_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_action_receipts_message
  ON vitalia_action_receipts (message_id);
```

### 2.5 Column additions to existing tables

**vitalia_audit_log (existing):** new `resource_type` enum values:
- `inbox.conversation`
- `inbox.message`
- `inbox.action_receipt`
- `inbox.cross_tenant_access_denied`
- `inbox.proactive_outbound_sent`

No DDL change — JSONB payload schema documented in `inbox/application/services/audit_log_helper.py`.

## 3. Domain entities

### 3.1 Conversation

```python
# vitalia/backend/src/modules/vitalia/crm/domain/conversation.py
"""Conversation domain entity — PHI dual-filter (tenant_id + clinic_id)."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID

ChannelType = Literal["whatsapp", "instagram", "facebook_messenger", "web", "walk_in", "phone"]
ConversationStatus = Literal["active", "paused", "closed", "archived"]
HandlerMode = Literal["ai", "human"]
StageDecision = Literal["interesado", "considerando", "listo", "decidio_no"] | None


@dataclass
class Conversation:
    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    lead_id: UUID
    patient_id: UUID | None
    channel: ChannelType
    channel_external_id: str | None
    status: ConversationStatus
    handler_mode: HandlerMode
    proposal_required: bool
    pause_until: datetime | None
    help_needed: bool
    help_needed_reason: str | None
    unread_media_count: int
    last_message_at: datetime | None
    last_message_preview: str | None
    messages_count: int
    stage_decision: StageDecision
    linked_offer_id: UUID | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
```

### 3.2 Message

```python
# vitalia/backend/src/modules/vitalia/crm/domain/message.py
"""Message domain entity — PHI dual-filter."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

SenderType = Literal["patient", "agent_ai", "agent_human", "system"]
MediaKind = Literal["audio", "image", "video", "document", "sticker"] | None


@dataclass
class Message:
    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    conversation_id: UUID
    channel: str
    external_message_id: str | None
    sender_type: SenderType
    sender_user_id: UUID | None
    body_text: str | None
    media_kind: MediaKind
    media_url: str | None
    media_duration_s: int | None
    media_phi_flagged: bool
    transcription_text: str | None
    transcription_confidence: float | None
    retracted_at: datetime | None
    retracted_by_user_id: UUID | None
    retracted_reason: str | None
    retract_succeeded: bool | None
    handler_mode: str
    cache_hit_rate: float | None
    llm_cost_usd: float | None
    sent_at: datetime
    delivered_at: datetime | None
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
```

### 3.3 ActivityEvent

```python
# vitalia/backend/src/modules/vitalia/crm/domain/activity_event.py
"""ActivityEvent — UI-tuned projection of copilot_trace_event."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID

AgentId = Literal["adrian", "valeria", "lucas", "system"]


@dataclass
class ActivityEvent:
    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    conversation_id: UUID
    source_trace_event_id: UUID | None
    event_kind: str
    description_es: str
    agent_id: AgentId
    occurred_at: datetime
    payload_sanitized: dict
    created_at: datetime
```

### 3.4 ActionReceipt

```python
# vitalia/backend/src/modules/vitalia/crm/domain/action_receipt.py
"""ActionReceipt — 5min undo window for ai messages."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

RetractReason = Literal["user_undo", "expired", "patient_replied"] | None


@dataclass
class ActionReceipt:
    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    message_id: UUID
    conversation_id: UUID
    expires_at: datetime
    retracted_at: datetime | None
    retract_succeeded: bool | None
    retract_reason: RetractReason
    created_at: datetime
    updated_at: datetime
```

### 3.5 Domain events (events.py)

```python
# vitalia/backend/src/modules/vitalia/crm/domain/events.py
"""Inbox/CRM domain events (consumed via core/luana-core-events outbox bus)."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from luana_core_events.domain.event import DomainEvent  # engine base


@dataclass
class ConversationStarted(DomainEvent):
    conversation_id: UUID
    tenant_id: UUID
    clinic_id: UUID
    lead_id: UUID
    channel: str
    occurred_at: datetime

@dataclass
class MessageSent(DomainEvent):
    message_id: UUID
    conversation_id: UUID
    tenant_id: UUID
    clinic_id: UUID
    sender_type: str
    channel: str
    occurred_at: datetime

@dataclass
class MessageRetracted(DomainEvent):
    message_id: UUID
    conversation_id: UUID
    tenant_id: UUID
    clinic_id: UUID
    retracted_by_user_id: UUID
    retract_succeeded: bool
    occurred_at: datetime

@dataclass
class ModeChanged(DomainEvent):
    conversation_id: UUID
    tenant_id: UUID
    clinic_id: UUID
    from_mode: str
    to_mode: str
    proposal_required: bool
    changed_by_user_id: UUID
    occurred_at: datetime

@dataclass
class AdrianPaused(DomainEvent):
    conversation_id: UUID
    tenant_id: UUID
    clinic_id: UUID
    duration_min: int
    paused_by_user_id: UUID
    occurred_at: datetime

@dataclass
class ProactiveOutboundSent(DomainEvent):
    conversation_id: UUID
    tenant_id: UUID
    clinic_id: UUID
    template_id: str
    channel: str
    sent_by_user_id: UUID
    occurred_at: datetime
```

## 4. API routes (8 endpoints inbox + 4 endpoints crm produced by this story)

All routes under `/api/v1/vitalia/`. `FastAPI(redirect_slashes=False)` in `vitalia/backend/src/main.py` (Story 11 cement). Bearer + `X-Tenant-ID` + `X-Clinic-ID` mandatory on PHI routes.

### 4.1 Inbox-specific endpoints (`vitalia/backend/src/modules/vitalia/inbox/api/router.py`)

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| POST | `/api/v1/vitalia/inbox/conversations/{conv_id}/messages` | Bearer · all roles auth | `SendMessageRequest` | `MessageResponse` | Send message human or trigger agent reply. Idempotency-Key header. |
| POST | `/api/v1/vitalia/inbox/conversations/{conv_id}/messages/{msg_id}/revert` | Bearer · all roles auth | `RetractMessageRequest` (reason opcional) | `RetractMessageResponse` | Revert via `connections.{X}.retract_message_id`. Fallback `marcar_erroneo`. 5min window enforced. |
| POST | `/api/v1/vitalia/inbox/conversations/{conv_id}/mode` | Bearer · all roles auth | `SetModeRequest` (mode + If-Match for OCC) | `ConversationResponse` | Mode change + OCC conflict resolve. 409 on stale `updated_at`. |
| POST | `/api/v1/vitalia/inbox/conversations/{conv_id}/pause-adrian` | Bearer · all roles auth | `PauseAdrianRequest` (reason opcional) | `ConversationResponse` | 60min pause · Redis lock + DB pause_until column. |
| GET | `/api/v1/vitalia/inbox/conversations/{conv_id}/activity-stream` | Bearer · all roles auth | (query: `limit`=8, `since_minutes`=5) | `ActivityStreamResponse` | List 8 last ActivityEvent (≤5min default). |
| GET | `/api/v1/vitalia/inbox/conversations/{conv_id}/tools` | Bearer · all roles auth | — | `ToolsStateResponse` | Derive from `offer.tools_enabled` mapping. Read-only Slice 1. |
| POST | `/api/v1/vitalia/inbox/conversations/{conv_id}/transcribe-audio` | Bearer · all roles auth | `TranscribeAudioRequest` (audio_url) | `TranscribeAudioResponse` | Wraps `WhisperTranscribeService`. Timeout 30s · fallback "no se entendió". |
| POST | `/api/v1/vitalia/inbox/proactive-outbound` | Bearer · all roles auth | `ProactiveOutboundRequest` (contact_id + template_id + variables) | `ProactiveOutboundResponse` | Send HSM via WA/IG. ComplianceService gate (PHI per canal). |

### 4.2 CRM endpoints produced by this story (`vitalia/backend/src/modules/vitalia/crm/api/router.py` — extend existing)

| Method | Path | Auth | Request DTO | response_model | Description | Consumers cross-story |
|---|---|---|---|---|---|---|
| GET | `/api/v1/vitalia/crm/leads` | Bearer · all roles auth | (query: `stage,channel,status,help_needed,unread_media,period,search,limit,cursor`) | `LeadListResponse` | Paginated list with filters. | pipeline (kanban), agenda (paciente link) |
| GET | `/api/v1/vitalia/crm/leads/{lead_id}` | Bearer · all roles auth | — | `LeadResponse` | EXISTING — already shipped Story 11 scaffold. Extends with `last_conversation_id` field. | pipeline (drawer), agenda (booking detail) |
| GET | `/api/v1/vitalia/crm/conversations` | Bearer · all roles auth | (query: `status,channel,limit,cursor`) | `ConversationListResponse` | Paginated. PHI dual-filter. | pipeline (signal flag) |
| GET | `/api/v1/vitalia/crm/conversations/{conv_id}` | Bearer · all roles auth | — | `ConversationDetailResponse` (with last N messages, action receipts, tools state) | Single conversation full detail. | pipeline (drawer historial) |

> **Note:** `POST /api/v1/vitalia/crm/leads/{lead_id}/stage` (advance stage) is **NOT** produced by this story. Producer = Ola 2 `/pipeline` story (per HANDOFF § 5). Inbox can READ stage via Lead/Conversation response but doesn't mutate.

### 4.3 Request/Response DTO shapes (Pydantic v2)

```python
# vitalia/backend/src/modules/vitalia/inbox/application/dto/send_message_dto.py
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Literal


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    body_text: str | None = Field(None, max_length=4000)
    media_url: str | None = None
    media_kind: Literal["audio", "image", "video", "document"] | None = None
    media_duration_s: int | None = Field(None, ge=0, le=300)
    handler_mode_override: Literal["ai", "human"] | None = None  # for proactive composer pre-fill
    idempotency_key: str | None = Field(None, max_length=64)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    conversation_id: UUID
    sender_type: Literal["patient", "agent_ai", "agent_human", "system"]
    sender_user_id: UUID | None = None
    body_text: str | None = None
    media_kind: Literal["audio", "image", "video", "document", "sticker"] | None = None
    media_url: str | None = None
    media_duration_s: int | None = None
    transcription_text: str | None = None
    transcription_confidence: float | None = None
    retracted_at: datetime | None = None
    retract_succeeded: bool | None = None
    handler_mode: Literal["ai", "human"]
    sent_at: datetime
    action_receipt_expires_at: datetime | None = None  # for ai messages within 5min window
```

Other DTOs follow same pattern. Reference `vitalia/backend/src/modules/vitalia/crm/application/dto/lead_dto.py` (existing Story 11 cement) for style.

## 5. Repository contracts

Every repo inherits engine `CompoundScopeRepositoryBase` with `scope_field="clinic_id"`:

```python
# vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/conversation_repository.py
from __future__ import annotations
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase
from src.modules.vitalia.crm.infrastructure.persistence.models.conversation_model import ConversationModel


class ConversationRepository(CompoundScopeRepositoryBase[ConversationModel, UUID]):
    MODEL = ConversationModel

    def __init__(self, *, session: AsyncSession) -> None:
        super().__init__(session=session, scope_field="clinic_id")

    # Inherited: get_by_id(id, tenant_id, scope_id) · list_for_scope(tenant_id, scope_id, ...)
    # Custom queries below MUST apply both filters.

    async def list_for_inbox(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        channel: str | None = None,
        status: str | None = None,
        stage: str | None = None,
        help_needed: bool | None = None,
        unread_media: bool | None = None,
        period_from: 'datetime | None' = None,
        search: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> list[ConversationModel]:
        """Paginated inbox query with filters. Dual-filter mandatory."""
        ...

    async def update_handler_mode(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        new_mode: str,
        new_proposal_required: bool,
        expected_updated_at: 'datetime',  # OCC
    ) -> ConversationModel | None:
        """Update mode with optimistic concurrency. Returns None if stale (409 Conflict caller-side)."""
        ...
```

## 6. Application services

### 6.1 `InboxOrchestrator`

Top-level service composing reads across Lead, Conversation, Message, ActivityEvent. Used by `GET /api/v1/vitalia/crm/conversations/{id}` endpoint for ConversationDetailResponse.

### 6.2 `SendMessageService`

- Idempotency via `Idempotency-Key` header → `core/luana-core-idempotency` table.
- If `handler_mode='ai'` and no `handler_mode_override='human'` → enqueue Adrián turn (engine sales_agent runtime).
- If `handler_mode='human'` or `override='human'` → directly call `connections.{channel}.send_message(...)`.
- Sync write audit_log row pre-response.
- Emit `MessageSent` domain event via outbox bus.

### 6.3 `RetractMessageService`

- Read `vitalia_action_receipts.expires_at` — if past → 410 Gone.
- If patient replied (`vitalia_messages` newer message from sender_type='patient' after this message) → 409 Conflict "cannot retract message with reply".
- Call `connections.{channel}.retract_message_id(external_message_id)` with timeout 5s.
  - Success → update `vitalia_messages.retract_succeeded=true` + `retracted_at` + flip `handler_mode='human'` in conversation.
  - Failure → fallback "marcar erróneo": update `retract_succeeded=false` + audit log entry + UI toast explanation.
- Emit `MessageRetracted` event.

### 6.4 `SetModeService`

- OCC check via `If-Match: <updated_at>` header.
- Update conversation row + emit `ModeChanged` event.
- Invalidate Redis cache for conv detail.

### 6.5 `PauseAdrianService`

- 60min pause: set `pause_until = NOW() + INTERVAL '60 min'`.
- Redis SET with TTL 60min for fast read (avoid DB roundtrip on every Adrián turn pre-check).
- Auto-resume via cron `vitalia.inbox.cleanup_expired_pauses` (1min interval) OR lazy resume in Adrián entry point (engine).
- Emit `AdrianPaused` event.

### 6.6 `ProactiveOutboundService`

- 5 templates Meta-approved hardcoded Slice 1 (`vitalia/backend/src/modules/vitalia/inbox/application/services/_templates.py`):
  - `recordatorio_proxima_sesion` (UTILITY)
  - `recordatorio_control_doctor` (UTILITY)
  - `invitacion_mantenimiento` (UTILITY)
  - `re_engagement_ausencia` (MARKETING — requires patient.marketing_opt_in)
  - `nps_post_tratamiento` (MARKETING)
- ComplianceService gate: PHI per canal + marketing opt-in for MARKETING templates.
- Throttle: 1 reminder per pattern per 7d (rate limit via `core/luana-core-billing.OutboundRateLimiter`).
- If conversation NEW (proactive starts conv) → emit `ConversationStarted` event.
- Always emit `ProactiveOutboundSent` event + `MessageSent`.

### 6.7 `WhisperTranscribeService`

- `connections/whisper/adapter.py` wraps OpenAI Whisper API.
- Timeout 30s · graceful-degradation: si timeout o confidence < 0.5 → return `transcription_text=None, confidence=0` → SendMessageService trigger fallback (per SC-02).
- Cost ~$0.006/min → log to `copilot_llm_call` table (engine observability).

### 6.8 `ActivityEventService`

- Read from `vitalia_activity_events` (projection) OR fall back to direct join `copilot_trace_event` filter by `conversation_id`.
- Sanitize payload via `core/luana-core-observability.recording.sanitization.sanitize_payload(payload, compliance_level="hipaa_lite")` before returning to UI.

### 6.9 `ToolsStateService`

- Read `offer.tools_enabled` mapping (engine `core/luana-core-offer-studio.OfferTypePreset.tools_enabled`).
- Last-used timestamp from `copilot_llm_call` filter by `(conversation_id, tool_name)`.
- Read-only: no mutation Slice 1.

## 7. Migration (raw SQL idempotent)

```python
# vitalia/backend/src/modules/vitalia/persistence/migrations/024_inbox_tables.py
"""Slice 1 inbox tables: conversations, messages, activity_events, action_receipts.

Idempotent raw SQL — IF NOT EXISTS pattern. NEVER op.create_table().
"""
from alembic import op

revision = "024_inbox_tables"
down_revision = "023_..."  # latest from slice-1-infra-cross-cutting story
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_conversations (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            clinic_id UUID NOT NULL,
            lead_id UUID NOT NULL,
            patient_id UUID NULL,
            channel VARCHAR(32) NOT NULL,
            channel_external_id VARCHAR(128) NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'active',
            handler_mode VARCHAR(16) NOT NULL DEFAULT 'ai',
            proposal_required BOOLEAN NOT NULL DEFAULT FALSE,
            pause_until TIMESTAMPTZ NULL,
            help_needed BOOLEAN NOT NULL DEFAULT FALSE,
            help_needed_reason TEXT NULL,
            unread_media_count INT NOT NULL DEFAULT 0,
            last_message_at TIMESTAMPTZ NULL,
            last_message_preview TEXT NULL,
            messages_count INT NOT NULL DEFAULT 0,
            stage_decision VARCHAR(32) NULL,
            linked_offer_id UUID NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_tenant_clinic_status ON vitalia_conversations (tenant_id, clinic_id, status) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_lead ON vitalia_conversations (tenant_id, clinic_id, lead_id) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_help_needed ON vitalia_conversations (tenant_id, clinic_id, help_needed, last_message_at DESC) WHERE help_needed = TRUE AND deleted_at IS NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_unread_media ON vitalia_conversations (tenant_id, clinic_id, unread_media_count, last_message_at DESC) WHERE unread_media_count > 0 AND deleted_at IS NULL")
    # ... (similar for vitalia_messages, vitalia_activity_events, vitalia_action_receipts — see § 2 SQL DDL)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS vitalia_action_receipts")
    op.execute("DROP TABLE IF EXISTS vitalia_activity_events")
    op.execute("DROP TABLE IF EXISTS vitalia_messages")
    op.execute("DROP TABLE IF EXISTS vitalia_conversations")
```

**Prod-clone test command:**
```bash
WS=$(git rev-parse --show-toplevel)
docker exec luana-vitalia-postgres-dev psql -U postgres -d vitalia_dev -c "BEGIN; \i /tmp/024_inbox_tables.sql; ROLLBACK;"
# Or via alembic dry-run on clone DB
```

## 8. Cross-cutting concerns

- **Tenant isolation:** every query filters `tenant_id` AND `clinic_id` (dual). Lead repo single-filter (Lead non-PHI per existing scaffold).
- **Currency:** `vitalia_messages.llm_cost_usd` typed as `NUMERIC(10,6)`. NO hardcoded currency code in DTOs (messages don't carry monetary user-facing fields — cost is internal).
- **Master data:** `DateTime(timezone=True)` mandatory for `sent_at`, `last_message_at`, etc. UTC stored, displayed via tenant locale.
- **Spanish neutro:** all `description_es` on `vitalia_activity_events` + error messages in router exceptions. No voseo.
- **PII sanitization:** `ActivityEventService.get_stream(conv_id)` calls `sanitize_payload` before return. Audit log `payload_redacted` is pgcrypto-encrypted column.
- **Native-first dev:** lint/tests run `${WS}/.venv/bin/{ruff,pytest}` (NOT docker exec).
- **Idempotency on writes:** `SendMessageService` uses `Idempotency-Key` header → engine `core/luana-core-idempotency`.

## 9. Architecture fitness impact

Gates that must keep passing post this story:

- `vitalia/backend/tests/architecture/test_phi_dual_filter.py` — new Conversation + Message + ActivityEvent + ActionReceipt repos consume `CompoundScopeRepositoryBase scope_field="clinic_id"`.
- `vitalia/backend/tests/architecture/test_response_model_required.py` — all 8 new inbox routes + 2 new crm routes declare `response_model=`.
- `vitalia/backend/tests/architecture/test_migrations_idempotent.py` — 024_inbox_tables uses `IF NOT EXISTS`.
- `vitalia/backend/tests/architecture/test_no_cross_brand_imports.py` — inbox modules don't import `nicolify/` or `comunify/` or `lupulo/`.
- `vitalia/backend/tests/architecture/test_audit_log_sync_write.py` — Send + Retract + SetMode + Pause + ProactiveOutbound services write audit row pre-response.

**Allowlist shrinkage:** zero new entries — all violations fix-forward.

## 10. capability YAML + modules.md updates required (post-merge)

Per `pm-redesign-2026-05` paradigma — `/pm-vitalia` writes these at merge:

- `vitalia/docs/product/capabilities/inbox/conversational-segmented.yaml` (NEW status=live)
- `vitalia/docs/product/capabilities/inbox/multimedia-audio-image.yaml` (NEW status=live audio · stub image)
- `vitalia/docs/product/capabilities/inbox/tools-sheet-read-only.yaml` (NEW status=live)
- `vitalia/docs/product/capabilities/inbox/activity-stream-transparency.yaml` (NEW status=live)
- `vitalia/docs/product/capabilities/inbox/action-receipts-undo.yaml` (NEW status=live)
- `vitalia/docs/product/capabilities/inbox/proactive-outbound.yaml` (NEW status=live)
- `vitalia/docs/product/modules/inbox.md` (NEW SSoT funcional viva — auto-list capabilities)

## 11. Test surfaces (TDD-mandatory · RED first per layer)

- **Domain** (`vitalia/backend/tests/modules/vitalia/crm/domain/`):
  - `test_conversation.py` (dataclass invariants · enum values · soft-delete shape)
  - `test_message.py` (sender_type enum · media_kind · retraction state machine)
  - `test_activity_event.py` (description_es required · agent_id enum)
  - `test_action_receipt.py` (5min expiry computation · state machine)

- **Infrastructure** (`vitalia/backend/tests/modules/vitalia/crm/infrastructure/`):
  - `test_conversation_repository.py` (dual-filter applied in get_by_id + list_for_inbox · OCC update_handler_mode)
  - `test_message_repository.py` (dual-filter · external_message_id unique · soft-delete excludes)
  - `test_activity_event_repository.py`
  - `test_action_receipt_repository.py`

- **Application** (`vitalia/backend/tests/modules/vitalia/inbox/application/`):
  - `test_send_message_service.py` (idempotency · ai-path enqueues Adrián · human-path direct channel send · audit log row written pre-response · MessageSent event emitted)
  - `test_retract_message_service.py` (5min window · patient replied = 409 · adapter success · adapter failure fallback "marcar erróneo")
  - `test_set_mode_service.py` (OCC happy + conflict 409 · ModeChanged event)
  - `test_pause_adrian_service.py` (60min Redis lock + DB column · auto-resume)
  - `test_proactive_outbound_service.py` (5 templates · ComplianceService gate · marketing_opt_in enforcement · throttle 7d)
  - `test_whisper_transcribe_service.py` (timeout 30s → fallback · confidence < 0.5 → fallback)
  - `test_activity_event_service.py` (sanitize_payload applied · projection vs direct query both paths)
  - `test_tools_state_service.py` (offer.tools_enabled read-only · last_used join)

- **API/E2E** (`vitalia/backend/tests/modules/vitalia/inbox/api/`):
  - `test_router_send_message.py` (Bearer + X-Tenant-ID + X-Clinic-ID enforced · 401 · 403 RBAC marketing role · 409 OCC · 410 Gone for retract expired · 201 happy)
  - `test_router_revert.py`
  - `test_router_mode.py`
  - `test_router_pause_adrian.py`
  - `test_router_activity_stream.py`
  - `test_router_tools.py`
  - `test_router_transcribe_audio.py`
  - `test_router_proactive_outbound.py`
  - `test_router_crm_leads_list.py` (filters + pagination + cursor)
  - `test_router_crm_conversations_list.py`
  - `test_cross_tenant_denied.py` (SC-04 adversarial)

- **Integration** (`vitalia/backend/tests/integration/`):
  - `test_inbox_send_retract_audit_log.py` (full flow: send ai msg → action receipt created → revert within 5min → audit log row + event emitted)
  - `test_inbox_whisper_fallback.py` (audio IN low confidence → auto-switch handler_mode=human + help_needed=true)

## 12. References

- `01-spec-extract.md` · `02-design-ui.md` · `03-arch.md`
- `vitalia/.claude/rules/hipaa-lite.md`
- `vitalia/config/brand.yaml`
- `core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py`
- `core/luana-core-channels/src/luana_core_channels/format_for_channel.py`
- `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py`
- `core/luana-core-idempotency/src/luana_core_idempotency/`
- `vitalia/backend/src/modules/vitalia/crm/` (EXISTING — extend)
- `vitalia/backend/src/modules/vitalia/sales_agent/tools/` (EXISTING shipped)
