/**
 * lighthouserc.cjs — Configuración Lighthouse CI para vitalia/frontend
 *
 * Validator ID: visual_perf_budget_lighthouse
 * Story: vitalia-slice-1-marketing
 * Ticket: T-mk-fe-7
 *
 * Presupuesto de rendimiento (03-arch-fe.md § 9):
 *   - LCP (Largest Contentful Paint) < 2500ms
 *   - INP (Interaction to Next Paint) < 200ms
 *   - CLS (Cumulative Layout Shift) < 0.1
 *   - FCP (First Contentful Paint) < 1800ms
 *   - TBT (Total Blocking Time) < 300ms
 *
 * Ejecución (requiere stack corriendo + @lhci/cli instalado):
 *   npx lhci autorun --config=lighthouserc.cjs
 * O directamente:
 *   npx lhci collect --url=http://localhost:3002/marketing
 *   npx lhci assert --config=lighthouserc.cjs
 *
 * CI/CD: corre en ci.yml en PRs que tocan vitalia/frontend/src/features/marketing/
 *
 * downstream-regression-na: brand-local Lighthouse config; no cross-brand consumers
 */

"use strict";

module.exports = {
  ci: {
    collect: {
      // URL de la página marketing en dev local
      url: [process.env.LHCI_URL || "http://localhost:3002/marketing"],
      numberOfRuns: 3,
      // Opciones de Chrome para entorno CI/Linux (sin GPU, sin sandbox)
      chromePath: process.env.CHROME_PATH,
      settings: {
        chromeFlags: [
          "--no-sandbox",
          "--disable-dev-shm-usage",
          "--disable-gpu",
          "--headless=new",
        ],
        // Throttling representativo de red 4G LTE (Lighthouse recomendado)
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 4,
        },
        // Emulación móvil Nexus 5X (estándar Lighthouse)
        formFactor: "mobile",
        screenEmulation: {
          mobile: true,
          width: 360,
          height: 640,
          deviceScaleFactor: 2.625,
          disabled: false,
        },
        // Accesibilidad siempre activa
        onlyCategories: ["performance", "accessibility", "best-practices"],
        // Skipear audits que no aplican al dominio clínico (sin manifest PWA)
        skipAudits: [
          "is-on-https",         // HTTPS no requerido en dev local
          "service-worker",      // No es PWA por diseño
          "installable-manifest", // No es PWA
          "apple-touch-icon",    // No requerido
        ],
      },
    },
    assert: {
      preset: "lighthouse:no-pwa",
      assertions: {
        // ─── Core Web Vitals (presupuesto per 03-arch-fe.md § 9) ──────────

        // LCP < 2500ms (Good threshold según Web.dev)
        "largest-contentful-paint": ["error", { maxNumericValue: 2500 }],

        // INP < 200ms (Good threshold según Web.dev — medido via TBT proxy)
        // Nota: Lighthouse mide TBT como proxy de INP en audits de lab
        "total-blocking-time": ["warn", { maxNumericValue: 300 }],

        // CLS < 0.1 (Good threshold según Web.dev)
        "cumulative-layout-shift": ["error", { maxNumericValue: 0.1 }],

        // FCP < 1800ms (Good threshold según Web.dev)
        "first-contentful-paint": ["warn", { maxNumericValue: 1800 }],

        // ─── Scores mínimos ───────────────────────────────────────────────

        // Performance score ≥ 70 (permisivo en dev con mocking)
        "categories:performance": ["warn", { minScore: 0.7 }],

        // Accessibility score ≥ 90 (WCAG 2.1 AA target)
        "categories:accessibility": ["error", { minScore: 0.9 }],

        // Best practices ≥ 80
        "categories:best-practices": ["warn", { minScore: 0.8 }],

        // ─── Audits específicos de accesibilidad ─────────────────────────

        // Botones deben tener texto accesible
        "button-name": "error",

        // Imágenes/figuras deben tener alt o aria-label
        "image-alt": "error",

        // Contraste de color mínimo (WCAG 2.1 AA)
        "color-contrast": "error",

        // Links deben tener texto descriptivo
        "link-name": "error",

        // Meta viewport presente (requerido para móvil)
        viewport: "error",

        // Elementos interactivos no deben superponer área de toque de 48px
        "tap-targets": "warn",

        // ─── Audits de rendimiento clave ─────────────────────────────────

        // Evitar render-blocking resources
        "render-blocking-resources": "warn",

        // JS mínimo en critical path
        "unused-javascript": "warn",

        // CSS no crítico diferido
        "unused-css-rules": "warn",

        // Usar formatos de imagen modernos (WebP/AVIF)
        "uses-optimized-images": "warn",

        // ─── Desactivados (no aplican al contexto) ────────────────────────
        "maskable-icon": "off",
        "splash-screen": "off",
        "themed-omnibox": "off",
        "content-width": "off",
      },
    },
    upload: {
      // En CI, subir a LHCI server si está configurado; en dev, usar filesystem
      target: process.env.LHCI_SERVER_URL ? "lhci" : "filesystem",
      serverBaseUrl: process.env.LHCI_SERVER_URL,
      token: process.env.LHCI_BUILD_TOKEN,
      outputDir: "./.lighthouseci",
    },
  },
};
