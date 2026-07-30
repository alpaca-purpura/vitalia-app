# vitalia-ux-discovery — Frontend sub-architecture

> **Consumer:** `builder-frontend` (Sonnet build) + `auditor-frontend` (Opus audit).
> **Index:** `03-arch.md` § 0-10 (read first).
> **Brand surface:** `vitalia/frontend/src/**` (Next.js 16 App Router · FSD-Lite).
> **Port:** 3002 dev (per `brand.yaml::infra.dev.frontend_port`).
> **Design tokens SSoT:** `vitalia/docs/architecture/design-system.md` (HEX → CSS vars → Tailwind classes).

## 1. Module structure (FSD-Lite per `.claude/rules/frontend-fsd.md`)

```
vitalia/frontend/src/
├── app/                                    ← Next.js App Router (thin)
│   ├── layout.tsx                          ← Shell + fonts + globals.css + Clerk provider
│   ├── globals.css                         ← :root CSS vars per design-system.md § 4
│   ├── (app)/                              ← Authenticated routes group
│   │   ├── layout.tsx                      ← Sidebar 240px + TopBar + Copilot rail 80px idle
│   │   ├── inbox/page.tsx                  ← /inbox
│   │   ├── pipeline/page.tsx               ← /pipeline
│   │   ├── agenda/page.tsx                 ← /agenda
│   │   ├── fidelizacion/page.tsx           ← /fidelización
│   │   └── marketing/page.tsx              ← /marketing
│   └── (onboarding)/
│       └── onboarding/page.tsx             ← Wizard chat-LEFT 50/50
├── components/
│   ├── ui/                                 ← Shadcn primitives (REUSE @luana/ui-kit)
│   └── shared/                             ← Vitalia-wide cross-feature components
│       ├── agents/
│       │   ├── AgentAvatar.tsx             ← NEW Slice 1 (avatar circular gradient)
│       │   ├── AgentAttribution.tsx        ← NEW Slice 1
│       │   ├── agent-names.ts              ← agentNameByRole mapping
│       │   └── index.ts                    ← Public API
│       ├── phi/
│       │   ├── PiiMaskedSpan.tsx           ← NEW Slice 1
│       │   ├── RequireRole.tsx             ← NEW Slice 1
│       │   ├── AuditedSection.tsx          ← NEW Slice 1
│       │   └── index.ts
│       ├── contact-sidebar/
│       │   ├── ContactSidebar.tsx          ← NEW Slice 1 PHI-aware (lift candidate Slice 2)
│       │   └── index.ts
│       ├── nps/
│       │   ├── NPSTagBadge.tsx             ← NEW Slice 1
│       │   └── index.ts
│       ├── activity-stream/
│       │   ├── ActivityStreamSticky.tsx    ← NEW Slice 1 (32px expand 240px)
│       │   └── index.ts
│       ├── copilot-rail/
│       │   ├── CopilotRail.tsx             ← NEW Slice 1 (80px idle / 460px chat)
│       │   ├── CopilotChat.tsx             ← REUSE adapter Nicolify copilot components
│       │   └── index.ts
│       ├── shell/
│       │   ├── AppShell.tsx                ← NEW Slice 1 (sidebar + topbar + main + rail)
│       │   ├── Sidebar.tsx                 ← NEW Slice 1 (240px nav)
│       │   ├── TopBar.tsx                  ← NEW Slice 1
│       │   └── index.ts
│       └── microcopy/
│           └── README.md                   ← Doc: copy.ts pattern per feature
├── features/
│   ├── inbox/
│   │   ├── api/                            ← React Query hooks
│   │   │   ├── use-conversations.ts
│   │   │   ├── use-conversation-detail.ts
│   │   │   ├── use-send-message.ts
│   │   │   ├── use-retract-message.ts
│   │   │   ├── use-pause-adrian.ts
│   │   │   ├── use-activity-stream.ts
│   │   │   ├── use-proactive-outbound.ts
│   │   │   └── use-transcribe-audio.ts
│   │   ├── components/
│   │   │   ├── InboxLayout.tsx
│   │   │   ├── ConversationList.tsx        ← REUSE adapter closer-studio Nicolify
│   │   │   ├── ConversationThread.tsx      ← REUSE adapter
│   │   │   ├── MessageBubble.tsx           ← REUSE adapter
│   │   │   ├── MessageInput.tsx            ← REUSE adapter (composer + attach)
│   │   │   ├── SegmentedControl3Modes.tsx  ← NEW (Adrián decide / consulta / Yo escribo)
│   │   │   ├── PauseAdrianButton.tsx       ← NEW
│   │   │   ├── FilterChips.tsx             ← NEW Vitalia
│   │   │   ├── VoiceMessagePlayer.tsx      ← NEW Slice 1
│   │   │   ├── ImageAnalysisCard.tsx       ← NEW Slice 1 (stub UI)
│   │   │   ├── AdrianToolsSheet.tsx        ← NEW (read-only)
│   │   │   ├── ActionReceiptUndoChip.tsx   ← NEW (5min undo)
│   │   │   ├── ProactiveOutboundModal.tsx  ← NEW Slice 1 cross-link
│   │   │   └── index.ts
│   │   ├── hooks/
│   │   ├── store/                          ← Zustand store (mode_filter, expanded_panels)
│   │   │   └── inbox-store.ts
│   │   ├── types/
│   │   ├── copy.ts                         ← INBOX_COPY constants LatAm neutro
│   │   └── index.ts
│   ├── pipeline/
│   │   ├── api/use-leads.ts, use-move-lead.ts, use-pipeline-summary.ts, use-screening.ts
│   │   ├── components/
│   │   │   ├── PipelineLayout.tsx
│   │   │   ├── PipelineBoard.tsx           ← REUSE adapter closer-studio Nicolify
│   │   │   ├── PipelineColumn.tsx          ← REUSE adapter
│   │   │   ├── PipelineCard.tsx            ← REUSE adapter + 3-state expand
│   │   │   ├── PipelineHeaderMetrics.tsx   ← NEW
│   │   │   ├── PipelineFilters.tsx         ← NEW
│   │   │   ├── StageAttributionChip.tsx    ← NEW
│   │   │   ├── ScreeningChip.tsx           ← NEW
│   │   │   ├── DepositBadge.tsx            ← NEW (diferenciador MUST #2 visible)
│   │   │   ├── AutoMoveFlashToast.tsx      ← NEW
│   │   │   └── index.ts
│   │   ├── store/pipeline-store.ts
│   │   ├── copy.ts                         ← PIPELINE_COPY
│   │   └── index.ts
│   ├── agenda/
│   │   ├── api/use-agenda-slots.ts, use-create-appointment.ts, use-cobro-saldo.ts, use-reschedule.ts, use-cancel.ts, use-fiscal-emit.ts
│   │   ├── components/
│   │   │   ├── AgendaLayout.tsx
│   │   │   ├── AgendaWeekGrid.tsx          ← NEW
│   │   │   ├── AgendaDayView.tsx           ← NEW
│   │   │   ├── AgendaMonthView.tsx         ← REUSE CalendarWidget Nicolify
│   │   │   ├── AgendaSlot.tsx              ← NEW color-coded balance_status
│   │   │   ├── AgendaContactSidebar.tsx    ← REUSE shared ContactSidebar + PHI wrappers
│   │   │   ├── PaymentSubform.tsx          ← NEW 3 capas cobranza
│   │   │   ├── CreateAppointmentDrawer.tsx ← NEW
│   │   │   ├── WalkInForm.tsx              ← NEW Slice 1
│   │   │   ├── PhoneManualForm.tsx         ← NEW Slice 1
│   │   │   ├── RescheduleConfirmModal.tsx  ← NEW
│   │   │   ├── CancelAppointmentModal.tsx  ← NEW
│   │   │   ├── ReceiptPrintButton.tsx      ← NEW (window.print() Slice 1)
│   │   │   ├── FiscalEmissionToggle.tsx    ← NEW (Nubefact PE Slice 1 feature flag)
│   │   │   └── index.ts
│   │   ├── store/agenda-store.ts
│   │   ├── copy.ts                         ← AGENDA_COPY
│   │   └── index.ts
│   ├── fidelizacion/
│   │   ├── api/use-re-engagement-patterns.ts, use-send-proactive-template.ts, use-pause-patient.ts, use-nps-responses.ts
│   │   ├── components/
│   │   │   ├── FidelizacionLayout.tsx
│   │   │   ├── FidelizacionKPIsHero.tsx    ← NEW
│   │   │   ├── FidelizacionTabsBar.tsx     ← NEW 5 tabs
│   │   │   ├── MultiSessionTab.tsx         ← NEW
│   │   │   ├── FollowUpTab.tsx             ← NEW
│   │   │   ├── MaintenanceTab.tsx          ← NEW
│   │   │   ├── AbsenceTab.tsx              ← NEW
│   │   │   ├── NPSResumenTab.tsx           ← NEW Slice 1 reduced stat card
│   │   │   ├── ReEngagementCard.tsx        ← NEW adaptive per pattern
│   │   │   ├── ReEngagementContactSidebar.tsx
│   │   │   ├── SuggestSlotsModal.tsx       ← NEW
│   │   │   ├── PausePatientModal.tsx       ← NEW
│   │   │   ├── ConfirmTemplateModal.tsx    ← NEW
│   │   │   └── index.ts
│   │   ├── store/fidelizacion-store.ts
│   │   ├── copy.ts                         ← FIDELIZACION_COPY
│   │   └── index.ts
│   ├── marketing/
│   │   ├── api/use-bowtie-summary.ts, use-stage-detail.ts, use-channel-detail.ts, use-lucas-recommendations.ts, use-approve-recommendation.ts, use-attribution-matrix.ts, use-referrals.ts
│   │   ├── components/
│   │   │   ├── MarketingLayout.tsx
│   │   │   ├── MarketingBowtieSVG.tsx      ← REUSE adapter growth-studio strategy-canvas (pixel-invariante)
│   │   │   ├── StageDispatcher.tsx         ← REUSE adapter
│   │   │   ├── AttractionStage.tsx         ← REUSE direct (AttractionScorecards + TrendChart + ChannelRow widgets)
│   │   │   ├── QualificationStage.tsx      ← REUSE adapter
│   │   │   ├── ReservationStage.tsx        ← NEW + AttributionMatrixWidget
│   │   │   ├── AdoptionStage.tsx           ← REUSE adapter (AdoptionDetail)
│   │   │   ├── ExpansionStage.tsx          ← NEW + ReferralsWidget
│   │   │   ├── LucasStageRecommendationsCard.tsx  ← NEW ★ protagonista (3 cards sticky top per stage)
│   │   │   ├── LucasRecommendationDetailModal.tsx ← NEW
│   │   │   ├── LucasApprovalModal.tsx      ← NEW
│   │   │   ├── AttributionMatrixWidget.tsx ← NEW Slice 1 (4 origins Stage Reserva)
│   │   │   ├── ReferralsWidget.tsx         ← NEW Slice 1 (Stage Expansión)
│   │   │   ├── ChannelDetailSidebar.tsx    ← REUSE adapter simplified 3 sections
│   │   │   ├── ChannelConnectionWizard.tsx ← NEW simplified 3 steps
│   │   │   ├── BottleneckBannerAdapter.tsx ← REUSE adapter Lucas-styled
│   │   │   └── index.ts
│   │   ├── store/marketing-store.ts
│   │   ├── copy.ts                         ← MARKETING_COPY
│   │   └── index.ts
│   └── onboarding/
│       ├── api/use-extract-tenant-context.ts, use-onboarding-progress.ts, use-confirm-slot.ts, use-simulate-voice.ts, use-complete-onboarding.ts, use-transcribe-audio.ts
│       ├── components/
│       │   ├── WizardOnboardingLayout.tsx  ← NEW (chat-LEFT 50/50 split)
│       │   ├── WizardChatThread.tsx        ← REUSE adapter Nicolify copilot conv UI
│       │   ├── SlotTrackerSticky.tsx       ← NEW
│       │   ├── ModeSelector.tsx            ← NEW (libre / guiado)
│       │   ├── SlotConfirmInline.tsx       ← NEW
│       │   ├── LiveWhatsAppPreview.tsx     ← NEW (debounced 1.5s)
│       │   ├── LiveLandingSnippetPreview.tsx ← NEW
│       │   ├── CloseSetupWarningModal.tsx  ← NEW
│       │   ├── WizardCompletionTransition.tsx ← NEW (morph 400ms transition)
│       │   └── index.ts
│       ├── store/onboarding-store.ts
│       ├── copy.ts                         ← ONBOARDING_COPY
│       └── index.ts
├── lib/
│   ├── api/
│   │   ├── fetchClient.ts                  ← Auto-injects X-Tenant-ID + X-Clinic-ID from Clerk JWT
│   │   └── react-query-client.ts
│   ├── tokens/                             ← Design tokens consumers (HEX→CSS vars)
│   ├── format/
│   │   ├── formatMoney.ts                  ← (amount, currency) — never hardcoded
│   │   ├── formatTenantDate.ts
│   │   ├── formatTenantDateTime.ts
│   │   └── formatTenantRelative.ts
│   ├── zod-schemas/                        ← Shared Zod schemas (forms)
│   └── nuqs-parsers/                       ← Shared nuqs parsers per feature
├── hooks/                                  ← Global hooks
│   ├── useTenantLocale.ts                  ← {currency, timezone, country, city}
│   ├── useCurrentUser.ts                   ← From Clerk
│   ├── useClinicId.ts
│   ├── useFeatureFlag.ts                   ← Reads brand.yaml feature flags
│   └── usePiiRoleGate.ts                   ← Boolean: can current user see PHI?
├── e2e/
│   ├── auth.fixture.ts                     ← Clerk testing token fixture
│   ├── fixtures/
│   ├── pages/                              ← POMs
│   │   ├── inbox.page.ts
│   │   ├── pipeline.page.ts
│   │   ├── agenda.page.ts
│   │   ├── fidelizacion.page.ts
│   │   ├── marketing.page.ts
│   │   └── wizard-onboarding.page.ts
│   └── specs/
│       └── smoke/
│           ├── inbox.smoke.spec.ts
│           ├── pipeline.smoke.spec.ts
│           ├── agenda.smoke.spec.ts
│           ├── fidelizacion.smoke.spec.ts
│           ├── marketing.smoke.spec.ts
│           └── wizard-onboarding.smoke.spec.ts
├── __tests__/
│   └── architecture/
│       ├── test_no_hardcoded_colors.test.ts
│       ├── test_no_hardcoded_strings.test.ts
│       ├── test_fsd_boundaries.test.ts
│       ├── test_no_cross_feature_imports.test.ts
│       ├── test_server_first.test.ts
│       ├── test_phi_pii_components_used.test.ts
│       ├── test_no_voseo_in_copy.test.ts
│       └── test_page_padding.test.ts
└── .storybook/                             ← Storybook config (NEW Slice 1)
    ├── main.ts
    └── preview.ts
```

