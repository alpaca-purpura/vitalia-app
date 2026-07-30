// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { ReferralsWidget } from "./ReferralsWidget";

/**
 * ReferralsWidget — 3 KPI hero cards + top 5 referrer leaderboard.
 * SC-MK-02 (Expansión stage): referidos widget.
 * HIPAA-lite: leaderboard shows ONLY referrerPatientIdHash — NEVER patient.name.
 * States: loading · error · empty (referralsCount=0) · populated.
 */
const meta: Meta<typeof ReferralsWidget> = {
  title: "Marketing/ReferralsWidget",
  component: ReferralsWidget,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
    docs: {
      description: {
        component:
          "Panel de referidos HIPAA-lite: KPIs (total referidos, tasa de conversión, LTV promedio) + " +
          "leaderboard top 5 con hash anónimo de paciente (NUNCA nombre). " +
          "Fuente: useReferrals hook (dual filter tenant+clinic).",
      },
    },
  },
  argTypes: {
    period: {
      control: "radio",
      options: ["7d", "30d", "90d"],
      description: "Período de análisis",
    },
  },
};
export default meta;

type Story = StoryObj<typeof ReferralsWidget>;

/** Período últimos 7 días */
export const Period7d: Story = {
  args: { period: "7d" },
  name: "Período 7 días",
};

/** Período últimos 30 días (default) */
export const Period30d: Story = {
  args: { period: "30d" },
  name: "Período 30 días (default)",
};

/** Período últimos 90 días */
export const Period90d: Story = {
  args: { period: "90d" },
  name: "Período 90 días",
};
