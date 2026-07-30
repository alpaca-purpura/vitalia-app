// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { MarketingStageTabs } from "./MarketingStageTabs";

/**
 * MarketingStageTabs — 5 horizontal tab selectors.
 * Active tab: cian gradient bg + cian bottom border.
 * Count badges: cian fill active, muted inactive.
 */
const meta: Meta<typeof MarketingStageTabs> = {
  title: "Marketing/MarketingStageTabs",
  component: MarketingStageTabs,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "white" },
    layout: "fullscreen",
  },
  args: {
    onTabChange: () => {},
  },
};
export default meta;

type Story = StoryObj<typeof MarketingStageTabs>;

const mockStages = [
  {
    slug: "attraction" as const,
    label: "Atracción",
    count: 182,
    primaryKpiValue: 24,
    primaryKpiLabel: "cpL",
  },
  {
    slug: "qualification" as const,
    label: "Calificación",
    count: 87,
    primaryKpiValue: 48,
    primaryKpiLabel: "conv%",
  },
  {
    slug: "reservation" as const,
    label: "Reserva",
    count: 36,
    primaryKpiValue: 41,
    primaryKpiLabel: "conv%",
  },
  {
    slug: "adoption" as const,
    label: "Adopción",
    count: 62,
    primaryKpiValue: 87,
    primaryKpiLabel: "adherencia%",
  },
  {
    slug: "expansion" as const,
    label: "Expansión",
    count: 28,
    primaryKpiValue: 72,
    primaryKpiLabel: "NPS",
  },
];

/** Active tab = Atracción (default) */
export const ActiveAttraction: Story = {
  args: { stages: mockStages, activeTab: "attraction" },
  name: "Active: Atracción",
};

/** Active tab = Calificación */
export const ActiveQualification: Story = {
  args: { stages: mockStages, activeTab: "qualification" },
  name: "Active: Calificación",
};

/** Active tab = Reserva */
export const ActiveReservation: Story = {
  args: { stages: mockStages, activeTab: "reservation" },
  name: "Active: Reserva",
};

/** Active tab = Expansión */
export const ActiveExpansion: Story = {
  args: { stages: mockStages, activeTab: "expansion" },
  name: "Active: Expansión",
};

/** Empty stages (loading) */
export const EmptyStages: Story = {
  args: { stages: [], activeTab: "attraction" },
  name: "Empty (loading)",
};
