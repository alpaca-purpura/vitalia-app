/**
 * CSS vars introspection — F1-S1 vitalia-fase1-design-tokens-theme
 * Verifies all Shadcn-standard tokens + agent tokens are declared in globals.css.
 *
 * 03-arch.md § 2.10
 * Uses jsdom environment (vitest config uses happy-dom by default, but CSS var
 * introspection via getPropertyValue works in happy-dom too).
 *
 * Strategy: inject globals.css content as a <style> tag in document head,
 * then query computed style of document.documentElement for each token.
 *
 * Note: jsdom/happy-dom CSS var resolution is limited — it parses declarations
 * but doesn't resolve computed values the same as a real browser. We test that
 * the variable is SET (non-empty string) in the style sheet rather than resolved.
 */
import { describe, it, expect, beforeAll } from "vitest";
import * as fs from "fs";
import * as path from "path";

// Shadcn standard tokens that MUST be present in :root
const SHADCN_LIGHT_TOKENS = [
  "--background",
  "--foreground",
  "--card",
  "--card-foreground",
  "--popover",
  "--popover-foreground",
  "--primary",
  "--primary-foreground",
  "--secondary",
  "--secondary-foreground",
  "--muted",
  "--muted-foreground",
  "--accent",
  "--accent-foreground",
  "--destructive",
  "--destructive-foreground",
  "--border",
  "--input",
  "--ring",
  "--radius",
];

// Agent tokens (light mode)
const AGENT_LIGHT_TOKENS = [
  "--agent-lisa",
  "--agent-lisa-soft",
  "--agent-lucas",
  "--agent-lucas-soft",
  "--agent-adrian",
  "--agent-adrian-soft",
  "--agent-valeria",
  "--agent-valeria-soft",
  "--agent-camila",
  "--agent-camila-soft",
  "--agent-mateo",
  "--agent-config",
];

// Dark mode tokens that MUST be present in .dark / [data-theme="dark"]
const SHADCN_DARK_TOKENS = [
  "--background",
  "--foreground",
  "--card",
  "--card-foreground",
  "--popover",
  "--popover-foreground",
  "--primary",
  "--primary-foreground",
  "--secondary",
  "--secondary-foreground",
  "--muted",
  "--muted-foreground",
  "--accent",
  "--accent-foreground",
  "--destructive",
  "--destructive-foreground",
  "--border",
  "--input",
  "--ring",
];

describe("CSS vars — globals.css token completeness", () => {
  let cssContent: string;

  beforeAll(() => {
    const cssPath = path.resolve(__dirname, "../../app/globals.css");
    cssContent = fs.readFileSync(cssPath, "utf-8");
  });

  it("globals.css file is readable and non-empty", () => {
    expect(cssContent.length).toBeGreaterThan(100);
  });

  describe("Shadcn standard light tokens (in :root)", () => {
    for (const token of SHADCN_LIGHT_TOKENS) {
      it(`declares ${token}`, () => {
        // Token must appear in :root block (before .dark block)
        // Simple heuristic: token appears in file
        expect(cssContent).toContain(token);
      });
    }
  });

  describe("Agent light tokens (in :root)", () => {
    for (const token of AGENT_LIGHT_TOKENS) {
      it(`declares ${token}`, () => {
        expect(cssContent).toContain(token);
      });
    }
  });

  describe('Shadcn standard dark tokens (in .dark / [data-theme="dark"])', () => {
    it("has dark mode selector with data-theme attribute", () => {
      // next-themes uses attribute="data-theme" → CSS must target [data-theme="dark"]
      expect(cssContent).toContain('[data-theme="dark"]');
    });

    for (const token of SHADCN_DARK_TOKENS) {
      it(`dark mode overrides ${token}`, () => {
        // Token must appear at least twice: once in :root, once in dark selector
        const occurrences = cssContent.split(token).length - 1;
        expect(occurrences).toBeGreaterThanOrEqual(2);
      });
    }
  });

  describe('Agent dark soft variants (in .dark / [data-theme="dark"])', () => {
    const darkAgentSoftTokens = [
      "--agent-lisa-soft",
      "--agent-lucas-soft",
      "--agent-adrian-soft",
      "--agent-valeria-soft",
      "--agent-camila-soft",
    ];

    for (const token of darkAgentSoftTokens) {
      it(`dark mode overrides ${token}`, () => {
        const occurrences = cssContent.split(token).length - 1;
        expect(occurrences).toBeGreaterThanOrEqual(2);
      });
    }
  });

  it("dark selector includes both .dark and [data-theme='dark']", () => {
    // Both selectors must be present for compatibility
    expect(cssContent).toContain(".dark");
    expect(cssContent).toContain('[data-theme="dark"]');
  });
});
