/**
 * @luana/eslint-config — shared design-system ESLint rules (flat config, ESLint 9).
 *
 * canon: design-system-canon.md §0 · story-origin: core-ds-foundation (T-2)
 *
 * Provides the `no-arbitrary-value` rule that locks Tailwind arbitrary values
 * on the four DS axes {spacing, radius, font-size, color-hex}. OPT-IN per brand
 * (RN-3): a brand wires it into its own eslint.config.mjs. It is NOT auto-applied
 * to nicolify/comunify — vitalia is the T-2 pilot.
 *
 * Usage in a brand flat config:
 *
 *   import luanaDs from "@luana/eslint-config";
 *   export default [
 *     // …
 *     {
 *       files: ["src/**\/*.{ts,tsx}"],
 *       plugins: { "@luana/ds": luanaDs },
 *       rules: { "@luana/ds/no-arbitrary-value": "error" },
 *     },
 *   ];
 */

import noArbitraryValue from "./no-arbitrary-value.js";

/** @type {import('eslint').ESLint.Plugin} */
const plugin = {
  meta: {
    name: "@luana/eslint-config",
    version: "0.1.0",
  },
  rules: {
    "no-arbitrary-value": noArbitraryValue,
  },
};

export default plugin;
export { noArbitraryValue };
