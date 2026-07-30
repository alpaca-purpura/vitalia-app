# vitalia-copilot-tools-impl — Backend sub-architecture

> **Consumer:** `builder-backend` (Sonnet/qwen-opencode default; Opus 4.7 for arch fitness test files only when novel pattern) + `auditor-backend` (Opus 4.7).
> **Index:** `03-arch.md` § 0-7 + `02-design-agentic.md` (RATIFIED v1.0 Chris 2026-05-17).
> **Brand surface:** `vitalia/backend/src/modules/vitalia/{copilot,sales_agent,agentic,compliance}/{domain,infrastructure,application,api}/` + persistence/migrations + schema-mirror persistence/models.
> **Engine consultation:** READ-ONLY `core/luana-core-*/`.

> **R23 cost-routing:** all tickets here `production_code: true` (services + repos + migrations + API routes) → Sonnet/qwen-opencode default. Arch fitness test files (mostly assertions over imports/strings) → Sonnet OK.

## 1. DDD Inside-Out layout (per `.claude/rules/backend-ddd.md`)

```
vitalia/backend/src/modules/vitalia/
├── copilot/                                             ← brand extension overlay (Valeria wizard)
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── onboarding_draft.py                     ← BrandStudioDraft entity (NEW)
│   │   │   └── wizard_slot.py                          ← WizardSlot value object (NEW)
│   │   ├── enums/
│   │   │   └── wizard_state.py                         ← StrEnum mode/state values
│   │   └── ports/
│   │       └── personality_service_port.py             ← Port for engine personality_service consumption
│   ├── infrastructure/
│   │   ├── repositories/
│   │   │   ├── onboarding_draft_repository.py          ← CRUD brand_studio_drafts (existing table, parent T-infra-1)
│   │   │   ├── onboarding_progress_repository.py       ← CRUD onboarding_progress (existing table)
│   │   │   └── audit_log_repository.py                 ← REUSE _shared/repositories/audit_log_repository.py
│   │   └── adapters/
│   │       ├── personality_service_adapter.py         ← Adapter calling engine `core.luana_core_brand_studio.application.personality_service`
│   │       ├── website_scraper_adapter.py             ← External scraping (timeout+fallback)
│   │       ├── document_extractor_adapter.py          ← PDF/docx parse (timeout+fallback)
│   │       └── whisper_stt_adapter.py                 ← OpenAI Whisper API (timeout+fallback)
│   ├── application/
│   │   └── services/
│   │       ├── onboarding_draft_service.py            ← OnboardingDraftService.persist_slot / load_draft / mark_complete
│   │       ├── extract_tenant_context_service.py     ← orchestrates 3 adapters (scraper/doc/whisper) + sanitize_payload
│   │       ├── simulate_personality_service.py      ← wraps engine personality_service.simulate + throttle 5/min/tenant + cache result
│   │       └── complete_onboarding_service.py       ← engine compile_full + BrandStudio commit + tenant.is_onboarded=true + seed default templates + audit_log
│   ├── api/
│   │   ├── dtos/
│   │   │   ├── extract_dto.py                        ← ExtractInput / ExtractResponse / WizardSlot
│   │   │   ├── confirm_slot_dto.py                   ← ConfirmSlotInput / ConfirmSlotResponse
│   │   │   ├── simulate_dto.py                       ← SimulateInput / SimulateResponse
│   │   │   └── complete_dto.py                       ← CompleteInput / CompleteResponse
│   │   └── routes/
│   │       ├── wizard_onboarding_routes.py           ← FastAPI routes (start/extract/confirm-slot/simulate-personality/complete + SSE stream)
│   │       └── lucas_cron_trigger_routes.py          ← internal-only POST /api/v1/vitalia/lucas/trigger (cron worker calls)
│   ├── persistence/
│   │   ├── models/
│   │   │   ├── copilot_trace_event.py                ← schema mirror engine `copilot_trace_event` (per backend-ddd schema-mirror exception)
│   │   │   ├── copilot_llm_call.py                   ← schema mirror engine `copilot_llm_call`
│   │   │   └── (existing brand_studio_drafts, onboarding_progress models per parent T-infra-1)
│   │   └── migrations/                                ← (covered by NEW migrations declared below in § 9)
│   ├── workflows/                                      ← agentic sub-arch ← see 03-arch-agentic.md
│   ├── tools/                                          ← agentic sub-arch ← see 03-arch-agentic.md
│   ├── prompts/                                        ← agentic sub-arch ← see 03-arch-agentic.md
│   ├── observability/recording/                        ← agentic sub-arch ← see 03-arch-agentic.md § 6
│   └── extractors/, kb/                                ← (parent Story 11 placeholders, NOT touched this story)
│
├── sales_agent/                                         ← brand extension overlay (Adrián closer)
│   ├── domain/
│   │   ├── entities/
│   │   │   └── lead_screening_event.py                ← NEW entity (mapped to lead_screening_events table)
│   │   └── enums/
│   │       └── screening_outcome.py                   ← StrEnum: ok_proceed / derivar_doctor / derivar_emergencia / awaiting_response
│   ├── infrastructure/
│   │   ├── repositories/
│   │   │   └── lead_screening_event_repository.py    ← tenant+clinic dual filter CRUD
│   │   └── adapters/
│   │       ├── mercadopago_adapter.py                 ← create_preference + webhook signature validate
│   │       └── whatsapp_business_adapter.py          ← send_template_message + retract (Slice 2)
│   ├── application/
│   │   └── services/
│   │       ├── screening_questions_service.py        ← LLM call (single nano) per vertical YAML + persist event
│   │       ├── payment_link_service.py               ← MercadoPago preference + WhatsApp send + DB write payment_events
│   │       └── reschedule_appointment_service.py    ← AppointmentService update + emit appointment_rescheduled event + operator notification
│   ├── api/
│   │   └── (no new routes — Adrián consumes engine sales_agent routes via brand extension overlay)
│   ├── persistence/
│   │   └── models/
│   │       ├── sales_agent_trace_event.py            ← schema mirror engine
│   │       ├── sales_agent_llm_call.py               ← schema mirror engine
│   │       └── lead_screening_event.py               ← NEW table (declared § 9)
│   ├── workflows/                                     ← agentic sub-arch
│   ├── tools/, personas/, prompts/, goldens/, observability/recording/ ← agentic sub-arch
│
├── agentic/                                             ← Lucas growth setter (cron-only Slice 1)
│   ├── lucas/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   ├── stage_recommendation.py           ← NEW entity (mapped to existing lucas_recommendations parent table)
│   │   │   │   ├── attribution_matrix_snapshot.py   ← NEW entity
│   │   │   │   └── referrals_leaderboard_snapshot.py ← NEW entity
│   │   │   └── enums/
│   │   │       └── stage.py                          ← StrEnum: attraction / qualification / reservation / adoption / expansion
│   │   ├── infrastructure/
│   │   │   ├── repositories/
│   │   │   │   ├── stage_recommendation_repository.py
│   │   │   │   ├── attribution_matrix_snapshot_repository.py
│   │   │   │   └── referrals_leaderboard_snapshot_repository.py
│   │   │   └── adapters/
│   │   │       └── analytics_engine_query_adapter.py ← Port to `core.luana_core_analytics_engine` ChannelRegistry + STAGE_CHANNEL_MAP reads (no DB ETL writes)
│   │   ├── application/
│   │   │   └── services/
│   │   │       ├── lucas_stage_recommendation_service.py  ← orchestrates LLM call Kimi per stage
│   │   │       ├── lucas_attribution_service.py          ← pure DB analytics (no LLM)
│   │   │       └── lucas_referrals_service.py            ← pure DB analytics (no LLM)
│   │   ├── workflows/                                ← agentic sub-arch
│   │   ├── tools/                                    ← agentic sub-arch
│   │   ├── personas/                                 ← agentic sub-arch
│   │   └── persistence/
│   │       └── models/                                ← see § 9 NEW tables
│   └── screening/
│       └── screening_questions_by_vertical.yaml      ← SSoT NEW (4 verticals × 2-4 questions)
│
└── compliance/                                          ← Medical guardrails + channel guards
    ├── guardrails/                                     ← (existing scaffold placeholders → REAL impl in this story)
    │   ├── medical_safety_no_diagnosis.py
    │   ├── medical_safety_no_prescription.py
    │   ├── medical_disclaimer_required.py
    │   └── prompt_injection_block_reuse.py
    └── application/services/
        └── channel_guard_service.py                   ← wraps engine ComplianceService.validate_outbound_message
```

