// story-origin: platform-lift-shell-chrome-ui-kit T-V1
"use client";
/**
 * ShellLayoutWire.tsx — T-V1 re-wire: mounts @luana/ui-kit ShellLayout with
 * vitalia brand props (catalog, store, testIds, slots).
 *
 * Lives in (shell-organism)/_components/ — consumed by layout.tsx (Server
 * Component) alongside the existing ShellOrganismLayout (deleted in T-V2).
 *
 * Bridge pattern: until T-V2 removes the chrome, layout.tsx renders this
 * wrapper which passes the new kit store + brand props.
 *
 * Client component (required): calls usePathname() + useShellStoreKit (zustand).
 *
 * SC-6: splitGroupId = 'vitalia-shell-split-agentic' + storageKey 'vitalia-shell-state'
 * conserved via useShellStoreKit (shell-store.ts).
 *
 * testIds: legacy vitalia values preserved — e2e suite asserts these verbatim.
 *
 * HIPAA-lite: not_applicable — layout chrome state; no PHI exposed here.
 * No Clerk Organizations — per MEMORY.md::no-clerk-organizations 2026-05-20.
 *
 * downstream-regression-na: brand-local layout; no cross-brand consumers.
 */

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { useStoreHydration } from "@luana/hooks/use-store-hydration";
import {
  ShellLayout,
  type AgentClassBundle,
  type ShellAgentDescriptor,
  type ShellChatStore,
  type ShellSubSubTabMeta,
  type ShellTestIds,
} from "@luana/ui-kit";

import {
  AGENT_CATALOG,
  AGENT_RIBBON_ORDER,
  RIBBON_SUBTABS,
  SHIPPED_STATIC_SUBTABS,
  type AgentSlug,
  type RibbonTabSlug,
} from "@/lib/agent-catalog";
import { AGENT_SUBSUBTABS } from "@/lib/shell-routes";
import {
  agentBgClass,
  agentBgSoftClass,
  agentTextClassSubTab,
} from "@/components/shared/shell-organism/_agent-tw-classes";
import { LogoMark } from "@/components/shared/shell-organism/LogoMark";
import { TenantSwitcher } from "@/components/shared/shell-organism/TenantSwitcher";
import { ThemeToggle } from "@/components/shared/shell-organism/ThemeToggle";
import { useChatStore } from "@/stores/chat-store";
import { useShellStoreKit } from "@/stores/shell-store";
import { useTenantStore } from "@/stores/tenant-store";

// ── Agent border class (JIT-static switch — Tailwind v4 requires literal strings) ────

/**
 * Per-agent accent border class.
 * CRITICAL: Tailwind v4 JIT purges dynamic class names — explicit switch only.
 */
function agentBorderClass(slug: AgentSlug): string {
  switch (slug) {
    case "lisa":
      return "border-agent-lisa";
    case "valeria":
      return "border-agent-valeria";
    case "adrian":
      return "border-agent-adrian";
    case "lucas":
      return "border-agent-lucas";
    case "camila":
      return "border-agent-camila";
    case "mateo":
      return "border-agent-mateo";
    default:
      return "border-agent-valeria";
  }
}

// ── getAgentClasses — brand-injected function (kit AgentClassBundle) ────────────

/**
 * Maps a vitalia agent slug → AgentClassBundle consumed by kit chrome atoms
 * (Ribbon active pill, avatar ring, hover states, border accents).
 *
 * Slug typed as `string` (kit contract) — unknown slugs fall back to valeria.
 */
function getAgentClasses(slug: string): AgentClassBundle {
  const s = (slug as AgentSlug) in AGENT_CATALOG ? (slug as AgentSlug) : "valeria";
  // agentTextClassSubTab handles WCAG AA contrast exceptions (mateo D20, lucas D18, config D19)
  return {
    accentBg: agentBgClass(s),
    softBg: agentBgSoftClass(s),
    accentText: agentTextClassSubTab(s as RibbonTabSlug),
    accentBorder: agentBorderClass(s),
  };
}

// ── ShellAgentDescriptor[] built from vitalia AGENT_CATALOG ─────────────────────

const AGENT_CATALOG_ARRAY: ShellAgentDescriptor[] = Object.values(AGENT_CATALOG).map(
  (desc) => ({
    slug: desc.slug,
    name: desc.name,
    role: desc.role,
    colorToken: desc.colorToken,
    colorSoftToken: desc.colorSoftToken,
    initial: desc.initial,
    thumbnail: desc.thumbnail,
    tabLabel: desc.tabLabel,
    defaultSubtab: desc.defaultSubtab,
  }),
);

