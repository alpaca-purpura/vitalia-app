// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * ClinicVerticalReadOnly.tsx — Read-only display of clinic vertical + specialties.
 *
 * Per D3-clinic decision: "clinic_vertical + primary_specialties READ-ONLY
 * desde onboarding-clinica story. Edit-link redirige usuario."
 *
 * Renders:
 *   - Vertical pill (e.g., "Odontología General")
 *   - Specialty pills (up to 5 shown, remainder behind "+N más")
 *   - Edit-link to /onboarding/clinic-config (opens in same tab)
 *
 * Spanish neutro LatAm — no voseo.
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-5 + CONTEXT-BRIEF § 2 D3-clinic
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const MAX_VISIBLE_SPECIALTIES = 5;

export interface ClinicVerticalReadOnlyProps {
  clinicVertical: string;
  primarySpecialties: string[];
  tenantId: string;
  className?: string;
}

/**
 * ClinicVerticalReadOnly — read-only card showing clinic category + specialties.
 * Edit-link navigates to onboarding config.
 */
export function ClinicVerticalReadOnly({
  clinicVertical,
  primarySpecialties,
  tenantId,
  className,
}: ClinicVerticalReadOnlyProps) {
  const visibleSpecialties = primarySpecialties.slice(0, MAX_VISIBLE_SPECIALTIES);
  const hiddenCount = primarySpecialties.length - visibleSpecialties.length;

  return (
    <section
      aria-label="Especialidad clínica (solo lectura)"
      className={cn(
        "rounded-lg border border-border bg-card p-4 flex flex-col gap-3",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            Especialidad clínica
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Configurado en el perfil de la clínica. Solo lectura.
          </p>
        </div>
        <Link
          href={`/${tenantId}/onboarding/clinic-config`}
          className="shrink-0 text-xs text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
          aria-label="Editar especialidad clínica en configuración de clínica"
        >
          Editar
        </Link>
      </div>

      {/* Vertical pill */}
      <div className="flex flex-wrap gap-1.5">
        {clinicVertical ? (
          <Badge
            variant="outline"
            className="text-xs font-medium border-primary/30 bg-primary/5 text-primary"
          >
            {clinicVertical}
          </Badge>
        ) : (
          <span className="text-xs text-muted-foreground italic">
            Sin especialidad registrada
          </span>
        )}
      </div>

      {/* Specialty pills */}
      {primarySpecialties.length > 0 && (
        <div
          aria-label="Especialidades de la clínica"
          className="flex flex-wrap gap-1.5"
        >
          {visibleSpecialties.map((specialty) => (
            <Badge
              key={specialty}
              variant="secondary"
              className="text-xs font-normal"
            >
              {specialty}
            </Badge>
          ))}
          {hiddenCount > 0 && (
            <Badge variant="outline" className="text-xs font-normal text-muted-foreground">
              +{hiddenCount} más
            </Badge>
          )}
        </div>
      )}
    </section>
  );
}

ClinicVerticalReadOnly.displayName = "ClinicVerticalReadOnly";
