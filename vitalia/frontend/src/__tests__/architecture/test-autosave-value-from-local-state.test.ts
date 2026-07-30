// cap: lisa.servicios
/**
 * Architecture test — test-autosave-value-from-local-state.test.ts
 * G2-F11 vitalia-fase2-lisa-servicios — ADR-vitalia-009 §3.3
 *
 * Enforces ADR-009 §2.1 invariant:
 *   "El value de todo input editable sale del estado de edición local (RHF
 *    field.value/register), NUNCA de value={queryData.x}"
 *
 * Heuristic: scan .tsx files that import useAutosave. For each, flag any
 * editable input (<Input>, <Textarea>, <input>, <textarea>) whose `value`
 * prop root is NOT `field` or `form` (i.e., `value={someQuery.something}`).
 *
 * This catches the 80% direct-binding case (ADR-009 §3.3).
 * False-positive escape: add file to KNOWN_AUTOSAVE_VALUE_FROM_QUERY below
 * (shrink-only ratchet — removing entries is always OK; adding requires
 * justification comment).
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
 */

import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, statSync } from "fs";
import { resolve, join, relative } from "path";

const ROOT = resolve(__dirname, "../../..");

// ── Allowlist (shrink-only ratchet) ──────────────────────────────────────────
// Files that are KNOWN to bind value from query data AND have an accepted
// justification. Remove entries when fixed (never add without comment).
const KNOWN_AUTOSAVE_VALUE_FROM_QUERY: ReadonlySet<string> = new Set([
  // Example (read-only display fields that are never editable):
  // "features/lisa/components/servicios/leaves/ResumenView.tsx",
  // (empty — ResumenView.tsx is fixed by G2-F11)
]);

// ── Helpers ──────────────────────────────────────────────────────────────────

function isCommentLine(line: string): boolean {
  const trimmed = line.trimStart();
  return (
    trimmed.startsWith("*") ||
    trimmed.startsWith("//") ||
    trimmed.startsWith("/*")
  );
}

function collectTsxFiles(dir: string): string[] {
  const results: string[] = [];
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return results;
  }
  for (const entry of entries) {
    if (entry === "node_modules" || entry === "__tests__" || entry === ".next") continue;
    const full = join(dir, entry);
    let stat;
    try {
      stat = statSync(full);
    } catch {
      continue;
    }
    if (stat.isDirectory()) {
      results.push(...collectTsxFiles(full));
    } else if (entry.endsWith(".tsx")) {
      results.push(full);
    }
  }
  return results;
}

/** Returns true if the file imports useAutosave */
function importsUseAutosave(content: string): boolean {
  return /useAutosave/.test(content);
}

/**
 * Returns lines that look like an editable input with value bound to
 * a non-local-state root (i.e., not field.* or form.*).
 *
 * Pattern: value={<ident>.<member>} where <ident> is not field or form.
 * Editable elements: <Input, <Textarea, <input, <textarea
 * Only matches on lines that contain both an editable tag and a value= prop.
 *
 * This is a heuristic single-pass scan. Multi-line JSX is not parsed;
 * patterns split across lines are not caught (acceptable per ADR-009 §3.3).
 */
function findDirectBindingLines(content: string): { line: number; text: string }[] {
  const findings: { line: number; text: string }[] = [];

  // Regex: value={identifier.member} where root is NOT field or form
  // Matches: value={servicio.foo} value={data.bar} value={someVar.x}
  // Does NOT match: value={field.value} value={form.something} value={"literal"} value={undefined}
  const VALUE_PATTERN =
    /\bvalue=\{(?!field\b|form\b)([a-zA-Z_$][a-zA-Z0-9_$]*)\.([a-zA-Z0-9_$.]+)\}/;

  // Editable element pattern (open tag on same line)
  const EDITABLE_TAG_PATTERN = /<(?:Input|Textarea|input|textarea)\b/;

  const lines = content.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (isCommentLine(line)) continue;
    if (!EDITABLE_TAG_PATTERN.test(line)) continue;
    if (!VALUE_PATTERN.test(line)) continue;
    findings.push({ line: i + 1, text: line.trim() });
  }
  return findings;
}

// ── Test ──────────────────────────────────────────────────────────────────────

describe("ADR-009 §2.1 — autosave editable inputs must use RHF local state", () => {
  it("no file importing useAutosave has editable inputs with value={query.field} outside allowlist", () => {
    const allTsx = collectTsxFiles(ROOT);
    const violations: string[] = [];

    for (const filePath of allTsx) {
      let content: string;
      try {
        content = readFileSync(filePath, "utf-8");
      } catch {
        continue;
      }

      if (!importsUseAutosave(content)) continue;

      const relPath = relative(ROOT, filePath);
      if (KNOWN_AUTOSAVE_VALUE_FROM_QUERY.has(relPath)) continue;

      const directBindings = findDirectBindingLines(content);
      for (const { line, text } of directBindings) {
        violations.push(`${relPath}:${line} — ${text}`);
      }
    }

    if (violations.length > 0) {
      const msg = [
        "",
        "ADR-009 §2.1 VIOLATION — editable input bound to query data in useAutosave file.",
        "Fix: wrap in <Controller> and use value={field.value ?? ''} instead.",
        "Or add to KNOWN_AUTOSAVE_VALUE_FROM_QUERY with justification (shrink-only).",
        "",
        ...violations.map((v) => `  ${v}`),
        "",
      ].join("\n");
      expect.fail(msg);
    }

    // Allowlist shrink-only: fail if allowlist has entries not found in files
    // (they were fixed but not removed from the allowlist)
    const scannedRelPaths = new Set(
      allTsx.map((f) => relative(ROOT, f)),
    );
    for (const allowlisted of KNOWN_AUTOSAVE_VALUE_FROM_QUERY) {
      if (!scannedRelPaths.has(allowlisted)) {
        expect.fail(
          `KNOWN_AUTOSAVE_VALUE_FROM_QUERY contains "${allowlisted}" but that file no longer exists. Remove it from the allowlist (shrink-only ratchet).`,
        );
      }
    }
  });
});
