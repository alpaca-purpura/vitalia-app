import type { Meta, StoryObj } from "@storybook/nextjs";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "../src/sheet";
import { Button } from "../src/button";
import { Input } from "../src/input";
import { Label } from "../src/label";

const meta = {
  title: "Organisms/Sheet",
  component: Sheet,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Sheet` es un panel lateral deslizante. Úsalo para **formularios largos o multistep**, edición de un registro complejo, y filtros avanzados que necesitan más espacio del que un Dialog o Popover pueden ofrecer. El usuario puede ver parcialmente el contexto original mientras trabaja.",
          "",
          "Puede abrirse desde cualquier lado (`side`: `right` [defecto], `left`, `top`, `bottom`).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Formulario corto (2-4 campos) o confirmación** → usa `Dialog` (menos intrusivo para tareas pequeñas).",
          "- **Menú de navegación mobile** → usa el componente de navigation propio.",
          "- **Información solo de lectura** → usa `Popover` o una sección expandible en la misma página.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Sheet>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story con sheet ABIERTO desde el lado derecho
export const Abierto: Story = {
  name: "Abierto — lateral derecho (revisión directa)",
  render: () => (
    <Sheet open>
      <SheetContent className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle>Editar perfil del profesional</SheetTitle>
          <SheetDescription>
            Actualiza los datos de la Dra. Valentina Suárez. Los cambios se guardan automáticamente.
          </SheetDescription>
        </SheetHeader>
        <div className="grid gap-4 py-6">
          <div className="grid gap-1.5">
            <Label htmlFor="sh-name">Nombre completo</Label>
            <Input id="sh-name" defaultValue="Dra. Valentina Suárez" />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="sh-specialty">Especialidad principal</Label>
            <Input id="sh-specialty" defaultValue="Cardiología" />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="sh-license">Número de matrícula</Label>
            <Input id="sh-license" defaultValue="MN 94523" />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="sh-email">Correo profesional</Label>
            <Input id="sh-email" type="email" defaultValue="v.suarez@clinicavitalia.com" />
          </div>
        </div>
        <SheetFooter>
          <Button variant="outline">Cancelar</Button>
          <Button>Guardar cambios</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  ),
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        story:
          "Sheet forzado `open` para revisión directa del layout y campos. En producción se abre con el trigger.",
      },
    },
  },
};

export const ConTrigger: Story = {
  name: "Con trigger interactivo",
  render: () => (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline">Editar profesional</Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Editar perfil</SheetTitle>
          <SheetDescription>Actualiza los datos del profesional.</SheetDescription>
        </SheetHeader>
        <div className="py-4">
          <div className="grid gap-1.5">
            <Label htmlFor="sh2-name">Nombre completo</Label>
            <Input id="sh2-name" defaultValue="Dr. Tomás Figueroa" />
          </div>
        </div>
        <SheetFooter>
          <Button>Guardar</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  ),
};
