// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * TreatmentListTable — paginated table of active treatments.
 *
 * Renders: treatment rows with status badge, adherence score, next
 * scheduled date, and link to detail panel.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";
import { useTreatments } from "@/features/vitalia/api/use-treatments";
import type { TreatmentSummary } from "@/features/vitalia/types/treatment.types";

export interface TreatmentListTableProps {
  onSelectTreatment?: (id: string) => void;
  className?: string;
}

function AdherenceBadge({ score }: { score: number | null }) {
  if (score === null) {
    return <span className="text-gray-400 text-xs">—</span>;
  }
  const colorClass =
    score >= 80
      ? "bg-green-100 text-green-700"
      : score >= 50
        ? "bg-yellow-100 text-yellow-700"
        : "bg-red-100 text-red-700";
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
        colorClass,
      )}
      aria-label={`Adherencia: ${score}%`}
    >
      {score}%
    </span>
  );
}

function formatNextScheduled(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es", { day: "2-digit", month: "short" });
}

function TreatmentRow({
  treatment,
  onSelect,
}: {
  treatment: TreatmentSummary;
  onSelect?: (id: string) => void;
}) {
  return (
    <tr
      className="border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer"
      onClick={() => onSelect?.(treatment.id)}
      tabIndex={0}
      role="row"
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect?.(treatment.id);
        }
      }}
      aria-label={`Tratamiento ${treatment.id.slice(0, 8)} — paso: ${treatment.current_step}`}
    >
      <td className="px-4 py-3 text-xs text-gray-500 font-mono whitespace-nowrap">
        {treatment.id.slice(0, 8)}...
      </td>
      <td className="px-4 py-3 text-sm text-gray-800">
        {treatment.plan_template_slug}
      </td>
      <td className="px-4 py-3 text-xs text-gray-600">
        {treatment.current_step}
      </td>
      <td className="px-4 py-3">
        <AdherenceBadge score={treatment.adherence_score} />
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">
        {formatNextScheduled(treatment.next_scheduled_at)}
      </td>
    </tr>
  );
}

const PAGE_SIZE = 10;

export function TreatmentListTable({
  onSelectTreatment,
  className,
}: TreatmentListTableProps) {
  const [page, setPage] = useState(0);
  const { data, isLoading, isError } = useTreatments();

  const allTreatments = data?.treatments ?? [];
  const total = data?.total ?? 0;
  const pageStart = page * PAGE_SIZE;
  const paginated = allTreatments.slice(pageStart, pageStart + PAGE_SIZE);
  const totalPages = Math.ceil(total / PAGE_SIZE);

  if (isError) {
    return (
      <div
        className={cn(
          "rounded-lg border border-red-200 bg-red-50 p-6 text-center",
          className,
        )}
        role="alert"
      >
        <p className="text-sm text-red-700">
          Error al cargar tratamientos. Intenta recargar la página.
        </p>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        {isLoading ? (
          <div
            className="p-8 text-center"
            role="status"
            aria-busy={true}
            aria-live="polite"
          >
            <div
              className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"
              aria-hidden="true"
            />
            <p className="mt-2 text-sm text-gray-500">
              Cargando tratamientos...
            </p>
          </div>
        ) : allTreatments.length === 0 ? (
          <div className="p-8 text-center" role="status">
            <p className="text-sm text-gray-500">Sin tratamientos activos.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table
              className="w-full text-left text-sm"
              aria-label="Lista de tratamientos"
            >
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr role="row">
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    ID
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Plan
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Paso actual
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Adherencia
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Próx. mensaje
                  </th>
                </tr>
              </thead>
              <tbody role="rowgroup">
                {paginated.map((t) => (
                  <TreatmentRow
                    key={t.id}
                    treatment={t}
                    onSelect={onSelectTreatment}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>
            Mostrando {pageStart + 1}–{Math.min(pageStart + PAGE_SIZE, total)}{" "}
            de {total}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="rounded-md border border-gray-200 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Página anterior"
            >
              Anterior
            </button>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="rounded-md border border-gray-200 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Página siguiente"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
