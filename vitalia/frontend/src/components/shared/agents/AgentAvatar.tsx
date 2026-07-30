// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * AgentAvatar — circular avatar for Vitalia AI agents.
 *
 * Displays agent initials on a gradient background per design-system.md.
 * Gradient CSS classes defined in globals.css (no HEX literals here).
 *
 * Size variants: sm (24px) | md (32px, default) | lg (48px)
 */

import { cn } from "@/lib/cn";
import {
  agentNameByRole,
  AGENT_GRADIENT_CLASS,
  AGENT_INITIALS,
} from "./agent-names";
import type { AgentRole } from "./agent-names";

export interface AgentAvatarProps {
  /** Agent role identifier */
  role: AgentRole | string;
  /** Avatar size */
  size?: "sm" | "md" | "lg";
  /** Additional CSS classes */
  className?: string;
}

const SIZE_CLASSES = {
  sm: "w-6 h-6 text-[10px]",
  md: "w-8 h-8 text-xs",
  lg: "w-12 h-12 text-sm",
} as const;

/**
 * Circular agent avatar with gradient background and initials.
 * No HEX literals — gradient comes from globals.css classes.
 */
export function AgentAvatar({
  role,
  size = "md",
  className,
}: AgentAvatarProps) {
  const name = agentNameByRole(role);
  const initials =
    role in AGENT_INITIALS
      ? AGENT_INITIALS[role as AgentRole]
      : name.slice(0, 2).toUpperCase();

  const gradientClass =
    role in AGENT_GRADIENT_CLASS
      ? AGENT_GRADIENT_CLASS[role as AgentRole]
      : "bg-vitalia-gradient-agent";

  return (
    <span
      className={cn(
        "inline-flex items-center justify-center rounded-full",
        "font-semibold text-white select-none shrink-0",
        gradientClass,
        SIZE_CLASSES[size],
        className,
      )}
      aria-label={`Agente ${name}`}
      role="img"
      title={name}
    >
      {initials}
    </span>
  );
}
