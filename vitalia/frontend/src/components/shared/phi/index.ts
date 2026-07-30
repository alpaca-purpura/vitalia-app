// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * phi — barrel exports for HIPAA-lite PHI protection components.
 * No default exports per FSD-Lite + arch fitness gate.
 */

export { PiiMaskedSpan } from "./PiiMaskedSpan";
export type { PiiMaskedSpanProps, PiiFieldType } from "./PiiMaskedSpan";

export { RequireRole } from "./RequireRole";
export type { RequireRoleProps, PhiRole } from "./RequireRole";

export { AuditedSection } from "./AuditedSection";
export type { AuditedSectionProps } from "./AuditedSection";
