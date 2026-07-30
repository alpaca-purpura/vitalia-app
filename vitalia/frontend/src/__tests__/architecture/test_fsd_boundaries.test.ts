/**
 * Architecture test — FE-A3: FSD-Lite boundary matrix enforcement.
 *
 * Per .claude/rules/frontend-fsd.md boundary matrix:
 *
 *   | From        | To: feature | feature:own | shared | ui | lib | util | hooks |
 *   |-------------|-------------|-------------|--------|----|-----|------|-------|
 *   | feature     | FORBIDDEN   | own only    | OK     | — | OK  | OK   | —     |
 *   | app         | OK          | OK          | OK     | OK | OK  | —    | OK    |
 *   | shared      | OK (*)      | OK (*)      | OK     | OK | OK  | OK   | —     |
 *   | lib         | —           | —           | —      | —  | —   | OK   | —     |
 *
 * (*) shared → feature:own is allowed for sidebar/tenant-switcher.
 *
 * Key rule: `features/X` CANNOT import from `features/Y` (different feature).
 * Components/hooks within a feature can only import from their OWN feature.
 *
 * This test scans import statements in src/features/vitalia/**\/*.ts(x) and
 * flags any import from another feature (cross-feature import).
 *
 * Note: since vitalia has a SINGLE feature (`vitalia`), this test currently
 * validates intra-feature sanity. When additional features are added
 * (e.g., `growth`, `crm`), this gate prevents cross-feature leakage.
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
const FEATURES_DIR = join(ROOT, "src", "features");

// Ratchet baseline — known violations at time of T-infra-4 creation (shrink-only).
const KNOWN_FSD_BOUNDARY_VIOLATIONS: ReadonlySet<string> = new Set<string>([
  // crm-shared is a PRODUCER feature (cross-story shared CRM contracts, Ola 1+):
  // Conversation/Lead types + useConversations/useConversationDetail hooks.
  // Intentional exception per 03-arch-fe.md § 1 (crm-shared ← adrian, pipeline, agenda).
  // Justified: crm-shared is infrastructure-like SSoT PRODUCER, never a downstream consumer.
  //
  // ★ 2026-06-11 (auditor shell-core-hardening, Carril R): the `inbox` feature was RENAMED
  // to `adrian` in a previous integration (e98e09a8) but this allowlist kept the old paths
  // → ratchet broke with 14 stale entries + 14 unlisted real files. Same justified
  // exception, real paths updated (rename, not new violations — net count unchanged).
  "src/features/crm-shared/api/use-conversation-detail.ts",
  "src/features/adrian/api/use-pause-adrian.ts",
  "src/features/adrian/api/use-proactive-outbound.ts",
  "src/features/adrian/api/use-set-mode.ts",
  "src/features/adrian/components/inbox/AdrianInboxView.tsx",
  "src/features/adrian/components/inbox/ComposerArea.tsx",
  "src/features/adrian/components/inbox/ConversationItem.test.tsx",
  "src/features/adrian/components/inbox/ConversationItem.tsx",
  "src/features/adrian/components/inbox/ConversationListPanel.tsx",
  "src/features/adrian/components/inbox/InboxConvList.tsx",
  "src/features/adrian/components/inbox/InboxPageClient.tsx",
  "src/features/adrian/components/inbox/InboxThread.tsx",
  "src/features/adrian/hooks/use-conversation-filters.ts",
  "src/features/adrian/hooks/use-mode-toggle.ts",
  "src/features/adrian/types/inbox.types.ts",
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

// Extract import paths from a TypeScript/TSX file.
function extractImportPaths(source: string): string[] {
  const imports: string[] = [];
  // Match: import ... from "..."  or  import ... from '...'
  const importPattern =
    /(?:^|\n)\s*import\s+(?:.*?)\s+from\s+['"]([^'"]+)['"]/g;
  let match: RegExpExecArray | null;
  while ((match = importPattern.exec(source)) !== null) {
    imports.push(match[1]);
  }
  // Also match: import("...") dynamic imports
  const dynamicPattern = /import\(['"]([^'"]+)['"]\)/g;
  while ((match = dynamicPattern.exec(source)) !== null) {
    imports.push(match[1]);
  }
  return imports;
}

describe("Vitalia FE — FSD boundary matrix (FE-A3)", () => {
  it("feature files do not import from a different feature folder", () => {
    if (!existsSync(FEATURES_DIR)) {
      console.log(
        "[SKIP] src/features/ directory not found — skipping test_fsd_boundaries",
      );
      return;
    }

    const featureDirs = readdirSync(FEATURES_DIR).filter((name) => {
      const full = join(FEATURES_DIR, name);
      return statSync(full).isDirectory();
    });

    if (featureDirs.length === 0) {
      console.log(
        "[SKIP] No feature directories found — skipping test_fsd_boundaries",
      );
      return;
    }

    const violations: string[] = [];

    for (const featureA of featureDirs) {
      const featureADir = join(FEATURES_DIR, featureA);
      const sourceFiles = collectTsFiles(featureADir);

      for (const absPath of sourceFiles) {
        const relPath = relative(ROOT, absPath).replace(/\\/g, "/");
        if (KNOWN_FSD_BOUNDARY_VIOLATIONS.has(relPath)) continue;

        const source = readFileSync(absPath, "utf-8");
        const imports = extractImportPaths(source);

        for (const importPath of imports) {
          // Check if the import targets a DIFFERENT feature via @/features/...
          // Pattern: @/features/<featureB>/... where featureB !== featureA
          const featureImportMatch = importPath.match(/^@\/features\/([^/]+)/);
          if (!featureImportMatch) continue;

          const featureB = featureImportMatch[1];
          if (featureB !== featureA) {
            violations.push(
              `${relPath}: imports from different feature '@/features/${featureB}' ` +
                `(violation: features/${featureA} → features/${featureB})`,
            );
          }
        }
      }
    }

    expect(
      violations,
      [
        "FSD boundary violation: cross-feature imports detected.",
        "",
        "Per .claude/rules/frontend-fsd.md: feature files CANNOT import",
        "from a different feature folder.",
        "",
        "Fix options:",
        "  1. Move shared code to src/components/shared/ or src/lib/",
        "  2. Expose via the feature's own index.ts (if it's an internal dep)",
        "",
        "If the import is justified (e.g., sidebar consuming tenant-switcher),",
        "add to KNOWN_FSD_BOUNDARY_VIOLATIONS (shrink-only ratchet).",
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("feature index.ts files exist as public API gates", () => {
    if (!existsSync(FEATURES_DIR)) {
      console.log(
        "[SKIP] src/features/ directory not found — skipping FSD index check",
      );
      return;
    }

    const featureDirs = readdirSync(FEATURES_DIR).filter((name) => {
      const full = join(FEATURES_DIR, name);
      return statSync(full).isDirectory();
    });

    const missingIndexFiles: string[] = [];
    for (const featureName of featureDirs) {
      const indexPath = join(FEATURES_DIR, featureName, "index.ts");
      if (!existsSync(indexPath)) {
        missingIndexFiles.push(`src/features/${featureName}/index.ts`);
      }
    }

    expect(
      missingIndexFiles,
      [
        "Feature folders without index.ts (public API gate) detected.",
        "",
        "Every feature must expose its public API via index.ts.",
        "Per FSD: consumers import from the index, not from internal paths.",
        "",
        "Fix: Create index.ts that re-exports public components/hooks/types.",
        "",
        ...missingIndexFiles,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("KNOWN_FSD_BOUNDARY_VIOLATIONS allowlist only references existing files", () => {
    for (const relPath of KNOWN_FSD_BOUNDARY_VIOLATIONS) {
      const absPath = join(ROOT, relPath);
      expect(
        existsSync(absPath),
        `KNOWN_FSD_BOUNDARY_VIOLATIONS references non-existent file: ${relPath}. Remove it.`,
      ).toBe(true);
    }
  });
});
