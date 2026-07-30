// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * PatientListTable — CDP medical-flavor list of patients.
 *
 * Renders: masekd patient rows (phone/email PII masked at BE), clinic
 * type badge, created date, and click-to-select for detail panel.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";
import { usePatients } from "@/features/vitalia/api/use-patients";
import type { PatientSummary } from "@/features/vitalia/types/treatment.types";

export interface PatientListTableProps {
  onSelectPatient?: (id: string) => void;
  clinicTypeFilter?: string;
  className?: string;
}

function PatientRow({
  patient,
  onSelect,
}: {
  patient: PatientSummary;
  onSelect?: (id: string) => void;
}) {
  const fullName = `${patient.name_first} ${patient.name_last_initial}.`;

  return (
    <tr
      className="border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer"
      onClick={() => onSelect?.(patient.id)}
      tabIndex={0}
      role="row"
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect?.(patient.id);
        }
      }}
      aria-label={`Paciente ${fullName}`}
    >
      <td className="px-4 py-3 text-sm text-gray-800 font-medium">
        {fullName}
      </td>
      <td className="px-4 py-3 text-xs text-gray-500 font-mono">
        {patient.phone_masked}
      </td>
      <td className="px-4 py-3 text-xs text-gray-500 font-mono truncate max-w-xs">
        {patient.email_masked}
      </td>
      <td className="px-4 py-3">
        {patient.clinic_type ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700 capitalize">
            {patient.clinic_type}
          </span>
        ) : (
          <span className="text-gray-400 text-xs">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">
        {new Date(patient.created_at).toLocaleDateString("es", {
          day: "2-digit",
          month: "short",
          year: "numeric",
        })}
      </td>
    </tr>
  );
}

const PAGE_SIZE = 10;

export function PatientListTable({
  onSelectPatient,
  clinicTypeFilter,
  className,
}: PatientListTableProps) {
  const [page, setPage] = useState(0);
  const { data, isLoading, isError } = usePatients(
    clinicTypeFilter ? { clinic_type: clinicTypeFilter } : undefined,
  );

  const allPatients = data?.patients ?? [];
  const total = data?.total ?? 0;
  const pageStart = page * PAGE_SIZE;
  const paginated = allPatients.slice(pageStart, pageStart + PAGE_SIZE);
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
          Error al cargar pacientes. Intenta recargar la página.
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
            <p className="mt-2 text-sm text-gray-500">Cargando pacientes...</p>
          </div>
        ) : allPatients.length === 0 ? (
          <div className="p-8 text-center" role="status">
            <p className="text-sm text-gray-500">Sin pacientes registrados.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table
              className="w-full text-left text-sm"
              aria-label="Lista de pacientes"
            >
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr role="row">
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Nombre
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Teléfono
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Correo
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Tipo clínica
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Registro
                  </th>
                </tr>
              </thead>
              <tbody role="rowgroup">
                {paginated.map((p) => (
                  <PatientRow
                    key={p.id}
                    patient={p}
                    onSelect={onSelectPatient}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

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
