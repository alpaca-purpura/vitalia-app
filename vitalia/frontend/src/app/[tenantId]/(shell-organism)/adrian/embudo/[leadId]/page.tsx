// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * LeadIdRedirectPage — Redirects /embudo/[leadId] → /embudo/[leadId]/resumen.
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * Default tab is "resumen" per spec V3.
 * Uses server-side redirect() — nav dura (not soft-nav intra-group).
 *
 * ⚠️ MEMORY.md::next16-softnav-redirect: if "Rendered more hooks" flakiness is
 * observed with redirect() inside dynamic routes + shell ssr:false, move to
 * edge redirect in proxy.ts. See docs/learnings/2026-06-03-next16-softnav.md.
 *
 * RN-16: leadId = UUID (never PHI in URL).
 * spec_anchor: 03-arch-fe.md § Routing
 */

import { redirect } from "next/navigation";

interface PageProps {
  params: Promise<{ tenantId: string; leadId: string }>;
}

export default async function LeadIdRedirectPage({ params }: PageProps) {
  const { tenantId, leadId } = await params;
  redirect(`/${tenantId}/adrian/embudo/${leadId}/resumen`);
}
