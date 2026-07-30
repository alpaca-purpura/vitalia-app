// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * SubTabsBar — brand-agnostic sub-tabs navigation bar (line 2 of shell).
 * T-K2 port of vitalia SubTabsBar (F1-S8).
 *
 * Brand coupling removed:
 *   - AGENT_CATALOG + RIBBON_SUBTABS replaced by injected agentCatalog + subTabsByAgent props
 *   - extractAgentFromPath/extractSubtabFromPath use injected routing opts
 *   - useRouter/useParams/usePathname: Next.js built-ins (peerDep — OK in kit)
 *
 * Roving tabindex WAI-ARIA tablist pattern (verbatim from vitalia):
 * - Only one sub-tab has tabIndex=0 at a time (the focused one)
 * - Arrow keys move focus without activating navigation
 * - Enter/Space activate (onNavigate)
 * - Keyboard handler on <nav> element (events bubble from child buttons)
 *
 * Q5 cement: if activeAgent is null OR subtabs is empty → return null total.
 * Q4 cement: container className includes min-h-[42px].
 *
 * Named export (NO default) per FSD-Lite enforce.
 */

import { useState, useRef, useCallback, type KeyboardEvent } from "react";
import { usePathname, useRouter, useParams } from "next/navigation";
import { extractAgentFromPath, extractSubtabFromPath } from "./routing";
import { SubTab } from "./SubTab";
import type {
  GetAgentClasses,
  ShellAgentDescriptor,
  ShellSubTabMeta,
} from "./types";

export interface SubTabsBarProps {
  /** Full agent catalog — slug → descriptor. */
  agentCatalog: Record<string, ShellAgentDescriptor>;
  /** Sub-tabs per agent slug. */
  subTabsByAgent: Record<string, readonly ShellSubTabMeta[]>;
  /** Brand fn returning Tailwind class bundles for agent slugs. */
  getAgentClasses: GetAgentClasses;
  /** Slugs of agents whose sub-tabs are in config-neutral mode (e.g. "config"). */
  configSlugs?: readonly string[];
  /** Navigation callback — defaults to router.push. */
  onNavigate?: (href: string) => void;
}

/**
 * SubTabsBar — horizontal sub-tabs navigation bar (line 2 of shell).
 *
 * Returns null when:
 * - No valid agent segment in pathname (extractAgentFromPath returns null)
 * - Active agent has no sub-tabs (empty array)
 */
export function SubTabsBar({
  agentCatalog,
  subTabsByAgent,
  getAgentClasses,
  configSlugs = [],
  onNavigate,
}: SubTabsBarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();

  const validSlugs = Object.keys(agentCatalog);

  // URL-derived state — single source of truth
  const activeAgent: string | null = extractAgentFromPath(pathname, {
    agentSlugs: validSlugs,
    subtabsByAgent: Object.fromEntries(
      Object.entries(subTabsByAgent).map(([k, tabs]) => [k, tabs.map((t) => t.id)]),
    ),
  });
  const activeSubtab: string | null = extractSubtabFromPath(pathname);

  // Subtabs for the active agent (or empty if no entries)
  const subtabs: readonly ShellSubTabMeta[] =
    activeAgent !== null ? (subTabsByAgent[activeAgent] ?? []) : [];

  // Initial focused index: index of active subtab, or 0
  const initialFocusIdx = (() => {
    if (!activeSubtab || subtabs.length === 0) return 0;
    const idx = subtabs.findIndex((t) => t.id === activeSubtab);
    return idx >= 0 ? idx : 0;
  })();

  const [focusedIdx, setFocusedIdx] = useState<number>(initialFocusIdx);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const totalTabs = subtabs.length;

  const navigate = useCallback(
    (subtabId: string) => {
      const tenantId = params?.tenantId;
      if (!tenantId || !activeAgent) return;
      const href = `/${tenantId}/${activeAgent}/${subtabId}`;
      if (onNavigate) {
        onNavigate(href);
      } else {
        router.push(href);
      }
    },
    [params, router, activeAgent, onNavigate],
  );

  const focusTab = useCallback(
    (idx: number) => {
      if (totalTabs === 0) return;
      const safeIdx = ((idx % totalTabs) + totalTabs) % totalTabs;
      setFocusedIdx(safeIdx);
      tabRefs.current[safeIdx]?.focus();
    },
    [totalTabs],
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLElement>) => {
      switch (e.key) {
        case "ArrowRight":
          e.preventDefault();
          focusTab(focusedIdx + 1);
          return;
        case "ArrowLeft":
          e.preventDefault();
          focusTab(focusedIdx - 1);
          return;
        case "Home":
          e.preventDefault();
          focusTab(0);
          return;
        case "End":
          e.preventDefault();
          focusTab(totalTabs - 1);
          return;
        case "Enter":
        case " ": {
          e.preventDefault();
          const focused = subtabs[focusedIdx];
          if (focused) {
            navigate(focused.id);
          }
          return;
        }
        default:
          break;
      }
    },
    [focusedIdx, focusTab, navigate, subtabs, totalTabs],
  );

  // Q5 cement: return null total when no active agent or no subtabs
  if (activeAgent === null || subtabs.length === 0) {
    return null;
  }

  const descriptor = agentCatalog[activeAgent];
  const ariaLabel = descriptor
    ? `Sub-secciones ${descriptor.name}`
    : "Sub-secciones";

  const isConfig = configSlugs.includes(activeAgent);

  return (
    <nav
      role="tablist"
      aria-label={ariaLabel}
      data-testid="sub-tabs-bar"
      onKeyDown={handleKeyDown}
      className="min-h-[42px] bg-card border-b border-border flex items-center px-4 gap-1 overflow-x-auto"
    >
      {subtabs.map((subtab, idx) => (
        <SubTab
          key={subtab.id}
          ref={(el) => {
            tabRefs.current[idx] = el;
          }}
          subtab={subtab}
          agentSlug={activeAgent}
          isConfig={isConfig}
          getAgentClasses={getAgentClasses}
          active={activeSubtab === subtab.id}
          tabIndex={focusedIdx === idx ? 0 : -1}
          onClick={() => navigate(subtab.id)}
          onFocus={() => setFocusedIdx(idx)}
        />
      ))}
    </nav>
  );
}
