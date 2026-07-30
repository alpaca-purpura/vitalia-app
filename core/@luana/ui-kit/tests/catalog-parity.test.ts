// cap: core.design-system.ui-kit.catalog
// C2-T1: arch-test parity 1:1 — export vigente ↔ story en storybook-static/index.json
// TDD: RED cuando catalog.json no existe (make ui-catalog genera), GREEN después.

import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeAll, describe, expect, it } from "vitest";

const __dirname = dirname(fileURLToPath(import.meta.url));
const KIT_ROOT = join(__dirname, "..");

const CATALOG_PATH = join(KIT_ROOT, "catalog.json");
const INDEX_PATH = join(KIT_ROOT, "src", "index.ts");

// Keep in sync with generate_ui_catalog.mjs
const RETIRING_NO_STORY = ["AutosaveBadge"];

interface CatalogEntry {
  module: string;
  lifecycle: "vigente" | "retiring" | "deprecated";
  story_ids: string[];
  titles: string[];
  source_files: string[];
}

interface Catalog {
  generated_at: string;
  source: string;
  storybook: string;
  retiring_no_story_allowlist: string[];
  entry_count: number;
  entries: CatalogEntry[];
}

/** Parse `export * from "..."` and `} from "..."` lines from index.ts */
function parseIndexModules(content: string): string[] {
  const modules = new Set<string>();
  for (const line of content.split("\n")) {
    // Matches: export * from "./X" OR } from "./X" (end of multi-line export blocks)
    const m = line.match(/(?:^export[^"']*|^}\s*)from\s+["'](\.[^"']+)["']/);
    if (m) modules.add(m[1]);
  }
  return [...modules];
}

describe("C2-T1: catalog parity 1:1", () => {
  let catalog: Catalog;
  let entries: CatalogEntry[];
  let indexModules: string[];

  beforeAll(() => {
    // RED state: catalog.json must exist — run `make ui-catalog` to generate
    if (!existsSync(CATALOG_PATH)) {
      throw new Error(
        "catalog.json not found. Run `make ui-catalog` to generate it.\n" +
          `Expected path: ${CATALOG_PATH}`,
      );
    }
    catalog = JSON.parse(readFileSync(CATALOG_PATH, "utf-8")) as Catalog;
    entries = catalog.entries;
    indexModules = parseIndexModules(readFileSync(INDEX_PATH, "utf-8"));
  });

  it("catalog.json has required top-level fields", () => {
    expect(catalog).toHaveProperty("generated_at");
    expect(catalog).toHaveProperty("source");
    expect(catalog).toHaveProperty("entries");
    expect(catalog).toHaveProperty("retiring_no_story_allowlist");
    expect(Array.isArray(entries)).toBe(true);
    expect(entries.length).toBeGreaterThan(0);
  });

  it("every module in src/index.ts has a catalog entry", () => {
    const catalogModuleSet = new Set(entries.map((e) => e.module));
    const missing = indexModules.filter((m) => !catalogModuleSet.has(m));
    expect(missing, `Modules missing from catalog: ${missing.join(", ")}`).toHaveLength(0);
  });

  it("no orphan entries (catalog only references modules in index.ts)", () => {
    const indexModuleSet = new Set(indexModules);
    const orphans = entries.filter((e) => !indexModuleSet.has(e.module));
    expect(orphans, `Orphan catalog entries: ${orphans.map((o) => o.module).join(", ")}`).toHaveLength(0);
  });

  it("every vigente export has ≥1 story — RETIRING_NO_STORY allowlist exempt", () => {
    const allowlist = RETIRING_NO_STORY;
    const violations = entries.filter((e) => {
      if (e.lifecycle !== "vigente") return false;
      const shortName = e.module.replace(/^\.\//, "").split("/").pop() ?? "";
      if (allowlist.includes(shortName)) return false;
      return e.story_ids.length === 0;
    });
    expect(
      violations,
      `Vigente exports without story: ${violations.map((v) => v.module).join(", ")}`,
    ).toHaveLength(0);
  });

  it("retiring/allowlisted entries are lifecycle:retiring (not vigente)", () => {
    const retiringEntries = entries.filter((e) => {
      const shortName = e.module.replace(/^\.\//, "").split("/").pop() ?? "";
      return RETIRING_NO_STORY.includes(shortName);
    });
    for (const entry of retiringEntries) {
      expect(
        entry.lifecycle,
        `${entry.module} is in RETIRING_NO_STORY but has lifecycle:${entry.lifecycle} — should be 'retiring'`,
      ).toBe("retiring");
    }
  });

  it("catalog retiring_no_story_allowlist matches RETIRING_NO_STORY constant", () => {
    expect(catalog.retiring_no_story_allowlist).toEqual(RETIRING_NO_STORY);
  });
});
