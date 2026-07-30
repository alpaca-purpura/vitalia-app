import path from "path";

import type { NextConfig } from "next";

// BE URL for rewrites — dev uses NEXT_PUBLIC_API_URL (localhost:8002), prod/staging uses
// INTERNAL_API_URL (Docker network). Client-side fetch("/api/v1/...") hits Next.js first;
// rewrite transparently proxies it to the BE so no CORS config needed on the BE side.
// Bug fix: previously missing → useTenants / useCurrentUser / other client hooks got 404
// from Next.js (no route handler exists for /api/v1/*). (vitalia-shell-core-hardening T-7)
const beUrl =
  process.env["INTERNAL_API_URL"] ??
  process.env["NEXT_PUBLIC_API_URL"] ??
  "http://localhost:8002";

const nextConfig: NextConfig = {
  // distDir env-overridable: el contenedor docker dev es dueño de .next (root);
  // un prod-build en host usa NEXT_DISTDIR=.next-prod (host-writable) sin tocar
  // el .next del contenedor. Sin env → .next (default, contenedor intacto).
  distDir: process.env["NEXT_DISTDIR"] ?? ".next",
  // output env-gated: standalone (deploy/docker) por defecto; un prod-build de
  // verificación en host usa NEXT_NO_STANDALONE=1 → output normal así `next start`
  // sirve (next start NO soporta standalone).
  ...(process.env["NEXT_NO_STANDALONE"] ? {} : { output: "standalone" as const }),
  // Turbopack (HB-78): el kit @luana/* vive en core/ (fuera del app root) → turbopack no lo
  // resuelve sin `root` = monorepo root; y resuelve zustand/middleware a CJS → named exports
  // undefined ("(void 0) is not a function") sin forzar sus subpaths ESM con resolveAlias.
  // Requiere root .npmrc node-linker=hoisted + patches/zustand.patch (compartidos). Doc + receta:
  // nicolify (1ra marca migrada) docker-compose.dev.yml. Stores: `import {create} from "zustand/react"`.
  turbopack: {
    root: path.join(__dirname, "..", ".."),
    resolveAlias: {
      zustand: "zustand/esm/index.mjs",
      "zustand/react": "zustand/esm/react.mjs",
      "zustand/vanilla": "zustand/esm/vanilla.mjs",
      "zustand/middleware": "zustand/esm/middleware.mjs",
    },
  },
  transpilePackages: ["@luana/design-tokens", "@luana/hooks", "@luana/ui-kit"],
  // Cross-origin Cloudflare Tunnel dev hostname for HMR + dev resources.
  // Without this Next.js blocks /_next/webpack-hmr from dev-app.vitalialat.com.
  allowedDevOrigins: ["dev-app.vitalialat.com"],
  images: {
    // Hosts permitidos para next/image. El logo de marca (y assets) se sirven desde
    // Cloudflare R2: dev usa el dominio público gestionado pub-<hash>.r2.dev; cuando
    // se provisione el dominio propio de prod/staging (assets-*.vitalialat.com) agregarlo aquí.
    remotePatterns: [{ protocol: "https", hostname: "**.r2.dev" }],
  },
  // Proxy all /api/* and /public/* requests to the BE.
  // Client Components call fetchClient("/api/v1/...") with a relative URL; Next.js
  // intercepts and forwards to the BE — avoids CORS issues + keeps auth headers.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${beUrl}/api/:path*`,
      },
      {
        source: "/public/:path*",
        destination: `${beUrl}/public/:path*`,
      },
    ];
  },
};

export default nextConfig;
