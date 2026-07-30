// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * AppPanelSlot — brand-agnostic application content panel host.
 * T-K2 port of vitalia AppPanelSlot (F1-S4/S7/S8/F2-S7).
 *
 * Hosts: Ribbon nav + SubTabsBar (line 2) + SubSubTabsBar (line 3, conditional) + content.
 *
 * All navigation catalog and routing props are injected by parent ShellLayoutClient.
 * Brand tokens + catalog are passed down to Ribbon/SubTabsBar/SubSubTabsBar.
 *
 * Server Component — no "use client" needed. <Ribbon />, <SubTabsBar />, <SubSubTabsBar />
 * are Client Components (Next.js App Router natural server/client boundary).
 *
 * Grid structure: flex-col with Ribbon (h-14) + SubTabsBar (min-h-[42px]) +
 * SubSubTabsBar (min-h-[38px], conditional) + content (flex-1 overflow-y-auto).
 *
 * Named export (NO default) per FSD-Lite enforce.
 */

import type { ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Ribbon } from "./Ribbon";
import { SubTabsBar } from "./SubTabsBar";
import { SubSubTabsBar } from "./SubSubTabsBar";
import type {
  GetAgentClasses,
  ShellAgentDescriptor,
  ShellLayoutLabels,
  ShellStore,
  ShellSubTabMeta,
} from "./types";
import type { ShellSubSubTabMeta } from "./SubSubTabsBar";

export interface AppPanelSlotProps {
  /** Page content rendered by the route group. */
  children?: ReactNode;
  /** Agent catalog as array (in ribbon render order). */
  agentCatalog: ShellAgentDescriptor[];
  /** Ribbon agent order (slugs). */
  ribbonOrder: string[];
  /** Sub-tabs per agent slug. */
  subTabsByAgent: Record<string, readonly ShellSubTabMeta[]>;
  /** Sub-sub-tabs keyed by "agent.subtab". */
  subSubTabsByKey?: Record<string, readonly ShellSubSubTabMeta[]>;
  /** Brand fn returning Tailwind class bundles for agent slugs. */
  getAgentClasses: GetAgentClasses;
  /** Slug for config/platform tab (config-neutral color). */
  configTabSlug?: string;
  /** Label for config/platform tab. */
  configTabLabel?: string;
  /** Slugs of agents whose sub-tabs use config-neutral mode. */
  configSlugs?: readonly string[];
  /** Slugs of sub-tabs that are shipped static (not placeholder). */
  shippedStaticSubtabs?: ReadonlySet<string>;
  /** Navigation callback — defaults to router.push. */
  onNavigate?: (href: string) => void;
  /** Content skeleton rendered when children is undefined. */
  contentSkeleton?: ReactNode;
  /**
   * Shell store — accepted for ShellLayoutClient compatibility.
   * AppPanelSlot itself is navigation-only; it does not read store state.
   */
  useShellStore?: ShellStore;
  /**
   * Layout labels — accepted for ShellLayoutClient compatibility.
   * configTabLabel from labels is used as fallback if configTabLabel prop absent.
   */
  labels?: Partial<ShellLayoutLabels>;
}

/**
 * AppPanelSlot — section host for Ribbon + SubTabsBar + SubSubTabsBar + content.
 */
export function AppPanelSlot({
  children,
  agentCatalog,
  ribbonOrder,
  subTabsByAgent,
  subSubTabsByKey = {},
  getAgentClasses,
  configTabSlug = "config",
  configTabLabel = "Configuración",
  configSlugs = [],
  shippedStaticSubtabs: _shippedStaticSubtabs,
  onNavigate,
  contentSkeleton,
  useShellStore: _useShellStore,
  labels: _labels,
}: AppPanelSlotProps) {
  const pathname = usePathname();
  const router = useRouter();
  const agentCatalogRecord = Object.fromEntries(agentCatalog.map((d) => [d.slug, d]));
  // configTabSlug incluido: la franja N3 aplica también a la caja config/Plataforma
  // (e.g. vitalia config.cuenta) — sin esto extractAgentFromPath devuelve null para
  // /tenant/config/... y la SubSubTabsBar nunca se pinta en esas rutas.
  const validSlugs = [...agentCatalog.map((d) => d.slug), configTabSlug];

  return (
    <section
      role="region"
      aria-label="Panel aplicación"
      data-testid="app-panel-slot"
      className="relative flex h-full min-h-0 flex-col overflow-hidden bg-background"
    >
      {/* Ribbon nav */}
      <Ribbon
        pathname={pathname}
        agentCatalog={agentCatalog}
        ribbonOrder={ribbonOrder}
        getAgentClasses={getAgentClasses}
        configTabSlug={configTabSlug}
        configTabLabel={configTabLabel}
        onNavigate={onNavigate ?? ((href) => { router.push(href); })}
      />

      {/* Sub-tabs line 2 */}
      <SubTabsBar
        agentCatalog={agentCatalogRecord}
        subTabsByAgent={subTabsByAgent}
        getAgentClasses={getAgentClasses}
        configSlugs={configSlugs}
        onNavigate={onNavigate}
      />

      {/* Sub-sub-tabs line 3 — N3-static bar (ADR-vitalia-004 v1.1).
          Returns null automatically for agent.subtab combos without N3 entries. */}
      <SubSubTabsBar
        subSubTabsByKey={subSubTabsByKey}
        validSlugs={validSlugs}
        onNavigate={onNavigate}
      />

      {/* Content area — flex-col + flex-1 + overflow-y-auto: marco de scroll de la hoja.
          AppPanelSlot + shell quedan overflow-hidden (marco fijo).
          `flex flex-col` (no solo block) para que las hojas que se montan con `flex-1`
          (EntityWorkspaceLayout: N3 fijo + scroll interno propio) CLAMPEN a la altura del
          panel y scrolleen internamente, en vez de crecer a su contenido y arrastrar sus
          toolbars (bug vitalia-bugfix-horarios-toolbar-sticky · verificado live 2026-06-15).
          Páginas normales (hoja = un bloque alto) siguen scrolleando vía overflow-y-auto. */}
      <div className="flex flex-col flex-1 min-h-0 overflow-y-auto">
        {children !== undefined ? (
          children
        ) : (
          contentSkeleton ?? (
            /* Default content skeleton */
            <div aria-hidden="true" className="flex flex-col gap-4 p-6">
              <div className="h-3.5 w-[42%] rounded bg-muted opacity-45" />
              <div className="h-2 w-[78%] rounded bg-muted opacity-45" />
              <div className="h-2 w-[60%] rounded bg-muted opacity-45" />
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="h-[120px] rounded-md bg-muted opacity-55" />
                <div className="h-[120px] rounded-md bg-muted opacity-55" />
                <div className="h-[120px] rounded-md bg-muted opacity-55" />
                <div className="h-[120px] rounded-md bg-muted opacity-55" />
              </div>
            </div>
          )
        )}
      </div>
    </section>
  );
}
