// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * SupervisorSidebar — shell organism root (supervisor panel).
 * T-K2 port of vitalia ValeriaSidebar (F1-S5 T-5 + shell-state-persistence T-4
 * + shell-core-hardening T-3). Brand-agnostic: supervisor identity + stores +
 * classes + testids + copy all inject by prop (RN-2, zero brand tokens).
 *
 * Architecture decisions (preserved verbatim):
 * - T-3 binary machine: supervisorOpen (closed | chat) + additive historyOpen
 *   drive THREE real layouts (the 60px rail is RETIRED):
 *     supervisorOpen "closed"               → state A: SupervisorCollapsedStrip
 *       (~44px tira-avatar at the left edge; agent panel gets the room).
 *     "chat" + historyOpen false            → state B: chat only.
 *     "chat" + historyOpen true             → state C: history (260px push) | chat.
 * - D4 keyboard shortcuts: c/r/f/n + Esc + mod+k via useKeyboardShortcuts.
 *   "n" → real chat-store newConversation (RN-13, no placeholder alert).
 *   mod+k focuses the composer (DOM id from testIds.composerPlaceholder).
 * - D5 mobile drawer (ADR-vitalia-006): visibility governed SOLELY by
 *   mobileDrawerOpen (independent slice) — NEVER derived from supervisorOpen
 *   (that was Bug #2 coupling). createPortal(document.body) escapes the
 *   `hidden md:block` parent (★ FIX T-5.bis — display:none descendants don't paint).
 *
 * The chat itself is injected as `chatSlot` (the brand-configured ChatPanel),
 * so the sidebar owns ONLY strip + history + drawer chrome (clean boundary).
 *
 * "use client" required: state + effects + handlers + matchMedia + portal.
 */

import { createPortal } from "react-dom";
import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { cn } from "@luana/format/utils";
import type {
  GetAgentClasses,
  ShellChatStore,
  ShellChatStoreApi,
  ShellStore,
  ShellStoreState,
  ShellTestIds,
} from "./types";
import { useKeyboardShortcuts } from "./useKeyboardShortcuts";
import { SupervisorCollapsedStrip } from "./SupervisorCollapsedStrip";
import {
  SupervisorHistory,
  type SupervisorHistoryLabels,
} from "./SupervisorHistory";

// Three real layouts (ValeriaRail retired): strip A · chat B · history C.
type SupervisorRender = "strip" | "chat" | "history";

export interface SupervisorSidebarLabels {
  /** aria-label of the panel (desktop + drawer). */
  panel: string;
  /** drawer close button aria-label. */
  drawerClose: string;
  /** live-region text per state. */
  liveHistory: string;
  liveClosed: string;
  liveOpen: string;
  /** strip aria-label ("Abrir a {name}"). */
  openStrip: string;
  history: Partial<SupervisorHistoryLabels>;
}

export interface SupervisorSidebarProps {
  useShellStore: ShellStore;
  useChatStore: ShellChatStore;
  getAgentClasses: GetAgentClasses;
  /** supervisor's own slug — for getAgentClasses(...).softBg (avatar circle). */
  supervisorSlug: string;
  supervisorName: string;
  supervisorInitial?: string;
  supervisorThumbnail?: string;
  /** status-dot bg class (brand token). */
  statusDotClass?: string;
  /** brand-configured chat panel (states B + C). */
  chatSlot: ReactNode;
  testIds?: ShellTestIds;
  labels: SupervisorSidebarLabels;
}

/**
 * SupervisorSidebar — composes SupervisorCollapsedStrip (A) +
 * SupervisorHistory (C) + the injected chatSlot (B + C).
 * Consumes useShellStore READ-ONLY (no schema mutation).
 */
export function SupervisorSidebar({
  useShellStore,
  useChatStore,
  getAgentClasses,
  supervisorSlug,
  supervisorName,
  supervisorInitial,
  supervisorThumbnail,
  statusDotClass,
  chatSlot,
  testIds,
  labels,
}: SupervisorSidebarProps) {
  // ── Stable selectors (binary machine) ──────────────────────────────────────
  const supervisorOpen = useShellStore((s: ShellStoreState) => s.supervisorOpen);
  const historyOpen = useShellStore((s: ShellStoreState) => s.historyOpen);
  const openSupervisor = useShellStore((s: ShellStoreState) => s.openSupervisor);
  const collapseSupervisor = useShellStore(
    (s: ShellStoreState) => s.collapseSupervisor,
  );
  const openHistory = useShellStore((s: ShellStoreState) => s.openHistory);
  const closeHistory = useShellStore((s: ShellStoreState) => s.closeHistory);
  const mobileDrawerOpen = useShellStore(
    (s: ShellStoreState) => s.mobileDrawerOpen,
  );
  const setMobileDrawerOpen = useShellStore(
    (s: ShellStoreState) => s.setMobileDrawerOpen,
  );
  // T-3: "+" / 'n' archive current conv + clear chat (RN-13, UI-local).
  const newConversation = useChatStore((s: ShellChatStoreApi) => s.newConversation);

  // ── Map machine → render shape (three real layouts) ────────────────────────
  const renderShape: SupervisorRender =
    supervisorOpen === "closed" ? "strip" : historyOpen ? "history" : "chat";

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleNewConversation = () => newConversation();

  const handleFocusComposer = () => {
    const id = testIds?.composerPlaceholder;
    if (!id) return;
    document.getElementById(id)?.focus();
  };

  // ── D4 keyboard shortcuts (handlers capture fresh closures per render) ──────
  useKeyboardShortcuts({
    c: () => collapseSupervisor(),
    r: () => {
      openSupervisor();
      closeHistory();
    },
    f: () => openHistory(),
    n: handleNewConversation,
    // Escape closes desktop supervisor AND mobile drawer (independent slice).
    Escape: () => {
      collapseSupervisor();
      setMobileDrawerOpen(false);
    },
    "mod+k": handleFocusComposer,
  });

  // ── Mobile drawer detection via matchMedia ─────────────────────────────────
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // Drawer zone: < lg (1024). On tablet (768–1023) the supervisor is a
    // drawer/overlay (not inline split) so the agent panel gets full width.
    const mq = window.matchMedia("(max-width: 1023px)");
    setIsMobile(mq.matches);

    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  // ── Derived values ─────────────────────────────────────────────────────────
  const isExpanded = renderShape !== "strip";
  // First grid column: strip 44px (A) · history 280px (C) · chat-only 0 (B).
  const firstColWidth =
    renderShape === "strip" ? 44 : renderShape === "history" ? 280 : 0;

  const liveText =
    renderShape === "history"
      ? labels.liveHistory
      : renderShape === "strip"
        ? labels.liveClosed
        : labels.liveOpen;

  // ── Hamburger ref (focus restoration post-drawer-close) ────────────────────
  const hamburgerRef = useRef<HTMLButtonElement>(null);
  const handleMobileClose = () => setMobileDrawerOpen(false);

  const supervisorSoftBg = getAgentClasses(supervisorSlug).softBg;

  // ── Mobile drawer render ───────────────────────────────────────────────────
  // D5: visibility = mobileDrawerOpen alone. Portal to document.body escapes
  // the `hidden md:block` parent (display:none descendants don't paint).
  if (isMobile && mobileDrawerOpen) {
    if (typeof document === "undefined") return null;

    return createPortal(
      <>
        {/* Backdrop */}
        <div
          data-testid={testIds?.supervisorDrawerBackdrop}
          aria-hidden="true"
          onClick={handleMobileClose}
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
        />

        {/* Drawer — role="dialog" + aria-modal valid combo (WCAG/ARIA). */}
        <aside
          role="dialog"
          aria-label={labels.panel}
          aria-modal="true"
          aria-expanded="true"
          data-testid={testIds?.supervisorSidebar}
          className="fixed inset-y-0 left-0 z-50 flex w-full flex-col bg-card shadow-2xl lg:hidden"
        >
          {/* Drawer header */}
          <div className="flex h-14 shrink-0 items-center justify-between border-b border-border px-3">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "flex h-7 w-7 items-center justify-center rounded-full",
                  supervisorSoftBg,
                )}
                aria-hidden="true"
              >
                <span className="select-none text-xs font-semibold text-white">
                  {supervisorInitial}
                </span>
              </div>
              <span className="text-sm font-semibold text-foreground">
                {supervisorName}
              </span>
            </div>

            <button
              ref={hamburgerRef}
              type="button"
              aria-label={labels.drawerClose}
              data-testid={testIds?.supervisorDrawerClose}
              onClick={handleMobileClose}
              className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-muted"
            >
              <X className="size-4" aria-hidden="true" />
            </button>
          </div>

          {/* Body: history + chat stacked */}
          <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
            <SupervisorHistory
              useChatStore={useChatStore}
              onNewConversation={handleNewConversation}
              onCollapseToRail={() => closeHistory()}
              activeClass={supervisorSoftBg}
              labels={labels.history}
            />
            {chatSlot}
          </div>
        </aside>
      </>,
      document.body,
    );
  }

  // ── Desktop render (strip A · chat B · history|chat C) ─────────────────────
  const gridColumns =
    renderShape === "strip"
      ? `${firstColWidth}px`
      : renderShape === "history"
        ? `${firstColWidth}px 1fr`
        : "1fr";

  return (
    <aside
      role="complementary"
      aria-label={labels.panel}
      aria-expanded={isExpanded}
      data-testid={testIds?.supervisorSidebar}
      className="hidden h-full overflow-hidden bg-card motion-reduce:transition-none lg:grid"
      style={{
        gridTemplateColumns: gridColumns,
        gridTemplateRows: "minmax(0, 1fr)",
        transition: "grid-template-columns 220ms cubic-bezier(.2,.8,.2,1)",
      }}
    >
      {/* Live region — announces state changes to screen readers */}
      <span role="status" aria-live="polite" aria-atomic="true" className="sr-only">
        {liveText}
      </span>

      {/* State A: tira-avatar strip (closed) — reopens to chat (RN-12) */}
      {renderShape === "strip" && (
        <SupervisorCollapsedStrip
          onOpenSupervisor={openSupervisor}
          supervisorName={supervisorName}
          supervisorThumbnail={supervisorThumbnail}
          supervisorInitial={supervisorInitial}
          supervisorSoftBg={supervisorSoftBg}
          statusDotClass={statusDotClass}
          stripTestId={testIds?.supervisorCollapsedStrip}
          statusDotTestId={testIds?.supervisorStripStatusDot}
          openLabel={labels.openStrip}
        />
      )}

      {/* State C: history (260px push) — XOR with strip */}
      {renderShape === "history" && (
        <SupervisorHistory
          useChatStore={useChatStore}
          onNewConversation={handleNewConversation}
          onCollapseToRail={() => closeHistory()}
          labels={labels.history}
        />
      )}

      {/* Chat — rendered in states B + C (whenever the supervisor is open) */}
      {isExpanded && chatSlot}
    </aside>
  );
}
