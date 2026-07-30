// canon: design-system-canon.md §2.1-§2.2 · story-origin: core-ds-foundation
"use client";
/**
 * EntityWorkspaceLayout.tsx — Canon N3 workspace layout for entity detail pages (@luana/ui-kit).
 *
 * Brand-agnostic 1-panel, URL-driven list/detail workspace. Mounts the N3 ribbon
 * (EntitySubNavBar) + {children} slot (the active leaf content).
 *
 * SSR-safe + STORE-FREE (G2): this component is "use client" (needs useParams for
 * activeLeaf URL-derivation) but subscribes to NO store. The skeleton path is
 * store-free — it renders inert markup, never reads Zustand/context.
 *
 * Pattern:
 *   [entityId]/layout.tsx (Server Component) → EntityWorkspaceLayout (Client)
 *   EntityWorkspaceLayout mounts EntitySubNavBar + children (the leaf page).
 *
 * activeLeaf is URL-derived from the [leaf] route segment — NEVER stored.
 * router.push between leaves = soft nav (no full reload, preserves cache).
 *
 * Named export (NO default). Store-free skeleton (G2 gate).
 */

import { useParams } from "next/navigation";
import { type ReactNode } from "react";

import { Skeleton } from "./skeleton";
import { EntitySubNavBar, type EntitySubNavLeaf, type EntitySubNavEntity } from "./EntitySubNavBar";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface EntityWorkspaceLayoutProps {
  /** Entity descriptor — null during SSR skeleton / master mode / loading state */
  entity: EntitySubNavEntity | null;
  /** Ordered leaves for the N3 nav bar (content leaves + optional add affordance) */
  leaves: EntitySubNavLeaf[];
  /** Href for the root leaf (master grid, e.g., /{tenantId}/{agent}/{collection}) */
  rootHref: string;
  /** Label for the root leaf (e.g., "ICPs") */
  rootLabel: string;
  /** Whether entity data is still loading (shows skeleton) */
  isLoading?: boolean;
  /** Optional placeholder shown in master mode (entity=null) */
  placeholder?: string;
  /**
   * Callback fired when the add-affordance leaf is clicked in EntitySubNavBar.
   * Forwarded verbatim to EntitySubNavBar.onAddAffordance. Allows the caller to
   * trigger a mutation without routing to a literal "__add__" path.
   */
  onAddAffordance?: () => void;
  /**
   * Optional entity-identity selector node forwarded verbatim to
   * EntitySubNavBar.entityIdentitySlot (mirror of onAddAffordance forwarding).
   * Canon §6.3: identity = selector (EntityPicker) — "cambiar sin volver".
   * Absent → static identity renders (back-compat). Master mode → never rendered.
   */
  entityIdentitySlot?: ReactNode;
  /**
   * Optional override for the active leaf id.
   *
   * When NOT provided, the active leaf is derived from the `[leaf]` dynamic
   * route param via useParams() — suitable for routes with a `[leaf]` segment.
   *
   * When provided, overrides URL-derivation entirely. Use this for routes that
   * use **static** leaf segments (e.g., `/perfil`, `/resumen`) where `useParams()`
   * does not expose the leaf name as a dedicated param key.
   *
   * Additive-minimal addition (2026-06-10, vitalia-shell-core-hardening T-5):
   * vitalia routes use static leaf segments; `[leaf]` dynamic param not present.
   */
  activeLeaf?: string | null;
  /** Leaf content — the active leaf page component */
  children: ReactNode;
  /** Additional className for the outer wrapper */
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

function classNames(...parts: Array<string | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

/**
 * EntityWorkspaceLayout — wrapper for entity detail pages.
 *
 * Derives activeLeaf from URL path params (URL-driven state, never a store).
 * Renders EntitySubNavBar (N3 ribbon) above children (leaf content).
 *
 * Loading state: a store-free skeleton bar replaces EntitySubNavBar while the
 * entity hydrates. Error state: handled by the leaf page (children).
 */
export function EntityWorkspaceLayout({
  entity,
  leaves,
  rootHref,
  rootLabel,
  isLoading = false,
  placeholder,
  onAddAffordance,
  entityIdentitySlot,
  activeLeaf: activeLeafProp,
  children,
  className,
}: EntityWorkspaceLayoutProps) {
  // URL-derived activeLeaf — reads the [leaf] param from the App Router.
  // useParams() is safe inside "use client" components and reads NO store (G2).
  const params = useParams<{ leaf?: string }>();
  // activeLeafProp overrides URL-derivation for routes using static leaf segments
  // (e.g., `/perfil`, `/resumen`) where `[leaf]` is not a dynamic route param.
  const activeLeaf = activeLeafProp !== undefined ? (activeLeafProp ?? null) : (params.leaf ?? null);

  return (
    <div
      className={classNames("flex flex-col flex-1 min-h-0 overflow-hidden", className)}
      data-testid="entity-workspace-layout"
    >
      {/* N3 ribbon — store-free skeleton loading state */}
      {isLoading ? (
        <div
          className="sticky top-0 z-20 w-full bg-card border-b border-border rounded-none flex items-center gap-3 min-h-[44px] px-4"
          aria-busy="true"
          data-testid="entity-sub-nav-skeleton"
        >
          {/* Root leaf skeleton */}
          <Skeleton className="h-7 w-14 rounded-md flex-shrink-0" />
          {/* Entity identity skeleton */}
          <Skeleton className="h-6 w-6 rounded-full flex-shrink-0" />
          <Skeleton className="h-4 w-32 rounded-sm" />
          {/* Leaf tabs skeleton */}
          <Skeleton className="h-7 w-20 rounded-md" />
          <Skeleton className="h-7 w-20 rounded-md" />
          <Skeleton className="h-7 w-20 rounded-md" />
        </div>
      ) : (
        <EntitySubNavBar
          rootHref={rootHref}
          rootLabel={rootLabel}
          entity={entity}
          leaves={leaves}
          activeLeaf={activeLeaf}
          placeholder={placeholder}
          onAddAffordance={onAddAffordance}
          entityIdentitySlot={entityIdentitySlot}
        />
      )}

      {/* Leaf content slot */}
      <div className="flex-1 min-h-0 overflow-auto" data-testid="entity-workspace-content">
        {children}
      </div>
    </div>
  );
}
