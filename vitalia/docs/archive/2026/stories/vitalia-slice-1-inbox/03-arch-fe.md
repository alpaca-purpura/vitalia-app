# vitalia-slice-1-inbox — Frontend sub-architecture

> **Consumer:** `builder-frontend` (Sonnet build) + `auditor-frontend` (Opus audit).
> **Index:** `03-arch.md` § 0-9 (read first).
> **Brand surface:** `vitalia/frontend/src/features/inbox/**` + `vitalia/frontend/src/features/crm-shared/**` (NEW) + `vitalia/frontend/src/lib/zod-schemas/{lead,conversation}.ts` (NEW).
> **Port:** 3002 dev (per `brand.yaml::infra.dev.frontend_port`).
> **Design tokens SSoT:** `vitalia/frontend/src/app/globals.css` (cementados Story 11).
> **Mockup SSoT:** `02-design-ui-mockup.html`.

## 1. FSD-Lite module structure

```
vitalia/frontend/src/
├── app/(app)/inbox/
│   └── page.tsx                              ← RSC entry · resuelve searchParams · pasa a InboxPageClient
├── features/
│   ├── crm-shared/                           ← NEW Slice 1 Ola 1 (producer, consumed por pipeline + agenda)
│   │   ├── types.ts                          ← Lead · Conversation · LeadStage interfaces (per HANDOFF § 3)
│   │   ├── api/
│   │   │   ├── use-leads.ts                  ← React Query hook GET /api/v1/vitalia/crm/leads (paginated)
│   │   │   ├── use-conversation-detail.ts    ← GET /api/v1/vitalia/crm/conversations/{id}
│   │   │   └── use-conversations.ts          ← GET /api/v1/vitalia/crm/conversations
│   │   └── index.ts                          ← Public API (types + hooks)
│   └── inbox/                                ← NEW Slice 1 (this story)
│       ├── api/
│       │   ├── use-send-message.ts           ← POST /messages · optimistic update + Idempotency-Key
│       │   ├── use-retract-message.ts        ← POST /messages/{id}/revert · If-Match header for OCC
│       │   ├── use-set-mode.ts               ← POST /mode · OCC + optimistic + rollback on 409
│       │   ├── use-pause-adrian.ts           ← POST /pause-adrian
│       │   ├── use-activity-stream.ts        ← GET /activity-stream · poll 5s when expanded
│       │   ├── use-tools-state.ts            ← GET /tools (cached 30s · read-only)
│       │   ├── use-transcribe-audio.ts       ← POST /transcribe-audio (operator upload flow)
│       │   ├── use-proactive-outbound.ts     ← POST /proactive-outbound (modal submit)
│       │   └── use-attach-media.ts           ← POST multipart attach (composer)
│       ├── components/
│       │   ├── InboxLayout.tsx               ← 3-pane grid (REUSE adapter closer-studio CloserLayout)
│       │   ├── InboxPageClient.tsx           ← "use client" wrapper with nuqsAdapter
│       │   ├── ConversationListPanel.tsx     ← 320px left pane (NEW assembly)
│       │   ├── SearchInput.tsx               ← debounce 300ms · nuqs `search` (NEW)
│       │   ├── FilterChips.tsx               ← primarios + collapsible "Más ▼" (NEW)
│       │   ├── ConversationList.tsx          ← REUSE adapter closer-studio
│       │   ├── ConversationItem.tsx          ← REUSE adapter + badges 🔴 📎 + stage chip
│       │   ├── ListEmptyState.tsx            ← 4 variants (NEW · consume copy.ts)
│       │   ├── ConversationThread.tsx        ← REUSE adapter closer-studio (retoken violeta→purpura)
│       │   ├── ThreadHeader.tsx              ← NEW (segmented + voiceStyleChip + 3 buttons)
│       │   ├── SegmentedControl3Modes.tsx    ← NEW · Shadcn ToggleGroup variant=outline 3-state
│       │   ├── VoiceStyleChip.tsx            ← NEW · read-only · 🟢 chip
│       │   ├── PauseAdrianButton.tsx         ← NEW · confirm modal · 60min pause
│       │   ├── ToolsSheetTrigger.tsx         ← NEW · opens AdrianToolsSheet
│       │   ├── ContactSidebarToggle.tsx      ← NEW · toggles right sidebar
│       │   ├── MessageBubble.tsx             ← REUSE adapter + audio + image stub render · ActionReceiptUndoChip mounted inline
│       │   ├── VoiceMessagePlayer.tsx        ← NEW · HTML5 audio + scrubber + speed + transcript collapsible
│       │   ├── ImageAnalysisCard.tsx         ← NEW stub Slice 1 · placeholder análisis Adrián
│       │   ├── ActionReceiptUndoChip.tsx     ← NEW · countdown 5min · click → modal → retract endpoint
│       │   ├── ComposerArea.tsx              ← assembly composer (REUSE adapter MessageInput + new attach/voice buttons)
│       │   ├── MessageInput.tsx              ← REUSE adapter · placeholder dinámico per-modo
│       │   ├── ComposerAttachButton.tsx      ← NEW · [📎] filesystem upload
│       │   ├── ComposerVoiceButton.tsx       ← NEW · [🎤] MediaRecorder API (REUSE direct VoiceOverlay copilot Nicolify)
│       │   ├── SendButton.tsx                ← NEW · texto dinámico "Enviar como Adrián ➤" o "Enviar"
│       │   ├── AgentActivityStream.tsx       ← NEW · sticky 32px expand 240px · poll 5s when expanded
│       │   ├── ContactSidebar.tsx            ← REUSE adapter · envolver PHI fields con <PiiMaskedSpan>/<RequireRole>/<AuditedSection>
│       │   ├── AdrianToolsSheet.tsx          ← NEW · Shadcn Sheet right 420px · read-only
│       │   ├── ProactiveOutboundModal.tsx    ← NEW · cross-link agenda+pipeline+marketing
│       │   ├── PauseAdrianConfirmModal.tsx   ← NEW
│       │   ├── ProposalCardBanner.tsx        ← NEW · banner for agent-waiting-approval state (modo Adrián consulta)
│       │   └── index.ts                      ← Public API (no deep imports)
│       ├── hooks/
│       │   ├── use-mode-toggle.ts            ← orchestrates SetMode + invalidation
│       │   ├── use-action-receipt-timer.ts   ← countdown 5min logic
│       │   ├── use-conversation-filters.ts   ← derive React Query key from nuqs URL state
│       │   └── use-activity-stream-poll.ts   ← poll 5s logic
│       ├── store/
│       │   └── inbox-store.ts                ← Zustand · UI-only state (expandedActivityStream, contactSidebarOpen, attachQueue, retractingMessages: Set<string>, proactiveModalOpen)
│       ├── types/
│       │   ├── message.ts                    ← Message interface (mirror Pydantic MessageResponse)
│       │   ├── action-receipt.ts
│       │   ├── activity-event.ts
│       │   ├── conversation-detail.ts
│       │   └── tools-state.ts
│       ├── url-state.ts                      ← nuqs INBOX_URL_SCHEMA (per § 4)
│       ├── copy.ts                           ← INBOX_COPY constants · LatAm neutro (NO voseo)
│       └── index.ts                          ← Public API
├── lib/
│   ├── zod-schemas/                          ← NEW shared (producer Ola 1)
│   │   ├── lead.ts                           ← leadSchema · consumed by inbox + pipeline + agenda
│   │   ├── conversation.ts                   ← conversationSchema · consumed by inbox + pipeline
│   │   └── index.ts
│   └── nuqs-parsers/
│       └── inbox.ts                          ← parsers shared if any
└── components/shared/                        ← Already exist (Story 11)
    ├── phi/                                  ← PiiMaskedSpan · RequireRole · AuditedSection
    ├── agents/                               ← AgentAvatar · AgentAttribution · agentNameByRole
    ├── activity-stream/                      ← ActivityStreamSticky base (Story 11 — extend per inbox needs)
    ├── contact-sidebar/                      ← ContactSidebar base (Story 11)
    └── shell/                                ← AppShell · Sidebar · TopBar (Story 11)
```

