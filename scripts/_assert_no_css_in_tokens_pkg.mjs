#!/usr/bin/env node
/**
 * C2-T2: Guard — @luana/design-tokens must NOT ship any .css file.
 *
 * Canon §6.8: design-tokens is TS-only SSoT. CSS ships from each brand's globals.css
 * (projected via @theme). Any .css file reachable from the package's exports or src/
 * is a violation: it would create a parallel source of truth.
 *
 * Exits 0 if clean, 1 on violation.
 *
 * Used by validator: c2_no_css_shipped
 */

import { readFileSync, readdirSync, statSync } from "fs";
import { resolve, join, extname } from "path";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const WS = resolve(__dirname, "..");
const PKG_DIR = join(WS, "core/@luana/design-tokens");

function walkDir(dir) {
  const results = [];
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    const stat = statSync(fullPath);
    if (stat.isDirectory()) {
      // Skip node_modules and dist
      if (entry === "node_modules" || entry === "dist" || entry === ".turbo") continue;
      results.push(...walkDir(fullPath));
    } else {
      results.push(fullPath);
    }
  }
  return results;
}

// 1. Check package.json exports — no .css in the exports map
const pkgJson = JSON.parse(readFileSync(join(PKG_DIR, "package.json"), "utf8"));
const exports = pkgJson.exports || {};
const cssExports = Object.entries(exports).filter(([, val]) =>
  typeof val === "string" && val.endsWith(".css")
);
if (cssExports.length > 0) {
  console.error("[FAIL] @luana/design-tokens exports .css files (canon §6.8 violation):");
  for (const [key, val] of cssExports) {
    console.error(`  exports["${key}"] = "${val}"`);
  }
  process.exit(1);
}

// 2. Check src/ directory — no .css files
const allFiles = walkDir(join(PKG_DIR, "src"));
const cssFiles = allFiles.filter((f) => extname(f) === ".css");
if (cssFiles.length > 0) {
  console.error("[FAIL] @luana/design-tokens/src/ contains .css files (canon §6.8 violation):");
  for (const f of cssFiles) {
    console.error(`  ${f.replace(WS + "/", "")}`);
  }
  process.exit(1);
}

// 3. Check root of package — no .css at root (e.g., generated index.css)
const rootFiles = readdirSync(PKG_DIR).filter((f) => extname(f) === ".css");
if (rootFiles.length > 0) {
  console.error("[FAIL] @luana/design-tokens root contains .css files (canon §6.8 violation):");
  for (const f of rootFiles) {
    console.error(`  core/@luana/design-tokens/${f}`);
  }
  process.exit(1);
}

console.log("[PASS] @luana/design-tokens ships no .css files — TS-only SSoT (canon §6.8 OK)");
process.exit(0);
