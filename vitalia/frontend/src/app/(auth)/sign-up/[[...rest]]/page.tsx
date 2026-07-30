// cap: auth.sign-in-sign-up-pages
// story-origin: TBD
import type { Metadata } from "next";
import { SignUp } from "@clerk/nextjs";

export const metadata: Metadata = {
  title: "Crear cuenta — Vitalia",
};

/**
 * Página de registro — Clerk SignUp.
 *
 * SC-04: <SignUp /> renderizado, sin placeholder.
 * Apariencia alineada con design tokens Vitalia:
 *   colorPrimary       = var(--vitalia-cian-color)       [hero, CTA primario]
 *   colorTextSecondary = var(--vitalia-text-muted-color)  [texto secundario]
 *   borderRadius       = 0.5rem
 */
export default function SignUpPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-vitalia-bg p-6">
      <SignUp
        appearance={{
          variables: {
            colorPrimary: "var(--vitalia-cian-color)",
            colorTextSecondary: "var(--vitalia-text-muted-color)",
            borderRadius: "0.5rem",
            fontFamily: "inherit",
          },
        }}
      />
    </main>
  );
}
