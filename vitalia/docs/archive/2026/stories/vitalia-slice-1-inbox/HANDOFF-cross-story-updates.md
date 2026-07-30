# HANDOFF cross-story updates — vitalia-slice-1-inbox produces

> **Consumer:** Olas 2+3 stories (`vitalia-slice-1-pipeline` · `vitalia-slice-1-marketing` · `vitalia-slice-1-agenda` · `vitalia-slice-1-fidelizacion`).
> **Parent SSoT:** `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md` § 3-6.
> **This doc:** scoped summary of what THIS sub-story (`vitalia-slice-1-inbox` · Ola 1) produces for cross-story consumption.
> **Update obligation:** `/pm-vitalia` updates parent HANDOFF doc § 10 Bitácora when this story merges to main.

## § 1 — Contratos TypeScript producidos

### `vitalia/frontend/src/features/crm-shared/types.ts` (NEW Ola 1)

Exporta interfaces consumibles cross-feature via `import { Lead, Conversation, LeadStage } from "@/features/crm-shared"`:

```typescript
export type LeadStage =
  | "interesado"
  | "calificando"
  | "considerando"
  | "listo"
  | "reservado_deposito"
  | "decidio_no";

export interface Lead {
  id: string;
  tenant_id: string;
  clinic_id: string;        // dual-scope per HIPAA-lite (REQUIRED downstream para queries)
  name: string;
  phone: string | null;     // PHI — consumers MUST wrap with <PiiMaskedSpan>
  email: string | null;     // PHI — idem
  stage: LeadStage;
  attribution: {
    origin: "sales_agent" | "walk_in" | "phone_manual" | "proactive_outbound";
    channel: string | null;
    attributed_at: string;
  };
  last_conversation_id: string | null;  // navegación a /inbox?lead={id}
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  lead_id: string;
  tenant_id: string;
  clinic_id: string;
  patient_id: string | null;
  channel: "whatsapp" | "instagram" | "facebook_messenger" | "web" | "walk_in" | "phone";
  status: "active" | "paused" | "closed" | "archived";
  handler_mode: "ai" | "human";
  proposal_required: boolean;
  pause_until: string | null;
  help_needed: boolean;
  help_needed_reason: string | null;
  unread_media_count: number;
  last_message_at: string;
  last_message_preview: string | null;
  messages_count: number;
  stage_decision: LeadStage | null;
  linked_offer_id: string | null;
  updated_at: string;
}
```

**Consumers:**
- `vitalia-slice-1-pipeline` Ola 2 → reads `Lead.stage` for kanban columns · reads `Conversation.help_needed` for signal flag
- `vitalia-slice-1-agenda` Ola 3 → reads `Lead.id` + `last_conversation_id` to link agenda detail → conversation history
- `vitalia-slice-1-fidelizacion` Ola 1 (parallel) → reads `Lead.stage = "decidio_no"` for re-engagement targeting

### Stage value mapping (BE ⟷ FE)

Backend uses Spanish slugs in `vitalia_conversations.stage_decision`: `interesado | considerando | listo | decidio_no`.
Frontend `Lead.stage` accepts wider enum (6 values · includes `calificando` + `reservado_deposito` produced by pipeline Ola 2).

**Coordination:** inbox Slice 1 ONLY writes 4 stage values (`interesado | considerando | listo | decidio_no`). Pipeline Ola 2 adds the other 2 (`calificando | reservado_deposito`). FE enum must include all 6 to handle pipeline-produced leads.

## § 2 — Schemas Zod producidos

| Schema | Path | Consumers cross-story |
|---|---|---|
| `leadSchema` | `vitalia/frontend/src/lib/zod-schemas/lead.ts` | pipeline (kanban card validation), agenda (paciente link), fidelización (re-engagement) |
| `conversationSchema` | `vitalia/frontend/src/lib/zod-schemas/conversation.ts` | pipeline (signal flag form validation), agenda (linked conversation lookup) |
| (`appointmentSchema`, `paymentEventSchema`, `npsSchema`, `lucasRecommendationSchema` PRODUCED BY OTHER STORIES per HANDOFF parent § 4) | — | — |