## 2. Domain Entities

### 2.1 `OnboardingDraft` (Valeria wizard)

```python
# vitalia/backend/src/modules/vitalia/copilot/domain/entities/onboarding_draft.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Optional

@dataclass
class OnboardingDraft:
    id: UUID
    tenant_id: UUID                                # cardinal
    user_id: UUID                                  # operator initiating wizard
    clinic_id: Optional[UUID]                      # may be None — wizard creates it on complete
    mode: str                                      # "libre" | "guiado"
    slots_required: dict                           # {"tenant.name": WizardSlot, "tenant.vertical": ..., "tenant.location": ...}
    slots_optional: dict                           # {"brand.tone_default": ..., "offer[0]": ...}
    bonus_extracted: dict                          # team, differentiators, testimonials, offer_catalog_full
    consent_voice_activation: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]                 # soft delete (mandatory)
    completed_at: Optional[datetime]               # set when complete_onboarding fires
```

### 2.2 `WizardSlot` (value object)

```python
@dataclass(frozen=True)
class WizardSlot:
    slot_id: str
    value: str | dict | None
    confidence: float                              # 0.0-1.0
    confirmed_at: Optional[datetime]
    source: str                                    # "extracted" | "user_text" | "user_correction"
```

### 2.3 `LeadScreeningEvent` (Adrián)

