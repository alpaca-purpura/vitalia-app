---
story_id: vitalia-slice-1-marketing
target_file: vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md
update_type: deltas-additions
generated_on: 2026-05-20
generator: /architect
---

# HANDOFF cross-story updates (deltas for global handoff doc)

> Verbatim deltas to apply to `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md` once this story produces the artifacts. Apply during `/pm-vitalia` merge cycle (Fase F per `.claude/rules/story-closure-gate.md`).

## § 3 — Contratos TypeScript compartidos (FE)

### Marketing-shared (consumido por marketing + pipeline) — CONFIRM produced

Ola 2 (`/marketing`) **produce** los tipos cementados:

```typescript
// vitalia/frontend/src/features/marketing-shared/types.ts (NEW Ola 2 — confirmado por vitalia-slice-1-marketing)

export type RecommendationStage = "attraction" | "qualification" | "reservation" | "adoption" | "expansion";
export type RecommendationStatus = "open" | "approved" | "rejected" | "expired" | "undone";

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
```

**Delta from parent handoff:** parent doc listed `LucasRecommendation` with `recommendation_type: 'stage_optimization' | 'attribution_insight' | 'referral_opportunity' | 'channel_alert'`. **This story uses `recommendationKind: string`** instead (flexible enum) since Lucas growth setter is shipping more kinds than originally cataloged. Pipeline consumers must update import to use `recommendationKind: string` + stage filter.

## § 4 — Schemas Zod compartidos

ADD row:

| Schema | Path | Producer | Consumers |
|---|---|---|---|
| `lucasRecommendationSchema` | `vitalia/frontend/src/lib/zod-schemas/lucas-recommendation.ts` | Ola 2 marketing (this story) | pipeline (stage_optimization cards), fidelización |

## § 5 — Endpoints API compartidos

### Producidos por Ola 2 — `/marketing` — CONFIRM 10 endpoints (refresh list)

| Method | Path | Consumers |
|---|---|---|
| GET | `/api/v1/vitalia/marketing/bowtie/summary` | (UI only — propio) |
| GET | `/api/v1/vitalia/marketing/stage/{stage_slug}` | (UI only) |
| GET | `/api/v1/vitalia/marketing/channels/{provider}` | (UI only — admin_clinic role) |
| POST | `/api/v1/vitalia/marketing/channels/{provider}/connect` | (UI only) |
| POST | `/api/v1/vitalia/marketing/channels/{provider}/sync` | (UI only — Idempotency-Key) |
| GET | `/api/v1/vitalia/marketing/recommendations` | pipeline (stage_optimization cards), fidelización (re-engagement cards) |
| POST | `/api/v1/vitalia/marketing/recommendations/{rec_id}/approve` | (UI only — admin_clinic + Idempotency-Key) |
| POST | `/api/v1/vitalia/marketing/recommendations/{rec_id}/reject` | (UI only — admin_clinic + Idempotency-Key) |
| POST | `/api/v1/vitalia/marketing/recommendations/{rec_id}/undo` | (UI only — admin_clinic + Idempotency-Key + 5min window) |
| GET | `/api/v1/vitalia/marketing/attribution-matrix` | pipeline (badge attribution insight cross-link) |
| GET | `/api/v1/vitalia/marketing/referrals` | fidelización (referral cards cross-link) |

Total = 11 endpoints (parent estimate 10; bowtie summary + stage detail + channel detail + connect + sync + recs list + approve + reject + undo + attribution + referrals = 11). Minor count update from parent's "10" — UI-only endpoints + cross-story = 11.

## § 6 — Domain events compartidos (engine outbox bus)

ADD rows:

| Event | Producer | Consumers |
|---|---|---|
| `LucasRecommendationGenerated` | marketing (cron lucas_daily_analysis_sweep) | pipeline (stage_optimization cards), fidelización (re-engagement cards), FE optional toast |
| `LucasRecommendationApproved` | marketing | FE invalidate React Query cache · Slice 2 wires real Meta API call |
| `LucasRecommendationRejected` | marketing | FE invalidate cache · telemetry |
| `LucasRecommendationUndone` | marketing | FE re-show card if still pending |
| `LucasRecommendationExpired` | marketing (cron expire_sweep nightly) | telemetry only |
| `ChannelSyncSucceeded` | marketing (cron channel_metrics_sync_*) | FE invalidate React Query cache |
| `ChannelSyncFailed` | marketing | Sentry alert + FE degraded state |
| `ReferralCodeGenerated` | marketing (patient activation handler) | telemetry |
| `ReferralConverted` | marketing (cron referrals_value_sync) | LucasReferralsService recomputes leaderboard next cron |

All events via `from luana_core_events.outbox.adapter_bus import publish` (post 2026-04-29 default ON).

