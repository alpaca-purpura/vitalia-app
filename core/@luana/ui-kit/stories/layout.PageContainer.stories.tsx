import type { Meta, StoryObj } from "@storybook/nextjs";

import { PageContainer } from "../src/layout/page";

const meta = {
  title: "Templates/PageContainer",
  component: PageContainer,
  tags: ["autodocs"],
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es el **envoltorio de padding estándar de toda hoja**. Aplica `px-6 py-5` (≈1.25rem · 1.5rem) para que el contenido no quede pegado a los bordes del shell. Úsalo en cualquier hoja que tenga contenido propio (formularios, listas, dashboards).",
          "",
          "Por convención se combina con `<PageContentStack>` para el espaciado vertical entre bloques.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** lo uses para la franja N3 (`EntitySubNavBar`) — esa debe ser full-bleed (canon §2.2).",
          "- **No** lo envuelvas con otro `<PageContainer>` — sólo uno por hoja.",
          "- Si solo necesitas apilar bloques con espacio entre ellos (sin padding exterior), usa `<PageContentStack>` directamente.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof PageContainer>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: (
      <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
        Contenido de la hoja. El relleno visible de los bordes es el padding de{" "}
        <code>PageContainer</code>.
      </div>
    ),
  },
};
