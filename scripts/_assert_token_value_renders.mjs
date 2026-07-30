#!/usr/bin/env node
/**
 * C2-T2: Guard — assert that a named token from @luana/design-tokens has a
 * non-trivial, renderable value (not undefined, null, empty string, or bare "none").
 *
 * Usage:
 *   node scripts/_assert_token_value_renders.mjs --token=SHADOW.md
 *   node scripts/_assert_token_value_renders.mjs --token=SHADOW.sm
 *   node scripts/_assert_token_value_renders.mjs --token=TYPOGRAPHY_SCALE.body.size
 *   node scripts/_assert_token_value_renders.mjs --token=SEMANTIC_COLOR_DEFAULTS.warning
 *
 * Exits 0 if the value is renderable (a non-empty string that is not "none" unless
 * the key is "none" itself), 1 on missing/trivial value.
 *
 * Token path: EXPORT.key[.subkey] — dot-separated path into the exported object.
 * The "none" sentinel is allowed only when the final key is literally "none".
 *
 * Used by validator: c2_value_change_visible
 */

import { resolve, join } from "path";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const WS = resolve(__dirname, "..");

// Parse --token=<path> arg
const tokenArg = process.argv.find((a) => a.startsWith("--token="));
if (!tokenArg) {
  console.error("[FAIL] Usage: node _assert_token_value_renders.mjs --token=EXPORT.key[.subkey]");
  process.exit(1);
}
const tokenPath = tokenArg.replace("--token=", "");
const parts = tokenPath.split(".");
if (parts.length < 2) {
  console.error(`[FAIL] Token path must be at least EXPORT.key, got: "${tokenPath}"`);
  process.exit(1);
}

const [exportName, ...keyPath] = parts;

// Dynamically import from @luana/design-tokens
const pkgIndexPath = join(WS, "core/@luana/design-tokens/src/index.ts");

// We can't directly import TS; use the individual source file that exports the constant.
// Strategy: map known exports to their source files.
const EXPORT_SOURCE_MAP = {
  SHADOW: "shadow.ts",
  TYPOGRAPHY_SCALE: "typography.ts",
  RADIUS_SCALE: "radius.ts",
  RADIUS_NAMES: "radius.ts",
  TYPOGRAPHY_TIERS: "typography.ts",
  SEMANTIC_COLOR_DEFAULTS: "color-values.ts",
  AGENT_ACCENT_CONTRAST: "color-values.ts",
  SPACING: "spacing.ts",
  Z_INDEX: "z-index.ts",
  COLOR_NAMES: "color-names.ts",
};

if (!EXPORT_SOURCE_MAP[exportName]) {
  console.error(`[FAIL] Unknown export: "${exportName}". Known: ${Object.keys(EXPORT_SOURCE_MAP).join(", ")}`);
  process.exit(1);
}

// Read the source file and extract the exported constant value with regex + eval-free parsing
import { readFileSync } from "fs";

const srcPath = join(WS, "core/@luana/design-tokens/src", EXPORT_SOURCE_MAP[exportName]);
const src = readFileSync(srcPath, "utf8");

// Find the export const block for the given export name
// Strategy: extract the object literal between `Object.freeze({` and `} as const)`
// then parse it as JSON after light normalization.

const blockRegex = new RegExp(
  `export\\s+const\\s+${exportName}\\s*=\\s*Object\\.freeze\\(\\{([\\s\\S]*?)\\}\\s*as\\s+const\\)`,
  "m"
);
const blockMatch = src.match(blockRegex);
if (!blockMatch) {
  console.error(`[FAIL] Could not locate "export const ${exportName} = Object.freeze({...})" in ${EXPORT_SOURCE_MAP[exportName]}`);
  process.exit(1);
}

// Parse the object literal using Function constructor (safe: no user input, read from repo source)
let exportedObj;
try {
  // eslint-disable-next-line no-new-func
  exportedObj = new Function(`return Object.freeze({${blockMatch[1]}})`)();
} catch (e) {
  console.error(`[FAIL] Could not parse ${exportName} object literal: ${e.message}`);
  process.exit(1);
}

// Walk keyPath into the object
let current = exportedObj;
for (const key of keyPath) {
  if (current == null || typeof current !== "object") {
    console.error(`[FAIL] Path "${tokenPath}": "${key}" not accessible (parent is ${JSON.stringify(current)})`);
    process.exit(1);
  }
  if (!(key in current)) {
    console.error(`[FAIL] Path "${tokenPath}": key "${key}" not found in ${JSON.stringify(Object.keys(current))}`);
    process.exit(1);
  }
  current = current[key];
}

const value = current;
const finalKey = keyPath[keyPath.length - 1];

if (value == null || value === "") {
  console.error(`[FAIL] ${tokenPath} = ${JSON.stringify(value)} — null/empty is not renderable`);
  process.exit(1);
}

if (typeof value !== "string") {
  console.error(`[FAIL] ${tokenPath} = ${JSON.stringify(value)} — expected string, got ${typeof value}`);
  process.exit(1);
}

// "none" is a valid CSS value only when the key is literally "none"
if (value === "none" && finalKey !== "none") {
  console.error(`[FAIL] ${tokenPath} = "none" but key is "${finalKey}" — unexpected sentinel`);
  process.exit(1);
}

console.log(`[PASS] ${tokenPath} = "${value}" — renderable (non-trivial string)`);
process.exit(0);
