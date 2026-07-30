// cap: __shared__
// story-origin: vitalia-fase2-adrian-inbox
/**
 * social-channels.ts — SSoT for SOCIAL NETWORK brand identity (real logos + colors).
 *
 * Single source of truth for ANY surface that references a social network: inbox
 * channel badges, conversation-list channel marker, filters, and the future
 * "connect a channel" (Connections) flow (e.g. adding Telegram).
 *
 * Why this exists (UI-AUDIT-2 #3): `channel-meta.ts` uses GENERIC lucide glyphs +
 * Tailwind palette. Chris asked for the REAL brand logos (WhatsApp/Instagram/…) and
 * the REAL brand colors, in one canonical place. This file holds the official SVG
 * path (simple-icons, viewBox 0 0 24 24) + the brand hex per network. `channel-meta`
 * keeps the soft Tailwind chips; this owns the brand identity.
 *
 * Lift candidate: brand-local for now. If ≥2 brands need it → lift to
 * `core/@luana/ui-kit` (or a `@luana/social-channels` package) via /pm-luana
 * promotion gate (anti-duplication.md). Mirror prohibited.
 *
 * Logo paths are the official brand marks (simple-icons). Brand COLORS are NOT
 * hardcoded here (FE-A1 arch gate) — they reference the `--channel-{slug}-bg` CSS
 * vars already defined in globals.css (the canonical hex lives there, exempt).
 *
 * downstream-regression-na: brand-local lib; no cross-brand consumers (yet)
 */

/** A social network with an official logo + brand color. */
export interface SocialChannelBrand {
  /** Canonical slug (matches Conversation.channel / Lead.channel). */
  slug: string;
  /** Spanish neutro display label. */
  label: string;
  /**
   * "social" → has an official brand logo + color (renders via SocialLogo).
   * "generic" → no brand logo; falls back to a neutral lucide glyph.
   */
  kind: "social" | "generic";
  /**
   * Brand color as a CSS var reference (e.g. "var(--channel-whatsapp-bg)").
   * The hex itself lives in globals.css — never hardcode it here (FE-A1).
   */
  brandColorVar: string;
  /** Official logo SVG path (viewBox 0 0 24 24). Present for kind="social". */
  logoPath?: string;
  /** lucide-react icon component name for kind="generic". */
  lucideGlyph?: string;
}

// Official brand mark paths (simple-icons, MIT — viewBox 0 0 24 24).
const WHATSAPP_PATH =
  "M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.885-9.885 9.885M20.52 3.449C18.24 1.245 15.24 0 12.045 0 5.463 0 .104 5.359.101 11.892c0 2.096.549 4.142 1.595 5.945L0 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.585 0 11.946-5.36 11.948-11.893a11.821 11.821 0 00-3.491-8.458";
const INSTAGRAM_PATH =
  "M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 1.381.164.422.36 1.057.413 2.227.057 1.266.07 1.646.07 4.85s-.015 3.585-.074 4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.413-1.274.057-1.649.07-4.859.07-3.211 0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.165-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 0-3.196.016-3.586.061-4.861.061-1.17.255-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06l.045.03zm0 3.678c-3.405 0-6.162 2.76-6.162 6.162 0 3.405 2.76 6.162 6.162 6.162 3.405 0 6.162-2.76 6.162-6.162 0-3.405-2.76-6.162-6.162-6.162zM12 16c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm7.846-10.405c0 .795-.646 1.44-1.44 1.44-.795 0-1.44-.646-1.44-1.44 0-.794.646-1.439 1.44-1.439.793-.001 1.44.645 1.44 1.439z";
const TELEGRAM_PATH =
  "M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z";
const MESSENGER_PATH =
  "M.001 11.639C.001 4.949 5.241 0 12 0s12 4.95 12 11.639c0 6.689-5.24 11.638-12 11.638-1.21 0-2.371-.16-3.461-.46a.96.96 0 0 0-.641.05l-2.39 1.05a.96.96 0 0 1-1.35-.85l-.07-2.14a.97.97 0 0 0-.32-.68A11.39 11.389 0 0 1 .001 11.639zm8.32-2.19l-3.52 5.6c-.35.53.32 1.139.82.749l3.79-2.87c.26-.2.6-.2.86 0l2.8 2.1c.84.63 2.04.4 2.6-.49l3.52-5.6c.35-.53-.32-1.13-.82-.75l-3.79 2.87c-.26.2-.6.2-.86 0l-2.8-2.1a1.8 1.8 0 0 0-2.6.49z";
const FACEBOOK_PATH =
  "M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z";
const TIKTOK_PATH =
  "M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z";

/** Canonical registry — add a network here and every surface inherits it.
 *  Colors reference globals.css `--channel-{slug}-bg` (hex lives there, not here). */
export const SOCIAL_CHANNELS: Readonly<Record<string, SocialChannelBrand>> = {
  whatsapp: { slug: "whatsapp", label: "WhatsApp", kind: "social", brandColorVar: "var(--channel-whatsapp-bg)", logoPath: WHATSAPP_PATH },
  instagram: { slug: "instagram", label: "Instagram", kind: "social", brandColorVar: "var(--channel-instagram-bg)", logoPath: INSTAGRAM_PATH },
  telegram: { slug: "telegram", label: "Telegram", kind: "social", brandColorVar: "var(--channel-telegram-bg)", logoPath: TELEGRAM_PATH },
  tiktok: { slug: "tiktok", label: "TikTok", kind: "social", brandColorVar: "var(--channel-tiktok-bg)", logoPath: TIKTOK_PATH },
  facebook: { slug: "facebook", label: "Facebook", kind: "social", brandColorVar: "var(--channel-meta-bg)", logoPath: FACEBOOK_PATH },
  facebook_messenger: { slug: "facebook_messenger", label: "Messenger", kind: "social", brandColorVar: "var(--channel-meta-bg)", logoPath: MESSENGER_PATH },
  meta: { slug: "meta", label: "Facebook", kind: "social", brandColorVar: "var(--channel-meta-bg)", logoPath: FACEBOOK_PATH },
  email: { slug: "email", label: "Correo", kind: "generic", brandColorVar: "var(--channel-email-bg)", lucideGlyph: "Mail" },
  web: { slug: "web", label: "Web", kind: "generic", brandColorVar: "var(--channel-web-bg)", lucideGlyph: "Globe" },
  phone: { slug: "phone", label: "Teléfono", kind: "generic", brandColorVar: "var(--channel-web-bg)", lucideGlyph: "Phone" },
  walk_in: { slug: "walk_in", label: "Presencial", kind: "generic", brandColorVar: "var(--channel-web-bg)", lucideGlyph: "MapPin" },
} as const;

/** Returns the brand identity for a slug, with a safe generic fallback. */
export function getSocialChannel(slug: string | null | undefined): SocialChannelBrand {
  const key = (slug ?? "").toLowerCase();
  return (
    SOCIAL_CHANNELS[key] ?? {
      slug: key || "web",
      label: key ? key.charAt(0).toUpperCase() + key.slice(1) : "Web",
      kind: "generic",
      brandColorVar: "var(--channel-web-bg)",
      lucideGlyph: "Globe",
    }
  );
}

/** Brand color at a given alpha for soft fills, e.g. `brandColorAlpha("whatsapp", 0.12)`.
 *  Uses color-mix so the canonical hex stays in globals.css (no hex literal here). */
export function brandColorAlpha(slug: string, alpha: number): string {
  const pct = Math.round(Math.min(1, Math.max(0, alpha)) * 100);
  return `color-mix(in srgb, ${getSocialChannel(slug).brandColorVar} ${pct}%, transparent)`;
}
