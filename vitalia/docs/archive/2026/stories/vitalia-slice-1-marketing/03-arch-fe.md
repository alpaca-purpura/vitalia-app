---
story_id: vitalia-slice-1-marketing
sub_arch: frontend
brand: vitalia
builder: builder-frontend (Sonnet)
auditor: auditor-frontend (Opus)
production_code: false
---

# Frontend sub-arch — vitalia-slice-1-marketing

> FSD-Lite per brand. Next.js 16 App Router · Server Components default. NO growth-studio reuse. Build simple consume scaffolds existentes + Lucas tools shipped.

## 1. FSD layout

```
vitalia/frontend/src/
├── app/
│   └── marketing/
│       └── page.tsx                         ← Server Component default. Renders <MarketingLayout>. Reads URL state via nuqs server-side.
├── features/
│   ├── marketing/                            ← NEW Slice 1 — domain-scoped feature
│   │   ├── api/
│   │   │   ├── use-bowtie-summary.ts        ← React Query useQuery
│   │   │   ├── use-stage-detail.ts
│   │   │   ├── use-channel-detail.ts
│   │   │   ├── use-lucas-recommendations.ts
│   │   │   ├── use-approve-recommendation.ts  ← useMutation + Idempotency-Key
│   │   │   ├── use-reject-recommendation.ts
│   │   │   ├── use-undo-recommendation.ts
│   │   │   ├── use-sync-channel.ts
│   │   │   ├── use-attribution-matrix.ts
│   │   │   └── use-referrals.ts
│   │   ├── components/
│   │   │   ├── MarketingLayout.tsx          ← Orchestrator: bowtie + tabs + stage content + sidebar
│   │   │   ├── MarketingBowtieSVG.tsx       ← Promotes scaffold components/shared/marketing/ → feature-scoped
│   │   │   ├── MarketingStageTabs.tsx       ← 5 tabs nav with counts + KPI hero
│   │   │   ├── StageDispatcher.tsx          ← Renders correct stage section by URL ?tab=
│   │   │   ├── AttractionStage.tsx          ← Lucas card + KPIs + ChannelBreakdown
│   │   │   ├── QualificationStage.tsx       ← Lucas card + KPIs
│   │   │   ├── ReservationStage.tsx         ← Lucas card + AttributionMatrixWidget + KPIs
│   │   │   ├── AdoptionStage.tsx            ← Lucas card + KPIs
│   │   │   ├── ExpansionStage.tsx           ← Lucas card + ReferralsWidget + NPS card
│   │   │   ├── LucasStageRecommendationsCard.tsx  ← Promote scaffold (3 cards sticky top)
│   │   │   ├── LucasRecommendationDetailModal.tsx ← NEW Slice 1
│   │   │   ├── LucasApprovalModal.tsx       ← NEW Slice 1
│   │   │   ├── LucasUndoChip.tsx            ← 5min countdown chip post-approve
│   │   │   ├── AttributionMatrixWidget.tsx  ← Promote scaffold
│   │   │   ├── ReferralsWidget.tsx          ← NEW Slice 1
│   │   │   ├── ChannelBreakdownRow.tsx      ← Promote scaffold
│   │   │   ├── ChannelDetailSidebar.tsx     ← NEW Slice 1 — 3 sections simplificado
│   │   │   ├── ChannelConnectionWizard.tsx  ← NEW Slice 1 — 3 pasos OAuth
│   │   │   ├── ConnectionBadge.tsx          ← OK / warning / error / disconnected
│   │   │   ├── MarketingActivityFooter.tsx  ← "Lucas analizó X · sync c/4h"
│   │   │   └── index.ts                     ← Public API barrel export
│   │   ├── store/
│   │   │   └── marketing-store.ts           ← Zustand: ephemeral UI state (active filters drilldown not URL-serializable)
│   │   ├── types/
│   │   │   ├── lucas-recommendation.ts      ← TS mirror Pydantic DTO
│   │   │   ├── bowtie.ts
│   │   │   ├── attribution.ts
│   │   │   ├── referrals.ts
│   │   │   ├── channel.ts
│   │   │   └── url-state.ts                 ← nuqs parsers (marketingParsers)
│   │   ├── copy.ts                          ← MARKETING_COPY Spanish neutro
│   │   ├── __tests__/                       ← Vitest unit
│   │   │   ├── MarketingBowtieSVG.test.tsx
│   │   │   ├── LucasStageRecommendationsCard.test.tsx
│   │   │   ├── LucasApprovalModal.test.tsx
│   │   │   ├── AttributionMatrixWidget.test.tsx
│   │   │   ├── ReferralsWidget.test.tsx
│   │   │   └── ChannelConnectionWizard.test.tsx
│   │   └── index.ts                         ← feature Public API
│   └── marketing-shared/                     ← NEW Slice 1 — cross-story types (consumed by /pipeline)
│       ├── types.ts                         ← LucasRecommendation (subset for cross-feature), AttributionEntry
│       └── index.ts
├── components/shared/                        ← Existing scaffolds promoted later to feature-local
│   ├── marketing/MarketingBowtieSVG.tsx     ← REMAINS exported via @luana/ui-kit candidate Slice 2
│   ├── lucas-recommendations/LucasStageRecommendationsCard.tsx
│   ├── attribution/AttributionMatrixWidget.tsx
│   └── channels/ChannelBreakdownRow.tsx
├── lib/
│   ├── api/fetchClient.ts                   ← Auto-injects X-Tenant-ID + X-Clinic-ID + Idempotency-Key support
│   ├── format/{formatMoney,formatTenantDate,formatTenantDateTime,formatTenantRelative}.ts
│   ├── zod-schemas/lucas-recommendation.ts  ← Z mirror of Pydantic DTO (cross-story handoff)
│   └── nuqs-parsers/marketing-parsers.ts    ← shared parser declarations
├── hooks/
│   ├── useTenantLocale.ts                   ← Provides currency + timezone
│   ├── useCurrentUser.ts
│   ├── useClinicId.ts
│   ├── useFeatureFlag.ts
│   └── useRoleGate.ts                       ← Boolean per role (admin_clinic for approval gating)
├── e2e/
│   ├── auth.fixture.ts                      ← Clerk testing token fixture (preflight cement)
│   ├── pages/marketing.page.ts              ← POM
│   └── specs/smoke/marketing.smoke.spec.ts  ← Happy path E2E
└── __tests__/architecture/
    └── (all arch fitness tests already enumerated in 03-arch.md § 0)
```

