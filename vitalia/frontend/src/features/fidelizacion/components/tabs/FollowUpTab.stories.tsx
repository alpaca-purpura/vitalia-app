// cap: patients.nps-tracking
// story-origin: TBD
/**
 * FollowUpTab — Storybook stories.
 *
 * Covers:
 *   - Estado inicial por período
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { fn } from "storybook/test";
import { FollowUpTab } from "./FollowUpTab";

const HANDLERS = {
  onSendReminder: fn(),
  onSuggestSlots: fn(),
  onPause: fn(),
  onMarkExternal: fn(),
  onMarkNoContinue: fn(),
  onLogManualCall: fn(),
  onOpenConversation: fn(),
};

const meta: Meta<typeof FollowUpTab> = {
  title: "Features/Fidelizacion/Tabs/FollowUpTab",
  component: FollowUpTab,
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

type Story = StoryObj<typeof FollowUpTab>;

/** Tab seguimiento médico — período 30 días */
export const Default: Story = {
  name: "Seguimiento médico — período 30 días",
};

/** Tab seguimiento médico — período 7 días */
export const Period7d: Story = {
  name: "Seguimiento médico — período 7 días",
  args: { period: "7d" },
};
