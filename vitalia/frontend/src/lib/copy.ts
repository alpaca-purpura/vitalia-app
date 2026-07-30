// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * copy.ts — Shared copy interpolation utility.
 *
 * Simple template interpolation for copy strings with dynamic values.
 * Avoids localization library overhead for single-locale use.
 *
 * Usage:
 *   formatCopy("Escribe tu mensaje a {patient_name}…", { patient_name: "María" })
 *   // → "Escribe tu mensaje a María…"
 *
 * downstream-regression-na: brand-local FE utility; no cross-brand consumers
 */

/**
 * Interpolates template string with provided variables.
 * Template syntax: `{key}` → replaced with `vars[key]`.
 * Unknown keys are left as-is (no error thrown).
 *
 * @param template - String with `{key}` placeholders
 * @param vars - Record of key → replacement value
 * @returns Interpolated string
 */
export function formatCopy(
  template: string,
  vars: Record<string, string>,
): string {
  return Object.entries(vars).reduce(
    (result, [key, value]) => result.replace(`{${key}}`, value),
    template,
  );
}
