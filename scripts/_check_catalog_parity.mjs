#!/usr/bin/env node
/**
 * C2-T1: Catalog parity gate
 *
 * Modes:
 *   (default)        — parity check: vigente exports must have ≥1 story
 *   --mode=coverage  — coverage check: every module in index.ts has a catalog entry
 *
 * Exits 0 on PASS, 1 on FAIL.
 *
 * Used by:
 *   - Validator c2_cat_covers_exports
 *   - _assert_parity_gate.mjs (in-memory variant)
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const WS = join(__dirname, "..");
const KIT_ROOT = join(WS, "core/@luana/ui-kit");

// Keep in sync with generate_ui_catalog.mjs
const RETIRING_NO_STORY = ["AutosaveBadge"];

function parseIndexModules(content) {
  const modules = new Set();
  for (const line of content.split("\n")) {
    const m = line.match(/(?:^export[^"']*|^}\s*)from\s+["'](\.[^"']+)["']/);
    if (m) modules.add(m[1]);
  }
  return [...modules];
}

/** Core parity check logic — shared with _assert_parity_gate.mjs */
export function checkParity(catalog) {
  const { entries, retiring_no_story_allowlist = RETIRING_NO_STORY } = catalog;
  const violations = entries.filter((e) => {
    if (e.lifecycle !== "vigente") return false;
    const shortName = (e.module ?? "").replace(/^\.\//, "").split("/").pop() ?? "";
    if (retiring_no_story_allowlist.includes(shortName)) return false;
    return (e.story_ids ?? []).length === 0;
  });
  return violations;
}

/** Coverage check: every module in index.ts has a catalog entry */
export function checkCoverage(catalog, indexContent) {
  const indexModules = parseIndexModules(indexContent);
  const catalogSet = new Set((catalog.entries ?? []).map((e) => e.module));
  return indexModules.filter((m) => !catalogSet.has(m));
}

// ── CLI ───────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const mode = args.find((a) => a.startsWith("--mode="))?.split("=")[1] ?? "parity";

let catalog;
try {
  catalog = JSON.parse(readFileSync(join(KIT_ROOT, "catalog.json"), "utf-8"));
} catch {
  console.error("FAIL: catalog.json not found — run `make ui-catalog` first");
  process.exit(1);
}

if (mode === "coverage") {
  let indexContent;
  try {
    indexContent = readFileSync(join(KIT_ROOT, "src", "index.ts"), "utf-8");
  } catch {
    console.error("FAIL: could not read src/index.ts");
    process.exit(1);
  }
  const missing = checkCoverage(catalog, indexContent);
  if (missing.length > 0) {
    console.error(`FAIL (coverage): ${missing.length} modules missing from catalog:`);
    for (const m of missing) console.error(`  ${m}`);
    process.exit(1);
  }
  const total = parseIndexModules(indexContent).length;
  console.log(`PASS (coverage): ${total} modules — all covered in catalog.json`);
} else {
  const violations = checkParity(catalog);
  if (violations.length > 0) {
    console.error(`FAIL (parity): ${violations.length} vigente exports without story:`);
    for (const v of violations) console.error(`  ${v.module}`);
    process.exit(1);
  }
  const vigente = (catalog.entries ?? []).filter((e) => e.lifecycle === "vigente").length;
  console.log(`PASS (parity): ${vigente} vigente exports — all have ≥1 story`);
}
