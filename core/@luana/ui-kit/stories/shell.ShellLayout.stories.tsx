import { useEffect } from "react";
import type { ReactNode } from "react";
import type { Decorator, Meta, StoryObj } from "@storybook/nextjs";

import {
  ShellLayout,
  PlaceholderCard,
  createShellStore,
  type ShellStore,
  type ShellStoreState,
  type ShellTestIds,
} from "../src";
import {
  buildCleanSubtabs,
  getBrandFixtures,
  getBrandChatStore,
  type BrandFixtureSet,
} from "./_shell-fixtures";

/**
 * Story consumes the REAL ShellLayout from src/ — the full composite: TopBar +
 * resizable split (SupervisorSidebar | AppPanelSlot) with Ribbon (N1) + SubTabsBar
 * (N2) + SubSubTabsBar (N3) + the agent's leaf content. Everything the brand wires
 * by prop flows in here (catalog, stores, classes, slots, routing).
 *
 * ★ ShellLayout is next/dynamic ssr:false. @storybook/nextjs mounts it client-side.
 *   Its children (AppPanelSlot → Ribbon/SubTabsBar/SubSubTabsBar) read
 *   usePathname()/useRouter() → each story sets parameters.nextjs.navigation
 *   (the `pathname` prop is required by the type but the chrome derives the active
 *   agent from the navigation hook). Different pathname ⇒ different agent color.
 *
 * ★ The brand catalog/colors/avatars/logo/supervisor flip with the toolbar `Marca`
 *   global (vitalia ↔ nicolify) via getBrandFixtures(globals.brand) in each render.
 *   The ACTIVE highlight is pinned by parameters.nextjs.navigation (static — can't read
 *   globals), so each brand has its own pinned stories. subTabsByAgent is rebuilt CLEAN
 *   (buildCleanSubtabs) — SubTabsBar does Object.entries and react-docgen-typescript
 *   stamps phantom enumerable props on raw fixture objects.
 *
 * ★ Store states: ShellLayoutClient calls useStoreHydration once on mount → merge()
 *   clobbers the injected store to {supervisorOpen:"chat", historyOpen:false}. The
 *   default/per-agent stories ARE state B, so they need no seeding. The closed (A)
 *   and history (C) states are re-applied AFTER hydration via a requestAnimationFrame
 *   decorator (a module-scope setState would be erased by the hydrate merge). The
 *   closed story uses its OWN store key so its persisted "closed" never bleeds into
 *   the default story.
 */

// Default/per-agent/history share one chat-based store (history not persisted).
const useShellDemo = createShellStore({ storageKey: "sb-shell-demo", version: 1 });
// Closed needs its OWN key — it persists supervisorOpen:"closed".
const useShellDemoClosed = createShellStore({ storageKey: "sb-shell-demo-closed", version: 1 });
// Mobile drawer: own key — persists mobileDrawerOpen:true.
const useShellDemoMobile = createShellStore({ storageKey: "sb-shell-demo-mobile", version: 1 });

/** Re-apply a demo state on the frame AFTER ShellLayoutClient's hydrate merge. */
function seedAfterHydrate(store: ShellStore, patch: Partial<ShellStoreState>): Decorator {
  return function SeedDecorator(Story) {
    useEffect(() => {
      const id = requestAnimationFrame(() => store.setState(patch));
      return () => cancelAnimationFrame(id);
    }, []);
    return <Story />;
  };
}

function rightClusterFor(f: BrandFixtureSet): ReactNode {
  const tenant = f.brand === "nicolify" ? "agencia-demo ▾" : "clinica-demo ▾";
  return (
    <div className="flex items-center gap-2">
      <button type="button" className="rounded-md px-2 py-1 text-xs hover:bg-muted">
        Tema
      </button>
      <button type="button" className="rounded-md border border-border px-2 py-1 text-xs">
        {tenant}
      </button>
    </div>
  );
}

const TEST_IDS: ShellTestIds = {
  supervisorSidebar: "supervisor-sidebar",
  supervisorCollapsedStrip: "supervisor-strip",
  chat: "supervisor-chat",
  chatHeader: "chat-header",
};

