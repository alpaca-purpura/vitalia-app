/**
 * Agent catalog unit tests — T-1 (TDD mandatory per tdd-mandatory.md)
 *
 * SC-1 gherkin coverage: AGENT_CATALOG 6 agentes + DEFAULT_CHAT_AGENT + shape invariants + AGENT_SLUGS
 * SC-2 gherkin coverage: AGENT_RIBBON_ORDER constant + extractAgentFromPath helper valid slugs
 * SC-3 gherkin coverage: extractAgentFromPath 'config' special slug
 * SC-4 gherkin coverage: extractAgentFromPath invalid input → null
 * SC-6 gherkin coverage: extractAgentFromPath XSS payload sanitization implícita
 * SC-8 gherkin coverage: tabLabel strings Spanish neutro verbatim
 *
 * spec_anchor: 01-spec.md § 5.1 + § Catalog SSoT + § Microcopy + § Gherkin SC-1..SC-4/SC-6/SC-8
 *              03-arch.md § 2.1
 *
 * LIFT CANDIDATE: shell-chat agent catalog cross-brand cuando ≥2 brands lo necesiten.
 * Hoy brand-local Vitalia per anti-duplication.md.
 */

import { describe, it, expect } from "vitest";
import type { AgentSlug, AgentDescriptor } from "../agent-catalog";
import {
  AGENT_CATALOG,
  DEFAULT_CHAT_AGENT,
  AGENT_SLUGS,
  AGENT_RIBBON_ORDER,
  extractAgentFromPath,
  RIBBON_SUBTABS,
  extractSubtabFromPath,
} from "../agent-catalog";

const EXPECTED_SLUGS: AgentSlug[] = [
  "lisa",
  "valeria",
  "adrian",
  "lucas",
  "camila",
  "mateo",
];

const AGENT_DESCRIPTOR_KEYS: (keyof AgentDescriptor)[] = [
  "slug",
  "name",
  "role",
  "colorToken",
  "colorSoftToken",
  "hex",
  "thumbnail",
  "transparent",
  "initial",
  "tabLabel",
  "defaultSubtab",
];

// ──────────────────────────────────────────────────────────────────────────────
// SC-1 — AGENT_CATALOG shape + F1-S6 regression guard
// ──────────────────────────────────────────────────────────────────────────────

