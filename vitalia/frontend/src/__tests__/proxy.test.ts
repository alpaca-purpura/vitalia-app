/**
 * Unit tests — proxy.ts (T-1 vitalia-auth-base-functional)
 *
 * Next.js 16 renamed `middleware.ts` → `proxy.ts` (deprecation v16.0.0). Same
 * location (src/), same config.matcher API. Clerk SDK helper `clerkMiddleware()`
 * is unchanged — its name is historical, just wraps a request handler.
 *
 * Verifica que la configuración del matcher en proxy.ts incluye las rutas
 * públicas correctas y protege el resto via auth.protect().
 *
 * Nota: clerkMiddleware de @clerk/nextjs no es directamente unit-testeable sin
 * un entorno Next.js completo. En su lugar, verificamos:
 *   1. La configuración de rutas públicas (publicRoutes array / matcher patterns)
 *   2. Que el matcher excluye _next y assets estáticos
 *   3. La existencia y estructura del archivo proxy.ts
 *
 * SC-01: Usuario no autenticado → redirect /sign-in (validado en E2E)
 * SC-02: Ruta pública /public/* → 200, sin redirect (validado en E2E)
 *
 * downstream-regression-na: brand-local proxy test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "fs";
import { resolve, join } from "path";

// __dirname = vitalia/frontend/src/__tests__
// ROOT = vitalia/frontend (2 levels up)
const ROOT = resolve(__dirname, "../..");
const PROXY_PATH = join(ROOT, "src", "proxy.ts");

describe("Vitalia FE — Proxy Clerk (T-1 SC-01, SC-02)", () => {
  it("proxy.ts exists at src/proxy.ts", () => {
    expect(
      existsSync(PROXY_PATH),
      "proxy.ts no encontrado en vitalia/frontend/src/proxy.ts — T-1 pendiente",
    ).toBe(true);
  });

  it("proxy.ts importa clerkMiddleware y createRouteMatcher de @clerk/nextjs/server", () => {
    if (!existsSync(PROXY_PATH)) {
      console.warn("[SKIP] proxy.ts no existe todavía — T-1 pendiente");
      return;
    }
    const source = readFileSync(PROXY_PATH, "utf-8");
    expect(source).toContain("clerkMiddleware");
    expect(source).toContain("createRouteMatcher");
    expect(source).toContain("@clerk/nextjs/server");
  });

  it("proxy.ts configura rutas públicas esperadas (sign-in, sign-up, public, webhooks, health)", () => {
    if (!existsSync(PROXY_PATH)) {
      console.warn("[SKIP] proxy.ts no existe todavía — T-1 pendiente");
      return;
    }
    const source = readFileSync(PROXY_PATH, "utf-8");

    expect(source).toContain("/sign-in");
    expect(source).toContain("/sign-up");
    expect(source).toContain("/public");
    expect(source).toContain("/api/v1/vitalia/webhooks");
    expect(source).toContain("/api/health");
  });

  it("proxy.ts exporta config con matcher que excluye _next y assets estáticos", () => {
    if (!existsSync(PROXY_PATH)) {
      console.warn("[SKIP] proxy.ts no existe todavía — T-1 pendiente");
      return;
    }
    const source = readFileSync(PROXY_PATH, "utf-8");

    expect(source).toContain("export const config");
    expect(source).toContain("matcher");
    expect(source).toContain("_next");
  });

  it("proxy.ts protege rutas no públicas via auth.protect()", () => {
    if (!existsSync(PROXY_PATH)) {
      console.warn("[SKIP] proxy.ts no existe todavía — T-1 pendiente");
      return;
    }
    const source = readFileSync(PROXY_PATH, "utf-8");

    expect(source).toContain("auth.protect()");
  });

  it("proxy.ts no contiene redirect manual ni RBAC (solo Clerk protect)", () => {
    if (!existsSync(PROXY_PATH)) {
      console.warn("[SKIP] proxy.ts no existe todavía — T-1 pendiente");
      return;
    }
    const source = readFileSync(PROXY_PATH, "utf-8");

    const hasManualRedirectToSignIn =
      /NextResponse\.redirect\s*\(.*sign-in/.test(source);
    expect(
      hasManualRedirectToSignIn,
      "proxy.ts usa NextResponse.redirect manual a /sign-in — Clerk lo maneja internamente",
    ).toBe(false);

    const hasRoleCheck = /role\s*===|sessionClaims\.role|user\.role/.test(
      source,
    );
    expect(
      hasRoleCheck,
      "proxy.ts contiene lógica RBAC (role checks) — no permitido en proxy",
    ).toBe(false);
  });

  it("proxy.ts no usa 'use client' (es un módulo server/edge, no React)", () => {
    if (!existsSync(PROXY_PATH)) {
      console.warn("[SKIP] proxy.ts no existe todavía — T-1 pendiente");
      return;
    }
    const source = readFileSync(PROXY_PATH, "utf-8");

    expect(
      source.includes('"use client"') || source.includes("'use client'"),
      "proxy.ts contiene 'use client' — proxy es Server/Edge Runtime, no React Component",
    ).toBe(false);
  });
});
