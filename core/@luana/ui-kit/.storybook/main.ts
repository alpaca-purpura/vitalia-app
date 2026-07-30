import type { StorybookConfig } from "@storybook/nextjs";

/**
 * @luana/ui-kit Storybook — platform design-system surface (story core-ds-foundation T-2).
 *
 * Renders the REAL kit components from src/ (stories CONSUME, never copy). The
 * @storybook/nextjs framework is mandatory: EntityWorkspaceLayout/EntitySubNavBar use
 * next/navigation hooks (useParams/useRouter/usePathname) — @storybook/nextjs mocks them.
 *
 * Stories live in ../stories/ (NOT co-located in src/) so authoring stories never
 * touches the component source tree.
 *
 * react-docgen-typescript drives the autodocs props table (ticket T-2 deliverable:
 * "código + props por story"). Declared explicitly so the props table never silently
 * falls back to the weaker react-docgen.
 */
const config: StorybookConfig = {
  stories: ["../stories/**/*.stories.@(ts|tsx)"],
  // Demo avatar assets (real vitalia agent thumbnails) served at /sb-assets so the
  // shell catalog stories render the production faces. Self-contained: the PNGs live
  // in stories/assets (copied, not referenced cross-package).
  staticDirs: [{ from: "../stories/assets", to: "/sb-assets" }],
  addons: ["@storybook/addon-docs", "@storybook/addon-a11y"],
  framework: {
    name: "@storybook/nextjs",
    options: {},
  },
  typescript: {
    reactDocgen: "react-docgen-typescript",
    reactDocgenTypescriptOptions: {
      shouldExtractLiteralValuesFromEnum: true,
      shouldRemoveUndefinedFromOptional: true,
      // Only document props declared on the component's own interface, not inherited
      // DOM-attribute soup from React.HTMLAttributes.
      propFilter: (prop) =>
        prop.parent ? !/node_modules/.test(prop.parent.fileName) : true,
    },
  },
  docs: {
    autodocs: "tag",
  },
};

export default config;
