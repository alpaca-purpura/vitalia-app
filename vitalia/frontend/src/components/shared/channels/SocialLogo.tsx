// cap: __shared__
// story-origin: vitalia-fase2-adrian-inbox
/**
 * SocialLogo.tsx — renders the REAL brand logo of a social network in its brand
 * color (UI-AUDIT-2 #3). Consumes the `social-channels.ts` SSoT.
 *
 *   <SocialLogo channel="whatsapp" size={16} />   → green WhatsApp mark
 *   <SocialLogo channel="instagram" />            → Instagram camera
 *   <SocialLogo channel="email" />                → neutral lucide envelope (generic)
 *
 * Server Component by default (no state). Accessible: role=img + label.
 *
 * downstream-regression-na: brand-local component; no cross-brand consumers
 */

import { Mail, Globe, Phone, MapPin } from "lucide-react";
import type { LucideProps } from "lucide-react";
import { getSocialChannel } from "@/lib/channels/social-channels";

const LUCIDE_FALLBACK: Record<string, React.ComponentType<LucideProps>> = {
  Mail,
  Globe,
  Phone,
  MapPin,
};

export interface SocialLogoProps {
  /** Channel slug — e.g. "whatsapp", "instagram", "telegram". */
  channel: string;
  /** Pixel size (square). Default 16. */
  size?: number;
  /** When false, renders in currentColor instead of the brand color. */
  colored?: boolean;
  className?: string;
  /** Override the accessible label / tooltip. */
  title?: string;
}

/**
 * SocialLogo — official brand mark (social) or neutral lucide glyph (generic).
 */
export function SocialLogo({
  channel,
  size = 16,
  colored = true,
  className,
  title,
}: SocialLogoProps) {
  const meta = getSocialChannel(channel);
  const label = title ?? meta.label;

  if (meta.kind === "social" && meta.logoPath) {
    return (
      <svg
        role="img"
        aria-label={label}
        viewBox="0 0 24 24"
        width={size}
        height={size}
        className={className}
        fill={colored ? meta.brandColorVar : "currentColor"}
        focusable={false}
      >
        <title>{label}</title>
        <path d={meta.logoPath} />
      </svg>
    );
  }

  const Icon = LUCIDE_FALLBACK[meta.lucideGlyph ?? "Globe"] ?? Globe;
  return (
    <Icon
      size={size}
      aria-label={label}
      className={className}
      style={colored ? { color: meta.brandColorVar } : undefined}
    />
  );
}
