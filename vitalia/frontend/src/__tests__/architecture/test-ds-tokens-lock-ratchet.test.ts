/**
 * Architecture test — core-ds-foundation T-2 (F-4): shrink-only ratchet over the
 * four locked token axes across vitalia/frontend/src.
 *
 * The @luana/eslint-config no-arbitrary-value rule is wired into
 * eslint.config.mjs with a per-file baseline allowlist so the build does NOT
 * break (NF-2). This vitest ratchet is the ENFORCEMENT teeth (RN-2, AC-4, AC-6):
 *
 *   - +1 locked-axis arbitrary anywhere → this test FAILS (count > baseline).
 *   - −N (migrate to tokens) → still passes, then the baseline is lowered.
 *   - The baseline may only DECREASE (shrink-only). It is NEVER raised.
 *
 * Baselines were MEASURED on 2026-06-08 (core-ds-foundation T-2 seed), not
 * guessed — `_ds-lock-scanner.ts::countLockedAxes` is the same logic the eslint
 * rule applies (SIZING allowlist RN-1, tokenized bypass, ds-lock-allow escape).
 *
 * To shrink: migrate arbitraries to design tokens, re-run, lower the number here.
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers.
 */
import { describe, it, expect } from "vitest";
import { resolve, join } from "path";
import {
  collectSourceFiles,
  countLockedAxes,
  read,
  type AxisCounts,
  type LockedAxis,
} from "./_ds-lock-scanner";

const ROOT = resolve(__dirname, "../../..");
const SRC = join(ROOT, "src");

// ── Shrink-only baselines (MEASURED 2026-06-08 — core-ds-foundation T-2) ──────
// Lower these as arbitraries migrate to tokens. NEVER raise.
const BASELINE: AxisCounts = {
  "font-size": 82,
  radius: 7,
  spacing: 4,
  "color-hex": 0,
};

function totalLockedAxes(): AxisCounts {
  const totals: AxisCounts = { "font-size": 0, radius: 0, spacing: 0, "color-hex": 0 };
  for (const abs of collectSourceFiles(SRC)) {
    const c = countLockedAxes(read(abs));
    totals["font-size"] += c["font-size"];
    totals.radius += c.radius;
    totals.spacing += c.spacing;
    totals["color-hex"] += c["color-hex"];
  }
  return totals;
}

describe("T-2 F-4 — locked-axis arbitraries ratchet (shrink-only)", () => {
  const totals = totalLockedAxes();
  const axes: LockedAxis[] = ["font-size", "radius", "spacing", "color-hex"];

  for (const axis of axes) {
    it(`${axis}: count (${totals[axis]}) does not exceed baseline (${BASELINE[axis]})`, () => {
      expect(
        totals[axis],
        [
          `New arbitrary "${axis}" value(s) detected: ${totals[axis]} > baseline ${BASELINE[axis]}.`,
          "",
          "Design System canon (ADR-014) locks this axis — use a token utility:",
          "  font-size → text-xs/sm/base/lg…   radius → rounded-sm/md/lg…",
          "  spacing   → p-/m-/gap- scale       color   → bg-/text-/border- semantic tokens",
          "",
          "If genuinely unavoidable, annotate the line with",
          "  // ds-lock-allow: <razón>",
          "which the scanner honors (RN-6). Otherwise migrate to a token.",
        ].join("\n"),
      ).toBeLessThanOrEqual(BASELINE[axis]);
    });

    it(`${axis}: baseline is not stale-high (encourages shrink)`, () => {
      // If the live count has dropped well below baseline, lower the constant.
      // (Advisory guard: fails only if baseline drifted >0 above an EMPTY axis,
      //  i.e. axis fully migrated but baseline left non-zero.)
      if (totals[axis] === 0) {
        expect(
          BASELINE[axis],
          `${axis} fully migrated to tokens — lower BASELINE.${axis} to 0 (shrink-only).`,
        ).toBe(0);
      } else {
        expect(BASELINE[axis]).toBeGreaterThan(0);
      }
    });
  }
});
