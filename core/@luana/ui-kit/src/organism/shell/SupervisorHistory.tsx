// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * SupervisorHistory — conversation history molecule (state C, 260px push).
 * T-K2 port of vitalia ValeriaHistory (F1-S5 T-4 + shell-core-hardening T-2/T-3).
 *
 * Header (título + quick actions) · search (case-insensitive trim filter,
 * Escape clears without propagating) · grouped items (Hoy / Ayer / Esta semana)
 * · EmptyStateInline for zero-conversations (SC-13) and empty-search distinct
 * copy. T-3: conversations come from the UI-local chat-store archive (RN-13),
 * not a static mock — so "+" archive shows up live and SC-13 empty is reachable.
 *
 * Brand data flows by prop: useChatStore (bound store) + labels. Zero brand
 * tokens (RN-2). Spanish-neutro copy ships as defaults, brand may override.
 *
 * "use client" required: useState (searchQuery, activeId) + handlers.
 */

import { ChevronLeft, Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { cn } from "@luana/format/utils";
import { Button } from "../../button";
import { Input } from "../../input";
import type { ShellChatStore, ShellChatStoreApi } from "./types";
import { EmptyStateInline } from "./EmptyStateInline";
import { HistoryGroup } from "./HistoryGroup";

export interface SupervisorHistoryLabels {
  heading: string;
  newConversation: string;
  collapse: string;
  searchPlaceholder: string;
  searchLabel: string;
  navLabel: string;
  groupToday: string;
  groupYesterday: string;
  groupThisWeek: string;
  /** SC-13 — zero archived conversations. */
  emptyAllHeading: string;
  emptyAllDescription: string;
  /** empty-search. */
  emptySearchHeading: string;
  emptySearchDescription: string;
}

const DEFAULT_LABELS: SupervisorHistoryLabels = {
  heading: "Conversaciones",
  newConversation: "Nueva conversación",
  collapse: "Colapsar a barra",
  searchPlaceholder: "Buscar conversación...",
  searchLabel: "Buscar conversación",
  navLabel: "Historial conversaciones",
  groupToday: "Hoy",
  groupYesterday: "Ayer",
  groupThisWeek: "Esta semana",
  emptyAllHeading: "Aún no hay conversaciones",
  emptyAllDescription: "Inicia una nueva conversación",
  emptySearchHeading: "Sin resultados",
  emptySearchDescription: "Intenta con otra palabra",
};

export interface SupervisorHistoryProps {
  /** brand-bound chat store (conversations archive · RN-13). */
  useChatStore: ShellChatStore;
  /** quick action: archive current + clear (newConversation). */
  onNewConversation?: () => void;
  /** quick action: collapse history back (closeHistory). */
  onCollapseToRail?: () => void;
  /** active-row bg class (brand soft token). */
  activeClass?: string;
  labels?: Partial<SupervisorHistoryLabels>;
  className?: string;
}

/**
 * SupervisorHistory — conversation history molecule.
 *
 * Filter logic (verbatim from source):
 * - Case-insensitive match on conversation title (trimmed query).
 * - 0 conversations → empty-all copy (SC-13) · 0 matches → empty-search copy.
 * - Groups with 0 items render null (HistoryGroup).
 *
 * Escape in search: non-empty query → clear + stopPropagation (prevents the
 * shell collapse shortcut while the input holds content); empty → propagate.
 */
export function SupervisorHistory({
  useChatStore,
  onNewConversation,
  onCollapseToRail,
  activeClass,
  labels,
  className,
}: SupervisorHistoryProps) {
  const l = { ...DEFAULT_LABELS, ...labels };
  const [searchQuery, setSearchQuery] = useState("");
  // Default active item is id='1' per source mockup.
  const [activeId, setActiveId] = useState<string | null>("1");

  const conversations = useChatStore(
    (s: ShellChatStoreApi) => s.conversations,
  );

  const filtered = useMemo(
    () =>
      conversations.filter((c) =>
        c.title.toLowerCase().includes(searchQuery.toLowerCase().trim()),
      ),
    [conversations, searchQuery],
  );

  // SC-13: zero archived conversations at all (distinct from empty-search).
  const noConversations = conversations.length === 0;

  const grouped = useMemo(
    () => ({
      today: filtered.filter((c) => c.group === "today"),
      yesterday: filtered.filter((c) => c.group === "yesterday"),
      this_week: filtered.filter((c) => c.group === "this_week"),
    }),
    [filtered],
  );

  return (
    <nav
      aria-label={l.navLabel}
      // shell-core-hardening T-2: ancho FIJO 260px que EMPUJA en el split inline
      // desktop (≥lg) — `shrink-0` evita compresión; en drawer mobile (<lg) se apila
      // sobre el chat → `w-full`.
      className={cn(
        "flex flex-col border-r border-border overflow-hidden h-full w-full lg:w-[260px] shrink-0",
        className,
      )}
    >
      {/* ── Header: título + quick actions ── */}
      <div className="px-3 pt-3 pb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">{l.heading}</h3>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            aria-label={l.newConversation}
            onClick={onNewConversation}
            className="h-7 w-7"
          >
            <Plus className="h-3.5 w-3.5" aria-hidden="true" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label={l.collapse}
            onClick={onCollapseToRail}
            className="h-7 w-7"
          >
            <ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" />
          </Button>
        </div>
      </div>

      {/* ── Search input ── */}
      <div className="px-3 pb-3">
        <div className="relative">
          <Search
            className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none"
            aria-hidden="true"
          />
          <Input
            type="search"
            aria-label={l.searchLabel}
            placeholder={l.searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Escape" && searchQuery) {
                // Clear locally without propagating Escape to the shell collapse
                // shortcut (input focused + has content).
                e.stopPropagation();
                setSearchQuery("");
              }
            }}
            className="w-full h-8 pl-8 pr-3 text-xs"
          />
        </div>
      </div>

      {/* ── Scrollable list ── */}
      <div className="flex-1 min-h-0 overflow-y-auto px-2 pb-3 flex flex-col gap-3">
        {noConversations ? (
          <EmptyStateInline
            heading={l.emptyAllHeading}
            description={l.emptyAllDescription}
          />
        ) : filtered.length === 0 ? (
          <EmptyStateInline
            heading={l.emptySearchHeading}
            description={l.emptySearchDescription}
          />
        ) : (
          <>
            <HistoryGroup
              label={l.groupToday}
              items={grouped.today}
              activeId={activeId}
              onItemClick={setActiveId}
              activeClass={activeClass}
            />
            <HistoryGroup
              label={l.groupYesterday}
              items={grouped.yesterday}
              activeId={activeId}
              onItemClick={setActiveId}
              activeClass={activeClass}
            />
            <HistoryGroup
              label={l.groupThisWeek}
              items={grouped.this_week}
              activeId={activeId}
              onItemClick={setActiveId}
              activeClass={activeClass}
            />
          </>
        )}
      </div>
    </nav>
  );
}