## 2. TypeScript types (mirror Pydantic DTOs · camelCase)

```ts
// vitalia/frontend/src/features/marketing/types/lucas-recommendation.ts
export type RecommendationStage = "attraction" | "qualification" | "reservation" | "adoption" | "expansion";
export type RecommendationStatus = "open" | "approved" | "rejected" | "expired" | "undone";
export type RejectReason = "not_priority" | "already_doing" | "data_wrong" | "too_risky" | "other";

export type LucasRecommendation = {
  id: string;
  tenantId: string;
  clinicId: string;
  stage: RecommendationStage;
  recommendationKind: string;
  title: string;
  body: string;
  rationaleJson: Record<string, unknown>;
  actionPayloadJson: Record<string, unknown> | null;
  priority: number;
  confidencePct: number | null;
  projectedImpactText: string | null;
  status: RecommendationStatus;
  approvedByUserId: string | null;
  approvedAt: string | null;  // ISO 8601 UTC
  undoUntil: string | null;
  expiresAt: string;
  createdAt: string;
};

export type LucasRecommendationsResponse = {
  items: LucasRecommendation[];
};

// vitalia/frontend/src/features/marketing/types/bowtie.ts
export type BowtieStage = {
  slug: RecommendationStage;
  label: string;
  count: number;
  primaryKpiValue: number | null;
  primaryKpiLabel: string | null;
};

export type BowtieSummaryResponse = {
  periodStart: string;
  periodEnd: string;
  stages: BowtieStage[];
  overallConversionPct: number;
  overallRoiX: number | null;
  overallLtvCents: number | null;
  currency: string | null;
  lastSyncAt: string | null;
};

// vitalia/frontend/src/features/marketing/types/attribution.ts
export type AttributionOrigin = "sales_agent" | "walk_in" | "phone_manual" | "proactive_outbound";

export type AttributionOriginRow = {
  origin: AttributionOrigin | "total";
  leads: number;
  qualified: number;
  convListo: number;
  reservations: number;
  adoption: number;
  valueCents: number;
};

export type AttributionMatrixResponse = {
  periodStart: string;
  periodEnd: string;
  origins: AttributionOriginRow[];
  totals: AttributionOriginRow;
  topInsightText: string | null;
  currency: string | null;
};

// vitalia/frontend/src/features/marketing/types/referrals.ts
export type ReferrerLeaderboardRow = {
  referrerPatientIdHash: string;  // NEVER patient name — hash only
  referralsCount: number;
  totalValueCents: number;
};

export type ReferralsResponse = {
  periodStart: string;
  periodEnd: string;
  referralsCount: number;
  convRate: number;
  avgLtvPerReferrerCents: number | null;
  topReferrers: ReferrerLeaderboardRow[];
  currency: string | null;
};

// vitalia/frontend/src/features/marketing/types/channel.ts
export type ProviderSlug = "meta_ads" | "google_ads";
export type SyncStatus = "idle" | "running" | "error" | "disconnected";

export type ChannelSyncState = {
  provider: ProviderSlug;
  lastSyncAt: string | null;
  lastSuccessAt: string | null;
  lastError: string | null;
  status: SyncStatus;
  enabled: boolean;
  accountId: string | null;
};

export type ChannelMetricRow = {
  provider: ProviderSlug;
  channelSlug: string;
  campaignId: string | null;
  campaignName: string | null;
  metricDate: string;
  impressions: number | null;
  clicks: number | null;
  conversions: number | null;
  spendCents: number | null;
  currency: string | null;
};

export type ChannelDetailResponse = {
  provider: ProviderSlug;
  syncState: ChannelSyncState;
  metrics: ChannelMetricRow[];
};
```

