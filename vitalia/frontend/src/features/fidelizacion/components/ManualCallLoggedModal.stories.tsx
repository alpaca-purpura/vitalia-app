// cap: patients.nps-tracking
// story-origin: TBD
/**
 * ManualCallLoggedModal — Storybook stories.
 *
 * Covers:
 *   - Estado inicial vacío
 *   - Con notas y resultado seleccionado
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { fn } from "storybook/test";
import { ManualCallLoggedModal } from "./ManualCallLoggedModal";

const meta: Meta<typeof ManualCallLoggedModal> = {
  title: "Features/Fidelizacion/Modals/ManualCallLoggedModal",
  component: ManualCallLoggedModal,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "fullscreen",
    nextjs: { appDirectory: true },
  },
  args: {
    eventId: "evt-ms-1",
    patientId: "pat-001",
    onClose: fn(),
  },
  argTypes: {
    eventId: { control: false },
    patientId: { control: false },
    onClose: { action: "close" },
  },
};

export default meta;

type Story = StoryObj<typeof ManualCallLoggedModal>;

/** Estado inicial — sin notas, sin resultado seleccionado */
export const Default: Story = {
  name: "Registrar llamada (estado inicial)",
};
