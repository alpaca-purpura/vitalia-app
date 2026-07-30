// cap: __shared__
// story-origin: TBD
/**
 * Shell Organism Root Page — Server Component redirect.
 * F1-S4 vitalia-fase1-shell-layout-5050 — T-4 (MODIFIED by F1-S9)
 *
 * 03-arch-fe.md § 2.2 MODIFY — verbatim spec.
 *
 * Visiting /{tenantId} immediately redirects server-side a
 * /{tenantId}/{DEFAULT_LANDING_SUBPATH} (= mateo/agenda v1.2; default landing).
 *
 * Bug #1 fix (vitalia-bugfix-shell-nav-scroll-errors T-1): antes redirigía a
 * `valeria/agenda`, que 404ea (isValidAgent('valeria') === false — Valeria es
 * supervisora sidebar, no ribbon agent). La agenda migró a mateo/agenda
 * (paradigm-map-zones T-5). El destino vive ahora en el SSoT DEFAULT_LANDING_SUBPATH
 * (lib/shell-routes.ts) para no driftear de nuevo.
 *
 * No "use client" — redirect() is a Server Action (Next.js App Router).
 * Next.js 16: params is Promise, must be awaited before use.
 *
 * SC-1: navega a /{tenantId} → redirect a /{tenantId}/mateo/agenda.
 *
 * HIPAA-lite: not applicable — routing only, no PHI.
 * downstream-regression-na: brand-local route; no cross-brand consumers.
 */

import { redirect } from "next/navigation";

import { DEFAULT_LANDING_SUBPATH } from "@/lib/shell-routes";

interface PageProps {
  params: Promise<{ tenantId: string }>;
}

export default async function ShellRootPage({ params }: PageProps) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/${DEFAULT_LANDING_SUBPATH}`);
}
