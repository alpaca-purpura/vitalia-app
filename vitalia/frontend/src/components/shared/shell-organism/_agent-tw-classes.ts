// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s6-TBD
/**
 * _agent-tw-classes.ts — internal Tailwind class name lookup for agent slugs.
 *
 * Vitalia shell-organism internal helper. Prefix `_` = module-private.
 *
 * CRITICAL: Tailwind v4 JIT purges dynamic class names (e.g. `bg-${agent}-soft`).
 * ALL class names MUST be statically knowable. Use explicit switch/map only.
 *
 * Consumed by: ChatHeader · TypingIndicator · DelegateMarker · MessageBubble · SubTab (F1-S8)
 *
 * spec_anchor: 03-arch.md § 2.4 "Tailwind classnames pattern" + § 2.5 sub-component contracts
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */

import type { AgentSlug, RibbonTabSlug } from "@/lib/agent-catalog";

/** Background class for agent (full saturation — avatar, user bubbles, accents). */
export function agentBgClass(slug: AgentSlug): string {
  switch (slug) {
    case "lisa":
      return "bg-agent-lisa";
    case "valeria":
      return "bg-agent-valeria";
    case "adrian":
      return "bg-agent-adrian";
    case "lucas":
      return "bg-agent-lucas";
    case "camila":
      return "bg-agent-camila";
    case "mateo":
      return "bg-agent-mateo";
    default:
      return "bg-agent-valeria";
  }
}

/** Soft background class for agent (desaturated — TypingIndicator bubble, DelegateMarker). */
export function agentBgSoftClass(slug: AgentSlug): string {
  switch (slug) {
    case "lisa":
      return "bg-agent-lisa-soft";
    case "valeria":
      return "bg-agent-valeria-soft";
    case "adrian":
      return "bg-agent-adrian-soft";
    case "lucas":
      return "bg-agent-lucas-soft";
    case "camila":
      return "bg-agent-camila-soft";
    case "mateo":
      return "bg-agent-mateo-soft";
    default:
      return "bg-agent-valeria-soft";
  }
}

/** Text color class for agent (for name labels inside TypingIndicator, DelegateMarker). */
export function agentTextClass(slug: AgentSlug): string {
  switch (slug) {
    case "lisa":
      return "text-agent-lisa";
    case "valeria":
      return "text-agent-valeria";
    case "adrian":
      return "text-agent-adrian";
    case "lucas":
      return "text-agent-lucas";
    case "camila":
      return "text-agent-camila";
    case "mateo":
      return "text-agent-mateo";
    default:
      return "text-agent-valeria";
  }
}

/** Dot/icon background for typing-dot dots (same as full bg). */
export const agentDotBgClass = agentBgClass;

/**
 * Text color class for active sub-tab label (F1-S8 SubTab molecule).
 *
 * Differs from agentTextClass (F1-S6) for two exceptions:
 * - "lucas": returns "text-foreground" because hex #111111 (near-black) has poor contrast
 *   on bg-agent-lucas-soft (rgba 10% black on dark backgrounds).
 *   spec_anchor: 03-arch.md § 2.2 D18 "Lucas exception"
 * - "config": returns "text-foreground" because Config is not an agent — uses bg-muted neutral.
 *   spec_anchor: 03-arch.md § 2.2 D19 "Config exception"
 *
 * CRITICAL: No dynamic string construction (e.g. `text-agent-${slug}`) — Tailwind v4 JIT
 * purges non-statically-knowable class names. All return values are explicit string literals.
 */
export function agentTextClassSubTab(slug: RibbonTabSlug): string {
  switch (slug) {
    case "lisa":
      return "text-agent-lisa";
    case "valeria":
      return "text-agent-valeria";
    case "adrian":
      return "text-agent-adrian";
    case "lucas":
      // Exception D18: near-black hex #111111 — poor contrast on rgba-10%-black bg-agent-lucas-soft.
      return "text-foreground";
    case "camila":
      return "text-agent-camila";
    case "mateo":
      // Exception D20: #FEE209 yellow on bg-agent-mateo-soft (#fcf7cf) = 1.21 contrast (fails WCAG AA).
      // Use text-foreground (near-black) for AA compliance. spec_anchor: T-V2 fix-loop axe SC-20.
      return "text-foreground";
    case "config":
      // Exception D19: Config is not an agent — bg-muted neutral, text-foreground per mockup.
      return "text-foreground";
    default: {
      // TypeScript exhaustiveness guard — should never reach here.
      const _exhaustiveCheck: never = slug;
      return _exhaustiveCheck;
    }
  }
}