## § 8 — Side effects esperados (Olas 2 ↔ 3 coordination)

ADD note:

**Ola 2 marketing ↔ vitalia-payment-adapter-mvp (side dep pipeline):** pipeline story consumes `LucasRecommendation` cards via `useLucasRecommendations({ stage: "qualification" })` to surface "3 leads sin screening" insights on pipeline kanban headers. Marketing produces these via Lucas daily cron — pipeline consumes via shared API endpoint. NO new contract needed; LucasRecommendation type already shared via marketing-shared.

**Ola 2 marketing ↔ Ola 1 fidelización (already shipped):** fidelización story may want to cross-link "referrals_value_sync" data into NPS dashboard (Slice 2). For Slice 1, fidelización imports `referralsResponse.topReferrers` via `/api/v1/vitalia/marketing/referrals` if needed for `ReferralsCrossLinkWidget` (defer Slice 2 if not cement Ola 1).

## § 9 — Lift candidates Slice 2 (delta-arch-notes for /pm-luana retrospective)

ADD entries:

- **Lucas recommendations pattern** — `vitalia/backend/src/modules/vitalia/marketing/application/services/lucas_recommendations_service.py` (approve/reject/undo state machine) — lift to engine `core/luana-core-sales-agent/` when 2nd brand opta-in growth agent recommendations (likely FitFlow gym retention recommendations, Retailly cart abandonment recommendations).
- **ChannelSyncState pattern** — `vitalia_channel_sync_state` table + OAuth wizard adapters — lift to engine `core/luana-core-connections/` when 2nd brand opta-in ad channel sync (likely Retailly Shopify/WooCommerce sync, Guestly Booking sync).
- **Referrals pattern** — `vitalia_referrals` table + leaderboard service — lift to engine `core/luana-core-crm/` when 2nd brand opta-in referral programs (likely FitFlow gym referral codes, Comunify creator referral).
- **AttributionMatrixWidget** (4 origins × downstream conversion) — FE component lift to `@luana/ui-kit` when 2nd brand opta-in attribution surface.

All lift candidates documented for `/pm-luana` retrospective post-merge.

## § 10 — Capability inventory updates (apply at `/pm-vitalia` Fase E DOCS)

CREATE NEW:

```yaml
# vitalia/docs/product/capabilities/marketing/bowtie-5stages-lucas.yaml
---
brand: vitalia
module: marketing
slug: bowtie-5stages-lucas
status: live
shipped_in: vitalia-slice-1-marketing (state=done — date TBD post merge)
description: |
  Bowtie salud 5 stages (Atracción+Captura · Calificación+Considerando · Reserva c/depósito ·
  Adopción · Expansión+Evangelización). Lucas growth setter recommendations protagonista 3 cards
  top per stage. AttributionMatrix 4 origins Stage Reserva. ReferralsWidget Stage Expansión.
  Meta + Google Ads API sync read-only Slice 1. UTM tracking lead→origin attribution.
verification:
  commands:
    - "cd ${WS} && .venv/bin/pytest vitalia/backend/tests/modules/vitalia/marketing/ -v"
    - "cd ${WS} && .venv/bin/pytest vitalia/backend/tests/workers/test_marketing_crons.py -v"
    - "cd ${WS}/vitalia/frontend && npx vitest run src/features/marketing/"
    - "cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/specs/smoke/marketing.smoke.spec.ts"
  gherkin_evidence:
    - vitalia/docs/product/stories/vitalia-slice-1-marketing/01-spec-extract.md (SC-MK-01..04)
    - vitalia/docs/product/stories/vitalia-slice-1-marketing/06-tickets.yaml (gherkin_coverage[] per ticket)
related_capabilities:
  - pipeline/consultive-funnel-6stages (cross-link stage_optimization)
  - fidelizacion/4patterns-reengagement (cross-link re-engagement recommendations)
lift_candidates_slice_2:
  - core/luana-core-sales-agent/ (Lucas recommendations pattern)
  - core/luana-core-connections/ (channel sync state pattern)
  - core/luana-core-crm/ (referrals pattern)
```

UPDATE:

```markdown
# vitalia/docs/product/modules/marketing.md (NEW — auto-list block updated by reconcile_capabilities.py per .claude/rules/brand-docs-schema.md R3)
```

## Confirm consumed by /pm-vitalia at Fase F MERGE

This file is read verbatim by `/pm-vitalia` when transitioning `reviewing → done`. Apply deltas to global handoff file. Then `git mv vitalia/docs/product/stories/vitalia-slice-1-marketing → vitalia/docs/archive/2026/stories/vitalia-slice-1-marketing` (per `.claude/rules/brand-docs-schema.md R2`).
