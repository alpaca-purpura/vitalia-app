// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { LucasUndoChip } from "./LucasUndoChip";

/**
 * LucasUndoChip — 5-min countdown undo chip after approving a recommendation.
 * SC-MK-01: post-approve undo window.
 * Note: chip reads from useMarketingStore — in Storybook renders null when no active timer.
 * To see the chip, the store must have a pending timer for the given recId.
 * Use StoryWithTimer decorator or test directly in the full LucasStageRecommendationsCard story.
 */
const meta: Meta<typeof LucasUndoChip> = {
  title: "Marketing/LucasUndoChip",
  component: LucasUndoChip,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
    docs: {
      description: {
        component:
          "El chip muestra un contador de 5 minutos tras aprobar una recomendación. Lee el estado de useMarketingStore — " +
          "se renderiza null cuando no hay timer activo. El estado completo se verifica en LucasStageRecommendationsCard stories.",
      },
    },
  },
};
export default meta;

type Story = StoryObj<typeof LucasUndoChip>;

/**
 * Sin timer activo — el chip no se renderiza (null).
 * Este es el estado default cuando no hay aprobación reciente.
 */
export const NoActiveTimer: Story = {
  args: { recId: "rec-no-timer" },
  name: "Sin timer activo — chip no visible (null)",
};
