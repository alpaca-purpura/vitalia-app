#!/usr/bin/env node
/**
 * C2-T1: UI-kit catalog generator
 * Crosses 3 sources → catalog.json (GITIGNORED, machine) + catalog.md (human)
 *
 * Source A: core/@luana/ui-kit/src/index.ts  (~54 export-from modules)
 * Source B: react-docgen-typescript config mirror (ponytail: props_source path ref, no full embed)
 * Source C: storybook-static/index.json       (story IDs + lifecycle tags)
 *
 * Usage: node scripts/generate_ui_catalog.mjs
 *        make ui-catalog
 */

import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const WS = join(__dirname, "..");
const KIT_ROOT = join(WS, "core/@luana/ui-kit");
const INDEX_PATH = join(KIT_ROOT, "src/index.ts");
const SB_INDEX_PATH = join(KIT_ROOT, "storybook-static/index.json");

// ponytail: shrink-only allowlist (AutosaveBadge seeds it per canon §2.6)
const RETIRING_NO_STORY = ["AutosaveBadge"];

const LAYER_ORDER = ["Atoms", "Molecules", "Organisms", "Shell", "Templates", "Foundations"];

// ── Source A: parse index.ts ──────────────────────────────────────────────────
/**
 * Extract all unique source module paths from index.ts.
 * Captures both:
 *   export * from "./X"         (single-line re-export)
 *   export { A, B } from "./X"  (named, possibly multi-line → } from "./X")
 *   export type { T } from "./X"
 */
