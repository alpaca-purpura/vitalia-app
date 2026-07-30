// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * AgentAttribution — shows which agent performed an action.
 *
 * Pattern: [Avatar] Valeria actualizó el perfil de la paciente
 * Per design-system.md: used in activity stream, copilot chat history.
 *
 * All colors via vt-* CSS classes from globals.css (no hsl literals).
 */

import { cn } from "@/lib/cn";
import { AgentAvatar } from "./AgentAvatar";
import { agentNameByRole } from "./agent-names";
import type { AgentRole } from "./agent-names";

export interface AgentAttributionProps {
  /** Agent role identifier */
  role: AgentRole | string;
  /** Action description (Spanish neutro — no voseo) */
  action: string;
  /** Target of the action (optional, e.g. "el perfil de Juan García") */
  target?: string;
  /** Timestamp string (already formatted via formatTenantRelative) */
  timestamp?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Attribution line showing agent + action + optional target + timestamp.
 * Used in activity streams and copilot history.
 */
export function AgentAttribution({
  role,
  action,
  target,
  timestamp,
  className,
}: AgentAttributionProps) {
  const name = agentNameByRole(role);

  return (
    <div
      className={cn("flex items-center gap-2 text-sm", className)}
      aria-label={`${name}: ${action}${target ? ` ${target}` : ""}`}
    >
      <AgentAvatar role={role} size="sm" />
      <span className="vt-text font-medium">{name}</span>
      <span className="vt-text-muted">{action}</span>
      {target && (
        <span className="vt-text font-medium truncate max-w-[160px]">
          {target}
        </span>
      )}
      {timestamp && (
        <span
          className="ml-auto text-xs vt-text-faint shrink-0"
          aria-label={`Hace: ${timestamp}`}
        >
          {timestamp}
        </span>
      )}
    </div>
  );
}
