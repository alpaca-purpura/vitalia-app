// cap: patients.nps-tracking
// story-origin: TBD
/**
 * AbsenceTab — Storybook stories.
 *
 * Covers:
 *   - Estado inicial por período
 *   - Con filtro de médico específico
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { fn } from "storybook/test";
import { AbsenceTab } from "./AbsenceTab";

const HANDLERS = {
  onSendReminder: fn(),
  onSuggestSlots: fn(),
  onPause: fn(),
  onMarkExternal: fn(),
  onMarkNoContinue: fn(),
  onLogManualCall: fn(),
  onOpenConversation: fn(),
};

const meta: Meta<typeof AbsenceTab> = {
  title: "Features/Fidelizacion/Tabs/AbsenceTab",
  component: AbsenceTab,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
    nextjs: { appDirectory: true },
  },
  args: {
    period: "90d",
    vertical: null,
    doctorId: null,
    urgency: [],
    ...HANDLERS,
  },
  argTypes: {
    period: {
      description: "Período de análisis. Para ausencia se recomienda 90d.",
      control: { type: "select" },
      options: ["7d", "30d", "90d"],
    },
    vertical: { control: { type: "text" } },
    doctorId: {
      description: "Filtrar por médico específico.",
      control: { type: "text" },
    },
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

type Story = StoryObj<typeof AbsenceTab>;

/** Tab ausencia — período 90 días */
export const Default: Story = {
  name: "Ausencia — período 90 días",
};

/** Tab ausencia — filtrado por médico */
export const WithDoctorFilter: Story = {
  name: "Ausencia — filtro por médico",
  args: { doctorId: "doctor-garcia-001" },
};
