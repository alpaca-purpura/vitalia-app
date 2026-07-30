import type { Meta, StoryObj } from "@storybook/nextjs";

import { StatusDot } from "../src";

/**
 * Story consumes the REAL StatusDot from src/. Pure presentational atom — a
 * small semantic color dot (green/yellow/gray). Brand-agnostic by construction.
 */
const meta = {
  title: "Shell/StatusDot",
  component: StatusDot,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`StatusDot` es el **punto de estado** semántico: verde (en línea / OK), amarillo (atención), gris (inactivo). Úsalo junto a un avatar de agente, en una tarjeta de estado o en una fila de lista. Colores semánticos fijos (no cambian con el agente — canon §2.8).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Etiqueta de estado con texto** → `Badge` (variante semántica).",
          "- **Color de un agente** → usa el token del agente, no este punto (es semántico, no de marca).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof StatusDot>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Verde: Story = { args: { variant: "green", label: "En línea" } };
export const Amarillo: Story = { args: { variant: "yellow", label: "Atención" } };
export const Gris: Story = { args: { variant: "gray", label: "Inactivo" } };

export const Todos: Story = {
  name: "Las 3 variantes",
  render: () => (
    <div className="flex items-center gap-6 text-sm text-muted-foreground">
      <span className="flex items-center gap-2"><StatusDot variant="green" /> En línea</span>
      <span className="flex items-center gap-2"><StatusDot variant="yellow" /> Atención</span>
      <span className="flex items-center gap-2"><StatusDot variant="gray" /> Inactivo</span>
    </div>
  ),
};
