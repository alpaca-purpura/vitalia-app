// cap: observability.otel-sentry-graceful-degradation
// story-origin: TBD
/**
 * nps.ts — Zod schemas for NPS response API.
 *
 * Runtime validation of NPS endpoints.
 * Mirrors NPSSummaryResponse + NPSRowDTO types from features/fidelizacion/types/nps.ts.
 *
 * downstream-regression-na: brand-local FE schema; no cross-brand consumers
 */

import { z } from "zod";

export const npsBandSchema = z.enum(["promoter", "passive", "detractor"]);

export const npsRowSchema = z.object({
  id: z.string(),
  patientId: z.string(),
  patientName: z.string().optional().nullable(),
  score: z.number().int().min(0).max(10),
  band: npsBandSchema,
  comment: z.string().optional().nullable(),
  treatmentVertical: z.string().optional().nullable(),
  respondedAt: z.string(), // ISO 8601
  npsResponseUrl: z.string().optional().nullable(),
});

export const npsSummaryResponseSchema = z.object({
  averageScore: z.number(),
  npsIndex: z.number(),
  totalResponses: z.number().int(),
  promotersCount: z.number().int(),
  passivesCount: z.number().int(),
  detractorsCount: z.number().int(),
  rows: z.array(npsRowSchema),
});

export type NpsBandSchema = z.infer<typeof npsBandSchema>;
export type NpsRowSchema = z.infer<typeof npsRowSchema>;
export type NpsSummaryResponseSchema = z.infer<typeof npsSummaryResponseSchema>;