## 2. Route + page entry

```tsx
// vitalia/frontend/src/app/(app)/inbox/page.tsx (RSC)
import { InboxPageClient } from "@/features/inbox";

export const dynamic = "force-dynamic"; // requires auth + tenant context

export default function InboxPage() {
  // RSC: only resolves layout shell. Client component owns nuqs state + data fetching.
  return <InboxPageClient />;
}
```

```tsx
// vitalia/frontend/src/features/inbox/components/InboxPageClient.tsx
"use client";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import { InboxLayout } from "./InboxLayout";

export function InboxPageClient() {
  return (
    <NuqsAdapter>
      <InboxLayout />
    </NuqsAdapter>
  );
}
```

## 3. URL state contract (nuqs)

```ts
// vitalia/frontend/src/features/inbox/url-state.ts
import { parseAsString, parseAsStringEnum, parseAsBoolean, useQueryStates } from "nuqs";

export const INBOX_URL_SCHEMA = {
  lead: parseAsString,                                                       // selected conv id (replace)
  channel: parseAsStringEnum<"whatsapp" | "instagram" | "email">(["whatsapp","instagram","email"]),
  status: parseAsStringEnum(["active","waiting-deposit","nps-pending","closed"]),
  stage: parseAsStringEnum(["interested","considering","ready-to-book","decided-no"]),
  mode: parseAsStringEnum(["adrian-decide","adrian-consulta","yo-escribo"]),
  period: parseAsStringEnum(["today","yesterday","week","month"]),
  helpNeeded: parseAsBoolean,
  unreadMedia: parseAsBoolean,
  search: parseAsString,
} as const;

export function useInboxUrlState() {
  return useQueryStates(INBOX_URL_SCHEMA, { history: "replace" });
}
```

