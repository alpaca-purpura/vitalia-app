// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
/**
 * [offer-id]/layout.tsx — Server Component layout for the servicio workspace.
 *
 * SSR-fetches the service detail once and passes it as initialServicio to
 * ServicioWorkspaceShell (which seeds the React Query cache — no fetch flash on
 * first paint). The active leaf is URL-derived inside the shell via usePathname().
 *
 * Store-free skeleton (G2): this layout is a pure Server Component.
 * ServicioWorkspaceShell ("use client") is imported directly — Next.js handles
 * the Server→Client boundary at the component level.
 *
 * Not-PHI: catalog detail gated by X-Tenant-ID only (RN-13, no clinic gate).
 * ADR-vitalia-004 § 3.1 · spec_anchor: 03-arch-fe.md § Routing
 */

import type { ReactNode } from "react";
import { getServicioDetail, ServicioWorkspaceShell } from "@/features/lisa";

interface ServicioWorkspaceLayoutProps {
  children: ReactNode;
  params: Promise<{ tenantId: string; "offer-id": string }>;
}

export default async function ServicioWorkspaceLayout({
  children,
  params,
}: ServicioWorkspaceLayoutProps) {
  const { tenantId, "offer-id": offerId } = await params;

  // SSR seed — null on fetch error → client React Query takes over.
  const initialServicio = await getServicioDetail({ tenantId, offerId });

  return (
    <ServicioWorkspaceShell
      tenantId={tenantId}
      offerId={offerId}
      initialServicio={initialServicio ?? undefined}
      // activeLeaf NOT passed — shell derives from usePathname() for static segments
    >
      {children}
    </ServicioWorkspaceShell>
  );
}
