import type { Meta, StoryObj } from "@storybook/nextjs";

import { ChatPanel } from "../src";
import {
  getBrandFixtures,
  getBrandChatStore,
  useDemoShellStore,
  useDemoChatStoreEmpty,
} from "./_shell-fixtures";

/**
 * Story consumes the REAL ChatPanel from src/ — the composite chat organism
 * (ChatHeader + ChatMessages + ChatComposer in a 3-row grid). The wrapper gives
 * it the supervisor-panel height; ChatPanel fills it (h-full). Supervisor identity
 * + accent follow the toolbar `Marca` global (Valeria/Luana).
 */
const meta = {
  title: "Shell/Chat/ChatPanel",
  component: ChatPanel,
  args: {
    useShellStore: useDemoShellStore,
    statusDotClass: "bg-emerald-500",
  },
  decorators: [
    (Story) => (
      <div className="h-[600px] w-[400px] overflow-hidden rounded-xl border border-border shadow-sm">
        <Story />
      </div>
    ),
  ],
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`ChatPanel` es el **organismo de chat completo** (ex-ValeriaChat): compone `ChatHeader` + `ChatMessages` + `ChatComposer` en una grilla de 3 filas. Es lo que vive en el panel del supervisor del shell — la cara conversacional de Valeria (o de un especialista). La marca le inyecta el catálogo de agentes + los stores; el kit no conoce ningún nombre de marca.",
          "",
          "Úsalo cuando necesites el chat entero. El padre debe darle altura (`h-full` o altura fija); el panel se encarga del layout interno (header fijo arriba, mensajes scrolleables al medio, composer fijo abajo).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Solo una parte** (cabecera, lista o composer) → usa el sub-componente (`ChatHeader` / `ChatMessages` / `ChatComposer`).",
          "- **El shell completo** (ribbon + sub-tabs + panel de app + este chat) → `ShellLayout`, que monta `ChatPanel` dentro del lado del supervisor.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof ChatPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ConConversacion: Story = {
  name: "Con conversación",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <ChatPanel
        supervisor={f.supervisor}
        agentCatalog={f.agentsBySlug}
        useShellStore={useDemoShellStore}
        useChatStore={getBrandChatStore(globals.brand as string | undefined)}
        getAgentClasses={f.getAgentClasses}
        userBubbleBgClass={f.getAgentClasses(f.supervisor.slug).accentBg}
        statusDotClass="bg-emerald-500"
      />
    );
  },
};

export const Vacio: Story = {
  name: "Conversación nueva (vacío)",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <ChatPanel
        supervisor={f.supervisor}
        agentCatalog={f.agentsBySlug}
        useShellStore={useDemoShellStore}
        useChatStore={useDemoChatStoreEmpty}
        getAgentClasses={f.getAgentClasses}
        userBubbleBgClass={f.getAgentClasses(f.supervisor.slug).accentBg}
        statusDotClass="bg-emerald-500"
      />
    );
  },
};
