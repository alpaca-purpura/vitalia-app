// cap: scheduling.mateo-agenda
// story-origin: vitalia-paradigm-map-zones
/**
 * MateoAgendaPage — Server Component.
 * Migrated from valeria/agenda (paradigm-map-zones T-5 v1.2 2026-05-30).
 * Mateo = Operar (agenda + pacientes del día). Valeria = supervisor sidebar only.
 *
 * Static route segment /mateo/agenda takes precedence over [agent]/[subtab]
 * per Next.js static-vs-dynamic routing rules (03-arch.md § 6.0).
 *
 * Responsibilities:
 *   1. Await params + searchParams (Next.js 16 App Router — Promise-based).
 *   2. Resolve view/date/presetFilter from URL (SSoT).
 *   3. Call getInitialAgendaState() for SSR hydration (graceful degradation).
 *   4. Pass initialData to MateoAgendaView (client root).
 *
 * No "use client" — Server Component.
 * Auth: shell-organism layout handles Clerk validation + tenant redirect.
 * HIPAA-lite: no PHI in metadata, no PHI in server logs.
 *
 * spec_anchor: 03-arch-fe.md § F6 + 06-tickets.yaml T-5
 * downstream-regression-na: brand-local route; no cross-brand consumers.
 */

import { type Metadata } from "next";
import {
  MateoAgendaView,
  getInitialAgendaState,
} from "@/features/mateo";
import type { AgendaView } from "@/features/mateo";

export const metadata: Metadata = {
  title: "Agenda — Mateo | Vitalia",
  description: "Gestión de citas y pagos de tu clínica",
};

interface PageProps {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{
    view?: string;
    date?: string;
    preset_filter?: string;
  }>;
}

const VALID_VIEWS: AgendaView[] = ["dia", "semana", "mes"];

function resolveView(raw?: string): AgendaView {
  if (raw && (VALID_VIEWS as string[]).includes(raw)) {
    return raw as AgendaView;
  }
  return "semana";
}

export default async function MateoAgendaPage({
  params,
  searchParams,
}: PageProps) {
  const { tenantId } = await params;
  const sp = await searchParams;

  const view = resolveView(sp.view);
  const date = sp.date ?? new Date().toISOString().slice(0, 10);
  // Cast to AgendaFilter | null — route layer validates trusted searchParams.
  // Unknown values reach the server as null (no PHI in URL per HIPAA-lite).
  const presetFilter = (sp.preset_filter ?? null) as import("@/features/mateo").AgendaFilter | null;

  // SSR initial data — graceful degradation (returns empty grid on error).
  // The HIPAA-lite actor context (X-Clinic-ID + X-User-ID + X-User-Role) the agenda grid
  // endpoint REQUIRES is resolved server-side inside getInitialAgendaState (X-Clinic-ID from
  // the Clerk user's publicMetadata.clinicId — the dev JWT has no clinic claim, which was the
  // bug). vitalia-bugfix-agenda-actor-headers-422.
  const initialData = await getInitialAgendaState({
    tenantId,
    view,
    date,
    presetFilter,
  });

  return (
    <MateoAgendaView
      initialData={initialData}
      initialView={view}
      initialDate={date}
      initialPresetFilter={presetFilter}
      tenantId={tenantId}
    />
  );
}
