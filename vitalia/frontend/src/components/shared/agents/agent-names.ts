// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * agent-names — Vitalia AI agent name mapping.
 *
 * Maps internal role identifiers to display names.
 * Names follow Spanish neutro LatAm (no voseo).
 */

export const AGENT_ROLES = ["valeria", "adrian", "lucas"] as const;
export type AgentRole = (typeof AGENT_ROLES)[number];

/**
 * Maps agent role to display name.
 * Adrián uses accent per Spanish orthography.
 */
const AGENT_NAMES: Record<AgentRole, string> = {
  valeria: "Valeria",
  adrian: "Adrián",
  lucas: "Lucas",
};

/**
 * Returns the display name for an agent role.
 * Returns "Agente" as fallback for unknown roles.
 */
export function agentNameByRole(role: string): string {
  if (role in AGENT_NAMES) {
    return AGENT_NAMES[role as AgentRole];
  }
  return "Agente";
}

/**
 * Agent gradient CSS class names per design-system.md.
 * Uses vitalia gradient CSS custom properties — no HEX or rgb/hsl literals.
 * Custom properties defined in globals.css.
 */
export const AGENT_GRADIENT_CLASS: Record<AgentRole, string> = {
  valeria: "bg-vitalia-gradient-agent",
  // Adrián: púrpura → azul-marino gradient (uses inline CSS property reference)
  adrian: "vitalia-agent-gradient-adrian",
  // Lucas: verde-lima → cian gradient (uses inline CSS property reference)
  lucas: "vitalia-agent-gradient-lucas",
};

/**
 * Agent initials for avatar fallback.
 */
export const AGENT_INITIALS: Record<AgentRole, string> = {
  valeria: "VA",
  adrian: "AD",
  lucas: "LU",
};