// ── Legacy vitalia testIds (e2e suite asserts these verbatim — DO NOT rename) ────

const TEST_IDS: ShellTestIds = {
  supervisorSidebar: "valeria-sidebar",
  supervisorCollapsedStrip: "valeria-collapsed-strip",
  supervisorDrawerBackdrop: "valeria-drawer-backdrop",
  supervisorDrawerClose: "valeria-drawer-close",
  chat: "valeria-chat",
  chatHeader: "chat-header",
  chatModePill: "chat-mode-pill",
};

// ── Ribbon order (string[] from const tuple) ─────────────────────────────────────

const RIBBON_ORDER: string[] = [...AGENT_RIBBON_ORDER];

// ── subTabsByAgent — convert RIBBON_SUBTABS (RibbonTabSlug keys) to string keys ──

const SUB_TABS_BY_AGENT: Record<string, readonly { id: string; label: string; icon: string }[]> =
  Object.fromEntries(
    Object.entries(RIBBON_SUBTABS).map(([slug, tabs]) => [slug, tabs]),
  );

// ── Slots ────────────────────────────────────────────────────────────────────────

const LOGO_SLOT: ReactNode = (
  <>
    <LogoMark variant="full" size="md" className="hidden lg:inline-flex" />
    <LogoMark variant="mark" size="md" className="inline-flex lg:hidden" />
  </>
);

const RIGHT_CLUSTER_SLOT: ReactNode = (
  <>
    <ThemeToggle />
    <TenantSwitcher />
  </>
);

// ── Wire component ───────────────────────────────────────────────────────────────

interface ShellLayoutWireProps {
  children: ReactNode;
}

/**
 * Thin client bridge: provides `pathname` (requires usePathname hook) + wires
 * all vitalia brand props into @luana/ui-kit ShellLayout.
 *
 * T-V2 will replace this with a single canonical wiring (after chrome deletion).
 */
export function ShellLayoutWire({ children }: ShellLayoutWireProps) {
  const pathname = usePathname();

  // ★ ADR-vitalia-006: el chrome viejo hidrataba shell + tenant stores en su
  // LayoutClient (único rehydrate del árbol). El kit hidrata el shell store
  // (inyectado, dentro del chunk ssr:false); el TENANT store es brand-specific
  // → se hidrata acá. Sin esto, setItem queda NO-OP y nada persiste.
  useStoreHydration(useTenantStore);

  return (
    <ShellLayout
      supervisorName="Valeria"
      supervisorSlug="valeria"
      supervisorThumbnail={AGENT_CATALOG.valeria.thumbnail}
      supervisorInitial="V"
      agentCatalog={AGENT_CATALOG_ARRAY}
      ribbonOrder={RIBBON_ORDER}
      subTabsByAgent={SUB_TABS_BY_AGENT}
      // N3 sub-sub-tabs (lisa.marca, config.cuenta) — fix regresión lift 3cb9d5a0:
      // el kit declaraba subSubTabsByKey en AppPanelSlot pero nadie lo cableaba.
      subSubTabsByKey={AGENT_SUBSUBTABS as Record<string, readonly ShellSubSubTabMeta[]>}
      shippedStaticSubtabs={SHIPPED_STATIC_SUBTABS}
      getAgentClasses={getAgentClasses}
      useShellStore={useShellStoreKit}
      // Vitalia's useChatStore is a plain zustand store (not SsrSafePersistedStore).
      // The kit only calls it as a hook + reads its API — compatible at runtime.
      // The .persist surface is absent; kit does NOT call .persist on the chat store.
      // Type-cast: zustand StoreApi<ChatStore> → ShellChatStore (SsrSafePersistedStore).
      // Safe: kit only reads messages/status/sendMessage — no .persist call.
      useChatStore={useChatStore as unknown as ShellChatStore}
      splitGroupId="vitalia-shell-split-agentic"
      logoSlot={LOGO_SLOT}
      rightClusterSlot={RIGHT_CLUSTER_SLOT}
      testIds={TEST_IDS}
      pathname={pathname}
      configTabSlug="config"
      configTabLabel="Plataforma"
    >
      {children}
    </ShellLayout>
  );
}
