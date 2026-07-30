import type { StorybookConfig } from "@storybook/nextjs";

/**
 * Vitalia Storybook config — v10 + Next.js framework.
 * Stories glob: src/components/**\/*.stories.@(ts|tsx)
 * Addons: a11y (HIPAA-lite accessibility) + essentials (bundled in storybook v10)
 */
const config: StorybookConfig = {
  stories: [
    "../src/components/**/*.stories.@(ts|tsx)",
    "../src/features/**/*.stories.@(ts|tsx)",
  ],
  addons: [
    "@storybook/addon-a11y",
  ],
  framework: {
    name: "@storybook/nextjs",
    options: {},
  },
  docs: {
    autodocs: "tag",
  },
};

export default config;
