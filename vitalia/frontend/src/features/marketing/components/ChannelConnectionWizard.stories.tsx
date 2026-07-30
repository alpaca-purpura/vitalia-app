// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { ChannelConnectionWizard } from "./ChannelConnectionWizard";

/**
 * ChannelConnectionWizard — 3-step OAuth connection wizard.
 * SC-MK-02: channel connection flow.
 * Step 1: selector de proveedor · Step 2: OAuth redirect · Step 3: confirmación.
 * Security: OAuth via full-page nav (window.location.href), NUNCA window.open popup.
 */
const meta: Meta<typeof ChannelConnectionWizard> = {
  title: "Marketing/ChannelConnectionWizard",
  component: ChannelConnectionWizard,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "fullscreen",
  },
  args: {
    open: true,
    onClose: () => {},
    onSuccess: () => {},
    // Inject test URL to prevent actual OAuth navigation in Storybook
    _testAuthorizationUrl: "#storybook-oauth-mock",
  },
};
export default meta;

type Story = StoryObj<typeof ChannelConnectionWizard>;

/** Paso 1: Selector de proveedor — estado inicial del wizard */
export const Step1Selector: Story = {
  args: { open: true },
  name: "Paso 1 — Selector de proveedor",
};

/** Wizard cerrado — no renderiza (open=false) */
export const Closed: Story = {
  args: { open: false },
  name: "Cerrado — no renderiza (open=false)",
  parameters: {
    docs: {
      description: {
        story:
          "Cuando open=false el componente retorna null. Estado de reposo.",
      },
    },
  },
};
