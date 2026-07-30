// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { LucasRejectModal } from "./LucasRejectModal";

/**
 * LucasRejectModal — reason-required form for rejecting a Lucas recommendation.
 * SC-MK-01: reject flow with Zod-validated radio group.
 * reason required; reasonOtherText conditional when reason === "other".
 */
const meta: Meta<typeof LucasRejectModal> = {
  title: "Marketing/LucasRejectModal",
  component: LucasRejectModal,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "fullscreen",
  },
  args: {
    onClose: () => {},
    recId: "rec-001",
  },
};
export default meta;

type Story = StoryObj<typeof LucasRejectModal>;

/** Estado inicial — formulario vacío, ningún motivo seleccionado */
export const Default: Story = {
  name: "Default — formulario vacío",
};

/** Motivo "Otro" seleccionado — textarea adicional visible */
export const OtherReasonSelected: Story = {
  name: "Motivo 'Otro' — textarea visible",
  // Note: motivo "otro" shows textarea; requires user interaction in Storybook
  parameters: {
    docs: {
      description: {
        story:
          "Al seleccionar 'Otro', aparece un campo adicional para especificar el motivo. Probar interactivamente en el canvas.",
      },
    },
  },
};
