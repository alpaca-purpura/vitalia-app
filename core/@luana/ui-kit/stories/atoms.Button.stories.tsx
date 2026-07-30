import type { Meta, StoryObj } from "@storybook/nextjs";
import { Plus, Trash2, Loader2 } from "lucide-react";

import { Button } from "../src/button";

const meta = {
  title: "Atoms/Button",
  component: Button,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Button` es el átomo de acción principal del design system. Úsalo para **cualquier acción del usuario**: guardar, confirmar, cancelar, eliminar, navegar. Tiene seis variantes CVA (`default`, `destructive`, `outline`, `secondary`, `ghost`, `link`) y cuatro tamaños (`sm`, `default`, `lg`, `icon`).",
          "",
          "- **`default`** — acción primaria de la pantalla (máximo 1 por bloque visual).",
          "- **`outline`** — acción secundaria o alternativa.",
          "- **`destructive`** — eliminar, dar de baja, acción irreversible.",
          "- **`ghost`** — acciones de baja jerarquía, dentro de tablas o listas.",
          "- **`link`** — navegación inline dentro de texto.",
          "- **`secondary`** — terciario, complemento del primario.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** uses `Button` para un enlace de navegación estándar → usa `<Link>` de Next.js (con `asChild`).",
          "- **No** uses `Button` para acciones de carga asíncrona sin indicador → usa `LoadingButton` (tiene spinner integrado).",
          "- **No** crees un botón desde cero con `<div onClick>` — accesibilidad y focus management ya están resueltos en este componente.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

// Galería completa de variantes
export const Galeria: Story = {
  name: "Galería de variantes",
  render: () => (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-3 items-center">
        <Button variant="default">Agendar turno</Button>
        <Button variant="secondary">Ver historial</Button>
        <Button variant="outline">Cancelar</Button>
        <Button variant="ghost">Editar</Button>
        <Button variant="destructive">Eliminar paciente</Button>
        <Button variant="link">Ver detalle</Button>
      </div>
      <div className="flex flex-wrap gap-3 items-center">
        <Button size="sm">Pequeño</Button>
        <Button size="default">Normal</Button>
        <Button size="lg">Grande</Button>
        <Button size="icon" aria-label="Agregar">
          <Plus />
        </Button>
      </div>
      <div className="flex flex-wrap gap-3 items-center">
        <Button disabled>Deshabilitado</Button>
        <Button variant="outline" disabled>
          Outline deshabilitado
        </Button>
      </div>
    </div>
  ),
  parameters: {
    layout: "padded",
    docs: {
      description: {
        story:
          "Vista rápida de las seis variantes, cuatro tamaños, estado deshabilitado y botón ícono.",
      },
    },
  },
};

export const Default: Story = {
  args: {
    children: "Confirmar turno",
    variant: "default",
  },
};

export const ConIcono: Story = {
  name: "Con ícono",
  render: () => (
    <div className="flex gap-3">
      <Button>
        <Plus />
        Agregar servicio
      </Button>
      <Button variant="destructive">
        <Trash2 />
        Eliminar
      </Button>
    </div>
  ),
};

export const Cargando: Story = {
  name: "Estado cargando (simulado)",
  render: () => (
    <Button disabled>
      <Loader2 className="animate-spin" />
      Guardando...
    </Button>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "Para acciones asíncronas considera `LoadingButton` que maneja el estado de carga internamente.",
      },
    },
  },
};
