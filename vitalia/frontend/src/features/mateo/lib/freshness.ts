// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
/**
 * freshness.ts — Helper de frescura para indicadores "Actualizado hace X" en Valeria Agenda.
 *
 * Thin wrapper sobre `src/lib/format/formatTenantRelative.ts` que:
 *   - Prefija el resultado con "Actualizado hace " para el patrón de FreshnessIndicator.
 *   - Acepta Date | string | number (ISO 8601, timestamp ms, o Date object).
 *   - Spanish neutro LatAm (sin voseo, tildes correctas).
 *   - Nunca lanza — devuelve "—" en caso de entrada inválida.
 *
 * Uso:
 *   formatRelativeTime(new Date()) // "Actualizado hace unos segundos"
 *   formatRelativeTime("2026-05-27T15:30:00Z") // "Actualizado hace 5 minutos"
 *   formatRelativeTime(null) // "—"
 *
 * Refs:
 *   - 01-spec § real-time: "FreshnessIndicator 'Actualizado hace Xs/Xm'"
 *   - .claude/rules/spanish-text.md
 *   - src/lib/format/formatTenantRelative.ts (base)
 */

import { formatTenantRelative } from "@/lib/format/formatTenantRelative";

/**
 * Convierte una fecha a string relativa con prefijo "Actualizado hace ...".
 *
 * @param date - Fecha a formatear (Date | ISO string | timestamp ms | null | undefined)
 * @param locale - BCP 47 locale (default: "es-419" = español LatAm)
 * @returns String de frescura, ej: "Actualizado hace 3 minutos" | "Actualizado hace 2 días" | "—"
 */
export function formatRelativeTime(
  date: Date | string | number | null | undefined,
  locale: string = "es-419",
): string {
  if (date === null || date === undefined) return "—";

  let isoString: string;

  try {
    if (typeof date === "number") {
      isoString = new Date(date).toISOString();
    } else if (date instanceof Date) {
      if (isNaN(date.getTime())) return "—";
      isoString = date.toISOString();
    } else {
      isoString = date;
    }
  } catch {
    return "—";
  }

  const relative = formatTenantRelative(isoString, locale);

  // formatTenantRelative devuelve "—" para entradas inválidas — propagar sin prefijo
  if (relative === "—") return "—";

  // El formateo "hace X" ya viene del Intl.RelativeTimeFormat
  // Ejemplo output de formatTenantRelative: "hace 3 minutos"
  // Nuestro output objetivo: "Actualizado hace 3 minutos"
  //
  // Si por alguna razón el Intl ya retorna "en X" (futuro), ignoramos el prefijo
  // ya que FreshnessIndicator solo muestra actualizaciones pasadas.
  return `Actualizado ${relative}`;
}
