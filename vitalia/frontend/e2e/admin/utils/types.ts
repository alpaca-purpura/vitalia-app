/**
 * types.ts — Shared types for Playwright admin-smoke DB verification.
 *
 * downstream-regression-na: brand-local E2E test utility; no cross-brand consumers
 */

export interface DbStateResponse {
  tenants: number;
  users: number;
  user_tenants: number;
  clinics: number;
}

export interface AuditLogEntry {
  id: string;
  tenant_id: string | null;
  clinic_id: string | null;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  occurred_at: string;
}
