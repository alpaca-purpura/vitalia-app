// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { MarketingActivityFooter } from "./MarketingActivityFooter";

/**
 * MarketingActivityFooter — activity/sync status footer row.
 * Template: "Lucas analizó {N} leads · sistema sync c/4h · última sync {time}"
 */
const meta: Meta<typeof MarketingActivityFooter> = {
  title: "Marketing/MarketingActivityFooter",
  component: MarketingActivityFooter,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
};
export default meta;

type Story = StoryObj<typeof MarketingActivityFooter>;

const recentSync = new Date(Date.now() - 23 * 60_000).toISOString(); // 23 min ago
const longAgoSync = new Date(Date.now() - 4 * 3600_000).toISOString(); // 4h ago

/** Default: recent sync, known lead count */
export const Default: Story = {
  args: {
    leadsAnalyzed: 182,
    lastSyncAt: recentSync,
    isLoading: false,
  },
};

/** Long sync ago (4h) */
export const OlderSync: Story = {
  args: {
    leadsAnalyzed: 87,
    lastSyncAt: longAgoSync,
    isLoading: false,
  },
  name: "Older sync (4h ago)",
};

/** Never synced */
export const NeverSynced: Story = {
  args: {
    leadsAnalyzed: null,
    lastSyncAt: null,
    isLoading: false,
  },
  name: "Never synced",
};

/** Loading state */
export const Loading: Story = {
  args: {
    leadsAnalyzed: null,
    lastSyncAt: null,
    isLoading: true,
  },
  name: "Loading state",
};
