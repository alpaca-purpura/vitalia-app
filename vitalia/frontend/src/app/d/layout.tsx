// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * /d/layout.tsx — Layout for public doctor profiles (no auth).
 *
 * Minimal layout — no shell-organism, no sidebar, no tenant context.
 * Routes under /d/** are excluded from Clerk auth via proxy.ts isPublicRoute.
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores
 */

export default function PublicDoctorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
