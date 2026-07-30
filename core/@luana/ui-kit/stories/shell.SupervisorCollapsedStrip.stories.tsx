import type { Meta, StoryObj } from "@storybook/nextjs";

import { SupervisorCollapsedStrip } from "../src";
import { getBrandFixtures } from "./_shell-fixtures";

/**
 * Story consumes the REAL SupervisorCollapsedStrip from src/. Pure-props — the
 * ~44px vertical tira-avatar shown at the left edge when the supervisor is
 * collapsed (state A). Click reopens to chat. The supervisor identity + soft color
 * follow the toolbar `Marca` global (Valeria · Vitalia / Luana · Nicolify).
 */
const meta = {
  title: "Shell/SupervisorCollapsedStrip",
  component: SupervisorCollapsedStrip,
  decorators: [
    (Story) => (
      <div className="flex h-[420px] items-stretch overflow-hidden rounded-lg border border-border bg-background">
        <Story />
        <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
          Panel del agente (toma el ancho cuando el supervisor está colapsado)
        </div>
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
          "Es el **estado colapsado del supervisor** (Valeria): una tira vertical de ~44px contra el borde izquierdo con el avatar + punto de estado + nombre rotado. Cede el ancho al panel del agente; un clic reabre el chat. Lo orquesta `SupervisorSidebar` cuando `supervisorOpen = \"closed\"`.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Supervisor abierto (chat)** → `ChatPanel` dentro de `SupervisorSidebar`.",
          "- **No** lo montes suelto en producción — es un estado interno del `SupervisorSidebar`; esta story lo aísla para revisión.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof SupervisorCollapsedStrip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Colapsado: Story = {
  name: "Colapsado",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <SupervisorCollapsedStrip
        onOpenSupervisor={() => {}}
        supervisorName={f.supervisor.name}
        supervisorInitial={f.supervisor.initial}
        supervisorSoftBg={f.getAgentClasses(f.supervisor.slug).softBg}
        statusDotClass="bg-emerald-500"
        openLabel={`Abrir a ${f.supervisor.name}`}
      />
    );
  },
};
