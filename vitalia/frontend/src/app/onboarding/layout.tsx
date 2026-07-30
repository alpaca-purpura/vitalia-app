// cap: onboarding.clinic-onboarding-3step
// story-origin: TBD
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Configuración inicial — Vitalia",
};

/**
 * Layout del wizard de incorporación — barra de progreso + contenedor centrado.
 * Progreso real renderizado en T-fe-3.
 */
export default function OnboardingLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex min-h-screen flex-col">
      {/* TODO T-fe-3: barra de progreso del wizard (3 pasos) */}
      <header className="border-b bg-white px-6 py-4">
        <div className="mx-auto max-w-2xl">
          <div className="h-2 rounded-full bg-gray-200">
            <div
              className="h-2 rounded-full bg-teal-500"
              style={{ width: "33%" }}
            />
          </div>
        </div>
      </header>
      <main className="flex flex-1 items-start justify-center px-6 py-12">
        <div className="w-full max-w-2xl">{children}</div>
      </main>
    </div>
  );
}
