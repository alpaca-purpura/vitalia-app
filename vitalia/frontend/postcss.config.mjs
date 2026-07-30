/**
 * PostCSS config for Vitalia frontend — Tailwind v4
 *
 * Origen 2026-05-22 F1-S0: el setup original NO tenía postcss.config — Tailwind v4
 * directives (@tailwind base/components/utilities en globals.css) eran serviadas
 * literales al browser sin procesar. Style classes Shadcn (bg-background, text-foreground,
 * agent-lisa, etc.) NO se aplicaban → /test-stack/* rendered como HTML raw sin estilos.
 *
 * Fix: agregado @tailwindcss/postcss plugin para procesar @tailwind directives.
 * Tailwind v4 requiere este plugin explícitamente (v3 venía built-in en Next.js).
 *
 * Ref: https://tailwindcss.com/docs/installation/using-postcss
 */
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
