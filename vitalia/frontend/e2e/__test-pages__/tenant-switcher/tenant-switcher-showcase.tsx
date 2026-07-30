/**
 * TenantSwitcher showcase — test page fixture
 * F1-S3 vitalia-fase1-tenant-switcher — T-FIX-1
 *
 * T-V2 (platform-lift-shell-chrome-ui-kit): TopBarGlobal (local chrome) replaced
 * by TopBarShell from @luana/ui-kit with vitalia brand slots injected inline.
 * TopBarShell preserves data-testid="topbar-global" so e2e specs are unaffected.
 *
 * Renders TopBarShell isolated in full-width layout for visual testing.
 * TopBarShell mounts TenantSwitcher via rightClusterSlot (F1-S3 T-8).
 * Used by Playwright visual and functional specs targeting TenantSwitcher.
 *
 * This fixture is imported by the Next.js test-stack route wrapper at:
 *   src/app/test-stack/tenant-switcher/page.tsx
 *
 * Accessible via dev server: /test-stack/tenant-switcher
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

export default function TenantSwitcherShowcasePage() {
  return (
    <div
      className="min-h-screen bg-background"
      data-testid="tenant-switcher-showcase"
    >
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
          Vitalia — TenantSwitcher (F1-S3 baseline)
        </h1>
        <p className="text-sm text-muted-foreground mt-2">
          Página de prueba para TenantSwitcher. Accede al componente en la barra
          de navegación superior.
        </p>
      </main>
    </div>
  );
}
