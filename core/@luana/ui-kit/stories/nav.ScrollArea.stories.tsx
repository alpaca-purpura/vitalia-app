import type { Meta, StoryObj } from "@storybook/nextjs";

import { ScrollArea } from "../src/scroll-area";
import { Separator } from "../src/separator";

const PACIENTES = [
  { nombre: "Valentina Suárez", especialidad: "Cardiología", hora: "08:00" },
  { nombre: "Tomás Figueroa", especialidad: "Dermatología", hora: "08:30" },
  { nombre: "Lucía Mendoza", especialidad: "Neurología", hora: "09:00" },
  { nombre: "Andrés Herrera", especialidad: "Cardiología", hora: "09:30" },
  { nombre: "Camila Torres", especialidad: "Endocrinología", hora: "10:00" },
  { nombre: "Diego Castillo", especialidad: "Ginecología", hora: "10:30" },
  { nombre: "Paula Morales", especialidad: "Dermatología", hora: "11:00" },
  { nombre: "Sebastián Ruiz", especialidad: "Neurología", hora: "11:30" },
  { nombre: "Natalia Vega", especialidad: "Cardiología", hora: "12:00" },
  { nombre: "Federico Álvarez", especialidad: "Dermatología", hora: "12:30" },
];

const meta = {
  title: "Atoms/ScrollArea",
  component: ScrollArea,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`ScrollArea` crea una región con scroll con scrollbar personalizada del design system (delgada, con thumb redondeado). Úsala cuando necesitás limitar la altura de un contenedor y hacer scroll dentro de él: lista de turnos del día, resultados de búsqueda en un Popover, historial de mensajes, lista de notificaciones.",
          "",
          "Soporta orientación `vertical` (defecto) y `horizontal`.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Scroll de la página completa** → el scroll nativo del browser es lo correcto.",
          "- **Lista virtualizada de miles de ítems** → considera una solución de windowing (react-virtual) ya que `ScrollArea` no virtualiza.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof ScrollArea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <ScrollArea className="h-64 w-72 rounded-md border">
      <div className="p-4">
        <h4 className="mb-4 text-sm font-medium leading-none">Agenda del día — 22 jun</h4>
        {PACIENTES.map((p, i) => (
          <div key={p.nombre}>
            <div className="text-sm">
              <span className="font-medium tabular-nums">{p.hora}</span>
              <span className="ml-3">{p.nombre}</span>
              <p className="text-xs text-muted-foreground ml-10">{p.especialidad}</p>
            </div>
            {i < PACIENTES.length - 1 && <Separator className="my-2" />}
          </div>
        ))}
      </div>
    </ScrollArea>
  ),
};

export const Horizontal: Story = {
  name: "Scroll horizontal",
  render: () => (
    <ScrollArea className="w-72 whitespace-nowrap rounded-md border">
      <div className="flex w-max space-x-4 p-4">
        {PACIENTES.map((p) => (
          <div key={p.nombre} className="w-40 shrink-0 rounded-md border p-3">
            <p className="text-xs font-medium">{p.hora}</p>
            <p className="text-sm mt-1 truncate">{p.nombre}</p>
            <p className="text-xs text-muted-foreground truncate">{p.especialidad}</p>
          </div>
        ))}
      </div>
    </ScrollArea>
  ),
};
