// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * ReEngagementContactSidebar — wraps shared ContactSidebar for fidelización.
 *
 * Composes @/components/shared/contact-sidebar with fidelización-specific props.
 * Passes minimal non-PHI contact info (patientId only); ContactSidebar
 * handles PHI display with its own PiiMaskedSpan masking.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { ContactSidebar } from "@/components/shared/contact-sidebar";

interface ReEngagementContactSidebarProps {
  patientId: string | null;
  /** Patient name — PHI, will be masked inside ContactSidebar */
  patientName?: string | null;
  onClose?: () => void;
}

/**
 * Sidebar panel showing patient contact info when a card is selected.
 * Uses the shared ContactSidebar component (reuse per anti-duplication.md).
 */
export function ReEngagementContactSidebar({
  patientId,
  patientName,
}: ReEngagementContactSidebarProps) {
  if (!patientId) return null;

  return (
    <ContactSidebar
      contact={{
        patientId,
        name: patientName ?? null,
      }}
    />
  );
}
