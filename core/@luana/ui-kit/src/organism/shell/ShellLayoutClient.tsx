// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * ShellLayoutClient — brand-agnostic shell chrome splitter (T-K2 port, re-port T-V2).
 *
 * VERBATIM port of vitalia ShellOrganismLayoutClient (fixes v4 SAGRADOS).
 * The binary state machine, the react-resizable-panels v4 footgun workarounds,
 * and the ★ Live-fix 2026-06-11 comments are preserved; only NAMES are generic
 * (no Valeria / no vitalia / no brand tokens in logic) and brand data flows in
 * BY PROP (supervisor*, agentCatalog, getAgentClasses, useShellStore/useChatStore,
 * splitGroupId, logoSlot, rightClusterSlot, labels, testIds).
 *
 * ★ Re-port 2026-06-11 (T-V2 e2e Bif-3): the first T-K2 port "cleaned up" the
 * source into isLg-branched JSX + simplified effects — that broke D1-D5 (single
 * <main>, Group ALWAYS mounted, hook-count stable, single AppPanelSlot, shellReady
 * signal) and 19/85 e2e survived. This file is now the source effect-for-effect:
 *   - <main id="main-content" ref={containerRef} data-shell-ready={shellReady}>
 *   - Group ALWAYS mounted (mobile = panel collapsed to 0, NOT unmounted)
 *   - reconciliation effect: !isLg → 0/100 · closed → collapse() retry-rAF with
 *     isCollapsed() check · open → expand() FIRST + snap-up to min
 *   - history-push (RN-7): flip-only ±histPct over CURRENT layout, floor min+hist,
 *     retry-rAF until converged (persistence overwrites first setLayout)
 *   - Panel born at target size (defaultSize=stripPct when closed → v4 auto-collapse)
 *   - minSize dynamic in C (min+hist), key remount includes A/B/C discriminator
 *
 * react-resizable-panels v4.11.1 footguns (do NOT "optimize"):
 * collapsible/collapsedSize/minSize CAPTURED AT MOUNT → key remount per state;
 * collapse() targets collapsedSize bypassing minSize (setLayout clamps to minSize);
 * expand() must run before setLayout on re-open; number = PX, "NN%" = %.
 *
 * NOTE: rendered ONLY inside the dynamic({ssr:false}) boundary of ShellLayout.tsx.
 */

import { useEffect, useRef, useState } from "react";
// react-resizable-panels Group/Separator aliased locally — kit already exports a
// form-field `Group` + a `./separator` primitive; re-exporting these would collide.
import {
  Group as ResizableGroup,
  Panel,
  Separator as ResizeSeparator,
  useDefaultLayout,
  useGroupRef,
  usePanelRef,
} from "react-resizable-panels";
import { cn } from "@luana/format/utils";
import { useStoreHydration } from "@luana/hooks/use-store-hydration";
import { Toaster } from "../../sonner";
import type { ShellLayoutProps, ShellStoreState } from "./types";
import { SUPERVISOR_MIN_PX } from "./useViewportGuard";
import { useViewportGuard } from "./useViewportGuard";
import { TopBarShell } from "./TopBarShell";
import { SupervisorSidebar } from "./SupervisorSidebar";
import type { SupervisorSidebarLabels } from "./SupervisorSidebar";
import { AppPanelSlot } from "./AppPanelSlot";
import { ChatPanel } from "./ChatPanel";

/** Generic panel ids (was VALERIA_PANEL_ID / APP_PANEL_ID — brand-agnostic). */
const SUPERVISOR_PANEL_ID = "supervisor-panel";
const APP_PANEL_ID = "app-panel";

/** Minimum px for the application (right) panel. */
const MIN_APP_PX = 480;

