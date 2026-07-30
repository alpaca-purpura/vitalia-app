/**
 * arch: skip-link target invariant (gate T-6)
 *
 * T-V2 (platform-lift-shell-chrome-ui-kit): ShellOrganismLayout.tsx deleted
 * from vitalia shell-organism (chrome lifted to @luana/ui-kit). The skip-link
 * target (#main-content + tabIndex=-1) now lives in the kit's ShellLayoutClient.tsx.
 *
 * Updated to check the kit source (same invariant, new location).
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

// T-V2: chrome lifted to @luana/ui-kit — check kit ShellLayoutClient
// __dirname = vitalia/frontend/src/__tests__/architecture
// 5× .. → workspace root (luana-vitalia/)
const LAYOUT_PATH = resolve(
  __dirname,
  "../../../../../core/@luana/ui-kit/src/organism/shell/ShellLayoutClient.tsx",
);

describe("arch: skip-link target invariant (NEW gate T-6)", () => {
  const src = readFileSync(LAYOUT_PATH, "utf-8");

  it("ShellLayoutClient (kit) contains main id='main-content'", () => {
    expect(src).toMatch(/<main[^>]*id=["']main-content["']/i);
  });

  it("main has tabIndex={-1}", () => {
    expect(src).toMatch(/tabIndex\s*=\s*\{?-1\}?/i);
  });
});
