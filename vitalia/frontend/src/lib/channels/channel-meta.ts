// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * channel-meta.ts — Central registry: channel slug → brand metadata.
 *
 * Single source of truth for channel colors, labels and glyphs.
 * Consumed by ChannelBadge (shell-organism), LeadCard (embudo), LeadsTable,
 * LeadSummaryHeader, FrozenLeadRow, and any future surface showing channel origin.
 *
 * Design rules:
 * - Colors are CSS custom property NAMES (e.g., "--channel-whatsapp-soft") — NOT hex literals.
 *   TSX consumers build `var(--channel-X)` references; hex values live in globals.css.
 * - Glyphs are lucide-react icon component names (string) — ChannelBadge resolves them.
 * - Labels are Spanish neutro LatAm (sin voseo, tildes correctas).
 *
 * Lift candidate: brand-local for now. If ≥2 brands need it → lift to
 * @luana/ui-kit via /pm-luana promotion gate (anti-duplication.md).
 *
 * Architecture gate: no hardcoded hex in this file.
 * spec_anchor: 03-arch-fe.md § NEW channel-meta + D.6
 * downstream-regression-na: brand-local lib; no cross-brand consumers
 */

/** Metadata for one communication channel. */
export interface ChannelMeta {
  /** Short Spanish neutro label shown in badges/filters. Sin voseo. */
  label: string;
  /**
   * CSS custom property NAME (without `var()`) for the primary badge background.
   * e.g. "--channel-whatsapp-soft".
   * Consumer: `var(${meta.softColorVar})` in Tailwind arbitrary or inline style
   * when needed — but prefer Tailwind utility classes via colorClass.
   */
  softColorVar: string;
  /**
   * CSS custom property NAME for the badge text/icon accent color.
   * e.g. "--channel-whatsapp-text".
   */
  textColorVar: string;
  /**
   * Tailwind utility class string for the badge (bg + text).
   * Uses semantic Tailwind tokens (NOT arbitrary var() — Tailwind scans these classes).
   * globals.css defines the corresponding CSS vars; Tailwind resolves class → token.
   */
  colorClass: string;
  /**
   * lucide-react icon component name (string).
   * ChannelBadge imports the matching icon by name.
   */
  glyph: string;
}

/**
 * CHANNEL_META — canonical registry.
 *
 * Keys: channel slugs used in Lead.channel, Conversation.channel, etc.
 * Add new channels here; consumers inherit automatically.
 *
 * Color classes use Tailwind semantic utilities aligned with Vitalia token palette:
 *   WhatsApp  → emerald (brand green)
 *   Instagram → pink (brand pink)
 *   Meta      → blue (Meta brand)
 *   Referido  → amber (warm referral)
 *   TikTok    → slate-neutral (dark brand handled via soft bg)
 *   Email     → sky (Vitalia info)
 *   Web       → muted (neutral)
 *   Telegram  → blue (Telegram brand)
 */
export const CHANNEL_META: Readonly<Record<string, ChannelMeta>> = {
  whatsapp: {
    label: "WhatsApp",
    softColorVar: "--channel-whatsapp-soft",
    textColorVar: "--channel-whatsapp-text",
    colorClass:
      "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
    glyph: "MessageCircle",
  },
  instagram: {
    label: "Instagram",
    softColorVar: "--channel-instagram-soft",
    textColorVar: "--channel-instagram-bg",
    colorClass:
      "bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300",
    glyph: "Camera",
  },
  meta: {
    label: "Meta",
    softColorVar: "--channel-meta-soft",
    textColorVar: "--channel-meta-bg",
    colorClass:
      "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
    glyph: "Globe",
  },
  referido: {
    label: "Referido",
    softColorVar: "--channel-referido-soft",
    textColorVar: "--channel-referido-bg",
    colorClass:
      "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
    glyph: "Users",
  },
  tiktok: {
    label: "TikTok",
    softColorVar: "--channel-tiktok-soft",
    textColorVar: "--channel-tiktok-bg",
    colorClass:
      "bg-slate-100 text-slate-800 dark:bg-slate-800/50 dark:text-slate-300",
    glyph: "Video",
  },
  email: {
    label: "Correo",
    softColorVar: "--channel-email-soft",
    textColorVar: "--channel-email-bg",
    colorClass:
      "bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300",
    glyph: "Mail",
  },
  web: {
    label: "Web",
    softColorVar: "--channel-web-soft",
    textColorVar: "--channel-web-bg",
    colorClass: "bg-muted text-muted-foreground",
    glyph: "Globe2",
  },
  telegram: {
    label: "Telegram",
    softColorVar: "--channel-telegram-soft",
    textColorVar: "--channel-telegram-bg",
    colorClass:
      "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
    glyph: "Send",
  },
} as const;

/**
 * Returns channel metadata for a slug, or a graceful fallback for unknown slugs.
 * Fallback uses a neutral muted style so unknown channels never crash the UI.
 */
export function getChannelMeta(slug: string): ChannelMeta {
  return (
    CHANNEL_META[slug] ?? {
      label: slug.charAt(0).toUpperCase() + slug.slice(1),
      softColorVar: "--channel-web-soft",
      textColorVar: "--channel-web-bg",
      colorClass: "bg-muted text-muted-foreground",
      glyph: "Globe",
    }
  );
}

/** Type guard — returns true if slug is a known channel. */
export function isKnownChannel(slug: string): slug is keyof typeof CHANNEL_META {
  return Object.prototype.hasOwnProperty.call(CHANNEL_META, slug);
}