```python
# vitalia/backend/src/modules/vitalia/sales_agent/domain/entities/lead_screening_event.py
@dataclass
class LeadScreeningEvent:
    id: UUID
    tenant_id: UUID                                # cardinal
    clinic_id: UUID                                # cardinal (PHI dual filter)
    lead_id: UUID
    vertical: str                                  # "dental" | "estetica" | "psicologia" | "fertilidad" | "otro"
    questions_asked: list[str]                     # JSONB
    response_text: Optional[str]                   # sanitized via sanitize_payload(compliance_level="hipaa_lite")
    outcome: str                                   # "ok_proceed" | "derivar_doctor" | "derivar_emergencia" | "awaiting_response"
    reasoning: Optional[str]                       # LLM rationale (sanitized)
    evaluated_at: Optional[datetime]
    created_at: datetime
    deleted_at: Optional[datetime]
```

### 2.4 `StageRecommendation` (Lucas)

```python
# vitalia/backend/src/modules/vitalia/agentic/lucas/domain/entities/stage_recommendation.py
@dataclass
class StageRecommendation:
    id: UUID
    tenant_id: UUID                                # cardinal
    clinic_id: UUID                                # cardinal (operator-scoped)
    stage: str                                     # StageEnum
    period: str                                    # "YYYY-MM"
    recommendation_text: str                       # structured per RecommendationDTO schema
    confidence: float                              # 0.0-1.0
    supporting_data: dict                          # JSONB with metric refs + currency for monetary
    status: str                                    # "active" | "skipped_timeout" | "skipped_budget" | "applied" | "rejected"
    created_at: datetime
    deleted_at: Optional[datetime]
```

### 2.5 `AttributionMatrixSnapshot` + `ReferralsLeaderboardSnapshot` (Lucas)

Similar shape: tenant_id + clinic_id + period + JSONB body + created_at + deleted_at.

## 3. SQLAlchemy 2.0 Models (mapped_column syntax, no SA 1.x)

Schema-mirror persistence per `.claude/rules/backend-ddd.md` schema-mirror exception. Example (others identical pattern):

```python
# vitalia/backend/src/modules/vitalia/sales_agent/persistence/models/lead_screening_event.py
from datetime import datetime
from uuid import UUID
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from vitalia.backend.src.shared.infrastructure.database import Base

class LeadScreeningEventModel(Base):
    __tablename__ = "lead_screening_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    lead_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False)
    questions_asked: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    response_text: Mapped[str | None] = mapped_column(String, nullable=True)  # sanitized pre-persist
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    reasoning: Mapped[str | None] = mapped_column(String, nullable=True)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_lead_screening_events_tenant_clinic_lead", "tenant_id", "clinic_id", "lead_id"),
        Index("ix_lead_screening_events_tenant_vertical_outcome", "tenant_id", "vertical", "outcome"),
    )
```

Tables this story declares (all with `tenant_id` + `clinic_id` cardinal + `deleted_at` + `created_at`):

| Table | Module | Purpose |
|---|---|---|
| `lead_screening_events` | sales_agent | Screening questions events per lead per vertical |
| `attribution_matrix_snapshots` | agentic/lucas | Daily attribution matrix per tenant+clinic+period |
| `referrals_leaderboard_snapshots` | agentic/lucas | Daily referrals top-5 per tenant+clinic+period |
| `vitalia_wizard_onboarding_checkpoints` | copilot | AsyncPostgresSaver-managed (declare via `await checkpointer.setup()`) — table_prefix |
| `vitalia_lucas_analysis_checkpoints` | agentic/lucas | AsyncPostgresSaver-managed — table_prefix |