function parseIndexModules(content) {
  const modules = new Set();
  for (const line of content.split("\n")) {
    const m = line.match(/(?:^export[^"']*|^}\s*)from\s+["'](\.[^"']+)["']/);
    if (m) modules.add(m[1]);
  }
  return [...modules];
}

// ── Source C: storybook-static/index.json ────────────────────────────────────
const sbRaw = JSON.parse(readFileSync(SB_INDEX_PATH, "utf-8"));
const sbEntries = sbRaw.entries;

// componentPath → [{id, title, tags}]  (stories only, not docs)
const cpToStories = new Map();
for (const [id, entry] of Object.entries(sbEntries)) {
  if (entry.type !== "story" || !entry.componentPath) continue;
  const cp = entry.componentPath;
  if (!cpToStories.has(cp)) cpToStories.set(cp, []);
  cpToStories.get(cp).push({ id, title: entry.title, tags: entry.tags ?? [] });
}

// ── Module → stories matching ────────────────────────────────────────────────
function getStoriesForModule(mod) {
  // Shell barrel: storybook sets componentPath to ./src/index.ts for all shell stories
  if (mod === "./organism/shell") {
    return cpToStories.get("./src/index.ts") ?? [];
  }

  const rel = mod.replace(/^\.\//, "");

  // Single file: ./src/{rel}.tsx or ./src/{rel}.ts
  for (const ext of [".tsx", ".ts"]) {
    const cp = `./src/${rel}${ext}`;
    if (cpToStories.has(cp)) return cpToStories.get(cp);
  }

  // Directory: collect all componentPaths under ./src/{rel}/
  const prefix = `./src/${rel}/`;
  const all = [];
  for (const [cp, stories] of cpToStories.entries()) {
    if (cp.startsWith(prefix)) all.push(...stories);
  }
  return all;
}

// ── Source files resolution (for props_source ref) ───────────────────────────
function resolveSourceFiles(mod) {
  const rel = mod.replace(/^\.\//, "");

  // Single file
  for (const ext of [".tsx", ".ts"]) {
    if (existsSync(join(KIT_ROOT, "src", rel + ext))) {
      return [`./src/${rel}${ext}`];
    }
  }

  // Directory — list .tsx/.ts files (excl. barrel index + story files)
  const dir = join(KIT_ROOT, "src", rel);
  if (existsSync(dir) && statSync(dir).isDirectory()) {
    return readdirSync(dir)
      .filter(
        (f) =>
          (f.endsWith(".tsx") || f.endsWith(".ts")) &&
          !f.includes(".stories.") &&
          f !== "index.ts" &&
          !f.startsWith("_"),
      )
      .sort()
      .map((f) => `./src/${rel}/${f}`);
  }

  return [];
}

// ── Build entries ─────────────────────────────────────────────────────────────
const indexContent = readFileSync(INDEX_PATH, "utf-8");
const modules = parseIndexModules(indexContent);

const entries = modules.map((mod) => {
  const shortName = mod.replace(/^\.\//, "").split("/").pop() ?? mod;
  const isAllowlisted = RETIRING_NO_STORY.includes(shortName);
  const sourceFiles = resolveSourceFiles(mod);
  const stories = isAllowlisted ? [] : getStoriesForModule(mod);

  const titles = [...new Set(stories.map((s) => s.title))];
  const storyIds = stories.map((s) => s.id);
  const allTags = stories.flatMap((s) => s.tags);

  // Derive lifecycle: allowlist > story tags > default vigente
  const lifecycle = isAllowlisted
    ? "retiring"
    : allTags.includes("deprecated")
      ? "deprecated"
      : "vigente";

  // Derive layer from first story title (e.g. "Molecules/Accordion" → "Molecules")
  const firstTitle = titles[0] ?? null;
  const layer = firstTitle ? firstTitle.split("/")[0] : null;

  // Representative story URL (first story in storybook order)
  const firstId = storyIds[0] ?? null;

  return {
    module: mod,
    source_files: sourceFiles,
    lifecycle,
    layer,
    titles,
    story_ids: storyIds,
    story_url: firstId ? `iframe.html?id=${firstId}&viewMode=story` : null,
    // ponytail: props_source = path ref only; full props live in Storybook autodocs (no dup)
    props_source: sourceFiles[0] ?? null,
  };
});

// ── Emit catalog.json ─────────────────────────────────────────────────────────
const catalogJson = {
  generated_at: new Date().toISOString(),
  source: "core/@luana/ui-kit/src/index.ts",
  storybook: "core/@luana/ui-kit/storybook-static/index.json",
  retiring_no_story_allowlist: RETIRING_NO_STORY,
  entry_count: entries.length,
  entries,
};

const CATALOG_JSON = join(KIT_ROOT, "catalog.json");
writeFileSync(CATALOG_JSON, JSON.stringify(catalogJson, null, 2));
console.log(`✓ catalog.json — ${entries.length} entries → ${CATALOG_JSON}`);

// ── Emit catalog.md ───────────────────────────────────────────────────────────
const byLayer = {};
for (const e of entries) {
  const l = e.layer ?? "Uncategorized";
  if (!byLayer[l]) byLayer[l] = [];
  byLayer[l].push(e);
}

const layerKeys = [
  ...LAYER_ORDER.filter((l) => byLayer[l]),
  ...Object.keys(byLayer).filter((l) => !LAYER_ORDER.includes(l)),
];

let md = `# @luana/ui-kit — Catálogo de componentes\n\n`;
md += `> Auto-generado ${new Date().toISOString()} · fuente: \`src/index.ts\` + \`storybook-static/index.json\`\n`;
md += `> Regenerar: \`make ui-catalog\`\n\n`;
md += `**${entries.length} módulos exportados** (${entries.filter((e) => e.lifecycle === "vigente").length} vigentes · ${RETIRING_NO_STORY.length} retiring)\n\n`;

for (const layer of layerKeys) {
  md += `## ${layer}\n\n`;
  const layerEntries = (byLayer[layer] ?? []).sort((a, b) =>
    a.module.localeCompare(b.module),
  );
  for (const e of layerEntries) {
    const tag = e.lifecycle !== "vigente" ? ` \`${e.lifecycle}\`` : "";
    md += `### \`${e.module}\`${tag}\n`;
    if (e.titles.length > 0) {
      const links = e.story_url
        ? e.titles.map((t) => `\`${t}\``).join(", ") + ` · [Storybook](${e.story_url})`
        : e.titles.map((t) => `\`${t}\``).join(", ");
      md += `- Stories: ${links}\n`;
    } else {
      const reason =
        e.lifecycle === "retiring" ? "retiring · exento per canon §2.6 + RETIRING_NO_STORY" : "sin story";
      md += `- ${reason}\n`;
    }
    if (e.props_source) md += `- Props: \`${e.props_source}\`\n`;
    md += "\n";
  }
}

const CATALOG_MD = join(KIT_ROOT, "catalog.md");
writeFileSync(CATALOG_MD, md);
console.log(`✓ catalog.md — ${layerKeys.length} capas → ${CATALOG_MD}`);
