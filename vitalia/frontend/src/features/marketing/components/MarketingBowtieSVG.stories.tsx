// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { MarketingBowtieSVG } from "./MarketingBowtieSVG";

/**
 * MarketingBowtieSVG — 5-stage bowtie funnel SVG (pixel-invariante per mockup v1 Batch 6).
 * Uses vitalia CSS var tokens — no hardcoded colors.
 */
const meta: Meta<typeof MarketingBowtieSVG> = {
  title: "Marketing/MarketingBowtieSVG",
  component: MarketingBowtieSVG,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
};
export default meta;

type Story = StoryObj<typeof MarketingBowtieSVG>;

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

/** Default state with all 5 stages loaded */
export const Default: Story = {
  args: { stages: mockStages, isLoading: false },
};

/** Loading skeleton state */
export const Loading: Story = {
  args: { stages: [], isLoading: true },
  name: "Loading state",
};

/** Empty state — no data returned */
export const Empty: Story = {
  args: { stages: [], isLoading: false },
  name: "Empty state (no data)",
};

/** Partial data — only first 3 stages */
export const PartialData: Story = {
  args: { stages: mockStages.slice(0, 3), isLoading: false },
  name: "Partial data (3 stages)",
};
