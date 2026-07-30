# vitalia-slice-1-fidelizacion — Frontend sub-architecture

> **Consumer:** `builder-frontend` (Sonnet build) + `auditor-frontend` (Opus audit).
> **Index:** `03-arch.md` § 0-9 (read first).
> **Brand surface:** `vitalia/frontend/src/features/fidelizacion/**` + `vitalia/frontend/src/components/shared/nps/` + `vitalia/frontend/e2e/{pages,specs}/fidelizacion*`.
> **Port:** 3002 dev. **Tokens SSoT:** `vitalia/frontend/src/app/globals.css` (cementado).

## 1. Module structure (FSD-Lite per `.claude/rules/frontend-fsd.md`)

```
vitalia/frontend/src/features/fidelizacion/
├── api/                                        ← React Query hooks
│   ├── use-fidelizacion-summary.ts             ← KPIs hero
│   ├── use-re-engagement-patterns.ts           ← Listings per tab
│   ├── use-nps-responses.ts                    ← NPS tabla reducida
│   ├── use-activity-stream.ts                  ← Activity footer
│   ├── use-send-proactive-template.ts          ← Mutation Adrián recordatorio
│   ├── use-pause-patient.ts                    ← Mutation pause
│   ├── use-mark-external.ts                    ← Mutation silence external
│   ├── use-mark-no-continue.ts                 ← Mutation marcar paciente decidió no
│   ├── use-log-manual-call.ts                  ← Mutation registrar llamada
│   ├── use-availability-slots.ts               ← CONSUME desde /agenda module (Public API)
│   └── index.ts
├── components/
│   ├── FidelizacionLayout.tsx                  ← Page orchestrator
│   ├── FidelizacionKPIsHero.tsx                ← 5 stat cards
│   ├── FidelizacionTabsBar.tsx                 ← 5 tabs vertical Shadcn
│   ├── FidelizacionActivityFooter.tsx          ← Sticky bottom activity
│   ├── tabs/
│   │   ├── MultiSessionTab.tsx
│   │   ├── FollowUpTab.tsx
│   │   ├── MaintenanceTab.tsx
│   │   ├── AbsenceTab.tsx
│   │   └── NPSResumenTab.tsx
│   ├── ReEngagementCard.tsx                    ← Polymorphic 4 variantes
│   ├── NPSRowCompact.tsx                       ← NPS tabla row
│   ├── ReEngagementContactSidebar.tsx          ← Composes shared <ContactSidebar>
│   ├── ConfirmTemplateModal.tsx                ← Adrián recordatorio confirm
│   ├── SuggestSlotsModal.tsx                   ← Calendar mini + 3-5 slots
│   ├── PausePatientModal.tsx                   ← Duración + razón
│   ├── ManualCallLoggedModal.tsx               ← Notas + outcome radio
│   ├── *.stories.tsx                           ← Storybook coverage mandatory
│   └── index.ts                                ← Public API
├── hooks/
│   ├── use-fidelizacion-store.ts               ← Zustand slice
│   └── use-fidelizacion-url-state.ts           ← nuqs wrapper
├── store/
│   └── fidelizacion-store.ts                   ← Zustand: ephemeral UI state (selectedPattern, expandedCardId, etc.)
├── types/
│   ├── re-engagement.ts                        ← TS types mirror Pydantic DTOs (camelCase)
│   ├── nps.ts
│   ├── fidelizacion-summary.ts
│   └── url-state.ts                            ← fidelizacionParsers (nuqs)
├── copy.ts                                     ← FIDELIZACION_COPY constants LatAm neutro
└── index.ts                                    ← Public API (re-exports)

vitalia/frontend/src/components/shared/nps/
├── NPSTagBadge.tsx                             ← Cross-feature chip (verde/amarillo/rojo per band)
├── NPSTagBadge.stories.tsx
├── README.md                                   ← Doc + reuse cross-feature
└── index.ts

vitalia/frontend/e2e/
├── pages/
│   └── fidelizacion.page.ts                    ← POM
└── specs/
    ├── smoke/
    │   └── fidelizacion.smoke.spec.ts          ← Smoke /fidelización mount + tabs nav
    └── regression/
        ├── fidelizacion-multi-session-happy.spec.ts       ← SC-01
        ├── fidelizacion-absence-no-optin.spec.ts          ← SC-02
        ├── fidelizacion-follow-up-doctor-vencido.spec.ts  ← SC-03
        └── fidelizacion-adversarial.spec.ts               ← SC-04
```

