import type { Config } from "tailwindcss";

/**
 * Vitalia — Tailwind CSS config
 * SSoT: vitalia/docs/architecture/design-system.md § 5
 * Tokens consumed via CSS vars in app/globals.css (hsl(var(--vitalia-X)))
 * ADR: vitalia/docs/architecture/ADR-vitalia-001-shared-vs-fork.md
 */
const config: Config = {
  // darkMode: ['class', '[data-theme="dark"]'] activates Tailwind dark: variants when either
  // .dark class OR [data-theme="dark"] attribute is present on <html>. next-themes uses
  // attribute="data-theme" → sets <html data-theme="dark">, so we need the attribute selector.
  // See: vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md § 5.2 (D4 ratificada 2026-05-22)
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
    "./widget/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        /* ── Shadcn standard semantic tokens (F1-S0) ─────────────────────── */
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        success: {
          DEFAULT: "hsl(var(--success))",
          foreground: "hsl(var(--success-foreground))",
        },
        warning: {
          DEFAULT: "hsl(var(--warning))",
          foreground: "hsl(var(--warning-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",

        /* ── Agent tokens (7 agents × base + soft) ───────────────────────── */
        agent: {
          lisa: "hsl(var(--agent-lisa))",
          "lisa-soft": "hsl(var(--agent-lisa-soft))",
          lucas: "hsl(var(--agent-lucas))",
          "lucas-soft": "hsl(var(--agent-lucas-soft))",
          adrian: "hsl(var(--agent-adrian))",
          "adrian-soft": "hsl(var(--agent-adrian-soft))",
          valeria: "hsl(var(--agent-valeria))",
          "valeria-soft": "hsl(var(--agent-valeria-soft))",
          camila: "hsl(var(--agent-camila))",
          "camila-soft": "hsl(var(--agent-camila-soft))",
          mateo: "hsl(var(--agent-mateo))",
          "mateo-soft": "hsl(var(--agent-mateo-soft))",
          config: "hsl(var(--agent-config))",
        },

        /* ── Brand core (4+1 colores oficiales brandbook 2026-05-17) ──────── */
        "vitalia-cian": "hsl(var(--vitalia-cian))",
        "vitalia-purpura": "hsl(var(--vitalia-purpura))",
        "vitalia-amarillo": "hsl(var(--vitalia-amarillo))",
        "vitalia-azul-marino": "hsl(var(--vitalia-azul-marino))",
        "vitalia-verde-lima": "hsl(var(--vitalia-verde-lima))",

        /* ── Neutrales (app shell) ───────────────────────────────────────── */
        "vitalia-bg": "hsl(var(--vitalia-bg))",
        "vitalia-surface": "hsl(var(--vitalia-surface))",
        "vitalia-surface-alt": "hsl(var(--vitalia-surface-alt))",
        "vitalia-muted": "hsl(var(--vitalia-muted))",
        "vitalia-text": "hsl(var(--vitalia-text))",
        "vitalia-text-muted": "hsl(var(--vitalia-text-muted))",
        "vitalia-text-faint": "hsl(var(--vitalia-text-faint))",
        "vitalia-border": "hsl(var(--vitalia-border))",
        "vitalia-border-soft": "hsl(var(--vitalia-border-soft))",

        /* ── Semantic (status médico) ─────────────────────────────────────── */
        "vitalia-success": "hsl(var(--vitalia-success))",
        "vitalia-warning": "hsl(var(--vitalia-warning))",
        "vitalia-danger": "hsl(var(--vitalia-danger))",
        "vitalia-info": "hsl(var(--vitalia-info))",
      },

      backgroundImage: {
        /* ── Gradients (consume CSS vars defined in globals.css) ─────────── */
        "vitalia-gradient-mariposa": "var(--vitalia-gradient-mariposa)",
        "vitalia-gradient-agent": "var(--vitalia-gradient-agent)",
        "vitalia-gradient-app-cta": "var(--vitalia-gradient-app-cta)",
      },

      fontFamily: {
        /* ── Typography stack (3 fuentes — design-system.md § 2) ─────────── */
        display: [
          "var(--font-general-sans)",
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
        ],
        heading: [
          "var(--font-manrope)",
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
        ],
        body: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
      },

      borderRadius: {
        /* ── Shape tokens (design-system.md § 3 + Shadcn F1-S0) ─────────── */
        DEFAULT: "var(--radius)",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        bubble: "var(--radius-bubble)",
        pill: "var(--radius-pill)",
        /* ── Control atom radius (RN-7 lift) ────────────────────────────── */
        /* Brand-overridable via --radius-control in globals.css. Falls back  */
        /* to vitalia's md = calc(var(--radius) - 2px) so an omitted token   */
        /* also renders at 8px (identical to pre-lift rounded-md behaviour). */
        control: "var(--radius-control, calc(var(--radius) - 2px))",
      },
    },
  },
  plugins: [],
};

export default config;
