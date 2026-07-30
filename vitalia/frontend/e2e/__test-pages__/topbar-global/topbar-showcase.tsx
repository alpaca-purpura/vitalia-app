/**
 * TopBarGlobal showcase — test page fixture
 * F1-S2 vitalia-fase1-topbar-global — T-6
 *
 * T-V2 (platform-lift-shell-chrome-ui-kit): TopBarGlobal (local chrome) replaced
 * by TopBarShell from @luana/ui-kit with vitalia brand slots injected inline.
 * TopBarShell preserves data-testid="topbar-global" so e2e specs are unaffected.
 *
 * Renders TopBarShell isolated in full-width layout for visual testing.
 * Used by Playwright visual and a11y specs.
 *
 * This fixture is imported by the Next.js test-stack route wrapper at:
 *   src/app/test-stack/topbar-global/page.tsx
 *
 * Accessible via dev server: /test-stack/topbar-global
 * NOT protected by Clerk auth (public dev-only, no PHI).
 *
 * HIPAA-lite: no-phi-scope — test fixture, zero PHI.
 * downstream-regression-na: brand-local E2E fixture; no cross-brand consumers
 */

"use client";

import { TopBarShell } from "@luana/ui-kit";
import { LogoMark } from "@/components/shared/shell-organism/LogoMark";
import { TenantSwitcher } from "@/components/shared/shell-organism/TenantSwitcher";
import { ThemeToggle } from "@/components/shared/shell-organism/ThemeToggle";
import { useShellStoreKit } from "@/stores/shell-store";

export default function TopBarShowcasePage() {
  return (
    <div className="min-h-screen bg-background" data-testid="topbar-showcase">
      <TopBarShell
        supervisorName="Valeria"
        logoSlot={<LogoMark />}
        rightClusterSlot={
          <>
            <ThemeToggle />
            <TenantSwitcher />
          </>
        }
        useShellStore={useShellStoreKit}
      />
      {/* Main content anchor for skip link target (WCAG 2.4.1) */}
      <main id="main-content" tabIndex={-1} className="p-6">
        <h1 className="text-lg font-semibold text-foreground">
          Vitalia — TopBar Global (F1-S2 baseline)
        </h1>
        <p className="text-sm text-muted-foreground mt-2">
          Página de prueba para TopBarGlobal. Clínica Aurora Dental — Mendoza,
          Argentina.
        </p>
      </main>
    </div>
  );
}
