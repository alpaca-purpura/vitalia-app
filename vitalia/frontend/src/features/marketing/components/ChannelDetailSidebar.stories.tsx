// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { ChannelDetailSidebar } from "./ChannelDetailSidebar";

/**
 * ChannelDetailSidebar — slide-in panel con KPIs + campañas + recomendaciones Lucas.
 * SC-MK-02: channel detail sidebar.
 * Security: external link target=_blank rel="noopener noreferrer".
 * States: open (loading · loaded) · closed (not rendered).
 */
const meta: Meta<typeof ChannelDetailSidebar> = {
  title: "Marketing/ChannelDetailSidebar",
  component: ChannelDetailSidebar,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "fullscreen",
  },
  args: {
    onClose: () => {},
  },
};
export default meta;

type Story = StoryObj<typeof ChannelDetailSidebar>;

/** Sidebar abierta con Meta Ads */
export const MetaAdsOpen: Story = {
  args: {
    open: true,
    provider: "meta_ads",
  },
  name: "Abierta — Meta Ads",
};

/** Sidebar abierta con Google Ads */
export const GoogleAdsOpen: Story = {
  args: {
    open: true,
    provider: "google_ads",
  },
  name: "Abierta — Google Ads",
};

/** Sidebar cerrada — no se renderiza */
export const Closed: Story = {
  args: {
    open: false,
    provider: "meta_ads",
  },
  name: "Cerrada — no renderiza (open=false)",
  parameters: {
    docs: {
      description: {
        story:
          "Cuando open=false el componente retorna null. No hay DOM renderizado.",
      },
    },
  },
};
