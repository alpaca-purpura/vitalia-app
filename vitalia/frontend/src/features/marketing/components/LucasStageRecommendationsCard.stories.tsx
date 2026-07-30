// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { LucasStageRecommendationsCard } from "./LucasStageRecommendationsCard";

/**
 * LucasStageRecommendationsCard — panel with top 3 priority recommendations + "Ver todas".
 * SC-MK-01: recommendations panel.
 * States: loading · error · empty · populated (open recs) · approved with undo · rejected · expired.
 * Note: hook data (useLucasRecommendations) is mocked via MSW or static args in CI.
 * The component itself renders loading/error/empty/populated states based on hook output.
 */
const meta: Meta<typeof LucasStageRecommendationsCard> = {
  title: "Marketing/LucasStageRecommendationsCard",
  component: LucasStageRecommendationsCard,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
    docs: {
      description: {
        component:
          "Muestra las top 3 recomendaciones de Lucas para un stage dado. " +
          "Las stories cubren el árbol de estados: loading → error → empty → populated con acciones RBAC. " +
          "En Storybook sin MSW, el hook renderiza la UI de loading (query enabled=false sin auth).",
      },
    },
  },
};
export default meta;

type Story = StoryObj<typeof LucasStageRecommendationsCard>;

/** Vista con filtro por stage Atracción (datos reales via hook en dev) */
export const AttractionStage: Story = {
  args: { stage: "attraction", userRole: "admin_clinic" },
  name: "Stage: Atracción — admin_clinic",
};

/** Vista con filtro por stage Calificación */
export const QualificationStage: Story = {
  args: { stage: "qualification", userRole: "doctor" },
  name: "Stage: Calificación — doctor",
};

/** Vista sin filtro de stage — cross-stage view */
export const AllStages: Story = {
  args: { stage: undefined, userRole: "admin_clinic" },
  name: "Cross-stage — todas las recomendaciones",
};

/** Rol recepcion — puede ver pero no aprobar (SC-MK-04) */
export const RecepcionRole: Story = {
  args: { stage: "attraction", userRole: "recepcion" },
  name: "Recepción — solo lectura (SC-MK-04)",
};
