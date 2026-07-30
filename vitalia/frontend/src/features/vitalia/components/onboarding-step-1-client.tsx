// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * OnboardingStep1Client — Step 1 of 3-step clinic onboarding wizard.
 *
 * Collects clinic profile: name, type (via ClinicTypePicker), country, city.
 * Validates with clinicProfileSchema (Zod). No "Guardar" button — data passed
 * via onNext callback when valid.
 *
 * D9 pattern: Server Component page renders this Client Component.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";
import { ClinicTypePicker } from "./clinic-type-picker";
import { clinicProfileSchema } from "@/features/vitalia/schemas/clinic-profile-schema";
import { MICROCOPY_ONBOARDING } from "@/features/vitalia/config/microcopy";
import type {
  ClinicType,
  Country,
} from "@/features/vitalia/types/vitalia.types";
import type { ClinicProfileInput } from "@/features/vitalia/schemas/clinic-profile-schema";

export interface OnboardingStep1ClientProps {
  initialData?: Partial<ClinicProfileInput>;
  onNext: (data: ClinicProfileInput) => void;
  isLoading?: boolean;
}

const COUNTRY_OPTIONS: { value: Country; label: string }[] = [
  { value: "AR", label: "Argentina" },
  { value: "CL", label: "Chile" },
  { value: "MX", label: "México" },
  { value: "BR", label: "Brasil" },
  { value: "CO", label: "Colombia" },
  { value: "PE", label: "Perú" },
  { value: "UY", label: "Uruguay" },
  { value: "US", label: "Estados Unidos" },
];

export function OnboardingStep1Client({
  initialData,
  onNext,
  isLoading = false,
}: OnboardingStep1ClientProps) {
  const [clinicName, setClinicName] = useState(initialData?.clinic_name ?? "");
  const [clinicType, setClinicType] = useState<ClinicType | null>(
    (initialData?.clinic_type as ClinicType) ?? null,
  );
  const [country, setCountry] = useState<string>(initialData?.country ?? "");
  const [city, setCity] = useState(initialData?.city ?? "");
  const [errors, setErrors] = useState<Record<string, string>>({});

  function handleNext() {
    const result = clinicProfileSchema.safeParse({
      clinic_name: clinicName,
      clinic_type: clinicType,
      country,
      city,
    });

    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of result.error.issues) {
        const field = String(issue.path[0] ?? "");
        if (field) fieldErrors[field] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    setErrors({});
    onNext(result.data);
  }

  const inputBaseClass =
    "w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">
          {MICROCOPY_ONBOARDING.sectionTitle}
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          {MICROCOPY_ONBOARDING.subtitle}
        </p>
      </div>

      {/* Clinic name */}
      <div className="flex flex-col gap-1">
        <label
          htmlFor="clinic-name"
          className="text-sm font-medium text-gray-700"
        >
          {MICROCOPY_ONBOARDING.fields.clinicName}
          <span className="text-red-500 ml-1" aria-hidden="true">
            *
          </span>
        </label>
        <input
          id="clinic-name"
          type="text"
          value={clinicName}
          onChange={(e) => {
            setClinicName(e.target.value);
            if (errors.clinic_name) {
              setErrors((prev) => ({ ...prev, clinic_name: "" }));
            }
          }}
          disabled={isLoading}
          aria-invalid={!!errors.clinic_name}
          aria-describedby={
            errors.clinic_name ? "clinic-name-error" : undefined
          }
          className={cn(
            inputBaseClass,
            errors.clinic_name ? "border-red-500" : "border-gray-300",
          )}
          placeholder="Ej: Dental Sonrisa"
          autoComplete="organization"
        />
        {errors.clinic_name && (
          <p
            id="clinic-name-error"
            role="alert"
            className="text-xs text-red-600"
          >
            {errors.clinic_name}
          </p>
        )}
      </div>

      {/* Clinic type */}
      <div className="flex flex-col gap-1">
        <ClinicTypePicker
          value={clinicType}
          onChange={(value) => {
            setClinicType(value);
            if (errors.clinic_type) {
              setErrors((prev) => ({ ...prev, clinic_type: "" }));
            }
          }}
          disabled={isLoading}
        />
        {errors.clinic_type && (
          <p role="alert" className="text-xs text-red-600 mt-1">
            {errors.clinic_type}
          </p>
        )}
      </div>

      {/* Country */}
      <div className="flex flex-col gap-1">
        <label htmlFor="country" className="text-sm font-medium text-gray-700">
          {MICROCOPY_ONBOARDING.fields.country}
          <span className="text-red-500 ml-1" aria-hidden="true">
            *
          </span>
        </label>
        <select
          id="country"
          value={country}
          onChange={(e) => {
            setCountry(e.target.value);
            if (errors.country) {
              setErrors((prev) => ({ ...prev, country: "" }));
            }
          }}
          disabled={isLoading}
          aria-invalid={!!errors.country}
          aria-describedby={errors.country ? "country-error" : undefined}
          className={cn(
            inputBaseClass,
            "bg-white",
            errors.country ? "border-red-500" : "border-gray-300",
          )}
        >
          <option value="">Selecciona un país</option>
          {COUNTRY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {errors.country && (
          <p id="country-error" role="alert" className="text-xs text-red-600">
            {errors.country}
          </p>
        )}
      </div>

      {/* City */}
      <div className="flex flex-col gap-1">
        <label htmlFor="city" className="text-sm font-medium text-gray-700">
          {MICROCOPY_ONBOARDING.fields.city}
          <span className="text-red-500 ml-1" aria-hidden="true">
            *
          </span>
        </label>
        <input
          id="city"
          type="text"
          value={city}
          onChange={(e) => {
            setCity(e.target.value);
            if (errors.city) {
              setErrors((prev) => ({ ...prev, city: "" }));
            }
          }}
          disabled={isLoading}
          aria-invalid={!!errors.city}
          aria-describedby={errors.city ? "city-error" : undefined}
          className={cn(
            inputBaseClass,
            errors.city ? "border-red-500" : "border-gray-300",
          )}
          placeholder="Ej: Buenos Aires"
          autoComplete="address-level2"
        />
        {errors.city && (
          <p id="city-error" role="alert" className="text-xs text-red-600">
            {errors.city}
          </p>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-end pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={handleNext}
          disabled={isLoading}
          aria-busy={isLoading}
          className={cn(
            "px-6 py-2 rounded-md text-sm font-medium transition-colors",
            "bg-blue-600 text-white hover:bg-blue-700",
            "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
            "disabled:opacity-50 disabled:cursor-not-allowed",
          )}
        >
          {isLoading ? "Guardando..." : MICROCOPY_ONBOARDING.cta.next}
        </button>
      </div>
    </div>
  );
}