## 2. TypeScript types (mirror Pydantic DTOs)

camelCase mirror snake_case BE. ISO 8601 datetimes as `string`. Explicit fields — no `any`.

```ts
// vitalia/frontend/src/features/fidelizacion/types/re-engagement.ts

export type ReEngagementPattern = "multi_session" | "follow_up" | "maintenance" | "absence" | "nps";
export type ReEngagementOutcome =
  | "sent"
  | "responded"
  | "rescheduled"
  | "declined"
  | "not_responsive"
  | "opted_out"
  | "failed_sending";

export type UrgencyLevel = "critical" | "alert" | "near" | "waiting" | "up_to_date";

export interface ReEngagementEvent {
  id: string;
  tenantId: string;
  clinicId: string;
  patientId: string;
  pattern: ReEngagementPattern;
  triggerSource: string;
  triggerAt: string;
  templateId: string | null;
  sentAt: string | null;
  responseAt: string | null;
  outcome: ReEngagementOutcome | null;
  convertedToAppointmentId: string | null;
  retryCount: number;
  lastError: string | null;
  createdAt: string;
}

export interface PatternRow {
  reEngagementEventId: string;
  patientId: string;
  patientName: string;                 // PHI — masked unless RequireRole guard passes
  pattern: ReEngagementPattern;
  urgency: UrgencyLevel;
  // pattern-specific fields (union)
  patternData: MultiSessionData | FollowUpData | MaintenanceData | AbsenceData;
  acciones: ActionDescriptor[];
}

export interface MultiSessionData {
  kind: "multi_session";
  offerLabel: string;
  sessionsCompleted: number;
  sessionsExpected: number;
  gapDays: number;
  lastSessionDate: string;
  doctorName: string;
}

export interface FollowUpData {
  kind: "follow_up";
  doctorName: string;
  followUpRequestedDuration: string;        // "3 meses" (formatted)
  followUpSetAt: string;
  followUpDueAt: string;
  daysUntilDue: number;                      // negative if past due
  followUpReason: string | null;
}

export interface MaintenanceData {
  kind: "maintenance";
  offerLabel: string;
  cadenceLabel: string;                      // "Cada 6 meses"
  lastServiceDate: string;
  monthsSinceLast: number;
  nextRecommendedDate: string;
  daysUntilDue: number;
}

export interface AbsenceData {
  kind: "absence";
  lastAppointmentDate: string;
  monthsInactive: number;
  lifetimeAppointments: number;
  lifetimeValueCents: number | null;
  currency: string | null;                   // explicit per master-data.md
  lastDoctorName: string;
  marketingOptIn: boolean;
}

export interface ActionDescriptor {
  id: "send_reminder" | "suggest_slots" | "pause_patient" | "mark_external" | "mark_no_continue" | "open_conversation" | "call_manually";
  enabled: boolean;
  disabledReason: string | null;            // e.g. "Paciente no aceptó marketing"
}

export interface SendProactiveRequest {
  templateId: string;
  pattern: ReEngagementPattern;
  slotValues: Record<string, string>;
  triggerSource: string;
}

export interface SendProactiveResponse {
  reEngagementEventId: string;
  status: ReEngagementOutcome;
  convId: string | null;
}

export interface PausePatientRequest {
  durationDays: number;                      // 7 | 30 | custom
  reason: string | null;
}

export interface PausePatientResponse {
  resumeAt: string;
}

// Mutation payloads, NPS types, summary types — análogos
```