All sub-state intra-route uses `history: 'replace'`. Solo nav inter-route P1 (sidebar) usa `push`.

## 4. Component contracts (TS types mirror Pydantic v2 DTOs)

```ts
// vitalia/frontend/src/features/crm-shared/types.ts (PRODUCER · consumed cross-story)
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
  clinic_id: string;
  name: string;
  phone: string | null;
  email: string | null;
  stage: LeadStage;
  attribution: {
    origin: "sales_agent" | "walk_in" | "phone_manual" | "proactive_outbound";
    channel: string | null;
    attributed_at: string;
  };
  last_conversation_id: string | null;
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

```ts
// vitalia/frontend/src/features/inbox/types/message.ts
export interface Message {
  id: string;
  conversation_id: string;
  sender_type: "patient" | "agent_ai" | "agent_human" | "system";
  sender_user_id: string | null;
  body_text: string | null;
  media_kind: "audio" | "image" | "video" | "document" | "sticker" | null;
  media_url: string | null;
  media_duration_s: number | null;
  transcription_text: string | null;
  transcription_confidence: number | null;
  retracted_at: string | null;
  retract_succeeded: boolean | null;
  handler_mode: "ai" | "human";
  sent_at: string;
  action_receipt_expires_at: string | null;
}

export interface ConversationDetail {
  conversation: Conversation;
  lead: Lead;
  messages: Message[];
  action_receipts: { message_id: string; expires_at: string }[];
  tools_state: ToolsState | null;
}
```

## 5. React Query hooks pattern

```ts
// vitalia/frontend/src/features/inbox/api/use-send-message.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchClient } from "@/lib/api/fetchClient";
import { conversationDetailKey, conversationsListKey } from "./_keys";
import type { Message } from "../types/message";

interface SendMessageInput {
  conversationId: string;
  bodyText?: string;
  mediaUrl?: string;
  mediaKind?: "audio" | "image" | "video" | "document";
  handlerModeOverride?: "ai" | "human";
  idempotencyKey: string;  // client-generated UUID
}

