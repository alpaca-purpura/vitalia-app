// cap: fidelizacion.re-engagement
// story-origin: TBD
/**
 * re-engagement-event.ts — Zod schemas for re-engagement pattern API responses.
 *
 * Runtime validation for /api/v1/vitalia/fidelization/re-engagement/patterns.
 * Mirrors PatternRow + PatternListResponse from features/fidelizacion/types/re-engagement.ts.
 *
 * downstream-regression-na: brand-local FE schema; no cross-brand consumers
 */

import { z } from "zod";

export const urgencyLevelSchema = z.enum([
  "critical",
  "alert",
  "near",
  "waiting",
  "up_to_date",
]);

export const reEngagementPatternSchema = z.enum([
  "multi_session",
  "follow_up",
  "maintenance",
  "absence",
]);

export const reEngagementOutcomeSchema = z.enum([
  "appointment_booked",
  "patient_paused",
  "marked_external",
  "marked_no_continue",
  "manual_call_logged",
  "slots_suggested",
  "ignored",
]);

// Multi-session specific data
export const multiSessionDataSchema = z.object({
  sessionsSold: z.number().int(),
  sessionsCompleted: z.number().int(),
  sessionsRemaining: z.number().int(),
  packagePrice: z.number(),
  packageCurrency: z.string().optional().nullable(),
  packageName: z.string().optional().nullable(),
  daysSinceLastSession: z.number().int(),
  adherenceRate: z.number().optional().nullable(),
});

// Follow-up specific data
export const followUpDataSchema = z.object({
  appointmentDate: z.string(),
  treatmentName: z.string().optional().nullable(),
  postTreatmentDayTarget: z.number().int().optional().nullable(),
  daysSinceAppointment: z.number().int(),
  doctorName: z.string().optional().nullable(),
  doctorId: z.string().optional().nullable(),
});

// Maintenance specific data
export const maintenanceDataSchema = z.object({
  maintenanceIntervalDays: z.number().int(),
  daysSinceLastVisit: z.number().int(),
  treatmentName: z.string().optional().nullable(),
  doctorId: z.string().optional().nullable(),
  doctorName: z.string().optional().nullable(),
  packagesHistory: z.number().int().optional().nullable(),
});

// Absence specific data
export const absenceDataSchema = z.object({
  daysSinceLastVisit: z.number().int(),
  lastVisitDate: z.string().optional().nullable(),
  treatmentName: z.string().optional().nullable(),
  totalVisitCount: z.number().int().optional().nullable(),
  estimatedChurnRisk: z.number().optional().nullable(),
  doctorId: z.string().optional().nullable(),
  doctorName: z.string().optional().nullable(),
});

export const actionDescriptorSchema = z.object({
  id: z.string(),
  label: z.string(),
  disabled: z.boolean().optional(),
  disabledReason: z.string().optional().nullable(),
  isPrimary: z.boolean().optional(),
  variant: z.enum(["default", "outline", "ghost", "destructive"]).optional(),
});

export const patternRowSchema = z.object({
  reEngagementEventId: z.string(),
  patientId: z.string(),
  patientName: z.string().optional().nullable(),
  patientPhone: z.string().optional().nullable(),
  patientEmail: z.string().optional().nullable(),
  pattern: reEngagementPatternSchema,
  urgency: urgencyLevelSchema,
  treatmentVertical: z.string().optional().nullable(),
  lastOutcome: reEngagementOutcomeSchema.optional().nullable(),
  lastActionAt: z.string().optional().nullable(),
  lastContactAt: z.string().optional().nullable(),
  cronScheduledAt: z.string().optional().nullable(),
  npsScore: z.number().optional().nullable(),
  data: z.union([
    multiSessionDataSchema,
    followUpDataSchema,
    maintenanceDataSchema,
    absenceDataSchema,
  ]),
  availableActions: z.array(actionDescriptorSchema),
});

export const patternListResponseSchema = z.object({
  rows: z.array(patternRowSchema),
  total: z.number().int(),
  pattern: reEngagementPatternSchema,
  period: z.string(),
});

export type UrgencyLevelSchema = z.infer<typeof urgencyLevelSchema>;
export type ReEngagementPatternSchema = z.infer<
  typeof reEngagementPatternSchema
>;
export type PatternRowSchema = z.infer<typeof patternRowSchema>;
export type PatternListResponseSchema = z.infer<
  typeof patternListResponseSchema
>;
