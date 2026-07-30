// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * AdrianRecuperarPage — /[tenantId]/adrian/recuperar.
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * Sub-tab hermana de Embudo (V4 spec v3.1).
 * Renders RecuperarView (frozen leads + decidio_no + diagnose + reactivate).
 *
 * spec_anchor: 01-spec.md § V4 + 03-arch-fe.md § RecuperarView D.11
 */

import { type Metadata } from "next";
import { RecuperarView } from "@/features/adrian";

export const metadata: Metadata = {
  title: "Recuperar — Adrián | Vitalia",
  description: "Leads congelados y reactivación",
};

interface PageProps {
  params: Promise<{ tenantId: string }>;
}

export default async function AdrianRecuperarPage({ params }: PageProps) {
  const { tenantId } = await params;

  return <RecuperarView tenantId={tenantId} />;
}
