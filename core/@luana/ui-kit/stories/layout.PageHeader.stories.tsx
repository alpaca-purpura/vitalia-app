import type { Meta, StoryObj } from "@storybook/nextjs";
import { Plus } from "lucide-react";

import { PageHeader } from "../src/layout/page";
import { Button } from "../src/button";

const meta = {
  title: "Templates/PageHeader",
  component: PageHeader,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es el **encabezado estándar de una hoja**: título prominente (`h1`) + subtítulo opcional + slot de acciones a la derecha (botones, menú). Úsalo como primer bloque de una hoja dentro de `<PageContainer>`.",
          "",
          "Aplica distribución `flex items-start justify-between` para que las acciones queden siempre a la derecha aunque el título sea largo.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** lo uses cuando la hoja está dentro de `EntityWorkspaceLayout` — ahí el encabezado de la entidad lo maneja `EntitySubNavBar` (franja N3, canon §2.2).",
          "- **No** lo uses como encabezado de sección (eso es `<PageSection title=...>`, con `h2`).",
          "",
          "### Slot back-pill → franja N3 (`backLabel` / `onBack`)",
          "",
          "> Para una **hoja-leaf alcanzada desde un padre** (ej. «Nueva cita» desde «Agenda»), pasá `backLabel` (+ `onBack`): el encabezado se renderiza como **franja N3 full-bleed** (sticky top · `bg-card` · `border-bottom` · `radius:0` — mismo lenguaje visual que `EntitySubNavBar`, canon §1.2/§2.2), con el pill «‹ {backLabel}» **a la izquierda** (= regreso/descarte) + título·subtítulo inline. Simula un sub-sub-tab, **NO** un encabezado con padding ni un pill flotante. Usa la flechita `‹` (no `←`). Aditivo — sin `backLabel` es el encabezado de contenido estándar. El slot `leading` permite un dot de agente o ícono.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof PageHeader>;

export default meta;
type Story = StoryObj<typeof meta>;

export const SinAcciones: Story = {
  args: {
    title: "Doctores",
    subtitle: "Gestiona el directorio médico de la clínica",
  },
};

export const ConAcciones: Story = {
  args: {
    title: "Doctores",
    subtitle: "4 doctores activos",
    actions: (
      <Button size="sm">
        <Plus className="mr-1.5 h-4 w-4" aria-hidden />
        Agregar doctor
      </Button>
    ),
  },
};

export const ConBackPill: Story = {
  name: "Con back-pill (hoja-leaf)",
  args: {
    backLabel: "Agenda",
    onBack: () => {},
    title: "Nueva cita",
    subtitle: "Martes 24 jun · 14:30",
    // Sin botón "Descartar" separado: el pill «‹ Agenda» (izquierda) ES el
    // regreso/descarte (volver a Agenda descarta la cita) — look limpio de sub-sub-tab.
    // El slot `actions` sigue disponible para consumers que pasen una acción real.
  },
  parameters: {
    docs: {
      description: {
        story:
          "Hoja-leaf alcanzada desde un padre: **franja N3 full-bleed** (sticky · bg-card · border-bottom · radius:0, lenguaje de EntitySubNavBar) con el pill «‹ Agenda» a la izquierda (= regreso/descarte) que llama a `onBack`. Simula un sub-sub-tab — pegado al top, no un header con padding.",
      },
    },
  },
};

export const TituloLargoConAcciones: Story = {
  name: "Título largo con acciones",
  args: {
    title: "Directorio de especialistas — Clínica San Martín, Sede Palermo",
    subtitle: "12 especialistas registrados · última actualización hace 2 días",
    actions: (
      <div className="flex gap-2">
        <Button variant="outline" size="sm">
          Exportar
        </Button>
        <Button size="sm">
          <Plus className="mr-1.5 h-4 w-4" aria-hidden />
          Nuevo
        </Button>
      </div>
    ),
  },
};
