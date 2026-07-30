import type { Meta, StoryObj } from "@storybook/nextjs";

import { PageContentStack } from "../src/layout/page";

const meta = {
  title: "Templates/PageContentStack",
  component: PageContentStack,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es el **gestor de espaciado vertical uniforme** entre bloques de una hoja. Aplica `flex flex-col gap-6` para que todos los bloques hijos tengan el mismo espacio entre sí sin que cada bloque tenga que declarar `mt-*`.",
          "",
          "Envuelve el contenido que va dentro de `<PageContainer>` — la combinación canónica es `<PageContainer><PageContentStack>…</PageContentStack></PageContainer>`.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** lo uses para espaciar elementos DENTRO de un bloque (ej. campos de un formulario) — para eso usa `gap-*` directo o `<FormLayout>`.",
          "- **No** lo anides dentro de otro `<PageContentStack>` — produce doble gap.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof PageContentStack>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: (
      <>
        <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
          Bloque A (ej. PageHeader)
        </div>
        <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
          Bloque B (ej. Toolbar + grilla)
        </div>
        <div className="rounded-lg border border-border/60 bg-card p-4 text-sm text-muted-foreground">
          Bloque C (ej. Pagination)
        </div>
      </>
    ),
  },
};