## 3. URL state SSoT (nuqs · 7 params)

```ts
// vitalia/frontend/src/features/marketing/types/url-state.ts
import { parseAsString, parseAsStringEnum, parseAsBoolean } from "nuqs";

export const marketingParsers = {
  tab: parseAsStringEnum(["attraction", "qualification", "reservation", "adoption", "expansion"]).withDefault("attraction"),
  period: parseAsStringEnum(["7d", "30d", "90d"]).withDefault("30d"),
  channel: parseAsString,
  selectedRecommendation: parseAsString,
  approvalModal: parseAsBoolean.withDefault(false),
  channelDetailSidebar: parseAsString,
  connectionWizard: parseAsStringEnum(["meta_ads", "google_ads"]),
};
```

Pattern: `replace` for intra-state (filters, modals, sidebar, selected rec). `push` for cross-route (drill `/pipeline`, `/agenda`, `/fidelizacion`, `/inbox`). External links new tab.

## 4. React Query hooks

```ts
// vitalia/frontend/src/features/marketing/api/use-lucas-recommendations.ts
import { useQuery } from "@tanstack/react-query";
import { fetchClient } from "@/lib/api/fetchClient";
import type { LucasRecommendationsResponse, RecommendationStage, RecommendationStatus } from "../types/lucas-recommendation";

export function useLucasRecommendations(params: {
  stage?: RecommendationStage;
  status?: RecommendationStatus;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["marketing", "lucas-recommendations", params],
    queryFn: () => fetchClient.get<LucasRecommendationsResponse>(
      "/api/v1/vitalia/marketing/recommendations",
      { params },
    ),
    staleTime: 5 * 60 * 1000,
  });
}

// vitalia/frontend/src/features/marketing/api/use-approve-recommendation.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchClient } from "@/lib/api/fetchClient";
import type { LucasRecommendation } from "../types/lucas-recommendation";

export function useApproveRecommendation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (recId: string) => fetchClient.post<LucasRecommendation>(
      `/api/v1/vitalia/marketing/recommendations/${recId}/approve`,
      {},
      { headers: { "Idempotency-Key": crypto.randomUUID() } },
    ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["marketing", "lucas-recommendations"] }),
  });
}
```

