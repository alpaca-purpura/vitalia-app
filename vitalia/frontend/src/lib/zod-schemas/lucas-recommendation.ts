// cap: marketing.lucas-stage-recommendations
// story-origin: TBD
/**
 * Zod schema for LucasRecommendation — mirrors Pydantic LucasRecommendationResponse (snake_case)
 * Used for runtime validation of BE API responses.
 * downstream-regression-na: brand-local FE schema; no cross-brand consumers
 */

import { z } from "zod";

export const recommendationStageSchema = z.enum([
  "attraction",
  "qualification",
  "reservation",
  "adoption",
  "expansion",
]);

export const recommendationStatusSchema = z.enum([
  "open",
  "approved",
  "rejected",
  "expired",
  "undone",
]);

export const rejectReasonSchema = z.enum([
  "not_priority",
  "already_doing",
  "data_wrong",
  "too_risky",
  "other",
]);

/**
 * Mirrors Pydantic LucasRecommendationResponse (snake_case keys per BE DTOs).
 * Used to validate raw API responses before camelCase transformation.
 */
export const lucasRecommendationSchema = z.object({
  id: z.string(),
  tenant_id: z.string(),
  clinic_id: z.string(),
  stage: recommendationStageSchema,
  recommendation_kind: z.string(),
  title: z.string(),
  body: z.string(),
  rationale_json: z.record(z.string(), z.unknown()),
  action_payload_json: z.record(z.string(), z.unknown()).nullable(),
  priority: z.number().int().min(1),
  confidence_pct: z.number().nullable(),
  projected_impact_text: z.string().nullable(),
  status: recommendationStatusSchema,
  approved_by_user_id: z.string().nullable(),
  approved_at: z.string().datetime({ offset: true }).nullable(),
  undo_until: z.string().datetime({ offset: true }).nullable(),
  expires_at: z.string().datetime({ offset: true }),
  created_at: z.string().datetime({ offset: true }),
});

export const lucasRecommendationsResponseSchema = z.object({
  items: z.array(lucasRecommendationSchema),
});

export type LucasRecommendationRaw = z.infer<typeof lucasRecommendationSchema>;
export type LucasRecommendationsResponseRaw = z.infer<
  typeof lucasRecommendationsResponseSchema
>;
