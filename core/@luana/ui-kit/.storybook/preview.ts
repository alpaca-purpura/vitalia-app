import type { Preview } from "@storybook/nextjs";
import "./preview.css";

/**
 * @luana/ui-kit Storybook preview (story core-ds-foundation T-2).
 *
 * - preview.css carries the full Tailwind v4 wiring + brand-agnostic token contract.
 * - nextjs.appDirectory:true so next/navigation hooks (useParams/useRouter/usePathname)
 *   used by EntityWorkspaceLayout/EntitySubNavBar are mocked under the App Router model.
 * - a11y enabled globally (kit components must stay accessible across all brands).
 */
const preview: Preview = {
  // Brand theme switcher — swaps the surface + shape token set (colores + formas)
  // per brand. The decorator sets [data-brand] on <html>; preview.css carries one
  // token block per brand. Same components, brand tokens → brand look.
  globalTypes: {
    brand: {
      description: "Marca — tokens de superficie + forma (colores + radios)",
      toolbar: {
        title: "Marca",
        icon: "paintbrush",
        items: [
          { value: "vitalia", title: "Vitalia · cian #01B2F8 · control 8px" },
          { value: "nicolify", title: "Nicolify · indigo #635BFF · control pill" },
        ],
        dynamicTitle: true,
      },
    },
  },
  initialGlobals: { brand: "vitalia" },
  decorators: [
    (Story, context) => {
      if (typeof document !== "undefined") {
        document.documentElement.setAttribute(
          "data-brand",
          String(context.globals.brand ?? "vitalia"),
        );
      }
      return Story();
    },
  ],
  parameters: {
    nextjs: {
      appDirectory: true,
    },
    // Viewport presets so shell stories can demo tablet/mobile. The shell reads
    // window.matchMedia (≥1024 inline split · <1024 supervisor drawer) → the iframe
    // width triggers the breakpoint; the viewport tool resizes that iframe.
    viewport: {
      options: {
        mobile: { name: "Mobile (390)", styles: { width: "390px", height: "844px" }, type: "mobile" },
        tablet: { name: "Tablet (834)", styles: { width: "834px", height: "1112px" }, type: "tablet" },
        desktop: { name: "Desktop (1280)", styles: { width: "1280px", height: "820px" }, type: "desktop" },
      },
    },
    backgrounds: {
      default: "surface",
      values: [
        { name: "surface", value: "#ffffff" },
        { name: "muted", value: "#f4f4f5" },
        { name: "dark", value: "#0a0a0b" },
      ],
    },
    a11y: {
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
