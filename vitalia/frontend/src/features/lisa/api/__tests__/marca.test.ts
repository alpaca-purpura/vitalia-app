/**
 * marca.test.ts — Vitest unit tests para la fábrica de keys React Query.
 *
 * T-9 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-9 deliverables + 03-arch.md § React Query key factory
 *
 * Tests cubiertos:
 *   - marcaKeys.all: array raíz ["lisa", "marca"]
 *   - marcaKeys.identity(tenantId): array con tenantId al final
 *   - marcaKeys.visuals(tenantId): array con tenantId al final
 *   - marcaKeys.logo(tenantId): array con tenantId al final
 *   - marcaKeys.personality(tenantId): array con tenantId al final
 *   - marcaKeys.voicePreview(tenantId, blocksHash): incluye tenantId + blocksHash
 *   - marcaKeys.prohibitedPhrases(tenantId): array con tenantId al final
 *   - marcaKeys.contact(tenantId): array con tenantId al final
 *   - marcaKeys.trustSignals(tenantId): array con tenantId al final
 *   - marcaKeys.trustCatalog(tenantId, countryCode): incluye tenantId + countryCode
 *   - marcaKeys.locations(tenantId): array con tenantId al final
 *   - Tenant isolation: tenantId diferente produce keys diferentes
 *   - Keys distintas no comparten prefijo completo (no colisión entre sub-recursos)
 *
 * downstream-regression-na: brand-local vitalia FE API key factory tests; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { marcaKeys } from "../marca";

// ── marcaKeys.all ──────────────────────────────────────────────────────────────

describe("marcaKeys.all — raíz del namespace", () => {
  it("es el array ['lisa', 'marca']", () => {
    expect(marcaKeys.all).toEqual(["lisa", "marca"]);
  });

  it("es readonly (as const — no mutable)", () => {
    // TypeScript garantiza readonly en compilación; en runtime verificamos que es un array
    expect(Array.isArray(marcaKeys.all)).toBe(true);
  });
});

// ── marcaKeys individuales ─────────────────────────────────────────────────────

describe("marcaKeys.identity — clave por tenantId", () => {
  it("contiene el prefijo all + 'identity' + tenantId", () => {
    const key = marcaKeys.identity("tenant-abc");
    expect(key).toEqual(["lisa", "marca", "identity", "tenant-abc"]);
  });

  it("tenantId diferente produce key diferente", () => {
    const keyA = marcaKeys.identity("tenant-A");
    const keyB = marcaKeys.identity("tenant-B");
    expect(keyA).not.toEqual(keyB);
  });
});

describe("marcaKeys.visuals — clave por tenantId", () => {
  it("contiene el prefijo all + 'visuals' + tenantId", () => {
    const key = marcaKeys.visuals("tenant-xyz");
    expect(key).toEqual(["lisa", "marca", "visuals", "tenant-xyz"]);
  });

  it("no colisiona con identity para el mismo tenantId", () => {
    const tenant = "same-tenant";
    expect(marcaKeys.identity(tenant)).not.toEqual(marcaKeys.visuals(tenant));
  });
});

describe("marcaKeys.logo — clave por tenantId", () => {
  it("contiene el prefijo all + 'logo' + tenantId", () => {
    const key = marcaKeys.logo("tenant-abc");
    expect(key).toEqual(["lisa", "marca", "logo", "tenant-abc"]);
  });
});

describe("marcaKeys.personality — clave por tenantId", () => {
  it("contiene el prefijo all + 'personality' + tenantId", () => {
    const key = marcaKeys.personality("tenant-salud");
    expect(key).toEqual(["lisa", "marca", "personality", "tenant-salud"]);
  });
});

describe("marcaKeys.voicePreview — clave por tenantId + blocksHash", () => {
  it("contiene el prefijo all + 'voicePreview' + tenantId + blocksHash", () => {
    const key = marcaKeys.voicePreview("tenant-abc", "hash-abc123");
    expect(key).toEqual(["lisa", "marca", "voicePreview", "tenant-abc", "hash-abc123"]);
  });

  it("mismo tenantId + diferente blocksHash produce keys diferentes", () => {
    const keyA = marcaKeys.voicePreview("t1", "hash-v1");
    const keyB = marcaKeys.voicePreview("t1", "hash-v2");
    expect(keyA).not.toEqual(keyB);
  });

  it("diferente tenantId + mismo blocksHash produce keys diferentes", () => {
    const keyA = marcaKeys.voicePreview("tenant-A", "same-hash");
    const keyB = marcaKeys.voicePreview("tenant-B", "same-hash");
    expect(keyA).not.toEqual(keyB);
  });
});

describe("marcaKeys.prohibitedPhrases — clave por tenantId", () => {
  it("contiene el prefijo all + 'prohibitedPhrases' + tenantId", () => {
    const key = marcaKeys.prohibitedPhrases("tenant-clinic");
    expect(key).toEqual(["lisa", "marca", "prohibitedPhrases", "tenant-clinic"]);
  });
});

describe("marcaKeys.contact — clave por tenantId", () => {
  it("contiene el prefijo all + 'contact' + tenantId", () => {
    const key = marcaKeys.contact("tenant-xyz");
    expect(key).toEqual(["lisa", "marca", "contact", "tenant-xyz"]);
  });
});

describe("marcaKeys.trustSignals — clave por tenantId", () => {
  it("contiene el prefijo all + 'trustSignals' + tenantId", () => {
    const key = marcaKeys.trustSignals("tenant-clinic");
    expect(key).toEqual(["lisa", "marca", "trustSignals", "tenant-clinic"]);
  });
});

describe("marcaKeys.trustCatalog — clave por tenantId + countryCode", () => {
  it("contiene el prefijo all + 'trustCatalog' + tenantId + countryCode", () => {
    const key = marcaKeys.trustCatalog("tenant-pe", "PE");
    expect(key).toEqual(["lisa", "marca", "trustCatalog", "tenant-pe", "PE"]);
  });

  it("diferente countryCode produce keys diferentes para el mismo tenant", () => {
    const keyPE = marcaKeys.trustCatalog("t1", "PE");
    const keyCO = marcaKeys.trustCatalog("t1", "CO");
    expect(keyPE).not.toEqual(keyCO);
  });
});

describe("marcaKeys.locations — clave por tenantId", () => {
  it("contiene el prefijo all + 'locations' + tenantId", () => {
    const key = marcaKeys.locations("tenant-lima");
    expect(key).toEqual(["lisa", "marca", "locations", "tenant-lima"]);
  });
});

// ── Tenant isolation global ────────────────────────────────────────────────────

describe("marcaKeys — tenant isolation (todas las keys)", () => {
  const TENANT_A = "clinica-san-pedro";
  const TENANT_B = "clinica-los-andes";

  it("identity: tenantId diferente produce key diferente", () => {
    expect(marcaKeys.identity(TENANT_A)).not.toEqual(marcaKeys.identity(TENANT_B));
  });

  it("visuals: tenantId diferente produce key diferente", () => {
    expect(marcaKeys.visuals(TENANT_A)).not.toEqual(marcaKeys.visuals(TENANT_B));
  });

  it("personality: tenantId diferente produce key diferente", () => {
    expect(marcaKeys.personality(TENANT_A)).not.toEqual(marcaKeys.personality(TENANT_B));
  });

  it("prohibitedPhrases: tenantId diferente produce key diferente", () => {
    expect(marcaKeys.prohibitedPhrases(TENANT_A)).not.toEqual(
      marcaKeys.prohibitedPhrases(TENANT_B),
    );
  });
});

// ── Sin colisiones entre sub-recursos ────────────────────────────────────────

describe("marcaKeys — sin colisiones entre sub-recursos", () => {
  const TENANT = "tenant-test";

  it("identity y visuals no colisionan", () => {
    expect(marcaKeys.identity(TENANT)).not.toEqual(marcaKeys.visuals(TENANT));
  });

  it("personality y prohibitedPhrases no colisionan", () => {
    expect(marcaKeys.personality(TENANT)).not.toEqual(marcaKeys.prohibitedPhrases(TENANT));
  });

  it("contact y trustSignals no colisionan", () => {
    expect(marcaKeys.contact(TENANT)).not.toEqual(marcaKeys.trustSignals(TENANT));
  });

  it("trustSignals y locations no colisionan", () => {
    expect(marcaKeys.trustSignals(TENANT)).not.toEqual(marcaKeys.locations(TENANT));
  });
});
