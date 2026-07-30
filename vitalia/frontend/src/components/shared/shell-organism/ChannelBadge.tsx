// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * ChannelBadge — reusable channel identifier badge (EXTEND — T-FE-1).
 *
 * Origin: T-3 vitalia-fase2-adrian-inbox (whatsapp/instagram/email/web/telegram).
 * Extension: T-FE-1 vitalia-fase2-adrian-embudo (+meta/referido/tiktok + channel-meta registry).
 *
 * Now consumes `channel-meta.ts` registry for all styling and labels.
 * Back-compat: `iconOnly` and `className` props unchanged; all existing consumers
 * in inbox continue to work without modification.
 *
 * Design rules:
 * - Colors via channel-meta.ts colorClass (Tailwind tokens, no hardcoded hex).
 * - Icons via lucide-react (resolved by glyph name from channel-meta).
 * - Server Component by default (no state, no effects).
 * - Spanish neutro labels from registry.
 *
 * Lift candidate: brand-local for now. If ≥2 brands need it → lift to
 * @luana/ui-kit via /pm-luana promotion gate (anti-duplication.md).
 *
 * spec_anchor: 03-arch-fe.md § EXTEND ChannelBadge (D.6)
 * downstream-regression-na: brand-local component; no cross-brand consumers
 */

import {
  MessageCircle,
  Camera,
  Mail,
  Globe,
  Globe2,
  Users,
  Video,
  Send,
} from "lucide-react";
import type { LucideProps } from "lucide-react";
import { cn } from "@/lib/utils";
import { getChannelMeta } from "@/lib/channels/channel-meta";

// ── Channel types ─────────────────────────────────────────────────────────────

/**
 * Known channel slugs union type.
 * Open-ended via `| string` for future channels — unknown slugs get graceful fallback.
 */
export type ChannelSlug =
  | "whatsapp"
  | "instagram"
  | "meta"
  | "referido"
  | "tiktok"
  | "email"
  | "web"
  | "telegram"
  | string;

// ── Icon resolver ─────────────────────────────────────────────────────────────

type LucideIconComponent = React.ComponentType<LucideProps>;

/** Maps lucide icon component names (from channel-meta glyph) to the actual component. */
const ICON_MAP: Record<string, LucideIconComponent> = {
  MessageCircle,
  Camera,
  Mail,
  Globe,
  Globe2,
  Users,
  Video,
  Send,
};

/**
 * Resolves the lucide icon component for a channel glyph name.
 * Falls back to Globe if the glyph name is unknown.
 */
function resolveIcon(glyph: string): LucideIconComponent {
  return ICON_MAP[glyph] ?? Globe;
}

// ── Component Props ───────────────────────────────────────────────────────────

export interface ChannelBadgeProps {
  /** Channel slug — e.g. "whatsapp", "instagram", "meta", "referido", "tiktok". */
  channel: ChannelSlug;
  /**
   * When true, renders icon only (no visible text label).
   * An sr-only span with the label is always rendered for a11y.
   * Defaults to false.
   */
  iconOnly?: boolean;
  /** Optional extra Tailwind classes injected on the outer span. */
  className?: string;
}

// ── ChannelBadge ─────────────────────────────────────────────────────────────

/**
 * ChannelBadge — compact badge identifying a communication channel.
 *
 * Resolves label, color class and icon from `channel-meta.ts` registry.
 * Back-compat with all existing inbox consumers (iconOnly, className props intact).
 *
 * Usage:
 *   <ChannelBadge channel="whatsapp" />
 *   <ChannelBadge channel="meta" iconOnly />
 *   <ChannelBadge channel="referido" className="my-4" />
 *
 * Accessible: icon is aria-hidden; label is visible text or sr-only (iconOnly).
 */
export function ChannelBadge({
  channel,
  iconOnly = false,
  className,
}: ChannelBadgeProps) {
  const meta = getChannelMeta(channel);
  const Icon = resolveIcon(meta.glyph);

  return (
    <span
      data-testid={`channel-badge-${channel}`}
      title={meta.label}
      aria-label={meta.label}
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        meta.colorClass,
        className,
      )}
    >
      <Icon size={12} aria-hidden focusable={false} />
      {iconOnly ? (
        <span className="sr-only">{meta.label}</span>
      ) : (
        <span>{meta.label}</span>
      )}
    </span>
  );
}