## 2. TypeScript types (mirror Pydantic DTOs)

Auto-generated TS types from OpenAPI spec via `openapi-typescript` (per `frontend-expert`). Manual override allowed for complex unions. camelCase mirror snake_case BE. ISO 8601 datetimes as `string`.

```ts
// vitalia/frontend/src/features/agenda/types/appointment.ts
export type AppointmentOrigin = "sales_agent" | "walk_in" | "phone_manual" | "proactive_outbound";
export type BalanceStatus = "pending" | "deposit_paid" | "full_paid" | "refunded";

export type Appointment = {
  id: string;
  tenantId: string;
  clinicId: string;
  patientId: string;
  doctorId: string | null;
  offerId: string | null;
  startsAt: string;  // ISO 8601 UTC
  endsAt: string;
  origin: AppointmentOrigin;
  balanceStatus: BalanceStatus;
  followUpDueAt: string | null;
  followUpReason: string | null;
  completedAt: string | null;
  utmSource: string | null;
  utmCampaign: string | null;
  currency: string | null;  // explicit per master-data.md
  createdAt: string;
  updatedAt: string;
};

export type LucasRecommendation = {
  id: string;
  tenantId: string;
  clinicId: string;
  stage: "attraction" | "qualification" | "reservation" | "adoption" | "expansion";
  recommendationKind: string;
  title: string;
  body: string;
  rationaleJson: Record<string, unknown>;
  priority: number;
  status: "open" | "approved" | "rejected" | "expired" | "undone";
  approvedByUserId: string | null;
  approvedAt: string | null;
  undoUntil: string | null;
  expiresAt: string;
  createdAt: string;
};
```

