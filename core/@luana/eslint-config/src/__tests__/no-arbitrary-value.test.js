/**
 * RuleTester unit tests for no-arbitrary-value (F-3).
 *
 * Covers:
 *   SC-1 — locked-axis arbitrary → error + token suggestion
 *          (font-size, radius, spacing, color-hex)
 *   SC-2 — sizing axis arbitrary → NO error (RN-1 allowlist)
 *   SC-4 — `// ds-lock-allow: <razón>` named escape → allowed (RN-6)
 *   + tokenized arbitraries (var()/hsl()/theme()) → NO error
 *
 * Run: `npm run test` (node --test) in core/@luana/eslint-config.
 */

import { RuleTester } from "eslint";
import rule from "../no-arbitrary-value.js";

const ruleTester = new RuleTester({
  languageOptions: { ecmaVersion: 2022, sourceType: "module" },
});

ruleTester.run("no-arbitrary-value", rule, {
  valid: [
    // SC-2 — sizing axes allowlisted (RN-1)
    { code: 'const c = "w-[200px]";' },
    { code: 'const c = "max-w-[640px]";' },
    { code: 'const c = "min-h-[3rem] h-[48px]";' },
    { code: 'const c = "size-[18px]";' },

    // tokenized arbitraries — NOT raw, already a token reference
    { code: 'const c = "text-[hsl(var(--vitalia-fg))]";' },
    { code: 'const c = "rounded-[var(--radius)]";' },
    { code: 'const c = "bg-[var(--card)]";' },
    { code: 'const c = "p-[theme(spacing.4)]";' },
    { code: 'const c = "text-[color-mix(in_oklch,_white,_black)]";' },

    // already-tokenized utilities (no arbitrary at all)
    { code: 'const c = "text-sm rounded-md p-4 text-agent-adrian bg-card";' },

    // SC-4 — named escape, same line
    {
      code: 'const c = "text-[13px]"; // ds-lock-allow: legacy badge, migrate Fase 3',
    },
    // SC-4 — named escape, previous line
    {
      code: [
        "// ds-lock-allow: third-party widget needs exact 7px",
        'const c = "rounded-[7px]";',
      ].join("\n"),
    },

    // arbitrary on a NON-locked, non-sizing axis (e.g. grid-cols) — out of scope
    { code: 'const c = "grid-cols-[1fr_2fr]";' },
    { code: 'const c = "z-[60]";' },
  ],

  invalid: [
    // SC-1 — font-size locked. Message asserts axis + actionable suggestion (AC-2).
    // (RuleTester forbids message+messageId together → assert by message regex
    //  where AC-2 coverage matters, by messageId/count elsewhere.)
    {
      code: 'const c = "text-[13px]";',
      errors: [{ message: /Arbitrary font-size value `text-\[13px\]`.*text-sm/ }],
    },
    {
      code: 'const c = "text-[1.5rem]";',
      errors: [{ messageId: "arbitrary" }],
    },
    // SC-1 — radius locked
    {
      code: 'const c = "rounded-[7px]";',
      errors: [{ message: /Arbitrary radius value `rounded-\[7px\]`.*rounded-md/ }],
    },
    {
      code: 'const c = "rounded-tl-[3px]";',
      errors: [{ message: /Arbitrary radius value/ }],
    },
    // SC-1 — spacing locked
    {
      code: 'const c = "p-[18px]";',
      errors: [{ message: /Arbitrary spacing value `p-\[18px\]`.*p-4/ }],
    },
    {
      code: 'const c = "gap-[10px] mt-[2px]";',
      errors: [{ messageId: "arbitrary" }, { messageId: "arbitrary" }],
    },
    // SC-1 — color-hex locked
    {
      code: 'const c = "text-[#635BFF]";',
      errors: [{ message: /Arbitrary color-hex value `text-\[#635BFF\]`.*text-foreground/ }],
    },
    {
      code: 'const c = "bg-[#fff] border-[#00D084]";',
      errors: [{ messageId: "arbitrary" }, { messageId: "arbitrary" }],
    },
    // variant-prefixed still locked
    {
      code: 'const c = "md:text-[13px] hover:p-[6px]";',
      errors: [{ messageId: "arbitrary" }, { messageId: "arbitrary" }],
    },
    // template literal quasi
    {
      code: "const c = `flex ${x} rounded-[5px]`;",
      errors: [{ message: /Arbitrary radius value/ }],
    },
    // a plain comment that is NOT the sanctioned `ds-lock-allow:` escape → still errors
    // (RN-6: only `// ds-lock-allow:` is honored; arbitrary prose does not exempt)
    {
      code: 'const c = "text-[13px]"; // TODO: revisit this badge size later',
      errors: [{ messageId: "arbitrary" }],
    },
  ],
});

// node --test harness: wrap so failures surface as a test result.
import { test } from "node:test";
test("no-arbitrary-value RuleTester suite passed", () => {
  // RuleTester.run throws synchronously on failure above; reaching here = pass.
});