export function useSendMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: SendMessageInput): Promise<Message> => {
      const r = await fetchClient(`/api/v1/vitalia/inbox/conversations/${input.conversationId}/messages`, {
        method: "POST",
        headers: { "Idempotency-Key": input.idempotencyKey, "Content-Type": "application/json" },
        body: JSON.stringify({
          body_text: input.bodyText,
          media_url: input.mediaUrl,
          media_kind: input.mediaKind,
          handler_mode_override: input.handlerModeOverride,
        }),
      });
      if (!r.ok) throw new Error(`Send failed: ${r.status}`);
      return r.json();
    },
    onSuccess: (newMsg, input) => {
      qc.invalidateQueries({ queryKey: conversationDetailKey(input.conversationId) });
      qc.invalidateQueries({ queryKey: conversationsListKey() });
    },
  });
}
```

React Query keys + invalidation strategy:
- `['inbox','conversations', filters]` → invalidated on `MessageSent` SSE event OR explicit mutations
- `['inbox','conversation', leadId]` → invalidated on `message:sent | message:retracted | mode:changed | adrian:paused`
- `['inbox','activity-stream', conversationId]` → polled every 5s when ActivityStream expanded · enabled flag conditional
- `['inbox','tools', conversationId]` → cached 30s (changes infrequent · read-only)

## 6. Optimistic update + OCC pattern (SetMode SC-03)

```ts
// vitalia/frontend/src/features/inbox/api/use-set-mode.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchClient } from "@/lib/api/fetchClient";

export function useSetMode(conversationId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: { newMode: "ai" | "human"; proposalRequired: boolean; expectedUpdatedAt: string }) => {
      const r = await fetchClient(`/api/v1/vitalia/inbox/conversations/${conversationId}/mode`, {
        method: "POST",
        headers: { "If-Match": input.expectedUpdatedAt, "Content-Type": "application/json" },
        body: JSON.stringify({ mode: input.newMode, proposal_required: input.proposalRequired }),
      });
      if (r.status === 409) {
        const err = new Error("conflict");
        (err as any).status = 409;
        throw err;
      }
      if (!r.ok) throw new Error("Set mode failed");
      return r.json();
    },
    onMutate: async (input) => {
      // Optimistic update
      const key = ["inbox","conversation", conversationId];
      await qc.cancelQueries({ queryKey: key });
      const previous = qc.getQueryData(key);
      qc.setQueryData(key, (old: any) => old && {
        ...old,
        conversation: { ...old.conversation, handler_mode: input.newMode, proposal_required: input.proposalRequired },
      });
      return { previous };
    },
    onError: (err: any, _input, ctx) => {
      // Rollback
      qc.setQueryData(["inbox","conversation", conversationId], ctx?.previous);
      if (err.status === 409) {
        // Re-fetch fresh state
        qc.invalidateQueries({ queryKey: ["inbox","conversation", conversationId] });
        // Trigger toast (handled by caller)
      }
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["inbox","conversation", conversationId] });
    },
  });
}
```

## 7. PHI components (reuse Story 11 shared)

```tsx
// vitalia/frontend/src/features/inbox/components/ContactSidebar.tsx (REUSE adapter + extend)
"use client";
import { PiiMaskedSpan, RequireRole, AuditedSection } from "@/components/shared/phi";
import { INBOX_COPY } from "../copy";
import type { Lead, Conversation } from "@/features/crm-shared";