## 3. URL state SSoT (nuqs + Next.js 16 App Router)

Per spec § Layout phases cementado Batch 1:
- **nuqs** (search params type-safe) is the URL SSoT
- **push** for inter-route nav (between P1 routes)
- **replace** for intra-state (filter changes, selected ID, expanded card, modals)
- **Event-based chat context refresh** — each URL change emits event to copilot chat backend

Per-route nuqs schemas (declared in `features/{route}/types/url-state.ts`):

### 3.1 /inbox URL state

```ts
// features/inbox/types/url-state.ts
export const inboxParsers = {
  mode: parseAsStringEnum(["adrian_decide", "adrian_consulta", "yo_escribo"]).withDefault("adrian_decide"),
  channel: parseAsStringEnum(["whatsapp", "instagram", "email", "web"]).withOptions({ clearOnDefault: true }),
  status: parseAsStringEnum(["all", "unread", "needs_help", "media_unread"]).withDefault("all"),
  period: parseAsStringEnum(["today", "7d", "30d", "all"]).withDefault("7d"),
  convId: parseAsString,
  expandedFilters: parseAsBoolean.withDefault(false),
  activityExpanded: parseAsBoolean.withDefault(false),
  proactiveModal: parseAsBoolean.withDefault(false),
  toolsSheetOpen: parseAsBoolean.withDefault(false),
};
```

