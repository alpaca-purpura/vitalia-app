import type { Meta, StoryObj } from "@storybook/nextjs";

import { Separator } from "../src/separator";

const meta = {
  title: "Atoms/Separator",
  component: Separator,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Separator` es una línea divisoria semántica (`<hr>` accesible con `role='separator'`). Úsalo para separar secciones dentro de un menú, una lista de opciones, o un bloque de contenido cuando el espacio en blanco no es suficiente para distinguir las áreas.",
          "",
          "Soporta orientación `horizontal` (defecto) y `vertical`.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- Si solo necesitás espacio entre elementos → usa `gap` de Tailwind, no un Separator.",
          "- Para separar páginas completas → usa `PageSection` con su título.",
          "- Para separar ítems dentro de un menú → el `DropdownMenuSeparator` ya lo incluye.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Separator>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Horizontal: Story = {
  render: () => (
    <div className="w-64 space-y-3">
      <div className="text-sm font-medium">Configuración de cuenta</div>
      <Separator />
      <div className="text-sm text-muted-foreground">Perfil del profesional</div>
      <Separator />
      <div className="text-sm text-muted-foreground">Preferencias de notificación</div>
    </div>
  ),
};

export const Vertical: Story = {
  name: "Vertical (en fila)",
  render: () => (
    <div className="flex items-center gap-3 h-6">
      <span className="text-sm">Lunes</span>
      <Separator orientation="vertical" />
      <span className="text-sm">Miércoles</span>
      <Separator orientation="vertical" />
      <span className="text-sm">Viernes</span>
    </div>
  ),
};
