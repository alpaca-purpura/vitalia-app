/**
 * Arch fitness test: SubTabContent PLACEHOLDER_MAP uses RIBBON_SUBTABS as SSoT.
 * F1-S10 vitalia-fase1-empty-states — T-9
 * F2-S1 vitalia-fase2-valeria-agenda — 07-merge.md W3 cleanup
 * paradigm-map-zones T-5 — mateo.pacientes added (mateo is now a ribbon agent)
 *
 * Invariants verified:
 *   1. Every key in PLACEHOLDER_MAP is present in RIBBON_SUBTABS (no orphan placeholders)
 *   2. Every RIBBON_SUBTABS entry NOT shipped as static route has a PLACEHOLDER_MAP key
 *   3. PLACEHOLDER_MAP === RIBBON_SUBTABS keys minus SHIPPED_STATIC_SUBTABS
 *   4. No 'valeria.*' keys (RIBBON_SUBTABS.valeria === [] since v1.2)
 *   5. SHIPPED_STATIC_SUBTABS keys are NOT in PLACEHOLDER_MAP (no overlap)
 *
 * Note (v1.2): mateo now has 2 subtabs [agenda, pacientes].
 *   mateo.agenda is in SHIPPED_STATIC_SUBTABS → excluded from PLACEHOLDER_MAP.
 *   mateo.pacientes is NOT shipped → MUST be in PLACEHOLDER_MAP.
 *
 * Method: parse SubTabContent.tsx source + read RIBBON_SUBTABS + SHIPPED_STATIC_SUBTABS at runtime.
 *
 * spec_anchor: 03-arch.md § 4 + 06-tickets.yaml T-9 val-fe-arch-subtab-content-ssot
 *              + archive/.../vitalia-fase2-valeria-agenda/07-merge.md W3
 *              + paradigm-map-zones/03-arch-fe.md § F6
 * downstream-regression-na: brand-local arch test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { resolve } from "path";
import { RIBBON_SUBTABS, SHIPPED_STATIC_SUBTABS } from "@/lib/agent-catalog";

// __dirname = vitalia/frontend/src/__tests__/architecture
// ../../.. = vitalia/frontend/src (SRC_ROOT)
const SRC_ROOT = resolve(__dirname, "../..");
const SUBTAB_CONTENT_PATH = resolve(
  SRC_ROOT,
  "components/shared/shell-organism/SubTabContent.tsx",
);

/**
 * Parse PLACEHOLDER_MAP keys from SubTabContent.tsx source.
 * Regex matches quoted string keys in the form "agent.subtab":
 * e.g. "lisa.marca": ... or 'lisa.marca': ...
 */
function parsePlaceholderMapKeys(source: string): Set<string> {
  const keys = new Set<string>();
  // Match "agent.subtab" keys inside the PLACEHOLDER_MAP block
  const mapBlockMatch = source.match(
    /const PLACEHOLDER_MAP\s*=\s*\{([\s\S]*?)\}\s*as const/,
  );
  if (!mapBlockMatch) return keys;

  const mapBlock = mapBlockMatch[1];
  const keyRegex = /"(\w+)\.(\w+)":/g;
  let match: RegExpExecArray | null;
  while ((match = keyRegex.exec(mapBlock)) !== null) {
    keys.add(`${match[1]}.${match[2]}`);
  }
  return keys;
}

/**
 * Derive valid RIBBON_SUBTABS keys: "{agent}.{subtab}" for all non-empty agents.
 * Excludes mateo (empty array, transversal agent).
 */
function getRibbonSubtabsKeys(): Set<string> {
  const keys = new Set<string>();
  for (const [agent, subtabs] of Object.entries(RIBBON_SUBTABS)) {
    for (const sub of subtabs) {
      keys.add(`${agent}.${sub.id}`);
    }
  }
  return keys;
}

/**
 * Sub-tab keys que el dispatcher PLACEHOLDER_MAP debe cubrir:
 * = RIBBON_SUBTABS keys − SHIPPED_STATIC_SUBTABS (rutas estáticas shadowean al dispatcher).
 */
function getDispatcherCoveredKeys(): Set<string> {
  const keys = new Set<string>();
  for (const key of getRibbonSubtabsKeys()) {
    if (!SHIPPED_STATIC_SUBTABS.has(key as Parameters<typeof SHIPPED_STATIC_SUBTABS.has>[0])) {
      keys.add(key);
    }
  }
  return keys;
}

describe("Architecture: SubTabContent PLACEHOLDER_MAP ↔ RIBBON_SUBTABS SSoT", () => {
  const source = readFileSync(SUBTAB_CONTENT_PATH, "utf-8");
  const placeholderKeys = parsePlaceholderMapKeys(source);
  const ribbonKeys = getRibbonSubtabsKeys();
  const dispatcherCovered = getDispatcherCoveredKeys();

  it("RIBBON_SUBTABS has exactly 23 valid sub-tab entries (valeria excluded — v1.2 sidebar-only)", () => {
    // v1.2 (2026-05-30): mateo gains 2 subtabs [agenda, pacientes], valeria=0 (sidebar).
    // T-FE-1 (2026-06-03): Adrián gains +1 sub-tab "recuperar" → 5 total (RN-19 v3.1).
    // Total is 23: lisa(4) + mateo(2) + lucas(5) + adrian(5) + camila(4) + config(3) = 23.
    expect(ribbonKeys.size).toBe(23);
  });

  it("PLACEHOLDER_MAP parses RIBBON_SUBTABS - SHIPPED_STATIC_SUBTABS keys from source", () => {
    expect(placeholderKeys.size).toBe(ribbonKeys.size - SHIPPED_STATIC_SUBTABS.size);
  });

  it("every PLACEHOLDER_MAP key is a valid RIBBON_SUBTABS key (no orphan placeholders)", () => {
    const orphans: string[] = [];
    for (const key of placeholderKeys) {
      if (!ribbonKeys.has(key)) {
        orphans.push(key);
      }
    }
    expect(orphans).toEqual([]);
  });

  it("every RIBBON_SUBTABS key NOT shipped as static has a PLACEHOLDER_MAP entry", () => {
    const missing: string[] = [];
    for (const key of dispatcherCovered) {
      if (!placeholderKeys.has(key)) {
        missing.push(key);
      }
    }
    expect(missing).toEqual([]);
  });

  it("no 'valeria.*' keys exist in PLACEHOLDER_MAP (valeria is sidebar-only — v1.2)", () => {
    // v1.2 (2026-05-30): valeria has 0 subtabs in RIBBON_SUBTABS (sidebar supervisor).
    // mateo.pacientes IS valid (mateo has 2 subtabs now; only mateo.agenda is shipped static).
    const valeriaKeys = [...placeholderKeys].filter((k) =>
      k.startsWith("valeria."),
    );
    expect(valeriaKeys).toEqual([]);
  });

  it("SHIPPED_STATIC_SUBTABS keys are NOT in PLACEHOLDER_MAP (no overlap)", () => {
    const leaked: string[] = [];
    for (const staticKey of SHIPPED_STATIC_SUBTABS) {
      if (placeholderKeys.has(staticKey)) {
        leaked.push(staticKey);
      }
    }
    expect(leaked).toEqual([]);
  });

  it("PLACEHOLDER_MAP keys match RIBBON_SUBTABS - SHIPPED_STATIC_SUBTABS exactly", () => {
    const placeholderArray = [...placeholderKeys].sort();
    const expectedArray = [...dispatcherCovered].sort();
    expect(placeholderArray).toEqual(expectedArray);
  });
});
