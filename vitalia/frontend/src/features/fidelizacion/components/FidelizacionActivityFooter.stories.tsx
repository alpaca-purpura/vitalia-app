// cap: patients.nps-tracking
// story-origin: TBD
/**
 * FidelizacionActivityFooter — Storybook stories.
 *
 * Covers:
 *   - Estado de carga (shimmer placeholders)
 *
 * Note: useActivityStream + useTenantLocale hooks make network calls.
 * State shown here is the initial loading skeleton.
 * Full populated/empty states require MSW handler (future enhancement).
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { FidelizacionActivityFooter } from "./FidelizacionActivityFooter";

const meta: Meta<typeof FidelizacionActivityFooter> = {
  title: "Features/Fidelizacion/FidelizacionActivityFooter",
  component: FidelizacionActivityFooter,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-surface" },
    layout: "padded",
    nextjs: { appDirectory: true },
  },
  argTypes: {
    className: { control: false },
  },
};

export default meta;

type Story = StoryObj<typeof FidelizacionActivityFooter>;

/** Footer de actividad reciente — estado de carga inicial */
export const Default: Story = {
  name: "Actividad reciente (estado inicial)",
};