describe("AGENT_CATALOG — 6 agentes canónicos Vitalia", () => {
  it("AGENT_CATALOG contains 6 agentes (lisa, valeria, adrian, lucas, camila, mateo)", () => {
    expect(Object.keys(AGENT_CATALOG)).toHaveLength(6);
    for (const slug of EXPECTED_SLUGS) {
      expect(Object.keys(AGENT_CATALOG)).toContain(slug);
    }
  });

  it("DEFAULT_CHAT_AGENT equals 'valeria'", () => {
    expect(DEFAULT_CHAT_AGENT).toBe("valeria");
  });

  it("each agent shape complete — all 11 keys present on AgentDescriptor (F1-S7 adds tabLabel + defaultSubtab)", () => {
    for (const slug of EXPECTED_SLUGS) {
      const descriptor = AGENT_CATALOG[slug];
      for (const key of AGENT_DESCRIPTOR_KEYS) {
        expect(descriptor, `${slug} missing key ${key}`).toHaveProperty(key);
        expect(
          descriptor[key],
          `${slug}.${key} should not be empty`,
        ).toBeTruthy();
      }
    }
  });

  it("AGENT_SLUGS array has 6 entries matching catalog keys", () => {
    expect(AGENT_SLUGS).toHaveLength(6);
    for (const slug of EXPECTED_SLUGS) {
      expect(AGENT_SLUGS).toContain(slug);
    }
    // Verify AGENT_SLUGS is derived from catalog keys
    expect([...AGENT_SLUGS].sort()).toEqual([...EXPECTED_SLUGS].sort());
  });

  it("valeria.hex equals '#7b2d91' (metadata only — not consumed by Tailwind)", () => {
    expect(AGENT_CATALOG.valeria.hex).toBe("#7b2d91");
  });

  it("thumbnail paths match /agents/{slug}/thumbnail.png pattern", () => {
    for (const slug of EXPECTED_SLUGS) {
      const { thumbnail } = AGENT_CATALOG[slug];
      expect(thumbnail).toMatch(/^\/agents\/[a-z]+\/thumbnail\.png$/);
      expect(thumbnail).toBe(`/agents/${slug}/thumbnail.png`);
    }
  });

  it("adrian.transparent ends with .jpeg (source originals — verbatim spec § 5.2)", () => {
    expect(AGENT_CATALOG.adrian.transparent).toMatch(/\.jpeg$/);
  });

  it("all other agents transparent ends with .png", () => {
    for (const slug of EXPECTED_SLUGS) {
      if (slug === "adrian") continue;
      expect(AGENT_CATALOG[slug].transparent).toMatch(/\.png$/);
    }
  });

  it("each agent slug field matches the catalog key", () => {
    for (const slug of EXPECTED_SLUGS) {
      expect(AGENT_CATALOG[slug].slug).toBe(slug);
    }
  });

  it("colorToken format is 'agent-{slug}' (no -- prefix, no hsl())", () => {
    for (const slug of EXPECTED_SLUGS) {
      const { colorToken } = AGENT_CATALOG[slug];
      expect(colorToken).toMatch(/^agent-[a-z]+$/);
      expect(colorToken).toBe(`agent-${slug}`);
    }
  });

  it("colorSoftToken format is 'agent-{slug}-soft'", () => {
    for (const slug of EXPECTED_SLUGS) {
      const { colorSoftToken } = AGENT_CATALOG[slug];
      expect(colorSoftToken).toBe(`agent-${slug}-soft`);
    }
  });

  it("initial is a single uppercase letter", () => {
    for (const slug of EXPECTED_SLUGS) {
      const { initial } = AGENT_CATALOG[slug];
      expect(initial).toHaveLength(1);
      expect(initial).toMatch(/^[A-Z]$/);
    }
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// SC-1 + SC-8 — tabLabel + defaultSubtab per agente (F1-S7 new fields)
// ──────────────────────────────────────────────────────────────────────────────

describe("AGENT_CATALOG — tabLabel + defaultSubtab (F1-S7 new fields)", () => {
  it("AGENT_CATALOG.lisa.tabLabel === 'Mi Clínica' + defaultSubtab === 'marca'", () => {
    expect(AGENT_CATALOG.lisa.tabLabel).toBe("Mi Clínica");
    expect(AGENT_CATALOG.lisa.defaultSubtab).toBe("marca");
  });

  it("AGENT_CATALOG.lucas.tabLabel === 'Atraer' + defaultSubtab === 'lanzar'", () => {
    expect(AGENT_CATALOG.lucas.tabLabel).toBe("Atraer");
    expect(AGENT_CATALOG.lucas.defaultSubtab).toBe("lanzar");
  });

  it("AGENT_CATALOG.adrian.tabLabel === 'Vender' + defaultSubtab === 'inbox'", () => {
    expect(AGENT_CATALOG.adrian.tabLabel).toBe("Vender");
    expect(AGENT_CATALOG.adrian.defaultSubtab).toBe("inbox");
  });

  it("AGENT_CATALOG.valeria.tabLabel + defaultSubtab present (shape-complete though valeria is sidebar-only v1.2)", () => {
    // v1.2: valeria is sidebar supervisor, not in ribbon — tabLabel/defaultSubtab kept for completeness
    expect(AGENT_CATALOG.valeria.tabLabel).toBeTruthy();
    expect(AGENT_CATALOG.valeria.defaultSubtab).toBeTruthy();
  });

  it("AGENT_CATALOG.camila.tabLabel === 'Mantener' + defaultSubtab === 'voz'", () => {
    expect(AGENT_CATALOG.camila.tabLabel).toBe("Mantener");
    expect(AGENT_CATALOG.camila.defaultSubtab).toBe("voz");
  });

  it("AGENT_CATALOG.mateo.tabLabel === 'Atender' + defaultSubtab === 'agenda' (v1.3 — 'Operar' renamed)", () => {
    // v1.3 (2026-06-22): "Operar" → "Atender" (clinical-warm, no surgical connotation). Slug unchanged.
    expect(AGENT_CATALOG.mateo.tabLabel).toBe("Atender");
    expect(AGENT_CATALOG.mateo.defaultSubtab).toBe("agenda");
  });

  it("existing F1-S6 fields (name, role, colorToken, hex, thumbnail, transparent, initial) preserved verbatim (no regression)", () => {
    // Spot-check verbatim values from F1-S6
    expect(AGENT_CATALOG.lisa.name).toBe("Lisa");
    expect(AGENT_CATALOG.lisa.role).toBe("Estratega de marca y oferta");
    expect(AGENT_CATALOG.lisa.hex).toBe("#00D084");
    expect(AGENT_CATALOG.lisa.thumbnail).toBe("/agents/lisa/thumbnail.png");
    expect(AGENT_CATALOG.lisa.initial).toBe("L");

    expect(AGENT_CATALOG.valeria.name).toBe("Valeria");
    expect(AGENT_CATALOG.valeria.role).toBe(
      "Tu secretaria virtual · coordinadora general",
    );
    expect(AGENT_CATALOG.valeria.hex).toBe("#7b2d91");

    expect(AGENT_CATALOG.adrian.name).toBe("Adrián");
    expect(AGENT_CATALOG.adrian.role).toBe(
      "Closer · califica leads y reactiva oportunidades",
    );
    expect(AGENT_CATALOG.adrian.transparent).toBe(
      "/agents/adrian/transparent.jpeg",
    );

    expect(AGENT_CATALOG.lucas.name).toBe("Lucas");
    expect(AGENT_CATALOG.camila.name).toBe("Camila");
    expect(AGENT_CATALOG.mateo.name).toBe("Mateo");
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// SC-2 — AGENT_RIBBON_ORDER constant
// ──────────────────────────────────────────────────────────────────────────────

describe("AGENT_RIBBON_ORDER — canonical ribbon tab order (v1.2 paradigm-map-zones T-5)", () => {
  it("AGENT_RIBBON_ORDER deep-equals ['lisa', 'lucas', 'adrian', 'mateo', 'camila'] in canonical value-chain order (v1.3)", () => {
    // v1.3 (2026-06-22): reordered to value-chain — Mi Clínica · Atraer · Vender · Atender · Mantener
    expect(AGENT_RIBBON_ORDER).toEqual([
      "lisa",
      "lucas",
      "adrian",
      "mateo",
      "camila",
    ]);
  });

  it("AGENT_RIBBON_ORDER.length === 5 (5 specialist ribbon tabs)", () => {
    expect(AGENT_RIBBON_ORDER).toHaveLength(5);
  });

  it("AGENT_RIBBON_ORDER contains 'mateo' (Operar — v1.2)", () => {
    expect(AGENT_RIBBON_ORDER).toContain("mateo");
  });

  it("AGENT_RIBBON_ORDER does not contain 'valeria' (supervisor sidebar — v1.2)", () => {
    expect(AGENT_RIBBON_ORDER).not.toContain("valeria");
  });

  it("AGENT_RIBBON_ORDER is readonly tuple (TypeScript const assertion — runtime shape check)", () => {
    // Runtime check: verify it's array-like and not mutable via normal API
    // (TypeScript const assertion enforces readonly at compile time; here we verify shape at runtime)
    expect(Array.isArray(AGENT_RIBBON_ORDER)).toBe(true);
    // Verify the canonical 5 v1.3 values (value-chain order)
    expect(AGENT_RIBBON_ORDER[0]).toBe("lisa");
    expect(AGENT_RIBBON_ORDER[4]).toBe("camila");
    expect(AGENT_RIBBON_ORDER[1]).toBe("lucas");
    expect(AGENT_RIBBON_ORDER[3]).toBe("mateo");
  });

  it("all entries in AGENT_RIBBON_ORDER exist in AGENT_CATALOG", () => {
    for (const slug of AGENT_RIBBON_ORDER) {
      expect(AGENT_CATALOG).toHaveProperty(slug);
    }
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// SC-2 — extractAgentFromPath · valid agent slugs
// ──────────────────────────────────────────────────────────────────────────────

describe("extractAgentFromPath — valid agent slugs (SC-2)", () => {
  it("extractAgentFromPath('/tenant-x/lisa/marca') returns 'lisa'", () => {
    expect(extractAgentFromPath("/tenant-x/lisa/marca")).toBe("lisa");
  });

  it("extractAgentFromPath('/tenant-x/camila/voz') returns 'camila'", () => {
    expect(extractAgentFromPath("/tenant-x/camila/voz")).toBe("camila");
  });

  it("extractAgentFromPath('/tenant-x/mateo/whatever') returns 'mateo' (catalog includes mateo even though not in ribbon order)", () => {
    expect(extractAgentFromPath("/tenant-x/mateo/whatever")).toBe("mateo");
  });

  it("extracts 'valeria' from path with tenantId prefix", () => {
    expect(extractAgentFromPath("/my-clinic-123/valeria/agenda")).toBe(
      "valeria",
    );
  });

  it("extracts 'lucas' from path", () => {
    expect(extractAgentFromPath("/tenant-x/lucas/lanzar")).toBe("lucas");
  });

  it("extracts 'adrian' from path", () => {
    expect(extractAgentFromPath("/tenant-x/adrian/inbox")).toBe("adrian");
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// SC-3 — extractAgentFromPath · 'config' special slug
// ──────────────────────────────────────────────────────────────────────────────

describe("extractAgentFromPath — 'config' special slug (SC-3)", () => {
  it("extractAgentFromPath('/tenant-x/config/cuenta') returns 'config' (RibbonTabSlug union)", () => {
    expect(extractAgentFromPath("/tenant-x/config/cuenta")).toBe("config");
  });

  it("extractAgentFromPath('/tenant-x/config') returns 'config' (minimal config path)", () => {
    // segments[1] = 'config', segments.length >= 2 (tenant + config)
    expect(extractAgentFromPath("/tenant-x/config")).toBe("config");
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// SC-4 — extractAgentFromPath · invalid input returns null
// ──────────────────────────────────────────────────────────────────────────────

describe("extractAgentFromPath — invalid input → null (SC-4)", () => {
  it("extractAgentFromPath('/tenant-x/foobar/baz') returns null", () => {
    expect(extractAgentFromPath("/tenant-x/foobar/baz")).toBeNull();
  });

  it("extractAgentFromPath('/tenant-x') returns null (insufficient segments — no [agent] segment)", () => {
    expect(extractAgentFromPath("/tenant-x")).toBeNull();
  });

  it("extractAgentFromPath('/') returns null (empty/root)", () => {
    expect(extractAgentFromPath("/")).toBeNull();
  });

  it("extractAgentFromPath(null) returns null (defensive nullable)", () => {
    expect(extractAgentFromPath(null)).toBeNull();
  });

  it("extractAgentFromPath(undefined) returns null", () => {
    expect(extractAgentFromPath(undefined)).toBeNull();
  });

  it("extractAgentFromPath('') returns null", () => {
    expect(extractAgentFromPath("")).toBeNull();
  });

  it("extractAgentFromPath('/only-one-segment') returns null (< 2 non-empty segments)", () => {
    // After split+filter: ['only-one-segment'] → length 1 < 2 → null
    expect(extractAgentFromPath("/only-one-segment")).toBeNull();
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// SC-6 — extractAgentFromPath · XSS payload sanitization implícita
// ──────────────────────────────────────────────────────────────────────────────

describe("extractAgentFromPath — XSS payload sanitization (SC-6)", () => {
  it("extractAgentFromPath('/tenant-x/<script>alert(1)</script>/foo') returns null (slug enum mismatch sanitizes)", () => {
    expect(
      extractAgentFromPath("/tenant-x/<script>alert(1)</script>/foo"),
    ).toBeNull();
  });

  it("extractAgentFromPath('/tenant-x/javascript:alert(1)/foo') returns null", () => {
    expect(
      extractAgentFromPath("/tenant-x/javascript:alert(1)/foo"),
    ).toBeNull();
  });

  it("extractAgentFromPath('/tenant-x/data:text/html,<h1>/foo') returns null", () => {
    expect(
      extractAgentFromPath("/tenant-x/data:text/html,<h1>/foo"),
    ).toBeNull();
  });

  it("extractAgentFromPath('/tenant-x/../etc/passwd') does not return a valid slug", () => {
    // Traversal attempt: segments after filter would be ['tenant-x', '..', 'etc', 'passwd']
    // segments[1] = '..' → does not match any AgentSlug or 'config' → null
    expect(extractAgentFromPath("/tenant-x/../etc/passwd")).toBeNull();
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// SC-8 — tabLabel strings Spanish neutro verbatim
// ──────────────────────────────────────────────────────────────────────────────

describe("tabLabel — Spanish neutro LatAm verbatim (SC-8)", () => {
  it("all 5 ribbon tabLabels are short Spanish neutro strings (1-3 words, no accented imperatives) — v1.3 value-chain order", () => {
    // v1.3 (2026-06-22): AGENT_RIBBON_ORDER = [lisa, lucas, adrian, mateo, camila]
    // Verify tabLabels are the expected exact strings (Spanish neutro LatAm per spec § Microcopy)
    // Each is a noun/infinitive verb — no imperative voseo forms
    const expectedLabels: string[] = [
      "Mi Clínica",  // lisa
      "Atraer",      // lucas
      "Vender",      // adrian
      "Atender",     // mateo (v1.3 — was "Operar")
      "Mantener",    // camila
    ];
    const ribbonLabels = AGENT_RIBBON_ORDER.map(
      (slug) => AGENT_CATALOG[slug].tabLabel,
    );
    expect(ribbonLabels).toEqual(expectedLabels);
  });

  it("Adrián role label has tilde (Adrián not 'Adrian')", () => {
    expect(AGENT_CATALOG.adrian.name).toBe("Adrián");
    // The name with tilde is the correct Spanish neutro form
    expect(AGENT_CATALOG.adrian.name).toContain("á");
  });

  it("Mi Clínica tabLabel has tilde (Clínica not 'Clinica')", () => {
    expect(AGENT_CATALOG.lisa.tabLabel).toBe("Mi Clínica");
    expect(AGENT_CATALOG.lisa.tabLabel).toContain("í");
  });

  it("lisa tabLabel is exactly 'Mi Clínica' (verbatim per spec § Microcopy SC-1)", () => {
    expect(AGENT_CATALOG.lisa.tabLabel).toBe("Mi Clínica");
  });

  it("lucas tabLabel is exactly 'Atraer'", () => {
    expect(AGENT_CATALOG.lucas.tabLabel).toBe("Atraer");
  });

  it("adrian tabLabel is exactly 'Vender'", () => {
    expect(AGENT_CATALOG.adrian.tabLabel).toBe("Vender");
  });

  it("mateo tabLabel is exactly 'Atender' (v1.3 — 'Operar' renamed, no surgical connotation)", () => {
    // v1.3 (2026-06-22): "Operar" → "Atender". Slug unchanged (mateo).
    expect(AGENT_CATALOG.mateo.tabLabel).toBe("Atender");
  });

  it("camila tabLabel is exactly 'Mantener'", () => {
    expect(AGENT_CATALOG.camila.tabLabel).toBe("Mantener");
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// F1-S8 — SubTabMeta interface + RIBBON_SUBTABS + extractSubtabFromPath
// spec_anchor: 01-spec.md § Catalog SSoT § 1 + 03-arch.md § 2.1
// ──────────────────────────────────────────────────────────────────────────────

describe("SubTabMeta interface — required fields (F1-S8)", () => {
  it("SubTabMeta shape: each entry has id (string), label (string), icon (string)", () => {
    // Use RIBBON_SUBTABS.lisa as representative sample
    const sample = RIBBON_SUBTABS.lisa[0];
    // TypeScript enforces shape at compile time; here we verify runtime presence
    expect(typeof sample.id).toBe("string");
    expect(typeof sample.label).toBe("string");
    expect(typeof sample.icon).toBe("string");
    expect(sample.id.length).toBeGreaterThan(0);
    expect(sample.label.length).toBeGreaterThan(0);
    expect(sample.icon.length).toBeGreaterThan(0);
  });

  it("SubTabMeta id uses kebab-case URL segment pattern", () => {
    // Verify all ids across all agents are valid URL segments (no spaces, lowercase)
    const allEntries = Object.values(RIBBON_SUBTABS).flatMap((tabs) => [
      ...tabs,
    ]);
    for (const entry of allEntries) {
      expect(entry.id).toMatch(/^[a-z][a-z0-9-]*$/);
    }
  });
});

describe("RIBBON_SUBTABS — total count and distribution (F1-S8)", () => {
  it("RIBBON_SUBTABS satisfies Record<RibbonTabSlug, readonly SubTabMeta[]> — all 7 keys present (lisa/lucas/adrian/valeria/camila/mateo/config)", () => {
    const expectedKeys = [
      "lisa",
      "lucas",
      "adrian",
      "valeria",
      "camila",
      "mateo",
      "config",
    ] as const;
    for (const key of expectedKeys) {
      expect(RIBBON_SUBTABS).toHaveProperty(key);
      expect(Array.isArray(RIBBON_SUBTABS[key])).toBe(true);
    }
  });

  it("mateo subtabs has 2 entries: agenda + pacientes (v1.2 — migrated from valeria)", () => {
    // v1.2 (2026-05-30): Mateo is Operar specialist with agenda + pacientes
    expect(RIBBON_SUBTABS.mateo).toHaveLength(2);
    expect(RIBBON_SUBTABS.mateo.map((t) => t.id)).toEqual(["agenda", "pacientes"]);
  });

  it("valeria subtabs is empty array (v1.2 — valeria is sidebar supervisor, not ribbon tab)", () => {
    // v1.2 (2026-05-30): Valeria is supervisor sidebar only, 0 ribbon subtabs
    expect(RIBBON_SUBTABS.valeria).toHaveLength(0);
  });

  it("total sub-tabs across 5 ribbon agents + config equals 23 (4+2+5+5+4+3)", () => {
    // v1.2: lisa(4) + mateo(2) + lucas(5) + adrian(5) + camila(4) + config(3) = 23
    // Valeria=0 (sidebar-only)
    // ★ 2026-06-11 (auditor shell-core-hardening): adrian ganó la sub-tab `recuperar`
    // en la story adrian-embudo (chip frozen → /adrian/recuperar); este test quedó stale.
    const ribbonAndConfig = (
      ["lisa", "mateo", "lucas", "adrian", "camila", "config"] as const
    ).reduce((acc, key) => acc + RIBBON_SUBTABS[key].length, 0);
    expect(ribbonAndConfig).toBe(23);
  });

  it("lisa has 4 sub-tabs in order: marca, staff, servicios, compliance", () => {
    // F2-S8 T-FE-1 (2026-05-31): sub-tab renamed 'doctores' → 'staff' per 01-spec.md v2
    const lisa = RIBBON_SUBTABS.lisa;
    expect(lisa).toHaveLength(4);
    expect(lisa.map((t) => t.id)).toEqual([
      "marca",
      "staff",
      "servicios",
      "compliance",
    ]);
  });

  it("lucas has 5 sub-tabs in order: lanzar, envuelo, recursos, resultados, mercado", () => {
    const lucas = RIBBON_SUBTABS.lucas;
    expect(lucas).toHaveLength(5);
    expect(lucas.map((t) => t.id)).toEqual([
      "lanzar",
      "envuelo",
      "recursos",
      "resultados",
      "mercado",
    ]);
  });

  it("adrian has 5 sub-tabs in order: inbox, embudo, recuperar, outbound, propuestas", () => {
    // ★ 2026-06-11: `recuperar` agregada por la story adrian-embudo (catálogo real SSoT).
    const adrian = RIBBON_SUBTABS.adrian;
    expect(adrian).toHaveLength(5);
    expect(adrian.map((t) => t.id)).toEqual([
      "inbox",
      "embudo",
      "recuperar",
      "outbound",
      "propuestas",
    ]);
  });

  it("valeria has 0 sub-tabs (v1.2 — sidebar supervisor only, not ribbon tab)", () => {
    // v1.2 (2026-05-30): valeria is supervisor sidebar, agenda/pacientes moved to mateo
    const valeria = RIBBON_SUBTABS.valeria;
    expect(valeria).toHaveLength(0);
    expect(valeria.map((t) => t.id)).toEqual([]);
  });

  it("camila has 4 sub-tabs in order: voz, reactivar, multiplicar, reputacion", () => {
    const camila = RIBBON_SUBTABS.camila;
    expect(camila).toHaveLength(4);
    expect(camila.map((t) => t.id)).toEqual([
      "voz",
      "reactivar",
      "multiplicar",
      "reputacion",
    ]);
  });

  it("config has 3 sub-tabs in order: cuenta, conexiones, avanzado", () => {
    const config = RIBBON_SUBTABS.config;
    expect(config).toHaveLength(3);
    expect(config.map((t) => t.id)).toEqual([
      "cuenta",
      "conexiones",
      "avanzado",
    ]);
  });
});

describe("RIBBON_SUBTABS — label strings Spanish neutro (F1-S8)", () => {
  it("lisa labels are 'Marca', 'Staff', 'Servicios', 'Compliance' verbatim", () => {
    // F2-S8 T-FE-1 (2026-05-31): sub-tab renamed 'Doctores' → 'Staff' per 01-spec.md v2
    expect(RIBBON_SUBTABS.lisa.map((t) => t.label)).toEqual([
      "Marca",
      "Staff",
      "Servicios",
      "Compliance",
    ]);
  });

  it("lucas labels: 'Lanzar', 'En vuelo', 'Recursos', 'Resultados', 'Mercado' verbatim", () => {
    expect(RIBBON_SUBTABS.lucas.map((t) => t.label)).toEqual([
      "Lanzar",
      "En vuelo",
      "Recursos",
      "Resultados",
      "Mercado",
    ]);
  });

  it("camila.voz label is 'Voz del paciente' (multi-word, no abbreviation)", () => {
    const voz = RIBBON_SUBTABS.camila.find((t) => t.id === "voz");
    expect(voz).toBeDefined();
    expect(voz!.label).toBe("Voz del paciente");
  });

  it("camila.reputacion label is 'Reputación' (with tilde — Spanish neutro LatAm)", () => {
    const rep = RIBBON_SUBTABS.camila.find((t) => t.id === "reputacion");
    expect(rep).toBeDefined();
    expect(rep!.label).toBe("Reputación");
    expect(rep!.label).toContain("ó"); // tilde present
  });

  it("config.cuenta label is 'Mi cuenta' (lowercase 'cuenta')", () => {
    const cuenta = RIBBON_SUBTABS.config.find((t) => t.id === "cuenta");
    expect(cuenta).toBeDefined();
    expect(cuenta!.label).toBe("Mi cuenta");
  });

  it("each label is a non-empty string with no leading/trailing whitespace", () => {
    const allEntries = Object.values(RIBBON_SUBTABS).flatMap((tabs) => [
      ...tabs,
    ]);
    for (const entry of allEntries) {
      expect(entry.label.trim()).toBe(entry.label);
      expect(entry.label.length).toBeGreaterThan(0);
    }
  });
});

describe("RIBBON_SUBTABS — icon field (emojis, F1-S8)", () => {
  it("each sub-tab has a non-empty icon string (emoji)", () => {
    const allEntries = Object.values(RIBBON_SUBTABS).flatMap((tabs) => [
      ...tabs,
    ]);
    for (const entry of allEntries) {
      expect(entry.icon.length).toBeGreaterThan(0);
    }
  });

  it("lisa.staff icon is '👨‍⚕️' (doctor emoji)", () => {
    // F2-S8 T-FE-1 (2026-05-31): renamed from 'lisa.doctores' → 'lisa.staff' per 01-spec.md v2
    const staff = RIBBON_SUBTABS.lisa.find((t) => t.id === "staff");
    expect(staff!.icon).toBe("👨‍⚕️");
  });

  it("config.conexiones icon is '🔌' (plug emoji — conexiones)", () => {
    const con = RIBBON_SUBTABS.config.find((t) => t.id === "conexiones");
    expect(con!.icon).toBe("🔌");
  });
});

describe("extractSubtabFromPath — valid paths (F1-S8)", () => {
  it("extractSubtabFromPath('/tenant-x/lisa/marca') returns 'marca'", () => {
    expect(extractSubtabFromPath("/tenant-x/lisa/marca")).toBe("marca");
  });

  it("extractSubtabFromPath('/tenant-x/camila/reactivar') returns 'reactivar'", () => {
    expect(extractSubtabFromPath("/tenant-x/camila/reactivar")).toBe(
      "reactivar",
    );
  });

  it("extractSubtabFromPath('/tenant-x/config/cuenta') returns 'cuenta'", () => {
    expect(extractSubtabFromPath("/tenant-x/config/cuenta")).toBe("cuenta");
  });

  it("extractSubtabFromPath('/tenant-x/lucas/envuelo') returns 'envuelo'", () => {
    expect(extractSubtabFromPath("/tenant-x/lucas/envuelo")).toBe("envuelo");
  });

  it("extractSubtabFromPath('/my-clinic-123/adrian/inbox') returns 'inbox'", () => {
    expect(extractSubtabFromPath("/my-clinic-123/adrian/inbox")).toBe("inbox");
  });

  it("returns raw segment (no validation against RIBBON_SUBTABS — consumer validates)", () => {
    // extractSubtabFromPath does NOT validate subtab membership — just extracts segment[2]
    // Consumer (SubTabsBar) does .find() to match valid subtabs
    expect(extractSubtabFromPath("/tenant-x/lisa/invalid-subtab")).toBe(
      "invalid-subtab",
    );
  });
});

describe("extractSubtabFromPath — invalid / null paths (F1-S8)", () => {
  it("extractSubtabFromPath(null) returns null (defensive nullable input)", () => {
    expect(extractSubtabFromPath(null)).toBeNull();
  });

  it("extractSubtabFromPath(undefined) returns null", () => {
    expect(extractSubtabFromPath(undefined)).toBeNull();
  });

  it("extractSubtabFromPath('') returns null (empty string)", () => {
    expect(extractSubtabFromPath("")).toBeNull();
  });

  it("extractSubtabFromPath('/tenant-x/lisa') returns null (insufficient segments — no subtab)", () => {
    expect(extractSubtabFromPath("/tenant-x/lisa")).toBeNull();
  });

  it("extractSubtabFromPath('/tenant-x') returns null (only 1 non-empty segment)", () => {
    expect(extractSubtabFromPath("/tenant-x")).toBeNull();
  });

  it("extractSubtabFromPath('/') returns null (root path)", () => {
    expect(extractSubtabFromPath("/")).toBeNull();
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// F1-S9 — isValidAgent + isValidSubtab validators (T-2)
// spec_anchor: 06-tickets.yaml T-2 gherkin_coverage
// ──────────────────────────────────────────────────────────────────────────────

import { isValidAgent, isValidSubtab } from "../agent-catalog";

describe("isValidAgent — type guard SC-1 happy path (F1-S9)", () => {
  it("isValidAgent('lisa') returns true", () => {
    expect(isValidAgent("lisa")).toBe(true);
  });

  it("isValidAgent('mateo') returns true (v1.2 — Mateo is now Operar ribbon specialist)", () => {
    // v1.2 (2026-05-30): mateo is now in AGENT_RIBBON_ORDER
    expect(isValidAgent("mateo")).toBe(true);
  });

  it("isValidAgent('adrian') returns true", () => {
    expect(isValidAgent("adrian")).toBe(true);
  });

  it("isValidAgent('lucas') returns true", () => {
    expect(isValidAgent("lucas")).toBe(true);
  });

  it("isValidAgent('camila') returns true", () => {
    expect(isValidAgent("camila")).toBe(true);
  });

  it("isValidAgent('config') returns true (RibbonTabSlug special slug)", () => {
    expect(isValidAgent("config")).toBe(true);
  });
});

describe("isValidAgent — type guard SC-2 negative (F1-S9)", () => {
  it("isValidAgent('valeria') returns false (v1.2 — supervisor sidebar, not ribbon agent)", () => {
    // v1.2 (2026-05-30): valeria is supervisor sidebar only, not in AGENT_RIBBON_ORDER
    expect(isValidAgent("valeria")).toBe(false);
  });

  it("isValidAgent('foo') returns false (unknown slug)", () => {
    expect(isValidAgent("foo")).toBe(false);
  });

  it("isValidAgent('') returns false (empty string)", () => {
    expect(isValidAgent("")).toBe(false);
  });

  it("isValidAgent('<script>') returns false (XSS payload sanitized by enum check)", () => {
    expect(isValidAgent("<script>")).toBe(false);
  });

  it("isValidAgent('LISA') returns false (case-sensitive — must be lowercase)", () => {
    expect(isValidAgent("LISA")).toBe(false);
  });

  it("isValidAgent('lisa ') returns false (trailing whitespace — not a valid slug)", () => {
    expect(isValidAgent("lisa ")).toBe(false);
  });
});

describe("isValidSubtab — type guard SC-3 happy path (F1-S9)", () => {
  it("isValidSubtab('lisa', 'marca') returns true", () => {
    expect(isValidSubtab("lisa", "marca")).toBe(true);
  });

  it("isValidSubtab('mateo', 'agenda') returns true (v1.2 — agenda migrated to mateo)", () => {
    // v1.2 (2026-05-30): agenda is a mateo subtab now
    expect(isValidSubtab("mateo", "agenda")).toBe(true);
  });

  it("isValidSubtab('mateo', 'pacientes') returns true (v1.2 — pacientes migrated to mateo)", () => {
    expect(isValidSubtab("mateo", "pacientes")).toBe(true);
  });

  it("isValidSubtab('camila', 'reputacion') returns true", () => {
    expect(isValidSubtab("camila", "reputacion")).toBe(true);
  });

  it("isValidSubtab('config', 'avanzado') returns true", () => {
    expect(isValidSubtab("config", "avanzado")).toBe(true);
  });

  it("isValidSubtab('lucas', 'envuelo') returns true", () => {
    expect(isValidSubtab("lucas", "envuelo")).toBe(true);
  });

  it("isValidSubtab('adrian', 'inbox') returns true", () => {
    expect(isValidSubtab("adrian", "inbox")).toBe(true);
  });
});

describe("isValidSubtab — type guard SC-3 negative (F1-S9)", () => {
  it("isValidSubtab('camila', 'foo') returns false (invalid subtab for agent)", () => {
    expect(isValidSubtab("camila", "foo")).toBe(false);
  });

  it("isValidSubtab('mateo', 'any') returns false (not a valid mateo subtab — only agenda/pacientes valid)", () => {
    // v1.2: mateo has [agenda, pacientes] — 'any' is not a subtab of mateo
    expect(isValidSubtab("mateo", "any")).toBe(false);
  });

  it("isValidSubtab('lisa', '') returns false (empty subtab string)", () => {
    expect(isValidSubtab("lisa", "")).toBe(false);
  });

  it("isValidSubtab('config', 'marca') returns false (subtab from different agent)", () => {
    expect(isValidSubtab("config", "marca")).toBe(false);
  });

  it("isValidSubtab('valeria', 'lanzar') returns false (lucas subtab not valid for valeria)", () => {
    expect(isValidSubtab("valeria", "lanzar")).toBe(false);
  });
});