Tables CONSUMED (declared in parent T-infra-1 migrations 002-016): `brand_studio_drafts`, `onboarding_progress`, `lucas_recommendations`, `payment_events`, `audit_log_vitalia`, `appointments`, etc.

## 4. Pydantic v2 DTOs (ConfigDict, no inner class Config)

### 4.1 Valeria wizard DTOs

```python
# vitalia/backend/src/modules/vitalia/copilot/api/dtos/extract_dto.py
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID

class WizardSlotDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    slot_id: str
    value: str | dict | None
    confidence: float = Field(ge=0.0, le=1.0)
    source: str

class ExtractInput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    urls: list[str] = Field(default_factory=list, max_length=5)
    doc_uploads: list[str] = Field(default_factory=list, max_length=3)  # signed URLs
    audio_uploads: list[str] = Field(default_factory=list, max_length=2)
    tenant_id: UUID
    user_id: UUID

class ExtractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    slots: list[WizardSlotDTO]
    pii_detected: bool = False
    extraction_duration_ms: int
```

Equivalent DTOs for `ConfirmSlotInput/Response`, `SimulateInput/Response`, `CompleteInput/Response` per design § 1.3 tools sequence + 03-arch-agentic.md § 4.1.

### 4.2 Adrián tools DTOs

```python
# vitalia/backend/src/modules/vitalia/sales_agent/application/dtos/screening_dto.py
class ScreeningInput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    lead_id: UUID
    vertical: Literal["dental", "estetica", "psicologia", "fertilidad", "otro"]
    tenant_id: UUID
    clinic_id: UUID
    lead_response: str | None = None  # if provided, evaluate=True

class ScreeningOutcomeDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    questions: list[str]
    outcome: Literal["ok_proceed", "derivar_doctor", "derivar_emergencia", "awaiting_response"]
    reasoning: str | None = None
```

Similar for `SendPaymentLinkInput/Response`, `RescheduleInput/Response`.

### 4.3 Lucas tools DTOs

```python
# vitalia/backend/src/modules/vitalia/agentic/lucas/application/dtos/recommendation_dto.py
class ComputeStageRecommendationInput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    stage: Literal["attraction", "qualification", "reservation", "adoption", "expansion"]
    tenant_id: UUID
    clinic_id: UUID
    period: str = Field(pattern=r"^\d{4}-\d{2}$")  # YYYY-MM

class RecommendationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    stage: str
    recommendation_text: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_data: dict
    currency: str | None = None  # ISO-4217 for monetary supporting figures
    status: Literal["active", "skipped_timeout", "skipped_budget", "applied", "rejected"]
```

## 5. API Routes (FastAPI thin, response_model= mandatory)

### 5.1 Wizard onboarding API (under `/api/v1/vitalia/onboarding/`)

`FastAPI(redirect_slashes=False)` enforced at app level (parent T-arch-1 cement).

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| POST | `/api/v1/vitalia/onboarding/start` | Bearer + X-Tenant-ID | `StartOnboardingInput` (mode + user_id) | `StartOnboardingResponse` (draft_id + greet_message) | Initialize wizard session, persist `onboarding_progress` row |
| POST | `/api/v1/vitalia/onboarding/extract` | Bearer + X-Tenant-ID | `ExtractInput` | `ExtractResponse` | Fire `extract_tenant_context` tool via wizard graph (subagent) |
| POST | `/api/v1/vitalia/onboarding/confirm-slot` | Bearer + X-Tenant-ID | `ConfirmSlotInput` | `ConfirmSlotResponse` | Persist confirmed slot to `brand_studio_drafts` |
| POST | `/api/v1/vitalia/onboarding/simulate-personality` | Bearer + X-Tenant-ID | `SimulateInput` | `SimulateResponse` | Wraps engine `personality_service.simulate` + throttle 5/min/tenant + cache |
| POST | `/api/v1/vitalia/onboarding/complete` | Bearer + X-Tenant-ID | `CompleteInput` | `CompleteResponse` | engine `compile_full` + BrandStudio commit + tenant.is_onboarded=true + seed templates + audit_log row sync write |
| GET | `/api/v1/vitalia/onboarding/stream/{draft_id}` | Bearer + X-Tenant-ID | (path param) | (SSE EventStream — no response_model since streaming) | SSE v2 protocol stream: `status`, `message_start`, `block_*`, `tool_*`, `ui_action`, `message_end`, `done`/`error` |
| GET | `/api/v1/vitalia/onboarding/progress/{draft_id}` | Bearer + X-Tenant-ID | (path param) | `OnboardingProgressDTO` | Resume support — return saved progress for re-entry after browser close |

