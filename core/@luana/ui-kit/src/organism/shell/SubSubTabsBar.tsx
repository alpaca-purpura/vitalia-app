// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * SubSubTabsBar — brand-agnostic N3-static sub-sub-tabs navigation bar (line 3 of shell).
 * T-K2 port of vitalia SubSubTabsBar (F2-S7 T-4, ADR-vitalia-004 v1.1).
 *
 * Brand coupling removed:
 *   - AGENT_SUBSUBTABS replaced by injected subSubTabsByKey prop (Record<"agent.subtab", SubSubTabMeta[]>)
 *   - extractAgentFromPath/extractSubtabFromPath/extractSubSubTabFromPath use injected routing opts
 *
 * ADR reference: ADR-vitalia-004 v1.1 — N3-static SubSubTabsBar pattern.
 * ANTI-PATTERN GUARD: This component renders a HEADER bar (NOT Shadcn <Tabs> body).
 *
 * Returns null when no sub-sub-tabs exist for the current agent.subtab combo.
 *
 * Named export (NO default) per FSD-Lite enforce.
 */

import {
  useState,
  useRef,
  useCallback,
  type KeyboardEvent,
} from "react";
import { usePathname, useRouter, useParams } from "next/navigation";
import {
  extractAgentFromPath,
  extractSubtabFromPath,
  extractSubSubTabFromPath,
} from "./routing";
import { cn } from "@luana/format/utils";

export interface ShellSubSubTabMeta {
  id: string;
  label: string;
  icon: string;
}

export interface SubSubTabsBarProps {
  /**
   * Sub-sub-tabs keyed by "agent.subtab".
   * e.g. { "lisa.marca": [{id:"identidad",...}, ...] }
   */
  subSubTabsByKey: Record<string, readonly ShellSubSubTabMeta[]>;
  /** Valid agent slugs (from catalog) for URL extraction. */
  validSlugs: string[];
  /** Navigation callback — defaults to router.push. */
  onNavigate?: (href: string) => void;
}

/**
 * SubSubTabsBar — horizontal N3-static navigation strip (line 3 of shell).
 * Returns null for all agent.subtab combos without N3 entries.
 */
export function SubSubTabsBar({
  subSubTabsByKey,
  validSlugs,
  onNavigate,
}: SubSubTabsBarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();

  const activeAgent = extractAgentFromPath(pathname, {
    agentSlugs: validSlugs,
    subtabsByAgent: {},
  });
  const activeSubtab = extractSubtabFromPath(pathname);
  const activeSubSubTab = extractSubSubTabFromPath(pathname);

  const subsubtabsKey =
    activeAgent && activeSubtab
      ? (`${activeAgent}.${activeSubtab}` as const)
      : null;
  const subsubtabs: readonly ShellSubSubTabMeta[] | null = subsubtabsKey
    ? (subSubTabsByKey[subsubtabsKey] ?? null)
    : null;

  // Detail route guard (vitalia lisa-servicios G2-F10): on an entity workspace
  // (e.g. /lisa/servicios/{offerId}/{leaf}) the segment after the subtab is an
  // entity id, NOT a declared sub-sub-tab. The entity's own EntitySubNavBar takes
  // over there, so the N3 sub-sub-tabs bar must NOT render. Generic across brands:
  // if the post-subtab segment exists but isn't a known sub-sub-tab id → it's a detail.
  const segAfterSubtab = pathname.split("/").filter(Boolean)[3] ?? null;
  const isDetailRoute =
    segAfterSubtab != null &&
    subsubtabs != null &&
    !subsubtabs.some((t) => t.id === segAfterSubtab);

  const initialFocusIdx = (() => {
    if (!activeSubSubTab || !subsubtabs || subsubtabs.length === 0) return 0;
    const idx = subsubtabs.findIndex((t) => t.id === activeSubSubTab);
    return idx >= 0 ? idx : 0;
  })();

  const [focusedIdx, setFocusedIdx] = useState<number>(initialFocusIdx);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const totalTabs = subsubtabs?.length ?? 0;

  const navigate = useCallback(
    (subsubtabId: string) => {
      const tenantId = params?.tenantId;
      if (!tenantId || !activeAgent || !activeSubtab) return;
      const href = `/${tenantId}/${activeAgent}/${activeSubtab}/${subsubtabId}`;
      if (onNavigate) {
        onNavigate(href);
      } else {
        router.push(href);
      }
    },
    [params, router, activeAgent, activeSubtab, onNavigate],
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
          if (subsubtabs) {
            const focused = subsubtabs[focusedIdx];
            if (focused) {
              navigate(focused.id);
            }
          }
          return;
        }
        default:
          break;
      }
    },
    [focusedIdx, focusTab, navigate, subsubtabs, totalTabs],
  );

  if (!subsubtabs || subsubtabs.length === 0 || isDetailRoute) {
    return null;
  }

  return (
    <nav
      role="tablist"
      aria-label="Sub-secciones de la pestaña actual"
      data-testid="sub-sub-tabs-bar"
      onKeyDown={handleKeyDown}
      className="min-h-[38px] bg-background border-b border-border/50 flex items-center px-6 gap-0.5 overflow-x-auto"
    >
      {subsubtabs.map((subsubtab, idx) => {
        const isActive = activeSubSubTab === subsubtab.id;
        return (
          <button
            key={subsubtab.id}
            ref={(el) => {
              tabRefs.current[idx] = el;
            }}
            role="tab"
            aria-selected={isActive}
            aria-current={isActive ? "page" : undefined}
            tabIndex={focusedIdx === idx ? 0 : -1}
            data-testid={`sub-sub-tab-${subsubtab.id}`}
            className={cn(
              "inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors whitespace-nowrap",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
              isActive
                ? "font-medium bg-muted text-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
            )}
            onClick={() => navigate(subsubtab.id)}
            onFocus={() => setFocusedIdx(idx)}
          >
            <span aria-hidden="true">{subsubtab.icon}</span>
            <span>{subsubtab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
