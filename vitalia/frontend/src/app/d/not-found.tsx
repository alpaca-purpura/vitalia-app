// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * not-found.tsx — Anti-enumeration 404 for /d/** routes.
 *
 * RN-D3D-9: toggle-OFF / unknown slug / cross-tenant slug all return
 * IDENTICAL "perfil no disponible" response — indistinguishable to prevent enumeration.
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores
 */

export default function PublicDoctorNotFound() {
  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center bg-background px-4"
      aria-label="Perfil no disponible"
    >
      <div className="text-center space-y-3 max-w-sm">
        <div
          className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mx-auto"
          aria-hidden="true"
        >
          <span className="text-2xl text-muted-foreground">👤</span>
        </div>
        <h1 className="text-lg font-semibold">Perfil no disponible</h1>
        <p className="text-sm text-muted-foreground">
          Este perfil profesional no está disponible en este momento.
        </p>
      </div>
    </main>
  );
}
