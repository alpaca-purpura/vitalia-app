/**
 * Shared scanner for the Design System lock arch-tests (core-ds-foundation T-2).
 *
 * Parity with `@luana/eslint-config` no-arbitrary-value: the same locked-axis
 * detection (font-size / radius / spacing / color-hex), the same SIZING
 * allowlist (RN-1), the same tokenized-value bypass (var()/theme()/hsl(var(..))),
 * and the same named escape `// ds-lock-allow: <razón>` (RN-6 / SC-4).
 *
 * Used by:
 *   - test-ds-tokens-lock.test.ts          (F-3 coverage: lock reports + honors escapes)
 *   - test-ds-tokens-lock-ratchet.test.ts  (F-4: shrink-only baselines per axis)
 *   - test-no-native-select.test.ts        (A-1: native <select> shrink-only)
 *   - test-no-div-layout.test.ts           (A-2: <div> layout shrink-only)
 *
 * downstream-regression-na: brand-local arch fitness helper; no cross-brand consumers.
 */
import { readFileSync, existsSync, readdirSync, statSync } from "fs";
import { join, relative } from "path";

// ---------------------------------------------------------------------------
// Comment stripping (so arbitraries inside comments are NOT counted, and the
// `ds-lock-allow:` escape is detected on the RAW source separately).
// ---------------------------------------------------------------------------
const MULTI_LINE_COMMENT = /\/\*[\s\S]*?\*\//g;
const SINGLE_LINE_COMMENT = /\/\/.*$/gm;

export function stripComments(source: string): string {
  return source
    .replace(MULTI_LINE_COMMENT, (m) => " ".repeat(m.length))
    .replace(SINGLE_LINE_COMMENT, (m) => " ".repeat(m.length));
}

// ---------------------------------------------------------------------------
// Locked axes (mirror of no-arbitrary-value.js).
// ---------------------------------------------------------------------------
export type LockedAxis = "font-size" | "radius" | "spacing" | "color-hex";

const FONT_SIZE = new Set(["text"]);
const RADIUS_PREFIX_RE =
  /^rounded(-(t|b|l|r|tl|tr|bl|br|s|e|ss|se|es|ee))?$/;
const SPACING = new Set([
  "p", "px", "py", "pt", "pb", "pl", "pr", "ps", "pe",
  "m", "mx", "my", "mt", "mb", "ml", "mr", "ms", "me",
  "gap", "gap-x", "gap-y", "space-x", "space-y",
  "inset", "inset-x", "inset-y", "top", "bottom", "left", "right", "start", "end",
]);
const COLOR = new Set([
  "text", "bg", "border", "ring", "fill", "stroke", "from", "to", "via",
  "outline", "decoration", "shadow", "ring-offset", "divide", "accent",
  "caret", "placeholder",
]);
// RN-1 — sizing axes are NEVER locked (arbitrary px/rem allowed for layout sizing).
const SIZING = new Set(["w", "h", "min-w", "max-w", "min-h", "max-h", "size", "basis"]);

