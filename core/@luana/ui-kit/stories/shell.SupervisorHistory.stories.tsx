import type { Meta, StoryObj } from "@storybook/nextjs";

import { SupervisorHistory } from "../src";
import {
  getBrandFixtures,
  getBrandChatStore,
  useDemoChatStoreNoConvos,
} from "./_shell-fixtures";

/**
 * Story consumes the REAL SupervisorHistory from src/. It reads `conversations`
 * from the injected chat store and groups them (Hoy / Ayer / Esta semana) with
 * search. Composes HistoryGroup + HistoryItem + EmptyStateInline. The active-row
 * highlight uses the supervisor's soft color, which follows the `Marca` global.
 */
const meta = {
  title: "Shell/SupervisorHistory",
  component: SupervisorHistory,
  args: {
    onNewConversation: () => {},
    onCollapseToRail: () => {},
  },
  decorators: [
    (Story) => (
      <div className="flex h-[480px] overflow-hidden rounded-lg border border-border bg-card">
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
          "El `SupervisorHistory` es el panel de **historial de conversaciones** del supervisor (estado C, franja de 260px que empuja al chat). Busca por título, agrupa por tiempo (Hoy / Ayer / Esta semana) y resalta la fila activa con el color soft del supervisor. Toma las conversaciones del store de chat (archivo UI-local). Lo orquesta `SupervisorSidebar` cuando `historyOpen = true`.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **El hilo activo** (mensajes) → `ChatMessages`.",
          "- **Un listado de entidades de negocio** (no conversaciones) → `EntityWorkspaceLayout`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof SupervisorHistory>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ConConversaciones: Story = {
  name: "Con conversaciones",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <SupervisorHistory
        onNewConversation={() => {}}
        onCollapseToRail={() => {}}
        activeClass={f.getAgentClasses(f.supervisor.slug).softBg}
        useChatStore={getBrandChatStore(globals.brand as string | undefined)}
      />
    );
  },
};

export const Vacio: Story = {
  name: "Sin conversaciones (vacío)",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <SupervisorHistory
        onNewConversation={() => {}}
        onCollapseToRail={() => {}}
        activeClass={f.getAgentClasses(f.supervisor.slug).softBg}
        useChatStore={useDemoChatStoreNoConvos}
      />
    );
  },
};
