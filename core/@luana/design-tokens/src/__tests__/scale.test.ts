// canon: design-system-canon.md §6.1 · story-origin: core-ds-foundation
/**
 * F-1 — @luana/design-tokens scale + NAME contract.
 * C2-T2 extension — VALUE axes: SHADOW + TYPOGRAPHY_SCALE + RADIUS_SCALE + SEMANTIC_COLOR_DEFAULTS.
 *
 * Asserts (AC-1, RN-4, RN-5, D1):
 *  - spacing scale = Tailwind 4px-base AS-IS (shared cross-brand, identical values).
 *  - radius / typography / color = shared NAME contract only (tiers/names),
 *    NOT per-brand VALUES (never merge palettes — RN-5).
 *  - all exports are frozen (Object.isFrozen) — same idiom as z-index.ts.
 *  - index barrel re-exports all (z-index preserved).
 *  - [T-2] SHADOW = shared elevation values (sm/md/lg/xl).
 *  - [T-2] TYPOGRAPHY_SCALE = shared base scale (size/lineHeight/weight per tier).
 *  - [T-2] RADIUS_SCALE = shared calc-relationship scale (sm/md/lg/control).
 *  - [T-2] SEMANTIC_COLOR_DEFAULTS = shared HSL channel values (success/warning/danger/info).
 *  - [T-2] AGENT_ACCENT_CONTRAST = contrast-family contract (canon §2.8).
 */
import { describe, it, expect } from "vitest";
import * as tokens from "../index";
import { SPACING, type SpacingKey } from "../spacing";
import { RADIUS_NAMES, RADIUS_SCALE, type RadiusName } from "../radius";
import { TYPOGRAPHY_TIERS, TYPOGRAPHY_SCALE, type TypographyTier } from "../typography";
import { COLOR_NAMES, type ColorName } from "../color-names";
import { SHADOW, type ShadowKey } from "../shadow";
import { SEMANTIC_COLOR_DEFAULTS, AGENT_ACCENT_CONTRAST } from "../color-values";

describe("@luana/design-tokens — spacing scale (RN-4, D1)", () => {
  it("exports the Tailwind 4px-base scale AS-IS", () => {
    // 4px-base ladder (rem): 0,1,2,3,4,5,6,8,10,12,16 — no invented rhythm.
    expect(SPACING["0"]).toBe("0");
    expect(SPACING["1"]).toBe(".25rem"); // 4px
    expect(SPACING["2"]).toBe(".5rem"); // 8px
    expect(SPACING["4"]).toBe("1rem"); // 16px
    expect(SPACING["6"]).toBe("1.5rem"); // 24px
    expect(SPACING["16"]).toBe("4rem"); // 64px
  });

  it("is frozen (immutable SSoT, z-index idiom)", () => {
    expect(Object.isFrozen(SPACING)).toBe(true);
  });

  it("has every key resolving to a non-empty value", () => {
    for (const k of Object.keys(SPACING) as SpacingKey[]) {
      expect(typeof SPACING[k]).toBe("string");
      expect(SPACING[k].length).toBeGreaterThan(0);
    }
  });
});

