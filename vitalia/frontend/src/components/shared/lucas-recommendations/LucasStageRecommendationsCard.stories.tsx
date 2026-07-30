// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { LucasStageRecommendationsCard } from "./LucasStageRecommendationsCard";
import type { StageRecommendation } from "./LucasStageRecommendationsCard";

/**
 * LucasStageRecommendationsCard — scaffold placeholder.
 * Full implementation arrives in copilot-tools-impl (Slice 2).
 */
const meta: Meta<typeof LucasStageRecommendationsCard> = {
  title: "Shared/LucasStageRecommendationsCard",
  component: LucasStageRecommendationsCard,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
};
export default meta;

type Story = StoryObj<typeof LucasStageRecommendationsCard>;

const nutritionRecs: StageRecommendation[] = [
  {
    id: "r1",
    title: "Programar sesión de seguimiento nutricional",
    priority: "high",
  },
  {
    id: "r2",
    title: "Enviar guía de alimentación post-tratamiento",
    detail: "PDF adjunto en la biblioteca",
    priority: "medium",
  },
  {
    id: "r3",
    title: "Recordar ingesta de suplementos recetados",
    priority: "low",
  },
];

/** Empty state */
export const EmptyState: Story = {
  name: "Estado vacío — sin recomendaciones",
  args: { stageLabel: "Nutrición", recommendations: [] },
};

/** Loading state */
export const LoadingState: Story = {
  name: "Cargando",
  args: { stageLabel: "Adopción", isLoading: true },
};

/** With recommendations */
export const WithRecommendations: Story = {
  name: "Con recomendaciones (etapa: Nutrición)",
  args: {
    stageLabel: "Nutrición",
    recommendations: nutritionRecs,
  },
};

/** Single high-priority recommendation */
export const SingleHighPriority: Story = {
  name: "Una recomendación de alta prioridad",
  args: {
    stageLabel: "Activación",
    recommendations: [
      {
        id: "r-hp",
        title: "Confirmar asistencia a próxima cita — paciente sin respuesta",
        priority: "high",
      },
    ],
  },
};
