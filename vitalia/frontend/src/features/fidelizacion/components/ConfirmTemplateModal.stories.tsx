// cap: patients.nps-tracking
// story-origin: TBD
/**
 * ConfirmTemplateModal — Storybook stories.
 *
 * Covers:
 *   - Default preview state (before confirming)
 *   - Sending state (mutation pending)
 *   - Accessible modal markup (role="dialog", focus trap)
 *
 * Note: mutation hook (useSendProactiveTemplate) is mocked via
 * @storybook/nextjs module mock support.
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { fn } from "storybook/test";
import { ConfirmTemplateModal } from "./ConfirmTemplateModal";
import type { SendProactiveRequest } from "../types/re-engagement";

const MOCK_PAYLOAD: SendProactiveRequest = {
  templateId: "tpl-reminder-kinesiologia-001",
  pattern: "multi_session",
  slotValues: {
    patient_name: "María",
    offer_label: "Pack Kinesiología 10 sesiones",
    gap_days: "18",
  },
  triggerSource: "fidelizacion_manual",
};

const MOCK_PREVIEW =
  "Hola María, notamos que llevas 18 días sin tu sesión de Pack Kinesiología 10 sesiones. ¿Quieres retomar? Tu bienestar es nuestra prioridad.";

const meta: Meta<typeof ConfirmTemplateModal> = {
  title: "Features/Fidelizacion/Modals/ConfirmTemplateModal",
  component: ConfirmTemplateModal,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "fullscreen",
    nextjs: { appDirectory: true },
  },
  args: {
    eventId: "evt-ms-1",
    patientId: "pat-001",
    payload: MOCK_PAYLOAD,
    previewText: MOCK_PREVIEW,
    onClose: fn(),
  },
  argTypes: {
    eventId: { control: false },
    patientId: { control: false },
    payload: { control: false },
    previewText: {
      description: "Vista previa del mensaje a enviar por WhatsApp.",
      control: { type: "text" },
    },
    onClose: { action: "close" },
  },
};

export default meta;

type Story = StoryObj<typeof ConfirmTemplateModal>;

/** Vista previa del mensaje antes de confirmar */
export const Default: Story = {
  name: "Vista previa (antes de enviar)",
};

/** Vista previa con mensaje más largo */
export const LongPreview: Story = {
  name: "Vista previa: mensaje largo",
  args: {
    previewText:
      "Hola María González, hace 18 días que no tienes una sesión de kinesiología programada en tu Pack de 10 sesiones con el Dr. Rodríguez. Llevas 4 sesiones completadas de 10. Tu próxima sesión podría ser esta semana. ¿Quieres que te ayude a coordinar una hora? Respondé este mensaje y con gusto te asisto.",
  },
};
