import type { Meta, StoryObj } from "@storybook/nextjs";

import { CollapsibleSection } from "../src/CollapsibleSection";
import { Input } from "../src/input";
import { Label } from "../src/label";
import { Textarea } from "../src/textarea";

const meta = {
  title: "Molecules/CollapsibleSection",
  component: CollapsibleSection,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`CollapsibleSection` es la molécula para agrupar campos de un formulario en secciones colapsables: Brand Studio, Offer Studio, configuración de perfil. Cada sección tiene: barra de acento (token de agente), header colapsable con título + resumen + chevron, y opcionalmente una alerta inline de campos faltantes (`missingFields`).",
          "",
          "Compone `Accordion` (Radix UI, single collapsible) + `Group`/`GroupHeader` del design system. Token-driven: `accentVar` / `accentClass` controlan el color lateral; NUNCA hex directo.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Sección siempre visible** → usa `Group` directamente (sin `CollapsibleSection`).",
          "- **Navegación entre secciones largas** → usa `Tabs` o el `EntitySubNavBar` del design system.",
          "- **Lista de ítems CRUD** → usa el patrón cards/split de form-runtime, no secciones colapsables.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof CollapsibleSection>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  name: "Abierta por defecto",
  render: () => (
    <div className="w-[560px]">
      <CollapsibleSection
        title="Identidad de marca"
        defaultOpen
        summary="4 de 6 campos"
      >
        <div className="flex flex-col gap-4 py-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="marca-nombre">Nombre de la marca</Label>
            <Input id="marca-nombre" defaultValue="Vitalia Salud" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="marca-tagline">Tagline</Label>
            <Input id="marca-tagline" defaultValue="Tu salud en manos expertas" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="marca-desc">Descripción</Label>
            <Textarea id="marca-desc" defaultValue="Centro médico especializado en salud preventiva y bienestar integral." rows={2} className="resize-none" />
          </div>
        </div>
      </CollapsibleSection>
    </div>
  ),
};

export const Cerrada: Story = {
  name: "Cerrada por defecto",
  render: () => (
    <div className="w-[560px]">
      <CollapsibleSection
        title="Posicionamiento"
        defaultOpen={false}
        summary="0 de 5 campos"
      >
        <div className="flex flex-col gap-4 py-3">
          <div className="flex flex-col gap-1.5">
            <Label>Propuesta de valor única</Label>
            <Textarea rows={2} className="resize-none" placeholder="¿Qué te hace único?" />
          </div>
        </div>
      </CollapsibleSection>
    </div>
  ),
};

export const ConError: Story = {
  name: "Con campos faltantes",
  render: () => (
    <div className="w-[560px]">
      <CollapsibleSection
        title="Buyer Persona"
        defaultOpen
        summary="1 de 4 campos"
        hasError
        missingFields={["Edad objetivo", "Dolores principales", "Canal preferido"]}
      >
        <div className="flex flex-col gap-4 py-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="bp-nombre">Nombre del avatar</Label>
            <Input id="bp-nombre" defaultValue="Marta, 42, profesional de salud" />
          </div>
        </div>
      </CollapsibleSection>
    </div>
  ),
};

export const MultiplesGrupos: Story = {
  name: "Múltiples secciones",
  render: () => (
    <div className="w-[560px] flex flex-col gap-3">
      {[
        { title: "Identidad", fields: 6, complete: 6, open: true },
        { title: "Historia de marca", fields: 5, complete: 3, open: false },
        { title: "Posicionamiento", fields: 7, complete: 0, open: false },
        { title: "Narrativa (StoryBrand)", fields: 8, complete: 5, open: false },
      ].map((s) => (
        <CollapsibleSection
          key={s.title}
          title={s.title}
          defaultOpen={s.open}
          summary={`${s.complete} de ${s.fields} campos`}
          hasError={s.complete === 0}
        >
          <div className="py-4 text-sm text-muted-foreground">
            Contenido de la sección {s.title}…
          </div>
        </CollapsibleSection>
      ))}
    </div>
  ),
};
