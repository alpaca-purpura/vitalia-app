// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Metadata } from "next";

interface ClinicPublicPageProps {
  params: Promise<{ "clinic-slug": string }>;
}

export async function generateMetadata({
  params,
}: ClinicPublicPageProps): Promise<Metadata> {
  const slug = (await params)["clinic-slug"];
  return {
    title: `${slug} — Vitalia`,
  };
}

/**
 * Página pública de clínica — perfil, servicios y CTA de reserva.
 * Server Component — contenido real en T-fe-4.
 * D9: chrome UI Spanish neutro tuteo.
 */
export default async function ClinicPublicPage({
  params,
}: ClinicPublicPageProps) {
  const slug = (await params)["clinic-slug"];

  return (
    <main aria-label="Perfil público de clínica">
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">Clínica</h1>
      {/* TODO T-fe-4: renderizar <ClinicPublicProfile clinicSlug={slug} /> */}
      <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-sm text-gray-400">
        Perfil público &quot;{slug}&quot; (pendiente T-fe-4)
      </div>
    </main>
  );
}
