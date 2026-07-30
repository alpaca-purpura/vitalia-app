import type { Meta, StoryObj } from "@storybook/nextjs";

import { FieldInfo } from "../src/field-info";
import { Label } from "../src/label";
import { Input } from "../src/input";

const meta = {
  title: "Atoms/FieldInfo",
  component: FieldInfo,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`FieldInfo` muestra un ícono `ⓘ` que al hover despliega un tooltip con información contextual de un campo. Es el reemplazo canónico del `<select>` nativo y de labels explicativos verbosos: en vez de llenar el formulario con texto aclaratorio, el usuario que necesita ayuda hace hover y la lee. Úsalo en campos técnicos o poco obvios de formularios de configuración.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Texto de ayuda permanente bajo el campo** → usa `FormDescription` (más visible, no requiere hover).",
          "- **Errores de validación** → usa `FormMessage` (rojo, debajo del campo).",
          "- **Contexto extenso (>2 líneas)** → considera un `Sheet` o un enlace a documentación.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof FieldInfo>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <FieldInfo description="La zona horaria se usa para mostrar los horarios de citas al paciente en su horario local." />
  ),
};

export const EnFormulario: Story = {
  name: "Integrado en formulario",
  render: () => (
    <div className="flex flex-col gap-4 w-80">
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center">
          <Label htmlFor="rfc">RFC / ID fiscal</Label>
          <FieldInfo description="En México: RFC de 13 caracteres. En Argentina: CUIT de 11 dígitos. En Colombia: NIT con dígito de verificación." />
        </div>
        <Input id="rfc" placeholder="XAXX010101000" />
      </div>
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center">
          <Label htmlFor="moneda">Moneda principal</Label>
          <FieldInfo description="Se usa para mostrar los precios de tus servicios. Puedes tener tarifas en varias monedas, esta es la que aparece por defecto." />
        </div>
        <Input id="moneda" placeholder="MXN" />
      </div>
    </div>
  ),
};

export const VariasDescripciones: Story = {
  name: "Varias instancias",
  render: () => (
    <div className="flex flex-col gap-3">
      {[
        "Porcentaje de comisión aplicado al total facturado en cada transacción.",
        "Tiempo en minutos que el sistema espera antes de liberar un turno sin confirmar.",
        "Correo al que se envían notificaciones críticas del sistema, separado del correo de soporte.",
      ].map((desc, i) => (
        <div key={i} className="flex items-center gap-1">
          <span className="text-sm text-muted-foreground">Campo {i + 1}</span>
          <FieldInfo description={desc} />
        </div>
      ))}
    </div>
  ),
};
