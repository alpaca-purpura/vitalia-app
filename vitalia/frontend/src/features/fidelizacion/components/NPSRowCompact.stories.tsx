// cap: patients.nps-tracking
// story-origin: TBD
/**
 * NPSRowCompact — Storybook stories.
 *
 * Covers:
 *   - Promotor con comentario
 *   - Detractor sin comentario
 *   - Pasivo con comentario largo (truncado)
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { NPSRowCompact } from "./NPSRowCompact";
import type { NPSRowDTO } from "../types/nps";

const PROMOTOR_ROW: NPSRowDTO = {
  id: "nps-001",
  patientName: "Laura Gómez",
  score: 10,
  band: "promoter",
  commentShort: "Excelente atención, muy recomendado.",
  respondedAt: "2025-05-10T14:30:00-03:00",
  taggedInInbox: false,
};

const DETRACTOR_ROW: NPSRowDTO = {
  id: "nps-002",
  patientName: "Juan Torres",
  score: 3,
  band: "detractor",
  commentShort: null,
  respondedAt: "2025-05-09T09:15:00-03:00",
  taggedInInbox: true,
};

const PASIVO_ROW: NPSRowDTO = {
  id: "nps-003",
  patientName: "Claudia Fernández",
  score: 7,
  band: "passive",
  commentShort:
    "El servicio estuvo bien pero los tiempos de espera podrían mejorar un poco.",
  respondedAt: "2025-05-08T16:45:00-03:00",
  taggedInInbox: false,
};

const meta: Meta<typeof NPSRowCompact> = {
  title: "Features/Fidelizacion/NPSRowCompact",
  component: NPSRowCompact,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
    nextjs: { appDirectory: true },
  },
  decorators: [
    (Story) => (
      <ul className="max-w-md">
        <Story />
      </ul>
    ),
  ],
  argTypes: {
    row: { control: false },
    className: { control: false },
  },
};

export default meta;

type Story = StoryObj<typeof NPSRowCompact>;

/** Promotor — score 10 con comentario positivo */
export const Promotor: Story = {
  name: "Promotor (score 10 con comentario)",
  args: { row: PROMOTOR_ROW },
};

/** Detractor — score 3 sin comentario, tagged en inbox */
export const Detractor: Story = {
  name: "Detractor (score 3 sin comentario)",
  args: { row: DETRACTOR_ROW },
};

/** Pasivo — score 7 con comentario largo */
export const Pasivo: Story = {
  name: "Pasivo (score 7 con comentario largo)",
  args: { row: PASIVO_ROW },
};
