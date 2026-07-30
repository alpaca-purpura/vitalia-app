// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * /d/[clinica-slug]/[doctor-slug]/page.tsx — Public doctor profile page.
 *
 * Server Component. NO auth required — route excluded from Clerk auth in proxy.ts.
 * Anti-enumeration (RN-D3D-9): toggle-OFF / unknown slug / cross-tenant slug ALL
 * return an IDENTICAL "perfil no disponible" response (same HTTP shape, same copy).
 *
 * OG tags: og:title / og:description / og:image from og-safe fields only (no PHI).
 * og:image: avatar via absolute APP_BASE_URL, fallback to brand default.
 *
 * Structure (per mockup D3-D):
 *   header: foto + nombre + especialidad + badge ✓ colegiatura
 *   Sobre mí → Formación → Experiencia → Tratamientos chips → Certificaciones
 *   Idiomas (only if > 1 — RN-D3D-5)
 *   Consultorio (clinic name)
 *   Footer: "Perfil profesional verificado por la clínica"
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-D.6
 */

import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Image from "next/image";
import { cn } from "@/lib/utils";
import type { PublicDoctorPageData } from "@/features/lisa";

// ── Server-side fetch ─────────────────────────────────────────────────────────

const API_SSR_BASE = process.env.INTERNAL_API_URL ?? "http://127.0.0.1:8002";
const APP_BASE_URL = process.env.NEXT_PUBLIC_APP_BASE_URL ?? "";

async function fetchPublicDoctorPage(
  clinicaSlug: string,
  doctorSlug: string,
): Promise<PublicDoctorPageData | null> {
  try {
    const res = await fetch(
      `${API_SSR_BASE}/api/public/clinic/${clinicaSlug}/doctors/${doctorSlug}`,
      {
        // No auth header — public endpoint
        next: { revalidate: 60 }, // ISR: re-validate every 60s
      },
    );
    if (res.status === 404) return null;
    if (!res.ok) return null;
    return (await res.json()) as PublicDoctorPageData;
  } catch {
    return null;
  }
}

// ── generateMetadata ──────────────────────────────────────────────────────────

interface PublicDoctorPageProps {
  params: Promise<{ "clinica-slug": string; "doctor-slug": string }>;
}

export async function generateMetadata({
  params,
}: PublicDoctorPageProps): Promise<Metadata> {
  const { "clinica-slug": clinicaSlug, "doctor-slug": doctorSlug } = await params;
  const data = await fetchPublicDoctorPage(clinicaSlug, doctorSlug);

  if (!data) {
    return {
      title: "Perfil no disponible — Vitalia",
      robots: { index: false, follow: false },
    };
  }

  const title = `${data.displayName}${data.specialty ? ` — ${data.specialty}` : ""}${data.clinicName ? ` | ${data.clinicName}` : ""}`;
  const description =
    data.sobreMi?.slice(0, 160) ??
    `Perfil profesional de ${data.displayName}${data.specialty ? `, ${data.specialty}` : ""}.`;

  // og:image — use avatar URL if available (absolute), else brand default
  // avatarKey es storage key (no URL pública resoluble) → og default de marca
  const ogImageUrl = `${APP_BASE_URL}/og-default.png`;

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "profile",
      images: [{ url: ogImageUrl, width: 400, height: 400, alt: data.displayName }],
      siteName: data.clinicName ?? "Vitalia",
    },
    twitter: {
      card: "summary",
      title,
      description,
      images: [ogImageUrl],
    },
    robots: { index: true, follow: true },
  };
}

// ── Initials helper ───────────────────────────────────────────────────────────

function getInitials(displayName: string): string {
  const parts = displayName.trim().split(/\s+/);
  return parts
    .slice(0, 2)
    .map((p) => p[0] ?? "")
    .join("")
    .toUpperCase();
}

// ── Page component ────────────────────────────────────────────────────────────

/**
 * PublicDoctorPage — no-auth Server Component.
 */
