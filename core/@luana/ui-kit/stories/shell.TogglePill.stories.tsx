import type { Meta, StoryObj } from "@storybook/nextjs";

import { TogglePill, TogglePillContent } from "../src";

/**
 * Story consumes the REAL TogglePill from src/ — a pill-styled tab switcher over
 * Shadcn Tabs. Brand-agnostic. Children are TogglePillContent panels.
 */
const meta = {
  title: "Shell/TogglePill",
  component: TogglePill,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`TogglePill` es un **conmutador en forma de píldora** (sobre Shadcn Tabs) para alternar vistas equivalentes de un mismo contenido: Día / Semana / Mes, o un filtro de rango. Compacto, se ajusta al contenido. Es el átomo canónico que reemplaza los `.toggle-pill` / `.segmented` sueltos.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Sub-secciones del shell** → `SubTabsBar` (N2) / `SubSubTabsBar` (N3), no este pill.",
          "- **Elegir un valor de una lista larga** → `Select` canónico.",
          "- **On/off de una preferencia** → `Switch`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof TogglePill>;

export default meta;
type Story = StoryObj<typeof meta>;

export const RangoDeFecha: Story = {
  name: "Día / Semana / Mes",
  render: () => (
    <TogglePill
      defaultValue="semana"
      items={[
        { value: "dia", label: "Día" },
        { value: "semana", label: "Semana" },
        { value: "mes", label: "Mes" },
      ]}
    >
      <TogglePillContent value="dia" className="pt-3 text-sm text-muted-foreground">
        Vista por día.
      </TogglePillContent>
      <TogglePillContent value="semana" className="pt-3 text-sm text-muted-foreground">
        Vista por semana.
      </TogglePillContent>
      <TogglePillContent value="mes" className="pt-3 text-sm text-muted-foreground">
        Vista por mes.
      </TogglePillContent>
    </TogglePill>
  ),
};
