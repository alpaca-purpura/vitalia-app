import type { Meta, StoryObj } from "@storybook/nextjs";

import { TypingIndicator } from "../src";
import { getBrandFixtures } from "./_shell-fixtures";

/**
 * Story consumes the REAL TypingIndicator from src/. The animated dots use the
 * `.typing-dot` keyframe defined in .storybook/preview.css (a brand ships it in
 * globals.css). Agent soft-bg + accent come from getAgentClasses — both follow the
 * brand picked by the toolbar `Marca` global (supervisor + ribbon agents flip).
 */
const meta = {
  title: "Shell/Chat/TypingIndicator",
  component: TypingIndicator,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`TypingIndicator` es la burbuja **viva** que muestra que un agente está trabajando: \"escribiendo…\" o, mejor, **qué acción está ejerciendo** (\"está abriendo Voz del paciente\"). Toma el **color soft del agente** como fondo y anima tres puntos. Da feedback inmediato mientras el turno corre.",
          "",
          "Por defecto el texto es `{Nombre} está escribiendo…`; pasa `text` para describir la acción concreta (más honesto que un genérico \"escribiendo\").",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Ya hay respuesta** → `MessageBubble role=\"bot\"`.",
          "- **Handoff a otro agente** → `DelegateMarker`.",
          "- **Carga de una pantalla/sección entera** (no un turno de chat) → usa un `Skeleton` / estado de carga de la hoja, no esta burbuja.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof TypingIndicator>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Escribiendo: Story = {
  name: "Supervisor escribiendo",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return <TypingIndicator agent={f.supervisor} getAgentClasses={f.getAgentClasses} />;
  },
};

export const AccionConcreta: Story = {
  name: "Acción concreta (primer especialista)",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    const agent = f.agentsRibbon[0];
    return (
      <TypingIndicator
        agent={agent}
        getAgentClasses={f.getAgentClasses}
        text={`${agent.name} está preparando tu tablero…`}
      />
    );
  },
};

export const VariosAgentes: Story = {
  name: "Color por agente",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <div className="flex flex-col gap-2.5 max-w-md">
        <TypingIndicator agent={f.supervisor} getAgentClasses={f.getAgentClasses} />
        <TypingIndicator agent={f.agentsRibbon[0]} getAgentClasses={f.getAgentClasses} />
        <TypingIndicator
          agent={f.agentsRibbon[2]}
          getAgentClasses={f.getAgentClasses}
          text={`${f.agentsRibbon[2].name} está revisando los leads nuevos…`}
        />
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: "El fondo soft cambia con el agente que trabaja — la persona reconoce quién está actuando sin leer el nombre.",
      },
    },
  },
};