/** Default SupervisorSidebarLabels — brand may override via ShellLayoutLabels. */
function buildSupervisorLabels(
  supervisorName: string,
  labels?: Partial<{ openSupervisor: string; collapseSupervisor: string }>,
): SupervisorSidebarLabels {
  return {
    panel: supervisorName,
    drawerClose: labels?.collapseSupervisor ?? `Cerrar ${supervisorName}`,
    liveHistory: "Historial abierto",
    liveClosed: `${supervisorName} cerrado`,
    liveOpen: `${supervisorName} abierto`,
    openStrip: labels?.openSupervisor ?? `Abrir a ${supervisorName}`,
    history: {},
  };
}

export function ShellLayoutClient({
  children,
  supervisorName,
  supervisorSlug,
  supervisorAvatar: _supervisorAvatar,
  supervisorInitial,
  supervisorThumbnail,
  agentCatalog,
  ribbonOrder,
  subTabsByAgent,
  subSubTabsByKey,
  shippedStaticSubtabs,
  getAgentClasses,
  useShellStore,
  useChatStore,
  splitGroupId,
  logoSlot,
  rightClusterSlot,
  labels,
  onNavigate,
  testIds,
  statusDotClass,
}: ShellLayoutProps) {
  // ★ ADR-vitalia-006 (SSR-safe persisted store): rehydrate() must be triggered
  // exactly once client-side — setItem is a NO-OP until _hasHydrated flips, so
  // WITHOUT this call the injected shell store NEVER reads NOR writes storage.
  // This component (inside the ssr:false chunk) is the ONLY place rehydrate()
  // is called for the shell store. Brand-specific stores (tenant, etc.) are
  // hydrated by the brand wire component. StrictMode-safe via ref guard.
  useStoreHydration(useShellStore);

  // Shell UI store (binary machine) — injected by the brand (persisted).
  const supervisorOpen = useShellStore((s: ShellStoreState) => s.supervisorOpen);
  const historyOpen = useShellStore((s: ShellStoreState) => s.historyOpen);

  // Store-inert viewport contract (D3 stable hook — call unconditionally).
  useViewportGuard();

  // ── Container measurement (verbatim source: sane 1280 default, NOT 0) ──────
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(1280); // sane default

  // Deterministic readiness signal: set true after the first post-mount layout
  // reconciliation (Fix A snap-up settled). Exposed as `data-shell-ready` for
  // consumers and E2E tests to await a stable layout.
  const [shellReady, setShellReady] = useState(false);

  // Inline split only at >= lg (1024). Below it, the supervisor is a drawer →
  // the supervisor Panel must collapse to 0 so the agent gets the FULL width.
  // SupervisorSidebar stays mounted (inside the Panel) so its drawer portal works.
  // Synchronous init (client-only via ssr:false) → no flash.
  const [isLg, setIsLg] = useState(
    () =>
      typeof window === "undefined" ||
      window.matchMedia("(min-width: 1024px)").matches,
  );
  useEffect(() => {
    if (typeof window === "undefined") return;
    const mq = window.matchMedia("(min-width: 1024px)");
    const handler = (e: MediaQueryListEvent) => setIsLg(e.matches);
    setIsLg(mq.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });
    ro.observe(el);
    setContainerWidth(el.getBoundingClientRect().width);
    return () => ro.disconnect();
  }, []);

  // Convert min pixels → percent based on actual container width.
  // Clamp a [10, 70] para evitar valores absurdos en viewport extremo.
  const clampPct = (px: number, total: number) =>
    Math.max(10, Math.min(70, (px / Math.max(total, 1)) * 100));
  const minSupervisorPct = clampPct(SUPERVISOR_MIN_PX, containerWidth);
  const minAppPct = clampPct(MIN_APP_PX, containerWidth);
  // Raw % of the 44px strip (no [10,70] clamp — the strip is intentionally
  // narrower than SUPERVISOR_MIN_PX; the Panel collapse bypasses minSize).
  const STRIP_SUPERVISOR_PX = 44;
  const stripPct = Math.max(
    1,
    (STRIP_SUPERVISOR_PX / Math.max(containerWidth, 1)) * 100,
  );
  // Default split 30% supervisor / 70% app — fresh default only (resizable +
  // persisted via useDefaultLayout).
  const defaultSupervisorPct = 30;
  // ★ Live-fix 2026-06-11 (RN-7 push REAL): el historial debe ENSANCHAR el panel
  // del supervisor (empujar al agente), NO robarle ancho al chat. 280px = la
  // columna REAL del grid del sidebar (state C: `280px 1fr`).
  const HISTORY_PX = 280;
  const histPct = (HISTORY_PX / Math.max(containerWidth, 1)) * 100;
  // ★ Ronda Chris 2026-06-11 (001.png): el MIN del panel en estado C debe incluir
  // el historial — si no, el drag clampea al min de B (320) y el historial (280)
  // se come el chat (~60px). Floor efectivo: chat-min + historial cuando C.
  const inStateC = isLg && supervisorOpen === "chat" && historyOpen;
  const minSupervisorEffectivePct = inStateC
    ? Math.min(80, minSupervisorPct + histPct)
    : minSupervisorPct;

  // ── Imperative Group ref for snap-up (Fix A — C3 bug mitigation) ─────────
  const groupRef = useGroupRef();

  // ── Imperative Panel ref for collapse/expand (BUG #1/#2 fix) ─────────────
  // v4: `collapse()` collapses to collapsedSize (bypasses minSize correctly).
  // `setLayout(stripPct)` was wrong — it clamps to minSize. `expand()` restores
  // from collapsed state so drag works again after reopen.
  const supervisorPanelRef = usePanelRef();

  // ── Drag-clamp (RN-8/RN-9) ────────────────────────────────────────────────
  // `collapsible` is DYNAMIC — true ONLY in state A (closed) or drawer mode
  // (below lg). When open (B/C) collapsible=false so the library clamps at
  // minSize on drag (never auto-collapses).
  const supervisorCollapsible = supervisorOpen === "closed" || !isLg;

  // Fix A: snap-up when containerWidth or minSupervisorPct changes (hydration
  // race + state change cycle). Signals readiness once layout reconciled.
  //
  // BUG #2 fix: use `supervisorPanelRef.current.collapse()` for the closed path
  // instead of `setLayout({supervisor: stripPct})` — setLayout clamps to minSize
  // and leaves a ~274px gap. `collapse()` targets collapsedSize (44px strip).
  //
  // BUG #1 fix: after a collapse→reopen cycle the panel's internal collapsed
  // state stays true even after setLayout — `expand()` must be called BEFORE
  // any setLayout so the library re-enables drag.
  useEffect(() => {
    if (containerWidth <= 0 || !groupRef.current) return;
    // Below lg: collapse supervisor to 0 so the agent panel takes full width
    // (drawer/overlay mode). Panel is `collapsible collapsedSize={0}`.
    if (!isLg) {
      groupRef.current.setLayout({
        [SUPERVISOR_PANEL_ID]: 0,
        [APP_PANEL_ID]: 100,
      });
      setShellReady(true);
      return;
    }
    // State A: closed → collapse() to collapsedSize (44px strip).
    if (supervisorOpen === "closed") {
      // ★ Live-fix 2026-06-11 (round 3): un único collapse() inmediato es no-op en
      // la transición runtime — el Group re-aplica el layout PERSISTIDO
      // (useDefaultLayout) al panel remontado y pisa el collapse si llega antes
      // del registro. Retry por rAF hasta que isCollapsed() (max ~30 frames):
      // converge en cuanto el Group registró el panel. En page-mount el primer
      // intento ya pega (containerWidth llega tarde → race ganada).
      let cancelled = false;
      let raf = 0;
      const tryCollapse = (attempt: number) => {
        if (cancelled) return;
        const handle = supervisorPanelRef.current;
        if (handle) {
          if (handle.isCollapsed()) {
            setShellReady(true);
            return;
          }
          handle.collapse();
        }
        if (attempt < 30) {
          raf = requestAnimationFrame(() => tryCollapse(attempt + 1));
        } else {
          setShellReady(true); // no bloquear el shell si la lib nunca registra
        }
      };
      tryCollapse(0);
      setShellReady(true);
      return () => {
        cancelled = true;
        cancelAnimationFrame(raf);
      };
    }
    // Open (state B/C): if panel is currently collapsed (e.g. just came from
    // state A via a click on the strip), call expand() FIRST so the library
    // marks the panel as non-collapsed. Without expand(), the drag handle
    // silently ignores input (BUG #1).
    if (supervisorPanelRef.current?.isCollapsed()) {
      supervisorPanelRef.current.expand();
    }
    const layout = groupRef.current.getLayout();
    const supervisorPct = layout[SUPERVISOR_PANEL_ID];
    // Snap up to minSupervisorPct if the current (or restored-from-expand)
    // width is below the legibility floor (e.g. still at strip width post-expand).
    if (supervisorPct !== undefined && supervisorPct < minSupervisorPct) {
      groupRef.current.setLayout({
        [SUPERVISOR_PANEL_ID]: minSupervisorPct,
        [APP_PANEL_ID]: 100 - minSupervisorPct,
      });
    }
    setShellReady(true);
    // deps SAGRADAS — verbatim from source (do not "optimize").
  }, [containerWidth, minSupervisorPct, groupRef, supervisorPanelRef, isLg, supervisorOpen, stripPct]);

  // ★ Live-fix 2026-06-11 — RN-7 push REAL del historial.
  // El historial EMPUJA (ensancha el panel del supervisor, angosta el agente) —
  // NO come del ancho del chat. Al flip de historyOpen: setLayout(actual ± histPct).
  // Floor en C: minSupervisorPct + histPct (chat nunca < min legible con historial).
  const prevHistoryOpenRef = useRef(historyOpen);
  useEffect(() => {
    const prev = prevHistoryOpenRef.current;
    prevHistoryOpenRef.current = historyOpen;
    if (prev === historyOpen) return; // solo en el flip
    if (!isLg || supervisorOpen !== "chat" || !groupRef.current) return;
    const layout = groupRef.current.getLayout();
    const current = layout[SUPERVISOR_PANEL_ID];
    if (current === undefined) return;
    const maxPct = 100 - minAppPct;
    const target = historyOpen
      ? Math.min(maxPct, Math.max(current + histPct, minSupervisorPct + histPct))
      : Math.max(minSupervisorPct, current - histPct);
    // ★ Retry rAF (ronda Chris 2026-06-11): el toggle B↔C REMONTA el panel (key
    // incluye hist-state para que la lib registre el minSize dinámico) y la
    // persistencia del Group re-aplica el layout viejo pisando el primer
    // setLayout — mismo patrón que el collapse de estado A. Reintentar hasta
    // converger (~30 frames máx).
    let cancelled = false;
    let raf = 0;
    const apply = (attempt: number) => {
      if (cancelled || !groupRef.current) return;
      const now = groupRef.current.getLayout()[SUPERVISOR_PANEL_ID];
      if (now !== undefined && Math.abs(now - target) <= 0.5) return; // convergió
      groupRef.current.setLayout({
        [SUPERVISOR_PANEL_ID]: target,
        [APP_PANEL_ID]: 100 - target,
      });
      if (attempt < 30) raf = requestAnimationFrame(() => apply(attempt + 1));
    };
    apply(0);
    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
    };
  }, [historyOpen, isLg, supervisorOpen, groupRef, histPct, minSupervisorPct, minAppPct]);

  // Persist layout across page reloads via localStorage.
  // Safe to call directly: this component is client-only via dynamic({ssr:false}).
  const layoutProps = useDefaultLayout({
    id: splitGroupId,
    panelIds: [SUPERVISOR_PANEL_ID, APP_PANEL_ID],
    storage: window.localStorage,
  });

  // ── End of unconditional hooks (D3) ────────────────────────────────────────
  // No JSX branch by viewport — the single resizable <Group> is the only layout.
  // Hook count is identical across renders.

  const supervisorLabels = buildSupervisorLabels(supervisorName, labels);

  // Injected chat slot (ChatPanel with brand-injected stores + classes).
  const chatSlot = (
    <ChatPanel
      supervisor={
        agentCatalog.find((d) => d.slug === supervisorSlug) ?? agentCatalog[0] ?? {
          slug: supervisorSlug,
          name: supervisorName,
          initial: supervisorInitial ?? supervisorName[0] ?? "?",
          role: "",
          colorToken: "",
          colorSoftToken: "",
          tabLabel: supervisorName,
          defaultSubtab: "",
          thumbnail: supervisorThumbnail,
        }
      }
      agentCatalog={Object.fromEntries(agentCatalog.map((d) => [d.slug, d]))}
      status="online"
      useShellStore={useShellStore}
      useChatStore={useChatStore}
      getAgentClasses={getAgentClasses}
      statusDotClass={statusDotClass}
      // T-V2 fix-loop (axe): el original pintaba el bubble del usuario con el
      // accent del supervisor (bg-agent-* + text-white = AA en las paletas brand).
      // El default bg-primary del kit (cyan vitalia) daba 2.49 white-on-cyan.
      userBubbleBgClass={getAgentClasses(supervisorSlug).accentBg}
      testIds={testIds}
    />
  );

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground">
      {/* Top bar — always visible (48px). Right cluster by slot. */}
      <TopBarShell
        supervisorName={supervisorName}
        useShellStore={useShellStore}
        logoSlot={logoSlot}
        rightClusterSlot={rightClusterSlot}
        labels={labels}
      />

      {/*
       * ── SINGLE <main id="main-content"> (D1) ──────────────────────────────
       * ONE main element wraps ALL chrome variants. containerRef lives here so
       * ResizeObserver measures the correct element in all modes (D5).
       * single-slot (D2): <AppPanelSlot>{children}</AppPanelSlot> is rendered
       * EXACTLY ONCE. <Group> is ALWAYS mounted (never gated by viewport — D4);
       * below lg the supervisor panel collapses to 0 (effect above) → hook-count
       * stable (D3).
       */}
      <main
        id="main-content"
        tabIndex={-1}
        className="flex-1 min-h-0 overflow-hidden"
        aria-label={labels?.mainContent ?? "Contenido principal"}
        ref={containerRef}
        data-shell-ready={shellReady ? "true" : "false"}
      >
        <ResizableGroup
          id={splitGroupId}
          orientation="horizontal"
          className="h-full"
          groupRef={groupRef}
          {...layoutProps}
          onLayoutChanged={layoutProps.onLayoutChanged}
        >
          <Panel
            id={SUPERVISOR_PANEL_ID}
            // ★ Live-fix 2026-06-11 (Chris repro): v4 captura collapsible/collapsedSize
            // AL MONTAR — la transición runtime open↔closed con props dinámicas era
            // INERTE. El key fuerza REMOUNT del Panel en cada cambio de estado → la
            // lib registra las props frescas y el effect collapse() corre en
            // mount-path. Bonus: remount limpia el drag-state interno → resize vivo
            // post-ciclo.
            // ★ Ronda Chris 2026-06-11: key incluye B|C — la lib captura minSize en
            // MOUNT; el min dinámico de C (chat-min + 280) solo aplica si el panel
            // REMONTA al togglear historial. El push/restore del ancho lo hace el
            // effect RN-7 (retry rAF contra la persistencia).
            key={`supervisor-${!isLg ? "mobile" : supervisorOpen === "closed" ? "A" : historyOpen ? "C" : "B"}`}
            // ★ Live-fix 2026-06-11 (round 2): el collapse() imperativo post-remount
            // corre ANTES de que el Group registre el panel nuevo (race) → no-op en
            // transición runtime. Vía determinista: el panel remontado NACE en el
            // tamaño destino — closed → defaultSize=stripPct (< minSize +
            // collapsible=true → la lib AUTO-COLAPSA a collapsedSize=44px por
            // contrato v4). El collapse() del effect queda como backup.
            defaultSize={!isLg ? 0 : supervisorOpen === "closed" ? stripPct : defaultSupervisorPct}
            minSize={`${minSupervisorEffectivePct}%`}
            // Drag-clamp (RN-8/RN-9): collapsible dynamic — true solo en A o drawer.
            collapsible={supervisorCollapsible}
            // ★ Live-fix 2026-06-11: v4 units — number = PX, string "NN%" = %.
            // collapsedSize={stripPct} (3.4375) era 3.4 PX, no 44px.
            collapsedSize={isLg ? STRIP_SUPERVISOR_PX : 0}
            // BUG #1/#2 fix: imperative ref so we can call collapse() / expand().
            panelRef={supervisorPanelRef}
          >
            {/* SupervisorSidebar stays mounted at all widths (its drawer portals
                to document.body); the inline aside hides itself < lg, and the
                Panel collapses to 0 < lg so the agent gets full width. */}
            <div className="h-full">
              <SupervisorSidebar
                supervisorSlug={supervisorSlug}
                supervisorName={supervisorName}
                supervisorInitial={supervisorInitial}
                supervisorThumbnail={supervisorThumbnail}
                getAgentClasses={getAgentClasses}
                useShellStore={useShellStore}
                useChatStore={useChatStore}
                chatSlot={chatSlot}
                labels={supervisorLabels}
                testIds={testIds}
                statusDotClass={statusDotClass}
              />
            </div>
          </Panel>

          {/* Separator — hidden on mobile (no resize handle when supervisor
              container is invisible). */}
          <ResizeSeparator
            id="shell-handle"
            className={cn(
              "hidden lg:block",
              // ★ Live-fix 2026-06-11: en estado A (closed) NO hay resize — drag
              // del seam expandiría el panel collapsed SIN pasar por el store
              // (estado inconsistente = gap con strip adentro). RN-9: reabrir
              // SOLO por avatar. Seam oculto en A.
              supervisorOpen === "closed" && "lg:hidden",
              // ★ Fix 2026-05-24: 1px visible (mockup parity) pero 8px hit area.
              "group relative w-2 shrink-0 bg-transparent cursor-col-resize outline-none",
              "after:absolute after:left-1/2 after:top-0 after:h-full after:w-px after:-translate-x-1/2",
              "after:bg-border after:transition-all after:duration-150",
              "hover:after:w-0.5 hover:after:bg-primary/60",
              "focus-visible:after:w-0.5 focus-visible:after:bg-primary",
            )}
            aria-label="Redimensionar paneles"
          />

          {/* App panel — ALWAYS visible. On mobile it takes full width since the
              supervisor panel is collapsed to 0. Contains the single
              <AppPanelSlot> — the ONLY slot in the DOM. */}
          <Panel
            id={APP_PANEL_ID}
            defaultSize={isLg ? 100 - defaultSupervisorPct : 100}
            minSize={`${minAppPct}%`}
          >
            <AppPanelSlot
              agentCatalog={agentCatalog}
              ribbonOrder={ribbonOrder}
              subTabsByAgent={subTabsByAgent}
              subSubTabsByKey={subSubTabsByKey}
              shippedStaticSubtabs={shippedStaticSubtabs}
              getAgentClasses={getAgentClasses}
              useShellStore={useShellStore}
              labels={labels}
              onNavigate={onNavigate}
            >
              {children}
            </AppPanelSlot>
          </Panel>
        </ResizableGroup>
      </main>
      {/* Sonner toast portal — required for toast() calls throughout the shell.
          Rendered here (inside client-only boundary) to avoid SSR issues. */}
      <Toaster position="bottom-right" richColors />
    </div>
  );
}

export type { ShellLayoutProps };
