import type { Meta, StoryObj } from "@storybook/nextjs";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "../src/tabs";

const meta = {
  title: "Organisms/Tabs",
  component: Tabs,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Tabs` organiza **secciones de contenido paralelas y de igual jerarquía** dentro de la misma página, donde el usuario alterna entre ellas. Ideal para el detalle de un paciente (historial / turnos / documentos), la configuración de un servicio (general / disponibilidad / precios), o paneles de análisis.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Navegación entre páginas de la app** → usa la barra de navegación lateral o `EntitySubNavBar` (que ya usa Tabs internamente para el detalle de una entidad en la arquitectura lista/detalle del canon).",
          "- **Contenido que se expande/colapsa** → usa `Accordion` (el usuario puede ver múltiples secciones abiertas simultáneamente).",
          "- **Pasos secuenciales** → usa un stepper, no Tabs (los tabs no implican orden).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Tabs>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Tabs defaultValue="historial" className="w-96">
      <TabsList>
        <TabsTrigger value="historial">Historial</TabsTrigger>
        <TabsTrigger value="turnos">Turnos</TabsTrigger>
        <TabsTrigger value="documentos">Documentos</TabsTrigger>
      </TabsList>
      <TabsContent value="historial" className="mt-4">
        <div className="rounded-lg border p-4 text-sm">
          <p className="font-medium">Última consulta: 15 jun 2026</p>
          <p className="text-muted-foreground mt-1">
            Revisión de cardiología. Sin novedades. Control en 6 meses.
          </p>
        </div>
      </TabsContent>
      <TabsContent value="turnos" className="mt-4">
        <div className="rounded-lg border p-4 text-sm">
          <p className="font-medium">Próximo turno: 22 jun 2026 · 14:30</p>
          <p className="text-muted-foreground mt-1">Dra. Valentina Suárez · Cardiología</p>
        </div>
      </TabsContent>
      <TabsContent value="documentos" className="mt-4">
        <div className="rounded-lg border p-4 text-sm text-muted-foreground">
          Sin documentos adjuntos.
        </div>
      </TabsContent>
    </Tabs>
  ),
};

export const Configuracion: Story = {
  name: "Configuración de servicio",
  render: () => (
    <Tabs defaultValue="general" className="w-96">
      <TabsList className="w-full">
        <TabsTrigger value="general" className="flex-1">General</TabsTrigger>
        <TabsTrigger value="disponibilidad" className="flex-1">Disponibilidad</TabsTrigger>
        <TabsTrigger value="precios" className="flex-1">Precios</TabsTrigger>
      </TabsList>
      <TabsContent value="general" className="mt-4 space-y-2">
        <p className="text-sm font-medium">Consulta cardiológica · 45 min</p>
        <p className="text-sm text-muted-foreground">Modalidad: presencial y teleconsulta</p>
      </TabsContent>
      <TabsContent value="disponibilidad" className="mt-4">
        <p className="text-sm text-muted-foreground">Lun, Mié, Vie · 8:00 – 17:00</p>
      </TabsContent>
      <TabsContent value="precios" className="mt-4">
        <p className="text-sm text-muted-foreground">ARS 18.500 · sin cobertura</p>
      </TabsContent>
    </Tabs>
  ),
};
