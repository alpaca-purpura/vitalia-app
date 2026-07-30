#!/usr/bin/env node
/**
 * Gate sb_when_to_use (story core-ds-foundation T-2).
 *
 * Every story in core/@luana/ui-kit/stories/ MUST carry a "## Cuándo usarlo" section in
 * its meta.parameters.docs.description.component (ticket T-2: doc obligatorio por story).
 * This is the doc Chris reads when deciding whether a component is the right tool — the
 * design system is useless without it.
 */
import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const storiesDir = join(root, "core/@luana/ui-kit/stories");

const storyFiles = readdirSync(storiesDir).filter((f) => f.endsWith(".stories.tsx"));

if (storyFiles.length === 0) {
  console.error("sb_when_to_use FAIL: no story files found");
  process.exit(1);
}

const failures = [];
for (const file of storyFiles) {
  const src = readFileSync(join(storiesDir, file), "utf8");
  if (!src.includes("## Cuándo usarlo")) {
    failures.push(`${file} missing "## Cuándo usarlo" section`);
  }
}

if (failures.length) {
  console.error("sb_when_to_use FAIL:");
  for (const f of failures) console.error("  - " + f);
  process.exit(1);
}
console.log(`sb_when_to_use PASS: ${storyFiles.length} stories carry "## Cuándo usarlo"`);
