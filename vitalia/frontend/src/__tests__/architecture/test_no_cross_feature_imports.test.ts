/**
 * Architecture test — FE-A4: no cross-feature imports via internal paths.
 *
 * Companion to test_fsd_boundaries.test.ts. Focuses on the PUBLIC API gate:
 * external consumers MUST import from a feature's `index.ts` (public API),
 * never from internal paths like `features/X/components/foo` directly.
 *
 * Rule: If a file outside `features/X/` imports from `@/features/X/`,
 * the import path MUST NOT go deeper than the feature root index
 * (i.e., `@/features/X` or `@/features/X/index` is OK;
 *        `@/features/X/components/foo` is FORBIDDEN).
 *
 * This enforces FSD encapsulation: internal module structure is private.
 *
 * Scope: src/ (all TS/TSX files)
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
const FEATURES_DIR = join(SRC, "features");

// Ratchet baseline — known violations at time of T-infra-4 creation (shrink-only).
const KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS: ReadonlySet<string> =
  new Set<string>([
    // T-inbox-fe-2: crm-shared/api/use-conversation-detail.ts imports inbox internal type
    // (conversation-detail.ts). crm-shared is a PRODUCER feature per 03-arch-fe.md § 1;
    // inbox/types/conversation-detail.ts has a bi-directional type dependency.
    // Justified: crm-shared ↔ inbox types are tightly coupled in Ola 1 (pipeline/agenda Ola 2+).
    "src/features/crm-shared/api/use-conversation-detail.ts",
    // T-inbox-fe-2: use-conversation-filters.ts imports ConversationsFilters type from
    // crm-shared/api/use-conversations internal path. To be refactored to use
    // crm-shared index.ts public API in T-inbox-fe-refactor.
    // ★ 2026-06-11 (auditor shell-core-hardening): path actualizado — feature `inbox`
    // renombrada a `adrian` en integración previa (e98e09a8); allowlist quedó stale.
    "src/features/adrian/hooks/use-conversation-filters.ts",
    // T-inbox-fe-3: ConversationListPanel imports useConversations from crm-shared internal path.
    // crm-shared is the SSoT producer for CRM data contracts. To be refactored to public
    // API (crm-shared index.ts) in T-inbox-fe-refactor.
    // ★ 2026-06-11: idem rename inbox→adrian.
    "src/features/adrian/components/inbox/ConversationListPanel.tsx",
    // ★ 2026-06-11 (auditor shell-core-hardening): embudo page (app layer) imports
    // `@/features/adrian/api/embudo-server` by direct path. JUSTIFIED: embudo-server is a
    // SERVER-ONLY initial-state fetch (T-FE-2 adrian-embudo) — re-exporting it from the
    // feature's public index.ts would pull server-only code into the client bundle graph
    // (the index is imported by Client Components). Direct-path import of server modules
    // from the app layer is the standard Next.js pattern for this split.
    "src/app/[tenantId]/(shell-organism)/adrian/embudo/page.tsx",
  ]);

function collectTsFiles(dir: string): string[] {
  if (!existsSync(dir)) return [];
  const files: string[] = [];
  const recurse = (current: string) => {
    for (const entry of readdirSync(current)) {
      const full = join(current, entry);
      const stat = statSync(full);
      if (stat.isDirectory()) {
        if (entry === "node_modules" || entry === "__tests__") continue;
        recurse(full);
      } else if (entry.endsWith(".ts") || entry.endsWith(".tsx")) {
        files.push(full);
      }
    }
  };
  recurse(dir);
  return files;
}

function getFeatureName(absPath: string): string | null {
  const rel = relative(FEATURES_DIR, absPath).replace(/\\/g, "/");
  const parts = rel.split("/");
  if (parts.length >= 1 && !parts[0].startsWith(".")) {
    return parts[0];
  }
  return null;
}

function isInternalFeaturePath(importPath: string): boolean {
  // Pattern: @/features/<name>/<subpath> where subpath is NOT empty/index
  const match = importPath.match(/^@\/features\/([^/]+)\/(.+)$/);
  if (!match) return false;
  const subPath = match[2];
  // Allow: @/features/X/index (explicit index reference)
  if (subPath === "index" || subPath === "index.ts" || subPath === "index.tsx")
    return false;
  // Any deeper path is an internal import
  return true;
}

function extractImportPaths(source: string): string[] {
  const imports: string[] = [];
  const importPattern =
    /(?:^|\n)\s*import\s+(?:.*?)\s+from\s+['"]([^'"]+)['"]/g;
  let match: RegExpExecArray | null;
  while ((match = importPattern.exec(source)) !== null) {
    imports.push(match[1]);
  }
  return imports;
}

describe("Vitalia FE — no cross-feature internal path imports (FE-A4)", () => {
  it("files outside a feature do not import internal feature paths", () => {
    if (!existsSync(SRC)) {
      console.log(
        "[SKIP] src/ directory not found — skipping test_no_cross_feature_imports",
      );
      return;
    }
    if (!existsSync(FEATURES_DIR)) {
      console.log(
        "[SKIP] src/features/ not found — skipping test_no_cross_feature_imports",
      );
      return;
    }

    const allFiles = collectTsFiles(SRC);
    const violations: string[] = [];

    for (const absPath of allFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");
      if (KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS.has(relPath)) continue;

      // Determine which feature (if any) this file belongs to
      const ownerFeature =
        existsSync(FEATURES_DIR) && absPath.startsWith(FEATURES_DIR)
          ? getFeatureName(absPath)
          : null;

      const source = readFileSync(absPath, "utf-8");
      const imports = extractImportPaths(source);

      for (const importPath of imports) {
        // Check for internal feature path imports
        if (!isInternalFeaturePath(importPath)) continue;

        // Extract the target feature from the import
        const targetFeatureMatch = importPath.match(/^@\/features\/([^/]+)/);
        if (!targetFeatureMatch) continue;
        const targetFeature = targetFeatureMatch[1];

        // If the importing file is INSIDE the same feature, it's allowed (intra-feature)
        if (ownerFeature === targetFeature) continue;

        violations.push(
          `${relPath}: imports internal path '${importPath}' ` +
            `(accessing feature '${targetFeature}' internals — must use index.ts public API)`,
        );
      }
    }

    expect(
      violations,
      [
        "Cross-feature internal path imports detected.",
        "",
        "External files MUST import from a feature's public API (index.ts),",
        "not from internal paths like @/features/X/components/foo.",
        "",
        "Fix: Update the import to use '@/features/X' or '@/features/X/index'",
        "     and ensure the symbol is exported via the feature's index.ts.",
        "",
        "If the internal import is genuinely required (e.g., a type shared via",
        "an internal namespace), add to KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS",
        "(shrink-only ratchet) with a justification comment.",
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS allowlist only references existing files", () => {
    for (const relPath of KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS) {
      const absPath = join(ROOT, relPath);
      expect(
        existsSync(absPath),
        `KNOWN_CROSS_FEATURE_INTERNAL_IMPORTS references non-existent file: ${relPath}. Remove it.`,
      ).toBe(true);
    }
  });
});
