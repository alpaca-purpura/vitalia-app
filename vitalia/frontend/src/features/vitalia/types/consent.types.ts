// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * Consent types — mirrors Pydantic consent_dtos.py Response DTOs.
 * snake_case preserved to match BE JSON field names.
 * PII fields (signed_ip, signed_user_agent, signed_name) NOT exposed per HIPAA-lite.
 */

export interface ConsentRecordResponse {
  id: string;
  patient_id: string;
  booking_id: string | null;
  consent_template_slug: string;
  template_version: string;
  status: string;
  expires_at: string;
  signed_at: string | null;
  signature_method: string | null;
  delivery_channels: string[];
  created_at: string;
}

export interface ConsentRecordListResponse {
  records: ConsentRecordResponse[];
  total: number;
}
