import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";

import {
  DetailPanel,
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from "../src/detail-panel";
import { Button } from "../src/button";
import { Badge } from "../src/badge";

const meta = {
  title: "Molecules/DetailPanel",
  component: DetailPanel,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`DetailPanel` es el panel lateral deslizante (slide-over) para mostrar el detalle de una entidad seleccionada en un listado: paciente, cita, lead, producto. Monta en `document.body` via `createPortal`; usa animación de entrada/salida y gestión de foco automática. Composible con `DetailPanelHeader`, `DetailPanelTitle` y `DetailPanelClose`.",
          "",
          "Tamaños: `sm` (400 px), `md` (550 px), `lg` (650 px).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Confirmaciones simples** → usa `Dialog` (Radix AlertDialog, §2.8 del canon).",
          "- **Formulario multilargo que reemplaza la página** → usa una ruta dedicada con `DetailLayout`.",
          "- **Menú contextual** → usa `DropdownMenu`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof DetailPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  name: "Panel de paciente (sm)",
  render: () => {
    const [open, setOpen] = React.useState(true);
    return (
      <div className="relative min-h-[420px]">
        <Button variant="outline" onClick={() => setOpen(true)}>
          Abrir panel
        </Button>
        <DetailPanel open={open} onClose={() => setOpen(false)} size="sm">
          <DetailPanelHeader>
            <div className="flex items-center justify-between">
              <DetailPanelTitle>Dr. Marcos Gutiérrez</DetailPanelTitle>
              <DetailPanelClose onClose={() => setOpen(false)} />
            </div>
            <p className="text-sm text-muted-foreground">Cardiología · Matrícula 12456</p>
          </DetailPanelHeader>

          <div className="flex flex-col gap-5 px-6 pt-4 pb-8">
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Estado</span>
              <Badge variant="default" className="w-fit">Activo</Badge>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Próxima cita</span>
              <span className="text-sm">Lunes 23 jun · 10:30 AM (America/Buenos_Aires)</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Consultorio</span>
              <span className="text-sm">Av. Rivadavia 1200, CABA · Piso 3, Of. 304</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Pacientes este mes</span>
              <span className="text-sm font-semibold">48</span>
            </div>
          </div>
        </DetailPanel>
      </div>
    );
  },
};

export const TamanoMedio: Story = {
  name: "Tamaño md — detalle de cita",
  render: () => {
    const [open, setOpen] = React.useState(true);
    return (
      <div className="relative min-h-[420px]">
        <Button variant="outline" onClick={() => setOpen(true)}>
          Abrir panel
        </Button>
        <DetailPanel open={open} onClose={() => setOpen(false)} size="md">
          <DetailPanelHeader>
            <div className="flex items-center justify-between">
              <DetailPanelTitle>Cita #C-2847</DetailPanelTitle>
              <DetailPanelClose onClose={() => setOpen(false)} />
            </div>
            <p className="text-sm text-muted-foreground">Solicitada el 20 jun 2026</p>
          </DetailPanelHeader>

          <div className="flex flex-col gap-5 px-6 pt-4 pb-8">
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Paciente</span>
                <span className="text-sm">Laura Castillo</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Especialidad</span>
                <span className="text-sm">Nutrición</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Fecha</span>
                <span className="text-sm">23 jun 2026 · 09:00</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Modalidad</span>
                <Badge variant="secondary" className="w-fit">Videollamada</Badge>
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Motivo</span>
              <span className="text-sm">Seguimiento control de peso — 3er mes programa metabólico.</span>
            </div>
            <div className="flex gap-2 pt-2">
              <Button size="sm">Confirmar</Button>
              <Button size="sm" variant="outline">Reprogramar</Button>
            </div>
          </div>
        </DetailPanel>
      </div>
    );
  },
};

export const Cerrado: Story = {
  name: "Cerrado (punto de partida)",
  render: () => {
    const [open, setOpen] = React.useState(false);
    return (
      <div className="min-h-[200px] flex items-start gap-4">
        <Button variant="outline" onClick={() => setOpen(true)}>
          Abrir panel de detalle
        </Button>
        <span className="text-sm text-muted-foreground mt-2">El panel no está montado hasta hacer clic.</span>
        <DetailPanel open={open} onClose={() => setOpen(false)} size="sm">
          <DetailPanelHeader>
            <div className="flex items-center justify-between">
              <DetailPanelTitle>Detalle de ejemplo</DetailPanelTitle>
              <DetailPanelClose onClose={() => setOpen(false)} />
            </div>
          </DetailPanelHeader>
          <div className="px-6 pt-4">
            <p className="text-sm text-muted-foreground">Contenido del panel.</p>
          </div>
        </DetailPanel>
      </div>
    );
  },
};
