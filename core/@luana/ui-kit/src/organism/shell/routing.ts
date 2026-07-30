// cap: platform.lift-shell-chrome-ui-kit
import type { ShellAgentDescriptor, ShellRoutingOptions } from "./types";

/**
 * Generic shell routing helpers (T-K1).
 *
 * Catalog-driven: the brand passes its own agent slug-set, special (non-agent)
 * tabs, and the valid sub-tab map by argument. The kit ships zero hardcoded
 * brand slugs/labels (RN-2).
 *
 * Path shape (brand-agnostic, mirrors the shell route group):
 *   /{tenantId}/{agent}/{subtab}/...
 * segment[0] = tenant, segment[1] = agent, segment[2] = subtab.
 *
 * Port of vitalia lib/agent-catalog.ts helpers, re-parametrized.
 */

/** Split a pathname into non-empty segments (tolerates leading/trailing slashes, null/undefined). */
function segmentsOf(pathname: string | null | undefined): string[] {
  if (!pathname) return [];
  return pathname.split("/").filter(Boolean);
}

/**
 * Extract the agent (or special-tab) slug from segment[1].
 * Returns the slug only if it is a known agent or a known special tab.
 */
export function extractAgentFromPath(
  pathname: string | null | undefined,
  opts: ShellRoutingOptions,
): string | null {
  const segments = segmentsOf(pathname);
  // segments[0] = tenantId, segments[1] = agent/special tab
  const candidate = segments[1];
  if (!candidate) return null;
  if (opts.specialTabs?.includes(candidate)) return candidate;
  if (opts.agentSlugs.includes(candidate)) return candidate;
  return null;
}

/**
 * Extract the sub-tab slug from segment[2] (raw — no validation).
 * Returns null when there is no sub-tab segment.
 */
export function extractSubtabFromPath(pathname: string | null | undefined): string | null {
  const segments = segmentsOf(pathname);
  return segments[2] ?? null;
}

/**
 * Extract the sub-sub-tab slug from segment[3] (raw — no validation).
 * Mirrors the shell route group N3-static shape:
 *   /{tenant}/{agent}/{subtab}/{subsubtab}/...
 * Returns null when there is no sub-sub-tab segment.
 */
export function extractSubSubTabFromPath(pathname: string | null | undefined): string | null {
  const segments = segmentsOf(pathname);
  return segments[3] ?? null;
}

/** True when `slug` is a known agent or special tab. */
export function isValidAgent(
  slug: string | null | undefined,
  opts: ShellRoutingOptions,
): boolean {
  if (!slug) return false;
  if (opts.specialTabs?.includes(slug)) return true;
  return opts.agentSlugs.includes(slug);
}

/** True when `subtabSlug` is a valid sub-tab for the given `agent`. */
export function isValidSubtab(
  agent: string,
  subtabSlug: string,
  opts: ShellRoutingOptions,
): boolean {
  const subtabs = opts.subtabsByAgent[agent];
  if (!subtabs) return false;
  return subtabs.includes(subtabSlug);
}

/**
 * Resolve an agent descriptor from the brand catalog by slug.
 *
 * Replaces the brand-side `AGENT_CATALOG[slug] ?? AGENT_CATALOG[DEFAULT]`
 * lookup in the chat atoms (MessageBubble / TypingIndicator / DelegateMarker /
 * ChatHeader). Falls back to the `fallbackSlug` descriptor (the supervisor /
 * default chat agent), then to the first catalog entry. The kit ships zero
 * brand slugs/labels (RN-2) — the catalog is injected.
 */
export function resolveAgent(
  catalog: readonly ShellAgentDescriptor[],
  slug: string | undefined,
  fallbackSlug?: string,
): ShellAgentDescriptor | undefined {
  if (slug) {
    const hit = catalog.find((a) => a.slug === slug);
    if (hit) return hit;
  }
  if (fallbackSlug) {
    const fb = catalog.find((a) => a.slug === fallbackSlug);
    if (fb) return fb;
  }
  return catalog[0];
}
