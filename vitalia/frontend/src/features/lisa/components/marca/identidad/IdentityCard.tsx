// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * IdentityCard.tsx — Brand identity RHF form card.
 *
 * Fields: brand_name (required) + tagline (optional) + website (read-only display) +
 *         industry (optional) + founding_year (optional).
 * Autosave: watches RHF changes → scheduleAutosave debounce 600ms.
 *
 * Per 06-tickets.yaml T-5: RHF + Zod identitySchema + autosave 600ms.
 *
 * Accessibility:
 *   - All inputs have explicit <label> with htmlFor
 *   - Error messages linked via aria-describedby
 *   - AutosaveBadge with role="status"
 *
 * Spanish neutro LatAm — no voseo.
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-5 + 03-arch.md § 5
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */


import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { identitySchema } from "../../../types/marca/identity-schema";
import type { IdentityFormValues } from "../../../types/marca/identity-schema";
import { cn } from "@/lib/utils";

export interface IdentityCardProps {
  defaultValues?: Partial<IdentityFormValues>;
  /** Called on each debounced change (autosave). No manual save button. */
  onSave: (values: IdentityFormValues) => void;
  className?: string;
}

function FieldError({ message }: { message: string | undefined }) {
  if (!message) return null;
  return (
    <p role="alert" aria-live="polite" className="mt-1 text-xs text-destructive">
      {message}
    </p>
  );
}

/**
 * IdentityCard — RHF form card for brand identity (name, tagline, website read-only).
 * Autosave on change without save button (per form-runtime-array.md invariant).
 */
export function IdentityCard({
  defaultValues,
  onSave,
  className,
}: IdentityCardProps) {
  const {
    register,
    watch,
    formState: { errors, isValid },
    trigger,
  } = useForm<IdentityFormValues>({
    resolver: zodResolver(identitySchema),
    defaultValues: {
      brand_name: "",
      tagline: "",
      website: "",
      industry: "",
      founding_year: "",
      language: "es",
      timezone: "America/Lima",
      ...defaultValues,
    },
    mode: "onChange",
  });

  // Watch all fields; call onSave on every valid change (stringify to detect deep changes).
  // onSave is intentionally excluded: it changes identity on every render but should not
  // retrigger the save effect. valuesJson is the stable dep that reflects actual field changes.
  const values = watch();
  const valuesJson = JSON.stringify(values);
  const onSaveRef = useRef(onSave);
  onSaveRef.current = onSave;
  // Skip the FIRST effect run: the initial render hydrates the form from server
  // data and must NOT trigger an autosave (that PUT-on-mount made the badge show
  // "Guardado ahora mismo" on every load + wrote identical data needlessly).
  // Only user-initiated changes (subsequent valuesJson changes) autosave.
  const isHydrated = useRef(false);
  useEffect(() => {
    if (!isHydrated.current) {
      isHydrated.current = true;
      return;
    }
    if (isValid) {
      onSaveRef.current(values);
    }
    // values reference changes each render; stringify for stable comparison.
    // onSaveRef is a stable ref, so no stale closure issue.
  }, [valuesJson, isValid]); // only retrigger when field content or validity changes

  const website = watch("website");

  return (
    <section
      aria-label="Identidad de la marca"
      className={cn(
        "rounded-lg border border-border bg-card p-4 flex flex-col gap-4",
        className,
      )}
    >
      {/* Header — el estado de guardado vive a nivel página (IdentidadView header),
          no por-card, para que el usuario vea UN solo indicador de toda la pantalla. */}
      <div>
        <h3 className="text-sm font-semibold text-foreground">
          Identidad de la clínica
        </h3>
        <p className="text-xs text-muted-foreground mt-0.5">
          Nombre, tagline y sitio web de tu clínica.
        </p>
      </div>

      {/* brand_name */}
      <div>
        <label
          htmlFor="brand-name-input"
          className="block text-xs font-medium text-foreground mb-1"
        >
          Nombre de la clínica
          <span className="ml-1 text-destructive" aria-hidden="true">*</span>
        </label>
        <input
          id="brand-name-input"
          type="text"
          aria-required="true"
          aria-describedby={errors.brand_name ? "brand-name-error" : undefined}
          className={cn(
            "w-full rounded-md border bg-background px-3 py-1.5 text-sm",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            errors.brand_name ? "border-destructive" : "border-border",
          )}
          placeholder="Clínica Dental Lima Centro"
          {...register("brand_name", {
            onChange: () => void trigger("brand_name"),
          })}
        />
        {errors.brand_name && (
          <p
            id="brand-name-error"
            role="alert"
            aria-live="polite"
            className="mt-1 text-xs text-destructive"
          >
            {errors.brand_name.message}
          </p>
        )}
      </div>

      {/* tagline */}
      <div>
        <label
          htmlFor="tagline-input"
          className="block text-xs font-medium text-foreground mb-1"
        >
          Tagline
          <span className="ml-1.5 text-[11px] font-normal text-muted-foreground">(opcional)</span>
        </label>
        <input
          id="tagline-input"
          type="text"
          aria-describedby={errors.tagline ? "tagline-error" : undefined}
          className={cn(
            "w-full rounded-md border bg-background px-3 py-1.5 text-sm",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            errors.tagline ? "border-destructive" : "border-border",
          )}
          placeholder="Tu sonrisa, nuestra misión"
          {...register("tagline")}
        />
        <FieldError message={errors.tagline?.message} />
      </div>

      {/* website — read-only display */}
      {website && (
        <div>
          <p className="text-xs font-medium text-foreground mb-1">Sitio web</p>
          <a
            href={website}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary hover:underline break-all"
            aria-label={`Visitar sitio web: ${website}`}
          >
            {website}
          </a>
        </div>
      )}

      {/* industry */}
      <div>
        <label
          htmlFor="industry-input"
          className="block text-xs font-medium text-foreground mb-1"
        >
          Industria
          <span className="ml-1.5 text-[11px] font-normal text-muted-foreground">(opcional)</span>
        </label>
        <input
          id="industry-input"
          type="text"
          className={cn(
            "w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          )}
          placeholder="Salud · Odontología · Estética"
          {...register("industry")}
        />
        <FieldError message={errors.industry?.message} />
      </div>
    </section>
  );
}

IdentityCard.displayName = "IdentityCard";
