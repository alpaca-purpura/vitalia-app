import type { Meta, StoryObj } from "@storybook/nextjs";
import * as React from "react";

import { FloatingAutosaveIndicator } from "../src/FloatingAutosaveIndicator";

/** Marco que simula la HOJA (panel del shell): relative + scroll. El indicador se ancla a su fondo. */
function HojaFrame({ children, lines = 14 }: { children: React.ReactNode; lines?: number }) {
  return (
    <div className="relative h-96 w-full max-w-xl overflow-hidden rounded-lg border bg-background">
      <div className="h-full space-y-3 overflow-y-auto p-6 pb-16">
        <p className="text-sm font-medium">Configuración de la hoja</p>
        {Array.from({ length: lines }, (_, i) => (
          <p key={i} className="text-sm text-muted-foreground">
            Campo {i + 1} — contenido de ejemplo de la hoja para mostrar el scroll y el overlay.
          </p>
        ))}
      </div>
      {children}
    </div>
  );
}

/** render que mete el indicador dentro de la HOJA (default 14 líneas de contenido). */
const inHoja =
  (lines?: number): NonNullable<Story["render"]> =>
  (args) => (
    <HojaFrame lines={lines}>
      <FloatingAutosaveIndicator {...args} />
    </HojaFrame>
  );

const meta = {
  title: "Molecules/FloatingAutosaveIndicator",
  component: FloatingAutosaveIndicator,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "Es el **indicador de autoguardado flotante canónico** (canon §2.6). **Pertenece a la HOJA** (el panel del shell), no a la página/viewport: por defecto (`anchor=\"sheet\"`) se ancla `absolute` al **borde inferior del marco `relative` de la hoja**, centrado en el ancho de la hoja, y queda **siempre pegado abajo** (contenido corto o largo). Su función es que el usuario SIEMPRE sepa el estado del guardado sin buscar un botón.",
          "",
          "Hay **UNA sola instancia por HOJA** (nunca uno por grupo). Se renderiza dentro del marco `relative` de la hoja (`AppPanelSlot` ya es `relative`), como hermano del contenido scrolleable.",
          "",
          "**Escape hatch `anchor=\"page\"`** (`fixed` al viewport): SOLO para el caso EXCEPCIONAL no-mapeado, sin hoja contenedora. Usar con cuidado.",
          "",
          "Los estados: `idle` → `dirty` (ámbar) → `saving` → `saved` (verde) → `error` (rojo).",
          "",
          "> Los ejemplos se renderizan dentro de un marco que simula la hoja — nota que la píldora queda anclada a su borde inferior, no al del canvas.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **No** pongas uno por `<Group>` — solo uno por hoja.",
          "- **No** lo uses en hojas de solo lectura (no hay nada que guardar).",
          "- **No** uses `anchor=\"page\"` salvo que no exista una hoja contenedora (excepción).",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof FloatingAutosaveIndicator>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Idle: Story = {
  args: { status: "idle" },
  render: inHoja(),
};

export const Dirty: Story = {
  name: "Dirty (cambios sin guardar)",
  args: { status: "dirty" },
  render: inHoja(),
};

export const Saving: Story = {
  name: "Saving (guardando…)",
  args: { status: "saving" },
  render: inHoja(),
};

export const Saved: Story = {
  name: "Saved (guardado)",
  args: { status: "saved", savedAt: new Date(Date.now() - 15 * 1000) },
  render: inHoja(),
  parameters: {
    docs: { description: { story: "Muestra «Guardado hace 15s». El timestamp viene de `savedAt`." } },
  },
};

export const Error: Story = {
  name: "Error al guardar",
  args: { status: "error" },
  render: inHoja(),
};

export const HojaContenidoCorto: Story = {
  name: "Hoja con contenido corto (sigue pegado al fondo)",
  args: { status: "saved", savedAt: new Date(Date.now() - 5 * 1000) },
  render: inHoja(2),
  parameters: {
    docs: {
      description: {
        story:
          "Aunque el contenido es corto, la píldora queda **pegada al borde inferior de la hoja** (no flota a media hoja como haría un `sticky`).",
      },
    },
  },
};

export const AnclaPagina: Story = {
  name: "anchor=page (escape hatch · viewport)",
  args: { status: "dirty", anchor: "page" },
  render: (args) => (
    <div className="relative h-96 w-full max-w-xl rounded-lg border border-dashed bg-muted/20 p-6">
      <p className="text-sm text-muted-foreground">
        Caso EXCEPCIONAL sin hoja: <code>anchor=&quot;page&quot;</code> ancla al viewport (
        <code>fixed</code>), no a este marco.
      </p>
      <FloatingAutosaveIndicator {...args} />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          "Escape hatch para el caso no-mapeado: la píldora se ancla al **viewport** (fondo del iframe), ignorando el marco. Solo cuando no hay hoja contenedora.",
      },
    },
  },
};
