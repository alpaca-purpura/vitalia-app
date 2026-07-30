// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
/**
 * nuevo/page.tsx — "Nuevo servicio" creation flow (Server Component).
 *
 * Renders BibliotecaPicker inline (NOT a modal — RN-16, RN-25).
 * On "Usar plantilla": POST /servicios/from-template → redirect [offer-id]/resumen.
 * On "Crear personalizado": POST /servicios/custom → redirect [offer-id]/resumen.
 *
 * Crear = editar (RN-16): same workspace, borrador chip + low completeness.
 * ADR-vitalia-004 § 3.1 · spec_anchor: 03-arch-fe.md § Routing
 */

import type { Metadata } from "next";
import { BibliotecaPicker } from "@/features/lisa";

export const metadata: Metadata = {
  title: "Nuevo servicio — Vitalia",
};

interface NuevoServicioPageProps {
  params: Promise<{ tenantId: string }>;
}

export default async function NuevoServicioPage({ params }: NuevoServicioPageProps) {
  const { tenantId } = await params;
  return <BibliotecaPicker tenantId={tenantId} />;
}
