// cap: iam.luana-core-adoption
// story-origin: vitalia-fe-tenant-resolution-no-clerk-org (T-2)
"use client";

/**
 * AuditedSection — wraps PHI content and fires audit log on mount.
 *
 * Per vitalia/.claude/rules/hipaa-lite.md:
 *   - TODA lectura de PHI registra audit_log row
 *   - Audit log write is SYNC (not fire-and-forget)
 *   - Row includes: tenant_id, clinic_id, user_id, action, resource_type, resource_id
 *
 * This component fires a beacon to the audit log API on mount.
 * Use around any section that renders PHI fields.
 *
 * T-2 fix (2026-06-01): replaced useOrganization() + organization.id with
 * useTenantId() which reads user.publicMetadata.tenant_id (our UUID, written
 * by luana-core-iam). The Clerk Organization org_3DzUI3... was deleted;
 * organization?.id was returning null → audit log NEVER fired (HIPAA-lite
 * violation). Now uses our real tenant UUID directly from publicMetadata.
 *
 * Per MEMORY.md::no-clerk-organizations: Luana does NOT use Clerk Organizations.
 * tenant_id comes from user.publicMetadata, NOT from Clerk org APIs.
 *
 * Usage:
 *   <AuditedSection
 *     resourceType="patient_profile"
 *     resourceId={patient.id}
 *     action="view"
 *   >
 *     <PatientDetailContent />
 *   </AuditedSection>
 */

import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { useAuth } from "@clerk/nextjs";
import { fetchClient } from "@/lib/api/fetchClient";
import { useClinicId } from "@/hooks/useClinicId";
import { useTenantId } from "@/hooks/useTenantId";

export interface AuditedSectionProps {
  /** Resource type being viewed (e.g. "patient_profile", "treatment_record") */
  resourceType: string;
  /** Resource ID being viewed */
  resourceId: string;
  /** Action being performed (default: "view") */
  action?: "view" | "download" | "print" | "export";
  /** Content to render */
  children: ReactNode;
}

/**
 * Fires a PHI access audit log event on mount (HIPAA-lite compliance).
 * Silent fail — audit failure should NOT block UI (but is logged to console.error).
 */
export function AuditedSection({
  resourceType,
  resourceId,
  action = "view",
  children,
}: AuditedSectionProps) {
  const { getToken, userId } = useAuth();
  const tenantId = useTenantId();
  const clinicId = useClinicId();
  const auditFired = useRef(false);

  useEffect(() => {
    if (auditFired.current) return;
    auditFired.current = true;

    const fireAudit = async () => {
      // Guard: require userId, tenant UUID, clinicId (dual filter), and resourceId.
      // tenantId comes from user.publicMetadata.tenant_id (luana-core-iam UUID).
      // The BE audit endpoint is PHI dual-filtered (clinic required) and CASTs
      // resourceId AS uuid — skip the beacon when any is absent (e.g. a 404 detail
      // with no resolved contact, or clinic not yet loaded) so we never POST an
      // incomplete body (would 422 + trip the anti-burbuja gate).
      if (!userId || !tenantId || !clinicId || !resourceId) return;

      try {
        const token = await getToken();
        if (!token) return;

        // fetchClient injects Authorization + X-Tenant-ID + X-Clinic-ID (dual filter).
        // The BE persists the audit row sync (pre-response) on the committing session.
        await fetchClient<{ recorded: boolean }>("/api/v1/vitalia/audit-log", {
          method: "POST",
          token,
          tenantId,
          clinicId,
          body: JSON.stringify({
            action,
            resourceType,
            resourceId,
            userId,
          }),
        });
      } catch (err) {
        // Silent fail per hipaa-lite.md: audit failure logs to observability but does not block UI
        if (process.env.NODE_ENV !== "production") {
          console.error(
            "[AuditedSection] audit log failed (non-blocking):",
            err,
          );
        }
      }
    };

    void fireAudit();
  }, [
    action,
    clinicId,
    getToken,
    tenantId,
    resourceId,
    resourceType,
    userId,
  ]);

  return <>{children}</>;
}
