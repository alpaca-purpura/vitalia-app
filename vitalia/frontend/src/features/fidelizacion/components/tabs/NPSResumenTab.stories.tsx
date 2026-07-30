// cap: patients.nps-tracking
// story-origin: TBD
/**
 * NPSResumenTab — Storybook stories.
 *
 * Covers:
 *   - Estado inicial por período (carga, vacío o poblado según API)
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { NPSResumenTab } from "./NPSResumenTab";

const meta: Meta<typeof NPSResumenTab> = {
  title: "Features/Fidelizacion/Tabs/NPSResumenTab",
  component: NPSResumenTab,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
    nextjs: { appDirectory: true },
  },
  args: {
    period: "30d",
  },
  argTypes: {
    period: {
      description: "Período para filtrar respuestas de NPS.",
      control: { type: "select" },
      options: ["7d", "30d", "90d"],
    },
  },
};

export default meta;

type Story = StoryObj<typeof NPSResumenTab>;

/** Tab NPS — período 30 días */
export const Default: Story = {
  name: "NPS Resumen — período 30 días",
};

/** Tab NPS — período 7 días */
export const Period7d: Story = {
  name: "NPS Resumen — período 7 días",
  args: { period: "7d" },
};

/** Tab NPS — período 90 días */
export const Period90d: Story = {
  name: "NPS Resumen — período 90 días",
  args: { period: "90d" },
};
