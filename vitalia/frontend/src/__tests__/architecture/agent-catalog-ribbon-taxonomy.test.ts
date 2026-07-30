// cap: shell-organism.shell-vitalia
/**
 * Architecture test — Agent Catalog Ribbon Taxonomy v1.2
 *
 * FE-3 validator for story vitalia-paradigm-map-zones T-5.
 *
 * Invariants verified:
 *   1. AGENT_RIBBON_ORDER contains mateo (specialist "Operar")
 *   2. AGENT_RIBBON_ORDER does NOT contain valeria (supervisor sidebar, not ribbon tab)
 *   3. AGENT_RIBBON_ORDER has exactly 5 entries: [lisa, mateo, adrian, lucas, camila]
 *   4. RIBBON_SUBTABS.mateo has agenda + pacientes (the ex-valeria subtabs)
 *   5. RIBBON_SUBTABS.valeria is empty (valeria is not a ribbon tab)
 *   6. SHIPPED_STATIC_SUBTABS contains 'mateo.agenda' (not 'valeria.agenda')
 *   7. SHIPPED_STATIC_SUBTABS does NOT contain 'valeria.agenda'
 *   8. AGENT_CATALOG.mateo.tabLabel === "Operar"
 *   9. AGENT_CATALOG.mateo.defaultSubtab === "agenda"
 *   10. isValidAgent("mateo") === true (mateo IS valid in ribbon now)
 *   11. isValidAgent("valeria") === false (valeria NOT in ribbon)
 *
 * spec_anchor: 04-validators.yaml FE-3 + 03-arch-fe.md § F6
 * downstream-regression-na: brand-local arch test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import {
  AGENT_RIBBON_ORDER,
  RIBBON_SUBTABS,
  SHIPPED_STATIC_SUBTABS,
  AGENT_CATALOG,
  isValidAgent,
} from "@/lib/agent-catalog";

describe("arch: agent-catalog ribbon taxonomy v1.2 — Mateo=Operar, Valeria=sidebar (FE-3)", () => {
  it("AGENT_RIBBON_ORDER contains 'mateo' (specialist Operar, in ribbon now)", () => {
    expect(AGENT_RIBBON_ORDER).toContain("mateo");
  });

  it("AGENT_RIBBON_ORDER does NOT contain 'valeria' (supervisor sidebar, not ribbon tab)", () => {
    expect(AGENT_RIBBON_ORDER).not.toContain("valeria");
  });

  it("AGENT_RIBBON_ORDER has exactly 5 entries: lisa · mateo · adrián · lucas · camila", () => {
    expect(AGENT_RIBBON_ORDER).toHaveLength(5);
    expect([...AGENT_RIBBON_ORDER].sort()).toEqual(
      ["adrian", "camila", "lisa", "lucas", "mateo"].sort()
    );
  });

  it("RIBBON_SUBTABS.mateo contains 'agenda' sub-tab (migrated from valeria)", () => {
    const mateoSubtabs = RIBBON_SUBTABS.mateo.map((s) => s.id);
    expect(mateoSubtabs).toContain("agenda");
  });

  it("RIBBON_SUBTABS.mateo contains 'pacientes' sub-tab (migrated from valeria)", () => {
    const mateoSubtabs = RIBBON_SUBTABS.mateo.map((s) => s.id);
    expect(mateoSubtabs).toContain("pacientes");
  });

  it("RIBBON_SUBTABS.mateo has exactly 2 entries: agenda + pacientes", () => {
    expect(RIBBON_SUBTABS.mateo).toHaveLength(2);
  });

  it("RIBBON_SUBTABS.valeria is empty (valeria is sidebar-only, not a ribbon agent)", () => {
    expect(RIBBON_SUBTABS.valeria).toHaveLength(0);
  });

  it("SHIPPED_STATIC_SUBTABS contains 'mateo.agenda' (agenda migrated to mateo)", () => {
    expect(SHIPPED_STATIC_SUBTABS.has("mateo.agenda")).toBe(true);
  });

  it("SHIPPED_STATIC_SUBTABS does NOT contain 'valeria.agenda' (valeria removed from ribbon)", () => {
    expect(SHIPPED_STATIC_SUBTABS.has("valeria.agenda")).toBe(false);
  });

  it("AGENT_CATALOG.mateo.tabLabel is 'Atender' (v1.3 — renamed from 'Operar')", () => {
    expect(AGENT_CATALOG.mateo.tabLabel).toBe("Atender");
  });

  it("AGENT_CATALOG.mateo.defaultSubtab is 'agenda'", () => {
    expect(AGENT_CATALOG.mateo.defaultSubtab).toBe("agenda");
  });

  it("isValidAgent('mateo') returns true — mateo is now a ribbon agent", () => {
    expect(isValidAgent("mateo")).toBe(true);
  });

  it("isValidAgent('valeria') returns false — valeria is supervisor sidebar, not ribbon", () => {
    expect(isValidAgent("valeria")).toBe(false);
  });

  it("isValidAgent('config') still returns true — config tab unchanged", () => {
    expect(isValidAgent("config")).toBe(true);
  });
});