export function ContactSidebar({ lead, conversation }: { lead: Lead; conversation: Conversation }) {
  return (
    <aside className="w-[280px] vt-bg-surface border-l vt-border" aria-label={INBOX_COPY.contactSidebar.sectionContact}>
      <section>
        <h3 className="text-sm font-semibold">{INBOX_COPY.contactSidebar.sectionContact}</h3>
        <AuditedSection resourceType="patient.contact" resourceId={lead.id}>
          {lead.phone && (
            <PiiMaskedSpan kind="phone" value={lead.phone} aria-label={INBOX_COPY.contactSidebar.revealField + ' teléfono'}>
              {/* renders ***-4567 🔓 by default; click reveal triggers audit log via AuditedSection */}
            </PiiMaskedSpan>
          )}
          {lead.email && (
            <PiiMaskedSpan kind="email" value={lead.email} />
          )}
        </AuditedSection>
      </section>

      <section>
        <h3 className="text-sm font-semibold">{INBOX_COPY.contactSidebar.sectionStage}</h3>
        {/* Stage decision chip */}
      </section>

      <RequireRole roles={["doctor","nurse","admin_clinic"]} fallback={null}>
        <section>
          <h3 className="text-sm font-semibold">{INBOX_COPY.contactSidebar.sectionNpsHistory}</h3>
          {/* NPS history list */}
        </section>
      </RequireRole>
    </aside>
  );
}
```

## 8. Microcopy (INBOX_COPY single-locale tree-shakable)

Already defined in parent `01-spec.md` § Microcopy (líneas 882-1052). Cement:

```ts
// vitalia/frontend/src/features/inbox/copy.ts
// SSoT microcopy /inbox · LatAm neutro (sin voseo) · ratificado /po-ux v1 Batch 2

export const INBOX_COPY = {
  pageTitle: "Inbox",
  empty: {
    noConversations: { heading: "Aún no hay conversaciones", body: "Cuando lleguen pacientes interesados, Adrián los va a recibir con calidez. Puedes acompañar siempre." },
    noHelpNeeded: { heading: "Adrián resuelve solo por ahora", body: "Si alguna conversación necesita tu mirada, va a aparecer acá con un indicador rojo." },
    noMediaUnread: { heading: "Sin audios o imágenes pendientes", body: "Cuando un paciente envíe una foto o nota de voz, vas a verla acá antes de que se enfríe." },
    noResultsFilter: { heading: "Sin resultados para este filtro", body: "Limpia los filtros para volver a ver todas las conversaciones.", cta: "Limpiar filtros" },
  },
  filters: { /* ... see parent line 882+ */ },
  segmentedMode: { /* ... */ },
  pauseAgent: { /* ... */ },
  voiceStyleChip: { configured: "Estilo: consultivo · sin presión", unconfigured: "Estilo: voz por defecto", cta: "Configurar" },
  composer: { /* ... */ },
  multimedia: { /* ... */ },
  toolsSheet: { /* ... */ },
  activityStream: { /* ... */ },
  actionReceipt: { /* ... */ },
  contactSidebar: { /* ... */ },
  helpNeededBanner: { /* ... */ },
  errors: { /* ... */ },
} as const;
```

Helper interpolation:

```ts
// vitalia/frontend/src/lib/copy.ts (NEW shared util — to be added by T-inbox-fe-shell ticket)
export function formatCopy(template: string, vars: Record<string,string>): string {
  return Object.entries(vars).reduce((s, [k, v]) => s.replace(`{${k}}`, v), template);
}
```

## 9. Reuse adapter pattern (fork físico)

| Component | Source nicolify path | Destination vitalia path | Token adapter |
|---|---|---|---|
| CloserLayout | `nicolify/frontend/src/features/closer-studio/components/CloserLayout.tsx` | `vitalia/frontend/src/features/inbox/components/InboxLayout.tsx` | bg-amber-50 → vt-bg-azul-marino-8 · violet-* → vt-purpura-* |
| ConversationList | `nicolify/frontend/src/features/closer-studio/components/inbox/ConversationList.tsx` | `vitalia/frontend/src/features/inbox/components/ConversationList.tsx` | chips Temperature borrados · NEW chips 🔴 + 📎 + Stage decisión |
| ConversationItem | idem | idem | + badge Stage chip + 🔴/📎 indicators |
| ConversationThread | idem | idem | header "AI Activo / Tienes el control" → SegmentedControl3Modes |
| MessageBubble | idem | idem | + audio render + image stub + ActionReceiptUndoChip inline · avatar Adrián gradient_adrian |
| MessageInput | idem | idem | + composer attach/voice buttons · placeholder dinámico |
| ContactSidebar | idem | idem | + PiiMaskedSpan/RequireRole/AuditedSection wrappers |
| VoiceOverlay (composer) | `nicolify/frontend/src/features/copilot/components/composer/VoiceOverlay.tsx` | `vitalia/frontend/src/features/inbox/components/ComposerVoiceButton.tsx` | retoken · public API exposed |

**Boundaries:** `vitalia/frontend/` MUST NOT import from `nicolify/frontend/` runtime. Copy adapter pattern = NEW files in vitalia with token retoken, NOT re-export. Arch fitness `test_no_cross_brand_imports.test.ts` enforces.

## 10. Storybook stories (NEW Slice 1 components)

Each NEW Slice 1 component has `.stories.tsx` with variants. See `02-design-ui.md` § 9 for list.

## 11. Architecture fitness impact

Gates that must keep passing post this story:

- `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_colors.test.ts` — only CSS vars from globals.css. No HEX literals in TSX.
- `vitalia/frontend/src/__tests__/architecture/test_fsd_boundaries.test.ts` — features/inbox doesn't import from features/pipeline OR features/agenda OR features/fidelizacion (consume only crm-shared Public API + components/shared).
- `vitalia/frontend/src/__tests__/architecture/test_no_cross_feature_imports.test.ts` — only via index.ts Public API.
- `vitalia/frontend/src/__tests__/architecture/test_server_first.test.ts` — RSC default. `"use client"` only on leaf nodes with state/handlers.
- `vitalia/frontend/src/__tests__/architecture/test_phi_pii_components_used.test.ts` — ContactSidebar wraps all PHI fields with PiiMaskedSpan/RequireRole/AuditedSection.
- `vitalia/frontend/src/__tests__/architecture/test_no_voseo_in_copy.test.ts` — copy.ts voseo glosario scan.
- `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_strings_inbox.test.ts` — NEW Slice 1 · grep `features/inbox/.*\.tsx` por strings hardcoded > 3 chars (allowlist whitelisted en arch test).

## 12. E2E Playwright

```ts
// vitalia/frontend/e2e/specs/smoke/inbox.smoke.spec.ts (NEW T-inbox-integ-1)
import { test, expect } from "../../fixtures/auth.fixture";
import { InboxPage } from "../../pages/inbox.page";

