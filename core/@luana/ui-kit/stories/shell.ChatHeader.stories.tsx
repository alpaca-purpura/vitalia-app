import type { Meta, StoryObj } from "@storybook/nextjs";

import { ChatHeader } from "../src";
import {
  getBrandFixtures,
  getBrandChatStore,
  useDemoShellStore,
  useDemoChatStore,
} from "./_shell-fixtures";

/**
 * Story consumes the REAL ChatHeader from src/. It reads injected stores
 * (shell: history/collapse · chat: newConversation). The mode pill uses a
 * container query (@[24rem]) → the wrapper is @container ≥ 24rem so it shows.
 * The agent (supervisor/specialist) + color follow the toolbar `Marca` global.
 */
const meta = {
  title: "Shell/Chat/ChatHeader",
  component: ChatHeader,
  args: {
    useShellStore: useDemoShellStore,
    useChatStore: useDemoChatStore,
  },
  decorators: [
    (Story) => (
      <div className="@container w-[400px] rounded-lg border border-border bg-background">
        <Story />
      </div>
    ),
  ],
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`ChatHeader` es la cabecera del panel de chat del supervisor/especialista: avatar con color del agente + punto de estado, nombre y rol, **píldora de modo** (🤖 agente / 🌐 web) y los controles del hilo — nueva conversación, mostrar/ocultar historial, colapsar el supervisor.",
          "",
          "Va siempre como fila superior de `ChatPanel` (no se monta suelto en producción). La píldora de modo aparece por **container query** (ancho del panel ≥ 24rem), no por viewport — se oculta sola cuando el panel se angosta.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Cabecera de una hoja de contenido** (no chat) → `PageHeader`.",
          "- **No** la montes fuera de un contenedor con altura/ancho del panel: depende del `@container` para la píldora.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof ChatHeader>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ModoAgente: Story = {
  name: "Modo agente (supervisor, en línea)",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <ChatHeader
        useShellStore={useDemoShellStore}
        useChatStore={getBrandChatStore(globals.brand as string | undefined)}
        getAgentClasses={f.getAgentClasses}
        agent={f.supervisor}
        status="online"
        mode="agent"
      />
    );
  },
};

export const ModoWeb: Story = {
  name: "Modo web",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <ChatHeader
        useShellStore={useDemoShellStore}
        useChatStore={getBrandChatStore(globals.brand as string | undefined)}
        getAgentClasses={f.getAgentClasses}
        agent={f.supervisor}
        status="online"
        mode="web"
      />
    );
  },
};

export const Especialista: Story = {
  name: "Especialista (primer ribbon)",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <ChatHeader
        useShellStore={useDemoShellStore}
        useChatStore={getBrandChatStore(globals.brand as string | undefined)}
        getAgentClasses={f.getAgentClasses}
        agent={f.agentsRibbon[0]}
        status="online"
        mode="agent"
      />
    );
  },
};
