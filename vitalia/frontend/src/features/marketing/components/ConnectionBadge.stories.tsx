// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { ConnectionBadge } from "./ConnectionBadge";

/**
 * ConnectionBadge — 4-state sync status pill badge.
 * States: idle | running | error | disconnected
 * Colors: vt-text-* CSS vars — no hardcoded HEX.
 */
const meta: Meta<typeof ConnectionBadge> = {
  title: "Marketing/ConnectionBadge",
  component: ConnectionBadge,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
  argTypes: {
    status: {
      control: "select",
      options: ["idle", "running", "error", "disconnected"],
    },
    variant: {
      control: "radio",
      options: ["default", "success"],
    },
  },
};
export default meta;

type Story = StoryObj<typeof ConnectionBadge>;

/** Sincronizado y en reposo */
export const Idle: Story = {
  args: { status: "idle" },
  name: "Idle — sincronizado",
};

/** Sincronización en progreso */
export const Running: Story = {
  args: { status: "running" },
  name: "Running — sincronizando",
};

/** Error de sincronización */
export const Error: Story = {
  args: { status: "error" },
  name: "Error — falla de sincronización",
};

/** Canal desconectado */
export const Disconnected: Story = {
  args: { status: "disconnected" },
  name: "Disconnected — sin conexión",
};

/** Variante success: recientemente conectado, badge verde aunque idle */
export const SuccessVariant: Story = {
  args: { status: "idle", variant: "success" },
  name: "Success variant — recientemente conectado",
};

/** Label personalizado */
export const CustomLabel: Story = {
  args: { status: "idle", label: "Activo" },
  name: "Custom label override",
};
