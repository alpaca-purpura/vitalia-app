/**
 * vite.config.ts — Vite UMD build config for the Vitalia booking widget.
 *
 * Produces:
 *   dist/widget.umd.js   — UMD bundle exposing VitaliaBookingWidget global
 *   dist/widget.css      — scoped CSS
 *
 * Per 03-arch-fe.md § 9.1 + T-widget-1 acceptance A1.
 *
 * React is BUNDLED (not external) to allow standalone embed on any page
 * without requiring the host to provide React. Trade-off: larger bundle
 * but zero host-page dependency. Accepted per spec § 17 Q5=B.
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: resolve(__dirname, "src/widget-entry.tsx"),
      name: "VitaliaBookingWidget",
      fileName: "widget",
      formats: ["umd"],
    },
    rollupOptions: {
      /**
       * React is BUNDLED into the widget (not external).
       * Rationale: embeddable widget must be standalone — clinic landing pages
       * may not have React available. Bundle size ~130kb gzipped (acceptable
       * for a checkout widget). Per spec § 17 Q5=B trade-off accepted.
       */
      external: [],
      output: {
        // Single UMD file for script tag embedding
        globals: {},
        // Ensure CSS is extracted to widget.css (not inlined)
        assetFileNames: "widget.[ext]",
        entryFileNames: "widget.umd.js",
      },
    },
    // Output directory relative to widget/ directory
    outDir: "dist",
    emptyOutDir: true,
    // Minified production output
    minify: "terser",
    sourcemap: true,
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  test: {
    environment: "happy-dom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
  },
});
