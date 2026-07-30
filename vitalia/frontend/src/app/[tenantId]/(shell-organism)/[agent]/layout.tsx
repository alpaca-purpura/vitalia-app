// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s9-TBD
/**
 * Agent Layout — Server Component.
 * F1-S9 vitalia-fase1-routing-shell — T-4
 *
 * 03-arch-fe.md § 9.5 — verbatim spec.
 *
 * Valida el [agent] param contra agent-catalog.ts::isValidAgent().
 * Agentes válidos: lisa · valeria · adrian · lucas · camila · config.
 * Excluye: mateo (transversal — no en AGENT_RIBBON_ORDER).
 * Excluye: cualquier slug desconocido (XSS, typos, etc.).
 *
 * Si inválido → notFound() → Next.js renderiza (shell-organism)/not-found.tsx.
 * Si válido → renderiza children (el sub-árbol [agent]/page.tsx + [agent]/[subtab]/page.tsx).
 *
 * No "use client" — notFound() es Server Action.
 * Next.js 16: params es Promise → await antes de usar.
 *
 * spec_anchor: 03-arch-fe.md § 9.5 + 04-validators.yaml SC-2 + 06-tickets.yaml T-4
 * downstream-regression-na: brand-local route; no cross-brand consumers.
 */

import { notFound } from "next/navigation";

import { isValidAgent } from "@/lib/agent-catalog";

interface LayoutProps {
  children: React.ReactNode;
  params: Promise<{ tenantId: string; agent: string }>;
}

export default async function AgentLayout({ children, params }: LayoutProps) {
  const { agent } = await params;
  if (!isValidAgent(agent)) notFound();
  return <>{children}</>;
}
