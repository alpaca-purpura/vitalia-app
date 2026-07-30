// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * NPSTagBadge — Storybook stories.
 *
 * Covers:
 *   - All three NPS categories (detractor 0-6, pasivo 7-8, promotor 9-10)
 *   - All three sizes (sm / md / lg)
 *   - All three shape variants (badge / chip / tag)
 *   - Null/undefined graceful fallback ("Sin NPS")
 *   - Score boundary values (0, 6, 7, 8, 9, 10)
 *
 * downstream-regression-na: vitalia-local Storybook artifact — no cross-brand consumers.
 */

import type { Meta, StoryObj } from "@storybook/nextjs";
import { NPSTagBadge } from "./NPSTagBadge";

const meta: Meta<typeof NPSTagBadge> = {
  title: "Shared/NPS/NPSTagBadge",
  component: NPSTagBadge,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
  argTypes: {
    score: {
      description: "NPS score 0–10. null/undefined renders fallback 'Sin NPS'.",
      control: { type: "number", min: 0, max: 10, step: 1 },
    },
    size: {
      description: "Visual size of the badge element.",
      control: { type: "select" },
      options: ["sm", "md", "lg"],
    },
    variant: {
      description:
        "Shape variant: badge (rounded), chip (pill), tag (squared).",
      control: { type: "select" },
      options: ["badge", "chip", "tag"],
    },
    className: { control: false },
  },
};

export default meta;

type Story = StoryObj<typeof NPSTagBadge>;

// ──────────────────────────────────────────────────────────────────────────────
// Category stories — score representative values
// ──────────────────────────────────────────────────────────────────────────────

/** Detractor (0-6) — rojo */
export const Detractor: Story = {
  name: "Detractor (score 5)",
  args: { score: 5, size: "md", variant: "badge" },
};

/** Pasivo (7-8) — amarillo */
export const Pasivo: Story = {
  name: "Pasivo (score 7)",
  args: { score: 7, size: "md", variant: "badge" },
};

/** Promotor (9-10) — verde */
export const Promotor: Story = {
  name: "Promotor (score 10)",
  args: { score: 10, size: "md", variant: "badge" },
};

// ──────────────────────────────────────────────────────────────────────────────
// Size variants
// ──────────────────────────────────────────────────────────────────────────────

/** Small — usado en filter chips compactos */
export const SizeSm: Story = {
  name: "Tamaño sm",
  args: { score: 9, size: "sm", variant: "badge" },
};

/** Medium — default; recomendado para la mayoría de usos */
export const SizeMd: Story = {
  name: "Tamaño md (default)",
  args: { score: 9, size: "md", variant: "badge" },
};

/** Large — para stat cards o encabezados de sección NPS */
export const SizeLg: Story = {
  name: "Tamaño lg",
  args: { score: 9, size: "lg", variant: "badge" },
};

// ──────────────────────────────────────────────────────────────────────────────
// Shape variants
// ──────────────────────────────────────────────────────────────────────────────

/** Badge (default) — bordes redondeados con --radius */
export const VariantBadge: Story = {
  name: "Variante badge (default)",
  args: { score: 8, size: "md", variant: "badge" },
};

/** Chip — pill shape; para inline filter chips */
export const VariantChip: Story = {
  name: "Variante chip (pill)",
  args: { score: 8, size: "md", variant: "chip" },
};

/** Tag — cuadrado (rounded-sm); para celdas de tabla compactas */
export const VariantTag: Story = {
  name: "Variante tag (cuadrado)",
  args: { score: 8, size: "md", variant: "tag" },
};

// ──────────────────────────────────────────────────────────────────────────────
// Boundary scores
// ──────────────────────────────────────────────────────────────────────────────

/** Score 0 — detractor extremo */
export const Score0: Story = {
  name: "Score 0 (detractor extremo)",
  args: { score: 0, size: "md", variant: "badge" },
};

/** Score 6 — límite superior detractor */
export const Score6: Story = {
  name: "Score 6 (límite detractor)",
  args: { score: 6, size: "md", variant: "badge" },
};

/** Score 7 — límite inferior pasivo */
export const Score7: Story = {
  name: "Score 7 (límite inferior pasivo)",
  args: { score: 7, size: "md", variant: "badge" },
};

/** Score 8 — límite superior pasivo */
export const Score8: Story = {
  name: "Score 8 (límite superior pasivo)",
  args: { score: 8, size: "md", variant: "badge" },
};

/** Score 9 — límite inferior promotor */
export const Score9: Story = {
  name: "Score 9 (límite inferior promotor)",
  args: { score: 9, size: "md", variant: "badge" },
};

// ──────────────────────────────────────────────────────────────────────────────
// Fallback — sin datos NPS
// ──────────────────────────────────────────────────────────────────────────────

/** Null — graceful fallback cuando paciente no ha respondido */
export const SinNPSNull: Story = {
  name: "Sin NPS (score null)",
  args: { score: null, size: "md", variant: "badge" },
};

/** Undefined — fallback idéntico a null */
export const SinNPSUndefined: Story = {
  name: "Sin NPS (score undefined)",
  args: { score: undefined, size: "md", variant: "badge" },
};
