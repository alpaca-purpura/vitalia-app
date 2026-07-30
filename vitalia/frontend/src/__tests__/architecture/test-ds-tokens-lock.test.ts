/**
 * Architecture test — core-ds-foundation T-2 (F-3 coverage):
 * the @luana/eslint-config `no-arbitrary-value` rule, loaded through the real
 * ESLint Linter, LOCKS the four token axes and honors the named escape.
 *
 * C2-T2 extension: verifies that the new VALUE modules are exported from
 * @luana/design-tokens (SHADOW, TYPOGRAPHY_SCALE, RADIUS_SCALE, SEMANTIC_COLOR_DEFAULTS).
 * These tests are GREEN after T-2. The vitalia globals.css @theme projection is T-3.
 *
 * C2-T3 extension: verifies that globals.css has @theme block projecting design-token
 * values, and that --vitalia-* status tokens alias canonical vars (alias-then-migrate).
 *
 * Covers (canon §0 — tokens-only, ADR-014):
 *   SC-1 — locked-axis arbitrary (font-size / radius / spacing / color-hex)
 *          → rule reports, with an actionable token suggestion (AC-2).
 *   SC-2 — sizing-axis arbitrary (w/h/min-w/max-w/min-h/size) → 0 reports (RN-1).
 *   SC-4 — `// ds-lock-allow: <razón>` named escape → allowed (RN-6).
 *   + tokenized arbitraries (`text-[hsl(var(--x))]`, `rounded-[var(--radius)]`) → 0.
 *   [T-2] SC-5 — new VALUE modules exported from @luana/design-tokens with correct shape.
 *   [T-3] SC-6 — globals.css @theme block projects design-token values + alias-then-migrate.
 *
 * downstream-regression-na: brand-local arch fitness test; no cross-brand consumers.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { Linter } from "eslint";
import noArbitraryValue from "@luana/eslint-config/no-arbitrary-value";
import {
  SHADOW,
  TYPOGRAPHY_SCALE,
  RADIUS_SCALE,
  SEMANTIC_COLOR_DEFAULTS,
  TYPOGRAPHY_TIERS,
} from "@luana/design-tokens";

// ── C2-T3: read globals.css once at module level for T-3 assertions ───────────
const _globalsCSS = readFileSync(
  resolve(__dirname, "../../app/globals.css"),
  "utf8"
);

const linter = new Linter();

/** Lint a snippet with ONLY the no-arbitrary-value rule = error. Returns messages. */
function lint(code: string) {
  return linter.verify(code, {
    plugins: { "@luana/ds": { rules: { "no-arbitrary-value": noArbitraryValue } } },
    rules: { "@luana/ds/no-arbitrary-value": "error" },
    languageOptions: { ecmaVersion: 2022, sourceType: "module" },
  });
}

describe("T-2 F-3 — no-arbitrary-value locks the four token axes (SC-1)", () => {
  const locked: Array<[string, string, RegExp]> = [
    ["font-size", 'const c = "text-[13px]";', /font-size.*text-sm/],
    ["radius", 'const c = "rounded-[7px]";', /radius.*rounded-md/],
    ["spacing", 'const c = "p-[18px]";', /spacing.*p-4/],
    ["color-hex", 'const c = "text-[#635BFF]";', /color-hex.*text-foreground/],
  ];

  for (const [axis, code, suggestion] of locked) {
    it(`flags a locked ${axis} arbitrary with an actionable suggestion (AC-2)`, () => {
      const msgs = lint(code);
      expect(msgs.length, `${axis}: expected exactly 1 report`).toBe(1);
      expect(msgs[0].ruleId).toBe("@luana/ds/no-arbitrary-value");
      // AC-2 — message names the axis AND suggests the nearest token utility.
      expect(msgs[0].message).toMatch(suggestion);
    });
  }

  it("flags multiple locked arbitraries in one className", () => {
    const msgs = lint('const c = "gap-[10px] rounded-[5px] text-[#fff]";');
    expect(msgs).toHaveLength(3);
  });
});

describe("T-2 F-3 — sizing axes are NOT locked (SC-2 / RN-1)", () => {
  const sizing = [
    'const c = "w-[200px]";',
    'const c = "max-w-[640px]";',
    'const c = "min-h-[3rem] h-[48px]";',
    'const c = "size-[18px]";',
  ];
  for (const code of sizing) {
    it(`sizing arbitrary scans clean: ${code}`, () => {
      expect(lint(code)).toHaveLength(0);
    });
  }
});

