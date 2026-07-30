import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";
import { useForm } from "react-hook-form";

import { RichSelect, type RichSelectOption } from "../src/rich-select";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "../src/form";

const meta = {
  title: "Molecules/RichSelect",
  component: RichSelect,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`RichSelect` extiende el `Select` canónico de Shadcn con opciones enriquecidas: cada opción tiene `label` (obligatorio) + `description` opcional que aparece como subtítulo dentro del item. Úsalo cuando las opciones necesitan contexto para que el usuario elija bien: archetype de oferta, tipo de consulta, especialidad médica, plan de facturación.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Opciones simples sin descripción** → usa `Select` estándar (más liviano).",
          "- **`<select>` nativo** → PROHIBIDO (canon §2.5).",
          "- **Búsqueda sobre muchas opciones** → usa `CurrencySelector` o `TimezoneSelect` (tienen Combobox con búsqueda).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof RichSelect>;

export default meta;
type Story = StoryObj<typeof meta>;

const especialidades: RichSelectOption[] = [
  { value: "cardiologia", label: "Cardiología", description: "Diagnóstico y tratamiento del corazón y sistema cardiovascular." },
  { value: "nutricion", label: "Nutrición y Metabolismo", description: "Planes alimentarios, control de peso y enfermedades metabólicas." },
  { value: "psicologia", label: "Psicología Clínica", description: "Atención de salud mental, terapia individual y grupal." },
  { value: "neurologia", label: "Neurología", description: "Sistema nervioso central y periférico." },
  { value: "medicina_general", label: "Medicina General", description: "Atención primaria, chequeos y derivaciones." },
];

const tiposConsulta: RichSelectOption[] = [
  { value: "presencial", label: "Presencial", description: "El paciente asiste al consultorio en la fecha pactada." },
  { value: "videollamada", label: "Videollamada", description: "Consulta remota por Google Meet o Zoom. Se envía link al paciente." },
  { value: "domicilio", label: "A domicilio", description: "El profesional se desplaza al domicilio del paciente. Aplica zona de cobertura." },
];

export const Default: Story = {
  render: () => {
    const form = useForm<{ especialidad: string }>({
      defaultValues: { especialidad: "" },
    });
    return (
      <Form {...form}>
        <form className="w-80">
          <FormField
            control={form.control}
            name="especialidad"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Especialidad</FormLabel>
                <RichSelect
                  options={especialidades}
                  placeholder="Selecciona una especialidad"
                  value={field.value}
                  onValueChange={field.onChange}
                />
                <FormMessage />
              </FormItem>
            )}
          />
        </form>
      </Form>
    );
  },
};

export const TipoConsulta: Story = {
  name: "Tipo de consulta",
  render: () => {
    const form = useForm<{ tipo: string }>({
      defaultValues: { tipo: "presencial" },
    });
    return (
      <Form {...form}>
        <form className="w-80">
          <FormField
            control={form.control}
            name="tipo"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Modalidad</FormLabel>
                <RichSelect
                  options={tiposConsulta}
                  placeholder="Selecciona la modalidad"
                  value={field.value}
                  onValueChange={field.onChange}
                />
                <FormMessage />
              </FormItem>
            )}
          />
        </form>
      </Form>
    );
  },
};

export const Deshabilitado: Story = {
  name: "Deshabilitado",
  render: () => {
    const form = useForm<{ especialidad: string }>({
      defaultValues: { especialidad: "cardiologia" },
    });
    return (
      <Form {...form}>
        <form className="w-80">
          <FormField
            control={form.control}
            name="especialidad"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Especialidad (bloqueada)</FormLabel>
                <RichSelect
                  options={especialidades}
                  value={field.value}
                  onValueChange={field.onChange}
                  disabled
                />
              </FormItem>
            )}
          />
        </form>
      </Form>
    );
  },
};

/** C2-T4 · consumer story — render-prop `renderItem` ejercido con punto de color por opción. */
const estadosConColor: (RichSelectOption & { color: string })[] = [
  { value: "activo", label: "Activo", description: "El profesional atiende normalmente.", color: "#22c55e" },
  { value: "licencia", label: "En licencia", description: "Fuera temporalmente, vuelve en fecha pactada.", color: "#f59e0b" },
  { value: "inactivo", label: "Inactivo", description: "No disponible para nuevas citas.", color: "#ef4444" },
];

export const ConRenderItem: Story = {
  name: "Con renderItem custom (C2-T4)",
  render: () => {
    const form = useForm<{ estado: string }>({ defaultValues: { estado: "activo" } });
    return (
      <Form {...form}>
        <form className="w-80">
          <FormField
            control={form.control}
            name="estado"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Estado del profesional</FormLabel>
                <RichSelect
                  options={estadosConColor}
                  value={field.value}
                  onValueChange={field.onChange}
                  renderItem={(opt) => {
                    const withColor = estadosConColor.find((e) => e.value === opt.value);
                    return (
                      <div className="flex items-center gap-2 text-left">
                        <span
                          className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
                          style={{ backgroundColor: withColor?.color }}
                          aria-hidden="true"
                        />
                        <div className="flex flex-col gap-0.5">
                          <span className="font-medium">{opt.label}</span>
                          {opt.description && (
                            <span className="text-xs text-muted-foreground">{opt.description}</span>
                          )}
                        </div>
                      </div>
                    );
                  }}
                />
              </FormItem>
            )}
          />
        </form>
      </Form>
    );
  },
  parameters: {
    docs: {
      description: {
        story:
          "Render-prop `renderItem` (C2-T4): cada opción incluye un punto de color semántico (verde/amarillo/rojo). Sin `renderItem` → layout predeterminado label+descripción. La marca controla el render sin tocar el componente interno.",
      },
    },
  },
};
