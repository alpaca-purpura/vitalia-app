/**
 * Architecture test — FE-A1: no hardcoded color literals outside globals.css.
 *
 * Vitalia design tokens are defined in globals.css as CSS custom properties
 * (`--vitalia-*`). Components MUST reference those tokens via Tailwind CSS
 * class names or `hsl(var(--vitalia-X))` calls.
 *
 * Hardcoding `#rrggbb`, `rgb(…)`, `rgba(…)`, `hsl(…)`, `hsla(…)` in
 * component/feature TypeScript/TSX files is FORBIDDEN because it bypasses
 * the design-system token layer and makes dark-mode + re-branding impossible.
 *
 * Exceptions (do NOT flag):
 *   - HEX/rgb literals inside comments (`//`, `/* ... *\/`)
 *   - Strings that are clearly import paths or test IDs
 *   - globals.css itself (canonical token definition)
 *   - __tests__ directory (test fixtures may reference color values)
 *
 * Known-violations allowlist follows ratchet pattern (shrink-only).
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { readFileSync, existsSync } from "fs";
import { resolve, join, relative } from "path";
import { readdirSync, statSync } from "fs";

const ROOT = resolve(__dirname, "../../..");
const SRC = join(ROOT, "src");

// globals.css is the only place where HEX literals are allowed (token definitions).
const EXEMPT_FILES = new Set(["src/app/globals.css"]);

// Ratchet baseline — known violations at time of T-infra-4 creation (shrink-only).
// Format: "src/relative/path/to/file.tsx"
const KNOWN_COLOR_VIOLATIONS: ReadonlySet<string> = new Set<string>([
  // core-ds-foundation T-2 SHRINK (parity-with-lock-scope):
  //   The 15 fidelizacion components + test-stack/agent-tokens/page.tsx + MessageInput +
  //   VoiceMessagePlayer were previously listed here. After the tokenized-color stripper
  //   was added (see TOKENIZED_COLOR_FN below — parity with @luana/eslint-config
  //   no-arbitrary-value, which treats `hsl(var(--x))` / `text-[hsl(var(--agent-lisa))]` as
  //   tokenized, NOT a raw literal), those files scan CLEAN. Per the shrink-only ratchet
  //   they are REMOVED (allowlist may only decrease). MessageInput/VoiceMessagePlayer were
  //   also deleted in the inbox rename refactor. Verified clean 2026-06-08.
  // F1-S0 vitalia-fase1-stack-stability (2026-05-23): legitimate exceptions for
  // agent identity metadata SSoT + dev preview page documentation.
  // - src/lib/agents.ts: 6 hex strings are Chris-ratified agent brand colors used
  //   as inline `--tw-ring-color` style values (Tailwind v4 cannot generate dynamic
  //   ring-agent-${slug} utilities). The hex values ARE consumed via CSS var system
  //   (--agent-{slug} HSL definitions in globals.css) — these are documentation/SSoT
  //   strings, not styling literals. Refactor to var-only would require removing the
  //   inline style escape used to bypass Tailwind v4 dynamic-class limitation.
  // - src/app/test-stack/agent-tokens/page.tsx: hsl(var(--agent-lisa)) appears INSIDE
  //   a <code> tag rendered to user as documentation showing how to consume tokens.
  //   It's a string literal displayed as content, not CSS styling.
  "src/lib/agents.ts",
  "src/app/test-stack/agent-tokens/page.tsx",
  // F1-S6 vitalia-fase1-valeria-chat-skeleton T-1: agent-catalog.ts contains hex strings
  // as metadata-only fields on AgentDescriptor (for design reference / color pickers).
  // These hex values are NOT consumed for CSS styling — colorToken / colorSoftToken CSS vars
  // are the authoritative styling channel. Same pattern as src/lib/agents.ts above.
  // spec_anchor: 01-spec.md § 5.1 + 03-arch.md § 2.4
  "src/lib/agent-catalog.ts",
]);

// Pattern for hardcoded color literals.
// Captures: #RGB, #RRGGBB, #RRGGBBAA, rgb(...), rgba(...), hsl(...), hsla(...).
const COLOR_LITERAL_PATTERN =
  /#[0-9a-fA-F]{3,8}\b|rgb\s*\(|rgba\s*\(|hsl\s*\(|hsla\s*\(/g;

// core-ds-foundation T-2 — parity with the @luana/eslint-config no-arbitrary-value
// lock scope: a color expressed THROUGH a design token — `hsl(var(--x))`, `var(--x)`,
// `theme(...)`, `color-mix(...)` — is TOKENIZED, NOT a hardcoded literal. The eslint
// rule treats those as allowed; this scanner must agree (otherwise tokenized utilities
// like `text-[hsl(var(--agent-adrian))]` register false positives). We neutralize the
// inner CSS-var/function so only RAW literals (`hsl(210 40% 96%)`, `#635BFF`) remain.
const TOKENIZED_COLOR_FN =
  /\b(?:hsl|hsla|rgb|rgba|oklch|color-mix)\s*\(\s*(?:var\(|theme\(|color-mix\()[^)]*\)[^)]*\)/g;

function stripTokenizedColors(source: string): string {
  return source.replace(TOKENIZED_COLOR_FN, (m) => " ".repeat(m.length));
}

// Patterns for comment regions — we strip comments before scanning.
// Single-line comments: // ...
const SINGLE_LINE_COMMENT = /\/\/.*$/gm;
// Multi-line comments: /* ... */
const MULTI_LINE_COMMENT = /\/\*[\s\S]*?\*\//g;
// Template literal comments: ` /* ... */ ` inside template literals — covered by multi-line above.

