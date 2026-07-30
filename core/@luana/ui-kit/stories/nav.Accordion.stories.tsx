import type { Meta, StoryObj } from "@storybook/nextjs";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "../src/accordion";

const meta = {
  title: "Molecules/Accordion",
  component: Accordion,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Accordion` organiza contenido en secciones **expand/collapse** donde el usuario puede abrir múltiples a la vez (`type='multiple'`) o solo una (`type='single'`). Ideal para FAQs, configuraciones agrupadas con muchas opciones (≥15 ítems donde el scroll se vuelve confuso), o secciones opcionales en un formulario largo.",
          "",
          "Nota del form-runtime: arrays de ≥15 ítems con búsqueda/import batch son el único caso donde `renderAs: 'accordion'` está justificado. Para arrays más pequeños usa `cards` (≤3 sub-campos) o `split` (≥4).",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Pocas secciones paralelas de igual jerarquía** → usa `Tabs` (más visible y directa).",
          "- **Un solo item que se puede expandir** → usa `Collapsible` (más ligero, semántica más precisa).",
          "- **Secciones en una lista/detalle** → usa `EntitySubNavBar` (navegación por URL).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Accordion>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Accordion type="single" collapsible className="w-96">
      <AccordionItem value="item-1">
        <AccordionTrigger>¿Qué incluye la consulta cardiológica?</AccordionTrigger>
        <AccordionContent>
          Evaluación cardiovascular completa con electrocardiograma (ECG), medición de presión
          arterial y oximetría de pulso. Duración: 45 minutos.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>¿Se aceptan coberturas médicas?</AccordionTrigger>
        <AccordionContent>
          Sí. Trabajamos con OSDE, Swiss Medical, Galeno, Medifé y más de 20 coberturas.
          Consulta la lista actualizada en el momento de agendar.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>¿Cómo cancelo o reprogramo un turno?</AccordionTrigger>
        <AccordionContent>
          Puedes cancelar o reprogramar hasta 24 horas antes del turno sin cargo. Pasado ese
          plazo, se aplica la política de cancelación tardía.
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  ),
};

export const Multiplo: Story = {
  name: "Múltiple (varios abiertos)",
  render: () => (
    <Accordion type="multiple" className="w-96" defaultValue={["conf-1", "conf-2"]}>
      <AccordionItem value="conf-1">
        <AccordionTrigger>Notificaciones</AccordionTrigger>
        <AccordionContent className="space-y-2 text-sm">
          <p>Recordatorios: 48h y 2h antes del turno.</p>
          <p>Canal: WhatsApp y correo electrónico.</p>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="conf-2">
        <AccordionTrigger>Política de cancelación</AccordionTrigger>
        <AccordionContent className="text-sm">
          Cancelación gratuita hasta 24h antes. Con menos de 24h, se retiene el 50% del valor.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="conf-3">
        <AccordionTrigger>Pagos aceptados</AccordionTrigger>
        <AccordionContent className="text-sm">
          Efectivo, transferencia bancaria, tarjeta de crédito/débito y MercadoPago.
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  ),
};