describe("T-2 F-3 — tokenized arbitraries are NOT raw literals", () => {
  const tokenized = [
    'const c = "text-[hsl(var(--vitalia-fg))]";',
    'const c = "rounded-[var(--radius)]";',
    'const c = "bg-[var(--card)]";',
    'const c = "p-[theme(spacing.4)]";',
  ];
  for (const code of tokenized) {
    it(`tokenized arbitrary scans clean: ${code}`, () => {
      expect(lint(code)).toHaveLength(0);
    });
  }
});

describe("T-2 F-3 — `ds-lock-allow` named escape (SC-4 / RN-6)", () => {
  it("same-line escape suppresses the report", () => {
    const code =
      'const c = "text-[13px]"; // ds-lock-allow: legacy badge, migrate Fase 3';
    expect(lint(code)).toHaveLength(0);
  });

  it("previous-line escape suppresses the report", () => {
    const code = [
      "// ds-lock-allow: third-party widget needs exact 7px",
      'const c = "rounded-[7px]";',
    ].join("\n");
    expect(lint(code)).toHaveLength(0);
  });

  it("arbitrary prose comment does NOT exempt (only ds-lock-allow is honored)", () => {
    const code = 'const c = "text-[13px]"; // TODO: revisit this badge size later';
    expect(lint(code)).toHaveLength(1);
  });
});

// ── C2-T2 extension — new VALUE modules are exported from @luana/design-tokens ──
// These tests are GREEN after T-2 creates the modules.
// The vitalia globals.css @theme projection is T-3 (not checked here).

describe("[T-2] SC-5 — SHADOW value module exported and valid", () => {
  it("SHADOW is exported, frozen, has sm/md/lg/xl", () => {
    expect(SHADOW).toBeDefined();
    expect(Object.isFrozen(SHADOW)).toBe(true);
    expect(SHADOW.sm).toBeTruthy();
    expect(SHADOW.md).toBeTruthy();
    expect(SHADOW.lg).toBeTruthy();
    expect(SHADOW.xl).toBeTruthy();
  });

  it("SHADOW.none is 'none'", () => {
    expect(SHADOW.none).toBe("none");
  });
});

describe("[T-2] SC-5 — TYPOGRAPHY_SCALE value module exported and valid", () => {
  it("TYPOGRAPHY_SCALE is exported, frozen, has size/lineHeight/weight per tier", () => {
    expect(TYPOGRAPHY_SCALE).toBeDefined();
    expect(Object.isFrozen(TYPOGRAPHY_SCALE)).toBe(true);
    for (const tier of TYPOGRAPHY_TIERS) {
      const entry = TYPOGRAPHY_SCALE[tier];
      expect(entry, `TYPOGRAPHY_SCALE.${tier} missing`).toBeDefined();
      expect(entry.size).toMatch(/rem$/);
      expect(typeof entry.lineHeight).toBe("string");
      expect(typeof entry.weight).toBe("string");
    }
  });
});

describe("[T-2] SC-5 — RADIUS_SCALE value module exported and valid", () => {
  it("RADIUS_SCALE is exported, frozen, has sm/md/lg/control", () => {
    expect(RADIUS_SCALE).toBeDefined();
    expect(Object.isFrozen(RADIUS_SCALE)).toBe(true);
    expect(RADIUS_SCALE.sm).toContain("calc");
    expect(RADIUS_SCALE.md).toBe("var(--radius)");
    expect(RADIUS_SCALE.lg).toContain("calc");
    expect(RADIUS_SCALE.control).toContain("- 2px"); // RN-7
  });
});

describe("[T-2] SC-5 — SEMANTIC_COLOR_DEFAULTS value module exported and valid", () => {
  const STATUS = ["success", "warning", "danger", "info"] as const;

  it("SEMANTIC_COLOR_DEFAULTS is exported, frozen, has all 4 status + foregrounds", () => {
    expect(SEMANTIC_COLOR_DEFAULTS).toBeDefined();
    expect(Object.isFrozen(SEMANTIC_COLOR_DEFAULTS)).toBe(true);
    for (const name of STATUS) {
      expect(SEMANTIC_COLOR_DEFAULTS[name], `${name} missing`).toBeTruthy();
      expect(SEMANTIC_COLOR_DEFAULTS[`${name}-foreground`], `${name}-foreground missing`).toBeTruthy();
    }
  });

  it("warning-foreground is dark (L < 30%) — contrast canon §2.8", () => {
    const wf = SEMANTIC_COLOR_DEFAULTS["warning-foreground"];
    const L = parseFloat(wf.split(" ")[2]);
    expect(L).toBeLessThan(30);
  });
});

