// cap: patients.nps-tracking
// story-origin: TBD
/**
 * FidelizacionKPIsHero — Storybook stories.
 *
 * Covers:
 *   - Loading state (skeleton pulse animation)
 *   - Populated state with representative KPI values
 *   - Zero-values edge case (all zeros)
 *   - Negative trends (near abandonment spike)
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { FidelizacionKPIsHero } from "./FidelizacionKPIsHero";
import type { FidelizacionSummaryResponse } from "../types/fidelizacion-summary";

const MOCK_SUMMARY: FidelizacionSummaryResponse = {
  patientsInFollowup: 142,
  nearAbandonment: 18,
  returnRate: 0.73,
  reEngagedThisPeriod: 31,
  npsAverage: 8.4,
  npsResponsesCount: 56,
  trendVsPreviousPeriod: {
    patientsInFollowup: 12,
    nearAbandonment: -3,
    returnRate: 0.05,
    reEngagedThisPeriod: 8,
    npsAverage: 0.2,
  },
};

const meta: Meta<typeof FidelizacionKPIsHero> = {
  title: "Features/Fidelizacion/FidelizacionKPIsHero",
  component: FidelizacionKPIsHero,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
  argTypes: {
    isPending: {
      description: "Shows skeleton placeholders when true.",
      control: { type: "boolean" },
    },
    data: {
      description: "KPI summary data — null/undefined triggers empty state.",
      control: false,
    },
    className: { control: false },
  },
};

export default meta;

type Story = StoryObj<typeof FidelizacionKPIsHero>;

/** Estado de carga — muestra skeletons animados */
export const Loading: Story = {
  name: "Cargando (skeleton)",
  args: {
    isPending: true,
    data: null,
  },
};

/** Estado poblado con valores representativos */
export const Populated: Story = {
  name: "Datos cargados",
  args: {
    isPending: false,
    data: MOCK_SUMMARY,
  },
};

/** Caso borde: todos los KPIs en cero */
export const ZeroValues: Story = {
  name: "Valores en cero (inicio de período)",
  args: {
    isPending: false,
    data: {
      patientsInFollowup: 0,
      nearAbandonment: 0,
      returnRate: 0,
      reEngagedThisPeriod: 0,
      npsAverage: 0,
      npsResponsesCount: 0,
      trendVsPreviousPeriod: {
        patientsInFollowup: 0,
        nearAbandonment: 0,
        returnRate: 0,
        reEngagedThisPeriod: 0,
        npsAverage: 0,
      },
    } satisfies FidelizacionSummaryResponse,
  },
};

/** Tendencia negativa — abandono en aumento */
export const NegativeTrend: Story = {
  name: "Tendencia negativa (abandono alto)",
  args: {
    isPending: false,
    data: {
      ...MOCK_SUMMARY,
      nearAbandonment: 47,
      trendVsPreviousPeriod: {
        ...MOCK_SUMMARY.trendVsPreviousPeriod,
        nearAbandonment: 29,
        returnRate: -0.12,
      },
    } satisfies FidelizacionSummaryResponse,
  },
};
