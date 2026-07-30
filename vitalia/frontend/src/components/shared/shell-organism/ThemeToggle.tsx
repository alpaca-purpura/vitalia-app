// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s1-TBD
"use client";

/**
 * ThemeToggle — F1-S1 vitalia-fase1-design-tokens-theme
 *
 * Toggle button for light/dark theme. Consumes next-themes ThemeProvider
 * (mounted in app/providers.tsx with attribute="data-theme").
 *
 * 03-arch.md § 2.3 — implementation verbatim.
 * Named export (no default export) per FSD-Lite enforce.
 * No wrapper useTheme hook — direct import per D5 ratificada.
 *
 * HIPAA-lite: no-phi-scope — UI shell component, zero PHI.
 */
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={`Cambiar tema (actual: ${isDark ? "oscuro" : "claro"})`}
      aria-pressed={isDark}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      data-testid="theme-toggle"
    >
      {isDark ? (
        <Sun className="h-[1.2rem] w-[1.2rem]" />
      ) : (
        <Moon className="h-[1.2rem] w-[1.2rem]" />
      )}
      <span className="sr-only">Cambiar tema</span>
    </Button>
  );
}
