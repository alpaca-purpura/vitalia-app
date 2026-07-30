/**
 * LogoMark showcase — test page fixture
 * F1-S2 vitalia-fase1-topbar-global — T-6
 *
 * Renders a 6-cell grid of all LogoMark combinations (3 sizes × 2 variants)
 * for visual golden snapshots (both light and dark mode).
 *
 * This fixture is imported by the Next.js test-stack route wrapper at:
 *   src/app/test-stack/logo-mark/page.tsx
 *
 * Accessible via dev server: /test-stack/logo-mark
 * NOT protected by Clerk auth (public dev-only, no PHI).
 *
 * HIPAA-lite: no-phi-scope — test fixture, zero PHI.
 * downstream-regression-na: brand-local E2E fixture; no cross-brand consumers
 */

import { LogoMark } from "@/components/shared/shell-organism/LogoMark";

const SIZES = ["sm", "md", "lg"] as const;
const VARIANTS = ["full", "mark"] as const;

export default function LogoMarkShowcasePage() {
  return (
    <div
      className="min-h-screen bg-background p-8"
      data-testid="logo-mark-showcase"
    >
      <h1 className="text-sm font-medium text-muted-foreground mb-6">
        Vitalia — LogoMark (F1-S2 baseline — 6 combinaciones)
      </h1>

      <div className="grid grid-cols-3 gap-8">
        {VARIANTS.map((variant) =>
          SIZES.map((size) => (
            <div
              key={`${variant}-${size}`}
              className="flex flex-col items-start gap-2 p-4 rounded-lg border border-border"
              data-testid={`logo-cell-${variant}-${size}`}
            >
              <span className="text-xs text-muted-foreground font-mono">
                {variant}/{size}
              </span>
              <LogoMark variant={variant} size={size} />
            </div>
          )),
        )}
      </div>
    </div>
  );
}
