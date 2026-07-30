// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * Ribbon — brand-agnostic navigation ribbon (T-K2 port of vitalia Ribbon).
 *
 * The roving-tabindex WAI-ARIA tablist (Arrow/Home/End/Enter/Space) is preserved
 * verbatim. Brand data flows by prop: agentCatalog + ribbonOrder + getAgentClasses
 * + configTab label. The active state is URL-derived (extractAgentFromPath over
 * the injected `pathname` — the kit never imports next/navigation, RN-2).
 * Navigation goes through `onNavigate(href)`; hrefs are built from segment[0]
 * (tenant) + the descriptor's defaultSubtab.
 *
 * data-testid preserved EXACT (vitalia e2e): ribbon, ribbon-tab-{slug},
 * ribbon-config-tab.
 */

import { useCallback, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { RibbonTab } from "./RibbonTab";
import { ConfigTab } from "./ConfigTab";
import { extractAgentFromPath } from "./routing";
import type { GetAgentClasses, ShellAgentDescriptor } from "./types";

export interface RibbonProps {
  /** current pathname (brand passes usePathname()). */
  pathname: string;
  agentCatalog: ShellAgentDescriptor[];
  /** agent slugs in ribbon order. */
  ribbonOrder: string[];
  getAgentClasses: GetAgentClasses;
  /** special (non-agent) config tab slug, e.g. "config". */
  configTabSlug: string;
  /** label for the config tab (Spanish neutro). */
  configTabLabel: string;
  onNavigate: (href: string) => void;
}

/** tenant = first path segment (mirrors /{tenant}/{agent}/{subtab}). */
function tenantOf(pathname: string): string | null {
  const segments = pathname.split("/").filter(Boolean);
  return segments[0] ?? null;
}

export function Ribbon({
  pathname,
  agentCatalog,
  ribbonOrder,
  getAgentClasses,
  configTabSlug,
  configTabLabel,
  onNavigate,
}: RibbonProps) {
  const bySlug = useMemo(() => {
    const map = new Map<string, ShellAgentDescriptor>();
    for (const d of agentCatalog) map.set(d.slug, d);
    return map;
  }, [agentCatalog]);

  const agentSlugs = useMemo(() => agentCatalog.map((d) => d.slug), [agentCatalog]);

  // URL-derived active state — single source of truth.
  const activeSlug = extractAgentFromPath(pathname, {
    agentSlugs,
    specialTabs: [configTabSlug],
    subtabsByAgent: {},
  });

  // Initial focus follows the active tab; fallback to index 0.
  const initialFocusIdx = (() => {
    if (activeSlug === configTabSlug) return ribbonOrder.length;
    if (activeSlug !== null) {
      const idx = ribbonOrder.indexOf(activeSlug);
      return idx >= 0 ? idx : 0;
    }
    return 0;
  })();

  const [focusedIdx, setFocusedIdx] = useState<number>(initialFocusIdx);

  // tabRefs[0..ribbonOrder.length-1] = agent tabs; [ribbonOrder.length] = config.
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  const totalTabs = ribbonOrder.length + 1;

  // Navigate to a slug — guards null tenant.
  const navigateTo = useCallback(
    (slug: string) => {
      const tenantId = tenantOf(pathname);
      if (!tenantId) return;

      if (slug === configTabSlug) {
        // Config landing is brand-routed; default to the special tab root. The
        // brand may intercept via onNavigate to add its own landing subtab.
        onNavigate(`/${tenantId}/${configTabSlug}`);
        return;
      }

      const descriptor = bySlug.get(slug);
      if (!descriptor) return;
      onNavigate(`/${tenantId}/${slug}/${descriptor.defaultSubtab}`);
    },
    [pathname, configTabSlug, bySlug, onNavigate],
  );

  // Move focus to idx (circular modulo-safe wrap).
  const focusTab = useCallback(
    (idx: number) => {
      const safeIdx = ((idx % totalTabs) + totalTabs) % totalTabs;
      setFocusedIdx(safeIdx);
      tabRefs.current[safeIdx]?.focus();
    },
    [totalTabs],
  );

  // Keyboard handler on <nav> — events bubble up from child buttons.
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
          if (focusedIdx < ribbonOrder.length) {
            navigateTo(ribbonOrder[focusedIdx]);
          } else {
            navigateTo(configTabSlug);
          }
          return;
        }
        default:
          break;
      }
    },
    [focusedIdx, focusTab, navigateTo, totalTabs, ribbonOrder, configTabSlug],
  );

  return (
    <nav
      role="tablist"
      aria-label="Agentes"
      data-testid="ribbon"
      onKeyDown={handleKeyDown}
      className="flex h-14 items-stretch gap-1 overflow-x-auto border-b border-border bg-card px-3"
    >
      {ribbonOrder.map((slug, idx) => {
        const descriptor = bySlug.get(slug);
        if (!descriptor) return null;
        return (
          <RibbonTab
            key={slug}
            ref={(el) => {
              tabRefs.current[idx] = el;
            }}
            descriptor={descriptor}
            getAgentClasses={getAgentClasses}
            active={activeSlug === slug}
            tabIndex={focusedIdx === idx ? 0 : -1}
            onClick={() => navigateTo(slug)}
            onFocus={() => setFocusedIdx(idx)}
          />
        );
      })}
      <ConfigTab
        ref={(el) => {
          tabRefs.current[ribbonOrder.length] = el;
        }}
        label={configTabLabel}
        active={activeSlug === configTabSlug}
        tabIndex={focusedIdx === ribbonOrder.length ? 0 : -1}
        onClick={() => navigateTo(configTabSlug)}
        onFocus={() => setFocusedIdx(ribbonOrder.length)}
      />
    </nav>
  );
}
