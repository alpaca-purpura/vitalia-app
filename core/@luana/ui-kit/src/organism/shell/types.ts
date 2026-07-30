// cap: platform.lift-shell-chrome-ui-kit
import type { ReactNode } from "react";
import type { ShellSubSubTabMeta } from "./SubSubTabsBar";
import type {
  SsrSafeHydration,
  SsrSafePersistedStore,
} from "@luana/hooks/create-ssr-safe-persisted-store";

/**
 * Generic shell organism types — brand-agnostic (T-K1).
 *
 * Naming is generic by contract (RN-2): the kit never references a brand or a
 * supervisor name. The brand injects its catalog + supervisor identity at mount.
 * Zero 'valeria' / 'vitalia' / 'nicolify' tokens live here.
 *
 * Verbatim from 03-arch.md § API contract — organism kit.
 */

// ── Generic agent descriptor (brand injects its catalog) ──────────────────────
export interface ShellAgentDescriptor {
  /** 'lisa' | 'abel' | ... — brand-defined, NOT an enum in the kit. */
  slug: string;
  name: string;
  role: string;
  /**
   * CSS var token name for the agent color, e.g. "agent-lisa". The brand's
   * globals.css defines `--agent-lisa`; the kit references it via the token.
   */
  colorToken: string;
  colorSoftToken: string;
  initial: string;
  /** Avatar: a slot/ReactNode OR an image src — brand decides. */
  avatar?: ReactNode;
  thumbnail?: string;
  tabLabel: string;
  defaultSubtab: string;
}

export interface ShellSubTabMeta {
  id: string;
  label: string;
  /** emoji (parity ribbon catalog) — brand-provided. */
  icon: string;
}

// ── Shell store contract (brand instantiates via createShellStore) ────────────

/** Generic supervisor open state — NOT "valeria*". A=closed (strip) · B=chat (split). */
export type SupervisorOpen = "closed" | "chat";

/** Persisted slice of the shell store (what survives a reload · SC-6). */
export interface ShellPersistedState {
  supervisorOpen: SupervisorOpen;
  splitPct: number | null;
  mobileDrawerOpen: boolean;
}

/** Full shell store state + actions (brand instantiates via createShellStore). */
export interface ShellStoreState extends SsrSafeHydration {
  // ── State ──────────────────────────────────────────────────────────────────
  /** A=closed (collapsed strip) · B=chat (split layout). */
  supervisorOpen: SupervisorOpen;
  /** Additive push panel (machine C) — never restored from persistence (no-clobber). */
  historyOpen: boolean;
  /** null = default (the layout resolves the default split, e.g. 30) · number = user-set %. */
  splitPct: number | null;
  mobileDrawerOpen: boolean;

  // ── Actions ─────────────────────────────────────────────────────────────────
  /** Set the supervisor open state. Setting "closed" forces historyOpen false (RN-5). */
  setSupervisorOpen: (open: SupervisorOpen) => void;
  /** Open the supervisor in chat. Does NOT restore history (RN-6). */
  openSupervisor: () => void;
  /** Collapse the supervisor: closed + history false (RN-6). */
  collapseSupervisor: () => void;
  /** Set history panel state directly. */
  setHistoryOpen: (open: boolean) => void;
  /** Open history: forces supervisorOpen "chat" + historyOpen true (RN-7). */
  openHistory: () => void;
  /** Close history (keeps chat). */
  closeHistory: () => void;
  /** Toggle history (opening forces chat). */
  toggleHistory: () => void;
  /** Set the split percentage (null resets to default). */
  setSplitPct: (pct: number | null) => void;
  /** Set the mobile drawer open state. */
  setMobileDrawerOpen: (open: boolean) => void;
}

// ── Chat store contract (the chat sub-tree reads this; brand provides impl) ────
/** Message role — determines the bubble render variant. */
export type ShellMessageRole = "bot" | "user" | "delegate" | "thinking";

