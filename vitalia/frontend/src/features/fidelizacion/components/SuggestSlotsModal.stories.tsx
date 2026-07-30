// cap: patients.nps-tracking
// story-origin: TBD
/**
 * SuggestSlotsModal — Storybook stories.
 *
 * Covers:
 *   - Estado vacío — sin turnos disponibles
 *   - (El estado de carga y con slots requiere mock de useAvailabilitySlots)
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { fn } from "storybook/test";
import { SuggestSlotsModal } from "./SuggestSlotsModal";

const meta: Meta<typeof SuggestSlotsModal> = {
  title: "Features/Fidelizacion/Modals/SuggestSlotsModal",
  component: SuggestSlotsModal,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "fullscreen",
    nextjs: { appDirectory: true },
  },
  args: {
    eventId: "evt-ms-1",
    patientId: "pat-001",
    doctorId: "doctor-001",
    onClose: fn(),
    onConfirm: fn(),
  },
  argTypes: {
    eventId: { control: false },
    patientId: { control: false },
    doctorId: {
      description:
        "ID del médico para filtrar turnos disponibles. Null = cualquier médico.",
      control: { type: "text" },
    },
    onClose: { action: "close" },
    onConfirm: { action: "confirm" },
  },
};

export default meta;

type Story = StoryObj<typeof SuggestSlotsModal>;

/** Modal de sugerencia de turnos — estado inicial (carga) */
export const Default: Story = {
  name: "Sugerir turnos (carga inicial)",
};

/** Sin médico específico — busca en todos */
export const SinDoctorFilter: Story = {
  name: "Sin filtro de médico",
  args: {
    doctorId: null,
  },
};
