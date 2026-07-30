// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * AdrianEmbudoPage — Server Component for /[tenantId]/adrian/embudo.
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * ADR-vitalia-004 § 3.1: static route segment /embudo.
 * Responsibilities:
 *   1. Await params + searchParams (Next.js 16 App Router — Promise-based)
 *   2. SSR initial board state (getEmbudoBoardInitialState — graceful degradation)
 *   3. Pass initialBoard to AdrianEmbudoView (client root)
 *
 * No PHI in metadata. No "use client" — Server Component.
 * Auth: (shell-organism)/layout.tsx handles Clerk validation + tenant redirect.
 *
 * spec_anchor: 03-arch-fe.md § Routing + 03-arch.md § 4 (GET /crm/board)
 */

import { type Metadata } from "next";
import { AdrianEmbudoView } from "@/features/adrian";
// getEmbudoBoardInitialState is Server-only — imported directly (not via the client
// barrel index.ts, per features/adrian/index.ts note). Belongs in the arch allowlist
// KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS (pending — that test file is mid-edit by the
// concurrent inbox session; entry to be added when the hub is coordinated).
import { getEmbudoBoardInitialState } from "@/features/adrian/api/embudo-server";

export const metadata: Metadata = {
  title: "Embudo — Adrián | Vitalia",
  description: "Supervisión del funnel de leads operado por Adrián",
};

// ── Page Props ────────────────────────────────────────────────────────────────

interface PageProps {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{ view?: string; sort?: string }>;
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function AdrianEmbudoPage({
  params,
  searchParams,
}: PageProps) {
  const { tenantId } = await params;
  const sp = await searchParams;

  const view = sp.view === "lista" ? "lista" : "kanban";
  const sort = (sp.sort as "stage_age_desc" | "score_desc" | "value_desc" | "last_activity_desc")
    ?? "stage_age_desc";

  // SSR initial data — graceful degradation on error
  const initialBoard = await getEmbudoBoardInitialState({
    tenantId,
    filters: { view, sort },
  });

  return (
    <AdrianEmbudoView
      initialBoard={initialBoard}
      tenantId={tenantId}
    />
  );
}
