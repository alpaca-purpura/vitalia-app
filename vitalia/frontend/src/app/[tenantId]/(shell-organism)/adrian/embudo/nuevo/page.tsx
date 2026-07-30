// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * NuevoLeadPage — /[tenantId]/adrian/embudo/nuevo.
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * Ruta-hoja (not a modal) per spec V5.
 * Static segment "nuevo" resolves before [leadId] (RN-19).
 * Renders NewLeadPage (RHF+Zod form + EntitySubNavBar workspace mode).
 *
 * spec_anchor: 01-spec.md § V5 D.10 + SC-nuevo
 */

import { type Metadata } from "next";
import { NewLeadPage } from "@/features/adrian";

export const metadata: Metadata = {
  title: "Nuevo lead — Adrián | Vitalia",
};

interface PageProps {
  params: Promise<{ tenantId: string }>;
}

export default async function NuevoLeadPageRoute({ params }: PageProps) {
  const { tenantId } = await params;

  return <NewLeadPage tenantId={tenantId} />;
}
