// cap: brand_studio.lisa-marca
// story-origin: estabilizar-harness-e2e-lisa-marca
/**
 * aggregateAutosave.ts — combina los estados de autosave de varias secciones de una
 * sub-tab de marca en UN solo estado de página.
 *
 * Origen: estabilizar-harness-e2e-lisa-marca (feedback de Chris). Antes el badge de
 * guardado era per-sección (solo Identidad) → el usuario no sabía si la paleta de
 * colores / tipografía se había guardado. Esta función alimenta un único
 * `<AutosaveBadge>` de nivel página que refleja TODAS las secciones.
 *
 * Prioridad (de mayor a menor urgencia visible): saving > error > dirty > saved > idle.
 * - saving: alguna sección está guardando ahora.
 * - error:  alguna sección falló (lo más importante de avisar tras saving).
 * - dirty:  hay cambios sin guardar pendientes de debounce.
 * - saved:  todo guardado; se muestra el timestamp MÁS RECIENTE entre las secciones.
 * - idle:   nada que mostrar (carga inicial, sin ediciones).
 */

import type { AutosaveStatus } from "@/components/marca/shared/AutosaveBadge";

export interface AutosaveEntry {
  status: AutosaveStatus;
  savedAt: Date | null;
}

export interface AggregatedAutosave {
  status: AutosaveStatus;
  savedAt: Date | null;
}

export function aggregateAutosaveStatus(entries: readonly AutosaveEntry[]): AggregatedAutosave {
  if (entries.some((e) => e.status === "saving")) return { status: "saving", savedAt: null };
  if (entries.some((e) => e.status === "error")) return { status: "error", savedAt: null };
  if (entries.some((e) => e.status === "dirty")) return { status: "dirty", savedAt: null };

  const saved = entries.filter(
    (e): e is { status: "saved"; savedAt: Date } => e.status === "saved" && e.savedAt !== null,
  );
  if (saved.length > 0) {
    const mostRecent = saved.reduce((a, b) => (a.savedAt.getTime() >= b.savedAt.getTime() ? a : b));
    return { status: "saved", savedAt: mostRecent.savedAt };
  }

  return { status: "idle", savedAt: null };
}