/** Demo leaf content — the agent's page below the nav bars. */
const DemoContent = () => (
  <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2 xl:grid-cols-3">
    <PlaceholderCard icon="📅" title="Pendientes de hoy" description="3 sin atender" count={3} />
    <PlaceholderCard icon="🎟️" title="En curso" description="Esta semana" count={12} status="yellow" />
    <PlaceholderCard icon="🧲" title="Leads" description="Nuevos del embudo" count={5} />
  </div>
);

/** Build a brand-aware ShellLayout render (catalog/colors/logo/supervisor flip). */
function renderShell(opts: {
  pathname: string;
  splitGroupId: string;
  useShellStore?: ShellStore;
}): Story["render"] {
  const useStore = opts.useShellStore ?? useShellDemo;
  return function ShellRender(_args, { globals }) {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <ShellLayout
        pathname={opts.pathname}
        supervisorName={f.supervisor.name}
        supervisorSlug={f.supervisor.slug}
        supervisorInitial={f.supervisor.initial}
        agentCatalog={f.agentsAll}
        ribbonOrder={f.ribbonOrder}
        subTabsByAgent={buildCleanSubtabs(f)}
        subSubTabsByKey={f.subSubTabsByKey}
        getAgentClasses={f.getAgentClasses}
        useShellStore={useStore}
        useChatStore={getBrandChatStore(f.brand)}
        splitGroupId={opts.splitGroupId}
        logoSlot={<f.Logo />}
        rightClusterSlot={rightClusterFor(f)}
        testIds={TEST_IDS}
        configTabSlug="config"
        configTabLabel={f.configTabLabel}
        statusDotClass="bg-emerald-500"
      >
        <DemoContent />
      </ShellLayout>
    );
  };
}

const meta = {
  title: "Shell/ShellLayout",
  component: ShellLayout,
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`ShellLayout` es **el shell completo** — el caparazón de toda la app de marca. Compone el `TopBarShell` arriba y, debajo, un split redimensionable: el `SupervisorSidebar` (el supervisor: Valeria en Vitalia / Luana en Nicolify) a la izquierda y el `AppPanelSlot` (Ribbon N1 + SubTabsBar N2 + SubSubTabsBar N3 + la hoja del agente) a la derecha. La marca inyecta TODO por prop: catálogo de agentes, stores, `getAgentClasses`, slots de logo/tema/tenant, copy, testids y el `pathname`. El kit no conoce ningún nombre de marca — el selector **Marca** de la toolbar cambia el roster, los colores y el logo.",
          "",
          "Úsalo una sola vez, como layout raíz del route-group autenticado. El color del agente activo se deriva de la URL (cada tab toma su color). Es la integración final — todos los componentes Shell/* viven adentro.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Una pieza suelta** → su componente (`SupervisorSidebar`, `AppPanelSlot`, `ChatPanel`, `Ribbon`, …).",
          "- **Una hoja dentro del shell** (lista/detalle) → `EntityWorkspaceLayout` / page-primitives, que se montan como `children`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof ShellLayout>;

export default meta;
type Story = StoryObj<typeof meta>;

// ★ distinct splitGroupId per story: useDefaultLayout persists the split width by this
// key, and a shared key would let one story's wider split bleed into another.
// The active highlight is pinned by nextjs.navigation per story (static). The vitalia
// stories pin a vitalia slug; the nicolify story pins a nicolify slug. The ROSTER /
// colors / logo / supervisor flip with the Marca global in renderShell.

export const Default: Story = {
  name: "Mateo · Agenda (landing default · vitalia)",
  render: renderShell({ pathname: "/clinica/mateo/agenda", splitGroupId: "sb-shell-default" }),
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/mateo/agenda",
        segments: [["tenantId", "clinica"], "mateo", "agenda"],
      },
    },
  },
};

export const LisaActiva: Story = {
  name: "Lisa activa (color + N3 · vitalia)",
  render: renderShell({ pathname: "/clinica/lisa/marca/identidad", splitGroupId: "sb-shell-lisa" }),
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/lisa/marca/identidad",
        segments: [["tenantId", "clinica"], "lisa", "marca", "identidad"],
      },
    },
  },
};

export const AdrianActivo: Story = {
  name: "Adrián · Inbox (color cian · vitalia)",
  render: renderShell({ pathname: "/clinica/adrian/inbox", splitGroupId: "sb-shell-adrian" }),
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/adrian/inbox",
        segments: [["tenantId", "clinica"], "adrian", "inbox"],
      },
    },
  },
};