export default async function PublicDoctorPage({ params }: PublicDoctorPageProps) {
  const { "clinica-slug": clinicaSlug, "doctor-slug": doctorSlug } = await params;
  const data = await fetchPublicDoctorPage(clinicaSlug, doctorSlug);

  // Anti-enumeration: unknown slug / toggle-OFF / cross-tenant → identical 404 page
  if (!data) {
    notFound();
  }

  // El endpoint público devuelve el perfil PLANO (PublicDoctorProfileDTO top-level,
  // no anidado en publicProfile) + frontera null→[] (RN-D3D-6).
  const profile = {
    sobreMi: data.sobreMi ?? null,
    formacion: data.formacion ?? [],
    experiencia: data.experiencia ?? [],
    tratamientos: data.tratamientos ?? [],
    certificaciones: data.certificaciones ?? [],
    idiomas: data.idiomas ?? [],
  };
  const initials = getInitials(data.displayName);

  return (
    <main
      className="min-h-screen bg-background"
      aria-label={`Perfil público de ${data.displayName}`}
    >
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="bg-gradient-to-b from-agent-lisa/10 to-background">
        <div className="mx-auto max-w-2xl px-4 py-8 flex flex-col items-center gap-4 text-center">
          {/* Avatar */}
          {/* avatarKey = storage key interno (no URL pública) → iniciales (RN-D3D-8) */}
          <div
            className="h-24 w-24 rounded-full bg-agent-lisa/20 border-2 border-background shadow-lg flex items-center justify-center"
            aria-label={`Iniciales ${initials}`}
          >
            <span className="text-2xl font-bold text-agent-lisa">{initials}</span>
          </div>

          {/* Name + specialty */}
          <div>
            <h1 className="text-xl font-bold">{data.displayName}</h1>
            {data.specialty && (
              <p className="text-sm text-muted-foreground mt-0.5">{data.specialty}</p>
            )}
          </div>

          {/* Credential badge (mockup v3.2: "✓ Nro. de colegiatura — verificado") */}
          {data.credentialLabel && (
            <div className="flex items-center gap-1.5 rounded-full bg-green-100 dark:bg-green-900/40 px-3 py-1">
              <span className="text-green-600 dark:text-green-400 text-sm" aria-hidden="true">✓</span>
              <span className="text-sm text-green-700 dark:text-green-300 font-medium">
                Colegiatura {data.credentialLabel} — verificado
              </span>
            </div>
          )}

          {/* Clinic name */}
          {data.clinicName && <p className="text-xs text-muted-foreground">{data.clinicName}</p>}
        </div>
      </div>

      {/* ── Content ────────────────────────────────────────────────────── */}
      <div className="mx-auto max-w-2xl px-4 pb-12 space-y-6">
        {/* Sobre mí */}
        {profile.sobreMi && (
          <Section title="Sobre mí">
            <p className="text-sm leading-relaxed text-foreground/90">{profile.sobreMi}</p>
          </Section>
        )}

        {/* Formación */}
        {profile.formacion.length > 0 && (
          <Section title="Formación">
            <ul className="space-y-2 list-none" aria-label="Formación académica">
              {profile.formacion.map((f, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-agent-lisa mt-0.5 shrink-0" aria-hidden="true">·</span>
                  <div>
                    <p className="text-sm font-medium">{f.titulo}</p>
                    {(f.institucion ?? f.anio) && (
                      <p className="text-xs text-muted-foreground">
                        {[f.institucion, f.anio].filter(Boolean).join(" · ")}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Experiencia */}
        {profile.experiencia.length > 0 && (
          <Section title="Experiencia">
            <ul className="space-y-3 list-none" aria-label="Experiencia profesional">
              {/* F2: real wire fields are puesto/lugar/anios (NOT cargo/institucion/desde/hasta/descripcion) */}
              {profile.experiencia.map((e, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-agent-lisa mt-0.5 shrink-0" aria-hidden="true">·</span>
                  <div>
                    <p className="text-sm font-medium">{e.puesto}</p>
                    {e.lugar && (
                      <p className="text-xs text-muted-foreground">{e.lugar}</p>
                    )}
                    {e.anios != null && (
                      <p className="text-xs text-muted-foreground">
                        {e.anios} {e.anios === 1 ? "año" : "años"}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Tratamientos */}
        {profile.tratamientos.length > 0 && (
          <Section title="Tratamientos">
            <div className="flex flex-wrap gap-2" aria-label="Tratamientos">
              {profile.tratamientos.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center rounded-full bg-muted px-3 py-1 text-xs font-medium"
                >
                  {t}
                </span>
              ))}
            </div>
          </Section>
        )}

        {/* Certificaciones */}
        {profile.certificaciones.length > 0 && (
          <Section title="Certificaciones">
            <ul className="space-y-2 list-none" aria-label="Certificaciones">
              {profile.certificaciones.map((c, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-agent-lisa mt-0.5 shrink-0" aria-hidden="true">✓</span>
                  <p className="text-sm font-medium">{c}</p>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Idiomas — RN-D3D-5: only if > 1 */}
        {profile.idiomas.length > 1 && (
          <Section title="Idiomas">
            <div className="flex flex-wrap gap-2" aria-label="Idiomas">
              {profile.idiomas.map((l, i) => (
                <span key={i} className="rounded-full bg-muted px-3 py-1 text-sm">{l}</span>
              ))}
            </div>
          </Section>
        )}

        {/* Consultorio */}
        <Section title="Consultorio">
          <p className="text-sm">{data.clinicName ?? "—"}</p>
        </Section>
      </div>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="border-t border-border py-4">
        <p className="text-center text-xs text-muted-foreground">
          Perfil profesional verificado por la clínica
        </p>
      </footer>
    </main>
  );
}

// ── Section sub-component ─────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={`pub-section-${title.replace(/\s+/g, "-").toLowerCase()}`}>
      <h2
        id={`pub-section-${title.replace(/\s+/g, "-").toLowerCase()}`}
        className={cn(
          "text-sm font-semibold mb-2 flex items-center gap-2",
          "text-foreground",
        )}
      >
        <span aria-hidden="true" className="h-3 w-1 rounded-full bg-agent-lisa shrink-0" />
        {title}
      </h2>
      {children}
    </section>
  );
}