test.describe("inbox smoke /inbox vitalia-slice-1-inbox", () => {
  test("renders shell + conversation list + thread placeholder on auth dr.demo", async ({ authenticatedPage }) => {
    const inbox = new InboxPage(authenticatedPage);
    await inbox.goto();
    await expect(inbox.shell).toBeVisible();
    await expect(inbox.conversationList).toBeVisible();
    await expect(inbox.threadPlaceholder).toBeVisible();
  });

  test("segmented control 3-modes toggles handler_mode (SC-01 happy)", async ({ authenticatedPage }) => {
    const inbox = new InboxPage(authenticatedPage);
    await inbox.goto({ lead: "mock-mrodriguez" });
    await expect(inbox.segmentedControl).toHaveAttribute("data-value", "adrian-decide");
    await inbox.clickMode("yo-escribo");
    await expect(inbox.segmentedControl).toHaveAttribute("data-value", "yo-escribo");
    await expect(inbox.composerPlaceholder).toContainText("Escribe tu mensaje a");
  });

  test("voice style chip visible + chip text per brand voice config", async ({ authenticatedPage }) => {
    const inbox = new InboxPage(authenticatedPage);
    await inbox.goto({ lead: "mock-mrodriguez" });
    await expect(inbox.voiceStyleChip).toContainText("Estilo: consultivo");
  });
});
```

POM `inbox.page.ts` (NEW T-inbox-integ-1):
```ts
import { Page, Locator } from "@playwright/test";

export class InboxPage {
  readonly shell: Locator;
  readonly conversationList: Locator;
  readonly threadPlaceholder: Locator;
  readonly segmentedControl: Locator;
  readonly composerPlaceholder: Locator;
  readonly voiceStyleChip: Locator;

