/**
 * Architecture test — core-ds-foundation T-2 (A-2): raw `<div>` LAYOUT
 * containers in vitalia/frontend/src should be page-primitives (canon §2.7,
 * ADR-014). A `<div className="flex-col gap-…">` or `<div className="grid-cols-…">`
 * is layout that belongs in a primitive (Section / PageContentStack / grid).
 *
 * SHRINK-ONLY ratchet:
 *   - +1 raw layout <div> → FAILS (count > baseline).
 *   - migrate a layout <div> to a primitive → passes, then lower the baseline.
 *   - the baseline NEVER rises.
 *
 * Baseline MEASURED 2026-06-08 (T-2 seed): 301 layout <div> across 121 files.
 * These are pre-existing; the studio adoption stories ({brand}-ds-adoption)
 * migrate them to primitives. The lock only blocks NEW raw layout divs.
 *
 * Detection (parity with _ds-lock-scanner::isLayoutDiv): className contains
 * (flex-col AND gap-) OR grid-cols-. className forms: "...", {`...`}, {cn(...)}.
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers.
 */
import { describe, it, expect } from "vitest";
import { resolve, join } from "path";
import { collectSourceFiles, countLayoutDivs, read, relPosix } from "./_ds-lock-scanner";

const ROOT = resolve(__dirname, "../../..");
const SRC = join(ROOT, "src");

// ── Shrink-only baseline (MEASURED 2026-06-08 — core-ds-foundation T-2) ───────
const BASELINE_TOTAL = 301;
const BASELINE_FILES = 121;

function scan(): { total: number; files: string[] } {
  let total = 0;
  const files: string[] = [];
  for (const abs of collectSourceFiles(SRC, [".tsx"])) {
    const n = countLayoutDivs(read(abs));
    if (n > 0) {
      total += n;
      files.push(relPosix(ROOT, abs));
    }
  }
  return { total, files };
}

describe("T-2 A-2 — raw <div> layout containers ratchet (canon §2.7, shrink-only)", () => {
  const { total, files } = scan();

  it(`layout <div> count (${total}) does not exceed baseline (${BASELINE_TOTAL})`, () => {
    expect(
      total,
      [
        `New raw layout <div> detected: ${total} > baseline ${BASELINE_TOTAL}.`,
        "Design System canon §2.7: a vertical flex stack or grid is layout that",
        "should use a page-primitive (Section / PageContentStack / grid primitive)",
        "instead of a raw <div className=\"flex-col gap-…\"> / <div grid-cols-…>.",
        "Migrate to a primitive, or lower this baseline if you removed one.",
      ].join("\n"),
    ).toBeLessThanOrEqual(BASELINE_TOTAL);
  });

  it(`files with layout <div> (${files.length}) does not exceed baseline (${BASELINE_FILES})`, () => {
    expect(files.length).toBeLessThanOrEqual(BASELINE_FILES);
  });

  it("baseline is not stale-high (zero layout divs → lower baseline to 0)", () => {
    if (total === 0) {
      expect(BASELINE_TOTAL, "all layout divs migrated — set BASELINE_TOTAL to 0").toBe(0);
    } else {
      expect(BASELINE_TOTAL).toBeGreaterThan(0);
    }
  });
});
