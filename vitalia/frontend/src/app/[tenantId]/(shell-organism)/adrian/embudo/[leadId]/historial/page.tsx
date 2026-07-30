// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * LeadHistorialPage — /[tenantId]/adrian/embudo/[leadId]/historial.
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * Server Component shell. Renders LeadWorkspace (EntitySubNavBar workspace mode)
 * + HistorialView (timeline comercial, RN-2 firewall activo).
 *
 * RN-2 FIREWALL: HistorialView renders commercial activities only.
 * NO clinical data. Server-side filters it out before sending to FE.
 * Link to Inbox (PHI-gated) for the actual conversation.
 *
 * RN-16: leadId = UUID (never PHI in URL).
 * spec_anchor: 03-arch-fe.md § Routing + 01-spec.md § V3 Vista Historial
 */

import { type Metadata } from "next";
import { LeadWorkspace, HistorialView } from "@/features/adrian";

export const metadata: Metadata = {
  title: "Historial del lead — Adrián | Vitalia",
};

interface PageProps {
  params: Promise<{ tenantId: string; leadId: string }>;
}

export default async function LeadHistorialPage({ params }: PageProps) {
  const { tenantId, leadId } = await params;

  return (
    <LeadWorkspace tenantId={tenantId} leadId={leadId} activeLeaf="historial">
      <HistorialView leadId={leadId} tenantId={tenantId} />
    </LeadWorkspace>
  );
}