### 5.2 Lucas cron trigger (internal-only)

| Method | Path | Auth | Request DTO | response_model | Description |
|---|---|---|---|---|---|
| POST | `/api/v1/vitalia/lucas/trigger` | Internal cron worker token (env `LUCAS_CRON_SECRET`) — X-Tenant-ID still required for tenant scope | `LucasTriggerInput` (tenant_id + clinic_id + period optional) | `LucasTriggerResponse` (job_id + scheduled_at) | Internal endpoint invoked by APScheduler cron daily 06:00 LOCAL tenant TZ. Spawns `lucas_daily_analysis_graph` LangGraph execution. |

### 5.3 Screening internal (called by Adrián specialist via tool, NO direct external route)

No external API — `screening_questions` tool invokes `ScreeningQuestionsService.run()` directly from Adrián's tool dispatcher (engine sales_agent LangGraph).

## 6. TypeScript Types (Frontend consumes via sub-stories — listed for cross-reference only)

Generated mirror lives in `vitalia/frontend/src/features/{onboarding-wizard,pipeline,marketing}/types/`. Architect publishes types-only TS file inside this story's deliverables? **NO** — types live in sub-stories per their own scope. This story only commits to BE Pydantic DTOs. Cross-reference here for FE downstream:

```typescript
// vitalia/frontend/src/features/onboarding-wizard/types/wizard.ts
// (FE sub-story vitalia-slice-1-onboarding-wizard owns this file)
export interface WizardSlotDto {
  slotId: string;
  value: string | Record<string, unknown> | null;
  confidence: number;
  source: 'extracted' | 'user_text' | 'user_correction';
}

export interface ExtractResponse {
  slots: WizardSlotDto[];
  piiDetected: boolean;
  extractionDurationMs: number;
}
// camelCase mirror, ISO 8601 datetimes as string, optional fields explicit
```

## 7. Repository Interfaces (async, tenant + clinic dual filter cardinal)

```python
# vitalia/backend/src/modules/vitalia/sales_agent/domain/ports/lead_screening_event_repository_port.py
from abc import ABC, abstractmethod
from uuid import UUID
from vitalia.backend.src.modules.vitalia.sales_agent.domain.entities.lead_screening_event import LeadScreeningEvent

class LeadScreeningEventRepositoryPort(ABC):
    @abstractmethod
    async def create(self, event: LeadScreeningEvent, *, tenant_id: UUID, clinic_id: UUID) -> LeadScreeningEvent: ...

    @abstractmethod
    async def get_by_id(self, event_id: UUID, *, tenant_id: UUID, clinic_id: UUID) -> LeadScreeningEvent | None: ...

    @abstractmethod
    async def list_by_lead(self, lead_id: UUID, *, tenant_id: UUID, clinic_id: UUID, limit: int = 10) -> list[LeadScreeningEvent]: ...
```

All methods include `tenant_id` + `clinic_id` (PHI) REQUIRED params. Query body: `.where(Model.tenant_id == tenant_id, Model.clinic_id == clinic_id)` — never one without the other.

## 8. Application Services (transaction boundaries + event emissions + idempotency)

### 8.1 `OnboardingDraftService` (Valeria wizard)

```python
# vitalia/backend/src/modules/vitalia/copilot/application/services/onboarding_draft_service.py
class OnboardingDraftService:
    async def persist_slot(self, draft_id: UUID, slot_id: str, value: dict, *, tenant_id: UUID, user_id: UUID) -> ConfirmSlotResponse:
        async with self.uow.begin():
            draft = await self.draft_repo.get_by_id(draft_id, tenant_id=tenant_id)
            draft.update_slot(slot_id, value)
            await self.draft_repo.save(draft, tenant_id=tenant_id)
            await self.audit_log_repo.write_sync(
                tenant_id=tenant_id, user_id=user_id, action="wizard.confirm_slot",
                resource_type="brand_studio_draft", resource_id=draft_id,
                payload_redacted=sanitize_payload({"slot_id": slot_id, "value": value}, compliance_level="hipaa_lite"),
            )
        return ConfirmSlotResponse(persisted=True, draft_id=draft_id)
```

Transactional with audit_log SYNC write per `hipaa-lite.md`.

### 8.2 `CompleteOnboardingService`

