/**
 * ThemeToggle showcase — test page fixture
 * F1-S1 vitalia-fase1-design-tokens-theme — 03-arch.md § 2.9
 *
 * Renders ThemeToggle isolated in a centered card with controlled padding
 * for consistent snapshot. Does NOT embed TopBar global (that is F1-S2 scope).
 *
 * This fixture is imported by the Next.js test-stack route wrapper at:
 *   src/app/test-stack/design-tokens-theme/page.tsx
 *
 * Accessible via dev server: /test-stack/design-tokens-theme
 * NOT protected by Clerk auth (public dev-only, no PHI).
 */
import { ThemeToggle } from "@/components/shared/shell-organism/ThemeToggle";

export default function ThemeToggleShowcasePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="rounded-lg border bg-card p-8 shadow-sm">
        <h1 className="text-sm font-medium text-muted-foreground mb-4">
          Vitalia — Tema (F1-S1 baseline)
        </h1>
        <ThemeToggle />
      </div>
    </div>
  );
}
