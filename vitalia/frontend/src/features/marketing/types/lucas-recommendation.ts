// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * Lucas recommendation domain types — mirror of BE LucasRecommendationResponse (camelCase)
 * downstream-regression-na: brand-local FE type; consumed by marketing feature only
 */

export type RecommendationStage =
  | "attraction"
  | "qualification"
  | "reservation"
  | "adoption"
  | "expansion";

export type RecommendationStatus =
  | "open"
  | "approved"
  | "rejected"
  | "expired"
  | "undone";

export type RejectReason =
  | "not_priority"
  | "already_doing"
  | "data_wrong"
  | "too_risky"
  | "other";

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
  approvedAt: string | null; // ISO 8601 UTC
  undoUntil: string | null;
  expiresAt: string; // ISO 8601 UTC
  createdAt: string; // ISO 8601 UTC
};

export type LucasRecommendationsResponse = {
  items: LucasRecommendation[];
};

export type ApproveRecommendationResponse = LucasRecommendation;
export type RejectRecommendationResponse = LucasRecommendation;
export type UndoRecommendationResponse = LucasRecommendation;
