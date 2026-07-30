// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * DoctorServiciosView.tsx — Servicios placeholder (Server Component).
 *
 * Business rule: Servicios de un integrante depende de "Mi Clínica → Servicios" story.
 * This is the permanent placeholder until that story ships.
 *
 * T-FE-2 vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § Servicios pendiente
 * downstream-regression-na: brand-local vitalia feature component
 */

export function DoctorServiciosView() {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border/60 p-10 text-center"
      data-testid="servicios-placeholder"
    >
      <span className="text-3xl" aria-hidden="true">
        🩺
      </span>
      <div>
        <p className="font-medium text-sm">Servicios — pendiente</p>
        <p className="text-xs text-muted-foreground mt-1">
          La asignación de servicios por integrante estará disponible próximamente. Depende de la configuración de servicios de la clínica.
        </p>
      </div>
    </div>
  );
}
