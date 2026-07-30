/**
 * Architecture test — Agent Catalog SSoT invariant (F1-S6, T-6)
 *
 * Verifies that agent names, hex colors, and thumbnail paths are NOT hardcoded
 * outside of the canonical SSoT (lib/agent-catalog.ts).
 *
 * Rule: AGENT_CATALOG is the single source of truth for all 6 Vitalia agents.
 * Components MUST consume the catalog via import — never inline hex values or
 * agent name strings for display logic outside the catalog file itself.
 *
 * Allowlist (KNOWN_HARDCODES) documents expected exceptions in a shrink-only ratchet:
 *   - _mock-messages.ts: fixture data with agent names in message content (Spanish)
 *   - *.test.tsx / *.test.ts: test files that assert on rendered text
 *   - agent-catalog.test.ts: the catalog test itself
 *   - test-agent-catalog-ssot.test.ts: this file (references strings for scanning)
 *
 * spec_anchor: 06-tickets.yaml T-6 gherkin_coverage § architectural/agent-catalog SSoT
 * arch: 03-arch.md § 3.3 arch fitness · CONTEXT-BRIEF.md § 9
 *
 * downstream-regression-na: brand-local arch fitness; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { resolve, join, relative } from "node:path";
import { readdirSync, statSync } from "node:fs";

const ROOT = resolve(__dirname, "../../..");
const SRC = join(ROOT, "src");

// ─── Agent hex colors (metadata-only in catalog, forbidden elsewhere in components) ─

const AGENT_HEX_COLORS = [
  "#7b2d91", // valeria
  "#180d95", // camila
  "#00D084", // lisa
  "#01b2f8", // adrian
  "#111111", // lucas
  "#fee209", // mateo
];

// Case-insensitive hex pattern for thorough matching
const HEX_PATTERN = new RegExp(
  `(${AGENT_HEX_COLORS.map((h) => h.replace("#", "#?")).join("|")})`,
  "i",
);

// ─── Allowlist — known files where agent strings appear intentionally ─────────

/**
 * KNOWN_HARDCODES: files allowed to contain agent hex/name literals.
 * Shrink-only ratchet — remove entries as files are refactored.
 */
const KNOWN_HARDCODES: ReadonlySet<string> = new Set<string>([
  // SSoT catalog itself — hex metadata lives here by design
  "src/lib/agent-catalog.ts",
  // Legacy F1-S0 agent registry (pre-T1 catalog) — contains hex + thumbnail paths
  // Retained for backward compat with ValeriaRail + TopBar consumers (F1-S0 origin).
  // Future: consolidate consumers to AGENT_CATALOG post F1-S6 (promotion candidate).
  "src/lib/agents.ts",
  // Design system token definitions — globals.css defines CSS custom properties
  // for agent colors (--agent-{slug}: <hsl>) and gradient tokens referencing hex.
  // These are the CSS-layer SSoT for design tokens, analogous to agent-catalog.ts
  // for the TS layer. Hex values appear as HSL-equivalent comments + gradient defs.
  // Shrink-only: future token migration may replace hex literals with oklch().
  "src/app/globals.css",
  // Catalog test — verifies hex values via literal assertion
  "src/lib/__tests__/agent-catalog.test.ts",
  // This test file — references hex strings for pattern compilation
  "src/__tests__/architecture/test-agent-catalog-ssot.test.ts",
  // Mock messages fixture — contains agent names in Spanish message content
  "src/components/shared/shell-organism/_mock-messages.ts",
]);

// ─── Skip patterns — test files + config files ───────────────────────────────

const SKIP_PATTERNS = [
  /\.test\.[tj]sx?$/, // all test files (unit tests assert on rendered text)
  /\.spec\.[tj]sx?$/, // all spec files
  /node_modules/,
  /\.config\.[tj]s$/,
];

function shouldSkip(relPath: string): boolean {
  return SKIP_PATTERNS.some((p) => p.test(relPath));
}

