// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s9-TBD
/**
 * Agent Root Page — Server Component redirect.
 * F1-S9 vitalia-fase1-routing-shell — T-4
 *
 * 03-arch-fe.md § 9.5 — verbatim spec.
 *
 * Visiting /{tenantId}/{agent} redirects server-side to the agent's defaultSubtab.
 * Defense-in-depth: calls notFound() if agent is invalid (layout should have
 * already caught this, but this page can also be hit directly in some Next.js
 * render paths).
 *
 * Special case: 'config' is a RibbonTabSlug but NOT an AgentSlug → not in
 * AGENT_CATALOG. Its defaultSubtab = 'cuenta' (first tab per RIBBON_SUBTABS[config]).
 *
 * No "use client" — redirect() / notFound() are Server Actions.
 * Next.js 16: params is Promise → await before use.
 *
 * spec_anchor: 03-arch-fe.md § 9.5 + 06-tickets.yaml T-4
 * downstream-regression-na: brand-local route; no cross-brand consumers.
 */

import { redirect, notFound } from "next/navigation";

import {
  AGENT_CATALOG,
  isValidAgent,
  type AgentSlug,
  type RibbonTabSlug,
} from "@/lib/agent-catalog";

/**
 * Returns the default subtab for a given RibbonTabSlug.
 * Handles 'config' separately since it is not in AGENT_CATALOG (Record<AgentSlug, ...>).
 */
function getDefaultSubtab(agent: RibbonTabSlug): string {
  if (agent === "config") return "cuenta";
  return AGENT_CATALOG[agent as AgentSlug].defaultSubtab;
}

interface PageProps {
  params: Promise<{ tenantId: string; agent: string }>;
}

export default async function AgentRootPage({ params }: PageProps) {
  const { tenantId, agent } = await params;
  if (!isValidAgent(agent)) notFound();
  const defaultSubtab = getDefaultSubtab(agent as RibbonTabSlug);
  redirect(`/${tenantId}/${agent}/${defaultSubtab}`);
}
