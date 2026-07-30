// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s9-TBD
"use client";
/**
 * NotFoundAgent — Inner 404 page (Client Component).
 * F1-S9 vitalia-fase1-routing-shell — T-4
 *
 * Renderiza cuando el subtab dentro de un agent válido no existe.
 * Ejemplo: /{tenantId}/camila/foo → isValidSubtab("camila","foo") = false
 * → notFound() → Next.js renderiza este archivo.
 *
 * DEBE ser Client Component porque:
 * - Los archivos not-found.tsx en Next.js App Router NO reciben params
 *   como argumentos de función (a diferencia de page.tsx y layout.tsx).
 * - Para conocer el agent slug (y mostrar el label contextual) se usa
 *   useParams() que solo funciona en Client Components.
 *
 * El chrome shell (TopBar + ValeriaSidebar + Ribbon + SubTabsBar) está
 * visible porque este not-found.tsx vive DENTRO del route group [agent]/,
 * que hereda el layout (shell-organism)/layout.tsx + [agent]/layout.tsx.
 *
 * Microcopy spec: 01-spec.md § 10 (Spanish neutro LatAm — sin voseo).
 * A11y: role="region" aria-label + aria-hidden en emoji.
 *
 * Special case: 'config' no está en AGENT_CATALOG (Record<AgentSlug, ...>)
 * → label = "Configurar", defaultSubtab = "cuenta".
 *
 * spec_anchor: 03-arch-fe.md § 3 (Client justified) + T-4 + 01-spec.md § 6.2 + § 10 + § 12
 * downstream-regression-na: brand-local route; no cross-brand consumers.
 */

import Link from "next/link";
import { useParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  AGENT_CATALOG,
  isValidAgent,
  type AgentSlug,
  type RibbonTabSlug,
} from "@/lib/agent-catalog";

/**
 * Resolves the human-readable label and defaultSubtab for the agent.
 * Handles 'config' separately since it is not in AGENT_CATALOG.
 */
function resolveAgentMeta(slug: string): {
  label: string;
  defaultSubtab: string;
} {
  if (slug === "config") {
    return { label: "Configurar", defaultSubtab: "cuenta" };
  }
  if (isValidAgent(slug) && slug !== "config") {
    const descriptor = AGENT_CATALOG[slug as AgentSlug];
    return { label: descriptor.name, defaultSubtab: descriptor.defaultSubtab };
  }
  // Fallback: should not happen if routing is correct (layout validates agent)
  return { label: "este agente", defaultSubtab: "" };
}

export default function NotFoundAgent() {
  const params = useParams<{ tenantId: string; agent: string }>();
  const tenantId = params?.tenantId ?? "";
  const agentSlug = params?.agent ?? "";
  const { label, defaultSubtab } = resolveAgentMeta(agentSlug);

  const mainHref =
    tenantId && agentSlug && defaultSubtab
      ? `/${tenantId}/${agentSlug}/${defaultSubtab}`
      : "/";

  return (
    <section
      className="flex flex-col items-center justify-center gap-6 h-full p-8 text-center"
      data-testid="not-found-agent"
      role="region"
      aria-label={`Vista no encontrada dentro de ${label}`}
    >
      {/* Ícono — aria-hidden per 01-spec.md § 12 */}
      <span
        aria-hidden="true"
        className="text-5xl opacity-50"
        role="img"
        aria-label="Advertencia"
      >
        🔍
      </span>

      <div className="flex flex-col items-center gap-3">
        <h2 className="text-xl font-semibold tracking-tight">
          No encontramos esa vista dentro de {label}
        </h2>
        <p className="max-w-sm text-muted-foreground text-sm">
          Quizás el enlace está roto o esa sub-pestaña no existe.
        </p>
      </div>

      {/* CTA — Button default + asChild + Link para SPA navigation */}
      <Button asChild>
        <Link href={mainHref}>Ir a la vista principal de {label}</Link>
      </Button>
    </section>
  );
}
