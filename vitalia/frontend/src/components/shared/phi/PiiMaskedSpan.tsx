// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * PiiMaskedSpan — masked display of PHI field values.
 *
 * Per vitalia/.claude/rules/hipaa-lite.md:
 *   - PHI fields NEVER rendered naked in components
 *   - Masking patterns: DNI "12***5678", phone "+54 11 ***-4567", email "j***@gmail.com"
 *   - PHI data NEVER in localStorage/sessionStorage — only hash IDs
 *
 * Usage:
 *   <PiiMaskedSpan value={patient.name} fieldType="name" />
 *   <PiiMaskedSpan value={patient.dni} fieldType="dni" />
 */

import { cn } from "@/lib/cn";

export type PiiFieldType =
  | "name"
  | "dni"
  | "cuit"
  | "phone"
  | "email"
  | "address"
  | "date_of_birth"
  | "generic";

export interface PiiMaskedSpanProps {
  /** Raw PHI value to mask */
  value: string | null | undefined;
  /** PHI field type determines masking pattern */
  fieldType: PiiFieldType;
  /** Additional CSS classes */
  className?: string;
  /**
   * When false, render the raw value (still tagged `data-phi` so the FE-A6 arch
   * gate + audit tooling keep treating it as a protected field). Default `true`
   * (masked). The tenant "Máxima seguridad" config flips this per tenant — until
   * that story lands, the inbox passes `masked={false}` for leads (not patients).
   */
  masked?: boolean;
}

/**
 * Apply masking pattern per field type.
 * Design: show enough context for user to recognize record, mask sensitive middle.
 */
function maskValue(value: string, fieldType: PiiFieldType): string {
  if (!value) return "—";

  switch (fieldType) {
    case "name": {
      const parts = value.trim().split(/\s+/);
      if (parts.length === 0) return "—";
      const first = parts[0];
      const masked =
        first.slice(0, 1) + "*".repeat(Math.max(1, first.length - 1));
      return parts.length > 1
        ? `${masked} ${parts
            .slice(1)
            .map((p) => p.slice(0, 1) + "***")
            .join(" ")}`
        : masked;
    }
    case "dni":
    case "cuit": {
      // "12***5678" — show first 2 + last 4
      if (value.length <= 6) return "***";
      return value.slice(0, 2) + "***" + value.slice(-4);
    }
    case "phone": {
      // "+54 11 ***-4567" — mask middle digits
      const digits = value.replace(/\D/g, "");
      if (digits.length <= 4) return "***";
      return (
        value.slice(0, Math.max(1, value.length - 8)) +
        "***-" +
        digits.slice(-4)
      );
    }
    case "email": {
      const atIdx = value.indexOf("@");
      if (atIdx <= 0) return "***@***";
      const local = value.slice(0, atIdx);
      const domain = value.slice(atIdx);
      const maskedLocal = local.slice(0, 1) + "***";
      return maskedLocal + domain;
    }
    case "date_of_birth": {
      // "**/**/1985" — mask day/month
      const parts = value.split(/[-/]/);
      if (parts.length >= 3) {
        return `**/**/${parts[parts.length - 1]}`;
      }
      return "**/**/**";
    }
    case "address":
    case "generic":
    default: {
      if (value.length <= 4) return "***";
      return value.slice(0, 2) + "***" + value.slice(-2);
    }
  }
}

/**
 * Renders a masked PHI value for display.
 * Always shows masked form — role-based unmasking is handled at BE level.
 *
 * Color: vt-text-muted class (from globals.css semantic tokens — no hsl literals here).
 */
export function PiiMaskedSpan({
  value,
  fieldType,
  className,
  masked = true,
}: PiiMaskedSpanProps) {
  const raw = value ?? "";

  // Revealed: show the real value but keep data-phi so the gate + audit still
  // recognise this as a protected field (tenant "Máxima seguridad" off).
  if (!masked) {
    return (
      <span data-phi data-phi-type={fieldType} className={cn(className)}>
        {raw || "—"}
      </span>
    );
  }

  const maskedText = raw ? maskValue(raw, fieldType) : "—";

  return (
    <span
      data-phi
      data-phi-type={fieldType}
      className={cn("font-mono vt-text-muted tracking-wide", className)}
      aria-label={`Dato privado — ${fieldType}`}
      title="Información protegida"
    >
      {maskedText}
    </span>
  );
}
