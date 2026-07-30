// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * PatientDetailPanel — right-panel detail view for a selected patient.
 *
 * Renders: masked PII fields, medical history summary, clinic type,
 * registration date.  PII masking happens at BE — FE displays as-is.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { cn } from "@/lib/cn";
import { usePatient } from "@/features/vitalia/api/use-patient";

export interface PatientDetailPanelProps {
  patientId: string;
  className?: string;
}

function DetailField({
  label,
  value,
}: {
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </span>
      <span className="text-sm text-gray-900">
        {value ?? <span className="text-gray-400">—</span>}
      </span>
    </div>
  );
}

export function PatientDetailPanel({
  patientId,
  className,
}: PatientDetailPanelProps) {
  const { data: patient, isLoading, isError } = usePatient(patientId);

  if (isLoading) {
    return (
      <div
        className={cn(
          "rounded-lg border border-gray-200 bg-white p-6 space-y-4",
          className,
        )}
        role="status"
        aria-busy={true}
        aria-live="polite"
      >
        {[0, 1, 2, 3, 4].map((i) => (
          <div key={i} className="space-y-1.5">
            <div className="h-3 w-24 rounded bg-gray-200 animate-pulse" />
            <div className="h-4 w-40 rounded bg-gray-100 animate-pulse" />
          </div>
        ))}
      </div>
    );
  }

  if (isError || !patient) {
    return (
      <div
        className={cn(
          "rounded-lg border border-red-200 bg-red-50 p-6 text-center",
          className,
        )}
        role="alert"
      >
        <p className="text-sm text-red-700">
          Error al cargar el paciente. Intenta recargar.
        </p>
      </div>
    );
  }

  const fullName = `${patient.name_first} ${patient.name_last_initial}.`;

  return (
    <article
      className={cn(
        "rounded-lg border border-gray-200 bg-white p-6 space-y-5",
        className,
      )}
      aria-label={`Detalle del paciente ${fullName}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between border-b border-gray-100 pb-4">
        <div>
          <h3 className="text-base font-semibold text-gray-900">{fullName}</h3>
          {patient.clinic_type && (
            <span className="inline-flex items-center mt-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700 capitalize">
              {patient.clinic_type}
            </span>
          )}
        </div>
      </div>

      {/* Fields grid */}
      <div className="grid grid-cols-2 gap-4">
        <DetailField label="Teléfono" value={patient.phone_masked} />
        <DetailField label="Correo" value={patient.email_masked} />
        <DetailField
          label="Registro"
          value={new Date(patient.created_at).toLocaleDateString("es", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          })}
        />
        <DetailField
          label="Última actualización"
          value={new Date(patient.updated_at).toLocaleDateString("es", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          })}
        />
      </div>

      {/* Medical history summary */}
      {patient.medical_history_summary && (
        <div className="space-y-1">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Resumen historial médico
          </span>
          <p className="text-sm text-gray-700 bg-gray-50 rounded-md p-3 leading-relaxed">
            {patient.medical_history_summary}
          </p>
        </div>
      )}

      {!patient.medical_history_summary && (
        <div className="rounded-md border border-dashed border-gray-200 p-4 text-center">
          <p className="text-xs text-gray-400">
            Sin historial médico registrado.
          </p>
        </div>
      )}
    </article>
  );
}
