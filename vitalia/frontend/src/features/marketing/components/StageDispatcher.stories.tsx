// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { StageDispatcher } from "./StageDispatcher";

/**
 * StageDispatcher — renders the correct stage section based on active tab.
 * Shows slot placeholders for T-mk-fe-3..5 content (Lucas cards, channels, attribution, referrals).
 */
const meta: Meta<typeof StageDispatcher> = {
  title: "Marketing/StageDispatcher",
  component: StageDispatcher,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-surface-alt" },
    layout: "padded",
  },
};
export default meta;

type Story = StoryObj<typeof StageDispatcher>;

/** Atracción stage — shows Lucas slot + channel breakdown slot */
export const Attraction: Story = {
  args: { activeTab: "attraction" },
  name: "Stage: Atracción",
};

/** Calificación stage — shows Lucas slot only */
export const Qualification: Story = {
  args: { activeTab: "qualification" },
  name: "Stage: Calificación",
};

/** Reserva stage — shows Lucas slot + attribution matrix slot */
export const Reservation: Story = {
  args: { activeTab: "reservation" },
  name: "Stage: Reserva",
};

/** Adopción stage — shows Lucas slot only */
export const Adoption: Story = {
  args: { activeTab: "adoption" },
  name: "Stage: Adopción",
};

/** Expansión stage — shows Lucas slot + referrals slot */
export const Expansion: Story = {
  args: { activeTab: "expansion" },
  name: "Stage: Expansión",
};
