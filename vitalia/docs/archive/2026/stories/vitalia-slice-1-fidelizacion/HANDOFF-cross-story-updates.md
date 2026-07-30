---
story: vitalia-slice-1-fidelizacion
type: producer-consumer-contract-updates
last_modified: 2026-05-20
last_modified_by: /architect (vitalia-slice-1-fidelizacion ready package)
purpose: |
  Cementa contratos PRODUCIDOS por esta story (consumed by sibling Olas 1+) y CONSUMIDOS
  (produced by other stories or engine pre-flight). Cross-references HANDOFF-cross-story.md
  outcome-level (which lists all 5 Ola stories en Slice 1).
---

# HANDOFF cross-story updates — vitalia-slice-1-fidelizacion

> Diff aplicado al HANDOFF outcome-level (`vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md`) tras /architect refresh 2026-05-20.
>
> Esta story = **producer** de NPS schema + re-engagement patterns API + ReEngagementTriggered + NPSScoreCollected events.
> Esta story = **consumer** de columns engine (appointments, offers, patients post Ola 0) + cron_envelope + CompoundScopeRepositoryBase (pre-flight gates).

## § 1 — Contratos PRODUCIDOS (esta story)

### 1.1 TypeScript types (shared cross-feature, consumed by /inbox Ola 1 paralela + future /marketing Ola 2)

```typescript
// vitalia/frontend/src/features/fidelizacion/types/nps.ts (CREATED Ola 1 this story)

export type NPSBand = "promoter" | "passive" | "detractor";

export interface NPSRowDTO {
  id: string;
  patientName: string;     // PHI — masked unless RequireRole guard
  score: number;           // 0-10
  band: NPSBand;
  commentShort: string | null;   // truncated 80 chars
  respondedAt: string;
  taggedInInbox: boolean;
}

export interface NPSSummaryResponse {
  averageScore: number;
  totalResponses: number;
  rows: NPSRowDTO[];
}

// vitalia/frontend/src/features/fidelizacion/types/re-engagement.ts (CREATED)

export type ReEngagementPattern = "multi_session" | "follow_up" | "maintenance" | "absence" | "nps";
export type ReEngagementOutcome = "sent" | "responded" | "rescheduled" | "declined" | "not_responsive" | "opted_out" | "failed_sending";
export type UrgencyLevel = "critical" | "alert" | "near" | "waiting" | "up_to_date";

export interface ReEngagementEvent { /* see 03-arch-fe.md § 2 full schema */ }
export interface PatternRow { /* polymorphic pattern variants */ }
```

### 1.2 Zod schemas (shared cross-feature)

```typescript
// vitalia/frontend/src/lib/zod-schemas/nps.ts (NEW — produced by this story)
import { z } from 'zod';

export const npsBandSchema = z.enum(['promoter', 'passive', 'detractor']);
export const npsRowSchema = z.object({
  id: z.string().uuid(),
  patientName: z.string(),
  score: z.number().int().min(0).max(10),
  band: npsBandSchema,
  commentShort: z.string().nullable(),
  respondedAt: z.string().datetime(),
  taggedInInbox: z.boolean(),
});
export const npsSummaryResponseSchema = z.object({
  averageScore: z.number().min(0).max(10),
  totalResponses: z.number().int().nonnegative(),
  rows: z.array(npsRowSchema),
});
export type NPSRow = z.infer<typeof npsRowSchema>;
export type NPSSummaryResponse = z.infer<typeof npsSummaryResponseSchema>;

// vitalia/frontend/src/lib/zod-schemas/re-engagement-event.ts (NEW)
export const reEngagementPatternSchema = z.enum(['multi_session', 'follow_up', 'maintenance', 'absence', 'nps']);
// ... (full schema per 03-arch-fe.md § 2)
```

### 1.3 Endpoints REST (consumed cross-story)

