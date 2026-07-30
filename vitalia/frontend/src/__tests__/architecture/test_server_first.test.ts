/**
 * Architecture test — FE-A5: Server Components first — "use client" only on leaf nodes.
 *
 * Next.js 15 App Router defaults to Server Components. Adding "use client" to a
 * component tree root causes the ENTIRE subtree to be client-side — this is
 * expensive in bundle size and kills server-side rendering benefits.
 *
 * Rule:
 *   - "use client" is REQUIRED for files that use: useState, useEffect, useCallback,
 *     useRef, useContext, useReducer, useTransition, useDeferredValue, useId,
 *     event handlers (onClick, onChange, etc. as component props), or form actions.
 *   - "use client" is FORBIDDEN for files that only use Server-safe APIs
 *     (no hooks listed above, no browser-only APIs like window/document).
 *   - "use client" should be on LEAF components only — never on a page/layout
 *     that wraps pure server-renderable content.
 *
 * This test checks the INVERSE: files that USE client hooks MUST declare "use client".
 * Missing "use client" on a hook-using file causes a runtime crash.
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

// Client-side hooks that REQUIRE "use client" directive.
const CLIENT_HOOKS = [
  "useState",
  "useEffect",
  "useCallback",
  "useRef",
  "useContext",
  "useReducer",
  "useTransition",
  "useDeferredValue",
  "useLayoutEffect",
  "useImperativeHandle",
  "useDebugValue",
  // React Query client hooks (also client-side)
  "useQueryClient",
  "useMutation",
  // Common client state patterns
  "createContext",
];

// Build a regex that matches any hook usage in source
// (method calls like `useState(...)` or `const [...] = useEffect(...)`)
const CLIENT_HOOK_PATTERN = new RegExp(
  `\\b(${CLIENT_HOOKS.join("|")})\\s*[(<]`,
  "g",
);

// Ratchet baseline — known violations at time of T-infra-4 creation (shrink-only).
// Format: "src/relative/path/to/file.tsx"
const KNOWN_MISSING_USE_CLIENT: ReadonlySet<string> = new Set<string>([
  // Empty baseline — clean at T-infra-4.
]);

// Files to skip entirely (not components, e.g. config/type files)
const SKIP_PATTERNS = [
  /\/__tests__\//,
  /\/node_modules\//,
  /\.config\.[tj]s$/,
  /\/types\//,
  /\.types\.[tj]sx?$/,
  /\/schemas\//,
  /\.schema\.[tj]sx?$/,
  /\/api\//, // API hooks (use-*.ts) use React Query which is initialized in a Provider
];

function shouldSkip(relPath: string): boolean {
  return SKIP_PATTERNS.some((p) => p.test(relPath));
}

function collectTsxFiles(dir: string): string[] {
  if (!existsSync(dir)) return [];
  const files: string[] = [];
  const recurse = (current: string) => {
    for (const entry of readdirSync(current)) {
      const full = join(current, entry);
      const stat = statSync(full);
      if (stat.isDirectory()) {
        if (entry === "node_modules") continue;
        recurse(full);
      } else if (entry.endsWith(".tsx") || entry.endsWith(".ts")) {
        files.push(full);
      }
    }
  };
  recurse(dir);
  return files;
}

describe("Vitalia FE — Server Components first; use client on hook-using files (FE-A5)", () => {
  it("files using client hooks declare 'use client'", () => {
    if (!existsSync(SRC)) {
      console.log(
        "[SKIP] src/ directory not found — skipping test_server_first",
      );
      return;
    }

    const allFiles = collectTsxFiles(SRC);
    const violations: string[] = [];

    for (const absPath of allFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");
      if (shouldSkip(relPath)) continue;
      if (KNOWN_MISSING_USE_CLIENT.has(relPath)) continue;

      const source = readFileSync(absPath, "utf-8");

      // Strip comments before scanning
      const stripped = source
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/\/\/.*$/gm, "");

      // Check if file uses any client hooks
      CLIENT_HOOK_PATTERN.lastIndex = 0;
      const usedHooks: string[] = [];
      let hookMatch: RegExpExecArray | null;
      while ((hookMatch = CLIENT_HOOK_PATTERN.exec(stripped)) !== null) {
        usedHooks.push(hookMatch[1]);
      }

      if (usedHooks.length === 0) continue; // No client hooks — server component OK

      // Verify "use client" is present. A leading comment/JSDoc block before the
      // directive is valid Next.js — so check the COMMENT-STRIPPED source's start
      // (the prior source.slice(0,500) window missed directives pushed past char 500
      // by long `// cap:` + JSDoc headers, e.g. ChannelConnectionWizard.tsx).
      const strippedStart = stripped.trimStart();
      const hasUseClient =
        strippedStart.startsWith('"use client"') ||
        strippedStart.startsWith("'use client'");

      if (!hasUseClient) {
        violations.push(
          `${relPath}: uses client hook(s) [${[...new Set(usedHooks)].join(", ")}] but missing "use client" directive`,
        );
      }
    }

    expect(
      violations,
      [
        'Files using React client hooks missing "use client" directive.',
        "",
        "Components that use useState/useEffect/useRef etc. MUST declare",
        '"use client" at the top of the file.',
        "Without it, Next.js App Router will throw a runtime error.",
        "",
        'Fix: Add `"use client";` as the FIRST line of the file.',
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("KNOWN_MISSING_USE_CLIENT allowlist only references existing files", () => {
    for (const relPath of KNOWN_MISSING_USE_CLIENT) {
      const absPath = join(ROOT, relPath);
      expect(
        existsSync(absPath),
        `KNOWN_MISSING_USE_CLIENT references non-existent file: ${relPath}. Remove it.`,
      ).toBe(true);
    }
  });
});
