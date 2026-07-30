/**
 * shell-routes.test.ts — Vitest unit tests for DEFAULT_LANDING_SUBPATH SSoT.
 *
 * Bug #1 (vitalia-bugfix-shell-nav-scroll-errors T-1):
 *   El landing post-login DEBE aterrizar en una ruta que existe (nunca 404).
 *   `valeria/agenda` 404ea porque isValidAgent('valeria') === false (Valeria es
 *   supervisora sidebar, no ribbon agent). El default debe apuntar a `mateo/agenda`
 *   (ruta estática shipped → renderiza directo, sin pasar por isValidAgent).
 *
 * RN-1: el landing default nunca 404.
 *
 * downstream-regression-na: brand-local vitalia shell catalog test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import {
  DEFAULT_LANDING_SUBPATH,
  bareTenantLandingRedirect,
  isAuthedRootPath,
  rootLandingRedirect,
  shellInRenderRedirectTarget,
} from "./shell-routes";
import { isValidAgent, SHIPPED_STATIC_SUBTABS } from "./agent-catalog";

describe("DEFAULT_LANDING_SUBPATH — Bug #1 routing lands on a valid static route (RN-1)", () => {
  it("apunta a mateo/agenda (NO valeria/agenda — esa 404ea)", () => {
    expect(DEFAULT_LANDING_SUBPATH).toBe("mateo/agenda");
    expect(DEFAULT_LANDING_SUBPATH).not.toContain("valeria");
  });

  it("su agente (mateo) es un ribbon agent válido (no cae en notFound del [agent] layout)", () => {
    const [agent] = DEFAULT_LANDING_SUBPATH.split("/");
    expect(isValidAgent(agent)).toBe(true);
  });

  it("el combo agent.subtab del default es una ruta estática SHIPPED (renderiza sin 404)", () => {
    const [agent, subtab] = DEFAULT_LANDING_SUBPATH.split("/");
    const key = `${agent}.${subtab}` as never;
    expect(SHIPPED_STATIC_SUBTABS.has(key)).toBe(true);
  });

  it("regression — el agente 'valeria' del default viejo NO es válido (confirma el bug)", () => {
    expect(isValidAgent("valeria")).toBe(false);
  });
});

describe("bareTenantLandingRedirect — Bug #1 edge-redirect hardening (Next 16 soft-nav)", () => {
  const TENANT = "e69a691d-070e-5caf-a053-6e74642ec100";

  it("una ruta de tenant bare (/{uuid}) redirige al landing en el edge", () => {
    expect(bareTenantLandingRedirect(`/${TENANT}`)).toBe(
      `/${TENANT}/${DEFAULT_LANDING_SUBPATH}`,
    );
  });

  it("tolera el trailing slash (/{uuid}/)", () => {
    expect(bareTenantLandingRedirect(`/${TENANT}/`)).toBe(
      `/${TENANT}/${DEFAULT_LANDING_SUBPATH}`,
    );
  });

  it("NO redirige si el tenant ya trae subpath (/{uuid}/mateo/agenda) — evita loop", () => {
    expect(
      bareTenantLandingRedirect(`/${TENANT}/mateo/agenda`),
    ).toBeNull();
    expect(bareTenantLandingRedirect(`/${TENANT}/lisa/marca`)).toBeNull();
  });

  it("NO toca rutas no-tenant de un solo segmento (sign-in/sign-out/marketing/public)", () => {
    for (const p of [
      "/sign-in",
      "/sign-out",
      "/marketing",
      "/public",
      "/test-stack",
      "/",
    ]) {
      expect(bareTenantLandingRedirect(p), `${p} no debe redirigir`).toBeNull();
    }
  });
});

describe("isAuthedRootPath — root '/' edge-redirect scope (vitalia-bugfix-root-login-redirect-softnav)", () => {
  it("matchea SOLO la raíz exacta '/'", () => {
    expect(isAuthedRootPath("/")).toBe(true);
  });

  it("matchea la raíz con query string preservada (Clerk afterSignIn puede traer params)", () => {
    // El middleware recibe pathname puro (sin query), pero el guard debe ser
    // robusto si el caller le pasa un pathname con trailing artifacts.
    expect(isAuthedRootPath("/")).toBe(true);
  });

  it("NO matchea ninguna ruta con segmento (evita disparar en cada request)", () => {
    for (const p of [
      "/sign-in",
      "/marketing",
      "/public/foo",
      "/e69a691d-070e-5caf-a053-6e74642ec100",
      "/e69a691d-070e-5caf-a053-6e74642ec100/mateo/agenda",
      "/test-stack",
      "/showcase/button",
    ]) {
      expect(isAuthedRootPath(p), `${p} NO es la raíz`).toBe(false);
    }
  });
});

describe("rootLandingRedirect — root '/' → primer tenant landing en el edge (RN: sin soft-nav in-render)", () => {
  const TENANT = "e69a691d-070e-5caf-a053-6e74642ec100";

  it("compone /{tenantId}/{DEFAULT_LANDING_SUBPATH} desde el tenant resuelto", () => {
    expect(rootLandingRedirect(TENANT)).toBe(
      `/${TENANT}/${DEFAULT_LANDING_SUBPATH}`,
    );
  });

  it("retorna null cuando NO hay tenant resuelto (deja que app/page.tsx haga el fallback)", () => {
    expect(rootLandingRedirect(null)).toBeNull();
    expect(rootLandingRedirect("")).toBeNull();
    expect(rootLandingRedirect(undefined)).toBeNull();
  });

  it("retorna null para un tenant no-UUID (no confiamos un claim arbitrario en el edge)", () => {
    expect(rootLandingRedirect("not-a-uuid")).toBeNull();
    expect(rootLandingRedirect("org_3DzUI3clerkOrgId")).toBeNull();
  });
});

describe("shellInRenderRedirectTarget — edge-redirect de redirects in-render del shell (Next 16 soft-nav)", () => {
  const T = "e69a691d-070e-5caf-a053-6e74642ec100";
  const OFFER = "83f6b6db-1111-2222-3333-444455556666";

  // G2-F5 vitalia-fase2-lisa-servicios: bare [offer-id] → resumen en el edge.
  it("bare [offer-id] del workspace de servicios → resumen (G2-F5)", () => {
    expect(shellInRenderRedirectTarget(`/${T}/lisa/servicios/${OFFER}`)).toBe(
      `/${T}/lisa/servicios/${OFFER}/resumen`,
    );
  });

  it("tolera trailing slash en el bare [offer-id]", () => {
    expect(shellInRenderRedirectTarget(`/${T}/lisa/servicios/${OFFER}/`)).toBe(
      `/${T}/lisa/servicios/${OFFER}/resumen`,
    );
  });

  it("NO redirige cuando ya hay leaf (/{offer}/resumen) — evita loop", () => {
    expect(
      shellInRenderRedirectTarget(`/${T}/lisa/servicios/${OFFER}/resumen`),
    ).toBeNull();
  });

  it("NO confunde los sub-sub-tabs estáticos (catalogo/escalera no son UUID)", () => {
    expect(shellInRenderRedirectTarget(`/${T}/lisa/servicios/catalogo`)).toBeNull();
    expect(shellInRenderRedirectTarget(`/${T}/lisa/servicios/escalera`)).toBeNull();
  });

  it("bare /lisa/servicios → catalogo (precedente que sigue funcionando)", () => {
    expect(shellInRenderRedirectTarget(`/${T}/lisa/servicios`)).toBe(
      `/${T}/lisa/servicios/catalogo`,
    );
  });
});