| Method | Path | Consumed by | Produced status |
|---|---|---|---|
| GET | `/api/v1/vitalia/fidelization/summary` | (UI only — propio /fidelización) | NEW Ola 1 fidelización |
| GET | `/api/v1/vitalia/fidelization/re-engagement/patterns` | /marketing (Ola 2 Lucas card source — future) | **Implementado** (T-7 + T-16 cement) |
| GET | `/api/v1/vitalia/fidelization/nps/summary` | **/inbox (Ola 1 paralela — tag detractor chip)** | **Implementado** (T-9 + T-16 cement) |
| POST | `/api/v1/vitalia/fidelization/nps/submit` | (paciente external token-specific link — webhook desde Adrián) | NEW Ola 1 fidelización |
| POST | `/api/v1/vitalia/fidelization/patients/{id}/send-proactive` | (UI only — propio modal + Adrián delegate) | NEW |
| POST | `/api/v1/vitalia/fidelization/patients/{id}/pause` | (UI only) | NEW |
| POST | `/api/v1/vitalia/fidelization/patients/{id}/mark-external` | (UI only) | NEW |
| POST | `/api/v1/vitalia/fidelization/patients/{id}/mark-no-continue` | (UI only) | NEW |
| POST | `/api/v1/vitalia/fidelization/patients/{id}/manual-call` | (UI only) | NEW |
| GET | `/api/v1/vitalia/fidelization/activity-stream` | (UI only — activity footer) | NEW |
| POST | `/api/v1/vitalia/crm/patients/{id}/opt-out` | (UI only — propio cascade) | NEW Ola 1 fidelización (extend CRM module) |
| PATCH | `/api/v1/vitalia/crm/patients/{id}/marketing-opt-in` | (UI only — consentimiento firma flow) | NEW |

### 1.4 Domain events (engine outbox bus — `luana_core_events.outbox.adapter_bus`)

| Event | Producer | Consumers | Status |
|---|---|---|---|
| `ReEngagementTriggered` | **fidelización (esta story)** Ola 1 | /inbox (Ola 1 paralela) — proactive_outbound conversation auto-creada con attribution metadata `Adrián abrió conv · solicitado por sistema (cron X) confirmado operador {user_id}` | **Implementado** (T-5 + T-16 cement) |
| `NPSScoreCollected` | **fidelización (esta story)** Ola 1 | /inbox (Ola 1 paralela) — tag chip render NPS badge per conversation. Future /marketing (Ola 2) — NPS distribution analytics dashboard Slice 2. | **Implementado** (T-5 + T-16 cement) |
| `PatientOptedOut` | **fidelización (esta story)** Ola 1 (vía opt_out_service) | /inbox + /pipeline + /marketing — cascade cancel pending conversations + filter futures. | **Implementado** (T-2 + T-16 cement) |
| `PatientPausedReEngagement` | **fidelización (esta story)** Ola 1 | /fidelización own UI refresh + log audit. (Slice 2: surface en /inbox CRM card toggle) | **Implementado** (T-5 + T-16 cement) |

Schemas concretos en `vitalia/backend/src/modules/vitalia/fidelizacion/domain/events.py`. Emit via `event_bus.publish(event, session=...)` with `USE_OUTBOX_PATTERN_*=True` default post 2026-04-30 (anti-default-flip cementado).

### 1.5 BE module surface visible (consumed by other Olas — Public API)

```python
# vitalia/backend/src/modules/vitalia/fidelizacion/__init__.py — exports (clean Public API)
from .application.services.re_engagement_service import ReEngagementService
from .application.services.nps_service import NPSService
from .application.services.patient_consent_service import PatientConsentService  # cross-listed in crm too
from .domain.entities.re_engagement_event import ReEngagementEvent
from .domain.entities.nps_response import NPSResponse
from .domain.events import ReEngagementTriggered, NPSScoreCollected, PatientOptedOut, PatientPausedReEngagement

__all__ = [
    "ReEngagementService", "NPSService", "PatientConsentService",
    "ReEngagementEvent", "NPSResponse",
    "ReEngagementTriggered", "NPSScoreCollected", "PatientOptedOut", "PatientPausedReEngagement",
]
```

Cross-module access via `from src.modules.vitalia.fidelizacion import ...` (within vitalia brand backend, allowed per DDD intra-brand). Cross-brand import FORBIDDEN.

### 1.6 Frontend Public API (shared cross-feature)

```typescript
// vitalia/frontend/src/features/fidelizacion/index.ts (Public API)
export { useFidelizacionSummary } from './api/use-fidelizacion-summary';
export { useReEngagementPatterns } from './api/use-re-engagement-patterns';
export { useNPSResponses } from './api/use-nps-responses';
export type { NPSBand, NPSRow, NPSSummaryResponse, ReEngagementPattern, PatternRow, ReEngagementEvent, UrgencyLevel } from './types/re-engagement';
export type { NPSRowDTO } from './types/nps';
// Components NOT exported via Public API (feature-internal) — only the cross-feature NPSTagBadge in components/shared/nps/

// vitalia/frontend/src/components/shared/nps/index.ts
export { NPSTagBadge } from './NPSTagBadge';
export type { NPSTagBadgeProps } from './NPSTagBadge';
```

`/inbox` Ola 1 imports `NPSTagBadge` from `@/components/shared/nps` (cross-feature shared root) — NOT from `@/features/fidelizacion` (feature-internal).
`/inbox` Ola 1 imports `useNPSResponses` from `@/features/fidelizacion` (Public API re-export OK for hooks shared cross-feature).

