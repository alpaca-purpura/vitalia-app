/**
 * Architecture test — F-2 (R-1SRC): globals.css has ONE source of truth per locked token.
 *
 * Before this story globals.css carried TWO --radius declarations:
 *   - Shadcn  --radius: 0.625rem  (line ~51) — KEEP
 *   - legacy  --radius: 0.5rem    (line ~151) — the CLASH, deleted by R-1SRC
 *
 * R-1SRC resolves to a single --radius and converts the legacy --vitalia-*
 * COLOR vars into ALIASES of the Shadcn tokens (e.g. --vitalia-cian: var(--primary))
 * so the ~85 existing `var(--vitalia-*)` / `.vt-*` consumers keep rendering unchanged
 * (non-breaking; migrating them is Fase 3).
 *
 * Rules asserted:
 *   1. Exactly ONE `--radius:` declaration in :root (light) — the clash is gone.
 *   2. That single --radius is 0.625rem (Shadcn kept, legacy 0.5rem deleted).
 *   3. The legacy brand COLOR vars (--vitalia-cian/purpura/amarillo/azul-marino)
 *      are aliases of Shadcn tokens (point at var(--...)), not raw `H S% L%` channels.
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { resolve } from "path";

const GLOBALS = resolve(__dirname, "../../app/globals.css");
const css = readFileSync(GLOBALS, "utf8");

/** Top-level --radius declarations (ignore --radius-lg / --radius-bubble / --radius-pill). */
function radiusBaseDeclarations(src: string): string[] {
  // match `--radius:` but NOT `--radius-...:`
  return src.match(/--radius\s*:(?![\w-])[^;]*/g) ?? [];
}

describe("R-1SRC — single --radius source of truth", () => {
  it("has exactly ONE base --radius declaration (clash resolved)", () => {
    const decls = radiusBaseDeclarations(css);
    expect(decls.length).toBe(1);
  });

  it("keeps the Shadcn 0.625rem value (legacy 0.5rem deleted)", () => {
    const decls = radiusBaseDeclarations(css);
    expect(decls[0]).toMatch(/0\.625rem/);
    expect(css).not.toMatch(/--radius\s*:(?![\w-])\s*0\.5rem/);
  });
});

describe("R-1SRC — legacy --vitalia-* brand colors alias Shadcn tokens", () => {
  // The four official brand-core colors must point at the Shadcn SSoT now.
  const aliasedVars = [
    "--vitalia-cian",
    "--vitalia-purpura",
    "--vitalia-amarillo",
    "--vitalia-azul-marino",
  ];

  for (const v of aliasedVars) {
    it(`${v} is an alias (var(--...)) not a raw HSL channel triple`, () => {
      // capture the FIRST :root declaration of this var
      const re = new RegExp(`${v}\\s*:\\s*([^;]+);`);
      const m = css.match(re);
      expect(m, `${v} declaration must exist`).not.toBeNull();
      const value = m![1].trim();
      expect(value, `${v} must alias a Shadcn token`).toMatch(/var\(--[\w-]+\)/);
      // must NOT be a raw `H S% L%` channel triple anymore
      expect(value).not.toMatch(/^\d+\s+\d+%\s+\d+%$/);
    });
  }
});

// ── DS dark-mode wiring contract (canon §2.10 · lift 2026-06-16) ─────────────
// Every @luana/ui-kit consumer must wire dark: so the kit's dark: variants honor
// the next-themes data-theme/.dark toggle (NOT @media prefers-color-scheme), and
// @source must scan the whole ui-kit/src (kit molecules outside organism/shell get
// purged silently otherwise — tsc green, visual broken). Mechanism-agnostic: the
// gate asserts the EFFECT, not the exact mechanism. vitalia uses the accepted-legacy
// @config + tailwind.config darkMode; nicolify/comunify use @custom-variant (v4-pure).
const TW_CONFIG = resolve(__dirname, "../../../tailwind.config.ts");
const twConfig = readFileSync(TW_CONFIG, "utf8");

describe("DS dark-mode wiring (canon §2.10 — kit dark: honors the theme toggle)", () => {
  it("dark variant targets [data-theme=dark]/.dark (not only prefers-color-scheme)", () => {
    // EITHER v4-pure @custom-variant in globals.css…
    const customVariant = /@custom-variant\s+dark\s*\([^)]*\[data-theme="dark"\][^)]*\)/.test(css);
    // …OR the accepted-legacy @config + tailwind.config darkMode targeting the attribute.
    const legacyConfig =
      /@config\s+"[^"]*tailwind\.config\.ts"/.test(css) && /\[data-theme="dark"\]/.test(twConfig);
    expect(
      customVariant || legacyConfig,
      "dark: won't honor the data-theme toggle — add @custom-variant dark OR @config + darkMode targeting [data-theme=dark]",
    ).toBe(true);
  });

  it("dark wiring also covers the .dark class", () => {
    const customVariant = /@custom-variant\s+dark\s*\([^)]*\.dark[^)]*\)/.test(css);
    const legacyClass = /darkMode\s*:\s*\[[^\]]*"class"/.test(twConfig);
    expect(customVariant || legacyClass, "dark wiring must also match the .dark class").toBe(true);
  });

  it('@source scans the whole @luana/ui-kit/src (not only "organism/shell")', () => {
    expect(css, "@source too narrow — kit dark:/arbitrary classes get purged silently").toMatch(
      /@source\s+"[^"]*@luana\/ui-kit\/src"\s*;/,
    );
  });
});