### 3.2 /pipeline URL state

```ts
export const pipelineParsers = {
  view: parseAsStringEnum(["kanban"]).withDefault("kanban"),  // Slice 1 only kanban
  offer: parseAsString,
  channel: parseAsString,
  period: parseAsStringEnum(["today", "7d", "30d", "all"]).withDefault("30d"),
  expandedCard: parseAsString,  // lead_id
};
```

### 3.3 /agenda URL state

```ts
export const agendaParsers = {
  view: parseAsStringEnum(["week", "day", "month"]).withDefault("week"),
  date: parseAsIsoDate.withDefault(new Date()),
  doctor: parseAsString,
  specialty: parseAsString,
  statusPago: parseAsStringEnum(["all", "deposit_paid", "full_paid", "pending"]).withDefault("all"),
  onlyWalkin: parseAsBoolean.withDefault(false),
  selectedSlot: parseAsString,  // appt_id
  drawer: parseAsStringEnum(["walkin", "phonemanual", "proactive"]),
};
```

### 3.4 /fidelización URL state (7 params)

```ts
export const fidelizacionParsers = {
  tab: parseAsStringEnum(["multisession", "followup", "maintenance", "absence", "nps"]).withDefault("multisession"),
  period: parseAsStringEnum(["7d", "30d", "90d"]).withDefault("30d"),
  vertical: parseAsString,
  doctor: parseAsString,
  urgency: parseAsStringEnum(["high", "medium", "low"]),
  selectedPatient: parseAsString,
  modal: parseAsStringEnum(["confirmtemplate", "suggestslots", "pause"]),
};
```