Public API via `vitalia/frontend/src/lib/zod-schemas/index.ts` — single import point.

## § 3 — API endpoints producidos (BE Slice 1 inbox)

### Inbox-specific (consumed UI only — no cross-story consumers)

| Method | Path | Auth | Consumers |
|---|---|---|---|
| POST | `/api/v1/vitalia/inbox/conversations/{conv_id}/messages` | Bearer | inbox UI only |
| POST | `/api/v1/vitalia/inbox/conversations/{conv_id}/messages/{msg_id}/revert` | Bearer | inbox UI only |
| POST | `/api/v1/vitalia/inbox/conversations/{conv_id}/mode` | Bearer | inbox UI only |
| POST | `/api/v1/vitalia/inbox/conversations/{conv_id}/pause-adrian` | Bearer | inbox UI only |
| GET | `/api/v1/vitalia/inbox/conversations/{conv_id}/activity-stream` | Bearer | inbox UI only |
| GET | `/api/v1/vitalia/inbox/conversations/{conv_id}/tools` | Bearer | inbox UI only |
| POST | `/api/v1/vitalia/inbox/conversations/{conv_id}/transcribe-audio` | Bearer | inbox UI only |
| POST | `/api/v1/vitalia/inbox/proactive-outbound` | Bearer | inbox UI only · also called CROSS-STORY from agenda/pipeline/marketing entry points (modal opened from those routes) |

### CRM endpoints (PRODUCED HERE · CONSUMED CROSS-STORY)

| Method | Path | Producer | Consumers |
|---|---|---|---|
| GET | `/api/v1/vitalia/crm/leads` (paginated + filters) | **inbox Ola 1** | pipeline (kanban load), agenda (paciente picker) |
| GET | `/api/v1/vitalia/crm/leads/{lead_id}` | **inbox Ola 1** (extends existing) | pipeline (drawer detail), agenda (booking detail) |
| GET | `/api/v1/vitalia/crm/conversations` (filter status+channel) | **inbox Ola 1** | pipeline (conversation signal flag) |
| GET | `/api/v1/vitalia/crm/conversations/{conv_id}` (with last N messages + tools + action receipts) | **inbox Ola 1** | pipeline (drawer historial) |

**NOT produced here:**
- `POST /api/v1/vitalia/crm/leads/{id}/stage` (advance stage) → produced by `vitalia-slice-1-pipeline` Ola 2

## § 4 — Domain events emitted (consumed via engine outbox bus)

| Event class | Producer | Consumers cross-story |
|---|---|---|
| `ConversationStarted` | inbox Ola 1 | pipeline (auto-add lead to "Interesado" if NEW), marketing (UTM tracking initial channel) |
| `MessageSent` | inbox Ola 1 | (cross-story: NONE direct · feed eventual analytics Slice 2) |
| `MessageRetracted` | inbox Ola 1 | pipeline (audit log mirror · operator activity sidebar), agenda (NA), fidelización (NA) |
| `ModeChanged` | inbox Ola 1 | (cross-story: NONE direct · audit log only) |
| `AdrianPaused` | inbox Ola 1 | (cross-story: NONE direct · audit log only) |
| `ProactiveOutboundSent` | inbox Ola 1 | pipeline (signal flag), fidelización (re-engagement counter), agenda (NA), marketing (UTM attribution + opt-out tracking for MARKETING templates) |

Outbox bus: `luana_core_events.outbox.adapter_bus.publish(event, session=None)` (post `USE_OUTBOX_PATTERN_*=True` default since 2026-04-29).

Subscribers register in their own story modules via:
```python
# In consumer story (e.g., vitalia-slice-1-pipeline)
from src.modules.vitalia.crm.domain.events import ConversationStarted
from luana_core_events.subscriber import subscribe

@subscribe(ConversationStarted)
async def on_conversation_started_for_pipeline(event: ConversationStarted, session: AsyncSession) -> None:
    # Auto-add lead to "Interesado" stage if not already in pipeline
    ...
```

