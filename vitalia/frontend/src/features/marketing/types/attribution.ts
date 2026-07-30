// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * Attribution matrix domain types — mirror of BE AttributionMatrixResponse (camelCase)
 * downstream-regression-na: brand-local FE type; consumed by marketing feature only
 * HIPAA-lite: NO patient names in attribution — only hashed IDs and aggregate stats
 */

export type AttributionOrigin =
  | "sales_agent"
  | "walk_in"
  | "phone_manual"
  | "proactive_outbound";

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
  periodStart: string; // ISO 8601 UTC
  periodEnd: string; // ISO 8601 UTC
  origins: AttributionOriginRow[];
  totals: AttributionOriginRow;
  topInsightText: string | null;
  currency: string | null;
};
