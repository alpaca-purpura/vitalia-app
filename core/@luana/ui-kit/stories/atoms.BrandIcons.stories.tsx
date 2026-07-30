import type { Meta, StoryObj } from "@storybook/nextjs";

import { BrandIcon } from "../src/brand-icons";

const meta = {
  title: "Foundations/Iconos de marca",
  component: BrandIcon,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "`BrandIcon` renderiza el ícono SVG de una plataforma o red social por nombre. Úsalo en el panel de Growth Studio para etiquetar canales (Facebook, Instagram, WhatsApp, TikTok, Google, etc.), en la configuración de conexiones, o en cualquier lista de integraciones donde el logo de la plataforma mejora el reconocimiento.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Íconos de UI genéricos (acciones, navegación)** → usa `lucide-react` directamente.",
          "- **Logo de la propia marca del tenant** → el logo se almacena en `BrandVisuals.logo_url` y se renderiza con `next/image`.",
          "- **Plataforma no soportada** → el componente retorna `null`; muestra un fallback genérico (`Globe` de lucide-react) en el consumer.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof BrandIcon>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <BrandIcon name="instagram" className="w-8 h-8" />,
};

export const GaleriaCanales: Story = {
  name: "Galería de canales soportados",
  render: () => {
    const channels = [
      { name: "facebook", label: "Facebook" },
      { name: "instagram", label: "Instagram" },
      { name: "whatsapp", label: "WhatsApp" },
      { name: "tiktok", label: "TikTok" },
      { name: "youtube", label: "YouTube" },
      { name: "linkedin", label: "LinkedIn" },
      { name: "google", label: "Google" },
      { name: "telegram", label: "Telegram" },
      { name: "shopify", label: "Shopify" },
      { name: "manychat", label: "ManyChat" },
      { name: "mailerlite", label: "MailerLite" },
      { name: "meta", label: "Meta" },
    ];
    return (
      <div className="grid grid-cols-4 gap-6">
        {channels.map((ch) => (
          <div key={ch.name} className="flex flex-col items-center gap-1.5">
            <BrandIcon name={ch.name} className="w-7 h-7" />
            <span className="text-xs text-muted-foreground">{ch.label}</span>
          </div>
        ))}
      </div>
    );
  },
};

export const FallbackDesconocido: Story = {
  name: "Plataforma desconocida (null)",
  render: () => (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <span>BrandIcon name="tinder":</span>
      <span className="italic">(retorna null — sin render)</span>
      {BrandIcon({ name: "tinder" })}
    </div>
  ),
};
