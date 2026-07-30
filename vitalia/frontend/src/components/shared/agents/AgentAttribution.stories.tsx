// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { AgentAttribution } from "./AgentAttribution";

/**
 * AgentAttribution — attribution line showing agent + action + optional target + timestamp.
 * Used in activity streams and copilot history per design-system.md.
 */
const meta: Meta<typeof AgentAttribution> = {
  title: "Shared/Agents/AgentAttribution",
  component: AgentAttribution,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-surface" },
    layout: "padded",
  },
  argTypes: {
    role: {
      control: "select",
      options: ["valeria", "adrian", "lucas"],
      description: "Agent role",
    },
  },
};
export default meta;

type Story = StoryObj<typeof AgentAttribution>;

/** Valeria updating a patient record */
export const ValeriaActualizoPerfil: Story = {
  name: "Valeria — actualizó perfil",
  args: {
    role: "valeria",
    action: "actualizó el perfil",
    target: "de la paciente",
    timestamp: "hace 5 min",
  },
};

/** Adrián sending a follow-up */
export const AdrianEnvioSeguimiento: Story = {
  name: "Adrián — envió seguimiento",
  args: {
    role: "adrian",
    action: "envió seguimiento",
    target: "por WhatsApp",
    timestamp: "hace 12 min",
  },
};

/** Lucas providing a recommendation */
export const LucasRecomendo: Story = {
  name: "Lucas — recomendó etapa",
  args: {
    role: "lucas",
    action: "recomendó pasar a",
    target: "etapa de nutrición",
    timestamp: "hace 1 h",
  },
};

/** Without role — only action text */
export const WithoutRole: Story = {
  name: "Sin target ni timestamp",
  args: {
    role: "valeria",
    action: "completó el formulario de admisión",
  },
};

/** All three agents stacked */
export const AllAgentsStacked: Story = {
  name: "Tres agentes — apilados",
  render: () => (
    <div className="flex flex-col gap-3 max-w-sm">
      <AgentAttribution
        role="valeria"
        action="actualizó el perfil"
        target="de la paciente"
        timestamp="hace 5 min"
      />
      <AgentAttribution
        role="adrian"
        action="envió mensaje de seguimiento"
        timestamp="hace 12 min"
      />
      <AgentAttribution
        role="lucas"
        action="registró nueva recomendación"
        target="para etapa nutrición"
        timestamp="hace 1 h"
      />
    </div>
  ),
};
