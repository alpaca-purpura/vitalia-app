/**
 * Arch fitness test: no hardcoded sub-tab key strings outside SubTabContent.tsx.
 * F1-S10 vitalia-fase1-empty-states — T-9
 *
 * The 22 "{agent}.{subtab}" composite keys are the SSoT of SubTabContent.tsx.
 * No other file in the codebase should hardcode these strings as literals.
 * Using them elsewhere creates implicit coupling that bypasses the registry.
 *
 * Allowed locations:
 *   - SubTabContent.tsx (the SSoT)
 *   - agent-catalog.ts (the RIBBON_SUBTABS source, not hardcoded as composite)
 *   - Architecture test files (this file and related tests)
 *
 * Method: glob TS/TSX source files, regex scan for the composite key pattern.
 *
 * spec_anchor: 03-arch.md § 4 + 06-tickets.yaml T-9 val-fe-arch-no-hardcoded-keys
 * downstream-regression-na: brand-local arch test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, statSync } from "fs";
import { resolve, relative } from "path";
import { RIBBON_SUBTABS } from "@/lib/agent-catalog";

// __dirname = vitalia/frontend/src/__tests__/architecture
// ../.. = vitalia/frontend/src (SRC_ROOT)
const SRC_ROOT = resolve(__dirname, "../..");

// Files explicitly allowed to contain composite sub-tab keys.
// Paths are relative to SRC_ROOT (vitalia/frontend/src/).
const ALLOWED_FILES = new Set([
  "components/shared/shell-organism/SubTabContent.tsx",
  "lib/agent-catalog.ts",
  // F2-S7 T-4 (ADR-vitalia-004 v1.1): shell-routes.ts is the N3-static SSoT catalog.
  // AGENT_SUBSUBTABS uses composite keys as first-class identifiers for sub-sub-tab routing.
  // Analogous to SubTabContent.tsx for N2 → shell-routes.ts is SSoT for N3.
  "lib/shell-routes.ts",
  // Arch test files are allowed (this file + related tests)
  "__tests__/architecture/test_subtab_content_uses_ribbon_subtabs_ssot.test.ts",
  "__tests__/architecture/test_no_hardcoded_subtab_keys.test.ts",
  "__tests__/architecture/test_no_phi_real_data.test.ts",
  // F2-S7 T-4: arch test for AGENT_SUBSUBTABS catalog uses composite keys as test fixtures
  "__tests__/architecture/test-agent-subsubtabs-ssot.test.ts",
  // paradigm-map-zones T-5: ribbon taxonomy test verifies mateo.agenda + valeria.agenda as string literals
  "__tests__/architecture/agent-catalog-ribbon-taxonomy.test.ts",
  // F2-S8 T-FE-1 (2026-05-31): agent-catalog unit tests reference composite keys to verify RIBBON_SUBTABS structure
  "lib/__tests__/agent-catalog.test.ts",
]);

/**
 * Build the set of composite key strings to check:
 * "agent.subtab" for all 22 valid sub-tab combinations.
 */
function buildCompositeKeys(): string[] {
  const keys: string[] = [];
  for (const [agent, subtabs] of Object.entries(RIBBON_SUBTABS)) {
    for (const sub of subtabs) {
      keys.push(`${agent}.${sub.id}`);
    }
  }
  return keys;
}

/**
 * Recursively collect all .ts and .tsx files under a directory.
 * Excludes node_modules and .next.
 */
function collectSourceFiles(dir: string): string[] {
  const files: string[] = [];
  try {
    const entries = readdirSync(dir);
    for (const entry of entries) {
      if (
        entry === "node_modules" ||
        entry === ".next" ||
        entry.startsWith(".")
      ) {
        continue;
      }
      const fullPath = resolve(dir, entry);
      try {
        const stat = statSync(fullPath);
        if (stat.isDirectory()) {
          files.push(...collectSourceFiles(fullPath));
        } else if (entry.endsWith(".ts") || entry.endsWith(".tsx")) {
          files.push(fullPath);
        }
      } catch {
        // skip inaccessible files
      }
    }
  } catch {
    // skip inaccessible directories
  }
  return files;
}

/**
 * Build a regex that matches any of the 22 composite keys as quoted string literals.
 * Matches: "agent.subtab" or 'agent.subtab' (as string literals in source code).
 */
function buildCompositeKeyRegex(keys: string[]): RegExp {
  const escaped = keys.map((k) => k.replace(".", "\\."));
  return new RegExp(`["'](${escaped.join("|")})["']`, "g");
}

describe("Architecture: no hardcoded sub-tab key strings outside SubTabContent", () => {
  const compositeKeys = buildCompositeKeys();
  const regex = buildCompositeKeyRegex(compositeKeys);
  const allSourceFiles = collectSourceFiles(SRC_ROOT);

  it("composite key set has 23 entries (fixture sanity check)", () => {
    // T-FE-1 (2026-06-03): Adrián gains +1 sub-tab "recuperar" → 23 total.
    expect(compositeKeys).toHaveLength(23);
  });

  it("no source file outside allowlist contains hardcoded composite sub-tab keys", () => {
    const violations: Array<{ file: string; matches: string[] }> = [];

    for (const fullPath of allSourceFiles) {
      const relPath = relative(SRC_ROOT, fullPath);
      if (ALLOWED_FILES.has(relPath)) continue;

      try {
        const content = readFileSync(fullPath, "utf-8");
        regex.lastIndex = 0;
        const matches: string[] = [];
        let match: RegExpExecArray | null;
        while ((match = regex.exec(content)) !== null) {
          matches.push(match[1]);
        }
        if (matches.length > 0) {
          violations.push({ file: relPath, matches });
        }
      } catch {
        // skip unreadable files
      }
    }

    if (violations.length > 0) {
      const report = violations
        .map((v) => `  ${v.file}: [${v.matches.join(", ")}]`)
        .join("\n");
      expect.fail(
        `Hardcoded sub-tab key strings found outside allowlist:\n${report}\n\n` +
          `Use agent-catalog.ts RIBBON_SUBTABS as SSoT. SubTabContent.tsx is the single point of truth for composite keys.`,
      );
    }

    expect(violations).toHaveLength(0);
  });
});
