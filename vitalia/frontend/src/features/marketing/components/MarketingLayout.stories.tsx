// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { MarketingLayout } from "./MarketingLayout";

/**
 * MarketingLayout — full page orchestrator.
 * Sticky bowtie SVG at top + stage tabs + dispatcher + activity footer.
 *
 * NOTE: requires nuqs NuqsAdapter in preview (set in .storybook/preview.tsx).
 * NOTE: React Query QueryClientProvider also required in preview.
 */
const meta: Meta<typeof MarketingLayout> = {
  title: "Marketing/MarketingLayout",
  component: MarketingLayout,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "fullscreen",
    docs: {
      description: {
        component:
          "Orchestrates bowtie SVG (sticky top) + 5-tab stage nav + stage content + activity footer. Consumes useBowtieSummary data hook and nuqs URL state.",
      },
    },
  },
};
export default meta;

type Story = StoryObj<typeof MarketingLayout>;

/**
 * Default layout — will show loading state until API resolves.
 * In Storybook, API is mocked by MSW handlers.
 */
export const Default: Story = {
  args: {},
  name: "Default layout",
};