/** A chat message (covers all role variants). Brand-agnostic shape. */
export interface ShellChatMessage {
  id: string;
  role: ShellMessageRole;
  /** bot/user/thinking text content. */
  content?: string;
  /** 'HH:MM' display time. */
  time?: string;
  /** bot/thinking source agent slug. */
  agent?: string;
  /** delegate only — who delegates. */
  fromAgent?: string;
  /** delegate only — who receives the delegation. */
  toAgent?: string;
  /** delegate only — mode label ('Mantener'/'Reactivar'/'Multiplicar'). */
  delegateMode?: string;
}

/** Chat status. */
export type ShellChatStatus = "idle" | "thinking" | "streaming";

/** A history conversation entry (UI-local archive · zero PHI by construction). */
export interface ShellConversationMeta {
  id: string;
  title: string;
  meta?: string;
  /** time bucket the history groups by. */
  group: "today" | "yesterday" | "this_week";
}

/**
 * Generic chat store state the chat sub-tree reads (brand provides the impl;
 * vitalia's is a MOCK conversational store today). The kit consumes this typed
 * surface — no brand names leak in (RN-2).
 */
export interface ShellChatStoreApi {
  messages: ShellChatMessage[];
  conversations: ShellConversationMeta[];
  /** active agent slug for new messages. */
  activeAgent: string;
  status: ShellChatStatus;
  sendMessage: (content: string) => void;
  clearMessages: () => void;
  newConversation: () => void;
  setActiveAgent: (agent: string) => void;
}

/**
 * A bound store carrying the shell state + SSR-safe hydration surface.
 * This is the concrete type returned by `createShellStore` (and consumed by
 * `ShellLayoutProps.useShellStore`) — the `@luana/hooks` persisted-store shape,
 * which extends the zustand hook with `.persist`/`.getState`/`.setState` (RN-8).
 */
export type ShellStore = SsrSafePersistedStore<ShellStoreState>;

/** A generic bound store for the brand-provided chat store (SSR-safe shape). */
export type ShellChatStore = SsrSafePersistedStore<ShellChatStoreApi & SsrSafeHydration>;

// ── Factory options (consumes @luana/hooks/createSsrSafePersistedStore) ───────
export interface CreateShellStoreOptions {
  /** brand passes 'vitalia-shell-state' / 'nicolify-shell-state' (SC-6 compat). */
  storageKey: string;
  /** default 1; brand passes its migrate() if the legacy shape differs. */
  version?: number;
  /** maps a legacy persisted shape into a partial of the generic state. */
  migrate?: (persisted: unknown, version: number) => Partial<ShellStoreState>;
}

// ── Agent class injection (JIT-static literal classes are brand-coupled) ──────
/**
 * Per-agent Tailwind class bundle the chrome atoms render. The brand owns the
 * JIT-static literal switch (its color tokens) and injects it as a function;
 * the kit ships ZERO brand color literals (RN-2). Slug → class names.
 */
export interface AgentClassBundle {
  /** solid accent bg (e.g. ribbon active pill). */
  accentBg: string;
  /** soft/tint bg (e.g. avatar ring, hover). */
  softBg: string;
  /** accent text/foreground. */
  accentText: string;
  /** accent border. */
  accentBorder: string;
}

export type GetAgentClasses = (slug: string) => AgentClassBundle;

// ── data-testid bundle (brand owns the literals its e2e asserts) ──────────────
/**
 * The chrome's data-testid values are part of the brand's e2e contract (vitalia
 * asserts `valeria-sidebar`, etc.). The kit ships ZERO brand-named testids
 * (RN-2): the brand injects this bundle and the kit renders the values verbatim.
 * Every field is optional; the kit only sets the attribute when provided.
 */
export interface ShellTestIds {
  supervisorSidebar?: string;
  supervisorCollapsedStrip?: string;
  supervisorStripStatusDot?: string;
  supervisorDrawerBackdrop?: string;
  supervisorDrawerClose?: string;
  composerPlaceholder?: string;
  chat?: string;
  chatHeader?: string;
  chatAvatar?: string;
  chatStatusDot?: string;
  chatModePill?: string;
}

