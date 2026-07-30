// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * LeadResumenPage — /[tenantId]/adrian/embudo/[leadId]/resumen.
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * Server Component shell. Renders LeadWorkspace (EntitySubNavBar workspace mode)
 * + ResumenView (Datos + Estado agente + Score glass-box).
 *
 * RN-16: leadId = UUID (never PHI in URL — test_no_phi_in_url_params).
 * ADR-vitalia-004 § 3.1 Server Component + "use client" client root.
 * spec_anchor: 03-arch-fe.md § Routing + 01-spec.md § V3 Vista Resumen
 */

import { type Metadata } from "next";
import { LeadWorkspace, ResumenView } from "@/features/adrian";

export const metadata: Metadata = {
  title: "Resumen del lead — Adrián | Vitalia",
};

interface PageProps {
  params: Promise<{ tenantId: string; leadId: string }>;
}

export default async function LeadResumenPage({ params }: PageProps) {
  const { tenantId, leadId } = await params;

  return (
    <LeadWorkspace tenantId={tenantId} leadId={leadId} activeLeaf="resumen">
      <ResumenView leadId={leadId} tenantId={tenantId} />
    </LeadWorkspace>
  );
}
