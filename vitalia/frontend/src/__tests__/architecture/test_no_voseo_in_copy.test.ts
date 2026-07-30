/**
 * Architecture test — FE-A7: no voseo in user-facing copy (Spanish neutro LatAm).
 *
 * Per .claude/rules/spanish-text.md: all user-facing text must use tuteo
 * (Spanish neutro LatAm). Voseo forms (tenés, podés, hacés, mirá, etc.) are
 * FORBIDDEN in component/copy files.
 *
 * Scope:
 *   - src/features/vitalia/config/microcopy.ts (SSoT copy)
 *   - src/features/vitalia/components/**\/*.tsx (component JSX copy)
 *   - src/components/shared/**\/*.tsx (shared UI components with copy)
 *
 * Exception: Files with magic comment `// voseo-allowed` or
 *   `<!-- voseo-allowed -->` are exempt (for test fixtures / rule docs).
 *
 * Known-violations allowlist follows ratchet pattern (shrink-only).
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
 */
// voseo-allowed: this file contains the voseo pattern list for detection (rule doc)

import { describe, it, expect } from "vitest";
import { readFileSync, existsSync } from "fs";
import { resolve, join, relative } from "path";
import { readdirSync, statSync } from "fs";

const ROOT = resolve(__dirname, "../../..");
const SRC = join(ROOT, "src");

// Complete voseo verb list per spanish-text.md rule
// voseo-allowed: pattern list for detection — not user-facing strings
const VOSEO_PATTERNS_RAW = [
  "tenés",
  "podés",
  "hacés",
  "venís",
  "decís",
  "sabés",
  "querés",
  "mirá",
  "dejá",
  "poné",
  "usá",
  "hacé",
  "elegí",
  "seleccioná",
  "arrancá",
  "empezá",
  "agregá",
  "configurá",
  "revisá",
  "escribí",
  "guardá",
  "subí",
  "abrí",
  "volvé",
  "cambiá",
  "ofrecés",
  "cobrás",
  "ejecutás",
  "activás",
  "desactivás",
  "linkeá",
  "despublicala",
  "reactivá",
  "cancelala",
  "validá",
  "considerá",
  "formulala",
  "marcá",
  "refirís",
  "atendés",
  "integrás",
  "listá",
  "probá",
  "mostrá",
  "compartí",
  "contá",
  "explicá",
  "fijate",
  "acordate",
  "dale",
  "andá",
];

const VOSEO_REGEX = new RegExp(`\\b(${VOSEO_PATTERNS_RAW.join("|")})\\b`, "i");

// Magic comment patterns (per spanish-text.md R25)
// Supports: # voseo-allowed (Python/shell), // voseo-allowed (TypeScript/JS), <!-- voseo-allowed --> (HTML/JSX)
const VOSEO_ALLOWED_COMMENT =
  /(?:(?:#|\/\/)\s*voseo-allowed([: \t—]|$)|<!--\s*voseo-allowed[^>]*-->)/;

// Ratchet baseline — known violations at T-infra-4 creation (shrink-only).
const KNOWN_VOSEO_VIOLATIONS: ReadonlySet<string> = new Set<string>([
  // Empty baseline — clean at T-infra-4.
]);

// Files/dirs to scan for voseo
const SCAN_DIRS = [
  join(SRC, "features", "vitalia", "config"),
  join(SRC, "features", "vitalia", "components"),
  join(SRC, "components", "shared"),
];

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

function findVoseoInSource(
  source: string,
): { line: number; text: string; match: string }[] {
  const violations: { line: number; text: string; match: string }[] = [];
  const lines = source.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    // Skip comment lines
    if (
      line.trim().startsWith("//") ||
      line.trim().startsWith("*") ||
      line.trim().startsWith("/*")
    ) {
      continue;
    }
    // Skip magic comment lines
    if (VOSEO_ALLOWED_COMMENT.test(line)) continue;
    // Skip import lines (they contain file paths, not user-facing text)
    if (/^\s*import\s/.test(line)) continue;

    const match = VOSEO_REGEX.exec(line);
    if (match) {
      violations.push({
        line: i + 1,
        text: line.trim().slice(0, 100),
        match: match[1],
      });
    }
  }
  return violations;
}

describe("Vitalia FE — no voseo in user-facing copy (FE-A7)", () => {
  it("microcopy.ts and component files contain no voseo verb forms", () => {
    const allFiles: string[] = [];
    for (const dir of SCAN_DIRS) {
      allFiles.push(...collectTsFiles(dir));
    }

    if (allFiles.length === 0) {
      console.log(
        "[SKIP] No component/copy files found — skipping test_no_voseo_in_copy",
      );
      return;
    }

    const violations: string[] = [];

    for (const absPath of allFiles) {
      const relPath = relative(ROOT, absPath).replace(/\\/g, "/");
      if (KNOWN_VOSEO_VIOLATIONS.has(relPath)) continue;

      const source = readFileSync(absPath, "utf-8");

      // Check for file-level magic comment escape
      if (VOSEO_ALLOWED_COMMENT.test(source)) continue;

      const fileViolations = findVoseoInSource(source);
      if (fileViolations.length > 0) {
        const details = fileViolations
          .slice(0, 3)
          .map((v) => `  line ${v.line}: "${v.match}" in: ${v.text}`);
        violations.push(
          `${relPath}: ${fileViolations.length} voseo occurrence(s):\n${details.join("\n")}`,
        );
      }
    }

    expect(
      violations,
      [
        "Voseo verb forms detected in user-facing copy.",
        "",
        "Per .claude/rules/spanish-text.md: ALL user-facing strings must use",
        "Spanish neutro LatAm (tuteo — tú, tienes, puedes, etc.).",
        "Voseo excludes MX/CO/PE/CL/EC users (majority of LatAm audience).",
        "",
        "Common replacements:",
        "  tenés → tienes   podés → puedes   hacés → haces",
        "  mirá  → mira     guardá → guarda  configurá → configura",
        "",
        "Exception: sales_agent OUTPUT (not in scope here — that respects tenant voice).",
        "",
        "If this file is a rule/test doc with the pattern list (not user-facing),",
        "add `// voseo-allowed` comment anywhere in the file.",
        "",
        ...violations,
      ].join("\n"),
    ).toHaveLength(0);
  });

  it("KNOWN_VOSEO_VIOLATIONS allowlist only references existing files", () => {
    for (const relPath of KNOWN_VOSEO_VIOLATIONS) {
      const absPath = join(ROOT, relPath);
      expect(
        existsSync(absPath),
        `KNOWN_VOSEO_VIOLATIONS references non-existent file: ${relPath}. Remove it (shrink-only ratchet).`,
      ).toBe(true);
    }
  });
});