// ── Root organism props ───────────────────────────────────────────────────────
export interface ShellLayoutLabels {
  openSupervisor: string;
  collapseSupervisor: string;
  newConversation: string;
  history: string;
  mainContent: string;
}

export interface ShellLayoutProps {
  children: ReactNode;
  // Brand identity (NO defaults that name a brand) ----------------------------
  /** e.g. "Valeria" | "Luana" — REQUIRED, no default. */
  supervisorName: string;
  /** The supervisor agent's slug (for class injection + chat). */
  supervisorSlug: string;
  /** slot; falls back to <initial> circle. */
  supervisorAvatar?: ReactNode;
  /** e.g. "V" | "L". */
  supervisorInitial?: string;
  /** Optional thumbnail URL for the supervisor's avatar. */
  supervisorThumbnail?: string;
  agentCatalog: ShellAgentDescriptor[];
  /** agent slugs in ribbon order. */
  ribbonOrder: string[];
  subTabsByAgent: Record<string, readonly ShellSubTabMeta[]>;
  /**
   * N3 sub-sub-tabs por key "agent.subtab" (brand inyecta su AGENT_SUBSUBTABS).
   * Optional + default {} — fix regresión lift 3cb9d5a0: AppPanelSlot declaraba la
   * prop pero ShellLayoutClient nunca la recibía → barra N3 nunca se pintaba.
   */
  subSubTabsByKey?: Record<string, readonly ShellSubSubTabMeta[]>;
  shippedStaticSubtabs?: ReadonlySet<string>;
  /** brand-injected per-agent class bundle (JIT-static literals stay brand-side). */
  getAgentClasses: GetAgentClasses;
  // Store injection (brand instantiates) -------------------------------------
  useShellStore: ShellStore;
  useChatStore: ShellChatStore;
  // Group/layout persistence keys (SC-6 compat — brand passes its key) --------
  /** e.g. "vitalia-shell-split-agentic". */
  splitGroupId: string;
  // TopBar slots (brand injects Logo/Theme/Tenant) ---------------------------
  /** brand LogoMark. */
  logoSlot: ReactNode;
  /** brand [ThemeToggle][TenantSwitcher]. */
  rightClusterSlot: ReactNode;
  // SSR skeleton (brand provides store-free header) --------------------------
  /** default = neutral inert header. */
  skeletonSlot?: ReactNode;
  // Copy / labels (Spanish neutro — brand may override) ----------------------
  labels?: Partial<ShellLayoutLabels>;
  // Routing helpers (or kit defaults from agentCatalog) ----------------------
  /**
   * Current pathname (brand passes `usePathname()`). The kit derives the active
   * agent / sub-tab / sub-sub-tab from it via routing.ts helpers and builds
   * hrefs from segment[0] (tenant) — it never imports next/navigation (RN-2).
   */
  pathname: string;
  /** the special (non-agent) tab slug, e.g. "config"/"settings". */
  configTabSlug?: string;
  /** label for the special config tab (Spanish neutro; brand may override). */
  configTabLabel?: string;
  onNavigate?: (href: string) => void;
  // data-testid contract (brand owns the literals — RN-2) -------------------
  /** brand e2e testid bundle; kit renders values verbatim, omits when absent. */
  testIds?: ShellTestIds;
  /** status-dot Tailwind bg class (brand token, e.g. "bg-emerald-500"). */
  statusDotClass?: string;
}

// ── Routing helper options (catalog injected by the brand) ────────────────────
export interface ShellRoutingOptions {
  /** the brand's agent slug-set (membership check). */
  agentSlugs: readonly string[];
  /** non-agent tabs that still route (e.g. "settings"/"config"). */
  specialTabs?: readonly string[];
  /** subtab slugs valid per agent/special-tab. */
  subtabsByAgent: Record<string, readonly string[]>;
}
