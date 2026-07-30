// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * Bowtie funnel domain types — mirror of BE BowtieSummaryResponse + StageDetailResponse (camelCase)
 * downstream-regression-na: brand-local FE type; consumed by marketing feature only
 */

import type { RecommendationStage } from "./lucas-recommendation";

export type BowtieStage = {
  slug: RecommendationStage;
  label: string;
  count: number;
  primaryKpiValue: number | null;
  primaryKpiLabel: string | null;
};

export type BowtieSummaryResponse = {
  periodStart: string; // ISO 8601 UTC
  periodEnd: string; // ISO 8601 UTC
  stages: BowtieStage[];
  overallConversionPct: number;
  overallRoiX: number | null;
  overallLtvCents: number | null;
  currency: string | null;
  lastSyncAt: string | null;
};

export type StageDetailResponse = {
  stage: RecommendationStage;
  label: string;
  periodStart: string;
  periodEnd: string;
  count: number;
  kpis: Array<{
    key: string;
    label: string;
    value: number | null;
    unit: string;
    currency: string | null;
  }>;
  trendData: Array<{
    date: string;
    value: number | null;
  }>;
};