### 3.5 /marketing URL state (7 params)

```ts
export const marketingParsers = {
  tab: parseAsStringEnum(["attraction", "qualification", "reservation", "adoption", "expansion"]).withDefault("attraction"),
  period: parseAsStringEnum(["7d", "30d", "90d"]).withDefault("30d"),
  channel: parseAsString,  // provider+slug
  selectedRecommendation: parseAsString,
  approvalModal: parseAsBoolean.withDefault(false),
  channelDetailSidebar: parseAsString,
  connectionWizard: parseAsStringEnum(["meta_ads", "google_ads"]),
};
```

### 3.6 Wizard onboarding URL state (replace intra-wizard)

```ts
export const onboardingParsers = {
  step: parseAsString.withDefault("greet"),
  mode: parseAsStringEnum(["libre", "guiado"]),
  draftId: parseAsString,
};
```

## 4. React Query data layer

All hooks pattern `use{Entity}{Action}.ts`. Per `frontend-expert::api-standards.md`:

```ts
// features/marketing/api/use-lucas-recommendations.ts
import { useQuery } from "@tanstack/react-query";
import { fetchClient } from "@/lib/api/fetchClient";

export function useLucasRecommendations(params: {
  stage?: string;
  status?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["marketing", "lucas-recommendations", params],
    queryFn: () => fetchClient.get<LucasRecommendationsResponse>("/api/v1/vitalia/marketing/recommendations", { params }),
    staleTime: 5 * 60 * 1000,  // 5min stale (Lucas regenerates daily cron)
  });
}
```

