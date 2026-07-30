import type { Meta, StoryObj } from "@storybook/nextjs";

import { ChatComposer } from "../src";
import { getBrandFixtures, getBrandChatStore } from "./_shell-fixtures";

/**
 * Story consumes the REAL ChatComposer from src/. It's interactive: type and
 * press Enter (or Enviar) → sendMessage on the injected chat store. Shift+Enter
 * inserts a newline; the textarea auto-resizes. Store + supervisor follow the
 * toolbar `Marca` global (Valeria · Vitalia / Luana · Nicolify).
 */
const meta = {
  title: "Shell/Chat/ChatComposer",
  component: ChatComposer,
  decorators: [
    (Story) => (
      <div className="w-[400px] rounded-lg border border-border bg-background">
        <Story />
      </div>
    ),
  ],
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`ChatComposer` es el pie del chat: textarea con auto-resize + botón Enviar (deshabilitado cuando está vacío). Enter envía, Shift+Enter inserta salto de línea, y respeta composición IME. Trae adornos decorativos (adjuntar / voz / comandos) marcados \"próximamente\".",
          "",
          "Va como fila inferior de `ChatPanel`. Es interactivo en esta story: escribe y presiona Enter para ver el mensaje agregarse.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Campo de un formulario** (no un mensaje de chat) → `Textarea` / `Input` del kit con RHF.",
          "- **Búsqueda** → `CommandInput` / `Input` con ícono de búsqueda.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof ChatComposer>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  name: "Composer (interactivo)",
  render: (_args, { globals }) => {
    const f = getBrandFixtures(globals.brand as string | undefined);
    return (
      <ChatComposer
        useChatStore={getBrandChatStore(globals.brand as string | undefined)}
        supervisorName={f.supervisor.name}
      />
    );
  },
};
