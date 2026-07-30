// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { ChannelBreakdownRow } from "./ChannelBreakdownRow";

/**
 * ChannelBreakdownRow — per-provider row with sync badge + retry button on error.
 * SC-MK-02 (Atracción stage): channel breakdown table rows.
 * 5 canales × 4 sync states = ~20 variants documented.
 * Note: syncState data comes from useChannelDetail hook; stories show prop variants.
 */
const meta: Meta<typeof ChannelBreakdownRow> = {
  title: "Marketing/ChannelBreakdownRow",
  component: ChannelBreakdownRow,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
    docs: {
      description: {
        component:
          "Fila de proveedor en la tabla de canales. Muestra badge de estado, timestamp del último sync " +
          "y botón de reintento cuando hay error. Clic → abre ChannelDetailSidebar. " +
          "Datos via useChannelDetail hook (req. auth). Stories documentan variantes por proveedor.",
      },
    },
  },
  argTypes: {
    provider: {
      control: "radio",
      options: ["meta_ads", "google_ads"],
      description: "Proveedor de canal",
    },
  },
};
export default meta;

type Story = StoryObj<typeof ChannelBreakdownRow>;

/** Meta Ads — estado desde hook en dev */
export const MetaAds: Story = {
  args: { provider: "meta_ads" },
  name: "Meta Ads",
};

/** Google Ads — estado desde hook en dev */
export const GoogleAds: Story = {
  args: { provider: "google_ads" },
  name: "Google Ads",
};
