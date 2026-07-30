// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { AttributionMatrixWidget } from "./AttributionMatrixWidget";

/**
 * AttributionMatrixWidget — 4 origins × KPI heatmap table.
 * SC-MK-03: attribution matrix.
 * Periods: 7d / 30d / 90d. States: loading · error · empty · populated.
 * Note: data via useAttributionMatrix hook (needs auth). Stories show prop variants.
 */
const meta: Meta<typeof AttributionMatrixWidget> = {
  title: "Marketing/AttributionMatrixWidget",
  component: AttributionMatrixWidget,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
    docs: {
      description: {
        component:
          "Tabla heatmap de atribución por origen (sales_agent, walk_in, phone_manual, proactive_outbound). " +
          "Muestra tasas de conversión con colores (verde ≥40%, amarillo ≥20%, rojo <20%). " +
          "Columnas: leads → calificados → conv. listo → reservas → adopción.",
      },
    },
  },
  argTypes: {
    period: {
      control: "radio",
      options: ["7d", "30d", "90d"],
      description: "Período de análisis",
    },
  },
};
export default meta;

type Story = StoryObj<typeof AttributionMatrixWidget>;

/** Período últimos 7 días */
export const Period7d: Story = {
  args: { period: "7d" },
  name: "Período 7 días",
};

/** Período últimos 30 días (default) */
export const Period30d: Story = {
  args: { period: "30d" },
  name: "Período 30 días (default)",
};

/** Período últimos 90 días */
export const Period90d: Story = {
  args: { period: "90d" },
  name: "Período 90 días",
};
