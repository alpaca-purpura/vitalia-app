/**
 * Arch fitness test: AGENT_SUBSUBTABS catalog (shell-routes.ts) consistency.
 *
 * T-4 vitalia-fase2-lisa-marca — ADR-vitalia-004 v1.1 enforcement
 *
 * Invariants verified:
 *   1. AGENT_SUBSUBTABS has an entry for "lisa.marca" (F2-S7 T-4 shipped)
 *   2. lisa.marca entry has exactly 3 sub-sub-tabs: identidad, voz-y-tono, presencia
 *   3. All AGENT_SUBSUBTABS keys follow "{agent}.{subtab}" format
 *   4. Every AGENT_SUBSUBTABS entry has at least 1 sub-sub-tab
 *   5. Every sub-sub-tab id uses kebab-case (no spaces, no uppercase)
 *   6. Every sub-sub-tab has non-empty label and icon
 *   7. Static page.tsx files exist for each sub-sub-tab entry (routing integrity)
 *   8. SHIPPED_STATIC_SUBTABS includes "lisa.marca" (agent-catalog.ts sync)
 *
 * spec_anchor: ADR-vitalia-004 v1.1 § 3.1.1 + 03-arch.md § T-4
 * downstream-regression-na: brand-local arch test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { existsSync } from "fs";
import { resolve } from "path";
import { AGENT_SUBSUBTABS } from "@/lib/shell-routes";
import { SHIPPED_STATIC_SUBTABS } from "@/lib/agent-catalog";

const SRC_ROOT = resolve(__dirname, "../..");
const APP_ROOT = resolve(SRC_ROOT, "app");

describe("Architecture: AGENT_SUBSUBTABS catalog — shell-routes.ts SSoT", () => {
  it("AGENT_SUBSUBTABS has an entry for 'lisa.marca' (F2-S7 T-4)", () => {
    expect(AGENT_SUBSUBTABS["lisa.marca"]).toBeDefined();
    expect(Array.isArray(AGENT_SUBSUBTABS["lisa.marca"])).toBe(true);
  });

  it("lisa.marca has exactly 3 sub-sub-tabs", () => {
    const subsubtabs = AGENT_SUBSUBTABS["lisa.marca"];
    expect(subsubtabs).toHaveLength(3);
  });

  it("lisa.marca sub-sub-tabs are: identidad, voz-y-tono, presencia (in order)", () => {
    const subsubtabs = AGENT_SUBSUBTABS["lisa.marca"];
    const ids = subsubtabs?.map((t) => t.id);
    expect(ids).toEqual(["identidad", "voz-y-tono", "presencia"]);
  });

  it("all AGENT_SUBSUBTABS keys follow '{agent}.{subtab}' format", () => {
    for (const key of Object.keys(AGENT_SUBSUBTABS)) {
      expect(key).toMatch(/^[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*$/);
    }
  });

  it("every AGENT_SUBSUBTABS entry has at least 1 sub-sub-tab", () => {
    for (const [key, subsubtabs] of Object.entries(AGENT_SUBSUBTABS)) {
      expect(
        Array.isArray(subsubtabs) && subsubtabs.length > 0,
        `Entry '${key}' must have at least 1 sub-sub-tab`,
      ).toBe(true);
    }
  });

  it("every sub-sub-tab id uses kebab-case (no spaces, no uppercase)", () => {
    for (const [key, subsubtabs] of Object.entries(AGENT_SUBSUBTABS)) {
      if (!subsubtabs) continue;
      for (const tab of subsubtabs) {
        expect(
          tab.id,
          `Sub-sub-tab id '${tab.id}' in '${key}' must be kebab-case`,
        ).toMatch(/^[a-z][a-z0-9-]*$/);
      }
    }
  });

  it("every sub-sub-tab has non-empty label and icon", () => {
    for (const [key, subsubtabs] of Object.entries(AGENT_SUBSUBTABS)) {
      if (!subsubtabs) continue;
      for (const tab of subsubtabs) {
        expect(
          tab.label.length > 0,
          `Sub-sub-tab '${tab.id}' in '${key}' must have non-empty label`,
        ).toBe(true);
        expect(
          tab.icon.length > 0,
          `Sub-sub-tab '${tab.id}' in '${key}' must have non-empty icon`,
        ).toBe(true);
      }
    }
  });

  it("SHIPPED_STATIC_SUBTABS includes 'lisa.marca' (agent-catalog sync)", () => {
    expect(SHIPPED_STATIC_SUBTABS.has("lisa.marca")).toBe(true);
  });

  it("SHIPPED_STATIC_SUBTABS includes 'mateo.agenda' (paradigm-map-zones T-5 — migrated from valeria.agenda)", () => {
    // v1.2 (2026-05-30): valeria.agenda → mateo.agenda (Mateo=Operar, Valeria=sidebar)
    expect(SHIPPED_STATIC_SUBTABS.has("mateo.agenda")).toBe(true);
    // valeria.agenda was removed from SHIPPED_STATIC_SUBTABS (valeria is sidebar-only now)
    expect(SHIPPED_STATIC_SUBTABS.has("valeria.agenda")).toBe(false);
  });
});

describe("Architecture: N3-static page.tsx files exist for AGENT_SUBSUBTABS entries", () => {
  it("lisa/marca redirect page.tsx exists", () => {
    const pagePath = resolve(
      APP_ROOT,
      "[tenantId]/(shell-organism)/lisa/marca/page.tsx",
    );
    expect(existsSync(pagePath), `Missing: ${pagePath}`).toBe(true);
  });

  it("lisa/marca/identidad page.tsx exists", () => {
    const pagePath = resolve(
      APP_ROOT,
      "[tenantId]/(shell-organism)/lisa/marca/identidad/page.tsx",
    );
    expect(existsSync(pagePath), `Missing: ${pagePath}`).toBe(true);
  });

  it("lisa/marca/voz-y-tono page.tsx exists", () => {
    const pagePath = resolve(
      APP_ROOT,
      "[tenantId]/(shell-organism)/lisa/marca/voz-y-tono/page.tsx",
    );
    expect(existsSync(pagePath), `Missing: ${pagePath}`).toBe(true);
  });

  it("lisa/marca/presencia page.tsx exists", () => {
    const pagePath = resolve(
      APP_ROOT,
      "[tenantId]/(shell-organism)/lisa/marca/presencia/page.tsx",
    );
    expect(existsSync(pagePath), `Missing: ${pagePath}`).toBe(true);
  });
});