Mutations:
```ts
// features/marketing/api/use-approve-recommendation.ts
export function useApproveRecommendation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (rec_id: string) => fetchClient.post(
      `/api/v1/vitalia/marketing/recommendations/${rec_id}/approve`,
      {},
      { headers: { "Idempotency-Key": crypto.randomUUID() } }  // idempotent retries
    ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["marketing", "lucas-recommendations"] }),
  });
}
```

## 5. Forms (RHF + Zod)

Pattern per `frontend-expert::component-rules.md`:

```ts
// features/agenda/components/WalkInForm.tsx
const walkInSchema = z.object({
  patientId: z.string().uuid().nullable(),
  patientName: z.string().min(2),  // if new patient
  patientDni: z.string().min(8),
  service: z.string().uuid(),
  doctor: z.string().uuid(),
  startsAt: z.string().datetime(),
  cobroOption: z.enum(["now", "after", "skip"]),
  amount: z.number().positive().optional(),
  currency: z.string().length(3).optional(),
});

export function WalkInForm() {
  const form = useForm<z.infer<typeof walkInSchema>>({
    resolver: zodResolver(walkInSchema),
  });
  // ...
}
```

## 6. Storybook (NEW Slice 1 obligatorio)

Per spec § Handoff #8. Components requiring stories:

| Component | Variants/States |
|---|---|
| `AgentAvatar` | valeria, adrian, lucas, sistema (per `agentNameByRole`) × sm/md/lg |
| `LucasStageRecommendationsCard` | 4 estados: open, approved (5min undo visible), rejected, expired |
| `MarketingBowtieSVG` | 5 stages active (one per story) + responsive breakpoints |
| `ChannelBreakdownRow` | normal · cost overrun · disconnected |
| `AttributionMatrixWidget` | 4 origins × period 7d/30d/90d |
| `ContactSidebar` | masked PHI · full PHI (audit-aware) · with patient · without patient |
| `WizardChatThread` | empty · slot pending · slot confirmed · agent thinking · agent failed |
| `DepositBadge` | 30% paid · full paid · pending |
| `AgentAttribution` | per agent × via channels |
| `PiiMaskedSpan` | dni · phone · email · full (role check on) |
| `RequireRole` | doctor allowed · denied state |
| `ActivityStreamSticky` | collapsed (32px) · expanded (240px) · loading · empty |

Storybook setup: `vitalia/frontend/.storybook/{main.ts,preview.ts}` + Chromatic integration for visual regression (per `04-validators.yaml::visual`).

## 7. Component decisions (REUSE vs NEW)

Per spec § Components mapping consolidado:

### 7.1 REUSE Nicolify (fork físico Slice 1 — ADR-vitalia-001)

Each REUSE component undergoes pre-fork audit:
1. Identify component path in `nicolify/frontend/src/features/{closer-studio,brand-studio,growth-studio,sales}/`
2. Copy to `vitalia/frontend/src/features/{target}/components/` (or `components/shared/` if cross-feature)
3. Replace token literals (`purple-600`, `slate-100`, hex literals) → Vitalia tokens (`vitalia-azul-marino`, `vitalia-muted`, CSS vars)
4. Wrap PHI surfaces with `<PiiMaskedSpan>` / `<RequireRole>` / `<AuditedSection>` per `hipaa-lite.md`
5. Replace hardcoded strings → `INBOX_COPY.{namespace}.{key}` (or feature-equivalent)
6. Server-First default — `"use client"` only on leaf nodes with state/handlers
7. Adapt API hooks to Vitalia endpoints

