#!/usr/bin/env node
/**
 * C2-T3: Guard — vitalia globals.css --vitalia-* status tokens must alias canonical vars.
 *
 * alias-then-migrate (RN-5): the legacy --vitalia-{success,warning,danger,info} tokens
 * MUST point at their canonical :root counterparts (--success/--warning/--danger/--info)
 * rather than carrying duplicate raw HSL channel values.
 *
 * Exits 0 if all checks pass, 1 on any violation.
 *
 * Usage: node scripts/_assert_legacy_tokens_unwound.mjs --brand=vitalia
 */

import { readFileSync } from "fs";
import { resolve } from "path";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const WS = resolve(__dirname, "..");

const brandArg = process.argv.find((a) => a.startsWith("--brand="));
if (!brandArg) {
  console.error("ERROR: --brand=<name> is required");
  process.exit(1);
}
const brand = brandArg.split("=")[1];

const cssPath = resolve(WS, `${brand}/frontend/src/app/globals.css`);
let css;
try {
  css = readFileSync(cssPath, "utf8");
} catch {
  console.error(`ERROR: cannot read ${cssPath}`);
  process.exit(1);
}

const checks = [
  [
    "--vitalia-success",
    /--vitalia-success:\s*var\(--success\)/,
    "must alias to var(--success) — not raw HSL",
  ],
  [
    "--vitalia-warning",
    /--vitalia-warning:\s*var\(--warning\)/,
    "must alias to var(--warning) — not raw HSL",
  ],
  [
    "--vitalia-danger",
    /--vitalia-danger:\s*var\(--danger\)/,
    "must alias to var(--danger) — not raw HSL",
  ],
  [
    "--vitalia-info",
    /--vitalia-info:\s*var\(--info\)/,
    "must alias to var(--info) — not raw HSL",
  ],
  [
    "--danger (canonical)",
    /--danger:\s*\d+\s+\d+%\s+\d+%/,
    "canonical --danger must be declared in :root",
  ],
  [
    "--info (canonical)",
    /--info:\s*\d+\s+\d+%\s+\d+%/,
    "canonical --info must be declared in :root",
  ],
];

let ok = true;
for (const [name, pattern, msg] of checks) {
  if (pattern.test(css)) {
    console.log(`PASS  ${name}`);
  } else {
    console.error(`FAIL  ${name}: ${msg}`);
    ok = false;
  }
}

if (ok) {
  console.log(`\nAll ${checks.length} legacy-token checks PASS for brand=${brand}`);
} else {
  console.error(`\nSome checks FAILED — run C2-T3 migration on ${brand}/frontend/src/app/globals.css`);
}
process.exit(ok ? 0 : 1);