// ── C2-T3 extension — vitalia globals.css @theme projection ──────────────────
// RED before globals.css is patched; GREEN after @theme block is added and
// --vitalia-* status tokens are aliased to canonical vars.

describe("[T-3] globals.css — @theme block projects design-token values", () => {
  it("has @theme { block (projection gate)", () => {
    expect(_globalsCSS).toMatch(/@theme\s*\{/);
  });

  it("preserves @source for @luana/ui-kit JIT scan (footgun guard)", () => {
    expect(_globalsCSS).toContain('@source "../../../../core/@luana/ui-kit/src"');
  });

  it("preserves dark wiring — .dark selector present", () => {
    expect(_globalsCSS).toContain(".dark");
  });

  it("preserves dark wiring — [data-theme=\"dark\"] selector present", () => {
    expect(_globalsCSS).toContain('[data-theme="dark"]');
  });

  it("@theme --shadow-none is 'none'", () => {
    expect(_globalsCSS).toContain(`--shadow-none: ${SHADOW.none}`);
  });

  it("@theme --shadow-sm matches SHADOW.sm (no-drift)", () => {
    expect(_globalsCSS).toContain(`--shadow-sm: ${SHADOW.sm}`);
  });

  it("@theme --shadow-md matches SHADOW.md (no-drift)", () => {
    expect(_globalsCSS).toContain(`--shadow-md: ${SHADOW.md}`);
  });

  it("@theme --shadow-lg matches SHADOW.lg (no-drift)", () => {
    expect(_globalsCSS).toContain(`--shadow-lg: ${SHADOW.lg}`);
  });

  it("@theme --shadow-xl matches SHADOW.xl (no-drift)", () => {
    expect(_globalsCSS).toContain(`--shadow-xl: ${SHADOW.xl}`);
  });

  it("@theme --text-display at TYPOGRAPHY_SCALE.display.size", () => {
    expect(_globalsCSS).toContain(`--text-display: ${TYPOGRAPHY_SCALE.display.size}`);
  });

  it("@theme --text-heading at TYPOGRAPHY_SCALE.heading.size", () => {
    expect(_globalsCSS).toContain(`--text-heading: ${TYPOGRAPHY_SCALE.heading.size}`);
  });

  it("@theme --text-body at TYPOGRAPHY_SCALE.body.size", () => {
    expect(_globalsCSS).toContain(`--text-body: ${TYPOGRAPHY_SCALE.body.size}`);
  });

  it("@theme --text-caption at TYPOGRAPHY_SCALE.caption.size", () => {
    expect(_globalsCSS).toContain(`--text-caption: ${TYPOGRAPHY_SCALE.caption.size}`);
  });
});

describe("[T-3] globals.css — --vitalia-* status tokens aliased (dual-system unwound)", () => {
  it("--vitalia-success aliases to var(--success) — not raw HSL (C2-T3 alias-then-migrate)", () => {
    expect(_globalsCSS).toMatch(/--vitalia-success:\s*var\(--success\)/);
  });

  it("--vitalia-warning aliases to var(--warning) — not raw HSL (C2-T3 alias-then-migrate)", () => {
    expect(_globalsCSS).toMatch(/--vitalia-warning:\s*var\(--warning\)/);
  });

  it("--vitalia-danger aliases to var(--danger) — :root --danger declared (C2-T3)", () => {
    expect(_globalsCSS).toMatch(/--vitalia-danger:\s*var\(--danger\)/);
  });

  it("--vitalia-info aliases to var(--info) — :root --info declared (C2-T3)", () => {
    expect(_globalsCSS).toMatch(/--vitalia-info:\s*var\(--info\)/);
  });

  it(":root has --danger declaration (canonical status var)", () => {
    expect(_globalsCSS).toMatch(/--danger:\s*0\s+\d+%\s+\d+%/);
  });

  it(":root has --info declaration (canonical status var)", () => {
    expect(_globalsCSS).toMatch(/--info:\s*\d+\s+\d+%\s+\d+%/);
  });
});