### 7.2 REUSE engine direct (no fork)

- `style_analyzer` LangGraph agent (wizard onboarding) — invoke via `core/luana-core-brand-studio/` endpoints via port (NEW lift candidate `shared/links/ports/brand_studio.py`)
- `personality_service` (compile + simulate) — idem
- `voice_fidelity/grader` — idem
- `brand_data_adapter` — extend Vitalia for medical vertical via Extension SDK EP

Frontend hooks consume these via REST endpoints (no engine code import — engine is BE).

### 7.3 NEW Vitalia Slice 1

Per spec § Components mapping NEW table — ~20+ components. All have arch-fitness coverage + Storybook stories.

## 8. Arch fitness tests (`vitalia/frontend/src/__tests__/architecture/`)

### 8.1 `test_no_hardcoded_colors.test.ts` (NEW Slice 1)

Greps for HEX literal patterns in `.tsx`/`.ts` outside `app/globals.css`:
```ts
test("no hardcoded HEX colors outside globals.css", async () => {
  const files = await glob("vitalia/frontend/src/**/*.{tsx,ts}");
  const HEX_PATTERN = /#[0-9A-Fa-f]{3,8}\b/;
  const offenders = [];
  for (const file of files) {
    if (file.endsWith("globals.css")) continue;
    const content = await fs.readFile(file, "utf-8");
    if (HEX_PATTERN.test(content)) offenders.push(file);
  }
  expect(offenders).toHaveLength(0);  // allowlist shrinks only
});
```

### 8.2 `test_no_hardcoded_strings.test.ts` (NEW Slice 1)

User-facing strings MUST live in `<feature>/copy.ts`. Greps `<p>`, `<span>`, `<button>` children for non-token, non-variable strings.

### 8.3 `test_fsd_boundaries.test.ts`

ESLint plugin `boundaries` enforces matrix per `frontend-fsd.md` § Boundary matrix.

### 8.4 `test_no_cross_feature_imports.test.ts`

Greps `import .* from "@/features/X"` in `features/Y/` (X !== Y). Public API via `index.ts` only.

### 8.5 `test_server_first.test.ts`

Greps `"use client"` directive. Allowlist (shrink only) for nodes that need it (state/handlers).

### 8.6 `test_phi_pii_components_used.test.ts` (NEW Slice 1)

For each `.tsx` containing `patient.dni|patient.phone|patient.email|diagnosis|treatment_plan`, MUST be wrapped in `<PiiMaskedSpan>` or `<RequireRole>` or `<AuditedSection>`.

### 8.7 `test_no_voseo_in_copy.test.ts` (NEW Slice 1)

For each `<feature>/copy.ts`, parse object values, run voseo glossary scanner per `.claude/rules/spanish-text.md` § R2.

### 8.8 `test_page_padding.test.ts` (EXISTING)

Studio page layouts consistent padding tokens.

## 9. E2E smoke tests (Playwright per `playwright-expert`)

Per `04-validators.yaml::functional::e2e`:

- `inbox.smoke.spec.ts` — happy path: load inbox · filter chip · open conv · send message
- `pipeline.smoke.spec.ts` — happy path: load pipeline kanban · expand card hover · check deposit badge visible
- `agenda.smoke.spec.ts` — happy path: load week · click empty slot · open walk-in drawer · save manual cash
- `fidelizacion.smoke.spec.ts` — happy path: load fidelización · click tab MultiSession · click ReEngagementCard · open ConfirmTemplateModal · cancel
- `marketing.smoke.spec.ts` — happy path: load marketing · bowtie SVG render · click stage tab · Lucas card visible · click recommendation detail modal · close
- `wizard-onboarding.smoke.spec.ts` — happy path: start onboarding · greet → confirm slot tenant.name inline · live preview WhatsApp visible · complete wizard

