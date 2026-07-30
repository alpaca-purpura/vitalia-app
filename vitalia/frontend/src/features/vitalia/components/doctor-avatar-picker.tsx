// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * DoctorAvatarPicker — doctor selection grid for offer wizard step 5 + booking widget.
 *
 * Vitalia-specific: specialties tooltip + availability indicator.
 * Justification: spec § 6.3.6 anti-duplication.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { cn } from "@/lib/cn";
import { MICROCOPY_BOOKING } from "@/features/vitalia/config/microcopy";

export interface DoctorOption {
  id: string;
  name: string;
  specialties: string[];
  isAvailable: boolean;
  avatarUrl?: string | null;
  /** Optional initials fallback if no avatarUrl */
  initials?: string;
}

export interface DoctorAvatarPickerProps {
  doctors: DoctorOption[];
  value: string | null;
  onChange: (doctorId: string) => void;
  disabled?: boolean;
  className?: string;
}

function DoctorCard({
  doctor,
  isSelected,
  onSelect,
  disabled,
}: {
  doctor: DoctorOption;
  isSelected: boolean;
  onSelect: () => void;
  disabled: boolean;
}) {
  const initials =
    doctor.initials ??
    doctor.name
      .split(" ")
      .map((p) => p[0] ?? "")
      .join("")
      .slice(0, 2)
      .toUpperCase();

  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={!doctor.isAvailable || disabled}
      aria-pressed={isSelected}
      aria-disabled={!doctor.isAvailable || disabled}
      title={
        doctor.isAvailable
          ? `${doctor.name} — ${doctor.specialties.join(", ")}`
          : `${doctor.name} — ${MICROCOPY_BOOKING.availability.busy}`
      }
      className={cn(
        "flex flex-col items-center gap-2 p-3 rounded-xl border-2 text-center transition-all",
        "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
        isSelected
          ? "border-blue-600 bg-blue-50"
          : "border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50",
        (!doctor.isAvailable || disabled) && "opacity-50 cursor-not-allowed",
      )}
    >
      {/* Avatar */}
      <div className="relative">
        {doctor.avatarUrl ? (
          <img
            src={doctor.avatarUrl}
            alt={doctor.name}
            className="w-12 h-12 rounded-full object-cover"
          />
        ) : (
          <div
            className={cn(
              "w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold",
              isSelected
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-600",
            )}
            aria-hidden="true"
          >
            {initials}
          </div>
        )}
        {/* Availability badge */}
        <span
          className={cn(
            "absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full border-2 border-white",
            doctor.isAvailable ? "bg-green-500" : "bg-gray-400",
          )}
          role="img"
          aria-label={
            doctor.isAvailable
              ? MICROCOPY_BOOKING.availability.available
              : MICROCOPY_BOOKING.availability.busy
          }
        />
      </div>

      {/* Name */}
      <span className="text-xs font-medium text-gray-900 leading-tight">
        {doctor.name}
      </span>

      {/* Specialties (truncated) */}
      {doctor.specialties.length > 0 && (
        <span className="text-xs text-gray-500 leading-tight">
          {doctor.specialties[0]}
          {doctor.specialties.length > 1 &&
            ` +${doctor.specialties.length - 1}`}
        </span>
      )}

      {/* Availability label */}
      <span
        className={cn(
          "text-xs font-medium",
          doctor.isAvailable ? "text-green-600" : "text-gray-400",
        )}
      >
        {doctor.isAvailable
          ? MICROCOPY_BOOKING.availability.available
          : MICROCOPY_BOOKING.availability.busy}
      </span>
    </button>
  );
}

export function DoctorAvatarPicker({
  doctors,
  value,
  onChange,
  disabled = false,
  className,
}: DoctorAvatarPickerProps) {
  if (doctors.length === 0) {
    return (
      <div
        className={cn(
          "rounded-lg border border-dashed border-gray-200 p-6 text-center",
          className,
        )}
        role="status"
      >
        <p className="text-sm text-gray-500">Sin profesionales disponibles.</p>
      </div>
    );
  }

  return (
    <fieldset className={cn("border-0 p-0 m-0", className)}>
      <legend className="sr-only">Seleccionar profesional</legend>
      <div
        className="grid grid-cols-3 gap-3 sm:grid-cols-4"
        role="radiogroup"
        aria-label="Seleccionar profesional"
      >
        {doctors.map((doctor) => (
          <DoctorCard
            key={doctor.id}
            doctor={doctor}
            isSelected={value === doctor.id}
            onSelect={() => onChange(doctor.id)}
            disabled={disabled}
          />
        ))}
      </div>
    </fieldset>
  );
}
