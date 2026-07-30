import type { Meta, StoryObj } from "@storybook/nextjs";

import { Avatar, AvatarFallback, AvatarImage } from "../src/avatar";

const meta = {
  title: "Atoms/Avatar",
  component: Avatar,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`Avatar` muestra la imagen o las iniciales de una persona o entidad. Úsalo en tarjetas de profesionales, encabezados de perfil, listas de asistentes, mensajes de conversación.",
          "",
          "`AvatarImage` carga la foto; si falla o no hay URL, `AvatarFallback` muestra las iniciales automáticamente.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- Para logos de empresas o marcas → usa `<Image>` de Next.js directamente (forma rectangular, no circular).",
          "- Para íconos de funcionalidades (sin persona asociada) → usa directamente los íconos de `lucide-react`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Avatar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Avatar>
      <AvatarImage src="https://github.com/shadcn.png" alt="Usuario" />
      <AvatarFallback>VS</AvatarFallback>
    </Avatar>
  ),
};

export const SoloIniciales: Story = {
  name: "Solo iniciales (sin foto)",
  render: () => (
    <Avatar>
      <AvatarFallback>VS</AvatarFallback>
    </Avatar>
  ),
};

export const Grupo: Story = {
  name: "Grupo de avatares (equipo)",
  render: () => (
    <div className="flex -space-x-2">
      {["VS", "TF", "LM", "AP"].map((initials) => (
        <Avatar key={initials} className="border-2 border-background">
          <AvatarFallback className="text-xs">{initials}</AvatarFallback>
        </Avatar>
      ))}
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: "Grupo de avatares superpuestos para mostrar miembros del equipo de una clínica.",
      },
    },
  },
};

export const Tamanos: Story = {
  name: "Tamaños con className",
  render: () => (
    <div className="flex items-center gap-4">
      <Avatar className="h-8 w-8">
        <AvatarFallback className="text-xs">SM</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarFallback>MD</AvatarFallback>
      </Avatar>
      <Avatar className="h-14 w-14">
        <AvatarFallback className="text-lg">LG</AvatarFallback>
      </Avatar>
    </div>
  ),
};
