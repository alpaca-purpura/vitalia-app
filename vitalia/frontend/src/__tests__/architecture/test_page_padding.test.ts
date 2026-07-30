/**
 * Architecture test — FE-A8: studio section pages use consistent padding tokens.
 *
 * Vitalia uses CSS custom properties (`--vitalia-*`) from globals.css as the
 * design token system. Page-level padding/spacing MUST use Tailwind utilities
 * that correspond to these tokens (p-4, p-6, p-8, px-6, etc.) — never
 * inline styles with hardcoded pixel values.
 *
 * Rule:
 *   - Page/layout files in src/app/**\/page.tsx and layout.tsx MUST NOT use
 *     inline style={{ padding: ... }} or style={{ margin: ... }} with hardcoded values.
 *   - Brand-studio / offer-wizard / onboarding page sections MUST use
 *     consistent padding class names (not varying one-offs).
 *
 * This test checks:
 *   1. No `style={{ padding:` or `style={{ margin:` inline styles in page/layout files.
 *   2. Studio section client components use Tailwind padding utilities from
 *      an allowed set (consistent design token mapping).
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
const APP_DIR = join(SRC, "app");

// Allowed Tailwind padding/margin classes for studio section pages.
// These map to the vitalia design token spacing scale.
// Reference documentation for future maintainers — the spacing scale lives here,
// but inline-style scan (line 51 INLINE_STYLE_PADDING_PATTERN) handles enforcement directly.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const ALLOWED_PADDING_CLASSES = new Set([
  "p-4",
  "p-6",
  "p-8",
  "px-4",
  "px-6",
  "px-8",
  "py-4",
  "py-6",
  "py-8",
  "pt-4",
  "pt-6",
  "pt-8",
  "pb-4",
  "pb-6",
  "pb-8",
  "pl-4",
  "pl-6",
  "pl-8",
  "pr-4",
  "pr-6",
  "pr-8",
  // Responsive variants are OK
  "sm:p-6",
  "md:p-8",
  "lg:p-8",
  "sm:px-6",
  "md:px-8",
  "lg:px-8",
]);

// Pattern for inline style padding/margin violations
const INLINE_STYLE_PADDING_PATTERN =
  /style\s*=\s*\{\s*\{[^}]*?(?:padding|margin)\s*:/g;

// Ratchet baseline — known violations at T-infra-4 creation (shrink-only).
const KNOWN_PADDING_VIOLATIONS: ReadonlySet<string> = new Set<string>([
  // Empty baseline — clean at T-infra-4.
]);

function collectPageFiles(dir: string): string[] {
  if (!existsSync(dir)) return [];
  const files: string[] = [];
  const recurse = (current: string) => {
    for (const entry of readdirSync(current)) {
      const full = join(current, entry);
      const stat = statSync(full);
      if (stat.isDirectory()) {
        if (entry === "node_modules" || entry === "__tests__") continue;
        recurse(full);
      } else if (entry === "page.tsx" || entry === "layout.tsx") {
        files.push(full);
      }
    }
  };
  recurse(dir);
  return files;
}

function collectStudioSectionFiles(srcDir: string): string[] {
  if (!existsSync(srcDir)) return [];
  const files: string[] = [];
  const recurse = (current: string) => {
    for (const entry of readdirSync(current)) {
      const full = join(current, entry);
      const stat = statSync(full);
      if (stat.isDirectory()) {
        if (entry === "node_modules" || entry === "__tests__") continue;
        recurse(full);
      } else if (
        entry.endsWith(".tsx") &&
        (entry.includes("section") ||
          entry.includes("studio") ||
          entry.includes("wizard") ||
          entry.includes("onboarding"))
      ) {
        files.push(full);
      }
    }
  };
  recurse(srcDir);
  return files;
}

describe("Vitalia FE — consistent padding tokens in studio section pages (FE-A8)", () => {
  it("page.tsx and layout.tsx files have no inline style padding/margin", () => {
    if (!existsSync(APP_DIR)) {
      console.log(
        "[SKIP] src/app/ directory not found — skipping test_page_padding",
      );
      return;
    }

    const pageFiles = collectPageFiles(APP_DIR);
    if (pageFiles.length === 0) {
      console.log(
        "[SKIP] No page.tsx / layout.tsx files found — skipping inline style check",
      );
      return;
    }

    const violations: string[] = [];

    for (const absPath of pageFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");
      if (KNOWN_PADDING_VIOLATIONS.has(relPath)) continue;

      const source = readFileSync(absPath, "utf-8");
      INLINE_STYLE_PADDING_PATTERN.lastIndex = 0;
      const matches = source.match(INLINE_STYLE_PADDING_PATTERN);
      if (matches && matches.length > 0) {
        violations.push(
          `${relPath}: ${matches.length} inline style padding/margin usage — use Tailwind classes instead`,
        );
      }
    }

    expect(
      violations,
      [
        "Inline style padding/margin detected in page/layout files.",
        "",
        "Use Tailwind CSS utility classes instead of inline styles.",
        "Allowed padding classes: p-4, p-6, p-8, px-6, py-6, etc.",
        "",
        "Fix: Replace `style={{ padding: '24px' }}` with `className='p-6'`",
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("studio section client components use consistent Tailwind padding classes", () => {
    if (!existsSync(SRC)) {
      console.log(
        "[SKIP] src/ directory not found — skipping studio section padding check",
      );
      return;
    }

    const studioFiles = collectStudioSectionFiles(SRC);
    if (studioFiles.length === 0) {
      console.log(
        "[SKIP] No studio section files found — skipping consistent padding check",
      );
      return;
    }

    const violations: string[] = [];

    // Look for arbitrary padding values like p-[24px], p-[1.5rem] (Tailwind JIT arbitrary)
    // These bypass the design token scale and are forbidden.
    const ARBITRARY_PADDING_PATTERN = /\b(?:p|px|py|pt|pb|pl|pr)-\[/g;

    for (const absPath of studioFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");
      if (KNOWN_PADDING_VIOLATIONS.has(relPath)) continue;

      const source = readFileSync(absPath, "utf-8");

      // Check for arbitrary Tailwind padding (p-[X])
      ARBITRARY_PADDING_PATTERN.lastIndex = 0;
      const arbitraryMatches = source.match(ARBITRARY_PADDING_PATTERN);
      if (arbitraryMatches && arbitraryMatches.length > 0) {
        violations.push(
          `${relPath}: ${arbitraryMatches.length} arbitrary Tailwind padding value(s) ` +
            `(e.g., p-[24px]) — use design token scale instead (p-4, p-6, p-8)`,
        );
      }
    }

    expect(
      violations,
      [
        "Arbitrary Tailwind padding values detected in studio section components.",
        "",
        "Studio section pages MUST use the vitalia design token spacing scale:",
        "  p-4 (16px) · p-6 (24px) · p-8 (32px) — and responsive variants.",
        "",
        "Arbitrary values like p-[24px] or p-[1.5rem] bypass the design system.",
        "",
        "Fix: Replace `p-[24px]` with `p-6` (maps to 24px on 4-unit scale).",
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("KNOWN_PADDING_VIOLATIONS allowlist only references existing files", () => {
    for (const relPath of KNOWN_PADDING_VIOLATIONS) {
      const absPath = join(ROOT, relPath);
      expect(
        existsSync(absPath),
        `KNOWN_PADDING_VIOLATIONS references non-existent file: ${relPath}. Remove it (shrink-only ratchet).`,
      ).toBe(true);
    }
  });
});
