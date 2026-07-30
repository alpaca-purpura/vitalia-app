// cap: marketing.attribution-matrix-4-origins
// story-origin: TBD
/**
 * AttributionMatrixWidget — attribution matrix per spec.
 *
 * Scaffold stub. Full implementation (with real attribution API + channel registry)
 * arrives in growth-studio story (Slice 2+).
 *
 * Matrix layout: channels (rows) × touchpoints (columns) × contribution value.
 * Per design-system.md: no hsl literals in TSX. All colors via vt-* classes.
 */

import { cn } from "@/lib/cn";

export interface AttributionCell {
  /** Channel slug */
  channelSlug: string;
  /** Touchpoint key (e.g. "first_touch", "last_touch", "linear") */
  touchpoint: string;
  /** Attribution contribution score 0..1 */
  score: number;
}

export interface AttributionChannel {
  /** Channel slug */
  slug: string;
  /** Display name */
  name: string;
}

export interface AttributionMatrixWidgetProps {
  /** Channels (rows) */
  channels?: AttributionChannel[];
  /** Touchpoint column labels */
  touchpoints?: string[];
  /** Attribution cells */
  cells?: AttributionCell[];
  /** Whether data is loading */
  isLoading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Attribution matrix — channels × touchpoints with contribution heatmap.
 * Scaffold: renders placeholder grid until Slice 2+ full impl.
 */
export function AttributionMatrixWidget({
  channels = [],
  touchpoints = ["Primer toque", "Último toque", "Lineal"],
  cells = [],
  isLoading = false,
  className,
}: AttributionMatrixWidgetProps) {
  function getScore(channelSlug: string, touchpoint: string): number | null {
    const cell = cells.find(
      (c) => c.channelSlug === channelSlug && c.touchpoint === touchpoint,
    );
    return cell?.score ?? null;
  }

  function scoreToOpacity(score: number | null): number {
    if (score === null) return 0;
    return Math.max(0.05, score);
  }

  return (
    <section
      className={cn(
        "vt-bg-surface vt-border border rounded-[var(--radius-lg)] p-4",
        className,
      )}
      aria-label="Matriz de atribución de canales"
      aria-busy={isLoading}
    >
      <h3 className="text-sm font-semibold vt-text mb-4">
        Matriz de atribución
      </h3>

      {isLoading && (
        <div
          className="text-xs vt-text-muted py-4 text-center"
          aria-live="polite"
        >
          Cargando datos de atribución...
        </div>
      )}

      {!isLoading && channels.length === 0 && (
        <p className="text-xs vt-text-faint text-center py-4">
          Sin datos de atribución.
          {/* Placeholder — Slice 2 impl */}
        </p>
      )}

      {!isLoading && channels.length > 0 && (
        <div
          className="overflow-x-auto"
          role="table"
          aria-label="Tabla de atribución"
        >
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr role="row">
                <th
                  className="text-left py-2 pr-3 vt-text-faint font-medium"
                  role="columnheader"
                  scope="col"
                >
                  Canal
                </th>
                {touchpoints.map((tp) => (
                  <th
                    key={tp}
                    className="text-center py-2 px-2 vt-text-faint font-medium"
                    role="columnheader"
                    scope="col"
                  >
                    {tp}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {channels.map((ch) => (
                <tr
                  key={ch.slug}
                  className="border-t vt-border-soft"
                  role="row"
                >
                  <td
                    className="py-2 pr-3 vt-text font-medium"
                    role="rowheader"
                    scope="row"
                  >
                    {ch.name}
                  </td>
                  {touchpoints.map((tp) => {
                    const score = getScore(ch.slug, tp);
                    const opacity = scoreToOpacity(score);
                    return (
                      <td
                        key={tp}
                        className="py-2 px-2 text-center"
                        role="cell"
                        aria-label={`${ch.name} — ${tp}: ${score !== null ? `${(score * 100).toFixed(0)}%` : "sin datos"}`}
                      >
                        <span
                          className="inline-flex items-center justify-center w-10 h-6 rounded text-white text-[10px] font-semibold"
                          style={{
                            backgroundColor: `color-mix(in srgb, var(--vitalia-cian-color) ${opacity * 100}%, transparent)`,
                          }}
                        >
                          {score !== null
                            ? `${(score * 100).toFixed(0)}%`
                            : "—"}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="mt-3 text-xs vt-text-faint italic">
        Implementación completa en Slice 2 (growth-studio).
      </p>
    </section>
  );
}
