// cap: marketing.attribution-matrix-4-origins
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { AttributionMatrixWidget } from "./AttributionMatrixWidget";
import type {
  AttributionChannel,
  AttributionCell,
} from "./AttributionMatrixWidget";

/**
 * AttributionMatrixWidget — channels × touchpoints attribution matrix.
 * Full implementation with real API data arrives in growth-studio (Slice 2+).
 */
const meta: Meta<typeof AttributionMatrixWidget> = {
  title: "Shared/Attribution/AttributionMatrixWidget",
  component: AttributionMatrixWidget,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
};
export default meta;

type Story = StoryObj<typeof AttributionMatrixWidget>;

const channels: AttributionChannel[] = [
  { slug: "instagram-organic", name: "Instagram Orgánico" },
  { slug: "google-ads", name: "Google Ads" },
  { slug: "whatsapp-outbound", name: "WhatsApp Saliente" },
  { slug: "referrals", name: "Referidos" },
];

const cells: AttributionCell[] = [
  { channelSlug: "instagram-organic", touchpoint: "Primer toque", score: 0.45 },
  { channelSlug: "instagram-organic", touchpoint: "Último toque", score: 0.12 },
  { channelSlug: "instagram-organic", touchpoint: "Lineal", score: 0.28 },
  { channelSlug: "google-ads", touchpoint: "Primer toque", score: 0.2 },
  { channelSlug: "google-ads", touchpoint: "Último toque", score: 0.58 },
  { channelSlug: "google-ads", touchpoint: "Lineal", score: 0.35 },
  { channelSlug: "whatsapp-outbound", touchpoint: "Primer toque", score: 0.1 },
  { channelSlug: "whatsapp-outbound", touchpoint: "Último toque", score: 0.22 },
  { channelSlug: "whatsapp-outbound", touchpoint: "Lineal", score: 0.18 },
  { channelSlug: "referrals", touchpoint: "Primer toque", score: 0.25 },
  { channelSlug: "referrals", touchpoint: "Último toque", score: 0.08 },
  { channelSlug: "referrals", touchpoint: "Lineal", score: 0.19 },
];

/** Empty state */
export const EmptyState: Story = {
  name: "Sin datos",
  args: { channels: [], cells: [] },
};

/** Loading */
export const Loading: Story = {
  name: "Cargando",
  args: { isLoading: true },
};

/** Full matrix with data */
export const WithData: Story = {
  name: "Matriz completa con datos",
  args: { channels, cells },
};

/** Single channel */
export const SingleChannel: Story = {
  name: "Un canal",
  args: {
    channels: [{ slug: "google-ads", name: "Google Ads" }],
    cells: cells.filter((c) => c.channelSlug === "google-ads"),
  },
};
