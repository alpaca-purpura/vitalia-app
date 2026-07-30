import type { Meta, StoryObj } from "@storybook/nextjs";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../src/card";
import { Button } from "../src/button";
import { Badge } from "../src/badge";

const meta = {
  title: "Atoms/Card",
  component: Card,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Card` es el contenedor de contenido agrupado del design system. Úsalo para métricas en un dashboard, resúmenes informativos, widgets de configuración, o cualquier bloque de contenido que necesite delimitación visual.",
          "",
          "La anatomía es: `CardHeader` (título + descripción opcional) + `CardContent` (cuerpo) + `CardFooter` (acciones).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Para ítems de una lista/detalle** → usa `EntityInfoCard` (tiene acciones kebab, avatar, métricas, estado ya integrados).",
          "- **Para agrupar campos de formulario** → usa `Group` con `GroupHeader` (tiene acento de agente y semántica de error).",
          "- **Para contenido de página completa** → el contenedor de hoja es `PageContainer` + `PageContentStack`, no una Card.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="w-80">
      <CardHeader>
        <CardTitle>Resumen del mes</CardTitle>
        <CardDescription>Junio 2026 · Clínica Vitalia</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-2xl font-bold">248</p>
            <p className="text-xs text-muted-foreground">Pacientes atendidos</p>
          </div>
          <div>
            <p className="text-2xl font-bold">12</p>
            <p className="text-xs text-muted-foreground">Profesionales activos</p>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button variant="outline" size="sm">
          Ver reporte completo
        </Button>
      </CardFooter>
    </Card>
  ),
};

export const Servicio: Story = {
  name: "Tarjeta de servicio",
  render: () => (
    <Card className="w-72">
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle className="text-base">Consulta cardiológica</CardTitle>
          <Badge variant="default">Activo</Badge>
        </div>
        <CardDescription>Duración: 45 min · Modalidad: presencial</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Evaluación cardiovascular completa con ECG y medición de presión arterial.
        </p>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button size="sm">Agendar</Button>
        <Button size="sm" variant="ghost">
          Editar
        </Button>
      </CardFooter>
    </Card>
  ),
};
