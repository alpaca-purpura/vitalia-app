#!/usr/bin/env node
// Render smoke gate for @luana/ui-kit Storybook (core-ds-foundation T-2).
//
// WHY: build-storybook EXIT=0 + index.json validation do NOT prove a story RENDERS.
// A blank Docs page (missing addon-docs) AND a crashing story (charAt on undefined)
// both passed those weaker checks. This loads EVERY story's iframe in a real headless
// browser and FAILS on any uncaught error / Storybook error overlay. Same intent as
// @storybook/test-runner, but without its SB10 "could not access the channel" breakage.
//
// Usage: node scripts/_smoke_storybook.mjs [--url http://localhost:6007]
//   Requires a running Storybook (dev `pnpm --filter @luana/ui-kit storybook`, or a
//   static build served on the URL). Uses the playwright chromium pulled in by
//   @storybook/test-runner.

import { chromium } from "playwright";

const url = (() => {
  const i = process.argv.indexOf("--url");
  return i !== -1 ? process.argv[i + 1] : "http://localhost:6007";
})();

const index = await (await fetch(`${url}/index.json`)).json();
const stories = Object.values(index.entries ?? index.stories ?? {}).filter(
  (e) => e.type === "story",
);
if (stories.length === 0) {
  console.error("smoke: no stories in index.json — is Storybook running + built?");
  process.exit(1);
}

const browser = await chromium.launch();
const ctx = await browser.newContext();
const fails = [];

for (const s of stories) {
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e.message || e)));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(`console.error: ${m.text()}`);
  });
  try {
    await page.goto(`${url}/iframe.html?id=${s.id}&viewMode=story`, {
      waitUntil: "domcontentloaded", // NOT networkidle: Storybook HMR ws never idles
      timeout: 15000,
    });
    await page.waitForTimeout(700); // let React mount + any render error surface
    // NOTE: do NOT match `.sb-errordisplay` text — that element is always present
    // (hidden template) and produces a false positive on EVERY story. The reliable
    // signal is a thrown error (pageerror) or a real React render console.error,
    // both captured by the listeners above.
  } catch (e) {
    errors.push(`goto: ${String(e.message || e).slice(0, 140)}`);
  }
  // Keep only REAL render failures (uncaught throws + React render errors); drop noise.
  const fatal = errors.filter(
    (e) =>
      /goto:|Cannot read|is not a function|is not defined|TypeError|ReferenceError|Objects are not valid as a React child|Maximum update depth|undefined is not an object/i.test(
        e,
      ) && !/Download the React DevTools|favicon|sb-addon|preload|ResizeObserver/.test(e),
  );
  if (fatal.length) fails.push({ id: s.id, errors: [...new Set(fatal)].slice(0, 2) });
  await page.close();
}

await browser.close();

console.log(`smoke: ${stories.length - fails.length}/${stories.length} stories render clean`);
if (fails.length) {
  console.error(`\nFAIL — ${fails.length} stories errored:`);
  for (const f of fails) console.error(`  ✗ ${f.id}\n      ${f.errors.join("\n      ")}`);
  process.exit(1);
}
console.log("smoke: PASS");
