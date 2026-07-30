// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
"use client";
/**
 * PhonePreview.tsx — Mobile-frame preview of the doctor's public page.
 *
 * Renders a Doctoralia-style phone frame showing the public profile
 * as patients will see it at /d/{clinica-slug}/{doctor-slug}.
 *
 * Structure (per mockup D3-D / RN-D3D-1..7):
 *   header: avatar/iniciales + nombre + especialidad + badge ✓ colegiatura
 *   Sobre mí (if present)
 *   Formación (if any)
 *   Experiencia (if any)
 *   Tratamientos chips (if any)
 *   Certificaciones (if any)
 *   Idiomas (RN-D3D-5: only if > 1 language)
 *   Footer: "Perfil profesional verificado por la clínica"
 *
 * Empty sections OMITTED (RN-D3D-6).
 * No PHI in preview — og-safe fields only.
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-D.5
 */

import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import type { DoctorDetail } from "../../../../types/staff.types";

interface PhonePreviewProps {
  doctor: DoctorDetail;
}

/** Generates initials from name for avatar fallback */
function getInitials(firstName: string, lastName: string): string {
  return `${firstName[0] ?? ""}${lastName[0] ?? ""}`.toUpperCase();
}

/**
 * PhonePreview — Doctoralia-style mobile frame preview.
 */
export function PhonePreview({ doctor }: PhonePreviewProps) {
  const profile = doctor.publicProfile;
  const initials = getInitials(doctor.firstName, doctor.lastName);

  return (
    <div
      aria-label="Vista previa del perfil en móvil"
      className="sticky top-4"
    >
      {/* Phone frame — W3: fixed pixel dimensions are intentional device-frame constraints,
           not arbitrary design values: 280px=typical phone width in sidebar, 6px=bezel thickness,
           520px=visible screen height matching common 844px phone at ~62% scale */}
      <div className="mx-auto w-[280px] rounded-3xl border-[6px] border-foreground/10 bg-background shadow-xl overflow-hidden">
        {/* Status bar mock */}
        <div className="h-6 bg-muted/50 flex items-center justify-center">
          <div className="w-16 h-1.5 rounded-full bg-foreground/20" />
        </div>

        {/* Scrollable content */}
        <div className="h-[520px] overflow-y-auto overscroll-contain">
          {/* Header */}
          <header className="flex flex-col items-center gap-2 bg-gradient-to-b from-agent-lisa/10 to-background px-4 pb-4 pt-5">
            {/* Avatar or initials */}
            <Avatar className="h-16 w-16 border-2 border-background shadow-md">
              <AvatarImage
                src={doctor.avatarUrl ?? undefined}
                alt={`Foto de ${doctor.firstName} ${doctor.lastName}`}
              />
              <AvatarFallback
                className="bg-agent-lisa/20 text-agent-lisa text-lg font-semibold"
                aria-label={`Iniciales ${initials}`}
              >
                {initials}
              </AvatarFallback>
            </Avatar>

            {/* Name */}
            <div className="text-center">
              <p className="font-semibold text-sm leading-tight">
                Dr. {doctor.firstName} {doctor.lastName}
              </p>
              {doctor.specialty && (
                <p className="text-xs text-muted-foreground mt-0.5">{doctor.specialty}</p>
              )}
            </div>

            {/* Badge colegiatura */}
            <div className="flex items-center gap-1 rounded-full bg-green-100 dark:bg-green-900/40 px-2.5 py-0.5">
              <span className="text-green-600 dark:text-green-400 text-xs" aria-hidden="true">✓</span>
              <span className="text-xs text-green-700 dark:text-green-300 font-medium">
                {doctor.credentialCountry} — {doctor.credential}
              </span>
            </div>
          </header>

          {/* Content sections */}
          <div className="px-4 pb-6 space-y-4 text-xs">
            {/* Sobre mí */}
            {profile?.sobreMi && (
              <div>
                <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-1">
                  Sobre mí
                </p>
                <p className="text-foreground leading-relaxed line-clamp-4">
                  {profile.sobreMi}
                </p>
              </div>
            )}

            {/* Formación */}
            {profile && profile.formacion.length > 0 && (
              <div>
                <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-1">
                  Formación
                </p>
                <ul className="space-y-1.5 list-none" aria-label="Formación académica">
                  {profile.formacion.map((f, i) => (
                    <li key={i} className="flex gap-1.5">
                      <span className="text-agent-lisa mt-0.5 shrink-0" aria-hidden="true">·</span>
                      <span>
                        <span className="font-medium">{f.titulo}</span>
                        {f.institucion && (
                          <span className="text-muted-foreground"> — {f.institucion}</span>
                        )}
                        {f.anio && (
                          <span className="text-muted-foreground"> ({f.anio})</span>
                        )}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Experiencia */}
            {profile && profile.experiencia.length > 0 && (
              <div>
                <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-1">
                  Experiencia
                </p>
                <ul className="space-y-1.5 list-none" aria-label="Experiencia profesional">
                  {profile.experiencia.map((e, i) => (
                    <li key={i} className="flex gap-1.5">
                      <span className="text-agent-lisa mt-0.5 shrink-0" aria-hidden="true">·</span>
                      <span>
                        {/* F2: real wire fields are puesto/lugar/anios (NOT cargo/institucion/desde/hasta) */}
                        <span className="font-medium">{e.puesto}</span>
                        {e.lugar && (
                          <span className="text-muted-foreground"> — {e.lugar}</span>
                        )}
                        {e.anios != null && (
                          <span className="text-muted-foreground"> ({e.anios} {e.anios === 1 ? "año" : "años"})</span>
                        )}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Tratamientos */}
            {profile && profile.tratamientos.length > 0 && (
              <div>
                <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-1.5">
                  Tratamientos
                </p>
                <div className="flex flex-wrap gap-1" aria-label="Tratamientos">
                  {profile.tratamientos.map((t) => (
                    <span
                      key={t}
                      className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Certificaciones */}
            {profile && profile.certificaciones.length > 0 && (
              <div>
                <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-1">
                  Certificaciones
                </p>
                <ul className="space-y-1 list-none" aria-label="Certificaciones">
                  {/* F3: certificaciones is string[] on the wire — render as plain string */}
                  {profile.certificaciones.map((c, i) => (
                    <li key={i} className="flex gap-1.5">
                      <span className="text-agent-lisa mt-0.5 shrink-0" aria-hidden="true">·</span>
                      <span>{c}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Idiomas — RN-D3D-5: only if > 1 */}
            {profile && profile.idiomas.length > 1 && (
              <div>
                <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-1.5">
                  Idiomas
                </p>
                <div className="flex flex-wrap gap-1" aria-label="Idiomas">
                  {/* F3: idiomas is string[] on the wire — render as plain string */}
                  {profile.idiomas.map((lang, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium"
                    >
                      {lang}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Empty state — no profile yet */}
            {!profile && (
              <p className={cn("py-8 text-center text-muted-foreground text-xs")}>
                Genera el perfil para ver la vista previa.
              </p>
            )}

            {/* Footer */}
            <div className="border-t border-border/50 pt-3 mt-2">
              <p className="text-center text-xs text-muted-foreground">
                Perfil profesional verificado por la clínica
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Preview label */}
      <p className="mt-2 text-center text-xs text-muted-foreground">
        Vista previa del perfil público
      </p>
    </div>
  );
}