## § 5 — Backend modules exportados

| Module | Path | Cross-story access pattern |
|---|---|---|
| `vitalia.crm` (extended) | `vitalia/backend/src/modules/vitalia/crm/` | Inbox extends with Conversation/Message/ActivityEvent/ActionReceipt domain. Pipeline Ola 2 extends with stage transition logic. Cross-story access ONLY via API endpoints + domain events. NEVER direct module import. |
| `vitalia.inbox` (NEW) | `vitalia/backend/src/modules/vitalia/inbox/` | API + services scope inbox-only. ProactiveOutbound API consumed cross-story by agenda/pipeline/marketing modal triggers. |
| `vitalia.connections.whisper` (NEW) | `vitalia/backend/src/modules/vitalia/connections/whisper/` | Brand-local adapter Slice 1. Lift candidate Slice 2 (`core/luana-core-llm/providers/whisper.py`). Cross-story usage = ONLY through `WhisperTranscribeService` (no direct adapter import). |
| `vitalia.sales_agent.tools.retract_last_message` (NEW) | `vitalia/backend/src/modules/vitalia/sales_agent/tools/retract_last_message.py` | Registered via EP-3 in extensions.py. Cross-story: Adrián runtime invokes tool — no direct import elsewhere. |

## § 6 — Side stories blockers cleared by this story

Inbox Slice 1 itself has NO side-story blockers (auto-contenida).

Inbox Slice 1 produces foundation that Olas 2+3 stories require:
- `vitalia-slice-1-pipeline` Ola 2 depends on `Lead` + `Conversation` types + endpoints producidos here
- `vitalia-slice-1-agenda` Ola 3 depends on `Lead` type + lead lookup endpoint + ProactiveOutbound modal entry point
- `vitalia-slice-1-marketing` Ola 2 depends on `LeadCreated` + `ConversationStarted` events for UTM attribution

## § 7 — Verificación cross-story al merge

Cuando esta story cierra `state: done`, ejecutar:

```bash
WS=$(git rev-parse --show-toplevel)

# 1. Smoke E2E ruta propia /inbox
cd ${WS}/vitalia/frontend && E2E_BASE_URL=https://dev-app.vitalialat.com npx playwright test --grep "vitalia-slice-1-inbox"

# 2. Smoke E2E rutas dependientes (regression check — verify no breaks downstream)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=https://dev-app.vitalialat.com npx playwright test --grep "vitalia-slice-1"

# 3. Cross-story contract tests (verify types + endpoints + events are stable)
cd ${WS} && ${WS}/.venv/bin/pytest vitalia/backend/tests/integration/test_cross_story_contracts.py -v

# 4. Update parent HANDOFF.md § 10 Bitácora marking contracts produced as "shipped"
```

## § 8 — Bitácora cross-story (este sub-story)

- 2026-05-17: parent `vitalia-ux-discovery` spec ratificada Chris (Batch 2 inbox cementado)
- 2026-05-19: parent archived to `vitalia/docs/archive/2026/stories/vitalia-ux-discovery/` (state=done)
- 2026-05-20: replan ratified Chris — esta sub-story refresh ready package post replan
- 2026-05-20: ready package emitted (this HANDOFF + 01-spec-extract + 02-design-ui + 03-arch* + 04-validators + 05-guidelines + 06-tickets)
- _post-merge_ (TBD by `/pm-vitalia` at story close): contracts marked shipped en parent HANDOFF doc § 10 Bitácora + capability YAMLs created

## § 9 — Referencias

- Parent SSoT: `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md`
- `01-spec-extract.md` (this story spec)
- `03-arch.md` (this story arch index)
- `03-arch-be.md` § 4 (endpoints) · § 3.5 (domain events)
- `03-arch-fe.md` § 4 (TS types) · § 1 (FSD structure showing crm-shared)
- HANDOFF parent § 3 (TS types) · § 4 (Zod) · § 5 (endpoints) · § 6 (events) · § 7 (BE modules)
