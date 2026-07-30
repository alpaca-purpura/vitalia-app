// cap: marketing.attribution-matrix-4-origins
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { ChannelBreakdownRow } from "./ChannelBreakdownRow";

/**
 * ChannelBreakdownRow — single channel performance row widget.
 * Full analytics data integration arrives in growth-studio (Slice 2+).
 */
const meta: Meta<typeof ChannelBreakdownRow> = {
  title: "Shared/Channels/ChannelBreakdownRow",
  component: ChannelBreakdownRow,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-surface" },
    layout: "padded",
  },
};
export default meta;

type Story = StoryObj<typeof ChannelBreakdownRow>;

/** Instagram organic with positive change */
export const InstagramPositive: Story = {
  name: "Instagram Orgánico — cambio positivo",
  args: {
    channelSlug: "instagram-organic",
    channelName: "Instagram Orgánico",
    primaryValue: 8520,
    primaryLabel: "impresiones",
    secondaryValue: 342,
    secondaryLabel: "clics",
    changePct: 12.5,
  },
};

/** Google Ads with negative change */
export const GoogleAdsNegative: Story = {
  name: "Google Ads — cambio negativo",
  args: {
    channelSlug: "google-ads",
    channelName: "Google Ads",
    primaryValue: 3100,
    primaryLabel: "impresiones",
    secondaryValue: 180,
    secondaryLabel: "clics",
    changePct: -3.2,
  },
};

/** No change (flat) */
export const FlatChange: Story = {
  name: "WhatsApp Outbound — sin cambio",
  args: {
    channelSlug: "whatsapp-outbound",
    channelName: "WhatsApp Saliente",
    primaryValue: 220,
    primaryLabel: "mensajes",
    changePct: 0,
  },
};

/** Without secondary metric or change */
export const MinimalProps: Story = {
  name: "Solo métrica primaria",
  args: {
    channelSlug: "referrals",
    channelName: "Referidos",
    primaryValue: 45,
    primaryLabel: "visitas",
  },
};

/** Loading state */
export const Loading: Story = {
  name: "Cargando",
  args: {
    channelSlug: "facebook-organic",
    channelName: "Facebook Orgánico",
    primaryValue: 0,
    primaryLabel: "impresiones",
    isLoading: true,
  },
};

/** Table of multiple rows */
export const MultipleRows: Story = {
  name: "Varios canales — tabla",
  render: () => (
    <div className="rounded-[14px] border overflow-hidden vt-border">
      <ChannelBreakdownRow
        channelSlug="ig"
        channelName="Instagram Orgánico"
        primaryValue={8520}
        primaryLabel="impresiones"
        secondaryValue={342}
        secondaryLabel="clics"
        changePct={12.5}
      />
      <ChannelBreakdownRow
        channelSlug="gads"
        channelName="Google Ads"
        primaryValue={3100}
        primaryLabel="impresiones"
        secondaryValue={180}
        secondaryLabel="clics"
        changePct={-3.2}
      />
      <ChannelBreakdownRow
        channelSlug="wa"
        channelName="WhatsApp Saliente"
        primaryValue={220}
        primaryLabel="mensajes"
        changePct={0}
      />
      <ChannelBreakdownRow
        channelSlug="ref"
        channelName="Referidos"
        primaryValue={45}
        primaryLabel="visitas"
      />
    </div>
  ),
};