```python
async def complete(self, draft_id: UUID, *, tenant_id: UUID, user_id: UUID) -> CompleteResponse:
    async with self.uow.begin():
        draft = await self.draft_repo.get_by_id(draft_id, tenant_id=tenant_id)
        # 1. Compile full personality profile via engine
        profile = await self.personality_service_adapter.compile_full(
            tenant_id=tenant_id,
            slots_confirmed=draft.all_confirmed_slots(),
        )
        # 2. Commit BrandStudio aggregate via engine port
        await self.brand_studio_port.commit_brand(tenant_id=tenant_id, profile=profile, slots=draft.all_confirmed_slots())
        # 3. Tenant activation
        await self.tenant_port.mark_onboarded(tenant_id=tenant_id)
        # 4. Seed default WhatsApp templates per vitalia/config/brand.yaml
        await self.template_seed_service.seed_defaults(tenant_id=tenant_id, vertical=draft.slots_required["tenant.vertical"].value)
        # 5. Audit log sync
        await self.audit_log_repo.write_sync(
            tenant_id=tenant_id, user_id=user_id, action="wizard.complete_onboarding",
            resource_type="tenant", resource_id=tenant_id,
            payload_redacted=sanitize_payload({"draft_id": str(draft_id)}, compliance_level="hipaa_lite"),
        )
        # 6. Emit domain event (outbox)
        await self.event_bus.publish(TenantOnboardedEvent(tenant_id=tenant_id, profile_id=profile.id))
    return CompleteResponse(tenant_activated=True, redirect_url="/inbox")
```

Idempotency: `complete_onboarding` re-call returns same `CompleteResponse` (check `tenant.is_onboarded` already True → 200 OK no-op).

### 8.3 `SimulatePersonalityService` (throttle + cache)

```python
async def simulate(self, profile_partial: dict, scenario: str, *, tenant_id: UUID) -> SimulateResponse:
    cache_key = f"vitalia:simulate:{tenant_id}:{hashlib.sha256(json.dumps(profile_partial, sort_keys=True).encode()).hexdigest()}:{scenario}"
    if cached := await self.cache.get(cache_key):
        return SimulateResponse(**cached, cache_hit=True)
    # Throttle: 5/min/tenant via Redis sliding window
    allowed = await self.rate_limiter.check(key=f"vitalia:simulate:{tenant_id}", limit=5, window_seconds=60)
    if not allowed:
        raise ThrottleExceededError("simulate_personality")
    sample = await self.personality_service_adapter.simulate(profile_partial=profile_partial, scenario=scenario, tenant_id=tenant_id)
    await self.cache.set(cache_key, sample.model_dump(), ttl=600)  # 10min cache
    return SimulateResponse(sample_text=sample.text, generated_at=utc_now(), cache_hit=False)
```

### 8.4 `ScreeningQuestionsService` (Adrián)

```python
async def run(self, *, lead_id: UUID, vertical: str, tenant_id: UUID, clinic_id: UUID, lead_response: str | None = None) -> ScreeningOutcomeDTO:
    # Load vertical questions from SSoT YAML
    questions = load_screening_yaml(vertical)  # vitalia/backend/src/modules/vitalia/agentic/screening/screening_questions_by_vertical.yaml
    if lead_response is None:
        # First call — emit questions, persist awaiting_response event
        event = LeadScreeningEvent(
            id=uuid4(), tenant_id=tenant_id, clinic_id=clinic_id, lead_id=lead_id,
            vertical=vertical, questions_asked=questions, response_text=None,
            outcome="awaiting_response", reasoning=None, evaluated_at=None,
            created_at=utc_now(), deleted_at=None,
        )
        await self.screening_repo.create(event, tenant_id=tenant_id, clinic_id=clinic_id)
        await self.audit_log_repo.write_sync(...)
        return ScreeningOutcomeDTO(questions=questions, outcome="awaiting_response")
    # Second call — evaluate response via LLM nano
    sanitized = sanitize_payload({"response": lead_response}, compliance_level="hipaa_lite")
    eval_result = await self.llm_service.evaluate_screening(
        vertical=vertical, questions=questions, response=sanitized["response"],
        tenant_id=tenant_id,  # for cost recording + cache slot 5
    )
    # eval_result.outcome ∈ {ok_proceed, derivar_doctor, derivar_emergencia}
    # Update existing event with outcome + reasoning
    event = await self.screening_repo.get_latest_awaiting(lead_id=lead_id, tenant_id=tenant_id, clinic_id=clinic_id)
    event.response_text = sanitized["response"]
    event.outcome = eval_result.outcome
    event.reasoning = eval_result.reasoning
    event.evaluated_at = utc_now()
    await self.screening_repo.save(event, tenant_id=tenant_id, clinic_id=clinic_id)
    await self.audit_log_repo.write_sync(...)
    return ScreeningOutcomeDTO(questions=questions, outcome=eval_result.outcome, reasoning=eval_result.reasoning)
```