export const LucasActivo: Story = {
  name: "Lucas · Lanzar (color negro · vitalia)",
  render: renderShell({ pathname: "/clinica/lucas/lanzar", splitGroupId: "sb-shell-lucas" }),
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/lucas/lanzar",
        segments: [["tenantId", "clinica"], "lucas", "lanzar"],
      },
    },
  },
};

export const CamilaActiva: Story = {
  name: "Camila · Voz del paciente (color azul marino · vitalia)",
  render: renderShell({ pathname: "/clinica/camila/voz", splitGroupId: "sb-shell-camila" }),
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/camila/voz",
        segments: [["tenantId", "clinica"], "camila", "voz"],
      },
    },
  },
};

export const ChristianNicolify: Story = {
  name: "Christian · Pipeline (nicolify — switch Marca a nicolify)",
  render: renderShell({ pathname: "/agencia/christian/pipeline", splitGroupId: "sb-shell-christian" }),
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/agencia/christian/pipeline",
        segments: [["tenantId", "agencia"], "christian", "pipeline"],
      },
    },
  },
};

export const SupervisorCerrado: Story = {
  name: "Supervisor cerrado (tira-avatar)",
  render: renderShell({
    pathname: "/clinica/mateo/agenda",
    splitGroupId: "sb-shell-cerrado",
    useShellStore: useShellDemoClosed,
  }),
  decorators: [seedAfterHydrate(useShellDemoClosed, { supervisorOpen: "closed", historyOpen: false })],
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/mateo/agenda",
        segments: [["tenantId", "clinica"], "mateo", "agenda"],
      },
    },
  },
};

export const ChatConHistorial: Story = {
  name: "Chat + historial",
  render: renderShell({ pathname: "/clinica/mateo/agenda", splitGroupId: "sb-shell-historial" }),
  decorators: [seedAfterHydrate(useShellDemo, { supervisorOpen: "chat", historyOpen: true })],
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/mateo/agenda",
        segments: [["tenantId", "clinica"], "mateo", "agenda"],
      },
    },
  },
};

/* ── Responsive (<1024) ──────────────────────────────────────────────────────────
 * Below lg the supervisor leaves the inline split (panel collapses to 0) and becomes
 * a drawer; the app panel takes the full width. The breakpoint is window.matchMedia,
 * so these stories set the viewport global (resizes the iframe). In the headless
 * render-smoke (fixed 1280) they render the desktop layout without crashing; open them
 * in the viewport tool — or resize — to see the responsive shell.
 */
export const Tablet: Story = {
  name: "Tablet (834 · supervisor → drawer)",
  render: renderShell({ pathname: "/clinica/mateo/agenda", splitGroupId: "sb-shell-tablet" }),
  globals: { viewport: { value: "tablet" } },
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/mateo/agenda",
        segments: [["tenantId", "clinica"], "mateo", "agenda"],
      },
    },
  },
};

export const Movil: Story = {
  name: "Móvil (390 · app a pantalla completa)",
  render: renderShell({ pathname: "/clinica/mateo/agenda", splitGroupId: "sb-shell-movil" }),
  globals: { viewport: { value: "mobile" } },
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/mateo/agenda",
        segments: [["tenantId", "clinica"], "mateo", "agenda"],
      },
    },
  },
};

export const MovilDrawerAbierto: Story = {
  name: "Móvil · drawer del supervisor abierto",
  render: renderShell({
    pathname: "/clinica/mateo/agenda",
    splitGroupId: "sb-shell-movil-drawer",
    useShellStore: useShellDemoMobile,
  }),
  globals: { viewport: { value: "mobile" } },
  // Drawer monta sólo con isMobile (matchMedia <1024) + mobileDrawerOpen. Seed
  // post-hydrate (la persistencia lo pisa a false en mount).
  decorators: [seedAfterHydrate(useShellDemoMobile, { mobileDrawerOpen: true })],
  parameters: {
    nextjs: {
      navigation: {
        pathname: "/clinica/mateo/agenda",
        segments: [["tenantId", "clinica"], "mateo", "agenda"],
      },
    },
  },
};
