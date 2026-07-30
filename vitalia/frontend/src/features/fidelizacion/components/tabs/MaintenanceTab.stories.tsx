// cap: patients.nps-tracking
// story-origin: TBD
/**
 * MaintenanceTab — Storybook stories.
 *
 * Covers:
 *   - Estado inicial por período
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { fn } from "storybook/test";
import { MaintenanceTab } from "./MaintenanceTab";

const HANDLERS = {
  onSendReminder: fn(),
  onSuggestSlots: fn(),
  onPause: fn(),
  onMarkExternal: fn(),
  onMarkNoContinue: fn(),
  onLogManualCall: fn(),
  onOpenConversation: fn(),
};

const meta: Meta<typeof MaintenanceTab> = {
  title: "Features/Fidelizacion/Tabs/MaintenanceTab",
  component: MaintenanceTab,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
    nextjs: { appDirectory: true },
  },
  args: {
    period: "30d",
    vertical: null,
    doctorId: null,
    urgency: [],
    ...HANDLERS,
  },
  argTypes: {
    period: {
      description: "Período de análisis.",
      control: { type: "select" },
      options: ["7d", "30d", "90d"],
    },
    vertical: { control: { type: "text" } },
    doctorId: { control: { type: "text" } },
    urgency: { control: false },
    onSendReminder: { action: "sendReminder" },
    onSuggestSlots: { action: "suggestSlots" },
    onPause: { action: "pause" },
    onMarkExternal: { action: "markExternal" },
    onMarkNoContinue: { action: "markNoContinue" },
    onLogManualCall: { action: "logManualCall" },
    onOpenConversation: { action: "openConversation" },
  },
};

export default meta;

type Story = StoryObj<typeof MaintenanceTab>;

/** Tab mantenimiento — período 30 días */
export const Default: Story = {
  name: "Mantenimiento — período 30 días",
};

/** Tab mantenimiento — período 90 días */
export const Period90d: Story = {
  name: "Mantenimiento — período 90 días",
  args: { period: "90d" },
};
