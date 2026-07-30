#!/usr/bin/env node
/**
 * C2-T1: TDD probe — assert the parity gate has teeth
 *
 * Modes:
 *   --plant=export-without-story  Assert gate FAILS for vigente export without story.
 *                                 Gate must exit 1 → assert exits 0 (teeth confirmed).
 *   --plant=retiring-no-story     Assert gate PASSES for retiring/allowlisted export
 *                                 without story. Gate must exit 0 → assert exits 0 (exemption works).
 *
 * Both modes read the REAL catalog.json and plant a fake entry IN MEMORY only.
 * No writes to src/ or catalog.json.
 *
 * Used by validators:
 *   c2_parity_gate_has_teeth  (--plant=export-without-story)
 *   c2_lifecycle_exempts      (--plant=retiring-no-story)
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// ponytail: inline the check logic (same as _check_catalog_parity.mjs) — small enough
import { checkParity } from "./_check_catalog_parity.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const WS = join(__dirname, "..");
const KIT_ROOT = join(WS, "core/@luana/ui-kit");

const RETIRING_NO_STORY = ["AutosaveBadge"];

const args = process.argv.slice(2);
const plant = args.find((a) => a.startsWith("--plant="))?.split("=")[1];

if (!plant) {
  console.error("Usage: node scripts/_assert_parity_gate.mjs --plant=<mode>");
  console.error("  --plant=export-without-story");
  console.error("  --plant=retiring-no-story");
  process.exit(2);
}

// Read real catalog.json
let baseCatalog;
try {
  baseCatalog = JSON.parse(readFileSync(join(KIT_ROOT, "catalog.json"), "utf-8"));
} catch {
  console.error("FAIL: catalog.json not found — run `make ui-catalog` first");
  process.exit(1);
}

if (plant === "export-without-story") {
  // Plant a fake vigente entry with no stories — gate MUST fail
  const planted = {
    module: "./__test_plant_vigente__",
    lifecycle: "vigente",
    story_ids: [],
    titles: [],
    source_files: [],
    story_url: null,
    props_source: null,
  };
  const patchedCatalog = {
    ...baseCatalog,
    entries: [...baseCatalog.entries, planted],
    retiring_no_story_allowlist: RETIRING_NO_STORY,
  };

  const violations = checkParity(patchedCatalog);
  const gateWouldFail = violations.some((v) => v.module === "./__test_plant_vigente__");

  if (gateWouldFail) {
    console.log(
      "PASS (gate has teeth): parity gate correctly FAILS for vigente export without story",
    );
    process.exit(0);
  } else {
    console.error(
      "FAIL (gate lacks teeth): parity gate did NOT fail for vigente export without story",
    );
    console.error("  This means the gate would silently allow missing stories.");
    process.exit(1);
  }
} else if (plant === "retiring-no-story") {
  // Plant a fake retiring entry with no stories — gate must PASS (exemption)
  const fakeModuleName = "__test_plant_retiring__";
  const planted = {
    module: `./${fakeModuleName}`,
    lifecycle: "retiring",
    story_ids: [],
    titles: [],
    source_files: [],
    story_url: null,
    props_source: null,
  };
  const patchedAllowlist = [...RETIRING_NO_STORY, fakeModuleName];
  const patchedCatalog = {
    ...baseCatalog,
    entries: [...baseCatalog.entries, planted],
    retiring_no_story_allowlist: patchedAllowlist,
  };

  const violations = checkParity(patchedCatalog);
  const gateWouldFail = violations.some((v) => v.module === `./${fakeModuleName}`);

  if (!gateWouldFail) {
    console.log(
      "PASS (lifecycle exempts): retiring/allowlisted export without story correctly exempted",
    );
    process.exit(0);
  } else {
    console.error(
      "FAIL (lifecycle exempts broken): retiring export triggered parity gate — exemption not working",
    );
    process.exit(1);
  }
} else {
  console.error(`Unknown --plant value: ${plant}`);
  process.exit(2);
}
