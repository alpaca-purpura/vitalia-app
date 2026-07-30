// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { MarketingBowtieSVG } from "./MarketingBowtieSVG";
import type { BowtieStage } from "./MarketingBowtieSVG";

/**
 * MarketingBowtieSVG — attribution bowtie funnel scaffold.
 * Full implementation with real analytics data arrives in Slice 2+.
 */
const meta: Meta<typeof MarketingBowtieSVG> = {
  title: "Shared/Marketing/MarketingBowtieSVG",
  component: MarketingBowtieSVG,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
};
export default meta;

type Story = StoryObj<typeof MarketingBowtieSVG>;

const acquisitionStages: BowtieStage[] = [
  { id: "awareness", label: "Atracción", value: 1200, side: "acquisition" },
  { id: "consideration", label: "Interés", value: 540, side: "acquisition" },
  { id: "decision", label: "Decisión", value: 180, side: "acquisition" },
];

const retentionStages: BowtieStage[] = [
  { id: "adoption", label: "Adopción", value: 160, side: "retention" },
  { id: "expansion", label: "Expansión", value: 90, side: "retention" },
  { id: "advocacy", label: "Referidos", value: 40, side: "retention" },
];

/** Default empty — placeholder SVG */
export const PlaceholderEmpty: Story = {
  name: "Sin datos — placeholder",
  args: {},
};

/** Loading */
export const Loading: Story = {
  name: "Cargando",
  args: { isLoading: true },
};

/** With data */
export const WithData: Story = {
  name: "Con datos de ejemplo",
  args: {
    acquisitionStages,
    retentionStages,
    width: 480,
    height: 200,
  },
};

/** Compact size */
export const Compact: Story = {
  name: "Tamaño compacto (300×140)",
  args: {
    acquisitionStages,
    retentionStages,
    width: 300,
    height: 140,
  },
};
