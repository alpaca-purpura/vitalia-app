// cap: public_landing.public-clinic-landing
// story-origin: TBD
import type { Metadata } from "next";

interface ClinicBookingPageProps {
  params: Promise<{ "clinic-slug": string }>;
}

export async function generateMetadata({
  params,
}: ClinicBookingPageProps): Promise<Metadata> {
  const slug = (await params)["clinic-slug"];
  return {
    title: `Reservar cita — ${slug} — Vitalia`,
  };
}

/**
 * Formulario público de reserva de cita en clínica.
 * Server Component — delegará en <BookingFormClient /> (T-fe-4).
 * D9: chrome UI Spanish neutro tuteo.
 */
export default async function ClinicBookingPage({
  params,
}: ClinicBookingPageProps) {
  const slug = (await params)["clinic-slug"];

  return (
    <main aria-label="Reservar cita">
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">
        Reservar cita
      </h1>
      <p className="mb-4 text-sm text-gray-500">
        Selecciona el servicio, el profesional y el horario que prefieres.
      </p>
      {/* TODO T-fe-4: renderizar <BookingFormClient clinicSlug={slug} /> */}
      <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-sm text-gray-400">
        Formulario de reserva &quot;{slug}&quot; (pendiente T-fe-4)
      </div>
    </main>
  );
}