```ts
// vitalia/frontend/src/features/fidelizacion/types/nps.ts
export type NPSBand = "promoter" | "passive" | "detractor";

export interface NPSRowDTO {
  id: string;
  patientName: string;                       // PHI — masked unless RequireRole
  score: number;
  band: NPSBand;
  commentShort: string | null;               // truncated 80 chars
  respondedAt: string;
  taggedInInbox: boolean;
}

export interface NPSSummaryResponse {
  averageScore: number;                      // 0-10 decimal
  totalResponses: number;
  rows: NPSRowDTO[];
}
```

```ts
// vitalia/frontend/src/features/fidelizacion/types/fidelizacion-summary.ts
export interface FidelizacionSummaryResponse {
  patientsInFollowup: number;
  nearAbandonment: number;
  returnRate: number;                        // 0.0-1.0
  reEngagedThisPeriod: number;
  npsAverage: number;
  npsResponsesCount: number;
  trendVsPreviousPeriod: {
    patientsInFollowup: number;
    nearAbandonment: number;
    returnRate: number;
    reEngagedThisPeriod: number;
    npsAverage: number;
  };
}
```

## 3. URL state (nuqs)

```ts
// vitalia/frontend/src/features/fidelizacion/types/url-state.ts
import { parseAsString, parseAsStringEnum, parseAsArrayOf } from 'nuqs';

export const fidelizacionParsers = {
  tab: parseAsStringEnum(['multisession', 'followup', 'maintenance', 'absence', 'nps']).withDefault('multisession'),
  period: parseAsStringEnum(['7d', '30d', '90d']).withDefault('30d'),
  vertical: parseAsString,
  doctor: parseAsString,
  urgency: parseAsArrayOf(parseAsStringEnum(['critical', 'alert', 'near', 'waiting', 'up_to_date'])),
  selectedPatient: parseAsString,
  pauseModal: parseAsString,
  confirmTemplateModal: parseAsString,
  manualCallModal: parseAsString,
  suggestSlotsModal: parseAsString,
};
```

Push history: `[Ver conversación →]` → `router.push('/inbox?lead={conv_id}')`. `[Ver turno]` → `router.push('/agenda?selectedSlot={appt_id}')`. Everything else = replace.

## 4. React Query hooks

```ts
// vitalia/frontend/src/features/fidelizacion/api/use-re-engagement-patterns.ts
import { useQuery } from '@tanstack/react-query';
import { fetchClient } from '@/lib/api/fetchClient';
import type { PatternRow } from '../types/re-engagement';

interface UseReEngagementPatternsArgs {
  pattern: ReEngagementPattern;
  vertical?: string;
  doctorId?: string;
  urgency?: UrgencyLevel[];
  period: '7d' | '30d' | '90d';
}

export function useReEngagementPatterns(args: UseReEngagementPatternsArgs) {
  return useQuery({
    queryKey: ['fidelizacion', args.pattern, args],
    queryFn: () => fetchClient.get<{ rows: PatternRow[] }>(`/api/v1/vitalia/fidelization/re-engagement/patterns`, {
      params: args,
    }),
    staleTime: 30_000,                                 // 30s
    refetchOnWindowFocus: true,
  });
}
```

Mutation pattern:

```ts
// use-send-proactive-template.ts
export function useSendProactiveTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (args: { patientId: string; payload: SendProactiveRequest }) => {
      const idempotencyKey = crypto.randomUUID();
      return fetchClient.post<SendProactiveResponse>(
        `/api/v1/vitalia/fidelization/patients/${args.patientId}/send-proactive`,
        args.payload,
        { headers: { 'Idempotency-Key': idempotencyKey } },
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fidelizacion'] });
      queryClient.invalidateQueries({ queryKey: ['inbox', 'conversations'] });
    },
  });
}
```

