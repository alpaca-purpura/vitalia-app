import type { Meta, StoryObj } from "@storybook/nextjs";
import { CalendarDays } from "lucide-react";

import { Popover, PopoverContent, PopoverTrigger } from "../src/popover";
import { Button } from "../src/button";

const meta = {
  title: "Molecules/Popover",
  component: Popover,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Popover` muestra contenido contextual **anclado a un elemento** sin interrumpir el flujo: filtros de fecha, información adicional de un campo, mini-formularios de edición inline (cambiar estado, asignar profesional). No es blocking — el usuario puede hacer clic afuera para cerrarlo.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Para información solo de lectura en hover** → usa `Tooltip` (más ligero, solo texto).",
          "- **Para acciones destructivas o confirmaciones** → usa `Dialog` o `AlertDialog` (son blocking intencionalmente).",
          "- **Para un menú de acciones** → usa `DropdownMenu`.",
          "- **Para formularios largos** → usa `Sheet`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Popover>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story clave: popover ABIERTO para revisión
export const Abierto: Story = {
  name: "Abierto (revisión directa)",
  render: () => (
    <div className="flex items-start justify-center pt-8">
      <Popover open>
        <PopoverTrigger asChild>
          <Button variant="outline">
            <CalendarDays className="mr-2 h-4 w-4" />
            Seleccionar fecha
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-72">
          <div className="grid gap-3">
            <div className="space-y-1">
              <h4 className="font-medium text-sm">Rango de fechas</h4>
              <p className="text-xs text-muted-foreground">
                Filtra los turnos por rango de fechas.
              </p>
            </div>
            <div className="grid gap-2">
              <div className="grid grid-cols-3 items-center gap-2">
                <label className="text-xs" htmlFor="pop-from">
                  Desde
                </label>
                <input
                  id="pop-from"
                  type="date"
                  className="col-span-2 h-8 rounded-control border border-input px-2 text-xs"
                  defaultValue="2026-06-01"
                />
              </div>
              <div className="grid grid-cols-3 items-center gap-2">
                <label className="text-xs" htmlFor="pop-to">
                  Hasta
                </label>
                <input
                  id="pop-to"
                  type="date"
                  className="col-span-2 h-8 rounded-control border border-input px-2 text-xs"
                  defaultValue="2026-06-30"
                />
              </div>
            </div>
            <Button size="sm">Aplicar filtro</Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  ),
  parameters: {
    layout: "padded",
    docs: {
      description: {
        story:
          "Popover forzado `open` para revisión directa. Muestra un filtro de rango de fechas anclado al trigger.",
      },
    },
  },
};

export const ConTrigger: Story = {
  name: "Con trigger interactivo",
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline">Filtrar por fecha</Button>
      </PopoverTrigger>
      <PopoverContent className="w-60">
        <p className="text-sm text-muted-foreground">Selecciona un rango para filtrar los turnos.</p>
      </PopoverContent>
    </Popover>
  ),
};