### 1.7 Tabla schema (cross-brand promotion candidates Slice 2+)

| Tabla | Status | Lift candidate Slice 2? |
|---|---|---|
| `vitalia_treatment_plans` | NEW Slice 1 brand-local | YES — si 2do brand adopta plan multi-sesión (creator economy?). Lift to `core/luana-core-platform/` |
| `vitalia_re_engagement_events` | NEW Slice 1 brand-local | YES — common re-engagement primitive cross-brand. Lift to NEW `core/luana-core-fidelizacion/` candidate |
| `vitalia_nps_responses` | NEW Slice 1 brand-local | YES — NPS common cross-brand. Lift to NEW `core/luana-core-feedback/` o `core/luana-core-fidelizacion/` |

Documented en `vitalia/docs/architecture/` future ADR + `/pm-luana` retrospective post-Slice 1.

## § 2 — Contratos CONSUMIDOS (producidos by other stories or engine pre-flight)

### 2.1 Engine pre-flight (HARD GATE)

| Surface | Producer | Status |
|---|---|---|
| `luana_core_platform.workers.cron_envelope` | promotion proposal `2026-05-20-core-platform-extensions-slice-1` | `state=migrated` REQUIRED before story dev start |
| `luana_core_platform.repositories.compound_scope_repository.CompoundScopeRepositoryBase` | idem proposal | idem |
| `core/luana-core-platform` 0.2.0 → 0.3.0 | idem proposal | idem |

### 2.2 Engine columns (already added Ola 0 or pre-flight)

| Column | Engine table | Producer story |
|---|---|---|
| `vitalia_appointments.follow_up_due_at` | engine vitalia (Story 11 cement + Ola 0 infra-cross-cutting) | DONE 2026-05-18 |
| `vitalia_appointments.follow_up_reason` | idem | DONE |
| `vitalia_appointments.completed_at` | idem | DONE |
| `vitalia_appointments.balance_status` | idem | DONE |
| `vitalia_appointments.origin` | idem | DONE |
| `offers.requires_multi_session` | engine `core/luana-core-offer-studio/` | promotion proposal `2026-05-17-offer-studio-multi-session-maintenance` (state=migrated) |
| `offers.sessions_expected` | idem | idem |
| `offers.gap_alert_days` | idem | idem |
| `offers.maintenance_schedule` | idem | idem |
| `offers.maintenance_custom_days` | idem | idem |

### 2.3 Engine modules (consumed direct — read-only consult)

| Module | Path | Purpose |
|---|---|---|
| `core/luana-core-platform/workers/cron_envelope` | post lift 2026-05-20 | 6 cron jobs wrap (idempotency + OTel + audit + sentry) |
| `core/luana-core-platform/repositories/CompoundScopeRepositoryBase` | post lift | PHI dual-filter base class (scope_field='clinic_id') |
| `core/luana-core-campaigns/workers/{scheduler_tick, execution_task, segment_refresh_tick, audit_retention_task}` | engine cementado Story 11 | Pattern reference — fidelización custom invocation siguen patrón ARQ + retry + idempotent |
| `core/luana-core-events/outbox/adapter_bus` | engine cementado 2026-04-30 | Emit ReEngagementTriggered + NPSScoreCollected events |
| `core/luana-core-observability/recording/sanitize_payload` | engine | PII sanitization en traces hipaa_lite profile |
| `core/luana-core-observability/recording/BaseObservabilityContext` | engine | Trace context (consume via Adrián callback handler subclass — Story 11 cement) |
| `core/luana-core-sales-agent/runtime/` | engine | Adrián runtime (service inject in ProactiveOutboundService) |
| `core/luana-core-compliance/ComplianceService.validate_outbound_message` | engine | Channel guard (block PHI canales no-encriptados) |
| `core/luana-core-idempotency/` | engine | Idempotency keys + `@idempotent` decorator |
| `core/luana-core-llm/providers/litellm` | engine (canonical post 2026-05-06) | LLM dispatch Lucas reasoning call (NO direct provider adapters) |

### 2.4 Side stories (Slice 1 cross-Olas)

NONE required esta story (Ola 1 fidelización es auto-contenida). Other Olas (2, 3) tienen side stories `vitalia-payment-adapter-mvp` + `vitalia-fiscal-emission-pe` + `vitalia-copilot-tools-impl` — esta story NO depende de ellas.

### 2.5 Consumer-only types from agenda module (cross-feature import via Public API)