`useAvailabilitySlots` consume from `@/features/agenda` (Public API) — NOT direct deep import:

```ts
// vitalia/frontend/src/features/fidelizacion/api/use-availability-slots.ts
export { useAvailabilitySlots } from '@/features/agenda';  // re-export from agenda Public API
```

(FSD boundary check passes — re-export via Public API allowed.)

## 5. Component patterns

### 5.1 `<ReEngagementCard variant>` polymorphic

```tsx
// vitalia/frontend/src/features/fidelizacion/components/ReEngagementCard.tsx
'use client';

import type { PatternRow, UrgencyLevel } from '../types/re-engagement';
import { useCopy } from '@/hooks/useCopy';
import { FIDELIZACION_COPY } from '../copy';
import { RequireRole } from '@/components/shared/phi';

interface ReEngagementCardProps {
  row: PatternRow;
  onAdrianReminder: () => void;
  onSuggestSlots: () => void;
  onPause: () => void;
  // ... pattern-specific handlers
}

export function ReEngagementCard({ row, ...handlers }: ReEngagementCardProps) {
  const copy = useCopy(FIDELIZACION_COPY);
  return (
    <RequireRole roles={['doctor', 'nurse', 'admin_clinic']}>
      <article
        data-testid={`re-engagement-card-${row.pattern}-${row.reEngagementEventId}`}
        className={cn(
          "border rounded-md p-4",
          urgencyClassMap[row.urgency],
          row.outcome === 'sent' && 'bg-[hsl(var(--vitalia-bg-soft))]',
        )}
      >
        <UrgencyBadge urgency={row.urgency} copy={copy.urgency} />
        <header>...</header>
        <PatternBody data={row.patternData} copy={copy} />
        <ActionsRow row={row} {...handlers} />
      </article>
    </RequireRole>
  );
}

function PatternBody({ data, copy }: { data: MultiSessionData | FollowUpData | MaintenanceData | AbsenceData; copy: any }) {
  switch (data.kind) {
    case 'multi_session': return <MultiSessionBody data={data} copy={copy.multi_session_card} />;
    case 'follow_up':     return <FollowUpBody     data={data} copy={copy.follow_up_card} />;
    case 'maintenance':   return <MaintenanceBody  data={data} copy={copy.maintenance_card} />;
    case 'absence':       return <AbsenceBody      data={data} copy={copy.absence_card} />;
  }
}
```

### 5.2 `<ConfirmTemplateModal>` pattern

```tsx
'use client';

export function ConfirmTemplateModal({ eventId, templateId, slotValues, onClose }: Props) {
  const { mutate, isLoading } = useSendProactiveTemplate();
  // ... preview + cancel + send
}
```

### 5.3 PHI guarding pattern (`<RequireRole>`)

```tsx
// All PHI-sensitive sections wrapped — Patient name, last_appointment_date, valor histórico etc.
import { RequireRole } from '@/components/shared/phi';
import { PiiMaskedSpan } from '@/components/shared/phi';

<RequireRole roles={['doctor', 'nurse', 'admin_clinic']} fallback={<AuditedAccessDeniedFallback />}>
  <PiiMaskedSpan content={patient.name} unmaskRoles={['doctor', 'nurse', 'admin_clinic']} />
</RequireRole>
```

(Pattern cemented Story 11 — shared components live in `vitalia/frontend/src/components/shared/phi/`.)

### 5.4 `<NPSTagBadge>` shared cross-feature

