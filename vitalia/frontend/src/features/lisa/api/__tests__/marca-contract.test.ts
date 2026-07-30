/**
 * marca-contract.test.ts — FE↔BE identity contract mapping (RED→GREEN).
 *
 * Origen: estabilizar-harness-e2e-lisa-marca (keystone). El de-mock reveló que
 * el FE consumía una forma FICTICIA (`brand_name`/camelCase, importada de
 * nicolify) mientras el BE vitalia devuelve `BrandIdentityDTO {name, tagline,
 * clinic_vertical}` con `tagline: null` para tenants sin tagline. El cast ciego
 * de `fetchClient` dejaba `brand_name=undefined` + `tagline=null` → el zod
 * `z.string().optional()` rechaza `null` → `isValid=false` perpetuo → el
 * autosave NUNCA dispara el PATCH (badge atascado en `idle`).
 *
 * Estos tests fijan el contrato real: getIdentity mapea BE→form (null-safe) y
 * updateIdentity mapea form→BE (`name`+`tagline`, omitiendo name vacío para no
 * gatillar el 422 de min_length del BE).
 *
 * downstream-regression-na: brand-local vitalia FE API contract tests; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { deleteLogo, getIdentity, updateIdentity, updateVisuals, uploadLogo } from "../marca";
import { fetchClient } from "@/lib/api/fetchClient";

vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn(),
}));

const fetchClientMock = vi.mocked(fetchClient);

const OPTS = {
  token: "tok",
  tenantId: "e69a691d-070e-5caf-a053-6e74642ec100",
  clinicId: "clinic-1",
  userId: "user_2abc",
  userRole: "owner",
};

beforeEach(() => {
  fetchClientMock.mockReset();
});

describe("getIdentity — mapea el contrato real del BE (BrandIdentityDTO)", () => {
  it("mapea name→brand_name y tolera tagline:null (no rompe zod)", async () => {
    // Forma REAL del BE vitalia (tenant sin datos).
    fetchClientMock.mockResolvedValueOnce({
      tenant_id: OPTS.tenantId,
      name: "",
      slug: "",
      tagline: null,
      clinic_vertical: "",
      primary_specialties: [],
      updated_at: null,
    } as never);

    const res = await getIdentity(OPTS);

    // brand_name viene de `name` (no undefined).
    expect(res.brand_name).toBe("");
    // tagline null → "" (nunca null, para no romper z.string().optional()).
    expect(res.tagline).toBe("");
    expect(res.tagline).not.toBeNull();
    // ningún campo del form es null/undefined (todos sanitizados).
    for (const v of Object.values(res)) {
      expect(v).not.toBeNull();
      expect(v).not.toBeUndefined();
    }
  });

  it("mapea name + tagline + clinic_vertical de un tenant con datos", async () => {
    fetchClientMock.mockResolvedValueOnce({
      tenant_id: OPTS.tenantId,
      name: "Salud Vitalia",
      slug: "salud-vitalia",
      tagline: "Tu bienestar, nuestra misión",
      clinic_vertical: "medicina_general",
      primary_specialties: ["medicina_general"],
      updated_at: "2026-06-02T10:00:00Z",
    } as never);

    const res = await getIdentity(OPTS);

    expect(res.brand_name).toBe("Salud Vitalia");
    expect(res.tagline).toBe("Tu bienestar, nuestra misión");
    // clinic_vertical preservado para ClinicVerticalReadOnly (cast en IdentidadView).
    expect((res as unknown as { clinic_vertical?: string }).clinic_vertical).toBe(
      "medicina_general",
    );
  });
});

describe("updateIdentity — mapea form→BE (name + tagline)", () => {
  it("envía `name` (no `brand_name`) cuando brand_name es no-vacío", async () => {
    fetchClientMock.mockResolvedValueOnce({
      tenant_id: OPTS.tenantId,
      name: "Clínica Nueva",
      tagline: null,
      clinic_vertical: "",
      primary_specialties: [],
      updated_at: "2026-06-02T11:00:00Z",
    } as never);

    await updateIdentity(OPTS, {
      brand_name: "Clínica Nueva",
      tagline: "Hola",
      website: "",
      industry: "",
      founding_year: "",
    } as never);

    const [, callOpts] = fetchClientMock.mock.calls[0]!;
    const body = JSON.parse((callOpts as { body: string }).body);
    expect(body.name).toBe("Clínica Nueva");
    expect(body.tagline).toBe("Hola");
    // NO debe filtrar campos que el BE no acepta.
    expect(body).not.toHaveProperty("brand_name");
    expect(body).not.toHaveProperty("website");
    expect(body).not.toHaveProperty("industry");
    expect(body).not.toHaveProperty("founding_year");
    expect((callOpts as { method: string }).method).toBe("PATCH");
  });

  it("OMITE `name` cuando brand_name está vacío (evita el 422 min_length del BE) y manda solo tagline", async () => {
    fetchClientMock.mockResolvedValueOnce({
      tenant_id: OPTS.tenantId,
      name: "",
      tagline: "Solo tagline",
      clinic_vertical: "",
      primary_specialties: [],
      updated_at: null,
    } as never);

    await updateIdentity(OPTS, {
      brand_name: "",
      tagline: "Solo tagline",
    } as never);

    const [, callOpts] = fetchClientMock.mock.calls[0]!;
    const body = JSON.parse((callOpts as { body: string }).body);
    expect(body).not.toHaveProperty("name");
    expect(body.tagline).toBe("Solo tagline");
  });

  it("manda tagline:null cuando el tagline del form es vacío (limpia el campo en BE)", async () => {
    fetchClientMock.mockResolvedValueOnce({
      tenant_id: OPTS.tenantId,
      name: "X",
      tagline: null,
      clinic_vertical: "",
      primary_specialties: [],
      updated_at: null,
    } as never);

    await updateIdentity(OPTS, {
      brand_name: "Clínica X",
      tagline: "",
    } as never);

    const [, callOpts] = fetchClientMock.mock.calls[0]!;
    const body = JSON.parse((callOpts as { body: string }).body);
    expect(body.tagline).toBeNull();
  });
});

describe("updateVisuals — whitelist a los 6 campos del BE (extra=forbid)", () => {
  it("manda SOLO los 6 aceptados; omite extras del merge + vacíos", async () => {
    fetchClientMock.mockResolvedValueOnce({} as never);

    await updateVisuals(OPTS, {
      primary_color: "#01B2F8",
      accent_color: "#7B2D91",
      background_color: "", // vacío → omitir (el BE exige ^#RRGGBB)
      font_heading: "Inter",
      font_body: "", // vacío → omitir
      // extras que el merge `{...visuals, ...partial}` del FE arrastra:
      secondary_color: "#FF0000",
      logo_url: "https://x.com/logo.png",
      design_style: "modern",
    } as never);

    const [, callOpts] = fetchClientMock.mock.calls[0]!;
    const body = JSON.parse((callOpts as { body: string }).body);
    expect(body).toEqual({
      primary_color: "#01B2F8",
      accent_color: "#7B2D91",
      font_heading: "Inter",
    });
    expect(body).not.toHaveProperty("background_color"); // vacío omitido
    expect(body).not.toHaveProperty("secondary_color"); // no aceptado por el BE
    expect(body).not.toHaveProperty("logo_url");
    expect(body).not.toHaveProperty("design_style");
  });
});

describe("uploadLogo — manda actor + rol (BE exige X-User-ID + brand_owner)", () => {
  it("incluye X-User-ID + X-User-Role en los headers", async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ logoUrl: "x", updatedAt: "y" }),
    });
    vi.stubGlobal("fetch", fetchSpy);

    const file = new File(["x"], "logo.png", { type: "image/png" });
    await uploadLogo(OPTS, file);

    const init = fetchSpy.mock.calls[0]![1] as { headers: Record<string, string> };
    expect(init.headers["X-User-ID"]).toBe(OPTS.userId);
    expect(init.headers["X-User-Role"]).toBe("owner");
    vi.unstubAllGlobals();
  });

  it("lanza si falta el userId (no manda un upload sin actor)", async () => {
    const file = new File(["x"], "logo.png", { type: "image/png" });
    await expect(
      uploadLogo({ ...OPTS, userId: null }, file),
    ).rejects.toThrow(/userId/i);
  });
});

describe("deleteLogo — contrato real del BE (DELETE /logos, sin {logo_id})", () => {
  it("pega a /logos (sin logo_id) con method DELETE + actor headers (X-User-ID)", async () => {
    fetchClientMock.mockResolvedValueOnce(undefined as never);

    await deleteLogo(OPTS);

    expect(fetchClientMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchClientMock.mock.calls[0];
    // Ruta sin {logo_id} (una marca = un logo) — el bug era pegarle sin el path correcto.
    expect(url).toBe("/api/v1/lisa/marca/logos");
    expect(init?.method).toBe("DELETE");
    // Headers de actor (el BE exige X-User-ID + rol brand_owner; antes faltaban → 403/422).
    expect(init?.headers).toMatchObject({
      "X-User-ID": OPTS.userId,
      "X-User-Role": OPTS.userRole,
    });
  });

  it("lanza si falta el userId (no manda un delete sin actor)", async () => {
    await expect(deleteLogo({ ...OPTS, userId: null })).rejects.toThrow(/userId/i);
  });
});