### 8.5 `PaymentLinkService` (Adrián)

Wraps `MercadoPagoAdapter.create_preference` + `WhatsAppBusinessAdapter.send_template_message`. Idempotency key: `(appointment_id, deposit_percent)` partial unique index in `payment_events` table.

Channel guard pre-check: BEFORE sending message, call `ChannelGuardService.validate(message, channel=whatsapp_business_tier=tier)` → raises `BlockedChannelError` if PHI on non-encrypted channel. Adrián catches and replies derive-portal alternative.

### 8.6 `LucasStageRecommendationService` (cron-invoked)

Orchestrates LLM call (Kimi reasoning) per stage. Reads analytics from engine `core.luana_core_analytics_engine` via `analytics_engine_query_adapter` (no direct DB queries to analytics tables — consume via ChannelRegistry + StageOverviewService).

Cost guard: BudgetGuard.check pre-LLM with `agent_kind="copilot"` (Lucas not sales_agent — uses Others pool). If exceeded → status `skipped_budget`.

LLM call: model `kimi-k2.6` per `LLM_ROLE_BY_SITE` engine SSoT (lucas reasoning role).

### 8.7 `LucasAttributionService` + `LucasReferralsService`

Pure DB analytics. Consume `core.luana_core_analytics_engine` ChannelRegistry + STAGE_CHANNEL_MAP. No LLM. No mirror of `_GROUP_MAP` (cardinal per `analytics-metrics.md`).

## 9. Migration Notes (idempotent raw SQL, IF NOT EXISTS)

This story adds migrations **017-021** (continuing from parent T-infra-1 series 002-016):

```python
# vitalia/backend/src/modules/vitalia/persistence/migrations/017_lead_screening_events.py
def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS lead_screening_events (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            clinic_id UUID NOT NULL,
            lead_id UUID NOT NULL,
            vertical VARCHAR(32) NOT NULL,
            questions_asked JSONB NOT NULL DEFAULT '[]'::jsonb,
            response_text TEXT,
            outcome VARCHAR(32) NOT NULL,
            reasoning TEXT,
            evaluated_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_lead_screening_events_tenant_clinic_lead ON lead_screening_events (tenant_id, clinic_id, lead_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_lead_screening_events_tenant_vertical_outcome ON lead_screening_events (tenant_id, vertical, outcome)")
```

Migrations:

| # | Path | Tables / Columns |
|---|---|---|
| 017 | `..._lead_screening_events.py` | `lead_screening_events` |
| 018 | `..._attribution_matrix_snapshots.py` | `attribution_matrix_snapshots` (tenant_id, clinic_id, period VARCHAR(7), origin_breakdown JSONB, created_at, deleted_at) |
| 019 | `..._referrals_leaderboard_snapshots.py` | `referrals_leaderboard_snapshots` (tenant_id, clinic_id, period, top_referrers JSONB, created_at, deleted_at) |
| 020 | `..._langgraph_checkpoint_tables.py` | wrapper calling `AsyncPostgresSaver.setup()` with prefixes `vitalia_wizard_onboarding_` + `vitalia_lucas_analysis_` |
| 021 | `..._screening_outcome_enum_check.py` | CHECK constraint on `lead_screening_events.outcome` IN ('ok_proceed','derivar_doctor','derivar_emergencia','awaiting_response') |

All migrations IF NOT EXISTS. Enum stored as VARCHAR (NEVER `sa.Enum(create_type=True)` broken SA 2.0.27 per `.claude/rules/backend-migrations.md`).

Migration #020 special: AsyncPostgresSaver library manages its own DDL; idempotency comes from `CREATE TABLE IF NOT EXISTS` baked into library. Wrap call in `try/except` for prod safety.

Pre-prod clone test command per § 4 of consolidated `03-arch.md`.

## 10. File Structure (BE side — NEW vs MODIFIED)