const HEX_RE = /^#[0-9a-fA-F]{3,8}$/;
const FONT_LEN_RE = /^[\d.]+(px|rem|em|pt|vw|vh|ch|ex)$/;
// A value expressed THROUGH a token is NOT a raw literal.
const TOKENIZED_RE = /var\(|theme\(|hsl\(|hsla\(|rgb\(|rgba\(|oklch\(|color-mix\(/;
// `<prefix:>*<base>-[<value>]` — variant prefixes (md:, hover:, !) allowed before base.
const ARBITRARY_TOKEN_RE = /(?:^|\s|["'`{])((?:[\w-]+:)*!?)([a-z][a-z0-9-]*?)-\[([^\]]+)\]/g;

/** Classify a single `base-[value]` arbitrary into a locked axis, or null if not locked. */
export function classifyArbitrary(base: string, value: string): LockedAxis | null {
  if (SIZING.has(base)) return null;
  if (TOKENIZED_RE.test(value)) return null;
  if (FONT_SIZE.has(base) && FONT_LEN_RE.test(value)) return "font-size";
  if (RADIUS_PREFIX_RE.test(base)) return "radius";
  if (SPACING.has(base)) return "spacing";
  if (COLOR.has(base) && HEX_RE.test(value)) return "color-hex";
  return null;
}

/** Lines carrying a `// ds-lock-allow:` escape (1-indexed). Same or previous line exempts. */
function escapedLineSet(rawSource: string): Set<number> {
  const escaped = new Set<number>();
  const lines = rawSource.split("\n");
  for (let i = 0; i < lines.length; i++) {
    if (/ds-lock-allow:/.test(lines[i])) {
      escaped.add(i + 1); // the escape line itself
      escaped.add(i + 2); // the NEXT line (escape on previous line)
    }
  }
  return escaped;
}

export interface AxisCounts {
  "font-size": number;
  radius: number;
  spacing: number;
  "color-hex": number;
}

/** Count locked-axis arbitraries in one source string, honoring escapes + comments. */
export function countLockedAxes(rawSource: string): AxisCounts {
  const counts: AxisCounts = { "font-size": 0, radius: 0, spacing: 0, "color-hex": 0 };
  const escaped = escapedLineSet(rawSource);
  const lines = stripComments(rawSource).split("\n");
  for (let i = 0; i < lines.length; i++) {
    if (escaped.has(i + 1)) continue;
    let m: RegExpExecArray | null;
    ARBITRARY_TOKEN_RE.lastIndex = 0;
    while ((m = ARBITRARY_TOKEN_RE.exec(lines[i]))) {
      const axis = classifyArbitrary(m[2], m[3]);
      if (axis) counts[axis] += 1;
    }
  }
  return counts;
}

// ---------------------------------------------------------------------------
// File walking.
// ---------------------------------------------------------------------------
const SKIP_DIRS = new Set(["__tests__", "node_modules", ".next"]);

export function collectSourceFiles(
  srcDir: string,
  extensions: string[] = [".tsx", ".ts"],
): string[] {
  if (!existsSync(srcDir)) return [];
  const out: string[] = [];
  const recurse = (current: string) => {
    for (const entry of readdirSync(current)) {
      const full = join(current, entry);
      const st = statSync(full);
      if (st.isDirectory()) {
        if (SKIP_DIRS.has(entry)) continue;
        recurse(full);
      } else if (extensions.some((ext) => entry.endsWith(ext))) {
        out.push(full);
      }
    }
  };
  recurse(srcDir);
  return out;
}

/** Relative POSIX path from a root. */
export function relPosix(root: string, abs: string): string {
  return relative(root, abs).replace(/\\/g, "/");
}

// ---------------------------------------------------------------------------
// A-2 — raw <div> used as a LAYOUT container where a page-primitive exists
// (canon §2.7). Heuristic: a `<div className=...>` whose class is a vertical
// flex stack (`flex-col` + `gap-`) or a grid (`grid-cols-`) is layout that
// should be a primitive (Section / PageContentStack / grid primitive).
// className forms supported: "...", {`...`}, {cn(...)}.
// ---------------------------------------------------------------------------
const DIV_CLASSNAME_RE =
  /<div\b[^>]*?\bclassName=(?:"([^"]*)"|\{`([^`]*)`\}|\{cn\(([\s\S]*?)\)\})/g;

/** True when a className string describes a layout container (flex-col+gap or grid-cols). */
export function isLayoutDiv(cls: string): boolean {
  if (!cls) return false;
  const hasGrid = /grid-cols-/.test(cls);
  const hasFlexColGap = /flex-col/.test(cls) && /\bgap-/.test(cls);
  return hasGrid || hasFlexColGap;
}

/** Count raw layout `<div>` containers in one source string (comments stripped). */
export function countLayoutDivs(rawSource: string): number {
  const src = stripComments(rawSource);
  let n = 0;
  let m: RegExpExecArray | null;
  DIV_CLASSNAME_RE.lastIndex = 0;
  while ((m = DIV_CLASSNAME_RE.exec(src))) {
    const cls = m[1] ?? m[2] ?? m[3] ?? "";
    if (isLayoutDiv(cls)) n += 1;
  }
  return n;
}

/** Read a file (utf-8). */
export function read(abs: string): string {
  return readFileSync(abs, "utf-8");
}
