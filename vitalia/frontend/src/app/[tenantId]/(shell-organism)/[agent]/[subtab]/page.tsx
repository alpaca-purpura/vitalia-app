// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s9-TBD
/**
 * Subtab Page — Server Component.
 * F1-S10 vitalia-fase1-empty-states — T-9 (MODIFY from F1-S9 placeholder)
 *
 * Validates both [agent] and [subtab] params against agent-catalog.ts.
 * If either is invalid → notFound() → Next.js renders [agent]/not-found.tsx (inner).
 *
 * On valid route → delegates to SubTabContent dispatcher which maps
 * the 22 {agent}.{subtab} combos to their placeholder components.
 *
 * No "use client" — Server Component.
 * Next.js 16 App Router: params is Promise → await before use.
 *
 * spec_anchor: 03-arch.md § 4 + 06-tickets.yaml T-9
 * downstream-regression-na: brand-local route; no cross-brand consumers.
 */

import { notFound } from "next/navigation";

import {
  isValidAgent,
  isValidSubtab,
  type RibbonTabSlug,
} from "@/lib/agent-catalog";
import { SubTabContent } from "@/components/shared/shell-organism/SubTabContent";

interface PageProps {
  params: Promise<{ tenantId: string; agent: string; subtab: string }>;
}

export default async function SubtabPage({ params }: PageProps) {
  const { agent, subtab } = await params;
  if (!isValidAgent(agent) || !isValidSubtab(agent as RibbonTabSlug, subtab)) {
    notFound();
  }
  return <SubTabContent agent={agent as RibbonTabSlug} subtab={subtab} />;
}