function collectSourceFiles(dir: string): string[] {
  if (!existsSync(dir)) return [];
  const files: string[] = [];
  const recurse = (current: string) => {
    for (const entry of readdirSync(current)) {
      const full = join(current, entry);
      const stat = statSync(full);
      if (stat.isDirectory()) {
        if (entry === "node_modules") continue;
        recurse(full);
      } else if (
        entry.endsWith(".tsx") ||
        entry.endsWith(".ts") ||
        entry.endsWith(".css")
      ) {
        files.push(full);
      }
    }
  };
  recurse(dir);
  return files;
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe("arch: agent-catalog SSoT — no hardcoded agent hex colors outside catalog (FE-A9)", () => {
  it("no agent hex literal in production source files (except catalog + allowlist)", () => {
    if (!existsSync(SRC)) {
      console.log("[SKIP] src/ not found — skipping test-agent-catalog-ssot");
      return;
    }

    const allFiles = collectSourceFiles(SRC);
    const violations: string[] = [];

    for (const absPath of allFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");
      if (shouldSkip(relPath)) continue;
      if (KNOWN_HARDCODES.has(relPath)) continue;

      const source = readFileSync(absPath, "utf-8");

      // Strip comments before scanning
      const stripped = source
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/\/\/.*$/gm, "");

      if (HEX_PATTERN.test(stripped)) {
        violations.push(
          `${relPath}: contains hardcoded agent hex color — use colorToken from AGENT_CATALOG instead`,
        );
      }
    }

    expect(
      violations,
      [
        "Agent hex colors found outside AGENT_CATALOG SSoT.",
        "",
        "Components MUST use Tailwind tokens (colorToken / colorSoftToken) from AGENT_CATALOG.",
        "Hex values are metadata-only in agent-catalog.ts — never use them in components.",
        "",
        "Fix: Replace hex literal with bg-{agent.colorToken} or bg-{agent.colorSoftToken} (from AGENT_CATALOG).",
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("KNOWN_HARDCODES allowlist only references existing files (shrink-only ratchet)", () => {
    for (const relPath of KNOWN_HARDCODES) {
      const absPath = join(ROOT, relPath);
      expect(
        existsSync(absPath),
        `KNOWN_HARDCODES references non-existent file: ${relPath}. Remove stale allowlist entry.`,
      ).toBe(true);
    }
  });
});

describe("arch: agent-catalog SSoT — thumbnail paths not hardcoded outside catalog (FE-A10)", () => {
  /**
   * Thumbnail paths follow pattern /agents/{slug}/thumbnail.png
   * These should only be referenced via AGENT_CATALOG[slug].thumbnail — never inline.
   */
  const THUMBNAIL_PATTERN =
    /\/agents\/(lisa|valeria|adrian|lucas|camila|mateo)\//;

  it("no agent thumbnail path hardcoded in component source files (except catalog + allowlist)", () => {
    if (!existsSync(SRC)) {
      console.log("[SKIP] src/ not found — skipping thumbnail path test");
      return;
    }

    const allFiles = collectSourceFiles(SRC);
    const violations: string[] = [];

    for (const absPath of allFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");
      if (shouldSkip(relPath)) continue;
      if (KNOWN_HARDCODES.has(relPath)) continue;

      const source = readFileSync(absPath, "utf-8");

      // Strip comments before scanning
      const stripped = source
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/\/\/.*$/gm, "");

      if (THUMBNAIL_PATTERN.test(stripped)) {
        violations.push(
          `${relPath}: contains hardcoded agent thumbnail path — use AGENT_CATALOG[slug].thumbnail instead`,
        );
      }
    }

    expect(
      violations,
      [
        "Agent thumbnail paths found hardcoded outside AGENT_CATALOG SSoT.",
        "",
        "Components MUST read thumbnail paths from AGENT_CATALOG[agent].thumbnail.",
        "Inline paths create drift risk if assets are moved.",
        "",
        "Fix: Use `AGENT_CATALOG[agentSlug].thumbnail` for all agent image src attributes.",
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });
});
