/*
 * Shared demo fixtures for the Shell organism stories (core-ds-foundation T-2).
 *
 * The shell kit is brand-agnostic (RN-2): the brand injects its agent catalog +
 * a getAgentClasses() fn at mount. These fixtures mirror that contract for the TWO
 * brands the toolbar switches between (vitalia · nicolify), so switching the `brand`
 * global flips the DATA (names + per-agent colors + avatars + logo), not just CSS.
 * This is DEMO data in stories/, NOT kit src (RN-2 intact).
 *
 * ★ getAgentClasses MUST return LITERAL class strings (a switch, never a
 *   template like `bg-agent-${slug}`). Tailwind v4 JIT only emits classes it
 *   sees verbatim; a constructed string purges to nothing (gray/black render —
 *   the same trap as the chart-black bug). These literals live under stories/,
 *   scanned via `@source "../stories"` in preview.css. Mirrors why each brand's
 *   real _agent-tw-classes.ts uses a literal switch.
 *
 * NOT a *.stories.* file → ignored by the story glob, imported by the stories.
 */

import type { ReactNode } from "react";
import {
  createShellStore,
  type AgentClassBundle,
  type ShellAgentDescriptor,
  type ShellChatMessage,
  type ShellChatStoreApi,
  type ShellConversationMeta,
  type ShellSubTabMeta,
  type ShellSubSubTabMeta,
} from "../src";
import {
  createSsrSafePersistedStore,
  type SsrSafeHydration,
} from "@luana/hooks/create-ssr-safe-persisted-store";