describe("@luana/design-tokens — radius NAME contract (RN-5)", () => {
  it("exports the shared tier names (sm/md/lg/bubble/pill/control), NOT per-brand values", () => {
    const expected: RadiusName[] = ["sm", "md", "lg", "bubble", "pill", "control"];
    expect([...RADIUS_NAMES]).toEqual(expected);
    // contract carries NAMES only — no hex / rem brand values leaked here.
    for (const name of RADIUS_NAMES) {
      expect(name).not.toMatch(/rem|px|#/);
    }
  });

  it("is frozen", () => {
    expect(Object.isFrozen(RADIUS_NAMES)).toBe(true);
  });
});

describe("@luana/design-tokens — typography NAME contract (RN-5)", () => {
  it("exports the shared tier names (display/heading/body/caption)", () => {
    const expected: TypographyTier[] = ["display", "heading", "body", "caption"];
    expect([...TYPOGRAPHY_TIERS]).toEqual(expected);
  });

  it("is frozen", () => {
    expect(Object.isFrozen(TYPOGRAPHY_TIERS)).toBe(true);
  });
});

describe("@luana/design-tokens — color NAME contract (RN-5)", () => {
  it("exports semantic + agent token NAMES (shared), never hex VALUES", () => {
    expect(COLOR_NAMES).toContain("primary");
    expect(COLOR_NAMES).toContain("agent-lisa");
    expect(COLOR_NAMES).toContain("danger");
    // NAMES only — no brand palette merged in (RN-5).
    for (const name of COLOR_NAMES) {
      expect(name).not.toMatch(/#|hsl|rgb|\d+%/);
    }
  });

  it("is frozen", () => {
    expect(Object.isFrozen(COLOR_NAMES)).toBe(true);
  });

  it("name list is unique (no dup tokens)", () => {
    expect(new Set(COLOR_NAMES).size).toBe(COLOR_NAMES.length);
  });
});

describe("@luana/design-tokens — index barrel", () => {
  it("re-exports the new scale + keeps z-index", () => {
    expect(tokens.SPACING).toBe(SPACING);
    expect(tokens.RADIUS_NAMES).toBe(RADIUS_NAMES);
    expect(tokens.TYPOGRAPHY_TIERS).toBe(TYPOGRAPHY_TIERS);
    expect(tokens.COLOR_NAMES).toBe(COLOR_NAMES);
    // z-index export preserved (no regression).
    expect((tokens as Record<string, unknown>).Z_INDEX).toBeDefined();
  });

  it("type names compile (ColorName narrowed)", () => {
    const c: ColorName = "primary";
    expect(c).toBe("primary");
  });

  it("[T-2] barrel re-exports SHADOW, RADIUS_SCALE, TYPOGRAPHY_SCALE, SEMANTIC_COLOR_DEFAULTS", () => {
    expect((tokens as Record<string, unknown>).SHADOW).toBeDefined();
    expect((tokens as Record<string, unknown>).RADIUS_SCALE).toBeDefined();
    expect((tokens as Record<string, unknown>).TYPOGRAPHY_SCALE).toBeDefined();
    expect((tokens as Record<string, unknown>).SEMANTIC_COLOR_DEFAULTS).toBeDefined();
  });
});

// ── C2-T2 VALUE axes ──────────────────────────────────────────────────────────

describe("[T-2] @luana/design-tokens — SHADOW elevation scale", () => {
  it("exports SHADOW with sm/md/lg/xl keys", () => {
    const expected: ShadowKey[] = ["none", "sm", "md", "lg", "xl"];
    for (const k of expected) {
      expect(SHADOW[k], `SHADOW.${k} missing`).toBeTruthy();
    }
  });

  it("values are valid CSS box-shadow strings (not empty)", () => {
    for (const [k, v] of Object.entries(SHADOW)) {
      if (k === "none") {
        expect(v).toBe("none");
      } else {
        expect(typeof v).toBe("string");
        expect((v as string).length).toBeGreaterThan(0);
        // Must look like CSS box-shadow (starts with px or 0)
        expect(v).toMatch(/^[0-9]/);
      }
    }
  });

  it("is frozen (SSoT — immutable cross-brand)", () => {
    expect(Object.isFrozen(SHADOW)).toBe(true);
  });
});

describe("[T-2] @luana/design-tokens — TYPOGRAPHY_SCALE values", () => {
  it("exports size/lineHeight/weight for every TYPOGRAPHY_TIERS entry", () => {
    for (const tier of TYPOGRAPHY_TIERS) {
      const entry = TYPOGRAPHY_SCALE[tier];
      expect(entry, `TYPOGRAPHY_SCALE.${tier} missing`).toBeDefined();
      expect(typeof entry.size, `${tier}.size should be string`).toBe("string");
      expect(entry.size, `${tier}.size should be a rem value`).toMatch(/rem$/);
      expect(typeof entry.lineHeight, `${tier}.lineHeight should be string`).toBe("string");
      expect(typeof entry.weight, `${tier}.weight should be string`).toBe("string");
    }
  });

  it("display > heading > body ≥ caption (size ordering)", () => {
    const parse = (rem: string) => parseFloat(rem);
    expect(parse(TYPOGRAPHY_SCALE.display.size)).toBeGreaterThan(
      parse(TYPOGRAPHY_SCALE.heading.size),
    );
    expect(parse(TYPOGRAPHY_SCALE.heading.size)).toBeGreaterThan(
      parse(TYPOGRAPHY_SCALE.body.size),
    );
    expect(parse(TYPOGRAPHY_SCALE.body.size)).toBeGreaterThanOrEqual(
      parse(TYPOGRAPHY_SCALE.caption.size),
    );
  });

  it("is frozen", () => {
    expect(Object.isFrozen(TYPOGRAPHY_SCALE)).toBe(true);
  });
});

describe("[T-2] @luana/design-tokens — RADIUS_SCALE relationships", () => {
  it("exports sm/md/lg/control keys", () => {
    const expected: (keyof typeof RADIUS_SCALE)[] = ["sm", "md", "lg", "control"];
    for (const k of expected) {
      expect(RADIUS_SCALE[k], `RADIUS_SCALE.${k} missing`).toBeDefined();
    }
  });

  it("sm/lg use calc() deltas relative to base --radius", () => {
    expect(RADIUS_SCALE.sm).toContain("calc");
    expect(RADIUS_SCALE.lg).toContain("calc");
  });

  it("md is var(--radius) (base passthrough)", () => {
    expect(RADIUS_SCALE.md).toBe("var(--radius)");
  });

  it("control = md-2px (RN-7 — between sm and md)", () => {
    expect(RADIUS_SCALE.control).toContain("- 2px");
  });

  it("is frozen", () => {
    expect(Object.isFrozen(RADIUS_SCALE)).toBe(true);
  });
});

describe("[T-2] @luana/design-tokens — SEMANTIC_COLOR_DEFAULTS", () => {
  const STATUS_COLORS = ["success", "warning", "danger", "info"] as const;

  it("exports HSL channels for each status color + foreground", () => {
    for (const name of STATUS_COLORS) {
      expect(
        SEMANTIC_COLOR_DEFAULTS[name],
        `SEMANTIC_COLOR_DEFAULTS.${name} missing`,
      ).toBeDefined();
      expect(
        SEMANTIC_COLOR_DEFAULTS[`${name}-foreground`],
        `SEMANTIC_COLOR_DEFAULTS.${name}-foreground missing`,
      ).toBeDefined();
    }
  });

  it("values are HSL channel format (H S% L%)", () => {
    for (const v of Object.values(SEMANTIC_COLOR_DEFAULTS)) {
      // Must be "H S% L%" OR "H S% L%" with decimals, OR just "0 0% 100%"
      expect(v).toMatch(/^\d+(\.\d+)?\s+\d+(\.\d+)?%\s+\d+(\.\d+)?%$/);
    }
  });

  it("warning-foreground is dark (L < 30%) — contrast canon §2.8", () => {
    const wf = SEMANTIC_COLOR_DEFAULTS["warning-foreground"];
    const L = parseFloat(wf.split(" ")[2]);
    expect(L, "warning-foreground must be dark (L < 30%) for contrast on amber").toBeLessThan(30);
  });

  it("is frozen", () => {
    expect(Object.isFrozen(SEMANTIC_COLOR_DEFAULTS)).toBe(true);
  });
});

describe("[T-2] @luana/design-tokens — AGENT_ACCENT_CONTRAST contract (canon §2.8)", () => {
  it("declares yellow-warm → dark-foreground", () => {
    expect(AGENT_ACCENT_CONTRAST["yellow-warm"]).toBe("dark-foreground");
  });

  it("declares dark-neutral → light-foreground", () => {
    expect(AGENT_ACCENT_CONTRAST["dark-neutral"]).toBe("light-foreground");
  });

  it("is frozen", () => {
    expect(Object.isFrozen(AGENT_ACCENT_CONTRAST)).toBe(true);
  });
});
