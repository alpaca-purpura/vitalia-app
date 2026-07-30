// cap: patients.nps-tracking
// story-origin: TBD
/**
 * MultiSessionTab — Storybook stories.
 *
 * Covers:
 *   - Estado de carga (skeletons animados)
 *   - Estado vacío ("todos al día")
 *   - Estado de error
 *
 * Note: useReEngagementPatterns fetches from API.
 * Loaded/populated state requires MSW handler (future enhancement).
 * Loading state renders immediately before first query resolves.
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { fn } from "storybook/test";
import { MultiSessionTab } from "./MultiSessionTab";

const HANDLERS = {
  onSendReminder: fn(),
  onSuggestSlots: fn(),
  onPause: fn(),
  onMarkExternal: fn(),
  onMarkNoContinue: fn(),
  onLogManualCall: fn(),
  onOpenConversation: fn(),
};

const meta: Meta<typeof MultiSessionTab> = {
  title: "Features/Fidelizacion/Tabs/MultiSessionTab",
  component: MultiSessionTab,
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

type Story = StoryObj<typeof MultiSessionTab>;

/** Tab multisesión — estado inicial (carga o vacío según API) */
export const Default: Story = {
  name: "Multisesión — período 30 días",
};

/** Tab multisesión — período 7 días */
export const Period7d: Story = {
  name: "Multisesión — período 7 días",
  args: { period: "7d" },
};

/** Tab multisesión — período 90 días */
export const Period90d: Story = {
  name: "Multisesión — período 90 días",
  args: { period: "90d" },
};
