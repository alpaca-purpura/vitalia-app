import type { Preview } from "@storybook/nextjs";
import "../src/app/globals.css";

/**
 * Vitalia Storybook preview config.
 *
 * - Imports globals.css so vt-* CSS utility classes + design tokens are available.
 * - Background palette uses Vitalia brand tokens (F7F9FC = --vitalia-bg).
 * - No hsl() literals here — tokens live in globals.css.
 */
const preview: Preview = {
  parameters: {
    backgrounds: {
      default: "vitalia-bg",
      values: [
        { name: "vitalia-bg", value: "#F7F9FC" },
        { name: "vitalia-surface", value: "#FFFFFF" },
        { name: "vitalia-azul-marino", value: "#180D95" },
        { name: "dark", value: "#1A1F36" },
      ],
    },
    a11y: {
      // a11y addon enabled globally — HIPAA-lite mandate accessible UI
      config: {},
      options: {
        checks: { "color-contrast": { options: { noScroll: true } } },
        restoreScroll: true,
      },
    },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
};

export default preview;
