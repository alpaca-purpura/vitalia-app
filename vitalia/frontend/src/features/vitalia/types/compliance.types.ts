// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * Compliance types — mirrors Pydantic compliance_dtos.py Response DTOs.
 * snake_case preserved to match BE JSON field names.
 * payload_redacted is pre-sanitized at BE write time (no raw PII).
 */

export type ComplianceSeverity = "info" | "medium" | "high";

export type ActorType = "clinic_owner" | "sales_agent" | "system" | "patient";

export interface ComplianceEventItem {
  id: string;
  event_type: string;
  severity: ComplianceSeverity;
  patient_id: string | null;
  booking_id: string | null;
  payload_redacted: Record<string, unknown>;
  actor_id: string | null;
  actor_type: ActorType | null;
  created_at: string;
}

export interface ComplianceEventListResponse {
  events: ComplianceEventItem[];
  total: number;
  page: number;
  page_size: number;
}
