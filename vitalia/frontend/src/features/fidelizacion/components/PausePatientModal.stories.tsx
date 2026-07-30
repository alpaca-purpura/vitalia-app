// cap: patients.nps-tracking
// story-origin: TBD
/**
 * PausePatientModal — Storybook stories.
 *
 * Covers:
 *   - Default state (7 días pre-seleccionado)
 *   - Duración personalizada seleccionada (input visible)
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { fn } from "storybook/test";
import { PausePatientModal } from "./PausePatientModal";

const meta: Meta<typeof PausePatientModal> = {
  title: "Features/Fidelizacion/Modals/PausePatientModal",
  component: PausePatientModal,
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

type Story = StoryObj<typeof PausePatientModal>;

/** Estado inicial — duración 7 días, sin razón */
export const Default: Story = {
  name: "Modal de pausa (estado inicial)",
};