Same pattern for: `useRejectRecommendation`, `useUndoRecommendation`, `useSyncChannel`, `useBowtieSummary`, `useStageDetail`, `useChannelDetail`, `useAttributionMatrix`, `useReferrals`.

## 5. Zustand store (ephemeral UI state)

```ts
// vitalia/frontend/src/features/marketing/store/marketing-store.ts
import { create } from "zustand";

type MarketingStoreState = {
  // Ephemeral UI state NOT URL-serializable (collapsed/expanded sub-sections, animation flags)
  bowtieAnimating: boolean;
  setBowtieAnimating: (animating: boolean) => void;
  // Action receipt 5min countdown timer per approved recommendation
  pendingUndoTimers: Map<string, number>;  // rec_id → unix_ms_expiry
  setPendingUndoTimer: (recId: string, expiryMs: number) => void;
  clearPendingUndoTimer: (recId: string) => void;
};

export const useMarketingStore = create<MarketingStoreState>((set) => ({
  bowtieAnimating: false,
  setBowtieAnimating: (animating) => set({ bowtieAnimating: animating }),
  pendingUndoTimers: new Map(),
  setPendingUndoTimer: (recId, expiryMs) => set((s) => {
    const next = new Map(s.pendingUndoTimers);
    next.set(recId, expiryMs);
    return { pendingUndoTimers: next };
  }),
  clearPendingUndoTimer: (recId) => set((s) => {
    const next = new Map(s.pendingUndoTimers);
    next.delete(recId);
    return { pendingUndoTimers: next };
  }),
}));
```

URL state stays in nuqs. Zustand for UI ephemera only.

## 6. Forms (RHF + Zod) — Reject reason modal

```ts
// vitalia/frontend/src/features/marketing/components/LucasRejectModal.tsx
const rejectSchema = z.object({
  reason: z.enum(["not_priority", "already_doing", "data_wrong", "too_risky", "other"]),
});

export function LucasRejectModal({ recId, onClose }: { recId: string; onClose: () => void }) {
  const form = useForm<z.infer<typeof rejectSchema>>({ resolver: zodResolver(rejectSchema) });
  const reject = useRejectRecommendation();
  // ...
}
```

## 7. Storybook stories (Slice 1 obligatorio)

| Component | Stories (variants × states) |
|---|---|
| `MarketingBowtieSVG` | 5 stages × 4 breakpoints = 20 |
| `LucasStageRecommendationsCard` | 4 estados (open · approved+5min undo · rejected · expired) |
| `LucasRecommendationDetailModal` | 3 estados (open · loading rationale · denied 403) |
| `LucasApprovalModal` | 2 estados (review · confirming) |
| `AttributionMatrixWidget` | 4 origins × 3 periods 7d/30d/90d × (populated, empty) = 24 |
| `ReferralsWidget` | (populated · empty · loading) |
| `ChannelBreakdownRow` | 5 canales × 4 sync states (idle/running/error/disconnected) = 20 |
| `ChannelConnectionWizard` | 3 pasos (selector · oauth redirect · confirm) |
| `ConnectionBadge` | 4 estados |
| `MarketingActivityFooter` | (sync OK · sync degraded · all-disconnected) |

Storybook + Chromatic integration shoots visual baselines per breakpoint (mobile 768 · tablet 1024 · desktop 1440). Diff threshold 0.1%.

## 8. Architecture fitness tests (allowlist shrink only)

