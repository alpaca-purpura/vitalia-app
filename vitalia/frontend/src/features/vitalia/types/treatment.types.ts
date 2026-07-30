// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * Treatment types — mirrors Pydantic treatment_dtos.py Response DTOs.
 * snake_case preserved to match BE JSON field names.
 * ISO 8601 datetimes typed as string.
 */

// ── Request types ─────────────────────────────────────────────────────────────

export interface ManualHandoffRequest {
  reason?: string | null;
}

export interface StartFollowupRequest {
  plan_template_slug: string;
  procedure_date: string;
}

// ── Response types ────────────────────────────────────────────────────────────

export interface TreatmentSummary {
  id: string;
  booking_id: string;
  patient_id: string;
  doctor_id: string;
  plan_template_slug: string;
  current_step: string;
  started_at: string;
  last_response_at: string | null;
  next_scheduled_at: string | null;
  adherence_score: number | null;
}

export interface TreatmentListResponse {
  treatments: TreatmentSummary[];
  total: number;
}

export interface TreatmentDetailResponse {
  id: string;
  booking_id: string;
  patient_id: string;
  doctor_id: string;
  plan_template_slug: string;
  current_step: string;
  started_at: string;
  last_response_at: string | null;
  next_scheduled_at: string | null;
  adherence_score: number | null;
  paused_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface TreatmentFollowupStateResponse {
  treatment_id: string;
  current_step: string;
  adherence_score: number | null;
  last_response_at: string | null;
  next_scheduled_at: string | null;
  paused_reason: string | null;
}

export interface ManualHandoffResponse {
  treatment_id: string;
  status: string;
  handoff_at: string;
}

export interface ReleaseHandoffResponse {
  treatment_id: string;
  status: string;
  released_at: string;
}

// ── Patient types ─────────────────────────────────────────────────────────────

export interface PatientSummary {
  id: string;
  name_first: string;
  name_last_initial: string;
  phone_masked: string;
  email_masked: string;
  clinic_type: string | null;
  created_at: string;
}

export interface PatientListResponse {
  patients: PatientSummary[];
  total: number;
}

export interface PatientDetailResponse {
  id: string;
  name_first: string;
  name_last_initial: string;
  phone_masked: string;
  email_masked: string;
  medical_history_summary: string | null;
  clinic_type: string | null;
  created_at: string;
  updated_at: string;
}

export interface UploadMedicalPdfRequest {
  file_name: string;
  content_type: "application/pdf";
  base64_content: string;
}

export interface UploadMedicalPdfResponse {
  patient_id: string;
  extraction_job_id: string;
  status: string;
  estimated_completion_seconds: number;
}
