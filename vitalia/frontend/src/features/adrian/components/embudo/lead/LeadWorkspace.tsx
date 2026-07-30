// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * LeadWorkspace — Client root for lead detail pages (V3, opción C).
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * Renders EntityWorkspaceLayout (@luana/ui-kit) — canon N3 workspace — with:
 *   - Back link: [‹ Embudo]
 *   - Entity: masked lead name + stage badge
 *   - Leaf tabs: Resumen · Historial (derived from URL)
 *
 * NO Shadcn Tabs in the body — views are derived from the URL path (spec V3).
 * Children = the active view content (ResumenView or HistorialView).
 *
 * Loading state: EntityWorkspaceLayout isLoading skeleton (spec V3 states).
 * Error/404: "Lead no encontrado" (RN-1, generic message, no info leak).
 *
 * MIGRATED to @luana/ui-kit EntityWorkspaceLayout (vitalia-shell-core-hardening T-5).
 * activeLeaf passed as prop — vitalia uses static leaf segments (/resumen, /historial).
 *
 * spec_anchor: 03-arch-fe.md § components/embudo/lead + 01-spec.md § V3 D.7/D.8
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { type ReactNode } from "react";
import { EntityWorkspaceLayout } from "@luana/ui-kit";
import type { EntitySubNavLeaf } from "@luana/ui-kit";
import { useLeadDetail } from "../../../api/lead";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface LeadWorkspaceProps {
  tenantId: string;
  leadId: string;
  /**
   * Active leaf tab id: "resumen" | "historial".
   * Passed explicitly because vitalia uses static leaf segments, not [leaf] dynamic param.
   */
  activeLeaf: "resumen" | "historial";
  children: ReactNode;
}

// ── Sub-components ────────────────────────────────────────────────────────────

function NotFoundState() {
  return (
    <div className="flex flex-col items-center justify-center p-12 gap-4 text-center">
      <p className="text-lg font-medium">Lead no encontrado</p>
      <p className="text-sm text-muted-foreground">
        Este lead no existe o no tienes acceso a él.
      </p>
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * LeadWorkspace — wraps lead detail pages with EntityWorkspaceLayout (opción C, spec V3).
 *
 * Fetches lead header data (name, stage) for entity identity prop.
 * Children render the active view content (Resumen / Historial).
 */
export function LeadWorkspace({
  tenantId,
  leadId,
  activeLeaf,
  children,
}: LeadWorkspaceProps) {
  const { data, isLoading, isError } = useLeadDetail(leadId);

  // Build leaf tabs (spec V3: Resumen · Historial)
  const leaves: EntitySubNavLeaf[] = [
    {
      id: "resumen",
      label: "Resumen",
      href: `/${tenantId}/adrian/embudo/${leadId}/resumen`,
    },
    {
      id: "historial",
      label: "Historial",
      href: `/${tenantId}/adrian/embudo/${leadId}/historial`,
    },
  ];

  // Build entity for EntityWorkspaceLayout
  // PHI: name is already masked by the BE (format: "María G███")
  const entity =
    !isLoading && !isError && data?.lead
      ? {
          id: data.lead.id,
          name: data.lead.name,
          avatarUrl: null, // leads don't have avatars
        }
      : null;

  return (
    <EntityWorkspaceLayout
      rootHref={`/${tenantId}/adrian/embudo`}
      rootLabel="Embudo"
      entity={entity}
      leaves={leaves}
      activeLeaf={isError ? null : activeLeaf}
      isLoading={isLoading}
    >
      {/* Content area */}
      {isError || (!isLoading && data === undefined) ? (
        <NotFoundState />
      ) : (
        children
      )}
    </EntityWorkspaceLayout>
  );
}
