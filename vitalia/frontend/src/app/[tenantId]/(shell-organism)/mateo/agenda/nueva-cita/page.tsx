// cap: scheduling.mateo-agenda
/**
 * NuevaCitaPage — Server Component.
 * T-FE-1 vitalia-fase2-mateo-nueva-cita
 *
 * Full-page appointment creation leaf sheet (AC-9 — no modal/drawer).
 * Reads ?date= and ?time= from URL for slot prefill (PHI-free; date/time
 * are scheduling metadata, not patient data — per hipaa-lite.md).
 *
 * Auth: (shell-organism) layout handles Clerk auth + tenant redirect.
 * No SSR data fetch here — services + doctors load client-side (React Query)
 * since they need auth headers. The page itself is a thin server shell.
 *
 * spec_anchor: 03-arch-fe.md § F3 + 06-tickets.yaml T-FE-1
 * downstream-regression-na: brand-local route; no cross-brand consumers.
 */

import { type Metadata } from "next";
import { NuevaCitaView } from "@/features/mateo";

export const metadata: Metadata = {
  title: "Nueva cita — Mateo | Vitalia",
  description: "Crear una nueva cita en la agenda",
};

interface PageProps {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{
    /** Pre-selected date YYYY-MM-DD (from empty slot click). PHI-free. */
    date?: string;
    /** Pre-selected time HH:mm (from empty slot click). PHI-free. */
    time?: string;
    /** Pre-selected origin ("walk_in"|"telefono") from CrearCitaButton. */
    origin?: string;
  }>;
}

export default async function NuevaCitaPage({ params, searchParams }: PageProps) {
  const { tenantId } = await params;
  const sp = await searchParams;

  return (
    <NuevaCitaView
      tenantId={tenantId}
      prefillDate={sp.date}
      prefillTime={sp.time}
    />
  );
}