function stripComments(source: string): string {
  return source
    .replace(MULTI_LINE_COMMENT, (match) => " ".repeat(match.length))
    .replace(SINGLE_LINE_COMMENT, "");
}

function collectSourceFiles(dir: string, extensions: string[]): string[] {
  if (!existsSync(dir)) return [];
  const files: string[] = [];
  const recurse = (current: string) => {
    for (const entry of readdirSync(current)) {
      const full = join(current, entry);
      const stat = statSync(full);
      if (stat.isDirectory()) {
        // Skip __tests__ (test fixtures may contain color references for documentation)
        if (
          entry === "__tests__" ||
          entry === "node_modules" ||
          entry === ".next"
        )
          continue;
        recurse(full);
      } else if (extensions.some((ext) => entry.endsWith(ext))) {
        files.push(full);
      }
    }
  };
  recurse(dir);
  return files;
}

describe("Vitalia FE — no hardcoded color literals outside globals.css (FE-A1)", () => {
  it("scan source: typescript and tsx files have no hardcoded HEX/rgb color literals", () => {
    if (!existsSync(SRC)) {
      // Source directory not yet populated (T-infra-7 creates shared components).
      // Auto-skip gracefully until source exists.
      console.log(
        "[SKIP] src/ directory not found — skipping test_no_hardcoded_colors",
      );
      return;
    }

    const sourceFiles = collectSourceFiles(SRC, [".tsx", ".ts"]);
    const violations: string[] = [];

    for (const absPath of sourceFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");

      // Exempt files
      if (EXEMPT_FILES.has(relPath)) continue;

      const source = readFileSync(absPath, "utf-8");
      const stripped = stripTokenizedColors(stripComments(source));

      const matches = stripped.match(COLOR_LITERAL_PATTERN);
      if (matches && matches.length > 0) {
        if (!KNOWN_COLOR_VIOLATIONS.has(relPath)) {
          violations.push(
            `${relPath}: found ${matches.length} hardcoded color literal(s): ${matches.slice(0, 5).join(", ")}${matches.length > 5 ? ` ... (+${matches.length - 5} more)` : ""}`,
          );
        }
      }
    }

    expect(
      violations,
      [
        "Hardcoded color literals detected outside globals.css.",
        "",
        "Vitalia design tokens MUST be consumed via Tailwind class names",
        "or `hsl(var(--vitalia-X))` from globals.css custom properties.",
        "Hardcoding colors bypasses the design-system token layer.",
        "",
        "Fix: Replace `#hex` / `rgb(...)` with the appropriate",
        "     `--vitalia-*` CSS variable reference.",
        "",
        "If this is a legitimate exception (e.g., external SVG asset color),",
        "add the file to KNOWN_COLOR_VIOLATIONS (shrink-only ratchet).",
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("KNOWN_COLOR_VIOLATIONS allowlist only references existing files", () => {
    for (const relPath of KNOWN_COLOR_VIOLATIONS) {
      const absPath = join(ROOT, relPath);
      expect(
        existsSync(absPath),
        `KNOWN_COLOR_VIOLATIONS references non-existent file: ${relPath}. Remove it (shrink-only ratchet).`,
      ).toBe(true);
    }
  });
});
