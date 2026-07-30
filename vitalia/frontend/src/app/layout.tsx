// cap: __shared__
// story-origin: TBD
import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { TenantStoreBootstrap } from "@/components/shared/shell-organism/TenantStoreBootstrap";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "Vitalia — Plataforma de salud",
  description:
    "Vitalia — Gestión clínica integral para profesionales de salud en Latinoamérica",
};

/**
 * RootLayout — root layout for Vitalia app.
 *
 * F1-S2 (T-5): Added WCAG 2.4.1 skip link before Providers wrapper.
 * Skip link is sr-only at rest; visible on keyboard focus (focus:not-sr-only).
 * Target: #main-content — id is set on <main> in AppShell (components/shared/shell/AppShell.tsx).
 *
 * F1-S3 (T-8): Added TenantStoreBootstrap inside Providers for tenant store hydration.
 * TenantStoreBootstrap is an invisible Client Component that mounts useTenants() +
 * useSignOutCleanup() hooks. Must be inside ClerkProvider + QueryClientProvider.
 *
 * Spanish neutro: "Saltar al contenido" (no voseo).
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className="min-h-screen bg-white font-sans antialiased">
        {/* WCAG 2.4.1 Bypass Blocks — skip link (T-5) */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:z-[200] focus:p-2 focus:bg-primary focus:text-primary-foreground"
        >
          Saltar al contenido
        </a>
        <Providers>
          {/* TenantStoreBootstrap: invisible Client Component — hydrates tenant store on boot */}
          <TenantStoreBootstrap />
          {children}
          {/* bug7 r3: Toaster sonner NUNCA estuvo montado — todos los
              toast.success/error del app (lisa/adrian/mateo) eran no-ops
              live. El feedback de guardado del round-1 dependía de esto. */}
          <Toaster position="bottom-right" richColors />
        </Providers>
      </body>
    </html>
  );
}