```tsx
// vitalia/frontend/src/components/shared/nps/NPSTagBadge.tsx
'use client';

import type { NPSBand } from '@/features/fidelizacion/types/nps';

interface NPSTagBadgeProps {
  score: number;
  band: NPSBand;
  compact?: boolean;
}

export function NPSTagBadge({ score, band, compact = false }: NPSTagBadgeProps) {
  const colorClass = {
    promoter: 'bg-[hsl(var(--vitalia-success-bg))] text-[hsl(var(--vitalia-success))]',
    passive: 'bg-[hsl(var(--vitalia-warn-bg))] text-[hsl(var(--vitalia-warn))]',
    detractor: 'bg-[hsl(var(--vitalia-danger-bg))] text-[hsl(var(--vitalia-danger))]',
  }[band];
  const icon = band === 'promoter' ? '🌟' : band === 'detractor' ? '⚠️' : '';
  return (
    <span
      className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium", colorClass)}
      role="status"
      aria-label={`NPS ${score} (${band})`}
    >
      {icon} NPS {score}
    </span>
  );
}
```

## 6. Estados visuales por componente (page-level)

| Estado | Trigger | Visual |
|---|---|---|
| `idle` | Page mount sin fetch | Skeleton 5 stat cards + 5 tabs + lista placeholder |
| `loading` | Fetch patrones en curso | Spinner overlay + dots animados "Cargando seguimiento..." |
| `success` | Data fetched, hay patrones | KPIs llenos + tab activo + cards + activity footer real |
| `error` | Fetch falló | Banner rojo "No pudimos cargar el seguimiento. [Intentá de nuevo]" |
| `empty` | Fetch OK, 0 patrones tab | Empty illustration + copy contextual ("Todos al día ✓") |
| `agent-thinking` | Cron mid-render | Banner sutil "Sistema ejecutando cron {nombre}..." |
| `agent-waiting-approval` | Adrián requires confirm | Modal `ConfirmTemplateModal` open |
| `agent-failed` | Template WA send failed | Toast error + card status_failed + chip "Envío falló · reintentar?" |

## 7. Accesibilidad (WCAG 2.1 AA)

- KPIs cards `role="status"` + `aria-label` con value + trend
- Tabs verticales: Shadcn `<Tabs orientation="vertical">` (ARIA-compliant)
- Cards: keyboard nav `Tab` → expand on `Enter`. Disabled `[Adrián WA]` button `aria-describedby={tooltip-disabled-marketing}`.
- Modals: focus trap + `aria-modal="true"` + `aria-labelledby={title}` + Escape closes
- Contraste tokens validated en design-system.md
- Screen reader: `<NPSTagBadge>` con `aria-label="NPS 9 (promoter)"`

## 8. Storybook coverage (mandatory)

Cada componente NEW tiene `.stories.tsx`:
- `ReEngagementCard.stories.tsx` — 4 variantes × 5 urgency states × paused
- `ConfirmTemplateModal.stories.tsx` — preview + loading + success + error states
- `PausePatientModal.stories.tsx`
- `ManualCallLoggedModal.stories.tsx`
- `SuggestSlotsModal.stories.tsx`
- `FidelizacionKPIsHero.stories.tsx` — loading + populated + error
- `FidelizacionTabsBar.stories.tsx` — counts dynamic
- `NPSTagBadge.stories.tsx` — 3 bands × score range
- Empty state stories per tab

## 9. Test surfaces (TDD-mandatory)

| Layer | Test pattern | RED first |
|---|---|---|
| Hook unit | `vitalia/frontend/src/features/fidelizacion/api/__tests__/use-*.test.ts` | YES |
| Component unit | `vitalia/frontend/src/features/fidelizacion/components/__tests__/*.test.tsx` | YES |
| Store | `__tests__/fidelizacion-store.test.ts` | YES |
| Architecture fitness | `vitalia/frontend/src/__tests__/architecture/*.test.ts` | YES |
| E2E smoke | `vitalia/frontend/e2e/specs/smoke/fidelizacion.smoke.spec.ts` (page mount + tab nav + KPIs visible) | YES |
| E2E regression | `vitalia/frontend/e2e/specs/regression/fidelizacion-*.spec.ts` × 4 scenarios | YES |
| Visual regression (Chromatic) | Storybook `*.stories.tsx` snapshot | YES |