```typescript
// vitalia/frontend/src/features/fidelizacion/api/use-availability-slots.ts
export { useAvailabilitySlots } from '@/features/agenda';   // re-exports from agenda Public API
```

Consumed por `SuggestSlotsModal` (consume cuando operador click `[📅 Sugerir slots]` → fetch open slots desde /agenda module).

Si Ola 3 /agenda no shipped al tiempo de Ola 1 fidelización dev → `useAvailabilitySlots` stub fallback returns hardcoded empty list (graceful degradation). Slice 1 modal SuggestSlots = stub "feature available cuando /agenda Ola 3 cierra".

## § 3 — Update outcome-level HANDOFF

Esta story APPEND-only en `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md`:

### § 3 TypeScript types — ADD NPS-shared block

```typescript
// NEW POST 2026-05-20 — produced by fidelización Ola 1

export type NPSBand = "promoter" | "passive" | "detractor";

export interface NPSRowDTO {
  id: string;
  patientName: string;
  score: number;
  band: NPSBand;
  commentShort: string | null;
  respondedAt: string;
  taggedInInbox: boolean;
}

export interface NPSSummaryResponse {
  averageScore: number;
  totalResponses: number;
  rows: NPSRowDTO[];
}
```

### § 4 Zod schemas — ADD rows

| Schema | Path | Producer | Consumers |
|---|---|---|---|
| `npsSchema` | `vitalia/frontend/src/lib/zod-schemas/nps.ts` | **fidelización Ola 1** | inbox (tag detractor) |
| `reEngagementEventSchema` | `vitalia/frontend/src/lib/zod-schemas/re-engagement-event.ts` | **fidelización Ola 1** | marketing Slice 2 (Lucas card source) |

### § 6 Domain events — ADD rows

| Event | Producer | Consumers |
|---|---|---|
| `ReEngagementTriggered` | **fidelización (esta story)** | inbox (proactive_outbound conversation), audit log |
| `NPSScoreCollected` | **fidelización (esta story)** | inbox (tag detractor), marketing (Slice 2 NPS distribution analytics) |
| `PatientOptedOut` | **fidelización (esta story) — via opt_out_service** | inbox + pipeline + marketing (cascade cancel) |
| `PatientPausedReEngagement` | **fidelización (esta story)** | fidelización own UI refresh + audit log |

### § 7 BE modules compartidos — ADD row

| Module | Path | Producer | Consumers |
|---|---|---|---|
| `vitalia/backend/src/modules/vitalia/fidelizacion/` | brand-local NEW | **Ola 1 fidelización** | inbox (NPS tag via NPSScoreCollected event consume), future marketing (Slice 2 Lucas card source) |

## § 4 — Bitácora HANDOFF update

- 2026-05-20: /architect produced ready package vitalia-slice-1-fidelizacion. Contracts cementados producidos + consumidos. APPEND-only diff aplicable a outcome-level HANDOFF al cierre /pm-vitalia merge ticket T-16.
- 2026-05-20: T-16 cementó contratos verbatim — 26 shape tests GREEN en `vitalia/backend/tests/integration/test_cross_story_contracts.py`. 4 eventos de dominio + 2 endpoint DTOs verificados (NPSScoreCollected, ReEngagementTriggered, PatientOptedOut, PatientPausedReEngagement, NPSSummaryResponse, ReEngagementPatternListResponse). Contratos listos para consumo Ola 2+ sin coordinación adicional.

## § 5 — Verificación cross-story al merge (post implement)

`/pm-vitalia` al cerrar `state=reviewing → done` ejecuta:

```bash
# 1. Smoke E2E ruta propia
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --grep "fidelizacion"

# 2. Smoke E2E rutas Ola 1 paralelas (regression check)
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --grep "vitalia-slice-1-ola-1"

# 3. Cross-story contract tests (NPS + ReEngagementTriggered shape)
cd vitalia/backend && ${WS}/.venv/bin/pytest tests/integration/test_cross_story_contracts.py -v -k "nps or reengagement"

# 4. Update HANDOFF outcome-level: marcar contratos produced como "shipped" + add bitácora row
# Update HANDOFF this story doc: marcar "implemented" all contracts
```

## § 6 — Notas estado fluido

Esta story consume Lead schema producido por inbox Ola 1 paralela SOLO en escenario hipotético future Slice 2 (visualizar lead activo en re-engagement context). Slice 1 fidelización NO consume Lead schema directamente — solo Patient + Appointment + Offer + Re-engagement events.

`/inbox` Ola 1 paralela consume NPSRowDTO + NPSScoreCollected event de esta story → coordination cross-Ola 1 ratificada Chris.
