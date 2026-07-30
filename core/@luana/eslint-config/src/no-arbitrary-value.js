/**
 * ESLint rule: no-arbitrary-value
 *
 * canon: design-system-canon.md §0 · story-origin: core-ds-foundation (T-2)
 *
 * Locks Tailwind ARBITRARY VALUES on the four design-system axes
 * {spacing, radius, font-size, color-hex}. Forces tokenized utilities
 * (text-sm, rounded-md, p-4, text-agent-adrian) instead of one-off
 * `text-[13px]` / `rounded-[7px]` / `p-[18px]` / `text-[#635BFF]`.
 *
 * NOT flagged (intentional escape valves):
 *   - SIZING axes (w/h/min-w/max-w/min-h/max-h)-[..]  → layout dimensions,
 *     no token scale exists for them (RN-1).
 *   - TOKENIZED arbitraries: any-[var(--x)] / -[hsl(var(--x))] / -[theme(..)]
 *     → already a token reference, just expressed as arbitrary.
 *   - A class preceded by a `// ds-lock-allow: <razón>` comment on the same
 *     or previous line (RN-6) — the sanctioned, grep-able, auditable escape.
 *
 * Scans: string literals (JSX className, cn()/clsx()/cva() args, template
 * literal quasis). It does not evaluate runtime expressions.
 */

// --- Locked axis prefixes -------------------------------------------------

// font-size: text-[<len>]  (only when value is a raw length, not a color/var)
const FONT_SIZE_PREFIXES = ["text"];

// radius: rounded / rounded-{t,b,l,r,tl,tr,bl,br,s,e,ss,se,es,ee}
const RADIUS_PREFIX_RE = /^rounded(-(t|b|l|r|tl|tr|bl|br|s|e|ss|se|es|ee))?$/;

// spacing: padding / margin / gap / space
const SPACING_PREFIXES = new Set([
  "p", "px", "py", "pt", "pb", "pl", "pr", "ps", "pe",
  "m", "mx", "my", "mt", "mb", "ml", "mr", "ms", "me",
  "gap", "gap-x", "gap-y",
  "space-x", "space-y",
  "inset", "inset-x", "inset-y", "top", "right", "bottom", "left", "start", "end",
]);

// color-hex axes: bg/text/border/ring/fill/stroke/... -[#hex]
const COLOR_PREFIXES = new Set([
  "bg", "text", "border", "ring", "fill", "stroke", "from", "to", "via",
  "shadow", "outline", "decoration", "divide", "accent", "caret",
  "placeholder", "ring-offset",
]);

// SIZING (allowlisted — never flagged, RN-1)
const SIZING_PREFIXES = new Set([
  "w", "h", "min-w", "max-w", "min-h", "max-h", "size", "basis",
]);

// Token suggestion per axis (actionable message, AC-2).
const SUGGESTIONS = {
  "font-size": "use a font-size token (text-xs / text-sm / text-base / text-lg / text-xl)",
  radius: "use a radius token (rounded-sm / rounded-md / rounded-lg / rounded-xl / rounded-full)",
  spacing: "use a spacing token (p-1 / p-2 / p-4 / gap-2 / gap-4 / m-4 …)",
  "color-hex": "use a color token (text-foreground / bg-card / border-border / text-agent-adrian …)",
};

// A value is TOKENIZED (not a violation) when it references a CSS var / theme().
function isTokenizedValue(value) {
  return /var\(|theme\(|hsl\(|rgb\(|oklch\(|color-mix\(/.test(value);
}

// Raw color hex inside an arbitrary, e.g. [#635BFF] or [#fff8]
function isRawHex(value) {
  return /^#[0-9a-fA-F]{3,8}$/.test(value.trim());
}

// Raw length: 13px / 1.5rem / 0.5em / 2vh / 100% … numbers + unit (or bare number)
function isRawLength(value) {
  return /^-?[\d.]+(px|rem|em|vh|vw|vmin|vmax|ch|ex|pt|pc|%)?$/.test(value.trim());
}

// Match one Tailwind utility token of the form `prefix-[value]`
// (handles optional variants like `md:`, `hover:`, `dark:`, `!`).
const ARBITRARY_TOKEN_RE = /(?:^|\s)((?:[\w-]+:)*!?)((?:[a-z][a-z0-9-]*?))-\[([^\]]+)\]/g;

/**
 * Classify a single `prefix-[value]` occurrence.
 * @returns {null | {axis: string}} null = ok, object = violation.
 */
function classify(prefix, value) {
  // Tokenized arbitrary → never a violation (it IS a token, just inline).
  if (isTokenizedValue(value)) return null;

  // Sizing axis → allowlisted (RN-1).
  if (SIZING_PREFIXES.has(prefix)) return null;

  // color-hex axis
  if (COLOR_PREFIXES.has(prefix) && isRawHex(value)) {
    return { axis: "color-hex" };
  }

  // radius axis
  if (RADIUS_PREFIX_RE.test(prefix) && isRawLength(value)) {
    return { axis: "radius" };
  }

  // spacing axis
  if (SPACING_PREFIXES.has(prefix) && isRawLength(value)) {
    return { axis: "spacing" };
  }

  // font-size axis: text-[<raw length>] (text-[#hex] handled by color-hex above)
  if (FONT_SIZE_PREFIXES.includes(prefix) && isRawLength(value)) {
    return { axis: "font-size" };
  }

  return null;
}

/** @type {import('eslint').Rule.RuleModule} */
const rule = {
  meta: {
    type: "problem",
    docs: {
      description:
        "Lock Tailwind arbitrary values on design-system axes (spacing, radius, font-size, color-hex); force tokens.",
      recommended: true,
    },
    schema: [],
    messages: {
      arbitrary:
        "Arbitrary {{axis}} value `{{cls}}` bypasses the design system. {{suggestion}}. " +
        "If unavoidable, annotate with `// ds-lock-allow: <razón>`.",
    },
  },

  create(context) {
    const sourceCode = context.sourceCode ?? context.getSourceCode();

    // Is this node escaped by a `// ds-lock-allow:` comment on same or prev line?
    function isEscaped(node) {
      const startLine = node.loc.start.line;
      const comments = sourceCode.getAllComments();
      return comments.some((c) => {
        if (!/ds-lock-allow:/.test(c.value)) return false;
        const cLine = c.loc.end.line;
        return cLine === startLine || cLine === startLine - 1;
      });
    }

    function scan(rawText, node) {
      let m;
      ARBITRARY_TOKEN_RE.lastIndex = 0;
      while ((m = ARBITRARY_TOKEN_RE.exec(rawText)) !== null) {
        const prefix = m[2];
        const value = m[3];
        const verdict = classify(prefix, value);
        if (!verdict) continue;
        if (isEscaped(node)) continue;
        const cls = `${m[1]}${prefix}-[${value}]`;
        context.report({
          node,
          messageId: "arbitrary",
          data: {
            axis: verdict.axis,
            cls,
            suggestion: SUGGESTIONS[verdict.axis],
          },
        });
      }
    }

    return {
      Literal(node) {
        if (typeof node.value === "string") scan(node.value, node);
      },
      TemplateElement(node) {
        if (node.value && node.value.raw) scan(node.value.raw, node);
      },
    };
  },
};

export default rule;
