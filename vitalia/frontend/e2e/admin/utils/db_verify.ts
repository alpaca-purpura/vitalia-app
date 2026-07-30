/**
 * db_verify.ts — Playwright admin-smoke DB verification via internal API.
 *
 * Calls the guarded admin helper endpoints at /api/v1/vitalia/admin/db-state
 * and /api/v1/vitalia/admin/audit-log. Both require X-Internal-Token header.
 *
 * SECURITY: VITALIA_INTERNAL_API_TOKEN NEVER hardcoded. Injected via env var.
 *
 * downstream-regression-na: brand-local E2E test utility; no cross-brand consumers
 */

import type { APIRequestContext } from "@playwright/test";
import type { AuditLogEntry, DbStateResponse } from "./types";

const BACKEND_URL = process.env["E2E_BACKEND_URL"] ?? "http://127.0.0.1:8002";
const INTERNAL_TOKEN = process.env["VITALIA_INTERNAL_API_TOKEN"] ?? "";

/**
 * Fetch current DB row counts for engine IAM tables + vitalia_clinic_branches.
 * Used by Playwright specs to assert create/delete operations.
 */
export async function getDbState(
  request: APIRequestContext,
): Promise<DbStateResponse> {
  const res = await request.get(
    `${BACKEND_URL}/api/v1/vitalia/admin/db-state`,
    { headers: { "X-Internal-Token": INTERNAL_TOKEN } },
  );
  if (!res.ok()) {
    throw new Error(`db-state ${res.status()}: ${await res.text()}`);
  }
  return res.json() as Promise<DbStateResponse>;
}

/**
 * Fetch sanitized audit log entries.
 * @param opts.action - Filter by action string (e.g. "tenant.create")
 * @param opts.sinceMsAgo - Only entries since N milliseconds ago
 */
export async function getAuditLog(
  request: APIRequestContext,
  opts: { action?: string; sinceMsAgo?: number } = {},
): Promise<AuditLogEntry[]> {
  const params: Record<string, string> = {};
  if (opts.action) params["action"] = opts.action;
  if (opts.sinceMsAgo) {
    params["since"] = new Date(Date.now() - opts.sinceMsAgo).toISOString();
  }
  const qs = new URLSearchParams(params).toString();
  const url = `${BACKEND_URL}/api/v1/vitalia/admin/audit-log${qs ? "?" + qs : ""}`;
  const res = await request.get(url, {
    headers: { "X-Internal-Token": INTERNAL_TOKEN },
  });
  if (!res.ok()) {
    throw new Error(`audit-log ${res.status()}: ${await res.text()}`);
  }
  return res.json() as Promise<AuditLogEntry[]>;
}
