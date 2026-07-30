import type { Meta, StoryObj } from "@storybook/nextjs";

import { DelegateMarker } from "../src";
import { getBrandFixtures } from "./_shell-fixtures";

/**
 * Story consumes the REAL DelegateMarker from src/. Brand injects the agent
 * descriptors + getAgentClasses (literal-switch, see _shell-fixtures). Supervisor
 * + the receiving specialist (name, color, avatar) follow the toolbar `Marca` global.
 */
const meta = {
  title: "Shell/Chat/DelegateMarker",
  component: DelegateMarker,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`DelegateMarker` es el marcador en línea del chat que muestra un **handoff entre trabajadores**: la supervisora (Valeria) delega la acción en un especialista. Materializa el invariante del paradigma — *los trabajadores orquestan, no reimplementan*: cuando algo cae fuera del scope de Valeria, ella delega y se ve en el hilo, con el **color y el avatar del agente que recibe**.",
          "",
          "Renderiza centrado, en cursiva: `→ delegando a [avatar] Nombre (modo {mode})`. El `mode` refleja la primitiva de delegación (`Mantener` / `Reactivar` / `Multiplicar`).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Mensaje normal del especialista** ya activo → `MessageBubble role=\"bot\"` (con `footerLabel` \"Especialista (vía Valeria)\" si quieres marcar el origen).",
          "- **Agente trabajando/abriendo una herramienta** → `TypingIndicator`.",
          "- **No** lo uses como botón de acción: es un marcador informativo del hilo, no un control.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof DelegateMarker>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Mantener: Story = {
  name: "Delega en el primer especialista (Mantener)",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <DelegateMarker
        fromAgent={f.supervisor}
        toAgent={f.agentsRibbon[0]}
        mode="Mantener"
        getAgentClasses={f.getAgentClasses}
      />
    );
  },
};

export const Multiplicar: Story = {
  name: "Delega en el último especialista (Multiplicar)",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <DelegateMarker
        fromAgent={f.supervisor}
        toAgent={f.agentsRibbon[f.agentsRibbon.length - 1]}
        mode="Multiplicar"
        getAgentClasses={f.getAgentClasses}
      />
    );
  },
};

export const EnHilo: Story = {
  name: "En el hilo (entre burbujas)",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <div className="flex flex-col gap-2.5 max-w-md">
        <DelegateMarker
          fromAgent={f.supervisor}
          toAgent={f.agentsRibbon[0]}
          mode="Mantener"
          getAgentClasses={f.getAgentClasses}
        />
        <DelegateMarker
          fromAgent={f.supervisor}
          toAgent={f.agentsRibbon[2]}
          mode="Reactivar"
          getAgentClasses={f.getAgentClasses}
        />
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: "Cómo se ven varios handoffs intercalados en una conversación. Cada uno toma el color del agente receptor.",
      },
    },
  },
};
