// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { WizardChatThread } from "./WizardChatThread";
import type { WizardMessage } from "./WizardChatThread";

/**
 * WizardChatThread — conversational onboarding wizard scaffold.
 * Full SSE streaming integration arrives in copilot-tools-impl (Slice 2).
 */
const meta: Meta<typeof WizardChatThread> = {
  title: "Shared/Wizard/WizardChatThread",
  component: WizardChatThread,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
};
export default meta;

type Story = StoryObj<typeof WizardChatThread>;

const basicMessages: WizardMessage[] = [
  {
    id: "m1",
    role: "assistant",
    content:
      "Hola, soy Valeria. Vamos a configurar tu perfil. ¿Cuál es el nombre de tu clínica?",
    timestamp: "10:01",
  },
  {
    id: "m2",
    role: "user",
    content: "Clínica Salud Integral",
    timestamp: "10:02",
  },
  {
    id: "m3",
    role: "assistant",
    content:
      "Perfecto. ¿Cuántos profesionales de salud trabajan en la clínica?",
    timestamp: "10:02",
  },
];

const completeMessages: WizardMessage[] = [
  ...basicMessages,
  {
    id: "m4",
    role: "user",
    content: "Somos 4 médicos y 2 enfermeras.",
    timestamp: "10:03",
  },
  {
    id: "m5",
    role: "assistant",
    content:
      "Excelente. Última pregunta: ¿cuál es la especialidad principal de la clínica?",
    timestamp: "10:03",
  },
  {
    id: "m6",
    role: "user",
    content: "Medicina general y nutrición.",
    timestamp: "10:04",
  },
  {
    id: "m7",
    role: "assistant",
    content:
      "¡Listo! Configuré tu perfil de clínica. Puedes editarlo en cualquier momento.",
    timestamp: "10:04",
  },
];

/** Empty state — no messages yet */
export const EmptyState: Story = {
  name: "Sin mensajes — inicio",
  args: {
    messages: [],
    stepLabel: "Paso 1 — Nombre de la clínica",
    progress: 0,
  },
};

/** Typing indicator */
export const TypingIndicator: Story = {
  name: "Asistente escribiendo",
  args: {
    messages: [{ id: "m1", role: "user", content: "Clínica Salud Integral" }],
    isTyping: true,
    stepLabel: "Paso 1",
    progress: 0.2,
  },
};

/** Mid-conversation */
export const MidConversation: Story = {
  name: "Conversación en progreso",
  args: {
    messages: basicMessages,
    stepLabel: "Paso 2 — Equipo de trabajo",
    progress: 0.4,
  },
};

/** Complete conversation */
export const Complete: Story = {
  name: "Conversación completada",
  args: {
    messages: completeMessages,
    stepLabel: "Configuración completa",
    progress: 1,
  },
};