| Test | Purpose |
|---|---|
| `test_no_hardcoded_colors.test.ts` | NO HEX literales en .tsx/.ts outside globals.css |
| `test_no_hardcoded_strings.test.ts` | All user-facing strings live in `copy.ts` |
| `test_fsd_boundaries.test.ts` | `features/marketing/` cannot import from another feature except via Public API `index.ts` |
| `test_no_cross_feature_imports.test.ts` | `marketing` can import only from `marketing/`, `marketing-shared/`, `lib/`, `hooks/`, `components/shared/` |
| `test_server_first.test.ts` | `"use client"` only at leaf nodes |
| `test_no_voseo_in_copy.test.ts` | Spanish neutro enforced |
| `test_page_padding.test.ts` | Design tokens consistency cross-page |
| `test_phi_pii_components_used.test.ts` | NA marketing (no PHI displayed — `referrerPatientIdHash` only) |

## 9. Performance budget

| Metric | Budget | Enforcement |
|---|---|---|
| LCP | < 2.5s | Lighthouse CI per route in CD |
| INP | < 200ms | Lighthouse CI |
| CLS | < 0.1 | Lighthouse CI |
| Bowtie SVG bundle | < 30KB gzipped | `next.config` bundle-analyzer + post-build size check script `vitalia/frontend/scripts/check-bowtie-bundle.ts` |
| Lucas card lazy-load | below-fold lazy via `<Suspense>` + IntersectionObserver | Manual review in T-mk-fe-7 |

## 10. E2E smoke (Playwright)

```ts
// vitalia/frontend/e2e/specs/smoke/marketing.smoke.spec.ts
import { test, expect } from "../../auth.fixture";
import { MarketingPage } from "../../pages/marketing.page";

test.describe("/marketing smoke", () => {
  test("loads bowtie + tabs + Lucas cards visible", async ({ page, authedContext }) => {
    const mp = new MarketingPage(page);
    await mp.goto();
    await expect(mp.bowtieSvg).toBeVisible();
    await expect(mp.stageTabs).toHaveCount(5);
    await expect(mp.lucasCardsSection).toBeVisible();
  });

  test("tab change updates URL + re-renders stage content", async ({ page }) => {
    const mp = new MarketingPage(page);
    await mp.goto();
    await mp.clickStageTab("reservation");
    await expect(page).toHaveURL(/tab=reservation/);
    await expect(mp.attributionMatrix).toBeVisible();
  });

  test("Lucas approval modal opens + closes (no confirm)", async ({ page }) => {
    const mp = new MarketingPage(page);
    await mp.goto();
    await mp.clickFirstLucasCardDetail();
    await expect(mp.approvalModalTitle).toBeVisible();
    await mp.closeApprovalModal();
    await expect(mp.approvalModalTitle).toBeHidden();
  });
});
```

## 11. Cross-story handoff (`marketing-shared/`)

Types consumed by `/pipeline` per `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md § 3 Marketing-shared`:

```ts
// vitalia/frontend/src/features/marketing-shared/types.ts (NEW)
export type { LucasRecommendation, RecommendationStage, RecommendationStatus } from "../marketing/types/lucas-recommendation";
export type { AttributionOrigin, AttributionOriginRow, AttributionMatrixResponse } from "../marketing/types/attribution";

// /pipeline imports:
// import type { LucasRecommendation } from "@/features/marketing-shared";
```

## 12. References

- `02-design-ui-mockup.html` (SSoT visual)
- `02-design-ui.md` (refresh design notes)
- `vitalia/docs/architecture/design-system.md` (tokens)
- `vitalia/docs/architecture/ADR-vitalia-001-shared-vs-fork.md`
- `.claude/rules/{frontend-fsd,frontend-quality,e2e-testing,spanish-text,master-data,currency-handling}.md`
- `vitalia/.claude/rules/hipaa-lite.md`
- Parent `vitalia/docs/archive/2026/stories/vitalia-ux-discovery/03-arch-fe.md`
- Existing scaffolds: `vitalia/frontend/src/components/shared/{marketing,lucas-recommendations,attribution,channels}/`
