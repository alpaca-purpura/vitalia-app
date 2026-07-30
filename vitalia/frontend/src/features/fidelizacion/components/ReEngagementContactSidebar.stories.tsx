// cap: patients.nps-tracking
// story-origin: TBD
/**
 * ReEngagementContactSidebar — Storybook stories.
 *
 * Covers:
 *   - Estado con paciente seleccionado
 *   - Estado sin paciente (returns null — no renderiza)
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { fn } from "storybook/test";
import { ReEngagementContactSidebar } from "./ReEngagementContactSidebar";

const meta: Meta<typeof ReEngagementContactSidebar> = {
  title: "Features/Fidelizacion/ReEngagementContactSidebar",
  component: ReEngagementContactSidebar,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
    nextjs: { appDirectory: true },
  },
  args: {
    onClose: fn(),
  },
  argTypes: {
    patientId: {
      description: "ID del paciente. Null = no renderiza el sidebar.",
      control: { type: "text" },
    },
    patientName: {
      description: "Nombre del paciente (PHI — enmascarado según rol).",
      control: { type: "text" },
    },
    onClose: { action: "close" },
  },
};

export default meta;

type Story = StoryObj<typeof ReEngagementContactSidebar>;

/** Sidebar con paciente seleccionado */
export const WithPatient: Story = {
  name: "Con paciente seleccionado",
  args: {
    patientId: "pat-001",
    patientName: "María González",
  },
};

/** Sin paciente — no renderiza (returns null) */
export const NoPatient: Story = {
  name: "Sin paciente (no renderiza)",
  args: {
    patientId: null,
    patientName: null,
  },
};