  constructor(private page: Page) {
    this.shell = page.locator("[data-testid=app-shell]");
    this.conversationList = page.locator("[data-testid=conversation-list]");
    this.threadPlaceholder = page.locator("[data-testid=thread-placeholder]");
    this.segmentedControl = page.locator("[data-testid=segmented-mode]");
    this.composerPlaceholder = page.locator("[data-testid=composer-input]");
    this.voiceStyleChip = page.locator("[data-testid=voice-style-chip]");
  }

  async goto(params?: { lead?: string; channel?: string }) {
    const search = new URLSearchParams(params as any).toString();
    await this.page.goto(`/inbox${search ? "?" + search : ""}`);
  }

  async clickMode(mode: "adrian-decide" | "adrian-consulta" | "yo-escribo") {
    await this.page.locator(`[data-testid=segmented-mode] [data-mode=${mode}]`).click();
  }
}
```

## 13. Performance budgets

- LCP `/inbox` < 2.5s (skeleton inicial + first conv list batch).
- INP < 200ms (segmented control switch · filter chip click · message send).
- CLS < 0.1 (composer fixed bottom · sticky activity stream no shift).
- Virtualization en ConversationList si > 50 items (`react-window` or `@tanstack/react-virtual`).
- Memoization en ConversationItem (`React.memo` + selector React Query slice).

## 14. Test surfaces (TDD-mandatory · RED first)

- **Hooks** (`vitalia/frontend/src/features/inbox/api/__tests__/`):
  - `use-send-message.test.ts` (idempotency-key generation · optimistic update · OCC 409 rollback)
  - `use-retract-message.test.ts` (5min timer · adapter success · adapter failure fallback)
  - `use-set-mode.test.ts` (optimistic + rollback SC-03)
  - `use-activity-stream.test.ts` (poll 5s when expanded · stop when collapsed · sanitize payload)
  - `use-pause-adrian.test.ts`
  - `use-proactive-outbound.test.ts`

- **Components** (`vitalia/frontend/src/features/inbox/components/__tests__/`):
  - `SegmentedControl3Modes.test.tsx` (3 states · keyboard nav · aria-checked)
  - `FilterChips.test.tsx` (single-active per dimension · clear all · collapsible "Más")
  - `VoiceMessagePlayer.test.tsx` (play/pause · scrubber · speed · transcript display · fallback noTranscription)
  - `ImageAnalysisCard.test.tsx` (stub render · placeholder mock)
  - `AdrianToolsSheet.test.tsx` (read-only · disabled tool with explanation · link /offer-studio)
  - `AgentActivityStream.test.tsx` (sticky 32px · expand 240px · 8 events scrollable · empty state)
  - `ActionReceiptUndoChip.test.tsx` (countdown 5min · expired hide · click confirm modal · retract dispatch)
  - `ContactSidebar.test.tsx` (PiiMaskedSpan reveal triggers audit · RequireRole hides for marketing role)
  - `ProactiveOutboundModal.test.tsx` (contact picker · template picker · preview WA · ComplianceService gate on marketing template without opt-in)
  - `ConversationList.test.tsx` (filter chips applied · virtualization · empty state per filter)
  - `MessageBubble.test.tsx` (audio render · image stub · ActionReceipt undo chip inline)
  - `PauseAdrianConfirmModal.test.tsx`

- **E2E** (`vitalia/frontend/e2e/specs/smoke/inbox.smoke.spec.ts`):
  - SC-01 happy path
  - SC-02 audio fallback (mock Whisper 0 confidence)
  - Cross-tenant deny (URL manipulation)

## 15. References

- `01-spec-extract.md` · `02-design-ui.md` · `03-arch.md`
- `vitalia/frontend/src/app/globals.css` (CSS vars cementados)
- `vitalia/docs/architecture/design-system.md`
- `nicolify/frontend/src/features/{closer-studio,crm-hub,copilot}/` (REUSE adapter source)
- `vitalia/frontend/src/components/shared/{phi,agents,activity-stream,contact-sidebar,shell}/` (Story 11 cement)
