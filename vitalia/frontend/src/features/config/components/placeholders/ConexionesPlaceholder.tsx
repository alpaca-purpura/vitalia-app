// cap: iam.iam-scaffold-slice-1
// story-origin: vitalia-fase1-s10-TBD
/**
 * ConexionesPlaceholder — placeholder especial Config/Conexiones con grid 6 categorías.
 * F1-S10 vitalia-fase1-empty-states — T-3
 *
 * Renders:
 *   - SubTabHeader: "Conexiones" + description
 *   - Grid responsive 1/2/3 cols con 6 PlaceholderCards categoría
 *   - Cada card: icon + label + providers lista + badge estado (activa/no configurado)
 *   - Flecha "→ Configurar" right-aligned (visual only, no link)
 *
 * Server Component — no toggle state, purely presentational.
 * Named export (NO default) per FSD-Lite enforce.
 *
 * spec_anchor: 06-tickets.yaml T-3 + 01-spec.md § 10 + mockup config-conexiones-placeholder.html
 * downstream-regression-na: brand-local placeholder; no cross-brand consumers
 */

import { cn } from "@/lib/utils";

/** Connection category definition for mock display. */
interface ConnectionCategory {
  id: string;
  icon: string;
  label: string;
  providers: string;
  /** Badge variant — 'active' shows green badge, 'none' shows muted text */
  badgeState: "active" | "none";
  /** Badge label for 'active' state */
  badgeLabel?: string;
}

/** Mock connection categories — F1 visual only, no backend wire. */
const CONNECTION_CATEGORIES: ConnectionCategory[] = [
  {
    id: "marketing",
    icon: "📣",
    label: "Marketing",
    providers: "Meta Ads · Google Ads · TikTok Ads",
    badgeState: "active",
    badgeLabel: "2 activas",
  },
  {
    id: "mensajeria",
    icon: "💬",
    label: "Mensajería",
    providers: "WhatsApp · ManyChat · Instagram DM",
    badgeState: "active",
    badgeLabel: "1 activa",
  },
  {
    id: "pagos",
    icon: "💳",
    label: "Pagos",
    providers: "Stripe · MercadoPago · Yape",
    badgeState: "none",
  },
  {
    id: "calendarios",
    icon: "📅",
    label: "Calendarios",
    providers: "Google Calendar · Outlook",
    badgeState: "active",
    badgeLabel: "1 activa",
  },
  {
    id: "presencia",
    icon: "🌐",
    label: "Presencia",
    providers: "Sitio web · Instagram · Facebook · Google Business",
    badgeState: "none",
  },
  {
    id: "tecnicas",
    icon: "🔧",
    label: "Técnicas",
    providers: "Webhooks · API tokens · Zapier",
    badgeState: "none",
  },
];

/**
 * ConexionesPlaceholder — placeholder especial para Config/Conexiones.
 * Server Component (no interactive state needed).
 */
export function ConexionesPlaceholder() {
  return (
    <div className="flex flex-col gap-0" data-testid="conexiones-placeholder">
      {/* Header */}
      <div className="flex flex-col gap-1 pb-4 border-b border-border mb-6">
        <h2 className="text-lg font-semibold text-foreground">Conexiones</h2>
        <p className="text-sm text-muted-foreground">
          Integraciones externas agrupadas por categoría.
        </p>
      </div>

      {/* Grid 6 categorías */}
      <div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3"
        data-testid="conexiones-grid"
      >
        {CONNECTION_CATEGORIES.map((cat) => (
          <div
            key={cat.id}
            data-testid={`conexion-card-${cat.id}`}
            className={cn(
              "rounded-lg border border-border bg-card p-4",
              "flex flex-col gap-2",
            )}
          >
            {/* Icon */}
            <span
              aria-hidden="true"
              className="text-2xl select-none leading-none"
            >
              {cat.icon}
            </span>

            {/* Label */}
            <h3 className="text-sm font-semibold text-foreground">
              {cat.label}
            </h3>

            {/* Providers list */}
            <p className="text-xs text-muted-foreground leading-relaxed">
              {cat.providers}
            </p>

            {/* Footer: badge + arrow */}
            <div className="mt-1 flex items-center justify-between gap-2">
              {cat.badgeState === "active" && cat.badgeLabel ? (
                <span
                  className={cn(
                    "inline-flex items-center rounded px-1.5 py-0.5",
                    "bg-agent-lisa-soft text-agent-lisa",
                    "text-[10px] font-medium",
                  )}
                  data-testid={`badge-active-${cat.id}`}
                >
                  {cat.badgeLabel}
                </span>
              ) : (
                <span
                  className="text-[11px] text-muted-foreground"
                  data-testid={`badge-none-${cat.id}`}
                >
                  no configurado
                </span>
              )}

              {/* Visual arrow — no navigation F1 */}
              <span
                aria-hidden="true"
                className="text-[11px] text-muted-foreground select-none"
              >
                → Configurar
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
