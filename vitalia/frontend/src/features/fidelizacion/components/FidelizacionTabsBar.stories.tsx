// cap: patients.nps-tracking
// story-origin: TBD
/**
 * FidelizacionTabsBar — Storybook stories.
 *
 * Covers:
 *   - Each of the 5 tabs as the active selection
 *   - Callback interaction via fn()
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { fn } from "storybook/test";
import { FidelizacionTabsBar } from "./FidelizacionTabsBar";
import type { FidelizacionTab } from "../types/url-state";

const meta: Meta<typeof FidelizacionTabsBar> = {
  title: "Features/Fidelizacion/FidelizacionTabsBar",
  component: FidelizacionTabsBar,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
  args: {
    onTabChange: fn(),
  },
  argTypes: {
    activeTab: {
      description: "Currently selected tab identifier.",
      control: { type: "select" },
      options: [
        "multisession",
        "followup",
        "maintenance",
        "absence",
        "nps",
      ] satisfies FidelizacionTab[],
    },
    onTabChange: { action: "tabChange" },
    className: { control: false },
  },
};

export default meta;

type Story = StoryObj<typeof FidelizacionTabsBar>;

/** Tab activa: Multisesión */
export const TabMultisession: Story = {
  name: "Tab activa: Multisesión",
  args: { activeTab: "multisession" },
};

/** Tab activa: Seguimiento médico */
export const TabFollowup: Story = {
  name: "Tab activa: Seguimiento médico",
  args: { activeTab: "followup" },
};

/** Tab activa: Mantenimiento */
export const TabMaintenance: Story = {
  name: "Tab activa: Mantenimiento",
  args: { activeTab: "maintenance" },
};

/** Tab activa: Ausencia */
export const TabAbsence: Story = {
  name: "Tab activa: Ausencia",
  args: { activeTab: "absence" },
};

/** Tab activa: NPS */
export const TabNPS: Story = {
  name: "Tab activa: NPS",
  args: { activeTab: "nps" },
};