```
vitalia/backend/src/modules/vitalia/
├── copilot/
│   ├── domain/entities/onboarding_draft.py                        ← NEW
│   ├── domain/entities/wizard_slot.py                             ← NEW
│   ├── domain/enums/wizard_state.py                               ← NEW
│   ├── domain/ports/personality_service_port.py                   ← NEW (abstract)
│   ├── infrastructure/repositories/onboarding_draft_repository.py ← NEW
│   ├── infrastructure/repositories/onboarding_progress_repository.py ← NEW
│   ├── infrastructure/adapters/personality_service_adapter.py    ← NEW
│   ├── infrastructure/adapters/website_scraper_adapter.py        ← NEW
│   ├── infrastructure/adapters/document_extractor_adapter.py     ← NEW
│   ├── infrastructure/adapters/whisper_stt_adapter.py            ← NEW
│   ├── application/services/onboarding_draft_service.py          ← NEW
│   ├── application/services/extract_tenant_context_service.py   ← NEW
│   ├── application/services/simulate_personality_service.py    ← NEW
│   ├── application/services/complete_onboarding_service.py     ← NEW
│   ├── api/dtos/{extract,confirm_slot,simulate,complete}_dto.py  ← NEW
│   ├── api/routes/wizard_onboarding_routes.py                    ← NEW
│   ├── api/routes/lucas_cron_trigger_routes.py                   ← NEW
│   ├── persistence/models/copilot_trace_event.py                 ← NEW (schema mirror exception per backend-ddd)
│   ├── persistence/models/copilot_llm_call.py                    ← NEW (schema mirror)
│   └── observability/recording/callback_handler.py               ← NEW (subclass — see agentic sub-arch § 6)
├── sales_agent/
│   ├── domain/entities/lead_screening_event.py                   ← NEW
│   ├── domain/enums/screening_outcome.py                         ← NEW
│   ├── infrastructure/repositories/lead_screening_event_repository.py ← NEW
│   ├── infrastructure/adapters/mercadopago_adapter.py            ← NEW
│   ├── infrastructure/adapters/whatsapp_business_adapter.py      ← NEW
│   ├── application/services/screening_questions_service.py      ← NEW
│   ├── application/services/payment_link_service.py             ← NEW
│   ├── application/services/reschedule_appointment_service.py   ← NEW
│   ├── persistence/models/sales_agent_trace_event.py             ← NEW (schema mirror)
│   ├── persistence/models/sales_agent_llm_call.py                ← NEW (schema mirror)
│   ├── persistence/models/lead_screening_event.py                ← NEW
│   └── observability/recording/callback_handler.py               ← NEW (subclass)
├── agentic/
│   ├── lucas/
│   │   ├── domain/entities/{stage_recommendation,attribution_matrix_snapshot,referrals_leaderboard_snapshot}.py ← NEW
│   │   ├── domain/enums/stage.py                                  ← NEW
│   │   ├── infrastructure/repositories/*.py                       ← NEW (3 repos)
│   │   ├── infrastructure/adapters/analytics_engine_query_adapter.py ← NEW
│   │   ├── application/services/*.py                              ← NEW (3 services)
│   │   └── persistence/models/*.py                                ← NEW (3 models)
│   └── screening/
│       └── screening_questions_by_vertical.yaml                   ← NEW (data file)
├── compliance/
│   └── guardrails/{medical_safety_no_diagnosis,medical_safety_no_prescription,medical_disclaimer_required,prompt_injection_block_reuse}.py ← MODIFIED (placeholders → real impl)
├── extensions.py                                                  ← MODIFIED (existing register_all → wire real tool callables + real guardrail callables for EP-13)
└── persistence/migrations/{017,018,019,020,021}_*.py             ← NEW (5 migrations)
```

## 11. Cross-Cutting Concerns (BE side) — see consolidated `03-arch.md § 3`

## 12. Architecture Fitness Impact

Existing gates (must keep passing): see `03-arch.md § 0.6`.

New gates added by this story:

- `vitalia/backend/tests/architecture/test_no_observability_mirror_copilot.py` — asserts `VitaliaCopilotCallbackHandler` subclasses `luana_core_observability.recording.base_callback_handler.BaseAgentCallbackHandler` AND does not redefine `_persist_llm_call_row`/`_persist_trace_event_row` signatures.
- `vitalia/backend/tests/architecture/test_no_observability_mirror_sales_agent.py` — same for sales_agent overlay.
- `vitalia/backend/tests/architecture/test_lucas_cron_tz_aware.py` — imports Lucas cron module + asserts it consumes `TenantLocationContract.timezone` (grep for `from luana_core_platform.contracts.tenant_location import`).
- `vitalia/backend/tests/architecture/test_screening_yaml_completeness.py` — loads `screening_questions_by_vertical.yaml` + asserts 4 verticals × ≥2 questions each.

Allowlist updates expected: **none new**. No legacy paths introduced.

## 13. Test Surfaces (TDD-mandatory RED first per layer) — see consolidated `03-arch.md § 5`