Coverage threshold: 20% baseline (per `.claude/rules/frontend-quality.md`). Slice 1 fidelización target ≥ 30% per feature.

## 10. Performance budgets

| Metric | Budget |
|---|---|
| LCP `/fidelización` | < 2.5s |
| INP tab switch | < 200ms |
| Bundle size feature | < 80 KB gzipped |
| Cards list 100 items | virtualization required (`@tanstack/react-virtual`) |
| Storybook stories load | < 500ms per story |

## 11. Architectural fitness impact

| Test file | Constraint |
|---|---|
| `test_no_hardcoded_colors.test.ts` | All colors via CSS vars `--vitalia-*` |
| `test_no_hardcoded_strings.test.ts` | All user-facing strings via `FIDELIZACION_COPY` |
| `test_fsd_boundaries.test.ts` | Feature `fidelizacion` boundary respected |
| `test_no_cross_feature_imports.test.ts` | Public API via `index.ts` only |
| `test_server_first.test.ts` | RSC default — `"use client"` solo en nodos hoja |
| `test_phi_pii_components_used.test.ts` | `<RequireRole>` + `<PiiMaskedSpan>` en patient name + lifetime value etc. |
| `test_no_voseo_in_copy.test.ts` | `copy.ts` Latam neutro tuteo |

Zero new allowlist entries.

## 12. Reuse explicit (Nicolify)

| Reuse from | What | Adaptation |
|---|---|---|
| `nicolify/frontend/src/features/campaigns-lite/components/CampaignDetailClient.tsx` | Detail card layout pattern | Token overrides (HEX → vitalia CSS vars). Strip Nicolify copy. Add PHI guards. |
| `nicolify/frontend/src/features/campaigns-lite/components/CampaignStatsCard.tsx` | Stat card primitive | Reuse pattern para `FidelizacionKPIsHero` constituent cards |
| `nicolify/frontend/src/features/campaigns-lite/api/use-*.ts` | React Query mutation + invalidation pattern | Fork shape, point at fidelización endpoints |
| `nicolify/frontend/src/features/notifications/components/NotificationCard.tsx` | Card render with timestamp + actions | Reference para `ReEngagementCard` urgency variants |
| `nicolify/frontend/src/features/notifications/components/NotificationPanel.tsx` | Modal preview area | Reference para `ConfirmTemplateModal` preview |

**Cross-brand mirror flag:** `ReEngagementCard` + `ConfirmTemplateModal` + `NPSTagBadge` son potencialmente repetibles. Slice 2 candidate lift to `@luana/ui-kit` o `core/luana-core-fidelizacion/` cuando 2do brand adopta. Promotion gate `/pm-luana` post Slice 2.

## 13. Cross-story consumer contract

Esta story PRODUCE en HANDOFF-cross-story-updates.md:
- TS types: `NPSRowDTO`, `NPSBand`, `NPSSummaryResponse`, `ReEngagementPattern`, `PatternRow`, `ReEngagementEvent`
- Zod schemas: `npsSchema`, `reEngagementEventSchema` en `vitalia/frontend/src/lib/zod-schemas/` (shared)
- Public API: `vitalia/frontend/src/features/fidelizacion/index.ts` exports `NPSTagBadge` ya en `components/shared/nps/` (cross-feature root, not feature-scoped)
- Endpoints contracts (see `03-arch-be.md` § 3)

Esta story CONSUME:
- `@/features/agenda` `useAvailabilitySlots` (re-exported in fidelización api/)
- `@/components/shared/phi` `RequireRole`, `PiiMaskedSpan`, `AuditedSection`
- `@/components/shared/contact-sidebar` `ContactSidebar`
- `@/components/shared/agents` `AgentAvatar`, `AgentAttribution`
- `@/hooks/useTenantLocale`, `useClinicId`, `useCurrentUser`, `usePiiRoleGate`
- `@/lib/api/fetchClient`, `@/lib/format/{formatMoney,formatTenantDate}`
