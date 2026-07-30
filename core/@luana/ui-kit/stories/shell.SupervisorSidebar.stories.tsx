import type { Meta, StoryObj } from "@storybook/nextjs";

import {
  ChatPanel,
  SupervisorSidebar,
  createShellStore,
  type ShellStore,
  type SupervisorSidebarLabels,
  type ShellTestIds,
} from "../src";
import {
  getBrandFixtures,
  getBrandChatStore,
  type BrandFixtureSet,
} from "./_shell-fixtures";

/**
 * Story consumes the REAL SupervisorSidebar from src/ — the supervisor side of
 * the shell. It composes THREE real layouts driven by the injected shell store:
 *   A=strip (supervisorOpen "closed") · B=chat · C=chat+history (historyOpen true).
 *
 * ★ SupervisorSidebar does NOT call useStoreHydration (only ShellLayoutClient
 *   does). So we seed each state by creating a fresh store + setState at module
 *   scope: the value sticks deterministically and never reads/writes localStorage
 *   (the @luana/hooks store NO-OPs persistence until hydrated). One store per
 *   state → zero bleed across stories.
 *
 * ★ The aside is `hidden lg:grid` → it only paints at viewport ≥1024. The smoke
 *   runs at 1280 (playwright default) so it renders; screenshot at ≥1024 too.
 */

// ── Per-state seeded stores (clean: no hydration → setState sticks) ─────────────
const useShellClosed = createShellStore({ storageKey: "sb-sidebar-closed", version: 1 });
useShellClosed.setState({ supervisorOpen: "closed", historyOpen: false });

const useShellChat = createShellStore({ storageKey: "sb-sidebar-chat", version: 1 });
useShellChat.setState({ supervisorOpen: "chat", historyOpen: false });

const useShellHistory = createShellStore({ storageKey: "sb-sidebar-history", version: 1 });
useShellHistory.setState({ supervisorOpen: "chat", historyOpen: true });

const useShellMobile = createShellStore({ storageKey: "sb-sidebar-mobile", version: 1 });
useShellMobile.setState({ supervisorOpen: "chat", historyOpen: false, mobileDrawerOpen: true });

// ── Shared brand-injected props ────────────────────────────────────────────────
/** Build supervisor sidebar labels for the active brand's supervisor name. */
function labelsFor(f: BrandFixtureSet): SupervisorSidebarLabels {
  const n = f.supervisor.name;
  return {
    panel: n,
    drawerClose: `Cerrar ${n}`,
    liveHistory: "Historial abierto",
    liveClosed: `${n} cerrado`,
    liveOpen: `${n} abierto`,
    openStrip: `Abrir a ${n}`,
    history: {},
  };
}

const TEST_IDS: ShellTestIds = {
  supervisorSidebar: "supervisor-sidebar",
  supervisorCollapsedStrip: "supervisor-strip",
  supervisorStripStatusDot: "supervisor-strip-dot",
};

/** Brand-configured chat panel (states B + C) bound to a given shell store. */
function makeChatSlot(useShellStore: ShellStore, f: BrandFixtureSet) {
  return (
    <ChatPanel
      supervisor={f.supervisor}
      agentCatalog={f.agentsBySlug}
      useShellStore={useShellStore}
      useChatStore={getBrandChatStore(f.brand)}
      getAgentClasses={f.getAgentClasses}
      userBubbleBgClass={f.getAgentClasses(f.supervisor.slug).accentBg}
      statusDotClass="bg-emerald-500"
      testIds={TEST_IDS}
    />
  );
}

/** Render a SupervisorSidebar state bound to a seeded shell store, brand-aware. */
function renderSidebar(useShellStore: ShellStore): Story["render"] {
  return function SidebarRender(_args, { globals }) {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <SupervisorSidebar
        supervisorSlug={f.supervisor.slug}
        supervisorName={f.supervisor.name}
        supervisorInitial={f.supervisor.initial}
        getAgentClasses={f.getAgentClasses}
        useChatStore={getBrandChatStore(f.brand)}
        labels={labelsFor(f)}
        testIds={TEST_IDS}
        statusDotClass="bg-emerald-500"
        useShellStore={useShellStore}
        chatSlot={makeChatSlot(useShellStore, f)}
      />
    );
  };
}

const meta = {
  title: "Shell/SupervisorSidebar",
  component: SupervisorSidebar,
  decorators: [
    (Story) => (
      <div className="h-[620px] w-full overflow-hidden border border-border bg-background">
        <Story />
      </div>
    ),
  ],
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`SupervisorSidebar` es el **lado del supervisor del shell** (la cara de Valeria). Es una máquina binaria de 3 layouts reales: **tira-avatar** (cerrado, ~44px), **chat** (abierto) e **historial + chat** (cuando se abre el historial). La marca le inyecta identidad + stores + clases + copy + testids (cero nombres de marca en el kit). El chat en sí entra como `chatSlot` (un `ChatPanel`), así el sidebar solo posee la tira/historial/drawer.",
          "",
          "Casi nunca lo montas suelto: vive dentro de `ShellLayout`, en el panel izquierdo redimensionable. Esta story existe para revisar los 3 estados + el drawer móvil en aislamiento. Necesita viewport ≥1024 (es `hidden lg:grid`).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **El shell completo** (ribbon + sub-tabs + panel de app + este supervisor) → `ShellLayout`, que lo monta + maneja el split resizable.",
          "- **Solo el chat** → `ChatPanel`. **Solo la tira/el historial** → `SupervisorCollapsedStrip` / `SupervisorHistory`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof SupervisorSidebar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Cerrado: Story = {
  name: "A — Cerrado (tira-avatar)",
  render: renderSidebar(useShellClosed),
};

export const Chat: Story = {
  name: "B — Chat",
  render: renderSidebar(useShellChat),
};

export const Historial: Story = {
  name: "C — Historial + chat",
  render: renderSidebar(useShellHistory),
};

export const DrawerMovil: Story = {
  name: "Drawer móvil (viewport <1024)",
  render: renderSidebar(useShellMobile),
  // El drawer solo monta con isMobile (matchMedia max-width:1023) + mobileDrawerOpen.
  // El viewport global achica el iframe → isMobile true. En el smoke (1280) renderiza
  // el aside desktop sin crashear; en el viewport tool / resize se ve el drawer (portal).
  globals: { viewport: { value: "mobile" } },
};
