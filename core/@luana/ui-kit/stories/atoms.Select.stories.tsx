import type { Meta, StoryObj } from "@storybook/nextjs";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "../src/select";

const meta = {
  title: "Atoms/Select",
  component: Select,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Select` (canónico Shadcn) es el selector de opción única sobre un **conjunto cerrado y pequeño** (2–20 ítems que el usuario puede ver de un vistazo): especialidad médica, tipo de turno, estado del lead, método de pago.",
          "",
          "**Regla del design system:** `<select>` nativo está prohibido en el producto — usa este componente siempre.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Colección grande (200+ ítems, server-side)** → usa `EntityPicker` (búsqueda debounced + paginación cursor + windowed render).",
          "- **Selección múltiple** → considera un grupo de `Checkbox` o un multi-select custom.",
          "- **Búsqueda + selección combinadas** → usa `Command` (tipo command palette).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Select>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story clave: select ABIERTO para que Chris lo pueda revisar
export const Abierto: Story = {
  name: "Abierto (revisión de opciones)",
  render: () => (
    <div className="relative" style={{ minHeight: 260 }}>
      <Select open>
        <SelectTrigger className="w-56">
          <SelectValue placeholder="Selecciona especialidad" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>Especialidades</SelectLabel>
            <SelectItem value="cardiology">Cardiología</SelectItem>
            <SelectItem value="dermatology">Dermatología</SelectItem>
            <SelectItem value="endocrinology">Endocrinología</SelectItem>
            <SelectItem value="gynecology">Ginecología</SelectItem>
            <SelectItem value="neurology">Neurología</SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "El `SelectContent` se monta como portal; esta story fuerza `open` para que el panel sea visible directamente en el canvas.",
      },
    },
  },
};

export const Default: Story = {
  render: () => (
    <Select>
      <SelectTrigger className="w-56">
        <SelectValue placeholder="Selecciona especialidad" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel>Especialidades</SelectLabel>
          <SelectItem value="cardiology">Cardiología</SelectItem>
          <SelectItem value="dermatology">Dermatología</SelectItem>
          <SelectItem value="endocrinology">Endocrinología</SelectItem>
          <SelectItem value="gynecology">Ginecología</SelectItem>
          <SelectItem value="neurology">Neurología</SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  ),
};

export const ConValorSeleccionado: Story = {
  name: "Con valor seleccionado",
  render: () => (
    <Select defaultValue="cardiology">
      <SelectTrigger className="w-56">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="cardiology">Cardiología</SelectItem>
        <SelectItem value="dermatology">Dermatología</SelectItem>
        <SelectItem value="endocrinology">Endocrinología</SelectItem>
      </SelectContent>
    </Select>
  ),
};

export const Deshabilitado: Story = {
  name: "Deshabilitado",
  render: () => (
    <Select disabled>
      <SelectTrigger className="w-56">
        <SelectValue placeholder="No disponible" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="x">Opción</SelectItem>
      </SelectContent>
    </Select>
  ),
};