All specs use Clerk auth fixture + `E2E_BASE_URL=http://localhost:3002`. Native execution (NEVER Docker per `e2e-testing.md`).

## 10. Performance budgets (per `03-arch.md § 5`)

| Metric | Budget | Validator |
|---|---|---|
| LCP | < 2.5s | `lighthouse-ci` per route |
| INP | < 200ms | `web-vitals` reporting |
| CLS | < 0.1 | `lighthouse-ci` |
| Bowtie SVG bundle | < 30KB gzipped | Webpack bundle analyzer |
| Lucas card lazy-load | below fold | React `Suspense` + intersection observer |
| Wizard simulate-voice | debounced 1.5s + throttle 5/min | Hook implementation |

## 11. A11y (WCAG 2.1 AA per `03-arch.md § 7 #11`)

- Bowtie SVG with `<title>` + `aria-labelledby`
- Lucas cards keyboard nav (Tab between cards, Enter to detail modal)
- Contrast ratios validated cross-tokens (CI: `@axe-core/playwright` per E2E spec)
- All interactive elements `aria-label`-ed
- Color NOT sole indicator (icons + text + color combo for status)
- `prefers-reduced-motion` fallback for morph transition wizard→app

## 12. Cross-cutting concerns (FE-specific)

- **`fetchClient`** auto-injects `X-Tenant-ID` + `X-Clinic-ID` from Clerk JWT — no manual passing
- **NO `any`** — use `unknown` + type guards per `frontend-expert::constraints`
- **NO default exports** (except Next pages) — named exports for tree-shake
- **React Query stale times** documented per hook (don't default 0)
- **Server Components default** — `"use client"` boundary minimized
- **`cn()` from `lib/utils.ts`** for Tailwind class composition — no helper duplicates
- **`formatMoney(amount, currency)`** ALWAYS — never `${amount} USD`
- **Tokens-only** — HEX literales prohibited outside `globals.css`
- **microcopy in copy.ts** — arch fitness enforced
- **Spanish neutro tuteo** — NO voseo (except Adrián output respects tenant config — backend concern)

## 13. Test surfaces (TDD-mandatory)

| Layer | Test file pattern | RED first |
|---|---|---|
| Hooks (React Query) | `features/{m}/api/__tests__/use-*.test.ts` | YES |
| Components | `features/{m}/components/__tests__/{Comp}.test.tsx` | YES |
| Store (Zustand) | `features/{m}/store/__tests__/{m}-store.test.ts` | YES |
| E2E smoke | `e2e/specs/smoke/{route}.smoke.spec.ts` | YES |
| Visual regression | Chromatic snapshots (Storybook) | NO (snapshot first) |
| Architecture fitness | `__tests__/architecture/test_*.test.ts` | YES (allowlist shrinkage) |

Coverage threshold: 20% FE (per `.claude/rules/frontend-quality.md`). Slice 1 target ≥ 30% per feature.

## 14. Anti-patterns (per spec § Handoff #6 — tabla 13 Nicolify NO replicar)

NEVER replicate from Nicolify:
1. 4-tier loading over-engineered (use 1-2 tiers max for Slice 1)
2. Sidebar mega-detailed 8 tabs per channel — Vitalia uses 3 sections drill
3. 13 hooks dispersos — consolidate to ≤ 5 per feature
4. 8 endpoints separated — bundle to 1-2 per resource
5. `ChannelGroupCard` artificial category — direct list flat Slice 1
6. `OfferLadder` too abstract — use medical_services_v1 preset directly
7. `BenchmarkBadge` without data — defer Slice 2 cuando data benchmarks salud LATAM
8. `LazyChannelGroup` tier loading — Suspense + intersection observer simpler
9. `_CATALOG_VERSION` bump manual — automated via build script
10. `useCopilotOffset` coupling — Copilot rail self-contained
11. Lazy-loading sin error boundary — always wrap with `<ErrorBoundary>`
12. Hard-coded slugs literales — use registries
13. Cross-feature imports sin port — `index.ts` Public API mandatory
14. Component naming por implementación — name by domain semantics

