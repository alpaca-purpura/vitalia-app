import type { Meta, StoryObj } from "@storybook/nextjs";

import { Switch } from "../src/switch";
import { Label } from "../src/label";

const meta = {
  title: "Atoms/Switch",
  component: Switch,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Switch` es para **una sola configuración binaria on/off** que tiene efecto inmediato: activar notificaciones, habilitar una funcionalidad, poner en modo mantenimiento. El efecto se produce al cambiar el toggle, sin necesidad de confirmar con un botón.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Seleccionar una entre varias opciones** → usa `RadioGroup`.",
          "- **Seleccionar múltiples ítems** → usa `Checkbox`.",
          "- **La acción requiere confirmación** (ej. desactivar una cuenta) → usa `AlertDialog` antes del toggle para evitar cambios accidentales.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Switch>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="flex items-center gap-3">
      <Switch id="notifications" />
      <Label htmlFor="notifications">Notificaciones por email</Label>
    </div>
  ),
};

export const Activo: Story = {
  name: "Activo por defecto",
  render: () => (
    <div className="flex items-center gap-3">
      <Switch id="whatsapp-reminders" defaultChecked />
      <Label htmlFor="whatsapp-reminders">Recordatorios por WhatsApp</Label>
    </div>
  ),
};

export const Deshabilitado: Story = {
  name: "Deshabilitado",
  render: () => (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <Switch id="disabled-off" disabled />
        <Label htmlFor="disabled-off" className="opacity-50">
          Funcionalidad no disponible en tu plan
        </Label>
      </div>
      <div className="flex items-center gap-3">
        <Switch id="disabled-on" disabled defaultChecked />
        <Label htmlFor="disabled-on" className="opacity-50">
          Activado (administrado por soporte)
        </Label>
      </div>
    </div>
  ),
};

export const Grupo: Story = {
  name: "Grupo de configuraciones",
  render: () => (
    <div className="flex flex-col gap-4 w-80">
      <p className="text-sm font-semibold">Preferencias de comunicación</p>
      {[
        { id: "sw-email", label: "Confirmaciones por correo", on: true },
        { id: "sw-wa", label: "Recordatorios por WhatsApp", on: true },
        { id: "sw-sms", label: "Alertas por SMS", on: false },
        { id: "sw-mkt", label: "Comunicaciones de marketing", on: false },
      ].map((s) => (
        <div key={s.id} className="flex items-center justify-between">
          <Label htmlFor={s.id}>{s.label}</Label>
          <Switch id={s.id} defaultChecked={s.on} />
        </div>
      ))}
    </div>
  ),
};
