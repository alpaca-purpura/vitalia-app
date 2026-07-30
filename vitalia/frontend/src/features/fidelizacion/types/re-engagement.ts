// cap: patients.nps-tracking
// story-origin: TBD
/**
 * re-engagement.ts — TS types mirroring Pydantic DTOs.
 *
 * camelCase mirror of snake_case BE DTOs (per 03-arch-fe.md § 2).
 * ISO 8601 datetimes as `string`. Explicit fields — no `any`.
 *
 * downstream-regression-na: brand-local FE types; no cross-brand consumers
 */

export type ReEngagementPattern =
  | "multi_session"
  | "follow_up"
  | "maintenance"
  | "absence"
  | "nps";

export type ReEngagementOutcome =
  | "sent"
  | "responded"
  | "rescheduled"
  | "declined"
  | "not_responsive"
  | "opted_out"
  | "failed_sending";

export type UrgencyLevel =
  | "critical"
  | "alert"
  | "near"
  | "waiting"
  | "up_to_date";

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
  /** Formatted string, e.g. "3 meses" */
  followUpRequestedDuration: string;
  followUpSetAt: string;
  followUpDueAt: string;
  /** Negative if past due */
  daysUntilDue: number;
  followUpReason: string | null;
}

export interface MaintenanceData {
  kind: "maintenance";
  offerLabel: string;
  /** e.g. "Cada 6 meses" */
  cadenceLabel: string;
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
  /** Null if no revenue tracked */
  lifetimeValueCents: number | null;
  /** Explicit per master-data.md — never hardcode currency */
  currency: string | null;
  lastDoctorName: string;
  marketingOptIn: boolean;
}

export type PatternData =
  | MultiSessionData
  | FollowUpData
  | MaintenanceData
  | AbsenceData;

export type ActionId =
  | "send_reminder"
  | "suggest_slots"
  | "pause_patient"
  | "mark_external"
  | "mark_no_continue"
  | "open_conversation"
  | "call_manually";

export interface ActionDescriptor {
  id: ActionId;
  enabled: boolean;
  /** e.g. "Paciente no aceptó marketing" */
  disabledReason: string | null;
}

export interface PatternRow {
  reEngagementEventId: string;
  patientId: string;
  /** PHI — masked unless RequireRole guard passes */
  patientName: string;
  pattern: ReEngagementPattern;
  urgency: UrgencyLevel;
  patternData: PatternData;
  acciones: ActionDescriptor[];
}

export interface PatternListResponse {
  rows: PatternRow[];
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
  /** 7 | 30 | custom (days) */
  durationDays: number;
  reason: string | null;
}

export interface PausePatientResponse {
  resumeAt: string;
}

export interface MarkExternalRequest {
  reason: string;
}

export interface MarkExternalResponse {
  ok: boolean;
}

export interface MarkNoContinueRequest {
  reason: string;
}

export interface MarkNoContinueResponse {
  ok: boolean;
}

export interface LogManualCallRequest {
  notes: string;
  outcome: "reached" | "voicemail" | "no_answer";
  callDurationSeconds: number | null;
}

export interface LogManualCallResponse {
  eventId: string;
  loggedAt: string;
}
