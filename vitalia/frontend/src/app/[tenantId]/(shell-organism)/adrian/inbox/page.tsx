// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * AdrianInboxPage — Server Component.
 * T-3 vitalia-fase2-adrian-inbox (CONN: ruta estática)
 *
 * Static route segment /adrian/inbox takes precedence over [agent]/[subtab]
 * per Next.js static-vs-dynamic routing rules (03-arch-fe.md § 1).
 *
 * Responsibilities:
 *   1. Await params + searchParams (Next.js 16 App Router — Promise-based).
 *   2. Validate + whitelist searchParams (conv UUID, filter enum).
 *   3. Call getInitialInboxState() for SSR hydration (graceful degradation).
 *   4. Pass initialData to AdrianInboxView (client root).
 *
 * HIPAA-lite: no PHI in metadata; PHI never in URL — only ?conv={UUID}, never patient name/data.
 * No "use client" — Server Component.
 * Auth: (shell-organism)/layout.tsx handles Clerk validation + tenant redirect.
 *
 * spec_anchor: 03-arch-fe.md § 1 + 06-tickets.yaml T-3
 * downstream-regression-na: brand-local route; no cross-brand consumers.
 */

import { type Metadata } from "next";
import {
  AdrianInboxView,
  getInitialInboxState,
} from "@/features/adrian";

export const metadata: Metadata = {
  title: "Inbox — Adrián | Vitalia",
  description: "Gestión de conversaciones y leads de tu clínica",
};

// ── Whitelist de filtros URL válidos (RN-14 — PHI nunca en URL) ────────────────

const VALID_FILTERS = new Set([
  "todos",
  "sin-leer",
  "asignadas",
  "esperando",
  "bot-activo",
  "cerradas",
]);

/** UUID-pattern guard — only allows RFC 4122-ish UUIDs (defence-in-depth). */
const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function resolveConvId(raw?: string): string | null {
  if (!raw) return null;
  // PHI-safe: reject any value that isn't a UUID format
  return UUID_RE.test(raw) ? raw : null;
}

function resolveFilter(raw?: string): string | null {
  if (!raw) return null;
  return VALID_FILTERS.has(raw) ? raw : null;
}

// ── Page Props ────────────────────────────────────────────────────────────────

interface PageProps {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{
    conv?: string;
    filter?: string;
  }>;
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function AdrianInboxPage({
  params,
  searchParams,
}: PageProps) {
  const { tenantId } = await params;
  const sp = await searchParams;

  const convId = resolveConvId(sp.conv);
  const filter = resolveFilter(sp.filter);

  // SSR initial data — graceful degradation (returns empty state on error)
  const initialData = await getInitialInboxState({
    tenantId,
    convId,
    filter,
  });

  return (
    <AdrianInboxView
      initialData={initialData}
      initialConvId={convId}
      initialFilter={filter}
      tenantId={tenantId}
    />
  );
}