/** A brand's full demo fixture set — the data the shell stories render. */
export interface BrandFixtureSet {
  brand: "vitalia" | "nicolify";
  /** Full catalog (all agents, supervisor first). */
  agentsAll: ShellAgentDescriptor[];
  /** Ribbon-only catalog (in ribbon order). */
  agentsRibbon: ShellAgentDescriptor[];
  /** Catalog keyed by slug (for stories that look up a single agent). */
  agentsBySlug: Record<string, ShellAgentDescriptor>;
  /** Ribbon order (slugs). */
  ribbonOrder: string[];
  /** Literal Tailwind class resolver (see file header). */
  getAgentClasses: (slug: string) => AgentClassBundle;
  /** Sub-tabs per ribbon agent (N2). */
  subTabsByAgent: Record<string, ShellSubTabMeta[]>;
  /** Sub-sub-tabs by "agent.subtab" (N3-static). */
  subSubTabsByKey: Record<string, ShellSubSubTabMeta[]>;
  /** Supervisor (sidebar) descriptor — Valeria / Luana. */
  supervisor: ShellAgentDescriptor;
  /** Config/Plataforma tab label. */
  configTabLabel: string;
  /** Brand logo (CSS light/dark swap). */
  Logo: () => ReactNode;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * VITALIA — real 6-agent catalog (Valeria supervisor + Lisa/Mateo/Adrián/Lucas/
 * Camila). Mirrors vitalia/frontend/src/lib/agent-catalog.ts. preview.css :root
 * carries the matching agent palette.
 * ═══════════════════════════════════════════════════════════════════════════ */

const VITALIA_AGENTS: Record<string, ShellAgentDescriptor> = {
  valeria: {
    slug: "valeria",
    name: "Valeria",
    role: "Tu secretaria virtual · coordinadora general",
    colorToken: "agent-valeria",
    colorSoftToken: "agent-valeria-soft",
    initial: "V",
    thumbnail: "/sb-assets/agents/valeria/thumbnail.png",
    tabLabel: "Valeria",
    defaultSubtab: "agenda",
  },
  lisa: {
    slug: "lisa",
    name: "Lisa",
    role: "Estratega de marca y oferta",
    colorToken: "agent-lisa",
    colorSoftToken: "agent-lisa-soft",
    initial: "L",
    thumbnail: "/sb-assets/agents/lisa/thumbnail.png",
    tabLabel: "Mi Clínica",
    defaultSubtab: "marca",
  },
  mateo: {
    slug: "mateo",
    name: "Mateo",
    role: "Operaciones · agenda y pacientes del día",
    colorToken: "agent-mateo",
    colorSoftToken: "agent-mateo-soft",
    initial: "M",
    thumbnail: "/sb-assets/agents/mateo/thumbnail.png",
    tabLabel: "Atender",
    defaultSubtab: "agenda",
  },
  adrian: {
    slug: "adrian",
    name: "Adrián",
    role: "Closer · califica leads y reactiva oportunidades",
    colorToken: "agent-adrian",
    colorSoftToken: "agent-adrian-soft",
    initial: "A",
    thumbnail: "/sb-assets/agents/adrian/thumbnail.png",
    tabLabel: "Vender",
    defaultSubtab: "inbox",
  },
  lucas: {
    slug: "lucas",
    name: "Lucas",
    role: "Estratega Growth · viraliza y consigue leads",
    colorToken: "agent-lucas",
    colorSoftToken: "agent-lucas-soft",
    initial: "L",
    thumbnail: "/sb-assets/agents/lucas/thumbnail.png",
    tabLabel: "Atraer",
    defaultSubtab: "lanzar",
  },
  camila: {
    slug: "camila",
    name: "Camila",
    role: "Fidelización · sube CLTV y monitorea satisfacción",
    colorToken: "agent-camila",
    colorSoftToken: "agent-camila-soft",
    initial: "C",
    thumbnail: "/sb-assets/agents/camila/thumbnail.png",
    tabLabel: "Mantener",
    defaultSubtab: "voz",
  },
};

/**
 * Vitalia brand-injected class resolver — LITERAL switch (see file header).
 * accentText uses the SubTab contrast exceptions (mateo/lucas → text-foreground,
 * because yellow/near-black fail WCAG AA on their own -soft bg).
 */
function getVitaliaAgentClasses(slug: string): AgentClassBundle {
  switch (slug) {
    case "lisa":
      return {
        accentBg: "bg-agent-lisa",
        softBg: "bg-agent-lisa-soft",
        accentText: "text-agent-lisa",
        accentBorder: "border-agent-lisa",
      };
    case "mateo":
      return {
        accentBg: "bg-agent-mateo",
        softBg: "bg-agent-mateo-soft",
        // #FEE209 yellow on its soft bg fails AA → text-foreground (vitalia D20).
        accentText: "text-foreground",
        accentBorder: "border-agent-mateo",
      };
    case "adrian":
      return {
        accentBg: "bg-agent-adrian",
        softBg: "bg-agent-adrian-soft",
        accentText: "text-agent-adrian",
        accentBorder: "border-agent-adrian",
      };
    case "lucas":
      return {
        accentBg: "bg-agent-lucas",
        softBg: "bg-agent-lucas-soft",
        // #111111 near-black on its soft bg fails AA → text-foreground (vitalia D18).
        accentText: "text-foreground",
        accentBorder: "border-agent-lucas",
      };
    case "camila":
      return {
        accentBg: "bg-agent-camila",
        softBg: "bg-agent-camila-soft",
        accentText: "text-agent-camila",
        accentBorder: "border-agent-camila",
      };
    case "valeria":
    default:
      return {
        accentBg: "bg-agent-valeria",
        softBg: "bg-agent-valeria-soft",
        accentText: "text-agent-valeria",
        accentBorder: "border-agent-valeria",
      };
  }
}

const VITALIA_RIBBON_ORDER: string[] = ["lisa", "lucas", "adrian", "mateo", "camila"];

const VITALIA_SUBTABS_BY_AGENT: Record<string, ShellSubTabMeta[]> = {
  lisa: [
    { id: "marca", label: "Marca", icon: "🏥" },
    { id: "staff", label: "Staff", icon: "👨‍⚕️" },
    { id: "servicios", label: "Servicios", icon: "🩺" },
    { id: "compliance", label: "Compliance", icon: "🛡️" },
  ],
  mateo: [
    { id: "agenda", label: "Agenda", icon: "📆" },
    { id: "pacientes", label: "Pacientes", icon: "👥" },
  ],
  adrian: [
    { id: "inbox", label: "Inbox", icon: "💬" },
    { id: "embudo", label: "Embudo", icon: "🎯" },
    { id: "recuperar", label: "Recuperar", icon: "🧊" },
    { id: "outbound", label: "Outbound", icon: "📣" },
    { id: "propuestas", label: "Propuestas", icon: "💼" },
  ],
  lucas: [
    { id: "lanzar", label: "Lanzar", icon: "🚀" },
    { id: "envuelo", label: "En vuelo", icon: "📡" },
    { id: "recursos", label: "Recursos", icon: "📚" },
    { id: "resultados", label: "Resultados", icon: "📈" },
    { id: "mercado", label: "Mercado", icon: "🌍" },
  ],
  camila: [
    { id: "voz", label: "Voz del paciente", icon: "🎤" },
    { id: "reactivar", label: "Reactivar", icon: "🪃" },
    { id: "multiplicar", label: "Multiplicar", icon: "🤝" },
    { id: "reputacion", label: "Reputación", icon: "📊" },
  ],
};

const VITALIA_SUBSUBTABS_BY_KEY: Record<string, ShellSubSubTabMeta[]> = {
  "lisa.marca": [
    { id: "identidad", label: "Identidad", icon: "🏥" },
    { id: "voz-y-tono", label: "Voz y tono", icon: "🎙️" },
    { id: "presencia", label: "Presencia", icon: "📍" },
  ],
  "lisa.servicios": [
    { id: "catalogo", label: "Catálogo", icon: "📋" },
    { id: "escalera", label: "Escalera", icon: "🪜" },
  ],
  "config.cuenta": [
    { id: "datos", label: "Datos", icon: "🏢" },
    { id: "preferencias", label: "Preferencias", icon: "⚙️" },
    { id: "responsable", label: "Responsable", icon: "🔐" },
  ],
};

/** Vitalia logo (real brand mark, CSS light/dark swap). */
function VitaliaLogo() {
  return (
    <span className="inline-flex items-center" aria-label="Clínica Demo inicio">
      <img src="/sb-assets/brand/vitalia-logo.png" alt="" className="block h-8 w-auto dark:hidden" />
      <img src="/sb-assets/brand/vitalia-logo-dark.png" alt="" className="hidden h-8 w-auto dark:block" />
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
 * NICOLIFY — real 6-agent catalog (Luana orchestrator sidebar + Abel/Brenda/
 * Christian/Sara/Norvil ribbon). Mirrors nicolify/frontend/src/lib/agent-catalog.ts
 * + shell-routes.ts (ribbon order, sub-tabs) + _agent-tw-classes.ts (literal switch).
 * preview.css [data-brand="nicolify"] carries the matching agent palette.
 * ═══════════════════════════════════════════════════════════════════════════ */

const NICOLIFY_AGENTS: Record<string, ShellAgentDescriptor> = {
  luana: {
    slug: "luana",
    name: "Luana",
    role: "Orquestadora · coordinadora del equipo de agentes",
    colorToken: "agent-luana",
    colorSoftToken: "agent-luana-soft",
    initial: "L",
    thumbnail: "/sb-assets/agents/luana/avatar.svg",
    tabLabel: "Luana",
    defaultSubtab: "",
  },
  abel: {
    slug: "abel",
    name: "Abel",
    role: "Estratega · branding y oferta",
    colorToken: "agent-abel",
    colorSoftToken: "agent-abel-soft",
    initial: "A",
    thumbnail: "/sb-assets/agents/abel/avatar.svg",
    tabLabel: "Estrategia",
    defaultSubtab: "icp",
  },
  brenda: {
    slug: "brenda",
    name: "Brenda",
    role: "Guardiana del presupuesto · growth",
    colorToken: "agent-brenda",
    colorSoftToken: "agent-brenda-soft",
    initial: "B",
    thumbnail: "/sb-assets/agents/brenda/avatar.svg",
    tabLabel: "Growth",
    defaultSubtab: "contenido-presencia",
  },
  christian: {
    slug: "christian",
    name: "Christian",
    role: "Cazador · SDR y outbound",
    colorToken: "agent-christian",
    colorSoftToken: "agent-christian-soft",
    initial: "C",
    thumbnail: "/sb-assets/agents/christian/avatar.svg",
    tabLabel: "Ventas",
    defaultSubtab: "pipeline",
  },
  sara: {
    slug: "sara",
    name: "Sara",
    role: "Jefa de proyectos · operación y delivery",
    colorToken: "agent-sara",
    colorSoftToken: "agent-sara-soft",
    initial: "S",
    thumbnail: "/sb-assets/agents/sara/avatar.svg",
    tabLabel: "Próximamente",
    defaultSubtab: "proximamente",
  },
  norvil: {
    slug: "norvil",
    name: "Norvil",
    role: "Account manager · retención y expansión",
    colorToken: "agent-norvil",
    colorSoftToken: "agent-norvil-soft",
    initial: "N",
    thumbnail: "/sb-assets/agents/norvil/avatar.svg",
    tabLabel: "Cuentas",
    defaultSubtab: "cartera",
  },
};

/**
 * Nicolify brand-injected class resolver — LITERAL switch. Mirrors nicolify's
 * _agent-tw-classes.ts. No contrast exceptions in the ribbon roster (all 6 agent
 * colors clear AA as text on their own -soft bg); luana is the supervisor.
 */
function getNicolifyAgentClasses(slug: string): AgentClassBundle {
  switch (slug) {
    case "abel":
      return {
        accentBg: "bg-agent-abel",
        softBg: "bg-agent-abel-soft",
        accentText: "text-agent-abel",
        accentBorder: "border-agent-abel",
      };
    case "brenda":
      return {
        accentBg: "bg-agent-brenda",
        softBg: "bg-agent-brenda-soft",
        accentText: "text-agent-brenda",
        accentBorder: "border-agent-brenda",
      };
    case "christian":
      return {
        accentBg: "bg-agent-christian",
        softBg: "bg-agent-christian-soft",
        accentText: "text-agent-christian",
        accentBorder: "border-agent-christian",
      };
    case "sara":
      return {
        accentBg: "bg-agent-sara",
        softBg: "bg-agent-sara-soft",
        accentText: "text-agent-sara",
        accentBorder: "border-agent-sara",
      };
    case "norvil":
      return {
        accentBg: "bg-agent-norvil",
        softBg: "bg-agent-norvil-soft",
        accentText: "text-agent-norvil",
        accentBorder: "border-agent-norvil",
      };
    case "luana":
    default:
      return {
        accentBg: "bg-agent-luana",
        softBg: "bg-agent-luana-soft",
        accentText: "text-agent-luana",
        accentBorder: "border-agent-luana",
      };
  }
}

const NICOLIFY_RIBBON_ORDER: string[] = ["abel", "brenda", "christian", "sara", "norvil"];

const NICOLIFY_SUBTABS_BY_AGENT: Record<string, ShellSubTabMeta[]> = {
  abel: [
    { id: "icp", label: "ICP & buyer", icon: "🎯" },
    { id: "oferta", label: "Oferta", icon: "📦" },
    { id: "marca", label: "Marca", icon: "🏷️" },
  ],
  brenda: [
    { id: "contenido-presencia", label: "Contenido & Presencia", icon: "✍️" },
    { id: "pauta", label: "Pauta", icon: "📢" },
    { id: "inteligencia-asesoria", label: "Inteligencia & Asesoría", icon: "🧠" },
  ],
  christian: [
    { id: "contactos", label: "Contactos", icon: "👥" },
    { id: "inbox", label: "Inbox", icon: "📥" },
    { id: "pipeline", label: "Pipeline", icon: "📊" },
    { id: "equipo-comercial", label: "Equipo comercial", icon: "🧑‍💼" },
    { id: "agenda", label: "Agenda", icon: "📅" },
    { id: "propuestas", label: "Propuestas", icon: "📝" },
  ],
  sara: [{ id: "proximamente", label: "Próximamente", icon: "⏳" }],
  norvil: [
    { id: "cartera", label: "Cartera", icon: "🗂️" },
    { id: "renovaciones", label: "Renovaciones", icon: "🔄" },
    { id: "fidelizacion", label: "Fidelización", icon: "💚" },
  ],
};

const NICOLIFY_SUBSUBTABS_BY_KEY: Record<string, ShellSubSubTabMeta[]> = {
  "abel.oferta": [
    { id: "catalogo-escalera", label: "Catálogo & escalera", icon: "📦" },
    { id: "dossier-mineria", label: "Dossier (minería)", icon: "⛏️" },
  ],
  "christian.propuestas": [
    { id: "propuestas", label: "Propuestas", icon: "📝" },
    { id: "licitaciones", label: "Licitaciones", icon: "⛏️" },
  ],
  "norvil.fidelizacion": [
    { id: "momentos", label: "Momentos", icon: "🎂" },
    { id: "champion-shield", label: "Champion-shield", icon: "🛡️" },
    { id: "value-proof-qbr", label: "Value-proof / QBR", icon: "📈" },
    { id: "gifting", label: "Gifting", icon: "🎁" },
  ],
};

/** Nicolify logo (real brand mark, CSS light/dark swap). */
function NicolifyLogo() {
  return (
    <span className="inline-flex items-center" aria-label="Nicolify inicio">
      <img src="/sb-assets/brand/nicolify-logo.svg" alt="" className="block h-8 w-auto dark:hidden" />
      <img src="/sb-assets/brand/nicolify-logo-dark.svg" alt="" className="hidden h-8 w-auto dark:block" />
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
 * Brand registry — the toolbar `brand` global picks the set via getBrandFixtures.
 * ═══════════════════════════════════════════════════════════════════════════ */

function buildSet(
  brand: "vitalia" | "nicolify",
  agents: Record<string, ShellAgentDescriptor>,
  ribbonOrder: string[],
  supervisorSlug: string,
  getAgentClasses: (slug: string) => AgentClassBundle,
  subTabsByAgent: Record<string, ShellSubTabMeta[]>,
  subSubTabsByKey: Record<string, ShellSubSubTabMeta[]>,
  configTabLabel: string,
  Logo: () => ReactNode,
): BrandFixtureSet {
  const agentsRibbon = ribbonOrder.map((slug) => agents[slug]);
  const supervisor = agents[supervisorSlug];
  return {
    brand,
    agentsBySlug: agents,
    agentsRibbon,
    agentsAll: [supervisor, ...agentsRibbon],
    ribbonOrder,
    getAgentClasses,
    subTabsByAgent,
    subSubTabsByKey,
    supervisor,
    configTabLabel,
    Logo,
  };
}

export const BRAND_FIXTURES: Record<"vitalia" | "nicolify", BrandFixtureSet> = {
  vitalia: buildSet(
    "vitalia",
    VITALIA_AGENTS,
    VITALIA_RIBBON_ORDER,
    "valeria",
    getVitaliaAgentClasses,
    VITALIA_SUBTABS_BY_AGENT,
    VITALIA_SUBSUBTABS_BY_KEY,
    "Plataforma",
    VitaliaLogo,
  ),
  nicolify: buildSet(
    "nicolify",
    NICOLIFY_AGENTS,
    NICOLIFY_RIBBON_ORDER,
    "luana",
    getNicolifyAgentClasses,
    NICOLIFY_SUBTABS_BY_AGENT,
    NICOLIFY_SUBSUBTABS_BY_KEY,
    "Configurar",
    NicolifyLogo,
  ),
};

/** Resolve the fixture set for the toolbar `brand` global (default vitalia). */
export function getBrandFixtures(brand: string | undefined): BrandFixtureSet {
  return brand === "nicolify" ? BRAND_FIXTURES.nicolify : BRAND_FIXTURES.vitalia;
}

/**
 * A class resolver covering BOTH brands' slugs — for nav-mock stories (SubTabsBar)
 * whose active agent is pinned by a static navigation param (cannot read globals),
 * so the pinned slug always resolves a valid bundle whichever brand is active. The
 * COLOR still switches with the brand: the token VALUE behind each bg-agent-* class
 * is brand-keyed in preview.css [data-brand].
 */
export function getAnyBrandAgentClasses(slug: string): AgentClassBundle {
  return slug in NICOLIFY_AGENTS || slug === "config"
    ? getNicolifyAgentClasses(slug)
    : getVitaliaAgentClasses(slug);
}

/** Union of both brands' agent descriptors keyed by slug (nav-mock stories). */
export const ALL_AGENTS_BY_SLUG: Record<string, ShellAgentDescriptor> = {
  ...VITALIA_AGENTS,
  ...NICOLIFY_AGENTS,
};

/** Union of both brands' sub-tabs keyed by slug (nav-mock stories). */
export const ALL_SUBTABS_BY_AGENT: Record<string, ShellSubTabMeta[]> = {
  ...VITALIA_SUBTABS_BY_AGENT,
  ...NICOLIFY_SUBTABS_BY_AGENT,
};

/** Union of both brands' N3-static sub-sub-tabs keyed by "agent.subtab" (nav-mock). */
export const ALL_SUBSUBTABS_BY_KEY: Record<string, ShellSubSubTabMeta[]> = {
  ...VITALIA_SUBSUBTABS_BY_KEY,
  ...NICOLIFY_SUBSUBTABS_BY_KEY,
};

/** Union of both brands' agent slugs + config (validSlugs for nav-mock stories). */
export const ALL_VALID_SLUGS: string[] = [
  ...Object.keys(ALL_AGENTS_BY_SLUG),
  "config",
];

/* ── Back-compat exports (vitalia default) ─────────────────────────────────────
 * Stories that don't render brand-aware (or use the vitalia default as meta args)
 * keep importing these. Brand-aware stories read getBrandFixtures(globals.brand).
 */
export const DEMO_AGENTS = VITALIA_AGENTS;
export const getDemoAgentClasses = getVitaliaAgentClasses;
export const DEMO_RIBBON_ORDER = VITALIA_RIBBON_ORDER;
export const DEMO_AGENTS_ARRAY = BRAND_FIXTURES.vitalia.agentsRibbon;
export const DEMO_AGENTS_ALL = BRAND_FIXTURES.vitalia.agentsAll;
export const DEMO_SUBTABS_BY_AGENT = VITALIA_SUBTABS_BY_AGENT;
export const DEMO_SUBSUBTABS_BY_KEY = VITALIA_SUBSUBTABS_BY_KEY;
export const DemoLogo = VitaliaLogo;

/**
 * ★ Build a clean subTabsByAgent Record — keyed ONLY by real slugs.
 *
 * MUST be a function, NOT an exported object: react-docgen-typescript stamps
 * `displayName` + `__docgenInfo` as enumerable props on every exported OBJECT, so
 * an exported Record gets phantom keys → `Object.entries(...)` (which SubTabsBar
 * does) → `tabs.map is not a function`. The caller assigns the RESULT to a local
 * (non-exported) const, which is never stamped.
 */
export function buildCleanSubtabs(
  fixtures: BrandFixtureSet = BRAND_FIXTURES.vitalia,
): Record<string, ShellSubTabMeta[]> {
  return Object.fromEntries(
    fixtures.ribbonOrder.map((slug) => [slug, fixtures.subTabsByAgent[slug]]),
  );
}

/* ── Demo stores (chat sub-tree stories) ───────────────────────────────────────
 *
 * The chat components read injected stores (the kit never imports brand stores).
 * The seeded conversation is BRAND-KEYED (vitalia: agenda/turnos · nicolify: leads/
 * propuestas) so switching the `brand` global flips the chat content + supervisor,
 * not just the CSS. Stories pick the store via getBrandChatStore(globals.brand).
 * The shell store drives ChatHeader's history/collapse buttons (brand-agnostic).
 *
 * ★ We never call useStoreHydration on them → the factory's skipHydration keeps them
 *   at the seed (zero localStorage writes, seed stable on every Storybook load).
 */

/** Demo shell store — drives ChatHeader's history/collapse buttons. */
export const useDemoShellStore = createShellStore({
  storageKey: "sb-demo-shell",
  version: 1,
});

const VITALIA_CONVERSATIONS: ShellConversationMeta[] = [
  { id: "c1", title: "Turnos de hoy", meta: "5 mensajes", group: "today" },
  { id: "c2", title: "Reprogramar control nutrición", meta: "3 mensajes", group: "yesterday" },
  { id: "c3", title: "Campaña blanqueamiento", meta: "8 mensajes", group: "this_week" },
];

/** Vitalia demo conversation (agenda/turnos → delegación Valeria→Mateo). */
const VITALIA_MESSAGES: ShellChatMessage[] = [
  { id: "m1", role: "bot", agent: "valeria", time: "09:14", content: "Buen día. Tienes 3 turnos sin confirmar para hoy." },
  { id: "m2", role: "user", time: "09:15", content: "Confírmalos y avísame si alguno se cae." },
  { id: "m3", role: "delegate", fromAgent: "valeria", toAgent: "mateo", delegateMode: "Atender" },
  { id: "m4", role: "bot", agent: "mateo", time: "09:15", content: "Confirmé 2 de 3. La paciente de las 16:00 pidió reprogramar; te dejé 3 opciones de horario." },
  { id: "m5", role: "thinking", agent: "valeria", content: "Valeria está preparando el resumen del día…" },
];

const NICOLIFY_CONVERSATIONS: ShellConversationMeta[] = [
  { id: "c1", title: "Leads de hoy", meta: "5 mensajes", group: "today" },
  { id: "c2", title: "Reagendar reunión TechCorp", meta: "3 mensajes", group: "yesterday" },
  { id: "c3", title: "Campaña outbound Q3", meta: "8 mensajes", group: "this_week" },
];

/** Nicolify demo conversation (leads/propuestas → delegación Luana→Christian). */
const NICOLIFY_MESSAGES: ShellChatMessage[] = [
  { id: "m1", role: "bot", agent: "luana", time: "09:14", content: "Buen día. Tienes 3 propuestas pendientes de enviar hoy." },
  { id: "m2", role: "user", time: "09:15", content: "Envíalas y avísame si alguna rebota." },
  { id: "m3", role: "delegate", fromAgent: "luana", toAgent: "christian", delegateMode: "Ventas" },
  { id: "m4", role: "bot", agent: "christian", time: "09:15", content: "Envié 2 de 3. El lead de TechCorp pidió reagendar la reunión; te dejé 3 horarios." },
  { id: "m5", role: "thinking", agent: "luana", content: "Luana está preparando el resumen del día…" },
];

function makeDemoChatStore(
  name: string,
  seed: ShellChatMessage[],
  convos: ShellConversationMeta[] = VITALIA_CONVERSATIONS,
  activeAgent = "valeria",
) {
  return createSsrSafePersistedStore<ShellChatStoreApi & SsrSafeHydration>(
    (set, get) => ({
      _hasHydrated: true, // stories treat the store as ready (no useStoreHydration call)
      setHasHydrated: (v) => set({ _hasHydrated: v }),
      messages: seed,
      conversations: convos,
      activeAgent,
      status: "idle",
      sendMessage: (content) =>
        set({
          messages: [
            ...get().messages,
            { id: `u${get().messages.length}`, role: "user", content, time: "ahora" },
          ],
        }),
      clearMessages: () => set({ messages: [] }),
      newConversation: () => set({ messages: [] }),
      setActiveAgent: (activeAgent) => set({ activeAgent }),
    }),
    { name, version: 1, partialize: () => ({}) },
  );
}

/** Seeded demo chat per brand (full conversation) + an empty one (empty state). */
export const useDemoChatStore = makeDemoChatStore("sb-demo-chat", VITALIA_MESSAGES, VITALIA_CONVERSATIONS, "valeria");
export const useDemoChatStoreNicolify = makeDemoChatStore("sb-demo-chat-nicolify", NICOLIFY_MESSAGES, NICOLIFY_CONVERSATIONS, "luana");
export const useDemoChatStoreEmpty = makeDemoChatStore("sb-demo-chat-empty", []);
/** No archived conversations — for the SupervisorHistory empty state (SC-13). */
export const useDemoChatStoreNoConvos = makeDemoChatStore("sb-demo-no-convos", [], []);

/**
 * Pick the brand's seeded demo chat store for the toolbar `brand` global. Returns
 * the store hook (the chat component calls it) — vitalia is the default. Stories
 * that render the seeded conversation use this so the chat content + active agent
 * flip with the brand, matching getBrandFixtures(globals.brand).
 */
export function getBrandChatStore(brand: string | undefined) {
  return brand === "nicolify" ? useDemoChatStoreNicolify : useDemoChatStore;
}
